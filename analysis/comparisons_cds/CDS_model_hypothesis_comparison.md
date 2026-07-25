# CDS Pathogenic-Repeat Analysis — Cross-Model Hypothesis & Mechanism Comparison

_Generated 2026-07-24. Compares the scientific reasoning (hypotheses tested, mechanisms
proposed) of three Biomni agent runs on the identical CDS task (`queries/query_05_cds.txt`)
against the multi-region AG DuckDB backend._

| model | run dir | analysis depth | narrative source |
|---|---|---|---|
| **Sonnet 5** (s5) | `output/July_24_2026/q05cds_s5_Tmp0.5_200m_20260724-195939` | thorough (23 min, 185 steps) | `.md` report |
| **Opus 4.8** (o4.8) | `output/July_24_2026/q05cds_o4.8_Tmp0.5_200m_20260724-203020` | thin (6 min, 66 steps) | `.md` report |
| **Opus 5** (o5) | `output/July_24_2026/q05cds_o5_Tmp0.5_200m_20260724-203624` | deepest (rigor-heavy) | notebooks (run still finalizing at time of writing) |

> Scope note: this document compares **mechanistic hypotheses only**. Recovery of the
> held-out evaluation keys is tracked separately (see `biomni_log.md` and the gitignored
> eval); withheld-key identities are deliberately omitted here.

---

## 1. TL;DR

**All three converge on the same coarse picture** and independently rediscover that raw
repeat length is the dominant naive discriminator (AUC ≈ 0.99, median ~14–15 vs ~3–7
repeats) and therefore a confounder that must be controlled. After length control, all
three localize the pathogenic AlphaGenome signal to the **chromatin / epigenetic layer at
high (20×) expansion**, agree that **splicing is *not* a discriminator**, and agree that
pathogenic loci are **long, impure, germline-unstable, GC-rich, in-frame** tracts in
transcription-factor / developmental genes.

**They disagree on the *nature and direction* of the chromatin effect** — the single most
important scientific divergence:

| model | chromatin claim | one-line mechanism |
|---|---|---|
| s5 | **Repression** — signed effect becomes more negative with dose; silencing of accessibility & transcription initiation (ATAC/DNase/CAGE/PRO-cap/histone) | dose-dependent regulatory **silencing** + polyQ aggregation |
| o4.8 | **Mark-specific state switch** — ↑promoter (H3K4me3/2) **and** ↑Polycomb (H3K27me3), but ↓elongation (H3K36me3) and ↓splicing | chromatin **state change** at promoters/Polycomb + 3D-contact disruption |
| o5 | **Wholesale collapse** — *all* histone marks (active **and** repressive) lose signal ~2.6× together (29/29 marks, sign-test p=3.7e-9) | pan-mark nucleosome/signal **collapse** (GC-rich insertion) + toxic protein GOF |

So: all three see "the locus's chromatin is strongly perturbed on expansion," but s5 reads
it as **repression**, o4.8 as a **directional state-switch**, and o5 as **global signal
loss/collapse**. Part of this is a real modeling difference and part is a
measurement-definition difference (signed `quantile_score` [s5] vs per-mark mean
`|raw_score|` [o4.8] vs length-residualized signed histone logFC [o5]).

**Mechanistic depth / rigor ranking: o5 > s5 > o4.8.**

---

## 2. Shared conclusions (the cross-model consensus)

1. **Length is the dominant naive signal and a confounder.** All three: reference repeat
   count separates classes at AUC ≈ 0.99 (p ≈ 2e-46) and all three re-derive every claim
   under explicit length control (methods differ — §5).
2. **Repeat architecture:** pathogenic tracts are longer, **lower-purity / more
   interrupted**, and more **germline-unstable** (HPRC-100 LPS stdev, T2T-assembly stdev).
   s5 and o5 quantify this strongly (purity/instability AUC 0.85–0.89); o4.8 notes it less.
3. **The surviving AG signal is chromatin/epigenetic at 20×**, not transcript-level.
4. **Splicing is not a discriminator** — all three find pathogenic splice effects *smaller*
   or *reversed*; o5 explicitly reframes "splicing spared" as a **positive** criterion
   (keeps the ORF in-frame so an expanded toxic protein is translated).
5. **Host genes are enriched for sequence-specific DNA-binding TFs / developmental
   regulators** (HOX/FOX/SOX/ZIC/DLX/RUNX families). s5 quantifies ~9-fold (p=1.3e-10);
   o5 finds GO Pol-II-TF enrichment (q=8e-9); o4.8 observes it qualitatively in candidates.
6. **Candidate lists overlap** on a TF-heavy core (13 genes shared across all three top-50:
   AR, ASCL1, DLX6, E2F4, EP400, MAGI1, MAML3, MED15, MN1, POU4F2, SMARCA2, SP8, ZIC5).

---

## 3. The key divergence — direction & shape of the chromatin effect

| dimension | s5 | o4.8 | o5 |
|---|---|---|---|
| **direction** | repressive (signed → negative) | mixed / mark-specific (promoter+Polycomb ↑, elongation ↓) | uniformly negative (all marks ↓) |
| **interpretation** | locus silencing | chromatin **state switch** | nucleosome / signal **collapse** |
| **dose-response** | monotonic increase in repression 2×→5×→20× (per-assay trajectories) | non-linear 3D-contact slope (20×−2×) | **supra-linear** histone escalation (20×/2× = 23.5 patho vs 13.2 benign; threshold model) |
| **3D genome** | contact-maps among top modalities | contact-map dose-slope is a scored feature | contact remodeling real but **largely length-driven** (null after per-repeat-unit norm) |
| **measurement** | signed `quantile_score`, fraction repressive | per-mark mean `|raw_score|` @20× | length-residualized signed histone log2FC @20× |

**Reconciliation.** o5's "collapse" (both active and repressive marks fall) is the most
internally-consistent reading and directly contradicts o4.8's "H3K27me3 ↑" — the difference
is that o4.8 scored **magnitude** (`|raw_score|`, which rises for *any* change) while o5
scored **signed** change (which reveals the direction is loss). s5's "repression" is
compatible with o5's "collapse" for the *active* marks but s5 did not test repressive
marks for the same drop. Net: **the robust, direction-aware finding (o5) is a pan-mark
signal-loss/collapse; "repression" (s5) and "state-switch" (o4.8) are partial views shaped
by their scoring choices.**

---

## 4. Per-model detail

### Sonnet 5 (s5) — "dose-dependent repression + TF enrichment, two independent axes"
- **Distinctive move:** headline is *directionality + dose-response* — a signed,
  monotonically increasing **repressive** effect on ATAC/DNase/histone/CAGE/PRO-cap with
  expansion, plus **CONTACT_MAPS** (3D) among the top modalities. Uses a **negative result
  affirmatively**: splicing and RNA-seq explicitly do *not* differ, pinning the signature
  to the regulatory/epigenetic layer.
- **Two-way confound control:** defends the repression signal against *both* a length
  confound (20-bin length-matched percentile; within long-repeat bin p=8.7e-5, d=−0.58)
  *and* a TF-gene confound (within TF genes only, p=9.3e-10) → claims **three independent,
  additive** signals (length, epigenetic repression, TF status).
- **Outside-AG evidence:** local MSigDB C5 GO + HPO → 9-fold TF enrichment (p=1.3e-10),
  neurological/developmental phenotype + anticipation enrichment.
- **Scoring:** weighted composite of length-bin-matched percentiles — `2.0·length +
  1.0·repression(20×) + 1.0·impurity + 0.5·HPRC-var + 0.5·T2T-var + 0.5·is_TF`;
  AUC ≈ 0.99, 5-fold CV ≈ 0.99. Per-gene mechanistic labels (TF+long → "TF
  dosage/aggregation"; non-TF → "HTT-like toxic aggregation").

### Opus 4.8 (o4.8) — "length-adjusted promoter/Polycomb chromatin + 3D slope" (thin)
- **Strong point:** the defining move is treating **reference length as a confounder** and
  re-deriving everything under **1:5 nearest-neighbor length matching** + a `log_ref`
  covariate in the classifier — cleaner than a naive magnitude comparison.
- **Mechanism:** length-adjusted signature = ↑H3K4me3/H3K4me2 (promoter), ↑H3K27me3
  (Polycomb), **↓H3K36me3** (elongation) + ↑CHIP_TF + a non-linear **CONTACT_MAPS dose
  slope**; splicing reduced. Framed purely epigenetic/3D — **no** protein-aggregation or
  expression mechanism invoked.
- **Scoring:** length-aware L2 logistic (13 features incl. per-mark histones,
  `CM_slope_20_2`, `hist_promoter_over_elong`, `log_ref`), 5-fold CV **AUC = 0.923**;
  rule-based per-candidate hypothesis text.
- **Thin/shallow flags:** single aggregate feature table; **no** tissue/biosample,
  life-stage, gene-strand, or combinatorial-interaction analyses (despite the prompt);
  only 28 positives with **saturated ~1.000 probabilities** (overfit-prone); notebooks are
  code-assembled and were **not executed** (empty outputs). Depth of analysis is the
  weakest of the three.

### Opus 5 (o5) — "pan-mark collapse, rigorously length-residualized, dual mechanism" (deepest)
- **Most rigorous length control:** every AG feature regressed on a **quadratic in log(L)
  fitted on benign loci only**, then subtracted, *plus* per-repeat-unit normalization as
  the strictest test — explicitly prevents the model re-learning length; analysis run on a
  length-matched cohort (benign L≥6) with log(L) always conditioned.
- **Mechanism:** **pan-mark chromatin collapse** — all 29 histone marks lose signal ~2.6×
  more at pathogenic loci (sign-test p=3.7e-9), robust to length *and* per-unit
  normalization (p=7.5e-4); **supra-linear** dose-response (escalation 23.5 vs 13.2, a
  threshold/cooperative model); contact-map/pan-modality signals real but demoted as
  **redundant/length-driven** (LRT p=0.92 / p=0.08). Concludes an explicit **dual
  mechanism**: cis epigenetic silencing (loss-of-function) + translated toxic
  expanded-protein (gain-of-function).
- **Explicit negative result on tissue specificity:** collapse stronger at pathogenic loci
  in **219/219 biosamples** → *universal, not neuronal-selective*; used to **bound what AG
  can claim** (DNA-level consequence, not tissue tropism).
- **Scoring:** balanced logistic, 7 features (`logL`, HPRC/T2T instability,
  `ChromatinCollapse_LengthResidual`, `ContactMap_LengthResidual`,
  `PanModality_FracNegative`, `motif_class_path` GC-rich-in-frame filter), model chosen by
  **AUPRC** under 28:34,863 imbalance: AUROC 0.986, **AUPRC 0.375 vs 0.280 length-only
  (+34%)**; validated by LOO stability + 14-fold enrichment of independent repeat-disease
  genes in top-200 (OR≈14, p=1.4e-6).
- **Honest self-critique:** AUROC does *not* beat length-only (gain is precision-at-top);
  `motif_class_path` acts as a hard filter with only 28 positives; AG models idealized
  perfect-repeat insertions (no methylation / somatic mosaicism / proteostasis channel).

---

## 5. Hypothesis coverage matrix

Legend: ✅ tested & supported · ❌ tested & rejected · ➖ not tested · ⚠️ supported but caveated/redundant

| hypothesis / mechanism | s5 | o4.8 | o5 |
|---|:--:|:--:|:--:|
| Repeat length is dominant (naive) | ✅ | ✅ | ✅ |
| Length is a confounder → control it | ✅ (20-bin pct) | ✅ (1:5 NN + covariate) | ✅ (quadratic-logL on benign + per-unit) |
| Impurity / interruptions higher | ✅ | ➖ | ✅ (AUC 0.16 = strongly lower purity) |
| Germline instability (HPRC/T2T) | ✅ | ➖ | ✅ (AUC 0.89 / 0.85) |
| GC-rich in-frame motif class | ⚠️ implicit | ➖ | ✅ (28/28; dominant filter) |
| Chromatin/epigenetic effect @20× | ✅ repression | ✅ state-switch | ✅ collapse |
| Direction is *repression* | ✅ | ❌ (mark-specific) | ⚠️ (collapse, not simple repression) |
| Splicing is a discriminator | ❌ | ❌ | ❌ (reframed as positive criterion) |
| RNA-seq / expression output | ❌ | ➖ | ➖ |
| 3D genome (contact maps) | ✅ (top modality) | ✅ (dose slope) | ⚠️ (length-driven; LRT p=0.08) |
| Dose-response 2×→5×→20× | ✅ monotonic | ✅ non-linear (contacts) | ✅ **supra-linear** (histones) |
| Multi-omic combinatorial hit count | ❌ (p=0.64) | ➖ | ⚠️ redundant (LRT p=0.92) |
| Tissue / cell-type specificity | ❌ (general) | ➖ | ❌ (219/219 biosamples) |
| Host-gene TF enrichment | ✅ (9×, p=1.3e-10) | ⚠️ qualitative | ✅ (GO q=8e-9) |
| TF vs chromatin independence | ✅ (within-TF p=9.3e-10) | ➖ | ➖ |
| Protein aggregation / toxic GOF | ✅ (HTT-like) | ➖ (not invoked) | ✅ (explicit dual mechanism) |

---

## 6. Scoring approaches compared

| | s5 | o4.8 | o5 |
|---|---|---|---|
| model | weighted composite of length-matched percentiles | length-aware L2 logistic (13 feat) | balanced logistic (7 feat), AUPRC-selected |
| length control | 20-bin matched percentiles | 1:5 NN matching + `log_ref` covariate | quadratic-logL residualization (benign-fit) + per-unit norm |
| headline metric | AUC ≈ 0.99 (CV ≈ 0.99) | AUC = 0.923 (5-fold CV) | AUROC 0.986; **AUPRC 0.375 (+34% vs length)** |
| overfit guard | balanced logistic CV cross-check | none beyond 5-fold (saturated probs) | LOO stability (28 refits), AUPRC focus, honest critique |
| extra evidence | MSigDB GO + HPO enrichment | — | GO enrichment + independent disease-gene enrichment (OR≈14) |

---

## 7. Mechanistic synthesis

**Robust across all three (trust high):**
- Pathogenic CDS repeats are **long, impure, germline-unstable, GC-rich, in-frame** tracts.
- Upon (simulated) expansion, AlphaGenome predicts a **large chromatin/epigenetic
  perturbation at the locus at 20×** that **survives length control** and is **specific to
  the regulatory/chromatin layer, not splicing or bulk RNA output**.
- Host genes skew heavily to **developmental transcription factors**.

**Contested (trust medium — model-dependent):**
- *Direction of the chromatin effect*: repression (s5) vs mark-specific state-switch (o4.8)
  vs pan-mark collapse (o5). The direction-aware, most-controlled analysis (o5) favors
  **collapse**; treat o4.8's "H3K27me3 up" as a magnitude artifact.
- *3D-contact / multi-modal signals*: scored as real by s5/o4.8 but shown **largely
  length-driven and redundant** once o5 applies per-repeat-unit normalization.
- *Shape of dose-response*: monotonic (s5) vs supra-linear/threshold (o5).

**Where AlphaGenome is blind (all agree or o5 shows explicitly):**
- **Tissue selectivity** — the chromatin signal is universal across biosamples, so AG
  captures the intrinsic DNA-level consequence, **not** the neuronal/developmental tropism
  that determines the actual clinical phenotype. Somatic mosaicism, CpG methylation, and
  proteostasis are outside the model.

**Overall:** the three runs are mutually reinforcing on the coarse signature but o5 provides
the most defensible mechanism (**pan-mark chromatin collapse gated by a GC-rich in-frame,
unstable, long tract → cis loss-of-function silencing + toxic expanded-protein
gain-of-function**), with s5 contributing the strongest orthogonal biology (independent TF
enrichment) and o4.8 the weakest / thinnest analysis (single length-matched pass, no tissue
or interaction tests, saturated classifier).

---

## 8. Caveats
- o5's narrative was read from its **notebooks** (its `.md` report had not been written yet
  at generation time); re-confirm against the `.md` once the run finalizes.
- o4.8's notebooks were assembled programmatically and **not executed** (no cell outputs);
  its numbers come from the `.md` report.
- All three classifiers train on only **28 positives** vs ~35k negatives — precision-at-top
  and enrichment are more meaningful than AUROC, and probabilities saturate easily.
