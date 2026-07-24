# biomni_log

Append-only run log for Biomni harness (`harness/run_biomni.py`) experiments.
Each run appends a `[start]` line and a `[done ]` line (status + deliverables).
Written automatically by the harness; do not hand-edit above this note.

2026-07-24 15:44:15  [start] q05b_s5_Tmp0.5_200m_20260724-154415  model=claude-sonnet-5  temp=0.5  timeout=12000s  query=q05b  out=output/July_24_2026/q05b_s5_Tmp0.5_200m_20260724-154415
2026-07-24 19:20:13  [done ] q05b_s5_Tmp0.5_200m_20260724-154415  status=success  log_entries=220  images=2  deliverables=3/3 [pathogenic_repeat_analysis.ipynb, Candidate_Identification.ipynb, Top_Candidate_Pathogenic_repeats.csv]

---

## 2026-07-24 — ag_db validation: s5 rerun vs 2026-07-21 baseline

**Purpose.** First run on the new **multi-region** AG DuckDB backend (5UTR+CDS+3UTR,
2.88B fact rows). Verify it reproduces the prior s5 result (which ran on the earlier
5UTR-only DB) for query_05_b. Both runs: Sonnet 5, temp ignored, same registered GCN
catalog (`B_Cat_5UTR_GCNs_masked.tsv`, 6,650 loci) + 7 pathogenic loci.

- NEW: `output/July_24_2026/q05b_s5_Tmp0.5_200m_20260724-154415`  (SLURM 37972802, COMPLETED, 3h36m)
- OLD: `output/July_20_2026/q05b_s5_Tmp0.5_200m_20260721-184059`

**Backend exercised OK.** The agent queried the new ag_db end-to-end via `query_ag`
and materialized 6 derived parquets (incl. a 230 MB `rnaseq_track_summary.parquet`,
`var_outtype_exp_summary.parquet`). Run produced all 3 deliverables + 2 plots.

**Candidate comparison (Top_Candidate_Pathogenic_repeats.csv, 50 rows each).**
- Gene overlap: **29/50** host genes shared, incl. EXOC3, LINGO3, MAB21L1, GLS,
  TMEM185A, RHOT1, FAM193B, DMRTC1B, AFF2, CARM1.
- Known-pathogenic recovery in top-50: FMR1 (both runs), LRP12 (new run additionally).
- Motif classes: OLD = 100% GCN (CCG 32, AGC 18). NEW = 42/50 GCN (CCG 37, AGC 5)
  **+ 8/50 non-GCN** (HLA-F/AAG ×2, DMRTC1B/AGG ×4, SYT17/ATC, TBC1D1/AGG).
- Scoring differs (OLD: composite_variance_score/final_score; NEW: instability_score
  + RNAseq/splice effect columns + mechanistic_hypothesis) — normal LLM run-to-run
  variability; ranks shift but the shared gene set is stable.

**Root cause of the non-GCN drift (NOT a backend defect).** The 5UTR variants dim now
holds the full TNR catalog `B_Cat_5UTR_msk_TNR.tsv` = 10,053 loci (6,650 GCN + 3,403
non-GCN), whereas the OLD DB's variants dim was GCN-only (6,650). The agent drew its
candidate universe from the DB `variants` view rather than the registered GCN catalog,
so out-of-scope non-GCN TNR loci (e.g. HLA-F GAA) leaked into the candidate list. The
AG scores themselves are correct and all 6,650 GCN loci are present with full scores.

**Minor issue.** One `ModuleNotFoundError: No module named 'query_ag'` — the agent tried
`import query_ag` inside a generated subprocess (no inherited sys.path); it recovered
via the registered tool. Suggested fix: `export PYTHONPATH=db` in the sbatch.

**CONCLUSION — the new multi-region ag_db is VALID.** It serves the AlphaGenome scores
correctly and reproduces the prior GCN analysis (29/50 gene overlap, known-pathogenic
recovery incl. FMR1 in both). The only discrepancy — 8 non-GCN candidates — is a
task-scoping artifact of the DB now carrying the full TNR set, not a data problem.
**Action for GCN-only runs:** constrain the candidate universe to GCN motifs, either by
keeping it anchored to the registered GCN catalog or by filtering
`WHERE canonical_motif IN ('CCG','AGC','CGG','CTG')` on the 5UTR variants.
