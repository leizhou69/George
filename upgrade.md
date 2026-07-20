# Upgrade / Migration Plan

Migrate the 5'UTR-TNR project out of the Biomni fork into a **clean sibling
project repo**, with **Biomni as an editable-installed dependency**, and stand up
the **DuckDB/Parquet AlphaGenome backend** (see `Rpt_Ds/AG_DB_DESIGN.md`) so the
pipeline can scale to other gene regions.

Status: **plan (no execution yet)** — review before running any step.

---

## Decisions locked
- **New sibling project repo**, fresh git history. Name: **George**
  (dir `/blue/zhou/leizhou/Agents/George`).
- **Biomni**: editable install (`pip install -e`) of the patched fork; drop the
  `sys.path.append("./")` shadowing.
- **AG data**: DuckDB over partitioned Parquet (per `AG_DB_DESIGN.md`).

## Constraints & safety principles
1. **~378 GB of data does not get copied.** `Rpt_Ds/data` = 86 GB,
   `Rpt_Ds/output` = 292 GB. All paths are on one mount (`/blue/zhou`), so any
   relocation is an **instant `mv` (metadata rename)**, and symlinks are free.
2. **Preserve the Biomni patches** (list below) — they are load-bearing.
3. **Delete-last / backups.** Never delete the 29 GB source TSVs until the DB
   path is proven end-to-end (backups also exist in separate storage).
4. **Freeze, don't destroy.** The old repo `Biomni_Rpts_Ds` stays intact as a
   read-only archive — it holds the paper's provenance and the 292 GB of prior
   run outputs.
5. Every phase ends with a **verification checkpoint**; do not proceed on failure.

## Paths & variables (adjust once, reuse)
```
OLD=/blue/zhou/leizhou/Agents/Biomni_Rpts_Ds        # current repo (becomes archive)
FORK=/blue/zhou/leizhou/Agents/biomni-fork          # extracted patched Biomni
PROJECT=/blue/zhou/leizhou/Agents/George         # new clean project repo
                                                     # data lives at $PROJECT/data (moved in Phase 3, instant rename)
ENV=biomni_e1                                        # conda env
```

## Biomni patches the fork must carry
| File | Patch | State |
|---|---|---|
| `biomni/llm.py` | `_anthropic_rejects_sampling_params()` → skip `temperature` on Opus 4.7+/Sonnet 5; `max_tokens` 8192→32000 | committed (`e021e51`, `eb63ba0`) |
| `biomni/agent/a1.py` | tool `observation` appended as `HumanMessage` (prefill fix, `Rpt_Ds/fix_prefill_20260327.md`) | **uncommitted — commit before extracting** |

---

## Target end-state layout
```
biomni-fork/                      # editable-installed dependency (own git repo)
  biomni/ ...  pyproject.toml  README.md  PATCHES.md

George/                        # new clean project repo
  README.md  CLAUDE.md  environment.md
  pyproject.toml (or requirements.txt)      # depends on -e ../biomni-fork
  harness/
    run_biomni.py                # the corrected harness
    slurm/  512GB.sbatch  196GB.sbatch
  db/
    AG_DB_DESIGN.md
    etl/   (DuckDB ETL scripts — built in Phase 4)
    query_ag.py                  # the agent query tool
  queries/  query_05_b.txt
  analysis/  pathogenic_repeat_analysis.ipynb  Candidate_Identification.ipynb ...
  manuscript/  5UTR_TNR_0605.pdf
  results/  Top_Candidate_Pathogenic_repeats.csv
  data/                          # moved here from OLD/Rpt_Ds/data (instant rename, same mount); gitignored
    5UTR/  (+ future 3UTR, ...)  #   region source files
    ag_db/                       #   DuckDB/Parquet backend (built Phase 4)
  output/                        # fresh run outputs (new); gitignored

  archive/                       # optional: superseded notebooks/queries
```

---

## Phase 0 — Prep (no changes yet)
- [ ] Pick the repo name; set `PROJECT`.
- [ ] Confirm `git status` on `$OLD` is understood; **commit the uncommitted
      a1.py prefill fix** so the fork carries it:
      `cd $OLD && git add biomni/agent/a1.py && git commit` (message: "Prefill fix: observation as HumanMessage").
- [ ] Confirm the backup of the 29 GB TSVs exists and is restorable.
- [ ] Snapshot the working env: `conda list -n $ENV --export > $OLD/env_snapshot_$(date +%F).txt`.
- ✅ Checkpoint: clean `git status` on `$OLD` (except intended); backup verified.

## Phase 1 — Extract the patched Biomni into its own repo + editable install
Clone the current repo to `$FORK`, strip it down to just the installable package,
then editable-install it so `import biomni` is unambiguous.
- [ ] `git clone $OLD $FORK`
- [ ] In `$FORK`, remove project-specific paths, keep only the package + packaging:
      `git rm -r Rpt_Ds run_biomni.py *.sbatch tutorials figs docs test.ipynb slurm-*.out CLAUDE.md upgrade.md` (keep `biomni/`, `pyproject.toml`, `MANIFEST.in`, `LICENSE`, `.pre-commit-config.yaml`, `.gitignore`).
- [ ] Add `$FORK/PATCHES.md` documenting the two patches above (so divergence from upstream is explicit).
- [ ] Point `origin` at a new empty remote (or leave local); keep the upstream
      remote for future rebases: `git remote rename origin upstream` (optional).
- [ ] `git commit -am "Strip to installable Biomni fork"`.
- [ ] Install editable: `conda activate $ENV && pip install -e $FORK`.
- ✅ Checkpoint (the critical one — proves the shadowing is gone):
  ```
  cd /tmp && python -c "import biomni,os; print(os.path.dirname(biomni.__file__))"
  # must print .../biomni-fork/biomni  (NOT the old repo, NOT site-packages/biomni 0.0.8)
  python -c "from biomni.llm import _anthropic_rejects_sampling_params as f; print(f('claude-opus-4-8'))"  # -> True
  ```
  If it still resolves elsewhere: `pip uninstall biomni` (removes the 0.0.8 wheel) then re-`pip install -e $FORK`.

## Phase 2 — Create the new project repo
- [ ] `mkdir -p $PROJECT && cd $PROJECT && git init`
- [ ] Create the directory skeleton (harness/ db/ queries/ analysis/ manuscript/ results/ output/).
- [ ] Add `.gitignore`: `data`, `output/`, `*.parquet`, `db/ag_db/`, `.env`,
      large `.tsv`, `*.ipynb_checkpoints`, `__pycache__/`. (Never track data/outputs.)
- [ ] Add `environment.md` / `pyproject.toml` recording the dependency:
      `pip install -e $FORK` + `duckdb`, `pyarrow`, plus the conda env name.
- [ ] `pip install -c conda-forge` (or pip) **duckdb** into `$ENV` (needed for the DB).
- ✅ Checkpoint: `git status` clean-ish; `python -c "import duckdb, biomni"` works.

## Phase 3 — Migrate the keepers (see inventory table below)
- [ ] Copy keepers from `$OLD` into the new structure (harness, query_05_b.txt,
      ms/ → manuscript/, AG_DB_DESIGN.md → db/, active notebooks → analysis/,
      Top_Candidate…csv → results/, CLAUDE.md → adapt).
- [ ] **Move data into George** (instant rename — same `/blue/zhou` mount, NOT an
      86 GB copy): `mv $OLD/Rpt_Ds/data $PROJECT/data`
      - Verify first that the target doesn't exist and the mount matches
        (`df -P $OLD/Rpt_Ds/data $PROJECT | awk 'NR>1{print $6,$1}'`).
      - Reversible: `mv $PROJECT/data $OLD/Rpt_Ds/data`. `$OLD` is being archived,
        so it losing its data dir is expected; backups also exist.
      - George's data is now self-contained (no symlink, no dependency on `$OLD`).
- [ ] Update paths in `run_biomni.py`: `DATA_FILES` and `data_root` to the new
      layout (`data/5UTR/...`, `data/ag_db`). Keep the corrected 5-entry DATA_FILES.
- [ ] Copy `.env` (do **not** commit it).
- ✅ Checkpoint: `python harness/run_biomni.py --help` runs; DATA_FILES all resolve
      (reuse the existence check we ran earlier); `import biomni` = fork.

## Phase 4 — Build the AG DuckDB/Parquet backend
Follow `db/AG_DB_DESIGN.md` §5/§9:
- [ ] Prototype ETL on one file (`B_5UTR_all_GCN_2xAG.tsv`) → dims + one fact
      partition set; validate a known pathogenic locus; measure size/time.
- [ ] Full 5'UTR ETL (all three expansions) → `data/ag_db/`.
- [ ] Implement `db/query_ag.py` (1k-row context cap + `to_file=` materialize mode).
- ✅ Checkpoint: `ag_db` size ≈ 1–2 GB; row counts per partition match source;
      spot-check scores for a pathogenic locus vs the raw TSV.

## Phase 5 — Rewire the harness to the DB
- [ ] In `run_biomni.py`, drop the three giant AG entries from `DATA_FILES`;
      register `query_ag` as a Biomni tool + add the schema/example-queries block
      to the prompt. Keep small files (catalog, pathogenic) registered as-is.
- ✅ Checkpoint: a dry agent run issues SQL via `query_ag`, gets ≤1k-row samples,
      and can aggregate/materialize without loading TSVs.

## Phase 6 — Validate parity
- [ ] Re-run the 5'UTR experiment (`s5`, `o4.8`) against the DB backend.
- ✅ Checkpoint: results consistent with the prior TSV-based analysis (candidate
      overlap / key stats). This is the gate for Phase 7.

## Phase 7 — Reclaim space (delete-last)
- [ ] **Only after Phase 6 parity:** remove the 29 GB source TSVs
      (`data/5UTR/B_5UTR_all_GCN_{2x,5x,20x}AG.tsv`), backups retained elsewhere.
      Reclaims ~87 GB.
- ✅ Checkpoint: pipeline still runs end-to-end on `ag_db` alone.

## Phase 8 — Freeze the old repo as archive
- [ ] Add `$OLD/README_ARCHIVED.md` pointing to `$PROJECT` and `$FORK`.
- [ ] Tag it: `cd $OLD && git tag archive-pre-migration && git commit -am "Archive: superseded by George + biomni-fork"`.
- [ ] Leave the 292 GB `Rpt_Ds/output` in place (historical provenance) unless you
      choose to prune separately.
- ✅ Checkpoint: George is **fully independent** of `$OLD` (its data now lives
      under `$PROJECT/data`); `$OLD` can be archived without breaking George.

---

## Keep / Archive / Drop inventory (from `$OLD`)
| Item | Action | Destination |
|---|---|---|
| `biomni/` (patched) + `pyproject.toml`, `MANIFEST.in`, `LICENSE` | → fork | `$FORK` |
| `run_biomni.py` | keep | `$PROJECT/harness/` |
| `512GB.sbatch`, `196GB.sbatch` | keep | `$PROJECT/harness/slurm/` |
| `Rpt_Ds/query_05_b.txt` | keep | `$PROJECT/queries/` |
| `Rpt_Ds/query_01..05.txt` | archive | `$PROJECT/archive/queries/` |
| `Rpt_Ds/ms/5UTR_TNR_0605.pdf` | keep | `$PROJECT/manuscript/` |
| `Rpt_Ds/AG_DB_DESIGN.md`, `upgrade.md`, `CLAUDE.md` | keep (adapt) | `$PROJECT/db/`, `$PROJECT/`, `$PROJECT/` |
| `Rpt_Ds/fix_prefill_20260327.md` | → fork docs | `$FORK/PATCHES.md` (fold in) |
| `pathogenic_repeat_analysis.ipynb`, `Candidate_Identification.ipynb`, `Evaluate.ipynb`, `Verify.ipynb` | keep (active) | `$PROJECT/analysis/` |
| `CompareOutput*.ipynb` (4 dated) | archive | stay in `$OLD` (archive) |
| `verify_q05_*.md` (6), `verify_q05_*.csv` | archive | stay in `$OLD` |
| `Top_Candidate_Pathogenic_repeats.csv` | keep | `$PROJECT/results/` |
| `Rpt_Ds/data/` (5UTR + future regions) | move (instant `mv`) | `$PROJECT/data/` |
| `Rpt_Ds/output/` (292 GB) | leave archived | `$OLD` |
| `Rpt_Ds/DoNotUse/`, `comparisons/`, one-off PNGs, `CCG_*`, `Verifying_keys.txt` | archive | stay in `$OLD` |
| `tutorials/`, `figs/`, `test.ipynb`, `slurm-*.out` | drop | already deleted / not migrated |

---

## Rollback & safety
- Phases 1–2 are additive (clone/copy) — abort by deleting `$FORK`/`$PROJECT`.
- Phase 3's data step is a **rename** (`mv`), the one change to `$OLD` before
  archival — reversible with `mv $PROJECT/data $OLD/Rpt_Ds/data`; backups also
  exist. Copy keepers before the `mv` so a mistake never risks the data.
- The only destructive step is **Phase 7** (delete TSVs), gated on Phase 6 parity
  and external backups. If parity fails, stop and keep TSVs.
- If the editable install misbehaves, `pip uninstall biomni` and re-install; the
  old repo still works via its `sys.path` hack as a fallback.

## Post-migration checklist
- [ ] `import biomni` → `$FORK` from any cwd.
- [ ] `run_biomni.py` runs from `$PROJECT` with no `sys.path.append("./")`.
- [ ] Agent queries AG data via `query_ag` (no 29 GB reads).
- [ ] 5'UTR parity confirmed; source TSVs removed; ~87 GB reclaimed.
- [ ] `$OLD` tagged/archived; `$PROJECT` + `$FORK` are the live repos.
- [ ] 3'UTR onboarded via the same ETL (first real test of multi-region).
