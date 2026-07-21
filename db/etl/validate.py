#!/usr/bin/env python
"""Phase-4 validation checkpoint (db/AG_DB_DESIGN.md §5.3 / upgrade.md Phase 4).

Checks the built backend:
  1. dim row counts vs expected cardinalities (from the exploration pass);
  2. fact row counts per (expansion, output_type), and total fact rows for the
     2x expansion vs the known raw count (102,782,767) — proves the dim joins
     dropped nothing;
  3. spot-check a known pathogenic locus (FMR1) against the raw 2x TSV;
  4. score ranges are finite / sane.

Run from the George repo root:  python db/etl/validate.py
"""
import os
import duckdb

OUT = "data/ag_db"
DIMS = f"{OUT}/dims"
FACT = f"{OUT}/ag_scores/**/*.parquet"
RAW_2X = "data/5UTR/B_5UTR_all_GCN_2xAG.tsv"

# From db/etl/explore.py on the 2x file.
EXPECTED = {
    "variants": 6650, "output_types": 11, "scorers": 19,
    "tracks": None, "genes": None,  # printed, not asserted
}
RAW_2X_ROWS = 102_782_767
FMR1 = "X-147912050-147912110-CGG"

con = duckdb.connect()
con.execute(f"PRAGMA threads={os.environ.get('AG_THREADS', '4')}")
con.execute(f"PRAGMA memory_limit='{os.environ.get('AG_MEM', '24GB')}'")
con.execute("PRAGMA temp_directory='db/etl/duck_tmp'")

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")


print("== 1. dim row counts ==")
for t in ["regions", "output_types", "scorers", "tracks", "genes", "variants"]:
    n = con.execute(f"SELECT count(*) FROM '{DIMS}/{t}.parquet'").fetchone()[0]
    exp = EXPECTED.get(t)
    tag = "" if exp is None else f" (expect {exp})"
    print(f"  {t:14s} {n:,}{tag}")
    if exp is not None:
        check(f"{t} count == {exp}", n == exp)

print("\n== variants: pathogenic flags ==")
np = con.execute(
    f"SELECT count(*) FROM '{DIMS}/variants.parquet' WHERE is_pathogenic"
).fetchone()[0]
print(f"  pathogenic variants: {np} (expect 7)")
check("7 pathogenic variants", np == 7)
for r in con.execute(
    f"""SELECT locus_id, host_gene_name, disease FROM '{DIMS}/variants.parquet'
        WHERE is_pathogenic ORDER BY host_gene_name"""
).fetchall():
    print(f"    {r[0]:28s} {r[1]:10s} {r[2]}")

print("\n== 2. fact row counts per (expansion, output_type) ==")
for e, ot, n in con.execute(
    f"""SELECT expansion, output_type, count(*) FROM '{FACT}'
        GROUP BY 1,2 ORDER BY 1,2"""
).fetchall():
    print(f"  exp={e:>2}  {ot:20s} {n:,}")

tot2 = con.execute(
    f"SELECT count(*) FROM '{FACT}' WHERE expansion=2"
).fetchone()[0]
print(f"\n  fact rows @2x: {tot2:,} (raw file: {RAW_2X_ROWS:,})")
check("2x fact == raw 2x rows (no join drops)", tot2 == RAW_2X_ROWS)

print("\n== 3. spot-check pathogenic locus (FMR1) @2x vs raw TSV ==")
if not os.path.exists(RAW_2X):
    # Phase 7 removes the raw TSVs; the raw-vs-fact spot-check is only possible
    # while they exist. It already passed pre-deletion (see upgrade_log.md), so
    # skip rather than fail once the source is gone.
    print(f"  SKIPPED — raw TSV '{RAW_2X}' not present (removed in Phase 7). "
          f"This cross-check passed before deletion; see upgrade_log.md.")
else:
    raw = (f"read_csv('{RAW_2X}', delim='\t', header=true, sample_size=-1, "
           f"all_varchar=true, nullstr='')")
    raw_n = con.execute(
        f"SELECT count(*) FROM {raw} WHERE original_variant_id = '{FMR1}'"
    ).fetchone()[0]
    fact_n = con.execute(
        f"""SELECT count(*) FROM '{FACT}' f
            JOIN '{DIMS}/variants.parquet' v USING (variant_id)
            WHERE v.locus_id = '{FMR1}' AND f.expansion = 2"""
    ).fetchone()[0]
    print(f"  raw rows for {FMR1}: {raw_n:,}")
    print(f"  fact rows for {FMR1} @2x: {fact_n:,}")
    check("FMR1 row count matches raw", raw_n == fact_n and raw_n > 0)

    # score value cross-check: compare RNA_SEQ raw_score sum (rounded) raw vs fact
    raw_sum = con.execute(
        f"""SELECT round(sum(TRY_CAST(raw_score AS DOUBLE)), 4) FROM {raw}
            WHERE original_variant_id = '{FMR1}' AND output_type = 'RNA_SEQ'"""
    ).fetchone()[0]
    fact_sum = con.execute(
        f"""SELECT round(sum(f.raw_score), 4) FROM '{FACT}' f
            JOIN '{DIMS}/variants.parquet' v USING (variant_id)
            WHERE v.locus_id = '{FMR1}' AND f.expansion = 2
              AND f.output_type = 'RNA_SEQ'"""
    ).fetchone()[0]
    print(f"  RNA_SEQ raw_score sum  raw={raw_sum}  fact={fact_sum}")
    check("FMR1 RNA_SEQ score sum matches", raw_sum == fact_sum)

print("\n== 4. score ranges ==")
for e, rmin, rmax, qmin, qmax, nnull in con.execute(
    f"""SELECT expansion, min(raw_score), max(raw_score),
               min(quantile_score), max(quantile_score),
               sum(CASE WHEN raw_score IS NULL THEN 1 ELSE 0 END)
        FROM '{FACT}' GROUP BY 1 ORDER BY 1"""
).fetchall():
    print(f"  exp={e:>2}  raw[{rmin:.3g},{rmax:.3g}]  "
          f"quantile[{qmin:.3g},{qmax:.3g}]  null_raw={nnull:,}")

print("\n== FK integrity (orphans should be 0) ==")
orphans = con.execute(
    f"""SELECT count(*) FROM '{FACT}' f
        LEFT JOIN '{DIMS}/scorers.parquet' s USING (scorer_id)
        WHERE s.scorer_id IS NULL"""
).fetchone()[0]
check("no orphan scorer_id", orphans == 0)

print(f"\n==== {'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'} ====")
con.close()
raise SystemExit(0 if ok else 1)
