---
name: biomni-slurm
description: >-
  Launch, right-size, and chain SLURM jobs for the George biomni harness
  (harness/run_biomni.py) — the 5UTR / CDS / 3UTR pathogenic-repeat agent runs
  against the AG DuckDB backend (data/ag_db). Use whenever submitting one of
  these runs, choosing --cpus-per-task / --mem, chaining a follow-up job, or
  checking how much CPU/RAM a finished run actually used.
---

# Running biomni harness jobs on HiPerGator

The harness runs a Biomni A1 agent on `queries/query_05_*.txt` against the AG
DuckDB/Parquet backend. Each invocation loops **models × temperatures**; per combo
it builds a fresh agent, registers the region's small data files + the `query_ag`
tool, runs `agent.go(prompt)`, and writes `.log` / `.md` / `media/*.png`. It also
appends `[start]` / `[done]` lines to `biomni_log.md` automatically.

## How to run

Always from the George project root (`cd /blue/zhou/leizhou/Agents/George`), env
`biomni_e1`:

```bash
python harness/run_biomni.py s5 --region CDS --output-dir output/<dated_dir>
python harness/run_biomni.py o4.8 s5 --region 5UTR      # multiple models (sequential)
```

- `--region {5UTR,CDS,...}` selects the query file + registered data files
  (`REGION_CONFIGS` in run_biomni.py). Default 5UTR.
- Model keys live in `MODEL_NAMES` (s5, o4.8, …). **Sonnet 5 and Opus 4.7+ reject
  the temperature param, so they run once** regardless of `--temperatures`.
- Models in one invocation run **sequentially**, so resource needs do NOT scale
  with the number of models — size for one.

## Right-sizing CPU / RAM  (IMPORTANT — these runs are API-bound, not compute-bound)

Measured from the 5UTR Sonnet-5 run (job 37972802, requested 48 CPU / 420 GB):

| metric | value | of request | 
|---|---|---|
| peak RAM (MaxRSS) | **1.21 GB** | 0.29 % of 420 GB |
| CPU time (TotalCPU) | **13.7 min** over 3h36m wall | 0.13 % of 48 cores (~0.06 cores avg) |

Almost the entire wall-clock is spent waiting on the Anthropic API. The only local
compute is DuckDB aggregate queries via `query_ag` (`AG_QUERY_THREADS=4`,
`AG_QUERY_MEM=16GB`, spills to disk) plus light pandas on materialized parquets.
**The model (Sonnet vs Opus vs GPT) runs on the provider's servers — it does not
change local RAM/CPU.** So every region/model needs the same modest footprint.

**Recommended request: `--cpus-per-task=8 --mem=64gb`.**
- Ratio-clean: HiPerGator grants up to **8 GB RAM per core**, so keep
  `mem ≤ cpus × 8gb`. 8×8 = 64 GB. Requesting more (e.g. 48 CPU / 420 GB → needs
  53 cores for the ratio) leaves jobs stuck in `PENDING (Resources)` and can bump
  billing.
- 8 cores covers DuckDB's 4 query threads + pandas/OS headroom; 64 GB is ~50×
  the observed peak.
- Tighter floor if the queue is busy: `--cpus-per-task=4 --mem=32gb` (still fine).
- **Do not** copy the old 48-CPU / 420-GB requests — they were ~300× oversized.

## Time limit

Agent timeout is `TIMEOUT_SECONDS=12000` (~200 min); total wall incl. trace/markdown
post-processing runs ~3.5 h. `--time=24:00:00` is safe (never hit) and doesn't affect
scheduling priority meaningfully on qos=zhou.

## Chaining a follow-up job ("submit once the current job is done")

Use a SLURM dependency instead of waiting:

```bash
sbatch --dependency=afterany:<running_jobid> harness/slurm/<next>.sbatch
```

`afterany` starts the follow-up when the first ends (any exit state); use `afterok`
to require success.

## Verify utilization after a run (seff is NOT installed here)

```bash
sacct -j <jobid> --format=JobID,AllocCPUS,AllocTRES%38,TotalCPU,Elapsed,MaxRSS,MaxVMSize
```

- mem % = MaxRSS / requested mem
- cpu % = TotalCPU / (Elapsed × AllocCPUS)

If either is tiny, shrink the next request accordingly.

## sbatch template (right-sized)

```bash
#!/bin/bash
#SBATCH --job-name=q05<region>_<models>
#SBATCH --mail-type=ALL
#SBATCH --mail-user=leizhou@ufl.edu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou
cd /blue/zhou/leizhou/Agents/George
ml conda
conda activate biomni_e1
mkdir -p output/<dated_dir>
python harness/run_biomni.py <models> --region <REGION> --output-dir output/<dated_dir> \
  2>&1 | tee output/<dated_dir>/q05<region>_<models>_$(date +%Y%m%d-%H%M%S).log
```
