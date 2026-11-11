# 5'UTR — Hypothesis comparison across the models that recovered 2/2 withheld keys

_Generated 2026-11-11. Covers the five re-masked runs in `output/Nov_11_2026_remasked/`
(catalogs and ag_db variants dim without `Source` / `FoundInPerfectRepeatsInReference`).
All five recovered both withheld 5'UTR keys in their top 50._

| Model | Run folder | Run time | Narrative steps |
|---|---|---|---|
| Sonnet 5 (s5) | `q05b_s5_Tmp0.5_200m_20261111-095906` | 15 min | 97 |
| Opus 4.8 (o4.8) | `q05b_o4.8_Tmp0.5_200m_20261111-095909` | 7 min | 34 |
| Opus 5.5 (o5.5) | `q05b_o5.5_Tmp0.5_200m_20261111-095906` | 16 min | — |
| Fable 5.2 (f5.2) | `q05b_f5.2_Tmp0.5_200m_20261111-095907` | 34 min | — |
| Gemini 4 Carbon (gem4c) | `q05b_gem4c_Tmp0.5_200m_20261111-095906` | 1 h 11 min | 45 |

> Scope: this document compares hypotheses, evidence and scoring only. Withheld-key
> identities are deliberately omitted; key-level recovery is in the gitignored
> `.keys/5utr_eval_report.md`. Statistics are quoted as each run reported them and were
> not re-computed. Each model was run once, so differences between models are not
> separable from run-to-run variation.

## 1. Short version

**All five agree on the catalog signature.** Pathogenic 5'UTR GCN loci have long
reference tracts (median 9 vs 3 repeats; AUC ≈ 0.96) and unusually high population
length variability (HPRC long-read length stdev median 4.3 vs 0.0; AUC ≈ 0.99). All five
put both features in their final score, which is the common thread behind the 2/2
recoveries.

**They split on whether AlphaGenome adds anything once length is controlled:**

| Model | Verdict on AlphaGenome (AG) | AG in final score? |
|---|---|---|
| f5.2 | No AG feature survives length adjustment (0 of 101 at FDR 5%) | No |
| o5.5 | Most AG signal is a length artefact; a host-gene RNA effect adds a little | Yes (3 of 6 features) |
| s5 | One modality survives: 3D contact-map disruption at 20x | Yes (2 of 5 features) |
| o4.8 | "Biphasic" signature: early 2x epigenetic change plus 20x contact disruption | Yes (7 of 9 features) |
| gem4c | Eleven-axis "promoter collapse" signature, claimed to survive length matching | Yes (two of three score pillars) |

The stricter the length control, the less AG signal survives. The two runs that tested
every AG feature under length control (f5.2, o5.5) both concluded that AG contributes
little or nothing; the two with the lightest control (s5, o4.8) kept the contact-map
signal; gem4c used three length controls and still reports a broad AG signature.

## 2. Hypotheses tested, by theme

Verdicts: **S** supported, **S\*** supported after length control, **W** weak or
suggestive, **C** confounded by length, **R** rejected, — not tested.

| Hypothesis | s5 | o4.8 | o5.5 | f5.2 | gem4c |
|---|---|---|---|---|---|
| Longer reference tract | S | S | S | S | S |
| Higher population length variability | S | S | S\* | S\* | S |
| 3D contact-map disruption at 20x | S\* | C / W | S\* (drops out of multivariable model) | W | S\* |
| Non-linear dose response across 2x/5x/20x | S (contact maps, not length-adjusted) | S (contact maps) | R | C | S |
| Early (2x) loss of accessibility / TF binding / initiation | R | S (quantile scale only) | C | C | S\* |
| Active histone-mark loss at 20x | R | S (quantile scale) | C; mark-specific version R | C | S\* |
| Host-gene RNA decrease on expansion | R | — | W | W | S\* |
| Brain-specific effect | R | — | C (W for RNA at 20x) | R | R |
| Splicing disruption | R | R | — | R | R |
| Host-gene properties (expression, GC, biotype, essentiality) | R | — | — | R | R |
| Purity, mappability, neighbouring repeats | W / R | R | R | R | — |
| TSS proximity of the repeat | — | — | — | R (within length strata) | S |

### Where they agree

- **Length and population variability.** Unanimous, with near-identical numbers, since
  all five ran the same Mann-Whitney tests on the same two catalog columns.
- **Variability survives length control.** o5.5 (residualised AUC 0.99; length-matched
  AUC 0.97) and f5.2 (within-length-stratum percentile 0.954, permutation q = 0.0006)
  both tested this directly. s5 asserted it without a length-adjusted test.
- **Splicing is not a discriminator.** Rejected by all four runs that tested it.
- **No brain-specific effect and no host-gene-property signal.** Rejected wherever
  tested, apart from o5.5's nominal brain-biased RNA effect at 20x (p ≈ 0.03 before
  correction), which it nonetheless kept in its score.

### Where they disagree

- **Contact maps.** Everyone sees the raw 20x signal (AUC ≈ 0.93, p ≈ 4e-6). After
  length control it is p = 0.006 for s5 (regression residual), AUC 0.85–0.87 for o5.5,
  residual AUC 0.79 but FDR q = 0.43 for f5.2, and p = 0.010 for gem4c. o4.8's own joint
  regression leaves it non-significant (coefficient 0.24, CI −0.19 to 0.67), though its
  write-up still headlines it. o5.5 found it redundant once length and variability are
  in the model.
- **Early epigenetic perturbation.** o4.8 and gem4c report it; s5, o5.5 and f5.2 find
  nothing after correction or length adjustment. o4.8's result exists only on a
  quantile-deviation scale (raw-scale tests for the same modalities are all
  non-significant) and was not length-adjusted.
- **Dose response.** s5 and gem4c report a disproportionate 20x effect; o5.5 found the
  same curve shape for pathogenic and background loci once length is residualised
  (contact-map ratio AUC 0.66, p = 0.14); f5.2 found all dose-shape features vanish
  under length control.
- **Host-gene RNA.** gem4c reports early host-gene silencing that holds under length
  matching and at a fixed +25-repeat insertion; o5.5 and f5.2 see the same direction at
  nominal significance only; s5 rejects it.

## 3. Confound control

| Model | Length control | Applied to | Other controls |
|---|---|---|---|
| s5 | OLS residual on repeat count | Contact-map 20x magnitude only | BH-FDR over output type × expansion × metric |
| o4.8 | Joint logistic with length | Contact-map 20x only | BH-FDR; none for the 2x features |
| o5.5 | Residual on log tract length, plus a length-matched background (≥15 bp, n = 1,080) | Top 40 AG features and all later contrasts | BH-FDR; nested models, ablation, permutation |
| f5.2 | Length residual, length-stratified permutation, and length matching | Every one of 101 AG features | FDR per hypothesis family; excluded `StdevFromIllumina174k` as a label leak (missingness reveals the label) |
| gem4c | Within-length-bin z-scores, fixed +25-repeat interpolation, and a ≥5-repeat subset | All headline hypotheses | BH-FDR; host gene separated from bystander genes |

None of the five controlled for motif or GC composition within the GCN set, and none
could address ascertainment (disease loci are partly discovered because they are
variable).

## 4. Final scoring methods

| Model | Features | Model | Reported performance |
|---|---|---|---|
| s5 | Repeat count, HPRC stdev, T2T stdev, contact-map 20x, contact-map 20x/2x ratio | Unsupervised sum of rank z-scores; nothing fitted to labels | Known loci all in top 500 of 6,650 (3 of 7 in top 35); permutation p < 1e-5; no AUC, no held-out test |
| o4.8 | Five 2x quantile-deviation features (ATAC, TF, DNase, CAGE, histone), contact-map 20x and 20x−2x, repeat count, HPRC stdev | Class-balanced logistic regression on percentile ranks | In-sample AUC 0.95 (AG only) / 0.97 (combined); leave-one-out median rank 143 |
| o5.5 | Log tract length, HPRC stdev, T2T stdev, contact-map 20x, max RNA effect at 5x, brain-minus-other RNA at 20x | L2 logistic regression | Leave-one-positive-out AUC 0.980, versus 0.947 length only and 0.928 length + variability |
| f5.2 | Log repeat count, log HPRC stdev | L2 logistic regression | Out-of-fold AUC 0.980; 3 of 7 held-out known loci in top 50; median held-out rank 51 |
| gem4c | Three hand-weighted pillars: AG global z (0.35), AG length-matched z (0.30), repeat instability z (0.35) | Fixed-weight linear composite; no fitted weights | Out-of-fold AUROC 0.997; AG-only 0.985; instability-only 0.992 |

Points worth noting:

- **Two catalog features match everything else.** f5.2's two-feature model reaches the
  same cross-validated AUC (0.980) as o5.5's six-feature model, and gem4c's
  instability-only pillar (0.992) is within 0.005 of its full composite (0.997).
- **o5.5's AG gain rests on screened features.** Its jump from 0.928 to 0.980 comes
  from the RNA features, which it selected against the same seven positives outside the
  cross-validation loop; it flags the AUC as optimistic.
- **f5.2 tested the same additions and declined them.** Adding the contact-map feature
  gave AUC 0.980 with 4 of 7 in the top 50, but its pre-set rule required no loss on an
  independent check, so it kept the two-feature model.
- **s5 and gem4c fit no weights to labels**, which limits overfitting with n = 7 but
  means AG's weight in the score is a design choice, not a data-driven one.
- **Performance figures are not comparable across runs**: they mix in-sample AUC,
  leave-one-out ranks and out-of-fold AUC.

## 5. Mechanisms proposed

| Model | Mechanism |
|---|---|
| s5 | Intrinsic repeat instability plus disruption of local 3D chromatin architecture near the TSS; the non-linear dose response is likened to length-dependent penetrance thresholds |
| o4.8 | "FMR1-like" silencing generalised: early loss of accessibility, TF binding and initiation, then progressive 3D-contact reorganisation |
| o5.5 | Toxic RNA or gene silencing by analogy with FXTAS / NIID; a long, pure, germline-unstable tract is an expansion-prone substrate, with a brain-biased RNA effect |
| f5.2 | None derived from the data; per-candidate mechanisms are labelled "hypothesis, not tested" |
| gem4c | Two-stage cis loss of function at a TSS-proximal promoter: Pol II / TFIID / TF eviction at low dose, then collapse of active promoter marks and 3D contacts between 5x and 20x, with host-gene-selective silencing |

Silencing of the host gene is the shared idea (o4.8, o5.5, gem4c), but only gem4c
claims AG evidence for it that survives length control.

## 6. What is distinctive about each run

- **s5:** broadest list of negative results; lands on a single surviving AG modality
  and uses a fully unsupervised score.
- **o4.8:** shortest run; mixes two effect scales (raw for contact maps, quantile
  deviation for the rest); its headline contact-map claim is not supported by its own
  length-adjusted regression.
- **o5.5:** deliberately deflationary; asks the multivariable question (does AG add to
  length + variability?) with nested models, ablation and a permutation test.
- **f5.2:** confound-first and negative; three independent length adjustments on every
  feature, a pre-registered decision rule for adding AG to the score, and detection of a
  further label leak through missing values in `StdevFromIllumina174k`.
- **gem4c:** most elaborate; decodes AG scorer polarity, separates host from bystander
  genes, per-mark and per-factor features, a fixed-insertion-size control, and a
  length-free AG pillar in the score. States the fewest limitations.

## 7. Reading the 2/2 result

The shared ingredients of all five scores are reference length and population
variability, and those two alone perform as well as any fuller model. The 2/2
recoveries therefore say that the catalog signature generalises to unseen disease loci;
they do not discriminate between the five accounts of what AlphaGenome contributes. The
open scientific question from this set is whether gem4c's length-matched promoter-collapse
signature is real, given that f5.2 and o5.5 tested overlapping features under comparable
controls and found nothing after correction.
