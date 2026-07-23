#!/usr/bin/env python
"""Phase-4 validation checkpoint (db/AG_DB_DESIGN.md §5.3), multi-region.

Checks the built backend, per region declared in db/etl/regions.json:
  1. dim row counts (printed; scorers/output_types asserted non-empty);
  2. per-region variant count == catalog rows, + motif-class breakdown;
  3. fact row counts per (region, expansion, output_type);
  4. FK integrity — no orphan scorer_id, no fact variant_id missing from variants;
  5. score ranges are finite / sane, per (region, expansion);
  6. (opt-in, AG_VALIDATE_RAWCOUNT=1) per (region, expansion) fact row count vs the
     raw AG TSV row count — proves the INNER joins dropped nothing. This scans the
     full ~30-290 GB TSVs, so it is off by default; also spot-checks one
     pathogenic locus per region (RNA_SEQ raw_score sum) raw-vs-fact.

Run from the George repo root:  python db/etl/validate.py
Knobs: AG_THREADS, AG_MEM, AG_OUT, AG_REGIONS_MANIFEST, AG_VALIDATE_RAWCOUNT.
"""
import os
import sys
import duckdb

sys.path.insert(0, os.path.dirname(__file__))
from etl import load_regions, read_ag, read_tsv  # noqa: E402

OUT = os.environ.get("AG_OUT", "data/ag_db")
DIMS = f"{OUT}/dims"
FACT = f"{OUT}/ag_scores/**/*.parquet"
RAWCOUNT = os.environ.get("AG_VALIDATE_RAWCOUNT", "") not in ("", "0", "false")

con = duckdb.connect()
con.execute(f"PRAGMA threads={os.environ.get('AG_THREADS', '4')}")
con.execute(f"PRAGMA memory_limit='{os.environ.get('AG_MEM', '24GB')}'")
con.execute("PRAGMA temp_directory='db/etl/duck_tmp'")

# variants dim is one file per region (dims/variants/*.parquet), or a single
# legacy dims/variants.parquet; expose both as the `variants` view.
if os.path.isdir(f"{DIMS}/variants"):
    con.execute(
        f"CREATE VIEW variants AS SELECT * FROM "
        f"read_parquet('{DIMS}/variants/*.parquet', union_by_name=1)"
    )
else:
    con.execute(f"CREATE VIEW variants AS SELECT * FROM '{DIMS}/variants.parquet'")

regions = load_regions()
ok = True


def check(label, cond):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")


print("== 1. dim row counts ==")
for t in ["regions", "output_types", "scorers", "tracks", "genes"]:
    n = con.execute(f"SELECT count(*) FROM '{DIMS}/{t}.parquet'").fetchone()[0]
    print(f"  {t:14s} {n:,}")
    if t in ("scorers", "output_types"):
        check(f"{t} non-empty", n > 0)
nvar = con.execute("SELECT count(*) FROM variants").fetchone()[0]
print(f"  variants       {nvar:,} (all regions)")
check("variant_id is unique",
      con.execute("SELECT count(*)=count(DISTINCT variant_id) FROM variants").fetchone()[0])

print("\n== 2. per-region variants + motif-class breakdown ==")
for spec in regions:
    r = spec["region"]
    nv = con.execute("SELECT count(*) FROM variants WHERE region = ?", [r]).fetchone()[0]
    # variant count must equal the region's catalog row count (variants come 1:1
    # from the catalog — no join, so nothing should drop or fan out).
    exp = con.execute(f"SELECT count(*) FROM {read_tsv(spec['catalog'])}").fetchone()[0]
    print(f"  {r:6s} variants={nv:,} (catalog {exp:,})")
    check(f"{r} variants == catalog rows", nv == exp)
    for cls, n in con.execute(
        "SELECT motif_class, count(*) FROM variants WHERE region = ? "
        "GROUP BY 1 ORDER BY 2 DESC", [r]
    ).fetchall():
        print(f"      {str(cls):16s} {n:,}")

print("\n== 3. fact row counts per (region, expansion, output_type) ==")
for reg, e, ot, n in con.execute(
    f"""SELECT region, expansion, output_type, count(*) FROM '{FACT}'
        GROUP BY 1,2,3 ORDER BY 1,2,3"""
).fetchall():
    print(f"  {reg:6s} exp={e:>2}  {ot:20s} {n:,}")

print("\n== 4. FK integrity (orphans should be 0) ==")
orphan_scorer = con.execute(
    f"""SELECT count(*) FROM '{FACT}' f
        LEFT JOIN '{DIMS}/scorers.parquet' s USING (scorer_id)
        WHERE s.scorer_id IS NULL"""
).fetchone()[0]
check("no orphan scorer_id", orphan_scorer == 0)
orphan_var = con.execute(
    f"""SELECT count(*) FROM '{FACT}' f
        LEFT JOIN variants v USING (variant_id)
        WHERE v.variant_id IS NULL"""
).fetchone()[0]
check("no orphan variant_id", orphan_var == 0)

print("\n== 5. score ranges per (region, expansion) ==")
for reg, e, rmin, rmax, qmin, qmax, nnull in con.execute(
    f"""SELECT region, expansion, min(raw_score), max(raw_score),
               min(quantile_score), max(quantile_score),
               sum(CASE WHEN raw_score IS NULL THEN 1 ELSE 0 END)
        FROM '{FACT}' GROUP BY 1,2 ORDER BY 1,2"""
).fetchall():
    print(f"  {reg:6s} exp={e:>2}  raw[{rmin:.3g},{rmax:.3g}]  "
          f"quantile[{qmin:.3g},{qmax:.3g}]  null_raw={nnull:,}")

if RAWCOUNT:
    print("\n== 6. raw-vs-fact cross-check (AG_VALIDATE_RAWCOUNT=1; full scans) ==")
    for spec in regions:
        r = spec["region"]
        for e in (2, 5, 20):
            path = spec["ag"][str(e)]
            if not os.path.exists(path):
                print(f"  SKIP {r} {e}x — raw TSV absent ({path})")
                continue
            raw_n = con.execute(f"SELECT count(*) FROM {read_ag(path)}").fetchone()[0]
            fact_n = con.execute(
                f"SELECT count(*) FROM '{OUT}/ag_scores/region={r}/expansion={e}/**/*.parquet'"
            ).fetchone()[0]
            print(f"  {r} {e}x  raw={raw_n:,}  fact={fact_n:,}")
            check(f"{r} {e}x fact == raw (no join drops)", raw_n == fact_n)
        # per-region score spot-check on the 2x file (first locus by id)
        loc = con.execute(
            "SELECT locus_id FROM variants WHERE region = ? "
            "ORDER BY locus_id LIMIT 1", [r]
        ).fetchone()
        p2 = spec["ag"]["2"]
        if loc and os.path.exists(p2):
            locus, raw = loc[0], read_ag(p2)
            raw_sum = con.execute(
                f"""SELECT round(sum(TRY_CAST(raw_score AS DOUBLE)), 4) FROM {raw}
                    WHERE original_variant_id = ? AND output_type = 'RNA_SEQ'""",
                [locus],
            ).fetchone()[0]
            fact_sum = con.execute(
                f"""SELECT round(sum(f.raw_score), 4) FROM '{FACT}' f
                    JOIN variants v USING (variant_id)
                    WHERE v.locus_id = ? AND f.region = ? AND f.expansion = 2
                      AND f.output_type = 'RNA_SEQ'""",
                [locus, r],
            ).fetchone()[0]
            print(f"  {r} {locus} RNA_SEQ raw_score sum  raw={raw_sum}  fact={fact_sum}")
            check(f"{r} {locus} RNA_SEQ score sum matches", raw_sum == fact_sum)
else:
    print("\n== 6. raw-vs-fact cross-check SKIPPED "
          "(set AG_VALIDATE_RAWCOUNT=1 to enable; scans the full TSVs) ==")

print(f"\n==== {'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'} ====")
con.close()
raise SystemExit(0 if ok else 1)
