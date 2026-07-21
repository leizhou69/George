# DB-vs-TSV Comparison Report

_Generated 2026-07-21 19:24_  ·  6 experiments

## Task 1 — key recovery

| Experiment     | Backend   | Model   |   N |   YES_hits |   Possible_hits |   Points |
|:---------------|:----------|:--------|----:|-----------:|----------------:|---------:|
| o4.8 · DB      | DB        | o4.8    |  50 |          2 |               5 |      150 |
| s5 · TSV       | TSV       | s5      |  50 |          2 |               5 |      150 |
| o4.6·T.7 · TSV | TSV       | o4.6    |  50 |          2 |               4 |      140 |
| o4.8 · TSV     | TSV       | o4.8    |  50 |          2 |               4 |      140 |
| s5 · DB        | DB        | s5      |  50 |          2 |               3 |      130 |
| o4.6·T.5 · TSV | TSV       | o4.6    |  50 |          0 |               4 |       40 |

## Task 2 — shared candidates (top-50)

|                |   s5 · DB |   o4.8 · DB |   s5 · TSV |   o4.8 · TSV |   o4.6·T.7 · TSV |   o4.6·T.5 · TSV |
|:---------------|----------:|------------:|-----------:|-------------:|-----------------:|-----------------:|
| s5 · DB        |        50 |          31 |         32 |           34 |               21 |               17 |
| o4.8 · DB      |        31 |          50 |         43 |           38 |               32 |               25 |
| s5 · TSV       |        32 |          43 |         50 |           38 |               30 |               22 |
| o4.8 · TSV     |        34 |          38 |         38 |           50 |               26 |               21 |
| o4.6·T.7 · TSV |        21 |          32 |         30 |           26 |               50 |               30 |
| o4.6·T.5 · TSV |        17 |          25 |         22 |           21 |               30 |               50 |

## Task 3 — consensus top-15

|   Rank | LocusId                    | Gene            |   ConsensusScore |   N_exp | is_YES   | is_Possible   |
|-------:|:---------------------------|:----------------|-----------------:|--------:|:---------|:--------------|
|      1 | 17-32142451-32142499-CCG   | RHOT1           |               90 |       6 | False    | False         |
|      2 | 19-10871583-10871649-GCG   | CARM1           |               81 |       5 | False    | False         |
|      3 | 5-443220-443277-GGC        | EXOC3           |               77 |       4 | False    | False         |
|      4 | X-149631735-149631780-CGC  | TMEM185A        |               73 |       6 | False    | True          |
|      5 | X-148500631-148500691-GCC  | AFF2            |               59 |       4 | True     | False         |
|      6 | X-19990922-19990973-CCG    | BCLAF3          |               54 |       5 | False    | True          |
|      7 | 12-124567591-124567636-GGC | NCOR2           |               51 |       5 | False    | False         |
|      8 | 2-190880872-190880920-GCA  | GLS             |               50 |       4 | True     | False         |
|      9 | 13-35476296-35476353-CTG   | MAB21L1         |               48 |       4 | False    | False         |
|     10 | 2-111120967-111121021-GCC  | BCL2L11         |               44 |       4 | False    | False         |
|     11 | 5-177554489-177554531-CGC  | FAM193B         |               42 |       4 | False    | False         |
|     12 | 2-210171295-210171340-GCC  | KANSL1L         |               41 |       4 | False    | False         |
|     13 | X-150983398-150983452-CCG  | HMGB3           |               29 |       3 | False    | False         |
|     14 | 19-10871586-10871640-GCA   | CARM1           |               26 |       2 | False    | False         |
|     15 | 7-55887600-55887639-GCG    | ENSG00000249773 |               25 |       3 | False    | True          |
