---
name: add-biomni-region
description: >-
  Onboard a new gene region (e.g. CDS, 3'UTR) into the George biomni
  pathogenic-repeat pipeline, or set up a run for an existing region — create the
  region's query file, register it in the harness --region switch, verify ag_db
  coverage, and launch. Use when adding a region task, adapting query_05_b.txt for
  a new region, or wiring DATA_FILES for a region.
---

# Onboarding a region into the biomni pipeline

A "region" (5UTR, CDS, 3UTR, …) is a task variant over a set of tandem-repeat loci
in a gene sub-region, scored by AlphaGenome expansion predictions in the `ag_db`.
Adding one = a query file + a `REGION_CONFIGS` entry + a coverage check + a run.

## Prerequisite: the region must be in the ag_db

The region's AlphaGenome scores must already be ingested (dims + fact partitions):
`data/ag_db/dims/variants/<REGION>.parquet` and
`data/ag_db/ag_scores/region=<REGION>/…`. If not, build it first via the ETL
(`db/etl/regions.json` manifest + `sbatch db/etl/build_ag_db.sbatch`; see
`db/db_construction.md`). A full rebuild needs every region's source TSVs present.

## Data files under `data/<REGION>/`

- **catalog** `B_Cat_<REGION>_msk_TNR.tsv` — all TNR loci + attributes (the agent's
  candidate universe).
- **given pathogenic list** (the positives shown to the agent), e.g.
  `B_<REGION>_Pathogenic_*.txt`.
- **withheld keys** go in **gitignored `.keys/<region>_keys`** — NEVER placed under
  `data/<REGION>/` and NEVER registered with the harness (see
  `compare-biomni-output` for the held-out-key discipline).

## Steps

1. **Query file** `queries/query_05_<region>.txt` — copy `queries/query_05_b.txt`
   and adapt:
   - region name, locus count, and number of known pathogenic loci in BACKGROUND;
   - **SCOPE line** — match the motif scope to the biology:
     - 5'UTR → **GCN only** (`canonical_motif IN ('CCG','AGC','CGG','CTG')`),
     - CDS / 3'UTR → **all TNR** (pathogenic repeats span AGC/CCG/CNG/ACG), i.e.
       filter `region='<REGION>'` with NO motif restriction;
   - the DATA file names + column descriptions (catalogs differ, e.g. CDS adds
     MANE gene fields);
   - keep the deliverable filenames identical
     (`Top_Candidate_Pathogenic_repeats.csv`, the two notebooks) so the harness's
     deliverables check finds them.

2. **Register in the harness** — add a `REGION_CONFIGS` entry in
   `harness/run_biomni.py`:
   ```python
   "<REGION>": {
       "query_file": "queries/query_05_<region>.txt",
       "query_id":   "q05<region>",
       "data_files": {
           "Pathogenic_repeats":   "data/<REGION>/B_<REGION>_Pathogenic_*.txt",
           "All_<REGION>_catalog": "data/<REGION>/B_Cat_<REGION>_msk_TNR.tsv",
           "AG_variants_dim":      "data/ag_db/dims/variants/<REGION>.parquet",
           "AG_tracks_dim":        "data/ag_db/dims/tracks.parquet",
       },
   },
   ```
   (Default region stays 5UTR; select at run time with `--region <REGION>`.)

3. **Verify coverage** — confirm every catalog locus + given pathogenic + withheld
   keys resolve in the ag_db with AG scores before running:
   ```python
   import sys; sys.path.insert(0,'db'); import query_ag
   c=query_ag.get_connection()
   c.execute("CREATE VIEW cat AS SELECT LocusId FROM read_csv('data/<REGION>/B_Cat_<REGION>_msk_TNR.tsv',delim='\t',header=true,all_varchar=true)")
   print(c.execute("SELECT count(DISTINCT v.locus_id) FROM cat x JOIN variants v ON x.LocusId=v.locus_id JOIN ag_scores s ON s.variant_id=v.variant_id WHERE v.region='<REGION>'").fetchone())
   ```

4. **Launch** — right-sized SLURM job (see `biomni-slurm` skill: 8 CPU / 64 GB):
   ```bash
   python harness/run_biomni.py <models> --region <REGION> --output-dir output/<dated>
   ```
   Note temperature handling: Opus 4.7+/Opus 5/Sonnet 5 reject temperature (run
   once); Opus 4.5 and older ACCEPT it, so pass `--temperatures 0.5` to avoid a
   3-way sweep.

## Then

- Evaluate / compare with the `compare-biomni-output` skill.
- Log is automatic (`biomni_log.md`); env + resources per `biomni-slurm`.
