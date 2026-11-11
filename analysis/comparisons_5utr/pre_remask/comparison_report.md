# 5UTR Cross-Model Comparison (s5 / o4.8 / o5 / o5.5 / f5.2 / gem4c)
_Generated 2026-11-11 09:36. Runs: s5 = `q05b_s5_Tmp0.5_200m_20260724-154415`; o4.8 = `q05b_o4.8_Tmp0.5_200m_20260724-213655`; o5 = `q05b_o5_Tmp0.5_200m_20260724-212112`; o5.5 = `q05b_o5.5_Tmp0.5_200m_20261111-040908`; f5.2 = `q05b_f5.2_Tmp0.5_200m_20261111-042358`; gem4c = `q05b_gem4c_Tmp0.5_200m_20261111-043508`._

> **Note:** The s5 comparator (`q05b_s5_...20260724-154415`) ran BEFORE the GCN `SCOPE` block was added to `query_05_b.txt`; every other run used it. The s5 list therefore includes non-GCN loci (e.g. HLA-F), which also enter the consensus. Recovery figures for s5 are not like-for-like with the other models.

## Recovery of withheld evaluation keys (aggregate)
Withheld-key recovery (identities in gitignored .keys/5utr_eval_report.md): s5 2/2, o4.8 1/2, o5 1/2, o5.5 2/2, f5.2 0/2, gem4c 2/2; consensus 2/2.

## Pairwise top-50 overlap (shared candidates)

|       |   s5 |   o4.8 |   o5 |   o5.5 |   f5.2 |   gem4c |
|:------|-----:|-------:|-----:|-------:|-------:|--------:|
| s5    |   50 |     14 |   10 |     25 |     28 |      30 |
| o4.8  |   14 |     50 |    6 |     20 |     22 |      25 |
| o5    |   10 |      6 |   50 |     11 |     11 |      12 |
| o5.5  |   25 |     20 |   11 |     50 |     29 |      30 |
| f5.2  |   28 |     22 |   11 |     29 |     50 |      37 |
| gem4c |   30 |     25 |   12 |     30 |     37 |      50 |

Jaccard similarity:

|       |   s5 |   o4.8 |   o5 |   o5.5 |   f5.2 |   gem4c |
|:------|-----:|-------:|-----:|-------:|-------:|--------:|
| s5    | 1    |   0.16 | 0.11 |   0.33 |   0.39 |    0.43 |
| o4.8  | 0.16 |   1    | 0.06 |   0.25 |   0.28 |    0.33 |
| o5    | 0.11 |   0.06 | 1    |   0.12 |   0.12 |    0.14 |
| o5.5  | 0.33 |   0.25 | 0.12 |   1    |   0.41 |    0.43 |
| f5.2  | 0.39 |   0.28 | 0.12 |   0.41 |   1    |    0.59 |
| gem4c | 0.43 |   0.33 | 0.14 |   0.43 |   0.59 |    1    |

Genes in all 6 top-50 (1): PCMTD2

## Consensus top-15 (rank-weighted over each model's top-20; predictions only)

|   Rank | LocusId                    | Gene     |   ConsensusScore |   N_exp |
|-------:|:---------------------------|:---------|-----------------:|--------:|
|      1 | 13-35476296-35476353-CTG   | MAB21L1  |               88 |       5 |
|      2 | 17-32142451-32142499-CCG   | RHOT1    |               81 |       5 |
|      3 | 5-443220-443277-GGC        | EXOC3    |               66 |       4 |
|      4 | 12-124567591-124567636-GGC | NCOR2    |               58 |       4 |
|      5 | 7-7673310-7673370-AGC      | UMAD1    |               56 |       4 |
|      6 | X-149631735-149631780-CGC  | TMEM185A |               55 |       4 |
|      7 | X-19990922-19990973-CCG    | BCLAF3   |               52 |       4 |
|      8 | 5-177554489-177554531-CGC  | FAM193B  |               45 |       3 |
|      9 | 19-2308142-2308175-GCC     | LINGO3   |               38 |       3 |
|     10 | 2-190880872-190880920-GCA  | GLS      |               38 |       3 |
|     11 | X-148500631-148500691-GCC  | AFF2     |               34 |       3 |
|     12 | 5-166979194-166979236-CAG  | TENM2    |               31 |       4 |
|     13 | 10-50991310-50991343-GCC   | PRKG1    |               29 |       4 |
|     14 | X-150983398-150983452-CCG  | HMGB3    |               29 |       3 |
|     15 | 19-10871583-10871649-GCG   | CARM1    |               26 |       4 |
