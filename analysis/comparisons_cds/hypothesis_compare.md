# CDS — Hypothesis comparison across the models that recovered 2/3 withheld keys

_Generated 2026-11-11. Covers the three re-masked runs in `output/Nov_11_2026_remasked/`
(catalogs and ag_db variants dim without `Source` / `FoundInPerfectRepeatsInReference`)
that recovered two of the three withheld CDS keys in their top 50. Opus 4.8 (0/3) and
Fable 5.2 (1/3) are not included._

| Model | Run folder | Run time | Narrative steps |
|---|---|---|---|
| Sonnet 5 (s5) | `q05cds_s5_Tmp0.5_200m_20261111-095826` | 12 min | 80 |
| Opus 5.5 (o5.5) | `q05cds_o5.5_Tmp0.5_200m_20261111-095906` | 9 min | — |
| Gemini 4 Carbon (gem4c) | `q05cds_gem4c_Tmp0.5_200m_20261111-095907` | 53 min | 31 |

> Scope: this document compares hypotheses, evidence and scoring only. Withheld-key
> identities are deliberately omitted; key-level recovery is in the gitignored
> `.keys/cds_eval_report.md`. Statistics are quoted as each run reported them and were
> not re-computed. Each model was run once, so differences between models are not
> separable from run-to-run variation.
>
> Residual leak: 11 CDS loci carry the degenerate `CNG` motif (purity ≈ 0.67). Ten are
> given positives and the eleventh is unlabelled. o5.5 and gem4c both noticed this;
> gem4c excluded `CNG` loci from its strict tests and kept motif and purity out of its
> score, while s5 and o5.5 use purity as a scoring feature.

## 1. Short version

**All three agree on the intrinsic signature.** Pathogenic CDS repeats are long
(median 14.5 vs 3 repeats; AUC ≈ 0.99), less pure, and more length-variable in the
population, and they sit disproportionately in DNA-binding transcription-factor genes.
All three reject splicing and bulk RNA change as discriminators.

**They split on what AlphaGenome adds beyond length:**

| Model | Verdict on AlphaGenome (AG) | Evidence it adds to prediction |
|---|---|---|
| o5.5 | One modest length-independent signal (pan-mark histone loss), read as an insert-dilution artefact | None: length alone AUROC 0.991; adding AG ΔAUPRC +0.01, p = 0.38 |
| s5 | "Combinatorial" extreme perturbation across chromatin assays survives a length-matched control | Not demonstrated: full model (AUC 0.903) scores below length + purity alone (0.964) |
| gem4c | Promoter-proximal chromatin niche plus H3K79me2 / pan-histone collapse and contact-map remodelling | Nested likelihood-ratio test p = 0.002; among loci ≥ 8 repeats AUROC 0.89 vs 0.82 sequence-only |

## 2. Hypotheses tested, by theme

Verdicts: **S** supported, **S\*** supported after length control, **W** weak or
suggestive, **C** confounded by length, **R** rejected, — not tested.

| Hypothesis | s5 | o5.5 | gem4c |
|---|---|---|---|
| Longer reference tract | S | S | S |
| Lower purity / interrupted tract | S | S (S\* within GC motifs) | Treated as a curation artefact of the `CNG` loci |
| Higher population length variability | S | S | S\* |
| Histone-signal change on expansion | S\* (magnitude, all expansions) | S\* (loss at 20x beyond length, motif and baseline) | S\* (H3K79me2 collapse; early H3K27me3 loss) |
| Histone effect is mark-specific | W (descriptive only) | R (29 of 29 marks move together) | S (H3K79me2, H3K27me3, H3K4me3 singled out) |
| 3D contact-map disruption | C (lost under length matching) | R (not independent of length) | S\* |
| Accessibility / TF binding / initiation (ATAC, DNase, TF ChIP, PRO-cap, CAGE) | S\* for ATAC, DNase, TF, PRO-cap; CAGE C | R after length adjustment | C (narrow-window shift vanishes under strict control) |
| Multi-assay "extreme" count | S\* (OR 3.75 vs length-matched, p = 0.003) | — | — |
| Non-linear dose response | R (flat; saturates by 2x) | W (super-linear, tracks inserted bp) | S (2x→20x collapse features) |
| Baseline chromatin state of the locus (promoter-type marks, YY1) | — | Used only as a covariate | S\* |
| Splicing disruption | R | R | W → not significant under strict control |
| Bulk / host RNA change | R | — | W → not significant under strict control |
| Brain or tissue specificity | R | — | R |
| Host gene is a DNA-binding transcription factor | S (39% vs 5.3%, OR 11.6) | — | S (52% vs 7.1% of genes, OR 14.2) |
| AG adds predictive value beyond length | Not shown | R | S\* |

### Where they agree

- **Length dominates.** All three identify it as both the strongest discriminator and
  the main confounder, because a 20x expansion of a long tract inserts far more sequence.
- **Histone signal is the AG layer that survives.** Each run, using a different
  summary, finds a histone effect that persists after its length control.
- **Not splicing, not bulk RNA, not tissue-specific.** Rejected or reduced to
  non-significance in every run that tested them.
- **Transcription-factor host genes.** s5 and gem4c both report strong enrichment;
  o5.5 did not test gene function.

### Where they disagree

- **What the histone effect means.** o5.5 shows all 29 marks, active and repressive,
  lose signal together and reads this as dilution by a long low-complexity GC-rich
  insert, not regulation. gem4c singles out H3K79me2 over a 2-kb window (AUROC 0.84
  under its strictest control) and an early H3K27me3 loss, and builds a mechanism on
  them. s5 reports larger magnitudes without resolving direction or marks.
- **Contact maps.** Strong in every raw screen (s5 p = 5e-12). s5 loses it under
  length matching (20x p = 0.27); o5.5's length-adjusted odds ratio spans 1
  (1.22, CI 0.83–1.79); gem4c retains it (strict-control AUROC 0.78, p = 1.5e-4).
- **Dose response.** s5 finds effects flat across 2x/5x/20x; o5.5 finds a super-linear
  rise that tracks inserted base pairs; gem4c treats the 2x→20x change as a signal in
  its own right.
- **Purity.** s5 and o5.5 treat lower purity as a real property and score on it. gem4c
  shows it is largely produced by the `CNG` loci, whose purity is mechanically capped at
  0.67, and that the difference disappears among concrete motifs with ≥ 8 repeats.

## 3. Confound control

| Model | Length control | Motif / leak handling | Other |
|---|---|---|---|
| s5 | Comparison against the 135 non-pathogenic loci with ≥ 10 repeats (a threshold filter, not matching or regression) | None | Bonferroni / FDR over 33 tests |
| o5.5 | Four escalating controls: GC-motif restriction with logistic adjustment; residuals from a controls-only cubic length + motif model; exact matching on motif and ±1 repeat (23 of 28 matchable); baseline chromatin activity added | Restricts to GC-rich motifs; flags `CNG`; removes candidates within 50 bp of a known locus | 10 × 4-fold repeated CV against a length-only baseline |
| gem4c | Every test repeated in ≥ 8-repeat and ≥ 10-repeat strata | Every test repeated excluding `CNG`; motif and purity kept out of the score | BH-FDR, Bonferroni, bootstrap CIs; nested likelihood-ratio test; gene-grouped CV |

s5's control is the weakest of the three: its "length-matched" set still has a much
lower median length than the pathogenic loci.

## 4. Final scoring methods

| Model | Features | Model | Reported performance |
|---|---|---|---|
| s5 | Log repeat count, impurity, three population-variability terms, AG extreme-assay count, transcription-factor flag | Class-balanced logistic regression on all 34,891 loci | 5-fold CV AUC 0.903; 27 of 28 known loci in the top 1% in-sample |
| o5.5 | Log repeat count, purity, HPRC variability, histone change at 20x and 2x, fraction of RNA tracks positive at 20x, contact-map change at 5x | L2 logistic regression on GC-motif loci; candidates ranked by out-of-fold probability | CV AUROC 0.979, AUPRC 0.573; not better than length alone (0.991 / 0.510) |
| gem4c | Log repeat count, imputed HPRC variability, neighbouring-repeat count, TSS proximity, plus about ten AG features (H3K79me2 and pan-histone collapse, early H3K27me3 change, contact-map gain, baseline promoter marks, YY1, PRO-cap, splicing, host RNA) | Equal-weight blend of L2 logistic regression and a 500-tree random forest | Gene-grouped CV: logistic AUROC 0.989; ensemble AUROC 0.979, AUPRC 0.394; sequence-only 0.977; AG-only 0.950 |

Points worth noting:

- **s5's AG and gene-function terms do not help its own model.** Its ablation gives
  AUC 0.964 for length + purity, 0.905 after adding variability, and 0.903 for the full
  model, although its prose says the added terms "substantially improve discrimination".
  The fitted coefficient on the transcription-factor flag is negative (−2.67), opposite
  to the enrichment it reports. The "median rank 67.5" in its summary comes from an
  earlier heuristic score, not the final model.
- **o5.5 scores with AG features it says add nothing.** Four of its seven features are
  AG-derived, but it states the ranking is dominated by length and GC motif.
- **gem4c is the only run with evidence that AG adds information**, and that evidence
  is clearest among long repeats (≥ 8 units: AUROC 0.89 integrative vs 0.82
  sequence-only).
- **Purity as a feature carries the residual leak** in s5 and o5.5.
- **Performance figures are not comparable across runs**: they use different candidate
  universes (all loci, GC-motif loci, exact-motif loci) and different CV schemes.

## 5. Mechanisms proposed

| Model | Mechanism |
|---|---|
| s5 | An inherently unstable tract in a dosage-sensitive transcription-factor gene, encoding an aggregation-prone homopolymer; toxic-protein, dominant-negative or haploinsufficiency routes |
| o5.5 | Protein-level: longer glutamine, alanine or proline tracts cause misfolding, aggregation or mislocalisation. The chromatin-signal loss is presented as supporting evidence, not a cause |
| gem4c | Pathogenic repeats lie in exon-1 / TSS-proximal chromatin at 3D domain boundaries; expansion collapses the H3K79me2 early-elongation domain, shifts Polycomb marks first, and remodels local contacts, while splicing is spared. Two baseline archetypes (polyQ vs polyA) converge on one expansion response |

s5 and o5.5 agree that the disease mechanism is at the protein level and that AG's
regulatory predictions are at most corroborating. gem4c proposes a cis-regulatory
mechanism in addition.

## 6. What is distinctive about each run

- **s5:** collapses AG into a single count of assays with extreme effects, and brings
  in external gene-function annotation (GO transcription-factor membership).
- **o5.5:** argues against its own strongest AG finding, benchmarks every feature set
  against a length-only model, and gives an explicitly negative answer to the question
  posed.
- **gem4c:** uses baseline chromatin state as well as expansion deltas, separates host
  from bystander genes, tests everything in length and motif strata, and uses
  gene-grouped cross-validation so no gene spans training and validation folds.

## 7. Reading the 2/3 result

All three scores are driven mainly by reference length, with population variability
second, and those are sufficient to place long unlabelled repeats in known disease
genes near the top. The residual `CNG` leak also still favours disease-catalog loci
(directly, through purity, in s5 and o5.5), so CDS recovery is not a fully clean metric. The
2/3 recoveries therefore do not discriminate between the three accounts of AlphaGenome's
role. The substantive disagreement to resolve is whether the histone effect is
mark-specific regulation (gem4c) or pan-mark dilution by the inserted sequence (o5.5);
the two runs analysed overlapping data and reached opposite readings.
