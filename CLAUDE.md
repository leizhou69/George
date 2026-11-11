# CLAUDE.md

Guidance for Claude Code (and future you) when working in the **George** repo.

## What this repo is

The clean project repo for the **tandem-repeat pathogenicity analysis** (5'UTR GCN
repeats, extended to CDS trinucleotide repeats), migrated out of the old `Biomni_Rpts_Ds` fork (see `upgrade.md` /
`upgrade_log.md` for the migration history). Two things changed vs the old repo:

1. **Biomni is now an editable-installed dependency** (`pip install -e
   ../biomni-fork`), not a vendored `sys.path.append("./")` copy. `import biomni`
   resolves to `/blue/zhou/leizhou/Agents/biomni-fork/biomni`. The fork carries
   four load-bearing patches — see `../biomni-fork/PATCHES.md`.
2. **AlphaGenome data** lives in a multi-region DuckDB/Parquet backend
   (`data/ag_db/`: 5UTR + CDS + 3UTR, ~2.9B fact rows; see `db/db_construction.md`
   and `db/ag_db_July2026_summary.md`). The agent reaches it only through the
   registered `query_ag` tool (`db/query_ag.py`); the raw AG `.tsv` files are no
   longer registered — or on disk (so the ETL cannot be re-run without restoring
   them).

The scientific task lives in `queries/query_05_b.txt` (5'UTR; `--region 5UTR`, the
default) and `queries/query_05_cds.txt` (CDS; `--region CDS`): an exploratory
analysis of what distinguishes disease-causing tandem-repeat loci, using AlphaGenome
expansion predictions plus supplied data. The agent emits
`pathogenic_repeat_analysis.ipynb`, `Candidate_Identification.ipynb`, and
`Top_Candidate_Pathogenic_repeats.csv`.

## Layout
```
harness/run_george.py          the batch-experiment harness
harness/slurm/*.sbatch         SLURM submit scripts (submit from repo root)
db/query_ag.py                 the agent's SQL tool over data/ag_db
db/*.md, db/etl/               AG backend design/build docs + ETL code
queries/query_05_b.txt         the 5'UTR task (default region)
queries/query_05_cds.txt       the CDS task
analysis/                      notebooks; comparisons_{5utr,cds}/ cross-model reports
manuscript/5UTR_TNR_0605.pdf
results/Top_Candidates_{5UTR,CDS}_24July26.csv
data/  (gitignored)            5UTR/ CDS/ 3UTR/ catalogs + pathogenic lists; ag_db/
output/ (gitignored)           run outputs (one dated subdir per batch)
.keys/ (gitignored)            held-out evaluation keys — never shown to the agent
biomni_log.md                  append-only run log (written by the harness)
biomni_data_cache/             the 15G local Biomni data lake (76 files); gitignored
archive/                       superseded queries/notebooks
```

## How it runs

Environment: conda env **`biomni_e1`**. API keys come from `.env` (gitignored).
See `environment.md` for install/verification.

**Always run from the George project root** so the harness's relative paths
(`data/`, `output/`, `queries/`, `biomni_data_cache`) resolve:

```bash
ml conda && conda activate biomni_e1                # `conda` is not on PATH until `ml conda`
python harness/run_george.py s5 o4.8              # run named model keys (5UTR)
python harness/run_george.py o5 --region CDS      # CDS task
python harness/run_george.py o4.5 --temperatures 0.7
python harness/run_george.py                       # no args → LLM_CONFIGS defaults

sbatch harness/slurm/o55_5utr.sbatch               # one script per (models, region) batch
sbatch harness/slurm/opus_cds.sbatch
```

SLURM sizing: **8 CPU / 64 GB** (runs are API-bound; see the `biomni-slurm` skill).
The harness exits non-zero if any experiment fails and the sbatch scripts use
`set -eo pipefail`, so a failed run shows as FAILED in SLURM rather than COMPLETED.

`run_george.py` loops **models × temperatures**; per combo it `cd`s into a fresh
`output/<prefix>/`, builds an `A1` agent (`path=./biomni_data_cache`,
`timeout_seconds=12000`), registers the region's `DATA_FILES` as absolute paths
plus the `query_ag` tool, appends the AG schema block to the prompt, runs
`agent.go(prompt)`, then writes `.log`, `.md`, and `media/*.png` and appends
`[start]`/`[done]` lines to `biomni_log.md`.

### Model keys (`MODEL_NAMES`)
`s5`→`claude-sonnet-5`, `o4.8`→`claude-opus-4-8`, `s4.6`→`claude-sonnet-4-6`,
`o4.6`→`claude-opus-4-6`, `o5`→`claude-opus-5`, `o5.5`→`claude-opus-5-5`, `f5.2`→`claude-fable-5-2`, `o4.5`→`claude-opus-4-5-20251101`, plus gpt5/gpt5.2/
gemini (incl. `gem4c`→`gemini-4-carbon`)/grok keys. Source auto-detected from the model-name prefix in
`biomni/llm.py::get_llm`.

### Config knobs (top of `run_george.py`)
`REGION_CONFIGS` (per region: `query_file`, `query_id`, and 4 `data_files` — the
given pathogenic list, the catalog, and the `variants`/`tracks` dim Parquets;
selected with `--region`, default `5UTR`), `LLM_CONFIGS`, `TEMPERATURES`,
`TIMEOUT_SECONDS` (12000).

## ⚠️ Known issues / gotchas
1. **`temperature` is rejected by Opus 4.7+/Sonnet 5** (HTTP 400). Handled: the
   fork's `biomni/llm.py::_anthropic_rejects_sampling_params` skips it, and the
   harness's `_model_ignores_temperature` runs those models once instead of
   sweeping. Don't re-add a temperature for these models.
2. **`max_tokens`** is 32000 in the fork's Anthropic branch (was 8192). Raise
   further if long deliverables truncate (`stop_reason: max_tokens`); note the
   SDK requires streaming above ~16K, which this path doesn't use yet.
3. **S3 data-lake 403s (resolved).** `run_george.py` passes
   `expected_data_lake_files=<local files>` to `A1()` so it skips all S3
   downloads and uses the local lake (`biomni_data_cache`, 76/76 files).
4. **Working-directory side effect.** `run_single_experiment` `os.chdir`es into
   the per-experiment output dir (restored in `finally`); that's why `DATA_FILES`
   are resolved to absolute paths against `original_cwd` (the repo root).
5. **`biomni_data_cache` is now a real local dir** (76 lake files), `mv`'d in
   from the old repo — George is fully self-contained with no dependency on
   `Biomni_Rpts_Ds` (which is archived). It stays gitignored.
6. **Forced `tool_choice` is rejected by Opus 5.5 / Sonnet 5.5 / Fable 5.1** (HTTP
   400). langchain-anthropic 0.3.21's `with_structured_output` forces it, which
   broke `A1.add_tool` (tool-schema generation). Handled by the fork's
   `biomni/llm.py::with_structured_output_compat` (Patch 3 in `PATCHES.md`); use it
   instead of calling `llm.with_structured_output` directly in the fork.
7. **Runs can hang after the deliverables are written** (the fork's thread-based
   execution timeout cannot kill a stuck thread). The candidate CSV is final by
   then, so `scancel` is safe — don't wait for a `[done]` line that may never come.
8. **Opus 5.5 runs do not work yet** (as of 2026-11-11): on 10-31 / 11-01 every
   model response failed the fork's `<execute>`/`<solution>` tag parse and the
   retry loop ran until a 403 `model_access_suspended`. The loop is now bounded
   (fork Patch 4: stops after 5 consecutive corrections and prints `stop_reason`
   + block types per parse error), but *why* the responses parse as empty is
   still unknown — read those diagnostic lines in the next attempt's log. See
   `F5.2_update_11Nov26.md` (B1). When the breaker fires the harness logs
   `status=success  deliverables=0/3`, so check the deliverables count.

9. **Catalog label leak — partly closed 2026-11-11.** `Source` and
   `FoundInPerfectRepeatsInReference` marked the disease-catalog loci (given
   positives + withheld keys); both are now dropped from the catalog TSVs and the
   ag_db variants dims (originals in gitignored `data/_unmasked_2026-11-11/`; see
   `db/db_construction.md` §4.4). Runs up to and including the 2026-11-11 batch saw
   them, so their withheld-key recovery is not clean and they are not comparable
   with later runs. Still leaking in CDS: the `CNG` motif / purity ≈ 0.67 on 11
   disease loci.

## Output layout
`output/<QUERYID>_<modelkey>_Tmp<temp>_<timeoutid>_<timestamp>/` with
`<prefix>.log`, `<prefix>.md`, `media/plot_*.png`.

## Conventions
- API keys: `.env` only — never hardcode or commit (`.gitignore` covers `.env`).
- Held-out evaluation keys live in gitignored `.keys/`; never register them with
  the harness and never write their identities into a tracked file (aggregate
  counts only — see the `compare-biomni-output` skill).
- Biomni changes go in `../biomni-fork` and get documented in its `PATCHES.md`;
  keep divergence from upstream minimal.
- Don't commit `data/`, `output/`, `biomni_data_cache`, or `data/ag_db/` (the AG
  backend lives under `data/`, per `db/AG_DB_DESIGN.md` §8.1; `db/` holds only the
  ETL/query code and design docs).
