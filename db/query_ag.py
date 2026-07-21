#!/usr/bin/env python
"""query_ag — DuckDB-backed query tool over the AlphaGenome star schema.

This is the agent's single entry point to the ~309 M-row AlphaGenome dataset
(db/AG_DB_DESIGN.md §6). It opens an in-process, read-only DuckDB over the
partitioned Parquet backend at ``data/ag_db/`` and exposes these views:

    ag_scores     fact: one row per AG record (variant × output_type × scorer
                  × track), dimensions replaced by integer FKs. Partition
                  columns region / expansion / output_type are queryable.
    variants      6.6k repeat loci + all catalog attributes + is_pathogenic/disease
    tracks        ~5k assay/biosample tracks
    scorers       19 variant scorers (family / requested_output / width / aggregation)
    genes         scored genes referenced per-row by ag_scores.gene_id (nullable)
    output_types  the 11 AG output types
    regions       region lookup (5UTR, …)

Two modes (§8.2):
  * inspect (default): returns a pandas DataFrame capped at ``limit`` (1000)
    rows — for sampling and strategy development. The cap limits the payload
    into context, NOT the computation: DuckDB still scans all rows, so
    GROUP BY / COUNT / AVG aggregations run full-dataset and return small
    results. If the result is truncated you get a note telling you to aggregate
    or use ``to_file``.
  * materialize (``to_file=...``): writes the FULL result to Parquet/CSV (by
    extension) and returns only a small head sample — for large derived tables
    (per-variant scores, candidate lists) that shouldn't enter context.

CLI (for testing):
    python db/query_ag.py --schema
    python db/query_ag.py "SELECT output_type, count(*) FROM ag_scores GROUP BY 1"
    python db/query_ag.py --to-file /tmp/x.parquet "SELECT * FROM ag_scores WHERE expansion=20"
"""
import os
import textwrap
import duckdb
import pandas as pd

AG_DB = os.environ.get("AG_DB", "data/ag_db")
ROW_CAP = int(os.environ.get("AG_QUERY_ROW_CAP", "1000"))
_MEM = os.environ.get("AG_QUERY_MEM", "16GB")
_THREADS = os.environ.get("AG_QUERY_THREADS", "4")

_DIMS = ["variants", "tracks", "scorers", "genes", "output_types", "regions"]


def get_connection(db=AG_DB):
    """Open a read-only in-process DuckDB with views over the backend."""
    if not os.path.isdir(db):
        raise FileNotFoundError(
            f"AG backend not found at '{db}'. Build it first: "
            f"sbatch db/etl/build_ag_db.sbatch (then db/etl/validate.py)."
        )
    con = duckdb.connect()
    con.execute(f"PRAGMA threads={_THREADS}")
    con.execute(f"PRAGMA memory_limit='{_MEM}'")
    # Fact: hive_partitioning re-adds region/expansion/output_type from the path.
    con.execute(
        f"""CREATE VIEW ag_scores AS
            SELECT * FROM read_parquet('{db}/ag_scores/**/*.parquet',
                                       hive_partitioning=1)"""
    )
    for d in _DIMS:
        p = f"{db}/dims/{d}.parquet"
        if os.path.exists(p):
            con.execute(f"CREATE VIEW {d} AS SELECT * FROM read_parquet('{p}')")
    return con


def query_ag(sql, to_file=None, limit=ROW_CAP, db=AG_DB):
    """Run SQL against the AlphaGenome backend.

    Args:
        sql: a single SELECT statement referencing the views above.
        to_file: if given (``.parquet`` or ``.csv``), write the FULL result
            there and return only a head sample. Use for large derived tables.
        limit: inspect-mode row cap returned to context (default 1000).
        db: backend directory (default data/ag_db).

    Returns:
        pandas.DataFrame — the capped result (inspect) or a head sample of the
        written file (materialize). Notes are printed to stdout.
    """
    con = get_connection(db)
    try:
        if to_file:
            ext = os.path.splitext(to_file)[1].lower()
            fmt = "csv" if ext == ".csv" else "parquet"
            opts = "FORMAT csv, HEADER" if fmt == "csv" else "FORMAT parquet"
            os.makedirs(os.path.dirname(os.path.abspath(to_file)), exist_ok=True)
            con.execute(f"COPY ({sql}) TO '{to_file}' ({opts})")
            n = con.execute(
                f"SELECT count(*) FROM read_{fmt}('{to_file}')"
            ).fetchone()[0]
            head = con.execute(
                f"SELECT * FROM read_{fmt}('{to_file}') LIMIT {limit}"
            ).df()
            print(f"[query_ag] wrote {n:,} rows to {to_file} "
                  f"(showing head {len(head)}). Read summaries from the file; "
                  f"don't pull all rows into context.")
            return head

        # inspect mode: fetch limit+1 to detect truncation without a count.
        df = con.execute(f"SELECT * FROM ({sql}) AS _q LIMIT {limit + 1}").df()
        if len(df) > limit:
            total = con.execute(
                f"SELECT count(*) FROM ({sql}) AS _q"
            ).fetchone()[0]
            df = df.head(limit)
            print(f"[query_ag] TRUNCATED: {total:,} rows total, returning first "
                  f"{limit}. Aggregate (GROUP BY/COUNT/AVG) or pass "
                  f"to_file='out.parquet' to materialize the full result.")
        return df
    finally:
        con.close()


def schema_doc(db=AG_DB):
    """Return a human/LLM-readable schema + example queries for the prompt."""
    lines = [SCHEMA_DOC]
    try:
        con = get_connection(db)
        try:
            lines.append("\nLive column listing:")
            for v in ["ag_scores"] + _DIMS:
                try:
                    cols = con.execute(f"DESCRIBE {v}").df()
                    cs = ", ".join(
                        f"{r['column_name']}:{r['column_type']}"
                        for _, r in cols.iterrows()
                    )
                    lines.append(f"  {v}({cs})")
                except duckdb.Error:
                    pass
        finally:
            con.close()
    except FileNotFoundError as e:
        lines.append(f"\n[backend not built yet: {e}]")
    return "\n".join(lines)


SCHEMA_DOC = textwrap.dedent(
    """\
    == AlphaGenome backend (query with the `query_ag` tool) ==
    A DuckDB/Parquet star schema of AlphaGenome expansion predictions for 5'UTR
    GCN tandem repeats. Query it with SQL via `query_ag(sql, to_file=None)`;
    never read the raw TSVs. The default result cap is 1000 rows — the cap is on
    ROWS RETURNED TO YOU, not the computation, so aggregate freely (DuckDB scans
    all ~309M rows). For large per-row derived outputs pass `to_file=`.

    Tables (views):
      ag_scores(variant_id, region, expansion, output_type, scorer_id, track_id,
                gene_id, junction_start, junction_end, raw_score, quantile_score)
          Grain = variant × output_type × scorer × track. region/expansion/
          output_type are partitions (fast to filter). gene_id/track_id are NULL
          for non-genic / non-tracked outputs. expansion ∈ {2,5,20}.
      variants(variant_id, locus_id, region, canonical_motif, motif_id,
               host_gene_name, host_gene_id, gencode_gene_region, is_pathogenic,
               disease, + all B-catalog attributes)
      tracks(track_id, track_key, track_name, track_strand, assay_title,
             ontology_curie, biosample_name, biosample_type, biosample_life_stage,
             data_source, endedness, genetically_modified, transcription_factor,
             histone_mark, gtex_tissue)
      scorers(scorer_id, scorer_name, scorer_family, requested_output, width,
              aggregation_type)
      genes(gene_id, gene_ensembl_id, gene_name, gene_type, gene_strand)
      output_types(output_type, output_type_ord)
      regions(region, motif_class, notes)

    Example queries:
      -- pathogenic vs background mean RNA_SEQ effect per expansion
      SELECT s.expansion,
             v.is_pathogenic,
             avg(s.raw_score) AS mean_raw,
             count(*)         AS n
      FROM ag_scores s JOIN variants v USING (variant_id)
      WHERE s.output_type='RNA_SEQ'
      GROUP BY 1,2 ORDER BY 1,2;

      -- top loci by max |raw_score| at 20x for CAGE
      SELECT v.locus_id, v.host_gene_name, max(abs(s.raw_score)) AS max_abs
      FROM ag_scores s JOIN variants v USING (variant_id)
      WHERE s.expansion=20 AND s.output_type='CAGE'
      GROUP BY 1,2 ORDER BY max_abs DESC LIMIT 20;

      -- materialize a full per-variant score table (don't pull into context)
      query_ag("SELECT variant_id, output_type, avg(raw_score) r "
               "FROM ag_scores GROUP BY 1,2", to_file="per_variant.parquet")
    """
)


def _main():
    import argparse
    ap = argparse.ArgumentParser(description="Query the AG DuckDB backend.")
    ap.add_argument("sql", nargs="?", help="SQL SELECT to run")
    ap.add_argument("--to-file", default=None)
    ap.add_argument("--limit", type=int, default=ROW_CAP)
    ap.add_argument("--schema", action="store_true", help="print schema + exit")
    ap.add_argument("--db", default=AG_DB)
    args = ap.parse_args()
    if args.schema or not args.sql:
        print(schema_doc(args.db))
        return
    df = query_ag(args.sql, to_file=args.to_file, limit=args.limit, db=args.db)
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(df.to_string(max_rows=args.limit))


if __name__ == "__main__":
    _main()
