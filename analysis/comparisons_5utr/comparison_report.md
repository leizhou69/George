# 5UTR Cross-Model Comparison (s5 / o4.8 / o5.5 / f5.2 / gem4c)
_Generated 2026-11-11 11:11. Runs: s5 = `q05b_s5_Tmp0.5_200m_20261111-095906`; o4.8 = `q05b_o4.8_Tmp0.5_200m_20261111-095909`; o5.5 = `q05b_o5.5_Tmp0.5_200m_20261111-095906`; f5.2 = `q05b_f5.2_Tmp0.5_200m_20261111-095907`; gem4c = `q05b_gem4c_Tmp0.5_200m_20261111-095906`._

> **Note:** All runs here used the re-masked catalogs / ag_db variants dim (`Source` and `FoundInPerfectRepeatsInReference` dropped 2026-11-11; see `db/db_construction.md` §4.4). Opus 5 has no re-masked run and is excluded. The pre-re-mask comparison (runs that could see those columns) is in `pre_remask/`.

## Recovery of withheld evaluation keys (aggregate)
Withheld-key recovery (identities in gitignored .keys/5utr_eval_report.md): s5 2/2, o4.8 2/2, o5.5 2/2, f5.2 2/2, gem4c 2/2; consensus 2/2.

## Pairwise top-50 overlap (shared candidates)

|       |   s5 |   o4.8 |   o5.5 |   f5.2 |   gem4c |
|:------|-----:|-------:|-------:|-------:|--------:|
| s5    |   50 |     30 |     20 |     30 |      27 |
| o4.8  |   30 |     50 |     15 |     22 |      23 |
| o5.5  |   20 |     15 |     50 |     32 |      25 |
| f5.2  |   30 |     22 |     32 |     50 |      33 |
| gem4c |   27 |     23 |     25 |     33 |      50 |

Jaccard similarity:

|       |   s5 |   o4.8 |   o5.5 |   f5.2 |   gem4c |
|:------|-----:|-------:|-------:|-------:|--------:|
| s5    | 1    |   0.43 |   0.25 |   0.43 |    0.37 |
| o4.8  | 0.43 |   1    |   0.18 |   0.28 |    0.3  |
| o5.5  | 0.25 |   0.18 |   1    |   0.47 |    0.33 |
| f5.2  | 0.43 |   0.28 |   0.47 |   1    |    0.49 |
| gem4c | 0.37 |   0.3  |   0.33 |   0.49 |    1    |

Genes in all 5 top-50 (9): AFF2, BICD2, CBL, EXOC3, GLS, NCOR2, PDE7A, RHOT1, TMEM185A

## Consensus top-15 (rank-weighted over each model's top-20; predictions only)

|   Rank | LocusId                   | Gene     |   ConsensusScore |   N_exp |
|-------:|:--------------------------|:---------|-----------------:|--------:|
|      1 | 17-32142451-32142499-CCG  | RHOT1    |               80 |       5 |
|      2 | 2-111120967-111121021-GCC | BCL2L11  |               58 |       4 |
|      3 | 13-35476296-35476353-CTG  | MAB21L1  |               57 |       4 |
|      4 | 20-36746079-36746121-GCG  | NDRG3    |               56 |       3 |
|      5 | X-148500631-148500691-GCC | AFF2     |               56 |       3 |
|      6 | 5-177554489-177554531-CGC | FAM193B  |               55 |       4 |
|      7 | 5-443220-443277-GGC       | EXOC3    |               54 |       4 |
|      8 | X-19990922-19990973-CCG   | BCLAF3   |               45 |       3 |
|      9 | X-149631735-149631780-CGC | TMEM185A |               44 |       5 |
|     10 | 9-92764801-92764831-GCC   | BICD2    |               40 |       3 |
|     11 | 2-190880872-190880920-GCA | GLS      |               37 |       3 |
|     12 | 19-10871583-10871649-GCG  | CARM1    |               31 |       2 |
|     13 | 2-210171295-210171340-GCC | KANSL1L  |               28 |       2 |
|     14 | 16-24729684-24729723-CGG  | TNRC6A   |               27 |       2 |
|     15 | 7-7673310-7673370-AGC     | UMAD1    |               26 |       3 |
