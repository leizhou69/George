#!/usr/bin/env python
"""AlphaGenome → DuckDB/Parquet star-schema ETL (upgrade.md Phase 4).

Builds the backend described in db/AG_DB_DESIGN.md:

    data/ag_db/
      dims/{variants,tracks,scorers,genes,output_types,regions}.parquet
      ag_scores/region=<R>/expansion=<E>/output_type=<OT>/part-*.parquet

DuckDB streams the ~30 GB TSVs directly (columnar, spills to disk), so this
runs inside a modest allocation. Dimensions are built from the 2x file only
(tracks/scorers/genes/output_types are identical across expansions — only the
variant allele differs), then the fact is built per expansion.

Run from the George repo root:
    python db/etl/etl.py dims                 # build dimension parquets
    python db/etl/etl.py fact --expansion 2   # build one expansion's fact
    python db/etl/etl.py fact                  # build all three expansions
    python db/etl/etl.py all                    # dims + all expansions

Knobs via env: AG_MEM (default 24GB), AG_THREADS (default 4), AG_TMP.
"""
import argparse
import os
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


def _track_key(prefix=""):
    """md5(concat_ws) over the 13 track cols; coalesce first so NULLs are kept
    positionally (concat_ws would otherwise drop them and collide keys)."""
    parts = ", ".join(f"coalesce({prefix}{c}, '')" for c in TRACK_COLS)
    return f"md5(concat_ws('||', {parts}))"

# ---- Region config (env-overridable so the same ETL onboards 3UTR etc.) ---
REGION = os.environ.get("AG_REGION", "5UTR")
MOTIF_CLASS = os.environ.get("AG_MOTIF_CLASS", "GCN")
DATA = os.environ.get("AG_DATA_DIR", "data/5UTR")
CATALOG = os.environ.get("AG_CATALOG", f"{DATA}/B_Cat_5UTR_GCNs_masked.tsv")
PATHOGENIC = os.environ.get("AG_PATHOGENIC", f"{DATA}/B_5UTR_Pathogenic_GCN.txt")
AG_FILES = {
    2: os.environ.get("AG_2X", f"{DATA}/B_5UTR_all_GCN_2xAG.tsv"),
    5: os.environ.get("AG_5X", f"{DATA}/B_5UTR_all_GCN_5xAG.tsv"),
    20: os.environ.get("AG_20X", f"{DATA}/B_5UTR_all_GCN_20xAG.tsv"),
}
OUT = os.environ.get("AG_OUT", "data/ag_db")
DIMS = f"{OUT}/dims"

MEM = os.environ.get("AG_MEM", "24GB")
THREADS = os.environ.get("AG_THREADS", "4")
TMP = os.environ.get("AG_TMP", "db/etl/duck_tmp")


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


# ---- Dimensions ----------------------------------------------------------

def build_dims():
    os.makedirs(DIMS, exist_ok=True)
    con = connect()
    ag = read_ag(AG_FILES[2])

    # regions ---------------------------------------------------------------
    con.execute(
        f"""COPY (SELECT '{REGION}' AS region, '{MOTIF_CLASS}' AS motif_class,
                         '5-prime UTR GCN tandem repeats' AS notes)
            TO '{DIMS}/regions.parquet' (FORMAT parquet)"""
    )

    # output_types ----------------------------------------------------------
    con.execute(
        f"""COPY (
              SELECT output_type,
                     row_number() OVER (ORDER BY output_type) AS output_type_ord
              FROM (SELECT DISTINCT output_type FROM {ag}
                    WHERE output_type IS NOT NULL)
            ) TO '{DIMS}/output_types.parquet' (FORMAT parquet)"""
    )

    # scorers ---------------------------------------------------------------
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
              FROM (SELECT DISTINCT variant_scorer FROM {ag}
                    WHERE variant_scorer IS NOT NULL)
            ) TO '{DIMS}/scorers.parquet' (FORMAT parquet)"""
    )

    # tracks ----------------------------------------------------------------
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
                FROM {ag}
                WHERE track_name IS NOT NULL
              )
            ) TO '{DIMS}/tracks.parquet' (FORMAT parquet)"""
    )

    # genes (scored gene referenced per-row) --------------------------------
    # AG `gene_id` (ensembl) is the natural key and is finer than gene_name
    # (19,695 ids vs 19,269 names). Dedup on gene_id so the fact join can't
    # fan out; name/type/strand are functionally dependent (min() = any).
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
                FROM {ag}
                WHERE gene_id IS NOT NULL
                GROUP BY gene_id
              )
            ) TO '{DIMS}/genes.parquet' (FORMAT parquet)"""
    )

    # variants (catalog ⨝ pathogenic) --------------------------------------
    cat = (
        f"read_csv('{CATALOG}', delim='\t', header=true, sample_size=-1, "
        f"all_varchar=true, nullstr='')"
    )
    pat = (
        f"read_csv('{PATHOGENIC}', delim='\t', header=true, sample_size=-1, "
        f"all_varchar=true, nullstr='')"
    )
    con.execute(
        f"""COPY (
              SELECT
                row_number() OVER (ORDER BY c.LocusId) AS variant_id,
                c.LocusId                     AS locus_id,
                '{REGION}'                    AS region,
                c.CanonicalMotif              AS canonical_motif,
                c.MotifID                     AS motif_id,
                c.GencodeGeneName             AS host_gene_name,
                c.GencodeGeneId               AS host_gene_id,
                c.GencodeGeneRegion           AS gencode_gene_region,
                (p.LocusId IS NOT NULL)       AS is_pathogenic,
                p.KnownDiseaseAssociatedLocus AS disease,
                c.* EXCLUDE (LocusId, CanonicalMotif, MotifID, GencodeGeneName,
                             GencodeGeneId, GencodeGeneRegion)
              FROM {cat} c
              LEFT JOIN {pat} p USING (LocusId)
            ) TO '{DIMS}/variants.parquet' (FORMAT parquet)"""
    )

    for t in ["regions", "output_types", "scorers", "tracks", "genes", "variants"]:
        n = con.execute(f"SELECT count(*) FROM '{DIMS}/{t}.parquet'").fetchone()[0]
        print(f"  dim {t:14s} {n:,} rows")
    con.close()


# ---- Fact ----------------------------------------------------------------

def build_fact(expansion):
    ag = read_ag(AG_FILES[expansion])

    # Idempotent: drop this expansion's partitions so a rerun can't duplicate
    # rows (APPEND below only avoids clobbering the *other* expansions).
    for d in glob.glob(f"{OUT}/ag_scores/region={REGION}/expansion={expansion}"):
        shutil.rmtree(d, ignore_errors=True)

    con = connect()
    # Load small dims into memory for the joins; fact streams from the TSV.
    con.execute(f"CREATE TEMP TABLE variants AS SELECT variant_id, locus_id FROM '{DIMS}/variants.parquet'")
    con.execute(f"CREATE TEMP TABLE scorers  AS SELECT scorer_id, scorer_name FROM '{DIMS}/scorers.parquet'")
    con.execute(f"CREATE TEMP TABLE genes    AS SELECT gene_id, gene_ensembl_id FROM '{DIMS}/genes.parquet'")
    con.execute(f"CREATE TEMP TABLE tracks   AS SELECT track_id, track_key FROM '{DIMS}/tracks.parquet'")

    con.execute(
        f"""
        COPY (
          SELECT
            v.variant_id,
            '{REGION}'                       AS region,
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
           COMPRESSION zstd, APPEND, FILENAME_PATTERN 'e{expansion}_{{uuid}}')
        """
    )
    n = con.execute(
        f"SELECT count(*) FROM '{OUT}/ag_scores/region={REGION}/expansion={expansion}/**/*.parquet'"
    ).fetchone()[0]
    print(f"  fact expansion {expansion}x written: {n:,} rows")
    con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["dims", "fact", "all"])
    ap.add_argument("--expansion", type=int, choices=[2, 5, 20])
    args = ap.parse_args()

    os.makedirs(TMP, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    if args.stage in ("dims", "all"):
        print("[dims]")
        build_dims()
    if args.stage in ("fact", "all"):
        exps = [args.expansion] if args.expansion else [2, 5, 20]
        for e in exps:
            print(f"[fact {e}x]")
            build_fact(e)


if __name__ == "__main__":
    main()
