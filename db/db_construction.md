# AG DuckDB construction plan (multi-region)

How the AlphaGenome DuckDB/Parquet backend (`data/ag_db/`) is (re)built to hold
**multiple gene regions in one database** — **5'UTR + CDS + 3'UTR** (more to
follow). This supersedes the single-region 5'UTR build recorded in
`upgrade_log.md` (Phases 4–7). Companion files: `db/AG_DB_DESIGN.md` (schema
rationale), `db/etl/` (the code), `db/query_ag.py` (the agent's read interface).

---

## 1. Goal

One star-schema warehouse the agent queries with `query_ag(sql)` (never raw TSVs),
covering every region, with **shared dimensions** and **consistent surrogate
keys** so a single SQL statement can compare regions (5'UTR vs CDS vs 3'UTR …).
**No pathogenic / disease information lives in the DB** — the catalogs are masked
(`msk`) and no pathogenic files are read.

## 2. Inputs (region manifest — `db/etl/regions.json`)

Each region contributes a **masked catalog** (loci + attributes, no disease info)
and three **AlphaGenome prediction** files. **Only AG files (names ending
`AG.tsv`, `AG.out.tsv`, or `AG.sout.tsv`) may populate the DB** — the ETL rejects
anything else in an `ag[]` slot.

| Region | Masked catalog (loci) | AG predictions (2x / 5x / 20x) | AG size each |
|--------|-----------------------|--------------------------------|--------------|
| 5UTR   | `data/5UTR/B_Cat_5UTR_msk_TNR.tsv` (10,054) | `data/5UTR/B_5UTR_TNR_{2,5,20}xAG.sout.tsv` | ~46 GB |
| CDS    | `data/CDS/B_Cat_CDS_msk_TNR.tsv` (34,892) | `data/CDS/B_TNR_msk_CDS_{2,5,20}xAG.out.tsv` | 188 / 207 / 293 GB |
| 3UTR   | `data/3UTR/B_Cat_3UTR_msk_TNR.tsv` (17,021) | `data/3UTR/B_TNR_msk_3UTR_{2,5,20}xAG.out.tsv` | 92 / 102 / 145 GB |

All three catalogs share one 36-column masked schema (no `MotifID`, no
pathogenic/disease columns). Adding a region later = append a `regions.json` entry
(region name, optional `repeat_type` label, catalog, the three AG paths) + rerun.

The AG TSV grain is one row per **variant × output_type × scorer × track**; the
join key `original_variant_id` (e.g. `1-923921-923930-CGG`) equals catalog
`LocusId`. Column layouts differ slightly across regions (5'UTR `.sout.tsv` leads
with `original_variant_id`; CDS/3'UTR `.out.tsv` have a leading `variant_id` and a
trailing `original_variant_id`) — the ETL joins by **column name**, so all work.

## 3. Target layout

```
data/ag_db/
  dims/
    variants/<region>.parquet     one file per region (read union_by_name)
    genes.parquet  tracks.parquet  scorers.parquet  output_types.parquet
    regions.parquet
  ag_scores/region=<R>/expansion=<E>/output_type=<OT>/part-*.parquet
  ag_db.log                       append-only build/provenance log
```

**Fact** `ag_scores` — one row per AG record, dimensions replaced by integer FKs
(`variant_id`, `scorer_id`, `track_id`, `gene_id`) + `raw_score`, `quantile_score`,
`junction_start/end`. Partitioned by `region / expansion / output_type` so region
and expansion filters are cheap. `track_id`/`gene_id` are NULL for
non-tracked / non-genic outputs.

**Dimensions**
- `variants` — one Parquet per region so each keeps its own catalog columns;
  `query_ag` unions them by name (missing columns → NULL). Global `variant_id`
  (offset per region). Adds `motif_len` + `motif_class` (see §4.3). No
  `is_pathogenic` / `disease`.
- `genes` / `tracks` / `scorers` / `output_types` — **shared across regions**,
  deduped by natural key (gene ensembl id; 13-column track hash `track_key`;
  scorer string; output_type), each with a global surrogate id.
- `regions` — `region`, `repeat_type` (free-form label), `notes`.

## 4. Key design decisions

### 4.1 Shared dims → full rebuild, not append
The surrogate keys span all regions, so the whole key space is assigned in one
pass → this is a **full rebuild**, and every region's AG TSVs must be present at
build time. Dims are read once from each region's **2x** file (tracks/scorers/
genes/output_types are identical across expansions); the fact is built once per
`(region, expansion)` in its own process so memory is released between the big
files.

### 4.2 Only AG files populate the DB
`load_regions()` validates every `ag[]` path against `AG\.(?:s?out\.)?tsv$` and
aborts otherwise — a catalog can never be mistaken for a fact source. The masked
catalog feeds **only** the `variants` dim.

### 4.3 Motif class is per-variant, length-derived (future-proof)
A region is **not** assumed to be one repeat class. Each variant gets
`motif_len = length(CanonicalMotif)` and `motif_class` = `trinucleotide` (3),
`tetranucleotide` (4), `pentanucleotide` (5) … with an `<n>-nucleotide` fallback.
So the current TNR datasets and any future tetra-/penta- repeats classify with no
code change. `regions.repeat_type` is only a free-form dataset label.

### 4.4 No pathogenic info
By design the ag_db holds no disease/pathogenic labels — the catalogs are masked
and no pathogenic file is read. Any pathogenic-vs-background analysis joins an
external locus list at analysis time, outside the DB.

### 4.5 Provenance log
Every ETL process appends timestamped lines to `data/ag_db/ag_db.log`: run start +
manifest, each input file with size/mtime, dim row counts (incl. per-region
variant counts and motif-class breakdown), and per-`(region, expansion)` fact row
counts. One chronological record of what went into the DB.

## 5. Build procedure

From the George project root (all three regions' TSVs are present):

```bash
sbatch db/etl/build_ag_db.sbatch      # 32 CPU / 250 GB / qos=zhou
```

The sbatch runs, per `regions.json`:
1. `etl.py preflight` — assert every input exists (fails fast, lists misses);
2. `etl.py dims` — shared dims + per-region variants;
3. `etl.py fact --region <R> --expansion <E>` for each region × {2,5,20}.

Idempotent: reruns overwrite dims and drop+rewrite each `(region, expansion)`
partition set.

## 6. Validation

```bash
python db/etl/validate.py                       # cheap structural checks
AG_VALIDATE_RAWCOUNT=1 python db/etl/validate.py  # + full raw-vs-fact row counts
```

Checks: dim counts; per-region variant count == catalog rows + motif-class
breakdown; global `variant_id` uniqueness; FK integrity (no orphan
`scorer_id`/`variant_id`); score ranges; and, opt-in, per-`(region, expansion)`
**fact rows == raw TSV rows** (proves the INNER joins dropped nothing) plus a
per-region `raw_score`-sum spot-check.

## 7. Resource estimate

5'UTR alone (~90 GB) built in ~19 min, peak ~28 GB RAM. This build streams
~140 (5'UTR) + ~690 (CDS) + ~340 (3'UTR) ≈ **1.16 TB** of AG TSV; expect roughly
**3–6 h** on 32 cores, RAM well under the 250 GB request (small dims hash-joined
against a streamed fact), DB output on the order of ~20–25 GB. `/blue/zhou` has
~3.8 TB free.

## 8. Notes

- **Rebuild cost.** Every new region triggers a full rebuild of all regions
  (shared surrogate keys). Acceptable for occasional additions; if regions start
  arriving often, we can switch to an append/upsert dim strategy later.
- **Old GCN files** (`B_Cat_5UTR_GCNs_masked.tsv`, `B_5UTR_Pathogenic_GCN.txt`,
  CDS `*_Pathogenic_*`) are no longer referenced by the manifest and are not read
  into the DB.
