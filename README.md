# George

Project repo for the **tandem-repeat pathogenicity analysis** (5'UTR GCN repeats,
extended to CDS trinucleotide repeats), migrated out of the `Biomni_Rpts_Ds` fork.
Biomni is an editable-installed dependency (`../biomni-fork`); the AlphaGenome
data is served from a multi-region DuckDB/Parquet backend (`data/ag_db/`:
5UTR + CDS + 3UTR) through the `query_ag` tool.

See `CLAUDE.md` for how the harness runs and known gotchas, `db/db_construction.md`
and `db/ag_db_July2026_summary.md` for the backend, and `biomni_log.md` for the
run history. `upgrade.md` / `upgrade_log.md` are the (completed) migration record.

## Layout
```
harness/    run_george.py + slurm/ sbatch scripts   (the batch-experiment harness)
db/         design docs, etl/ (DuckDB ETL), query_ag.py (agent query tool)
queries/    query_05_b.txt (5'UTR task), query_05_cds.txt (CDS task)
analysis/   notebooks, cross-model comparisons (comparisons_5utr/, comparisons_cds/)
manuscript/ 5UTR_TNR_0605.pdf
results/    Top_Candidates_5UTR_24July26.csv, Top_Candidates_CDS_24July26.csv
data/       region catalogs + pathogenic lists + ag_db/   (gitignored)
output/     run outputs                                    (gitignored)
archive/    superseded queries
```

## Quickstart
```bash
ml conda && conda activate biomni_e1
pip install -e ../biomni-fork
pip install duckdb pyarrow
python harness/run_george.py s5 o4.8                 # 5'UTR task (default region)
python harness/run_george.py o5 --region CDS         # CDS task
```
See `environment.md` for details.

## Migration status
Complete (Phases 1–8 of `upgrade.md`, finished 2026-07-21; log in `upgrade_log.md`).
George is self-contained; `Biomni_Rpts_Ds` is a frozen archive.
