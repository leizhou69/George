# Scoring Model Comparison: S5 (5'UTR) vs O5 (CDS)
_Generated 2026-08-24. Compares the actual candidate-scoring methodology each model built in its
best-performing run per region — s5 on 5'UTR (`q05b_s5_Tmp0.5_200m_20260724-154415`, withheld-key
recovery 2/2) and o5 on CDS (`q05cds_o5_Tmp0.5_200m_20260724-203624`, withheld-key recovery 2/3)._
_Underlies `results/Top_Candidates_5UTR_24July26.csv` and `results/Top_Candidates_CDS_24July26.csv`._

This is **not** a repeat of `analysis/comparisons_{5utr,cds}/` (those compare o5/o4.8/s5 candidate
lists *within* a region). This asks a different question: given that a different model won each
region, how did the two winning models actually build their scoring function — same statistical
recipe applied to different data, or genuinely different approaches?

## Task scope differs going in

| | 5'UTR (s5) | CDS (o5) |
|---|---|---|
| Catalog size | ~10,053 GCN loci (5'UTR task is GCN-motif-restricted by design) | 34,891 all-TNR loci (28 positive, 34,863 benign) — not motif-restricted upfront |
| Known pathogenic (n) | 7 | 28 |
| Effective independent labels | 7 | ~23 genes (HOXA13, ARX, ATXN7, HTT each contribute 2-3 loci) |

CDS gives o5 4x the positives and no motif prefilter, which is enough to support genuine supervised
learning; 5'UTR's n=7 pushes s5 toward a simpler, hand-specified statistic where every design choice
can be justified individually rather than fit.

## The two scoring models are fundamentally different kinds of model

| | **s5 — 5'UTR: fixed-weight composite z-score** | **o5 — CDS: cross-validated logistic regression** |
|---|---|---|
| Model family | Linear combination of 4 hand-picked z-scored features, weights **set by hand** | `StandardScaler` + `LogisticRegression(class_weight='balanced')`, weights **learned** by fitting to labels |
| Weight source | Weights (0.45 / 0.30 / 0.20 / 0.05) assigned by **rank order of each feature's univariate Cohen's d**, not optimized | Standardized coefficients estimated by maximum likelihood; magnitude and sign both learned |
| Features in the score | `resid(LPSLengthStdevFromHPRC100 ~ log(1+L))`, `log(1+NumRepeatsInReference)`, `resid(StdevFromT2TAssemblies ~ log(1+L))`, `-ReferenceRepeatPurity` | `logL`, `LPS`, `T2T`, `collapse_resid` (length-residualized 20x histone log2FC), `contact_resid` (length-residualized 3D contact-map score), `pan_neg` (5-modality fraction-negative), `motif_class_path` (AGC/CCG/CNG/ACG indicator) |
| Role of AlphaGenome | **Excluded from the score entirely.** AG RNA-seq magnitude was tested and explicitly rejected as a discriminator (pathogenic effect size *smaller*, 0.07 vs 0.28 at 20x, p=0.046 in the wrong direction); AG is used only for **post-hoc annotation** of the already-ranked candidates (host-gene RNA-seq/splicing, OMIM links) | **Central to the score.** Two AG-derived features (chromatin collapse, contact-map residual) plus a third summary (pan-modality negativity) are in the trained model; an ablation shows adding them raises AUPRC by ~34% over length alone |
| Model selection | None performed — one scheme (the 4-feature weighted sum) was built and adopted directly | Explicit **model comparison**: length-only vs length+instability vs length+AG vs full 7-feature logistic vs full 7-feature random forest, scored by 10-fold CV AUPRC (5 seeds); logistic chosen over random forest for interpretability and lower overfit risk at n=28 |
| Validation | AUC = 0.992 (in-sample); **leave-one-out** on the residualization step only (refit the length-regression excluding each of the 7 positives, recheck its rank) — 5/7 positives still land in top 1% | **10-fold CV, 5 seeds** for every candidate scheme (proper held-out prediction, not just in-sample fit); **leave-one-out stability check** on the final ranking itself (refit excluding each of 28 positives, Spearman rho of the resulting candidate order vs. the full-data order); separate **enrichment test** against a held-out list of 15 known repeat-disease genes never used in training (Fisher's exact OR, top-200 candidates) |
| Confounder handling | Residualizes 2 of 4 features against log(reference length) via OLS; purity and repeat count used directly | Residualizes AG features against a **quadratic** in log(length) fit on **benign loci only** (so the model can't relearn length through them); explicitly excludes `ACTIVE_SUM`-type scorers because they measure baseline chromatin state, not effect, and are confounded with promoter-proximal location |
| Final score meaning | `instability_score` = unbounded weighted z-score sum; reported alongside a separately computed `percentile_rank` (0–100) since the raw score has no natural scale | `PathogenicityScore` = `predict_proba` output of the fitted logistic model — a genuine (if uncalibrated) probability in [0, 1]; top candidates cluster at >0.9999, bucketed into a `ConfidenceTier` (e.g. "Very High") |
| Multiple-testing correction | Benjamini-Hochberg FDR used in the earlier univariate screen (Section 2) that fed the Cohen's-d weight ranking, not in the final score itself | BH-FDR applied across 486 naive + 348 length-adjusted univariate tests during feature discovery, upstream of the final 7-feature model |

## Why the approaches diverge: n, not model philosophy

Both notebooks run the *same* upstream discovery process — univariate screening of catalog and
AlphaGenome features against known pathogenic loci, Cohen's d + Mann-Whitney/FDR, explicit
residualization against reference repeat length to avoid confounding, and an explicit
called-out rejection of hypotheses that didn't hold up (s5 rejects AG-magnitude and tissue-expression
signals; o5 rejects splicing disruption, tissue-specific collapse, and multi-modal Q99 coincidence
as independent signals). The divergence is downstream, at the point of turning validated signals into
a ranking function:

- **s5 (n=7)** treats the exercise as "we found one dominant, well-powered signal (population repeat
  instability, Cohen's d=12.3) — build the simplest defensible combination of it with 3 secondary
  correlates, weighted by effect size, and stop." No optimization step exists to overfit with, by
  construction.
- **o5 (n=28)** treats it as a genuine classification problem: enough positives to hold out folds,
  compare model families, and fit real coefficients — while still guarding against the n=28 sample
  size (LOO rank-stability check, motif indicator flagged in the caveats as "a hard filter... its
  coefficient is inflated," explicit statement that AUPRC gain is concentrated at the top of the
  ranking, not global separation).

Put simply: **s5 could not have safely fit a logistic regression on 7 positives, and didn't try; o5
had enough positives to fit one, and validated that doing so actually helped (AUPRC 0.375 vs 0.280
for length alone) rather than assuming it would.**

## Consequence for how to read the two candidate lists

- 5'UTR candidates are ranked by a **transparent, unweighted-by-data statistic** — every candidate's
  score decomposes into 4 interpretable numbers with fixed weights. AlphaGenome evidence attached to
  each candidate is *descriptive*, not part of why it ranked where it did.
- CDS candidates are ranked by a **fitted, AlphaGenome-informed probability** — the score itself
  already encodes the AG chromatin-collapse signal, so a high `PathogenicityScore` is doing double
  duty as both "long/unstable repeat" and "AG-predicted regulatory consequence," which is why o5's
  own caveats stress the list is "not a set of independent discoveries so much as a prioritisation"
  dominated by length and motif class.

Neither is more "correct" in the abstract — s5's choice is the right one at n=7, and o5's is the
right one at n=28. The practical implication is that the two `PathogenicityScore`/`instability_score`
columns in `results/Top_Candidates_5UTR_24July26.csv` and `results/Top_Candidates_CDS_24July26.csv`
are **not on comparable scales and were not produced by comparable procedures** — don't rank-merge
them directly across regions without accounting for this.
