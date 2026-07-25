# CDS Cross-Model Comparison (o5 / o4.8 / s5)
_Generated 2026-07-24 22:51. All-TNR (not GCN-restricted). 3 models on the multi-region ag_db._

## Recovery of withheld evaluation keys (aggregate)
Withheld-key recovery (identities in gitignored .keys/cds_eval_report.md): s5 0/3, o4.8 1/3, o5 2/3; consensus 2/3.

## Pairwise top-50 overlap (shared candidates)

|      |   s5 |   o4.8 |   o5 |
|:-----|-----:|-------:|-----:|
| s5   |   50 |     19 |   18 |
| o4.8 |   19 |     50 |   22 |
| o5   |   18 |     22 |   50 |

Genes in all three top-50 (13): AR, ASCL1, DLX6, E2F4, EP400, MAGI1, MAML3, MED15, MN1, POU4F2, SMARCA2, SP8, ZIC5

## Consensus top-15 (rank-weighted; predictions only)

|   Rank | LocusId                    | Gene    |   ConsensusScore |   N_exp |
|-------:|:---------------------------|:--------|-----------------:|--------:|
|      1 | 4-139889903-139889966-TGC  | MAML3   |               44 |       3 |
|      2 | 4-146639305-146639344-GGC  | POU4F2  |               28 |       2 |
|      3 | 4-78870928-78871009-CAG    | BMP2K   |               25 |       2 |
|      4 | 13-99970407-99970449-GGC   | ZIC5    |               20 |       2 |
|      5 | 1-153934796-153934847-CTG  | DENND4B |               20 |       2 |
|      6 | 16-67195890-67195935-CAG   | E2F4    |               20 |       1 |
|      7 | 7-5312914-5313034-GAT      | TNRC18  |               20 |       1 |
|      8 | 12-102958393-102958429-GCA | ASCL1   |               19 |       3 |
|      9 | 7-15686163-15686199-TGG    | MEOX2   |               19 |       1 |
|     10 | 1-154869723-154869765-GCT  | KCNN3   |               19 |       1 |
|     11 | 12-132062548-132062611-CAG | EP400   |               18 |       3 |
|     12 | 7-27199700-27199730-GCA    | HOXA13  |               18 |       1 |
|     13 | 14-77027412-77027484-TGT   | IRF2BPL |               18 |       1 |
|     14 | 19-13207858-13207897-CTG   | CACNA1A |               18 |       1 |
|     15 | 9-2039764-2039824-CAG      | SMARCA2 |               17 |       2 |

_Note: the o5 CDS run's SLURM process hung after deliverables were written (20:47) and was cancelled; the candidate CSV used here is the final, stable output._