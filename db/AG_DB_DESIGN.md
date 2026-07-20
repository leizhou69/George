# AlphaGenome Data Backend — Design & Plan

Status: **proposal (design only, no code yet)** · Author: agent-assisted · Target: DuckDB over partitioned Parquet

## 1. Problem

The AlphaGenome (AG) prediction dumps are the bottleneck for scaling the
5'UTR-TNR pipeline (see `ms/5UTR_TNR_0605.pdf`) to other gene regions.

- Per region, three files (`_2xAG`, `_5xAG`, `_20xAG`), each **~29 GB / ~103 M rows**
  → **~87 GB / ~309 M rows for 5'UTR alone**.
- Heavily **denormalized**: grain is `variant × output_type × variant_scorer ×
  track`; only ~24 distinct variants per 500 k rows (~15 k rows/variant). Track
  and assay metadata (file columns 11–23) repeat billions of times.
- The Biomni agent cannot `read_csv` these even on 420 GB RAM, and each new
  region (3'UTR is staged; exon/intron next) multiplies the volume.

**Goal:** a compact, queryable backend the agent hits with SQL for subsets,
that grows cleanly as new regions are added.

## 2. Chosen approach

**DuckDB (embedded SQL) over a partitioned-Parquet star schema.**

Rationale vs PostgreSQL (which was considered): no daemon to run on SLURM,
columnar + larger-than-RAM streaming, direct Parquet reads, ~1–2 GB compressed
footprint, one `pip/conda install`, and the agent still gets full SQL. Postgres
would add a user-space server to babysit for no analytical benefit here. The
Parquet layer is engine-agnostic, so a Postgres loader can be added later if a
standing shared server is ever needed.

Prereqs: `pyarrow` (present) + `duckdb` (install: `conda install -c conda-forge
python-duckdb` or `pip install duckdb`). No root, no server.

## 3. Schema (star)

### Fact — `ag_scores`
One row per raw AG record, with dimensions replaced by integer FKs.

| column | type | notes |
|---|---|---|
| `variant_id` | int32 FK → variants | from `original_variant_id` |
| `region` | string (partition) | `5UTR`, `3UTR`, … |
| `expansion` | int8 (partition) | `2`, `5`, `20` |
| `output_type` | string (partition) | `RNA_SEQ`, `SPLICE_JUNCTIONS`, … (11) |
| `scorer_id` | int16 FK → scorers | parsed from `variant_scorer` |
| `track_id` | int32 FK → tracks | from `track_name` (+strand) |
| `gene_id` | int32 **null** FK → genes | **scored gene** for this row; null for non-genic outputs (ATAC/DNASE/CHIP_TF/CHIP_HISTONE/CAGE/PROCAP/CONTACT_MAPS). A variant is scored against **many** genes (up to ~16), so this is per-row, not per-variant. |
| `junction_start` | int32 null | only for splice rows |
| `junction_end` | int32 null | only for splice rows |
| `raw_score` | double | effect size |
| `quantile_score` | double | empirical position |

Estimate: 309 M rows × ~30–40 B → **~4 GB uncompressed / ~1–2 GB Parquet.**

### Dimensions (small, shared across regions)
- **`variants`** (~6.6 k for 5'UTR) — PK `variant_id`; `locus_id`
  (`chrom-start-end-motif`), `region`, `canonical_motif`, `motif_id`,
  **host** gene from the catalog (`host_gene_name` = `GencodeGeneName`,
  `host_gene_id`, `gencode_gene_region`) — i.e. the gene the repeat *sits in*,
  distinct from the per-row *scored* gene in the `genes` dim —
  `is_pathogenic` (bool), `disease` (from pathogenic file), **plus all B-catalog
  attributes** (mappability, `NumRepeatsInReference`, `ReferenceRepeatPurity`,
  allele-freq stdevs, `VariationCluster*`, etc. — cols 1–31 of
  `B_Cat_5UTR_GCNs_masked.tsv`). Source = catalog ⨝ pathogenic file (7 flagged).
- **`tracks`** (~5 k) — PK `track_id`; `track_name`, `track_strand`,
  `assay_title`, `ontology_curie`, `biosample_name`, `biosample_type`,
  `biosample_life_stage`, `data_source`, `endedness`, `genetically_modified`,
  `transcription_factor`, `histone_mark`, `gtex_tissue` (the last three are
  conditionally populated — 9–14 % — which is exactly why they belong here, not
  in the fact).
- **`genes`** — PK `gene_id`; `gene_name`, `gene_ensembl_id`, `gene_type`,
  `gene_strand`. The **scored gene** referenced by the fact's `gene_id`. Distinct
  from the variant's *host* gene (below): one repeat is scored against many
  neighboring genes, so this dimension holds every gene appearing in the AG
  `gene_name`/`gene_id` columns (est. a few thousand). Deduped across regions.
- **`scorers`** (19) — PK `scorer_id`; `scorer_name`, `scorer_family`
  (GeneMask/CenterMask/Splice/Polyadenylation…), `requested_output`, `width`,
  `aggregation_type` — parsed from the `variant_scorer` string.
- **`output_types`** (11) — enum kept as a partition string + a lookup table.
- **`regions`** — `region`, `motif_class` (e.g. GCN), notes.

Join key confirmed: AG `original_variant_id` == catalog `LocusId` == pathogenic
`LocusId` (`chrom-start-end-motif`), so the fact→variant join is exact.

## 4. Layout & partitioning

Hive-partitioned Parquet for predicate pushdown (agent scans only what it needs):

```
Rpt_Ds/data/ag_db/
  ag_scores/region=5UTR/expansion=2/output_type=RNA_SEQ/part-*.parquet
  ...
  dims/variants.parquet  tracks.parquet  scorers.parquet  output_types.parquet  regions.parquet
```

Partitioning by `region / expansion / output_type` matches the paper's analysis
axes (compare pathogenic vs background, per output_type, across 2×/5×/20×).

## 5. ETL plan

DuckDB streams the 29 GB TSVs directly (no Python row loop, no OOM). One-time,
per region:

1. **Dimensions first.**
   - `variants` ← `read_csv(B_Cat_*.tsv)` left-joined to `read_csv(pathogenic.txt)`
     for `is_pathogenic`/`disease`; assign surrogate `variant_id`.
   - `tracks` / `scorers` / `output_types` ← `SELECT DISTINCT` over the AG TSVs
     (one cheap pass), with `scorer_name` parsed into family/output/width/agg.
2. **Fact.** For each of the 3 TSVs: `CREATE VIEW raw AS read_csv(...)`, join to
   the dim tables on the natural keys to get FKs, then
   `COPY (SELECT …) TO 'ag_db/ag_scores' (FORMAT parquet, PARTITION_BY (region,
   expansion, output_type), COMPRESSION zstd)`.
3. **Validate.** Row counts per partition vs source; spot-check a known
   pathogenic locus; confirm score ranges.

Runs as a single parameterized DuckDB SQL script (`region`, input paths) driven
by a small Python wrapper — no persistent process. Fits in a modest SLURM job
(DuckDB spills to disk; set `PRAGMA memory_limit`, `temp_directory`).

## 6. Agent integration

Replace the current `agent.add_data({... 29GB TSVs ...})` with a **DuckDB-backed
query tool** so the agent queries subsets instead of loading files:

- A helper (registered as a Biomni custom tool / data-lake entry), e.g.
  `query_ag(sql, to_file=None) -> DataFrame`, that opens an in-process DuckDB,
  creates views over `ag_db/ag_scores/**` (`hive_partitioning=1`) + the dim
  Parquets, and runs the SQL. Two modes:
  - **inspect (default):** return ≤ **1,000 rows** to context (see §8.2) for
    sampling and strategy development.
  - **materialize (`to_file=...`):** `COPY (<sql>) TO '<file>.parquet'` for
    full-scale derived outputs (per-variant scores, candidate tables); the agent
    then reads back only summaries/`head`. Keeps big results out of context while
    still computing over all rows.
- Give the agent the **schema + a few example queries** in the prompt (it writes
  SQL, not pandas over 29 GB). Register `variants`/`tracks` as small browsable
  tables it can still read directly.
- The small files (`B_Cat_*`, pathogenic) can still be registered as-is; only the
  three giant AG TSVs move behind the query tool.

## 7. Expanding to other gene regions

- Rerun the ETL with `region=3UTR` (and its AG TSVs) → new partitions under the
  same `ag_scores/`. `variants` gains 3'UTR rows; `tracks`/`scorers`/
  `output_types` are shared and stable (same AlphaGenome catalog).
- No schema change, no reload of existing regions. The agent's cross-region
  queries are `WHERE region IN (...)`.
- Keep per-region catalog + pathogenic files under `Rpt_Ds/data/<REGION>/`
  mirroring the current `5UTR/` layout.

## 8. Open questions / decisions

1. **Output location & retention** — ✅ **DECIDED.** Location: `Rpt_Ds/data/ag_db/`
   (per §4). Retention: **remove the 29 GB source TSVs after conversion** —
   backups exist in separate storage and the Parquet dataset is persistent
   (plain on-disk files, not an ephemeral server). Guard: removal is a
   **separate, explicit step gated on validation passing** (§5.3), never
   automatic inside the ETL.
2. **Result-size guardrail** — ✅ **DECIDED: cap `query_ag` at 1,000 rows
   returned to the LLM context.** Purpose is inspection/strategy sampling, not
   feeding raw rows to the model. *Critical distinction:* the cap limits the
   **payload into context**, NOT the computation — DuckDB still scans all ~309 M
   rows, and aggregation queries (`GROUP BY`/`COUNT`/`AVG`/scoring) legitimately
   run full-dataset and return small results. For large intermediate/derived
   outputs (e.g. per-variant score tables) the agent writes to a Parquet/CSV file
   and reads back summaries, rather than pulling rows into context. Implementation:
   wrap the query as `SELECT * FROM (<agent sql>) LIMIT 1000`, and if the inner
   result exceeds 1000 rows, return the 1000 + a note ("N rows total; refine with
   aggregation or write to a file") so the agent knows to aggregate.
3. **Per-row gene** — ✅ **RESOLVED (data-checked): gene is per-row, not
   per-variant.** 115/122 sampled variants map to *multiple* scored genes (up to
   ~16); gene-centric outputs (`RNA_SEQ`, `SPLICE_*`) are always populated,
   localized/epigenetic outputs are always blank. Design updated: nullable
   `gene_id` FK on the fact + a `genes` dimension; the variant's *host* gene stays
   separate in `variants`.
4. **`scorer` parsing** — enumerate all 19 scorer strings to finalize the
   `scorers` parse (families: GeneMaskLFC/Active, CenterMask, SpliceJunction,
   GeneMaskSplicing, Polyadenylation, …).

## 9. Phased rollout

1. Install `duckdb`; prototype ETL on **one** file (`B_5UTR_all_GCN_2xAG.tsv`) →
   measure size/time, validate a known locus. *(chose design-first, so this is
   step 1 of implementation once approved.)*
2. Full 5'UTR ETL (all 3 expansions) + dim tables.
3. Validate (§5.3).
4. `query_ag` tool + wire into `run_biomni.py` (replace the 3 big `DATA_FILES`).
5. Re-run the 5'UTR experiment against the DB; confirm parity with prior results.
6. **Only after end-to-end parity:** remove the 5'UTR source TSVs (backups
   retained elsewhere) to reclaim ~87 GB — delete-last, so the pipeline is proven
   on the DB before the source is gone.
7. Onboard 3'UTR; then generalize per region.
