# 5'UTR Pathogenic-Repeat Analysis — Cross-Model Hypothesis & Mechanism Comparison

_Generated 2026-07-24. Compares the scientific reasoning (hypotheses tested, mechanisms
proposed) of three Biomni agent runs on the identical 5'UTR GCN task
(`queries/query_05_b.txt`, GCN-scoped) against the multi-region AG DuckDB backend._

| model | run dir | analysis depth | narrative source |
|---|---|---|---|
| **Sonnet 5** (s5) | `output/July_24_2026/q05b_s5_Tmp0.5_200m_20260724-154415` | thorough (23 min) | `.md` report |
| **Opus 4.8** (o4.8) | `output/July_24_2026/q05b_o4.8_Tmp0.5_200m_20260724-213655` | moderate (7 min, competent) | `.md` report |
| **Opus 5** (o5) | `output/July_24_2026/q05b_o5_Tmp0.5_200m_20260724-212112` | thorough (rigor-heavy) | `.md` report |

> Scope note: this document compares **mechanistic hypotheses only**. Recovery of the
> held-out evaluation keys is tracked separately (`biomni_log.md` + gitignored eval);
> withheld-key identities are omitted here.

---

## 1. TL;DR

All three agree pathogenic 5'UTR GCN repeats are (a) **longer** in the reference and,
above all, (b) **population-length-unstable** — and all three treat reference repeat
length as a confounder to control. But they **disagree on where the discriminating
signal lives**:

| model | where the signal lives | one-line mechanism |
|---|---|---|
| **s5** | **Catalog repeat instability only** — AlphaGenome effect magnitude explicitly REJECTED (even opposite-direction); final score uses **zero AG features** | intrinsic population-level repeat instability |
| **o4.8** | **AlphaGenome CONTACT_MAPS 3D-chromatin dose-response** (primary), + reduced ATAC/RNA | non-linear 3D-chromatin disruption + FMR1-like silencing |
| **o5** | **Both, in a gate** — instability is the NECESSARY Stage-1 gate (single best feature, AUC 0.993), AG is a Stage-2 re-ranker that adds non-redundant signal (AUC 0.771 within unstable loci) | instability (can-it-expand) × combinatorial AG silencing signature |

**s5 and o5 independently find the same single strongest discriminator — HPRC long-read
repeat-length instability** (s5 Cohen's d=12.3 / AUC 0.992; o5 AUC 0.993). Their
difference is what to do with AlphaGenome: s5 discards it, o5 keeps it as a secondary
re-ranker. o4.8 is the outlier — it kept AlphaGenome (contact maps) as the *primary*
signal and leaned less on the instability catalog fields.

**Cross-task contrast:** for CDS, all three models were AG-chromatin-centric (see
`../comparisons_cds/CDS_model_hypothesis_comparison.md`); for 5'UTR, two of three
concluded the answer is largely **not** in AlphaGenome but in intrinsic repeat
instability — consistent with the biology (5'UTR GCN disease ≈ FMR1-style
expansion-plus-promoter-silencing, gated by the repeat's capacity to expand).

---

## 2. Shared conclusions

1. **Length is a confounder** — all three: pathogenic loci have longer reference tracts
   (median ~9–10 vs ~3) and all control for it (residualization and/or length-matching).
2. **Repeat instability discriminates strongly** — HPRC-100 LPS length stdev and T2T
   allele-freq stdev are far higher for pathogenic loci; >95% of background loci are
   "frozen" (stdev ≈ 0). s5 and o5 make this the top feature; o4.8 uses length but not the
   instability fields as heavily.
3. **FMR1-like silencing is the recurring mechanism** — reduced host-gene RNA output /
   loss of active-promoter chromatin on expansion (all three, in different weights).
4. **Splicing is not a discriminator** (all three; expected for 5'UTR).
5. **Host-gene-level signals are weak/absent** — biotype, GC content, GTEx tissue
   enrichment all n.s. (s5 tested and rejected; o5 rejected a single shared causal tissue).
6. **AFF2 / FRAXE cited as an external positive control** — a known 5'UTR repeat disease
   outside the 7 given loci that each run surfaced as a top candidate (the runs' own
   validation move).

---

## 3. The key divergence — is the signal in the catalog (instability) or in AlphaGenome?

| dimension | s5 | o4.8 | o5 |
|---|---|---|---|
| **primary discriminator** | repeat instability (HPRC/T2T) | AG CONTACT_MAPS dose-response | instability (gate) + AG (re-rank) |
| **AlphaGenome verdict** | REJECTED as discriminator (magnitude n.s. / reversed) | primary signal (3D contacts) | naive magnitude is a length artifact; but a residualized 3-pillar AG signature adds real signal |
| **AG features in final score** | none | cm_delta, cm_max20, cm_e20, atac_low (+ length, ml_prob) | RNA-silencing + RNA tissue-variance + contact-disruption (gated) |
| **dose-response** | reframed as "early saturation" (patho extreme at 2×–5×) | non-linear contact slope Δ(20×−2×) | super-linear/convex histone-effect ratio (threshold collapse) |
| **conclusion shape** | univariate: instability | univariate: 3D-chromatin | conjunction: instability × combinatorial AG |

**Reconciliation.** s5 and o5 agree instability is the dominant axis; o5's more nuanced
result — that a *length-residualized* AG signature (RNA silencing direction + cross-tissue
variance + contact disruption) still adds non-redundant signal *within* the unstable
subset — is the bridge between s5 ("AG is nothing") and o4.8 ("AG is everything"). o4.8's
contact-map "primary signal" survives its own length control but o4.8 did not test it
against instability, so it likely captures part of what o5 attributes to the gate.

---

## 4. Per-model detail

### Sonnet 5 (s5) — "it's repeat instability, not AlphaGenome" (thorough)
- **Inverts the task framing:** although the deliverable is AG expansion predictions, s5
  concludes the discriminating signal is almost entirely in the **static population
  catalog** (repeat instability), and reports AG functional magnitude as a **failed**
  hypothesis (H4 rejected, even opposite-direction; H5 combinatorial rejected; H6 threshold
  only suggestive).
- **Top features:** `LPSLengthStdevFromHPRC100` (d=12.3, p=7.4e-11), `NumRepeatsInReference`
  (d=4.25), `StdevFromT2TAssemblies` (d=3.74); excess instability survives regressing out
  length (H2 supported, LOO-robust for 5/7).
- **Score = "Repeat Instability Score":** 0.45·resid-HPRC-var + 0.30·log-NumRepeats +
  0.20·resid-T2T-var + 0.05·(−purity); **zero AG features**; AUC 0.992. Per-candidate
  mechanistic text invokes uORF/RAN-translation/R-loop RNA toxicity.

### Opus 4.8 (o4.8) — "3D-chromatin (CONTACT_MAPS) dose-response" (moderate, competent)
- **Distinctive angle:** CONTACT_MAPS 3D-contact disruption as the *primary* discriminator,
  explicitly non-linear (2× ≈ null → 20× strong), plus reduced ATAC accessibility and RNA
  silencing (FMR1-like). Confirmed length is a confounder (NumRepeats alone AUC 0.964) but
  showed the contact dose-response is **independent and additive** (length-adjusted residual
  p=0.0027; length-matched composite AUC 0.890).
- **Score:** hand-weighted percentiles — `cm_delta`(0.30, contact Δ20×−2×) +
  `cm_max20`(0.20) + `num_rep`(0.20) + `atac_low`(0.15) + `cm_e20`(0.15), blended 50/50 with
  a balanced-logistic `ml_prob`. Permutation test (p<0.0005), LOO, and AFF2/FRAXE external
  recovery (rank #3).
- **Depth:** competent for 7 min (dose-response + confound analysis + validation) but a
  single-signal story — raised then dropped the histone-mark mechanism, and skipped
  tissue/TF/combinatorial analyses.

### Opus 5 (o5) — "instability gate × combinatorial AG signature" (thorough, confounder-first)
- **Confounder-first rigor:** discovers the reference-length confounder, **rejects its own
  most impressive naive AG result** (H1: naive AUC>0.90 is a length artifact — pathogenic
  loci sit at only ~0.4–0.6 percentile vs length-matched controls), and re-runs everything
  under length-matching + quadratic OLS residualization.
- **Two-component conjunction:** (1) NECESSARY — population instability (HPRC LPS stdev,
  AUC 0.993, the single best feature, used as a Stage-1 gate); (2) SUFFICIENT — a
  length-residualized **3-pillar AG signature**: asymmetric tissue-selective **RNA
  silencing** (ADJ-AUC 0.74–0.78), **cross-tissue LFC variance** (no shared causal tissue —
  H4 rejected), and **3D contact disruption** (ADJ-AUC 0.77). Mechanistic color: loss of
  active-promoter histone marks (H3K4me2/3, H2A.Z, acetyls); super-linear (threshold)
  dose-response.
- **Score (gated):** `InstabilityScore + 0.3·AlphaGenomeScore·1[Instability ≥ 95th pct]`;
  AG demoted to a re-ranker within unstable loci (non-redundant, AUC 0.771). 6/7 known loci
  in top 1.7%; LOO median rank 56/6650.

---

## 5. Hypothesis coverage matrix

Legend: ✅ tested & supported · ❌ tested & rejected · ➖ not tested · ⚠️ supported-but-caveated

| hypothesis / mechanism | s5 | o4.8 | o5 |
|---|:--:|:--:|:--:|
| Reference length longer (naive) | ✅ | ✅ | ✅ |
| Length is a confounder → control it | ✅ (residualize) | ✅ (regress + matched) | ✅ (matched + quadratic resid) |
| Population repeat **instability** (HPRC/T2T) | ✅ (d=12.3, top feature) | ➖ (length only) | ✅ (AUC 0.993, top feature) |
| Excess instability beyond length | ✅ | ➖ | ✅ |
| Lower reference purity | ⚠️ (tiny, d=−0.14) | ➖ | ➖ |
| AG effect **magnitude** discriminates | ❌ | ✅ (contacts) | ❌ (length artifact) |
| Non-linear/threshold dose-response | ⚠️ (early saturation) | ✅ (contact slope) | ✅ (super-linear histone) |
| 3D contact-map disruption | ➖ | ✅ (primary) | ✅ (pillar, adjusted) |
| RNA silencing / reduced expression | ❌ (magnitude) | ✅ (weak) | ✅ (directional, robust) |
| Tissue-selective vs tissue-shared | ➖ | ➖ | ✅ selective / ❌ shared tissue |
| Multi-omic combinatorial | ❌ (saturates) | ➖ | ✅ (3 weakly-corr pillars) |
| Active-promoter histone-mark loss | ➖ | ⚠️ (raised, dropped) | ✅ (mechanistic) |
| Host-gene properties (biotype/GC/tissue) | ❌ | ➖ | ❌ |
| CCG motif enrichment | ❌ (OR 5.1, p=0.13) | ➖ | ➖ |
| Splicing discriminates | ❌ | ❌ | ❌ |
| AG adds signal beyond instability | ❌ (implicitly) | ➖ | ✅ (H7, AUC 0.771) |

---

## 6. Scoring approaches compared

| | s5 | o4.8 | o5 |
|---|---|---|---|
| model | weighted z-score composite (instability only) | hand-weighted percentiles + balanced logistic (`ml_prob`) | gated: instability + 0.3·AG (if unstable) |
| AG features used | **none** | contact-map (cm_delta/max20/e20) + atac + rna | RNA-silencing + tissue-variance + contact (residualized) |
| length control | OLS residualization | regression + length-matched subset | quadratic residualization + matched cohort |
| headline metric | AUC 0.992 | AUC 0.96→0.98; permutation p<5e-4 | instability AUC 0.993; composite AG 0.809 |
| validation | LOO + AFF2/FRAXE control | LOO + permutation + AFF2/FRAXE (#3) | LOO (median 56/6650) + AFF2/FRAXE |

---

## 7. Mechanistic synthesis

**Robust across all three (trust high):**
- Pathogenic 5'UTR GCN repeats are **longer and population-length-unstable**; the repeat's
  demonstrated capacity to expand (HPRC/T2T variability) is the strongest single signal
  (s5 and o5 both rank it #1; o5 makes it a necessary gate).
- The recurring molecular mechanism is **FMR1-like host-gene silencing** (reduced RNA
  output / loss of active-promoter chromatin) on expansion.
- Splicing and host-gene-level (biotype/GC/tissue) signals do **not** discriminate.

**Contested (trust medium — model-dependent):**
- *Does AlphaGenome carry the signal?* s5 says no (instability only); o4.8 says yes (3D
  contacts); o5 says partly (a length-residualized 3-pillar AG signature adds non-redundant
  signal on top of the instability gate). The most-controlled analysis (o5) supports a
  **secondary but real** AG contribution — reconciling the two extremes.
- *Shape of dose-response:* early-saturation (s5) vs contact-slope (o4.8) vs super-linear
  threshold (o5).

**Where AlphaGenome is weak here (vs CDS):** unlike the CDS task (where the AG chromatin
signal was central), for 5'UTR the naive AG effect is largely a **reference-length
artifact** (o5 shows this explicitly; s5 finds AG magnitude non-discriminating). The
disease-defining property is upstream — the repeat's instability/expandability — which AG
does not model. AG's residual contribution is a tissue-selective silencing + 3D-contact
signature within already-unstable loci.

**Overall:** the emergent 5'UTR picture is a **conjunction** — a GCN repeat becomes
pathogenic when it is *both* long/unstable enough to expand *and* (on expansion) silences
its host gene via promoter-chromatin loss / 3D disruption in a tissue-selective way. o5
captures this conjunction most explicitly; s5 nails the necessary (instability) half with
the cleanest stats; o4.8 characterizes the sufficient (3D-chromatin) half.

---

## 8. Caveats
- All three train on only **7 positives** vs thousands of negatives — precision-at-top /
  enrichment and LOO are more meaningful than AUROC; feature selection used all 7 loci
  (LOO is optimistic about selection).
- LRP12 lacks HPRC instability data (missing in the catalog) — a systematic miss for the
  instability-centric scores (s5, o5).
- o5 flags segmental-duplication candidates (NOTCH2NL/NBPF families) as having unreliable
  instability estimates.
