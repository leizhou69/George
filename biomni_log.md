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
2026-07-24 19:59:39  [start] q05cds_s5_Tmp0.5_200m_20260724-195939  model=claude-sonnet-5  temp=0.5  timeout=12000s  query=q05cds  out=output/July_24_2026/q05cds_s5_Tmp0.5_200m_20260724-195939
2026-07-24 20:22:02  [done ] q05cds_s5_Tmp0.5_200m_20260724-195939  status=success  log_entries=185  images=1  deliverables=3/3 [pathogenic_repeat_analysis.ipynb, Candidate_Identification.ipynb, Top_Candidate_Pathogenic_repeats.csv]

---

## 2026-07-24 — CDS pathogenic-repeat run (s5), standalone baseline

First CDS task run (query_05_cds.txt) on the multi-region ag_db. No prior CDS run
to compare against, so this is a baseline soundness check.

- Run: `output/July_24_2026/q05cds_s5_Tmp0.5_200m_20260724-195939` (SLURM 37985680,
  COMPLETED 22m46s, status=success, 3/3 deliverables). MaxRSS 3.0 GB.
- Backend: queried the CDS partitions via `query_ag` and materialized several
  per-variant parquets (per_variant_summary, per_variant_signed, repress_20x, …)
  + ROC plots — CDS partitions served correctly end-to-end.
- Scope OK: top candidates span multiple TNR motif classes (CAG/AGC, CCG, CTG, GAG,
  TGG), i.e. the run correctly did NOT restrict to GCN (as intended for CDS).
- Result: 50 candidates, scored by CompositeScore = 20x epigenetic repression +
  Is_TranscriptionFactor + repeat features. Strongly enriched for developmental
  transcription factors (E2F4, MEOX2, HOXA13, DLX6, DACH1, ASCL1, SP8, POU4F2,
  ZIC5, FOXL2, MEF2A, …) — biologically consistent with known coding-repeat
  disorders (HOX/FOX/ZIC/RUNX/SOX polyQ & polyA genes).
- Known-pathogenic recovery: 3 of the 28 known pathogenic CDS genes (AR, FOXL2,
  HOXA13) appear in the top-50 — positive signal that the score ranks true
  coding-repeat-disease TFs highly (candidate list is not strictly novel-only).

**CONCLUSION:** the CDS run looks sound — the ag_db CDS partitions and the
`--region CDS` harness path work end-to-end, scoping is correct (all TNR classes),
and the candidate signature is biologically plausible with partial recovery of
known pathogenic loci. Cross-model CDS runs (Opus 4.8 + Opus 5, SLURM 37987506)
launched for comparison; summary to follow.

### Resource right-sizing (measured; feeds the biomni-slurm skill)
The 5'UTR s5 run (48 CPU / 420 GB) used **1.2 GB peak RAM** and **13.7 min CPU over
3.6 h** (0.3% mem, 0.13% CPU) — these agent runs are API-latency-bound, not
compute-bound (local work = DuckDB 4-thread queries + light pandas; model runs on
the provider side). The CDS s5 run peaked at 3.0 GB. New runs use **8 CPU / 64 GB**
(ratio-clean at HPG's 8 GB/core, ~20-50x headroom); the Opus CDS job scheduled
**instantly** at that size vs the old 48/420 sitting in PENDING (Resources). See
`.claude/skills/biomni-slurm/SKILL.md`.
2026-07-24 20:30:20  [start] q05cds_o4.8_Tmp0.5_200m_20260724-203020  model=claude-opus-4-8  temp=0.5  timeout=12000s  query=q05cds  out=output/July_24_2026/q05cds_o4.8_Tmp0.5_200m_20260724-203020
2026-07-24 20:36:24  [done ] q05cds_o4.8_Tmp0.5_200m_20260724-203020  status=success  log_entries=66  images=0  deliverables=3/3 [pathogenic_repeat_analysis.ipynb, Candidate_Identification.ipynb, Top_Candidate_Pathogenic_repeats.csv]
2026-07-24 20:36:24  [start] q05cds_o5_Tmp0.5_200m_20260724-203624  model=claude-opus-5  temp=0.5  timeout=12000s  query=q05cds  out=output/July_24_2026/q05cds_o5_Tmp0.5_200m_20260724-203624
2026-07-24 21:18:45  [start] q05b_o5_Tmp0.5_200m_20260724-211845  model=claude-opus-5  temp=0.5  timeout=12000s  query=q05b  out=output/July_24_2026/q05b_o5_Tmp0.5_200m_20260724-211845
2026-07-24 21:21:12  [start] q05b_o5_Tmp0.5_200m_20260724-212112  model=claude-opus-5  temp=0.5  timeout=12000s  query=q05b  out=output/July_24_2026/q05b_o5_Tmp0.5_200m_20260724-212112
2026-07-24 21:36:55  [done ] q05b_o5_Tmp0.5_200m_20260724-212112  status=success  log_entries=80  images=0  deliverables=3/3 [pathogenic_repeat_analysis.ipynb, Candidate_Identification.ipynb, Top_Candidate_Pathogenic_repeats.csv]
2026-07-24 21:36:55  [start] q05b_o4.8_Tmp0.5_200m_20260724-213655  model=claude-opus-4-8  temp=0.5  timeout=12000s  query=q05b  out=output/July_24_2026/q05b_o4.8_Tmp0.5_200m_20260724-213655
2026-07-24 21:43:29  [done ] q05b_o4.8_Tmp0.5_200m_20260724-213655  status=success  log_entries=60  images=0  deliverables=3/3 [pathogenic_repeat_analysis.ipynb, Candidate_Identification.ipynb, Top_Candidate_Pathogenic_repeats.csv]

---

## 2026-07-24 — 5'UTR cross-model comparison (o5 / o4.8 / s5)

Three 5'UTR GCN runs on the multi-region ag_db: o5 (`...q05b_o5_...212112`), o4.8
(`...q05b_o4.8_...213655`), s5 (existing `...q05b_s5_...154415`). Compared with the
compare-biomni-output skill (rank-weighted consensus of top-20).

- **Withheld-key recovery (aggregate; identities in gitignored `.keys/5utr_eval_report.md`):**
  s5 **2/2**, o4.8 **1/2**, o5 **1/2**; **consensus 2/2**. (Note: for 5'UTR s5 was best,
  the inverse of the CDS run where o5 led — model performance is task-dependent.)
- **Overlap:** low agreement (top-50 Jaccard 0.06–0.16); 4 genes in all three top-50.
- **Consensus top:** NCOR2, MAB21L1, RHOT1, TMEM185A, AFF2, HLA-F, STK39, PRKG1, BCLAF3…
- **Hypothesis/mechanism divergence:** s5 → signal is intrinsic **repeat instability**
  (AlphaGenome rejected, 0 AG features); o4.8 → **AG CONTACT_MAPS 3D dose-response**;
  o5 → **conjunction** (instability gate × residualized AG silencing signature). s5 and o5
  agree HPRC instability is the single strongest discriminator. Full writeup:
  `analysis/comparisons_5utr/5UTR_model_hypothesis_comparison.md`.
- Shareable outputs (predictions only): `analysis/comparisons_5utr/{consensus_top_candidates.csv,
  overlap_shared_counts.csv, comparison_report.md}`.

CORRECTION to the earlier CDS s5 note (2026-07-24 CDS baseline section): the true
evaluation metric is recovery of the **withheld** keys in `.keys/`, NOT the 28 given
pathogenic loci the agent was shown. (CDS consensus recovery is finalized when the CDS o5
run completes.)


---

## 2026-07-24 — CDS cross-model comparison (o5 / o4.8 / s5)

Three CDS runs on the multi-region ag_db (all-TNR scope): s5 (`...q05cds_s5_...195939`),
o4.8 (`...q05cds_o4.8_...203020`), o5 (`...q05cds_o5_...203624`). NOTE: the o5 CDS SLURM
process hung after its deliverables were written (~20:47) — same thread-timeout hang as the
earlier s5 5'UTR run — and was cancelled (37987506); its candidate CSV is final/stable.

- **Withheld-key recovery (aggregate; identities in gitignored `.keys/cds_eval_report.md`):**
  s5 0/3, o4.8 1/3, o5 2/3; consensus 2/3.
  (o5 led on CDS — inverse of the 5'UTR run where s5 led; model performance is task-dependent.)
- **Overlap:** top-50 Jaccard ~0.22-0.28; 13 genes shared across all three.
- **Consensus top:** MAML3, POU4F2, BMP2K, ZIC5, DENND4B, E2F4, TNRC18, ASCL1 ...
- Hypothesis/mechanism writeup: `analysis/comparisons_cds/CDS_model_hypothesis_comparison.md`.
- Shareable outputs (predictions only): `analysis/comparisons_cds/{consensus_top_candidates.csv,overlap_shared_counts.csv,comparison_report.md}`.
