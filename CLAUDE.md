# CLAUDE.md

Guidance for Claude Code (and future you) when working in the **George** repo.

## What this repo is

The clean project repo for the **5'UTR GCN tandem-repeat pathogenicity analysis**,
migrated out of the old `Biomni_Rpts_Ds` fork (see `upgrade.md` /
`upgrade_log.md` for the migration history). Two things changed vs the old repo:

1. **Biomni is now an editable-installed dependency** (`pip install -e
   ../biomni-fork`), not a vendored `sys.path.append("./")` copy. `import biomni`
   resolves to `/blue/zhou/leizhou/Agents/biomni-fork/biomni`. The fork carries
   two load-bearing patches — see `../biomni-fork/PATCHES.md`.
2. **AlphaGenome data** is moving to a DuckDB/Parquet backend (`db/AG_DB_DESIGN.md`)
   so the pipeline can scale to other gene regions (3'UTR, …). Until Phase 4/5 of
   the migration land, the harness still registers the raw `.tsv` files directly.

The scientific task lives in `queries/query_05_b.txt`: an exploratory analysis of
what distinguishes disease-causing 5'UTR GCN tandem-repeat loci, using AlphaGenome
expansion predictions plus supplied data. The agent emits
`pathogenic_repeat_analysis.ipynb`, `Candidate_Identification.ipynb`, and
`Top_Candidate_Pathogenic_repeats.csv`.

## Layout
```
harness/run_biomni.py          the batch-experiment harness
harness/slurm/*.sbatch         SLURM submit scripts (submit from repo root)
db/AG_DB_DESIGN.md, db/etl/    the AG DuckDB/Parquet backend (built Phase 4)
queries/query_05_b.txt         the active task
analysis/*.ipynb               active notebooks
manuscript/5UTR_TNR_0605.pdf
results/Top_Candidate_Pathogenic_repeats.csv
data/  (gitignored)            5UTR/ + 3UTR/ region files; ag_db/ (Phase 4)
output/ (gitignored)           run outputs
biomni_data_cache/             the 15G local Biomni data lake (76 files); gitignored
archive/                       superseded queries/notebooks
```

## How it runs

Environment: conda env **`biomni_e1`**. API keys come from `.env` (gitignored).
See `environment.md` for install/verification.

**Always run from the George project root** so the harness's relative paths
(`data/`, `output/`, `queries/`, `biomni_data_cache`) resolve:

```bash
conda activate biomni_e1
python harness/run_biomni.py s5 o4.8              # run named model keys
python harness/run_biomni.py o4.8 --temperatures 0.7
python harness/run_biomni.py                       # no args → LLM_CONFIGS defaults

sbatch harness/slurm/512GB.sbatch                  # s5 + o4.8 on SLURM
sbatch harness/slurm/196GB.sbatch                  # LLM_CONFIGS defaults
```

`run_biomni.py` loops **models × temperatures**; per combo it `cd`s into a fresh
`output/<prefix>/`, builds an `A1` agent (`path=./biomni_data_cache`,
`timeout_seconds=12000`), registers `DATA_FILES` as absolute paths, runs
`agent.go(prompt)`, then writes `.log`, `.md`, and `media/*.png`.

### Model keys (`MODEL_NAMES`)
`s5`→`claude-sonnet-5`, `o4.8`→`claude-opus-4-8`, `s4.6`→`claude-sonnet-4-6`,
`o4.6`→`claude-opus-4-6`, `o4.5`→`claude-opus-4-5-20251101`, plus gpt5/gpt5.2/
gemini/grok keys. Source auto-detected from the model-name prefix in
`biomni/llm.py::get_llm`.

### Config knobs (top of `run_biomni.py`)
`QUERY_FILE` (`queries/query_05_b.txt`), `QUERY_ID`, `LLM_CONFIGS`,
`TEMPERATURES`, `TIMEOUT_SECONDS` (12000), `DATA_FILES` (5 entries under
`data/5UTR/`).

## ⚠️ Known issues / gotchas
1. **`temperature` is rejected by Opus 4.7+/Sonnet 5** (HTTP 400). Handled: the
   fork's `biomni/llm.py::_anthropic_rejects_sampling_params` skips it, and the
   harness's `_model_ignores_temperature` runs those models once instead of
   sweeping. Don't re-add a temperature for these models.
2. **`max_tokens`** is 32000 in the fork's Anthropic branch (was 8192). Raise
   further if long deliverables truncate (`stop_reason: max_tokens`); note the
   SDK requires streaming above ~16K, which this path doesn't use yet.
3. **S3 data-lake 403s (resolved).** `run_biomni.py` passes
   `expected_data_lake_files=<local files>` to `A1()` so it skips all S3
   downloads and uses the local lake (`biomni_data_cache`, 76/76 files).
4. **Working-directory side effect.** `run_single_experiment` `os.chdir`es into
   the per-experiment output dir (restored in `finally`); that's why `DATA_FILES`
   are resolved to absolute paths against `original_cwd` (the repo root).
5. **`biomni_data_cache` is now a real local dir** (76 lake files), `mv`'d in
   from the old repo — George is fully self-contained with no dependency on
   `Biomni_Rpts_Ds` (which is archived). It stays gitignored.

## Output layout
`output/<QUERYID>_<modelkey>_Tmp<temp>_<timeoutid>_<timestamp>/` with
`<prefix>.log`, `<prefix>.md`, `media/plot_*.png`.

## Conventions
- API keys: `.env` only — never hardcode or commit (`.gitignore` covers `.env`).
- Biomni changes go in `../biomni-fork` and get documented in its `PATCHES.md`;
  keep divergence from upstream minimal.
- Don't commit `data/`, `output/`, `biomni_data_cache`, or `db/ag_db/`.
