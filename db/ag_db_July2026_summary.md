# AG DuckDB/Parquet backend — state summary (July 2026)

Snapshot of `data/ag_db/` as built on **2026-07-23** (verified 2026-07-24).
Companion to `AG_DB_DESIGN.md` (design) and `db_construction.md` (how to rebuild).
This file is a point-in-time reference; the authoritative provenance is the
append-only `data/ag_db/ag_db.log`.

## What it holds

A **multi-region** AlphaGenome (AG) expansion-prediction store as a Hive-partitioned
Parquet star schema, queried through `db/query_ag.py`. Three gene regions × three
tandem-repeat expansion factors, all TNR / trinucleotide loci:

| region | 2× | 5× | 20× | region total |
|---|--:|--:|--:|--:|
| 5UTR | 155,250,960 | 156,846,562 | 156,454,819 | 468,552,341 |
| CDS  | 540,775,685 | 542,290,915 | 529,907,274 | 1,612,973,874 |
| 3UTR | 266,258,073 | 269,050,484 | 265,533,786 | 800,842,343 |
| **all** | | | | **2,882,368,558** |

On-disk size **≈ 19 GB** (zstd Parquet), 99 fact parquet files. Fact row counts
above match `ag_db.log` exactly and every fact row joins to a variant (100%
coverage after the fix noted below).

## Layout

```
data/ag_db/
  ag_scores/region=<R>/expansion=<E>/output_type=<OT>/e<E>_<R>_<uuid>.parquet
  dims/
    variants/<region>.parquet     one per region (5UTR, CDS, 3UTR); union_by_name
    regions.parquet  output_types.parquet  scorers.parquet
    tracks.parquet    genes.parquet
  ag_db.log                        append-only build/provenance log
```

Partition axes (`region / expansion / output_type`) match the paper's analysis
axes so the agent scans only what a query needs.

## Dimensions

| dim | rows | notes |
|---|--:|---|
| regions | 3 | 5UTR, CDS, 3UTR (all `repeat_type=TNR`) |
| output_types | 11 | ATAC, CAGE, CHIP_HISTONE, CHIP_TF, CONTACT_MAPS, DNASE, PROCAP, RNA_SEQ, SPLICE_JUNCTIONS, SPLICE_SITES, SPLICE_SITE_USAGE |
| scorers | 19 | families: CenterMask (12), GeneMaskSplicing (2), GeneMaskLFC, GeneMaskActive, ContactMap, Polyadenylation, SpliceJunction |
| tracks | 5,563 | 13-column natural key hashed into `track_key` |
| genes | 47,502 | deduped by ensembl `gene_id` |
| variants — 5UTR | 10,053 | `variant_id` 1–10,053 |
| variants — CDS | 34,891 | `variant_id` 10,054–44,944 |
| variants — 3UTR | 17,020 | `variant_id` 44,945–61,964 |
| **variants — total** | **61,964** | contiguous global ids 1–61,964 |

Variant ids are a single global surrogate-key space (offset per region), which is
why the fact must be **fully rebuilt** whenever the region set changes.

## Schema

`ag_scores` (fact) columns: `variant_id`, `scorer_id`, `track_id`, `gene_id`
(FKs), `junction_start`, `junction_end`, `raw_score` (DOUBLE), `quantile_score`
(DOUBLE, in [-1, 1]), plus partition columns `region`, `expansion`,
`output_type`. `raw_score` is unbounded (observed 5UTR 2× range ≈ −6 … 4.8e5).

`variants` (per region, 41 columns) carries `locus_id`, `region`,
`canonical_motif`, `motif_id`, `motif_len`, `motif_class`, host-gene fields, and
the full masked catalog attributes. **No `is_pathogenic` / `disease` columns** —
by design the ag_db carries no disease labels (the masked catalogs supply none;
pathogenic annotation is joined in downstream, outside this DB).

## Provenance (2026-07-23 build)

Built by `db/etl/etl.py` (manifest `db/etl/regions.json`) from ~1.65 TB of source
AG TSVs. The completed run ran preflight → shared dims → 9 facts between 19:19 and
21:54. Two earlier same-day runs were partial/aborted (the first reached only 5UTR
facts); the final 19:19 run is a clean full rebuild and is what the DB reflects.
Source TSVs are retained under `data/{5UTR,CDS,3UTR}/`.

## Fixed defect (2026-07-24)

A stale single-file `dims/variants.parquet` (6,650-row, 5UTR-only, from an old
2026-07-21 single-region build) was shadowing the per-region `dims/variants/`
directory: `query_ag.get_connection()` prefers `dims/<d>.parquet` over
`dims/<d>/*.parquet`, so the `variants` view resolved to 6,650 rows and only
**11%** of fact rows joined to a variant (all CDS/3UTR and the corrected 5UTR
catalog were invisible). Fixes applied:

1. Removed the stale `dims/variants.parquet` → `variants` view now 61,964 rows,
   fact join coverage 100%.
2. Hardened `etl.py::build_dims()` to delete any stale single-file
   `dims/variants.parquet` at the start of a build so it can't recur.

## Querying

```python
import sys; sys.path.insert(0, "db")
from query_ag import query_ag, get_connection, schema_doc
# inspect mode: returns ≤1,000 rows to context
df = query_ag("SELECT region, expansion, count(*) FROM ag_scores GROUP BY 1,2")
# materialize mode: full result to a file, keeps big output out of context
query_ag("SELECT ... FROM ag_scores s JOIN variants v USING(variant_id) WHERE ...",
         to_file="out.parquet")
```

Views available: `ag_scores`, `variants`, `tracks`, `scorers`, `genes`,
`output_types`, `regions`. Backend dir overridable via env `AG_DB` (default
`data/ag_db`).

## Rebuild

See `db_construction.md`. In short, from repo root with `biomni_e1` active:

```bash
sbatch db/etl/build_ag_db.sbatch      # preflight → dims → all region×expansion facts
python db/etl/validate.py             # row counts vs source, spot checks
```
