# CDS Cross-Model Comparison (s5 / o4.8 / o5.5 / f5.2 / gem4c)
_Generated 2026-11-11 13:05. Runs: s5 = `q05cds_s5_Tmp0.5_200m_20261111-095826`; o4.8 = `q05cds_o4.8_Tmp0.5_200m_20261111-095906`; o5.5 = `q05cds_o5.5_Tmp0.5_200m_20261111-095906`; f5.2 = `q05cds_f5.2_Tmp0.5_200m_20261111-095906`; gem4c = `q05cds_gem4c_Tmp0.5_200m_20261111-095907`._

> **Note:** All runs here used the re-masked catalogs / ag_db variants dim (`Source` and `FoundInPerfectRepeatsInReference` dropped 2026-11-11; see `db/db_construction.md` §4.4). Opus 5 has no re-masked run and is excluded. The pre-re-mask comparison (runs that could see those columns) is in `pre_remask/`.
> **Note:** Residual leak: the `CNG` canonical motif (also in the `LocusId`) and `ReferenceRepeatPurity` ~0.67 still mark 11 disease-catalog CDS loci, so CDS recovery is not a fully clean metric.

## Recovery of withheld evaluation keys (aggregate)
Withheld-key recovery (identities in gitignored .keys/cds_eval_report.md): s5 2/3, o4.8 0/3, o5.5 2/3, f5.2 1/3, gem4c 2/3; consensus 2/3.

## Pairwise top-50 overlap (shared candidates)

|       |   s5 |   o4.8 |   o5.5 |   f5.2 |   gem4c |
|:------|-----:|-------:|-------:|-------:|--------:|
| s5    |   50 |      0 |     13 |     17 |       7 |
| o4.8  |    0 |     50 |      2 |      1 |       2 |
| o5.5  |   13 |      2 |     50 |     22 |      21 |
| f5.2  |   17 |      1 |     22 |     50 |      20 |
| gem4c |    7 |      2 |     21 |     20 |      50 |

Jaccard similarity:

|       |   s5 |   o4.8 |   o5.5 |   f5.2 |   gem4c |
|:------|-----:|-------:|-------:|-------:|--------:|
| s5    | 1    |   0    |   0.15 |   0.2  |    0.08 |
| o4.8  | 0    |   1    |   0.02 |   0.01 |    0.02 |
| o5.5  | 0.15 |   0.02 |   1    |   0.28 |    0.27 |
| f5.2  | 0.2  |   0.01 |   0.28 |   1    |    0.25 |
| gem4c | 0.08 |   0.02 |   0.27 |   0.25 |    1    |

Genes in all 5 top-50 (0): 

## Consensus top-15 (rank-weighted over each model's top-20; predictions only)

|   Rank | LocusId                   | Gene    |   ConsensusScore |   N_exp |
|-------:|:--------------------------|:--------|-----------------:|--------:|
|      1 | 22-27798894-27798978-TGC  | MN1     |               59 |       4 |
|      2 | 4-41745972-41746032-GCN   | PHOX2B  |               56 |       4 |
|      3 | 14-77027412-77027484-TGT  | IRF2BPL |               52 |       3 |
|      4 | 7-5312881-5312995-GAA     | TNRC18  |               49 |       3 |
|      5 | 7-5312914-5313034-GAT     | TNRC18  |               43 |       3 |
|      6 | 4-139889903-139889966-TGC | MAML3   |               38 |       3 |
|      7 | 8-123369897-123369978-TCT | ATAD2   |               36 |       2 |
|      8 | 6-156778268-156778319-CAG | ARID1B  |               34 |       2 |
|      9 | 20-47651089-47651158-CAA  | NCOA3   |               26 |       2 |
|     10 | 20-57488407-57488470-TCT  | HMGB1P1 |               26 |       2 |
|     11 | 19-13207858-13207897-CTG  | CACNA1A |               22 |       2 |
|     12 | 19-2015541-2015580-GGC    | BTBD2   |               20 |       3 |
|     13 | 4-78870928-78871009-CAG   | BMP2K   |               20 |       2 |
|     14 | 2-73385903-73385951-GGA   | ALMS1   |               20 |       1 |
|     15 | 7-39951730-39951739-CGC   | CDK13   |               19 |       1 |
