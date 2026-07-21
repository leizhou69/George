#!/usr/bin/env python
"""Phase-4 prototype exploration: minimal streaming passes over one AG TSV.

Enumerates every distinct `variant_scorer` / `output_type` (to finalize the
scorers/output_types dims) and measures cardinalities + per-output_type gene
population. Three full scans total; read-only. Run unbuffered:

    python -u db/etl/explore.py [path/to/AG.tsv]
"""
import sys
import time
import duckdb

AG = sys.argv[1] if len(sys.argv) > 1 else "data/5UTR/B_5UTR_all_GCN_2xAG.tsv"

con = duckdb.connect()
con.execute("PRAGMA threads=4")
con.execute("PRAGMA memory_limit='24GB'")
con.execute("PRAGMA temp_directory='db/etl/duck_tmp'")
RAW = (f"read_csv('{AG}', delim='\t', header=true, sample_size=-1, "
       f"all_varchar=true, nullstr='')")


def scan(label, sql):
    t = time.time()
    rows = con.execute(sql).fetchall()
    print(f"[scan {label}: {time.time()-t:.0f}s]", flush=True)
    return rows


print(f"== File: {AG} ==", flush=True)

# Scan 1: one pass, all counts together.
r = scan("counts", f"""
    SELECT count(*),
           count(DISTINCT original_variant_id),
           count(DISTINCT output_type),
           count(DISTINCT variant_scorer),
           count(DISTINCT track_name),
           count(DISTINCT gene_name),
           count(DISTINCT gene_id)
    FROM {RAW}""")[0]
labels = ["rows", "variants", "output_types", "scorers", "track_names",
          "gene_names", "gene_ids"]
for lab, v in zip(labels, r):
    print(f"  {lab:14s} {v:,}", flush=True)

# Scan 2: per-output_type distribution + gene-blank share (one pass).
print("\n== output_type: rows / blank-gene ==", flush=True)
for ot, c, blank in scan("by_output_type", f"""
    SELECT output_type, count(*),
           sum(CASE WHEN gene_name IS NULL THEN 1 ELSE 0 END)
    FROM {RAW} GROUP BY 1 ORDER BY 2 DESC"""):
    print(f"  {ot:20s} rows={c:>13,}  blank_gene={blank:>13,}", flush=True)

# Scan 3: the distinct scorer strings (drives the scorers-dim parse).
print("\n== distinct variant_scorer ==", flush=True)
for (vs,) in scan("scorers", f"SELECT DISTINCT variant_scorer FROM {RAW} ORDER BY 1"):
    print(f"  {vs}", flush=True)

con.close()
