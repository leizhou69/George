# CDS Cross-Model Comparison (s5 / o4.8 / o5 / o5.5 / f5.2 / gem4c)
_Generated 2026-11-11 09:36. Runs: s5 = `q05cds_s5_Tmp0.5_200m_20260724-195939`; o4.8 = `q05cds_o4.8_Tmp0.5_200m_20260724-203020`; o5 = `q05cds_o5_Tmp0.5_200m_20260724-203624`; o5.5 = `q05cds_o5.5_Tmp0.5_200m_20261111-040908`; f5.2 = `q05cds_f5.2_Tmp0.5_200m_20261111-042358`; gem4c = `q05cds_gem4c_Tmp0.5_200m_20261111-044943`._

> **Note:** The o5 CDS run's SLURM process hung after deliverables were written (2026-07-24 20:47) and was cancelled; the candidate CSV used here is the final, stable output.

## Recovery of withheld evaluation keys (aggregate)
Withheld-key recovery (identities in gitignored .keys/cds_eval_report.md): s5 0/3, o4.8 1/3, o5 2/3, o5.5 2/3, f5.2 0/3, gem4c 2/3; consensus 2/3.

## Pairwise top-50 overlap (shared candidates)

|       |   s5 |   o4.8 |   o5 |   o5.5 |   f5.2 |   gem4c |
|:------|-----:|-------:|-----:|-------:|-------:|--------:|
| s5    |   50 |     19 |   18 |     18 |     19 |      23 |
| o4.8  |   19 |     50 |   22 |     32 |     30 |      30 |
| o5    |   18 |     22 |   50 |     28 |     19 |      26 |
| o5.5  |   18 |     32 |   28 |     50 |     31 |      31 |
| f5.2  |   19 |     30 |   19 |     31 |     50 |      26 |
| gem4c |   23 |     30 |   26 |     31 |     26 |      50 |

Jaccard similarity:

|       |   s5 |   o4.8 |   o5 |   o5.5 |   f5.2 |   gem4c |
|:------|-----:|-------:|-----:|-------:|-------:|--------:|
| s5    | 1    |   0.23 | 0.22 |   0.22 |   0.23 |    0.3  |
| o4.8  | 0.23 |   1    | 0.28 |   0.47 |   0.43 |    0.43 |
| o5    | 0.22 |   0.28 | 1    |   0.39 |   0.23 |    0.35 |
| o5.5  | 0.22 |   0.47 | 0.39 |   1    |   0.45 |    0.45 |
| f5.2  | 0.23 |   0.43 | 0.23 |   0.45 |   1    |    0.35 |
| gem4c | 0.3  |   0.43 | 0.35 |   0.45 |   0.35 |    1    |

Genes in all 6 top-50 (7): AR, EP400, MAML3, MN1, POU4F2, SMARCA2, ZIC5

## Consensus top-15 (rank-weighted over each model's top-20; predictions only)

|   Rank | LocusId                    | Gene    |   ConsensusScore |   N_exp |
|-------:|:---------------------------|:--------|-----------------:|--------:|
|      1 | 4-139889903-139889966-TGC  | MAML3   |               69 |       5 |
|      2 | X-67546514-67546565-GGC    | AR      |               69 |       4 |
|      3 | 14-77027412-77027484-TGT   | IRF2BPL |               64 |       4 |
|      4 | 22-27798894-27798978-TGC   | MN1     |               57 |       4 |
|      5 | 4-146639305-146639344-GGC  | POU4F2  |               53 |       5 |
|      6 | 7-5312914-5313034-GAT      | TNRC18  |               50 |       3 |
|      7 | 2-73385903-73385951-GGA    | ALMS1   |               49 |       3 |
|      8 | 7-5312881-5312995-GAA      | TNRC18  |               46 |       3 |
|      9 | 12-102958393-102958429-GCA | ASCL1   |               42 |       5 |
|     10 | 4-78870928-78871009-CAG    | BMP2K   |               39 |       3 |
|     11 | 1-154869723-154869765-GCT  | KCNN3   |               39 |       3 |
|     12 | 12-132062548-132062611-CAG | EP400   |               38 |       6 |
|     13 | 13-99970407-99970449-GGC   | ZIC5    |               38 |       4 |
|     14 | 1-153934796-153934847-CTG  | DENND4B |               37 |       3 |
|     15 | 8-123369897-123369978-TCT  | ATAD2   |               33 |       2 |
