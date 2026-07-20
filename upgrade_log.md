# Upgrade / Migration Log

Running record of migration work executed against `upgrade.md`. Newest last.

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
