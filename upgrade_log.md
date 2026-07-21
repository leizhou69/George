# Upgrade / Migration Log

Running record of migration work executed against `upgrade.md`. Newest last.

---

## ⏸️ CURRENT STATE — paused 2026-07-21 after Phase 4 (backend built + validated)

**Done: Phases 1, 2, 3, 4.** **Next: Phase 5** — wire `query_ag` into
`run_biomni.py` (drop the 3 giant AG TSVs from `DATA_FILES`, register the tool,
add the schema/example block to the prompt).

- **`data/ag_db/`** built (2.0 GB, gitignored): dims + `ag_scores` partitioned by
  region/expansion/output_type. ~311M fact rows (2x=102,782,767, 5x=104,210,211,
  20x=104,366,423). ETL job COMPLETED in 18m41s (peak RAM 28.5 GB — the 250 GB
  request was generous; ~64 GB would suffice next time).
- **`db/etl/`** (committable): `explore.py`, `etl.py` (env-overridable for 3UTR),
  `validate.py`, `build_ag_db.sbatch`. **`db/query_ag.py`** = the agent query tool.
- **`validate.py` → "ALL CHECKS PASSED"**: dim counts, 7 pathogenic loci,
  2x fact == raw 102,782,767 (no join drops), FMR1 row-count + RNA_SEQ score-sum
  match the raw TSV, quantile∈[-1,1], no orphan FKs.
- **`query_ag` live-tested**: aggregation, 1k-row truncation note
  (7.26M→1000), `to_file` parquet materialize (73k rows).

**Nothing destructive done.** Source TSVs untouched (Phase 7 delete is gated on
Phase 6 parity). Nothing committed yet.

**To resume Phase 5**: edit `harness/run_biomni.py` — remove the three
`data/5UTR/*AG.tsv` entries from `DATA_FILES`; register `query_ag` as a Biomni
custom tool; inject `query_ag.schema_doc()` + example queries into the prompt.
Keep catalog + pathogenic registered. Checkpoint = a dry agent run issues SQL
via `query_ag` and never loads the TSVs.

- **`biomni-fork`** (`/blue/zhou/leizhou/Agents/biomni-fork`): patched Biomni,
  editable-installed into `biomni_e1`. `import biomni` resolves here. HEAD `3bcdf5f`.
- **`George`** (`/blue/zhou/leizhou/Agents/George`): live project repo, 3 commits
  (HEAD `2414b63`). Keepers migrated; harness repointed & runs (`--help` OK, all
  `DATA_FILES` resolve). `data/` is a real dir (moved via `mv`); `biomni_data_cache`
  is a symlink into `$OLD`.
- **`Biomni_Rpts_Ds`** (`$OLD`): the archive. Only change so far = its
  `Rpt_Ds/data/` was moved out (reversible). Not yet frozen (Phase 8). `upgrade.md`
  still shows uncommitted.
- **Nothing destructive done.** No TSVs deleted (Phase 7 is the only destructive
  step, gated on Phase 6 parity). The 292 GB `$OLD/Rpt_Ds/output` untouched.

**To resume**: `cd $PROJECT`, `conda activate biomni_e1`, then Phase 4 per
`db/AG_DB_DESIGN.md` §5/§9 — prototype ETL on `data/5UTR/B_5UTR_all_GCN_2xAG.tsv`,
then full 5'UTR ETL → `data/ag_db/`, then `db/query_ag.py`.

**Open follow-ups (non-blocking)**: (1) `biomni-fork/README.md` is still the
project readme, not Biomni's; (2) `biomni_data_cache` is a symlink — `mv` it into
George to fully detach; (3) commit `$OLD/upgrade.md` if desired.

---

## 2026-07-20 — Phase 2 DONE: scaffold `../George`

Created the clean sibling project repo at
`/blue/zhou/leizhou/Agents/George` (Phase 2 of `upgrade.md`).

**Actions**
- `mkdir -p harness/slurm db/etl queries analysis manuscript results output archive/queries`
- `git init` → branch `main`.
- `.gitignore`: ignores `data/`, `output/`, `db/ag_db/`, `*.parquet`, `*.tsv`,
  `*.duckdb`, `.env`, `__pycache__/`, `.ipynb_checkpoints/`.
- `environment.md`: conda env `biomni_e1`, editable install of `../biomni-fork`,
  `duckdb`+`pyarrow`, plus the import-resolution verification commands.
- `README.md`: layout, quickstart, migration status.
- `.gitkeep` placeholders in empty tracked dirs.
- Initial commit: **`cbc660c`** "Scaffold George project repo (Phase 2)".

**Deliberately NOT done (correct per plan)**
- Did **not** create `data/` — Phase 3 does `mv $OLD/Rpt_Ds/data $PROJECT/data`,
  which needs the target absent.
- Confirmed both paths are on the same `/blue/zhou` mount (`df -P`), so the
  Phase 3 `mv` will be an instant metadata rename, not an 86 GB copy.
- `output/` left untracked (gitignored).

**Checkpoint status**: skeleton in place. The plan's Phase 2 checkpoint
(`python -c "import duckdb, biomni"`) is NOT yet satisfied — it depends on the
Phase 1 editable install (below).

---

## 2026-07-20 — Phase 1 STARTED (investigation only; no changes made yet)

Began Phase 1 (extract patched Biomni into `$FORK=/blue/zhou/leizhou/Agents/biomni-fork`).
**Only inspected — no clone, no writes, no changes to `$OLD` yet.**

**Findings**
- Phase 0 prerequisite already satisfied: the `a1.py` prefill fix is **committed**
  (`b4aebb6` "Prefill fix: append tool observation as HumanMessage"). Working tree
  clean except `upgrade.md` (the plan itself, being edited — left alone).
- `git ls-files` shows the huge dirs are **untracked/ignored** — `Rpt_Ds/` (0 tracked
  files), `*.sbatch`, `tutorials/`, `figs/`, `test.ipynb`, `slurm-*.out`,
  `biomni_data_cache/`, `data/`, `output/`. A `git clone` therefore carries only
  the 141 tracked files (`.git` is 7.3 MB) — clone is cheap and safe.
- So the plan's `git rm` strip list is mostly moot (those items aren't tracked).
  Tracked top-level: `biomni/`, `biomni_env/`, `docs/`, `CLAUDE.md`, `.env.example`,
  `.gitignore`, `LICENSE`, `MANIFEST.in`, `.pre-commit-config.yaml`,
  `pyproject.toml`, `README.md`, `Rpts_Ds_readme.md`, `run_biomni.py`, `upgrade.md`.
- `README.md` is **identical** to `Rpts_Ds_readme.md` (both 15702 B) — the project
  readme, not Biomni's original.

**Planned deviation from upgrade.md (needs confirmation)**
- Plan's strip list includes `docs`. But `biomni_env/` and `docs/` are **upstream
  Biomni's own files** (env-setup scripts; Sphinx docs). Per the repo convention
  "keep divergence from upstream minimal," deleting upstream files makes future
  rebases messier and isn't needed for an editable install. **Intended: KEEP
  `biomni_env/` and `docs/`; strip only project-specific tracked files**
  (`run_biomni.py`, `CLAUDE.md`, `upgrade.md`, `Rpts_Ds_readme.md`).

**NOT yet done** (interrupted before executing): `git clone $OLD $FORK`, the strip
`git rm`, `PATCHES.md`, `pip install -e $FORK`, and the import-resolution checkpoint.
No `$FORK` directory exists yet.

---

## 2026-07-20 — Phase 1 DONE: patched Biomni extracted + editable-installed

Extracted the fork to `$FORK=/blue/zhou/leizhou/Agents/biomni-fork` and
editable-installed it. **Confirmed to keep `docs/` and `biomni_env/`** (upstream
files) — deviation from the plan's literal strip list, approved.

**Actions**
- `git clone $OLD $FORK` — cheap (7.2 MB `.git`); no untracked data dirs carried.
- Stripped project-specific tracked files: `git rm run_biomni.py CLAUDE.md
  upgrade.md Rpts_Ds_readme.md`. Kept `biomni/`, `pyproject.toml`, `MANIFEST.in`,
  `LICENSE`, `.pre-commit-config.yaml`, `.gitignore`, `README.md`, **`biomni_env/`,
  `docs/`**.
- Wrote `$FORK/PATCHES.md` (folds in `fix_prefill_20260327.md` + the llm.py
  sampling-param/`max_tokens` patch).
- Commit: **`3bcdf5f`** "Strip to installable Biomni fork; add PATCHES.md".
  `origin` left pointing at `$OLD` (local) as the rebase source.
- `pip install -e $FORK --no-deps --no-build-isolation` in `biomni_e1` — this
  **uninstalled the shadowing site-packages `biomni 0.0.8` wheel** and installed
  the editable fork.

**Checkpoint — ALL PASS** (run from `/tmp`, so no cwd shadowing):
- `import biomni` → `/blue/zhou/leizhou/Agents/biomni-fork/biomni` ✅
  (not site-packages, not `$OLD`).
- `_anthropic_rejects_sampling_params('claude-opus-4-8')` → `True`;
  `('claude-sonnet-4-6')` → `False` ✅.
- `a1.py` observation appended as `HumanMessage` ✅.
- `pip show biomni` → "Editable project location: .../biomni-fork" ✅.

**Notes / follow-ups**
- `$FORK/README.md` is currently the *project* readme (identical to the removed
  `Rpts_Ds_readme.md`), not Biomni's original — flagged in PATCHES.md; replace if
  desired.
- The old repo still has its local `biomni/` package dir; with the 0.0.8 wheel
  now gone, its `sys.path.append("./")` still works from its own root as a
  fallback, but the fork is the live install.

**Next**: Phase 3 — migrate keepers into `$PROJECT` (harness/, queries/, db/,
analysis/, manuscript/, results/) and the instant `mv` of `data/`, then repoint
`run_biomni.py` paths.

---

## 2026-07-20 — Phase 3 DONE: keepers migrated into George

Copied all keepers into `$PROJECT` and moved `data/`. Commit **`c41e411`**
"Migrate keepers into George (Phase 3)".

**Copied (originals left intact in `$OLD` archive)**
- `run_biomni.py` → `harness/`; `512GB.sbatch`, `196GB.sbatch` → `harness/slurm/`.
- `query_05_b.txt` → `queries/`; `query_01..05.txt` → `archive/queries/`.
- `ms/5UTR_TNR_0605.pdf` → `manuscript/`; `AG_DB_DESIGN.md` → `db/`.
- `pathogenic_repeat_analysis.ipynb`, `Candidate_Identification.ipynb`,
  `Evaluate.ipynb`, `Verify.ipynb` → `analysis/`.
- `Top_Candidate_Pathogenic_repeats.csv` → `results/`.
- adapted `CLAUDE.md` (new layout, run-from-root, fork/gotchas) → `$PROJECT/`.
- `upgrade.md`, `upgrade_log.md`, `.env` (gitignored) → `$PROJECT/`.

**Moved (the one change to `$OLD`)**
- `mv $OLD/Rpt_Ds/data $PROJECT/data` — instant rename (same `/blue/zhou` mount),
  after asserting the target was absent. `$OLD/Rpt_Ds/data` no longer exists
  (expected; reversible with the reverse `mv`; backups also exist).
- Symlinked the 15G local data-lake cache: `$PROJECT/biomni_data_cache ->
  $OLD/biomni_data_cache` (76 lake files). Reversible/free; NOT in the plan's
  inventory but required by `run_biomni.py`. **George is otherwise self-contained
  (its `data/` is a real dir); to fully detach later, `mv` the cache in.**

**Harness path updates (`run_biomni.py`)**
- Dropped `sys.path.append("./")` (biomni is the editable fork now).
- `QUERY_FILE` → `queries/query_05_b.txt`; `DATA_FILES` → `data/5UTR/...`;
  default `--output-dir` → `output`. Kept the corrected 5-entry `DATA_FILES`.
- sbatch scripts: `python harness/run_biomni.py ...`, output under `output/`,
  "submit from repo root" note added.

**Checkpoint — ALL PASS** (run from `$PROJECT`):
- `python harness/run_biomni.py --help` → exit 0 (no shadow error; loaded `.env`).
- All 5 `DATA_FILES` resolve (three ~30 GB AG TSVs + catalog + pathogenic) and
  `QUERY_FILE` resolves.
- `import biomni` → `.../biomni-fork/biomni` (fork).
- `./biomni_data_cache` resolves to 76 lake files via the symlink.

**Gotcha hit & fixed**: git `.gitignore` doesn't support inline `# comments` —
`biomni_data_cache  # …` briefly staged the symlink. Moved the comment to its own
line; verified `git check-ignore` catches `biomni_data_cache`, `.env`, `data`,
`output`.

**Next**: Phase 4 — build the AG DuckDB/Parquet backend per `db/AG_DB_DESIGN.md`
(prototype ETL on one file, then full 5'UTR ETL → `data/ag_db/`, then
`db/query_ag.py`).

---

## 2026-07-21 — Phase 4 IN PROGRESS: ETL authored + sample-validated (full run not submitted)

Installed `duckdb` 1.5.4 into `biomni_e1` (`pip`). Environment note: this repo
is worked from inside a SLURM interactive job (4 CPU / **32 GB**), on a heavily
shared node — hence the full ETL is a dedicated sbatch, not an in-session run.

**Phase 4 step 1 — exploration (`db/etl/explore.py`, done).** Three streaming
passes over `B_5UTR_all_GCN_2xAG.tsv` (~6 min each on the contended node):
- **102,782,767 rows**; 6,650 variants; 11 output_types; 19 scorers;
  4,619 track_names; 19,269 gene_names; **19,695 gene_ids** (gene_id is finer).
- Per-row gene confirmed nullable exactly as designed: `RNA_SEQ`/`SPLICE_*`
  always have a gene; `ATAC`/`CHIP_TF`/`CHIP_HISTONE`/`CAGE`/`DNASE`/
  `CONTACT_MAPS`/`PROCAP` always blank.
- All 19 `variant_scorer` strings enumerated; families: CenterMask, ContactMap,
  GeneMaskActive, GeneMaskLFC, GeneMaskSplicing, Polyadenylation, SpliceJunction.
  `width=None` present (GeneMaskSplicing) → parses to NULL. Parse regex verified.

**ETL design choices (vs the raw design doc):**
- **Hashed track key.** track_name is not unique across biosamples, so the
  13 track-metadata cols are `md5(concat_ws('||', coalesce(col,'')…))`-hashed into
  `track_key`; the 100M-row fact joins tracks on that one column (not a 13-way
  equality join). `coalesce` first so NULLs are kept positionally.
- **genes deduped by `gene_id`** (ensembl), the natural key, so the fact's LEFT
  JOIN can't fan out; name/type/strand taken via `min()` (functionally dependent).
- **Idempotent fact**: each `build_fact(expansion)` drops its own
  `region=5UTR/expansion=E/` dirs then writes with `APPEND` (so it never clobbers
  the other expansions). Dims built once from the 2x file (identical across exps).

**Dry-run on a 2M-row `head` sample (AG_OUT=/tmp, no full scan) — ALL PASS:**
- dims build; scorers=19, output_types=11 (tracks/genes sample-limited, expected).
- fact = **1,999,999 rows = sample − header → INNER joins on variants/scorers
  dropped nothing.** 11 output_type partitions written.
- **FK integrity:** 0 orphan `scorer_id`; `track_id` NULLs == raw blank
  track_name (hashed join matched every tracked row); `gene_id` NULLs ==
  raw blank gene_id (921,033 == 921,033).
- **Value parity:** RNA_SEQ `raw_score` sum for a sample variant identical
  raw-vs-fact (1429.2969 == 1429.2969).

**NOT yet done:** the real full ETL (submit `db/etl/build_ag_db.sbatch`),
`validate.py` against the real DB, size/time measurement, and `query_ag.py`.
Nothing destructive; source TSVs untouched (Phase 7 is the only delete step).

---

## 2026-07-21 — Phase 4 DONE: AG backend built, validated, query tool live

**Full ETL run** (`sbatch db/etl/build_ag_db.sbatch`, job 37734973): COMPLETED
in **18m41s**, exit 0, peak RAM **28.5 GB** (250 GB requested — overkill; ~64 GB
would do). First submit (job 37734801) failed at `conda activate`
(`MKL_INTERFACE_LAYER: unbound variable`) — `set -euo pipefail`'s `-u` breaks
conda's activate.d; fixed by activating before `set -eo pipefail` (no `-u`) and
`cd`-ing to the repo root so submit-dir doesn't matter.

**`data/ag_db/` = 2.0 GB** (vs ~90 GB TSV):
- dims: variants 6,650 · tracks 5,563 · genes 19,695 · scorers 19 ·
  output_types 11 · regions 1.
- `ag_scores` partitioned region/expansion/output_type: 2x=102,782,767,
  5x=104,210,211, 20x=104,366,423 (~311M rows). 5x/20x have more
  SPLICE_JUNCTIONS/RNA_SEQ rows than 2x (larger expansions → more junctions) —
  expected; the non-genic outputs (ATAC/CHIP/…) are identical across expansions.

**Validation (`db/etl/validate.py` → "ALL CHECKS PASSED"):**
- 2x fact total == raw file (102,782,767) → INNER joins dropped nothing.
- FMR1 (`X-147912050-147912110-CGG`) @2x: row count 14,172==14,172 and RNA_SEQ
  `raw_score` sum 270.6513==270.6513 vs the raw TSV.
- 7 pathogenic loci flagged (ABCD3, DIP2B, FMR1, GIPC1, LRP12, PPP2R2B, XYLT1).
- quantile_score ∈ [-1,1]; no orphan scorer_id. A tiny set of raw_score are NULL
  (792/5,544/18,216 per expansion) — blank in source, faithfully preserved.
- Note: `validate.py` made env-overridable (`AG_THREADS`/`AG_MEM`, default
  4/24GB) so it runs on the small interactive node without OOM.

**`query_ag` live-tested against the real backend:**
- aggregation (pathogenic vs background mean RNA_SEQ per expansion) runs
  full-dataset, tiny result;
- inspect cap: 7,261,800-row query → first 1000 + TRUNCATED note;
- `to_file=` materialize: 73,014-row per-variant table → Parquet, head returned.

**Next: Phase 5** — wire `query_ag` into `run_biomni.py`.
