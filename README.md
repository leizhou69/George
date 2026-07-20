# George

Clean project repo for the **5'UTR GCN tandem-repeat pathogenicity analysis**,
migrated out of the `Biomni_Rpts_Ds` fork. Biomni is an editable-installed
dependency (`../biomni-fork`); the AlphaGenome data is served from a
DuckDB/Parquet backend so the pipeline can scale to other gene regions.

See `upgrade.md` for the migration plan and `db/AG_DB_DESIGN.md` for the DB design.

## Layout
```
harness/    run_biomni.py + slurm/ sbatch scripts   (the batch-experiment harness)
db/         AG_DB_DESIGN.md, etl/ (DuckDB ETL), query_ag.py (agent query tool)
queries/    query_05_b.txt (the active scientific task)
analysis/   active notebooks (pathogenic_repeat_analysis.ipynb, ...)
manuscript/ 5UTR_TNR_0605.pdf
results/    Top_Candidate_Pathogenic_repeats.csv
data/       region source files + ag_db/  (moved from old repo; gitignored)
output/     fresh run outputs             (gitignored)
archive/    superseded queries/notebooks
```

## Quickstart
```bash
conda activate biomni_e1
pip install -e ../biomni-fork
pip install duckdb pyarrow
python harness/run_biomni.py s5 o4.8
```
See `environment.md` for details.

## Migration status
Scaffolded per **Phase 2** of `upgrade.md`. The Biomni fork extraction (Phase 1),
keeper migration + data move (Phase 3), and the DuckDB backend (Phase 4+) are
still pending.
