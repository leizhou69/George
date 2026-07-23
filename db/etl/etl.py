#!/usr/bin/env python
"""AlphaGenome → DuckDB/Parquet star-schema ETL (upgrade.md Phase 4; multi-region).

Builds the backend described in db/AG_DB_DESIGN.md as a SINGLE multi-region DB:

    data/ag_db/
      dims/
        variants/<region>.parquet          one file per region (union_by_name)
        tracks.parquet scorers.parquet genes.parquet output_types.parquet
        regions.parquet
      ag_scores/region=<R>/expansion=<E>/output_type=<OT>/part-*.parquet
      ag_db.log                            append-only build/provenance log

Only AlphaGenome prediction files (names ending AG.tsv / AG.out.tsv / AG.sout.tsv)
are accepted as fact inputs; every build appends inputs + row counts to ag_db.log.
Each variant is classified by repeat-unit length (motif_len / motif_class), so the
schema handles tri-, tetra-, penta-nucleotide … repeats without a region-wide
assumption; `regions.repeat_type` is only a free-form dataset label.

The set of regions and their input files is declared in a manifest
(`db/etl/regions.json`; override with env AG_REGIONS_MANIFEST). Adding a region
(3'UTR, exon, …) = add a manifest entry + rerun.

Dimensions are SHARED across regions and given global surrogate keys:
  * scorers / output_types / tracks / genes are deduped over the UNION of every
    region's 2x AG file (they are AlphaGenome-intrinsic, so identical or
    overlapping across regions; genes are deduped by ensembl id per the design).
  * variants get a single global `variant_id` space (offset per region) but are
    written one Parquet per region so each region keeps its own catalog columns
    (schemas differ: e.g. 5'UTR has MotifID, CDS has ManeGene*); query_ag reads
    them with union_by_name.

Because the surrogate keys span all regions, the fact must be rebuilt for EVERY
region whenever the region set changes — i.e. this is a full rebuild, not an
incremental append. That is why all regions' source TSVs must be present (the
5'UTR TSVs deleted in Phase 7 need restoring before a rebuild).

DuckDB streams the ~30–290 GB TSVs directly (columnar, spills to disk), so this
runs inside a modest allocation; the fact is built per (region, expansion) in its
own process so memory is released between the big files.

Run from the George repo root:
    python db/etl/etl.py preflight                    # check every manifest file exists
    python db/etl/etl.py regions                       # print region names (for sbatch loop)
    python db/etl/etl.py dims                          # build all shared dims + per-region variants
    python db/etl/etl.py fact --region CDS --expansion 2   # one region+expansion's fact
    python db/etl/etl.py fact                           # every region × {2,5,20}
    python db/etl/etl.py all                            # dims + all facts

Knobs via env: AG_MEM (default 24GB), AG_THREADS (default 4), AG_TMP, AG_OUT,
AG_REGIONS_MANIFEST.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import glob
import duckdb

# The 13 track-metadata columns (AG names), in a fixed order. A track's natural
# key is all of them together (track_name alone is not unique across biosamples),
# so we hash them into one `track_key` and join the 100M-row fact on that single
# column instead of a 13-way equality join.
TRACK_COLS = [
    "track_name", "track_strand", '"Assay title"', "ontology_curie",
    "biosample_name", "biosample_type", "biosample_life_stage", "data_source",
    "endedness", "genetically_modified", "transcription_factor",
    "histone_mark", "gtex_tissue",
]

# Catalog columns promoted to first-class variant attributes (and therefore
# EXCLUDEd from the catch-all `c.* EXCLUDE (...)`). MotifID is handled separately
# because it is present in the 5'UTR catalog but not the CDS one.
PROMOTED = [
    "LocusId", "CanonicalMotif", "GencodeGeneName", "GencodeGeneId",
    "GencodeGeneRegion",
]
# Only AlphaGenome prediction files may populate the fact/dims. Their names end in
# AG.tsv, AG.out.tsv, or AG.sout.tsv (5'UTR uses .sout.tsv, CDS/3'UTR use .out.tsv,
# the original 5'UTR used plain .tsv). Anything else in a manifest ag[] slot is
# rejected so a catalog/pathogenic file can't be fed in by mistake.
AG_FILE_RE = re.compile(r"AG\.(?:s?out\.)?tsv$")

# Repeat-unit motif classification is derived per variant from the length of the
# canonical motif, so it is future-proof for tetra-/penta-nucleotide repeats
# rather than assuming a whole region is "trinucleotide".
MOTIF_CLASS_BY_LEN = {
    1: "mononucleotide", 2: "dinucleotide", 3: "trinucleotide",
    4: "tetranucleotide", 5: "pentanucleotide", 6: "hexanucleotide",
}


def _motif_class_sql(motif_expr):
    """SQL expr → human motif class from the canonical-motif length (NULL-safe).
    Unknown lengths fall back to '<n>-nucleotide' so nothing is silently dropped."""
    whens = " ".join(
        f"WHEN {k} THEN '{v}'" for k, v in sorted(MOTIF_CLASS_BY_LEN.items())
    )
    return (
        f"CASE length({motif_expr}) {whens} "
        f"ELSE length({motif_expr})::VARCHAR || '-nucleotide' END"
    )


def _track_key(prefix=""):
    """md5(concat_ws) over the 13 track cols; coalesce first so NULLs are kept
    positionally (concat_ws would otherwise drop them and collide keys)."""
    parts = ", ".join(f"coalesce({prefix}{c}, '')" for c in TRACK_COLS)
    return f"md5(concat_ws('||', {parts}))"


def _sqlstr(s):
    """Single-quote a Python string for inlining into SQL (doubles embedded ')."""
    return "'" + str(s).replace("'", "''") + "'"


# ---- Config / manifest ---------------------------------------------------
OUT = os.environ.get("AG_OUT", "data/ag_db")
DIMS = f"{OUT}/dims"
MANIFEST = os.environ.get(
    "AG_REGIONS_MANIFEST", os.path.join(os.path.dirname(__file__), "regions.json")
)

MEM = os.environ.get("AG_MEM", "24GB")
THREADS = os.environ.get("AG_THREADS", "4")
TMP = os.environ.get("AG_TMP", "db/etl/duck_tmp")

# Build/provenance log written alongside the DB (travels with the data). Every
# ETL process appends to it, so a full build leaves one chronological record of
# which inputs were consumed and what was produced.
LOG = os.environ.get("AG_LOG", f"{OUT}/ag_db.log")


def log(msg):
    """Print and append a timestamped line to the ag_db build log."""
    os.makedirs(os.path.dirname(LOG) or ".", exist_ok=True)
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(line)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def load_regions():
    """Load and lightly validate the region manifest."""
    with open(MANIFEST) as fh:
        regions = json.load(fh)
    if not isinstance(regions, list) or not regions:
        raise ValueError(f"{MANIFEST}: expected a non-empty list of regions")
    seen = set()
    for r in regions:
        for k in ("region", "catalog", "ag"):
            if k not in r:
                raise ValueError(f"{MANIFEST}: region entry missing '{k}': {r}")
        if r["region"] in seen:
            raise ValueError(f"{MANIFEST}: duplicate region '{r['region']}'")
        seen.add(r["region"])
        for e in (2, 5, 20):
            if str(e) not in r["ag"]:
                raise ValueError(f"{MANIFEST}: region {r['region']} missing ag[{e}]")
            path = r["ag"][str(e)]
            if not AG_FILE_RE.search(os.path.basename(path)):
                raise ValueError(
                    f"{MANIFEST}: region {r['region']} ag[{e}] = '{path}' is not an "
                    f"AlphaGenome prediction file (must end in AG.tsv / AG.out.tsv / "
                    f"AG.sout.tsv). Only AG files may populate the ag_db."
                )
        # `repeat_type` is a free-form dataset label (e.g. 'TNR'), NOT load-bearing:
        # the authoritative per-repeat class is derived per variant (motif_class).
        r.setdefault("repeat_type", None)
        r.setdefault("notes", r["region"])
    return regions


def region_files(spec):
    """Every input file a region depends on (for the preflight existence check).
    No pathogenic file: the masked catalogs carry no disease info, and by design
    the ag_db holds none either."""
    return [spec["catalog"], *spec["ag"].values()]


def connect():
    con = duckdb.connect()
    con.execute(f"PRAGMA threads={THREADS}")
    con.execute(f"PRAGMA memory_limit='{MEM}'")
    con.execute(f"PRAGMA temp_directory='{TMP}'")
    con.execute("PRAGMA preserve_insertion_order=false")  # lower memory for COPY
    return con


def read_ag(path):
    """A read_csv() clause over one AG TSV; all_varchar so we control casts."""
    return (
        f"read_csv('{path}', delim='\t', header=true, sample_size=-1, "
        f"all_varchar=true, nullstr='')"
    )


def read_ag_multi(paths):
    """read_csv() over several AG TSVs unioned by name (columns may differ
    slightly across regions); used to derive the shared dims."""
    lst = ", ".join(f"'{p}'" for p in paths)
    return (
        f"read_csv([{lst}], delim='\t', header=true, sample_size=-1, "
        f"all_varchar=true, nullstr='', union_by_name=true)"
    )


def read_tsv(path):
    """read_csv() clause over a catalog / pathogenic TSV."""
    return (
        f"read_csv('{path}', delim='\t', header=true, sample_size=-1, "
        f"all_varchar=true, nullstr='')"
    )


def _columns(con, relation):
    """Column names of a read_csv relation (a 0-row probe is cheap for TSVs)."""
    return [d[0] for d in con.execute(f"SELECT * FROM {relation} LIMIT 0").description]


# ---- Dimensions ----------------------------------------------------------

def build_dims():
    regions = load_regions()
    os.makedirs(DIMS, exist_ok=True)
    os.makedirs(f"{DIMS}/variants", exist_ok=True)
    con = connect()
    ag_all = read_ag_multi([r["ag"]["2"] for r in regions])
    log(f"[dims] building shared dims from 2x files of regions: "
        f"{', '.join(r['region'] for r in regions)}")

    # regions --------------------------------------------------------------
    # `repeat_type` is the free-form dataset label; the per-variant motif_class
    # (in the variants dim) is the authoritative repeat classification.
    def _rt(r):
        return _sqlstr(r["repeat_type"]) if r["repeat_type"] else "CAST(NULL AS VARCHAR)"
    sel = " UNION ALL ".join(
        f"SELECT {_sqlstr(r['region'])} AS region, "
        f"{_rt(r)} AS repeat_type, "
        f"{_sqlstr(r['notes'])} AS notes"
        for r in regions
    )
    con.execute(f"COPY ({sel}) TO '{DIMS}/regions.parquet' (FORMAT parquet)")

    # output_types ---------------------------------------------------------
    con.execute(
        f"""COPY (
              SELECT output_type,
                     row_number() OVER (ORDER BY output_type) AS output_type_ord
              FROM (SELECT DISTINCT output_type FROM {ag_all}
                    WHERE output_type IS NOT NULL)
            ) TO '{DIMS}/output_types.parquet' (FORMAT parquet)"""
    )

    # scorers --------------------------------------------------------------
    # variant_scorer looks like:
    #   CenterMaskScorer(requested_output=ATAC, width=501, aggregation_type=DIFF_LOG2_SUM)
    # Family = text before "Scorer("; then pull the three named params (any may
    # be absent for some families → NULL via regexp_extract).
    con.execute(
        f"""COPY (
              SELECT
                row_number() OVER (ORDER BY variant_scorer) AS scorer_id,
                variant_scorer AS scorer_name,
                regexp_extract(variant_scorer, '^([A-Za-z0-9_]+?)Scorer', 1)
                    AS scorer_family,
                nullif(regexp_extract(variant_scorer,
                    'requested_output=([^,\\)]+)', 1), '') AS requested_output,
                TRY_CAST(nullif(regexp_extract(variant_scorer,
                    'width=([0-9]+)', 1), '') AS INTEGER) AS width,
                nullif(regexp_extract(variant_scorer,
                    'aggregation_type=([^,\\)]+)', 1), '') AS aggregation_type
              FROM (SELECT DISTINCT variant_scorer FROM {ag_all}
                    WHERE variant_scorer IS NOT NULL)
            ) TO '{DIMS}/scorers.parquet' (FORMAT parquet)"""
    )

    # tracks ---------------------------------------------------------------
    # Natural key = all 13 track columns together, hashed into `track_key` so the
    # fact join is one column. Blank track rows (splice/gene outputs) excluded.
    con.execute(
        f"""COPY (
              SELECT
                row_number() OVER (ORDER BY track_key) AS track_id,
                track_key, track_name, track_strand,
                "Assay title" AS assay_title, ontology_curie,
                biosample_name, biosample_type, biosample_life_stage,
                data_source, endedness, genetically_modified,
                transcription_factor, histone_mark, gtex_tissue
              FROM (
                SELECT DISTINCT {_track_key()} AS track_key,
                       track_name, track_strand, "Assay title", ontology_curie,
                       biosample_name, biosample_type, biosample_life_stage,
                       data_source, endedness, genetically_modified,
                       transcription_factor, histone_mark, gtex_tissue
                FROM {ag_all}
                WHERE track_name IS NOT NULL
              )
            ) TO '{DIMS}/tracks.parquet' (FORMAT parquet)"""
    )

    # genes (scored gene referenced per-row; deduped across regions) --------
    # AG `gene_id` (ensembl) is the natural key and is finer than gene_name.
    # Dedup on gene_id so the fact join can't fan out; name/type/strand are
    # functionally dependent (min() = any).
    con.execute(
        f"""COPY (
              SELECT
                row_number() OVER (ORDER BY gene_ensembl_id) AS gene_id,
                gene_ensembl_id, gene_name, gene_type, gene_strand
              FROM (
                SELECT gene_id AS gene_ensembl_id,
                       min(gene_name)   AS gene_name,
                       min(gene_type)   AS gene_type,
                       min(gene_strand) AS gene_strand
                FROM {ag_all}
                WHERE gene_id IS NOT NULL
                GROUP BY gene_id
              )
            ) TO '{DIMS}/genes.parquet' (FORMAT parquet)"""
    )

    # variants (one file per region, global variant_id offset) -------------
    offset = 0
    for spec in regions:
        offset += _build_variants(con, spec, offset)

    for t in ["regions", "output_types", "scorers", "tracks", "genes"]:
        n = con.execute(f"SELECT count(*) FROM '{DIMS}/{t}.parquet'").fetchone()[0]
        log(f"[dims]   {t:14s} {n:,} rows")
    for spec in regions:
        r = spec["region"]
        n = con.execute(
            f"SELECT count(*) FROM '{DIMS}/variants/{r}.parquet'"
        ).fetchone()[0]
        log(f"[dims]   variants[{r}] {n:,} rows")
    con.close()


def _build_variants(con, spec, offset):
    """Write one region's variants Parquet with global ids offset by `offset`;
    return the region's row count (so the caller advances the offset).

    Built from the masked catalog only — NO pathogenic/disease columns are added
    (by design the ag_db carries no pathogenic info)."""
    region = spec["region"]
    cat = read_tsv(spec["catalog"])
    cat_cols = _columns(con, cat)

    has_motif = "MotifID" in cat_cols
    motif_sel = "c.MotifID AS motif_id" if has_motif else \
        "CAST(NULL AS VARCHAR) AS motif_id"
    excl = PROMOTED + (["MotifID"] if has_motif else [])

    # motif_len / motif_class are derived from the canonical-motif length so the
    # classification is per-variant and future-proof (tetra-, penta-nucleotide …)
    # rather than a region-wide assumption.
    con.execute(
        f"""COPY (
              SELECT
                row_number() OVER (ORDER BY c.LocusId) + {offset} AS variant_id,
                c.LocusId                     AS locus_id,
                {_sqlstr(region)}             AS region,
                c.CanonicalMotif              AS canonical_motif,
                {motif_sel},
                length(c.CanonicalMotif)      AS motif_len,
                {_motif_class_sql('c.CanonicalMotif')} AS motif_class,
                c.GencodeGeneName             AS host_gene_name,
                c.GencodeGeneId               AS host_gene_id,
                c.GencodeGeneRegion           AS gencode_gene_region,
                c.* EXCLUDE ({", ".join(excl)})
              FROM {cat} c
            ) TO '{DIMS}/variants/{region}.parquet' (FORMAT parquet)"""
    )
    n = con.execute(
        f"SELECT count(*) FROM '{DIMS}/variants/{region}.parquet'"
    ).fetchone()[0]
    classes = con.execute(
        f"""SELECT motif_class || '=' || count(*)
            FROM '{DIMS}/variants/{region}.parquet'
            GROUP BY motif_class ORDER BY count(*) DESC"""
    ).fetchall()
    log(f"[dims] variants[{region}] <- {spec['catalog']} : {n:,} rows "
        f"(variant_id {offset + 1}..{offset + n}; motif_id="
        f"{'yes' if has_motif else 'null'}; "
        f"motif_class {', '.join(c[0] for c in classes)})")
    return n


# ---- Fact ----------------------------------------------------------------

def build_fact(spec, expansion):
    region = spec["region"]
    ag = read_ag(spec["ag"][str(expansion)])

    # Idempotent: drop this (region, expansion)'s partitions so a rerun can't
    # duplicate rows (APPEND below only avoids clobbering the *other* partitions).
    for d in glob.glob(f"{OUT}/ag_scores/region={region}/expansion={expansion}"):
        shutil.rmtree(d, ignore_errors=True)

    con = connect()
    # Load small dims into memory for the joins; fact streams from the TSV.
    con.execute(
        f"CREATE TEMP TABLE variants AS "
        f"SELECT variant_id, locus_id FROM '{DIMS}/variants/{region}.parquet'"
    )
    con.execute(f"CREATE TEMP TABLE scorers AS SELECT scorer_id, scorer_name FROM '{DIMS}/scorers.parquet'")
    con.execute(f"CREATE TEMP TABLE genes   AS SELECT gene_id, gene_ensembl_id FROM '{DIMS}/genes.parquet'")
    con.execute(f"CREATE TEMP TABLE tracks  AS SELECT track_id, track_key FROM '{DIMS}/tracks.parquet'")

    con.execute(
        f"""
        COPY (
          SELECT
            v.variant_id,
            {_sqlstr(region)}                AS region,
            {expansion}                      AS expansion,
            r.output_type,
            s.scorer_id,
            t.track_id,
            g.gene_id,
            TRY_CAST(r.junction_Start AS INTEGER) AS junction_start,
            TRY_CAST(r.junction_End   AS INTEGER) AS junction_end,
            TRY_CAST(r.raw_score      AS DOUBLE)  AS raw_score,
            TRY_CAST(r.quantile_score AS DOUBLE)  AS quantile_score
          FROM {ag} r
          JOIN variants v ON r.original_variant_id = v.locus_id
          JOIN scorers  s ON r.variant_scorer      = s.scorer_name
          LEFT JOIN genes  g ON r.gene_id          = g.gene_ensembl_id
          LEFT JOIN tracks t ON t.track_key        = {_track_key('r.')}
        ) TO '{OUT}/ag_scores'
          (FORMAT parquet, PARTITION_BY (region, expansion, output_type),
           COMPRESSION zstd, APPEND, FILENAME_PATTERN 'e{expansion}_{region}_{{uuid}}')
        """
    )
    n = con.execute(
        f"SELECT count(*) FROM '{OUT}/ag_scores/region={region}/expansion={expansion}/**/*.parquet'"
    ).fetchone()[0]
    log(f"[fact] {region} {expansion}x <- {spec['ag'][str(expansion)]} : "
        f"{n:,} rows written")
    con.close()


# ---- Preflight -----------------------------------------------------------

def preflight():
    regions = load_regions()
    log(f"[preflight] ===== ETL run start; manifest: {MANIFEST} =====")
    missing = []
    for spec in regions:
        log(f"[preflight] region {spec['region']} "
            f"(repeat_type={spec['repeat_type'] or 'n/a'}):")
        for f in region_files(spec):
            if os.path.exists(f):
                st = os.stat(f)
                mt = datetime.datetime.fromtimestamp(st.st_mtime)
                log(f"[preflight]   OK   {f}  ({st.st_size/1e9:.2f} GB, "
                    f"mtime {mt:%Y-%m-%d %H:%M})")
            else:
                log(f"[preflight]   MISS {f}")
                missing.append(f)
    if missing:
        raise SystemExit(
            f"[preflight] {len(missing)} input file(s) missing — a full rebuild "
            f"needs every region's TSVs. Restore them and rerun:\n  "
            + "\n  ".join(missing)
        )
    log("[preflight] all inputs present.")


# ---- CLI -----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["preflight", "regions", "dims", "fact", "all"])
    ap.add_argument("--region", help="limit fact build to one region")
    ap.add_argument("--expansion", type=int, choices=[2, 5, 20])
    args = ap.parse_args()

    os.makedirs(TMP, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    if args.stage == "regions":
        print(" ".join(r["region"] for r in load_regions()))
        return
    if args.stage == "preflight":
        preflight()
        return
    if args.stage in ("dims", "all"):
        print("[dims]")
        build_dims()
    if args.stage in ("fact", "all"):
        regions = load_regions()
        if args.region:
            regions = [r for r in regions if r["region"] == args.region]
            if not regions:
                raise SystemExit(f"--region {args.region} not in manifest")
        exps = [args.expansion] if args.expansion else [2, 5, 20]
        for spec in regions:
            for e in exps:
                print(f"[fact {spec['region']} {e}x]")
                build_fact(spec, e)


if __name__ == "__main__":
    main()
