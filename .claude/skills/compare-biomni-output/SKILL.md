---
name: compare-biomni-output
description: >-
  Compare multiple Biomni agent runs of the SAME George task (different models
  and/or backends), build a rank-weighted consensus candidate list, and evaluate
  recovery of HELD-OUT answer keys withheld from the agent. Use when comparing
  model outputs for a region (5UTR/CDS/3UTR), producing a consensus
  Top_Candidate list, scoring runs against withheld keys, or writing a
  cross-model hypothesis/mechanism comparison.
---

# Comparing Biomni run outputs + consensus + held-out-key evaluation

Each biomni run writes `Top_Candidate_Pathogenic_repeats.csv` (its ranked
predictions), a `<prefix>.md` narrative, and `pathogenic_repeat_analysis.ipynb` /
`Candidate_Identification.ipynb`. This skill turns a set of such runs into (1) a
model comparison, (2) a pooled consensus, and (3) a recovery score against the
held-out keys. The canonical reference implementation is
`analysis/_build_compare_nb.py` (the 5UTR DB-vs-TSV comparison); reuse its logic.

## ⚠️ Held-out-key discipline (read first)

Evaluation = did the agents' candidate search recover the **known pathogenic loci
that were withheld from the agent**? These keys are the answer key and must be
protected:

- Keys live in **`.keys/`** which is **gitignored** (`.gitignore` has `.keys/`).
- Keys are **never** registered with the harness (`DATA_FILES` / `add_data`) and
  the query never references them — the biomni agent must never see them. The
  `ag_db` also carries no pathogenic labels by design.
- **You (the evaluator) may read `.keys/` to score**, but the withheld-key
  identities must **never enter a committed/pushed file**:
  - Shareable (pushable) outputs contain only the agents' **predictions**
    (`Rank,LocusId,Gene,ConsensusScore,N_exp`) — **no** `is_key`/answer column.
  - Detailed key-level recovery (which key, which model, what rank) goes in a
    **gitignored** file: `.keys/<region>_eval_report.md`.
  - `biomni_log.md` (pushed) gets **aggregate only**: e.g. "consensus recovered
    N/K withheld keys; per-model N/K" + a pointer to the gitignored report.
- The given/positive pathogenic list the agent WAS shown (e.g.
  `data/CDS/B_CDS_Pathogenic_TNR_Nokey.txt`) is NOT the eval set — recovering
  those is not the metric.

## Inputs

- One run dir per model, each with `Top_Candidate_Pathogenic_repeats.csv`. Column
  names differ across models/runs — detect flexibly:
  - id: `LocusId` / `locus_id` / `variant_id` / `original_variant_id`
  - gene: `GeneName` / `GencodeGeneName` / `host_gene_name` / `gene_name`
  - rank: `Rank` / `rank`
- Withheld keys: `.keys/<region>_keys` (tab-separated; `LocusId` + `GencodeGeneName`).
- Sanity-check each CSV has the expected N rows (e.g. 50) and isn't degenerate —
  a suspiciously fast run (few log entries) can still emit 50 rows; verify.

## Procedure (mirror analysis/_build_compare_nb.py)

```python
import glob, itertools, pandas as pd
from collections import defaultdict
ID=['LocusId','locus_id','variant_id','original_variant_id']
GENE=['GeneName','GencodeGeneName','host_gene_name','gene_name']; RANK=['Rank','rank']
pick=lambda d,c: next((x for x in c if x in d.columns), None)
def load(p):
    d=pd.read_csv(p); i,g,r=pick(d,ID),pick(d,GENE),pick(d,RANK)
    return pd.DataFrame({'locus':d[i].astype(str).str.strip(),
                         'gene':(d[g].astype(str).str.strip() if g else ''),
                         'rank':(d[r].values if r else range(1,len(d)+1))})
runs={m:load(glob.glob(f'output/.../q05..._{m}_*/Top_Candidate_Pathogenic_repeats.csv')[0])
      for m in ['s5','o4.8','o5']}

# (a) recovery vs withheld keys  — EVAL METRIC
k=pd.read_csv('.keys/<region>_keys',sep='\t')
key_loci=set(k['LocusId'].astype(str).str.strip())
for m,d in runs.items():
    hit={row['gene']:int(row['rank']) for _,row in d.iterrows() if row['locus'] in key_loci}
    print(m, f"{len(hit)}/{len(key_loci)}", hit)

# (b) pairwise top-50 overlap + Jaccard
S={m:set(runs[m]['locus'].head(50)) for m in runs}
for a,b in itertools.combinations(runs,2):
    i=S[a]&S[b]; u=S[a]|S[b]; print(a,b,len(i),round(len(i)/len(u),2))

# (c) rank-weighted consensus: each model top-20 adds (20-rank+1)
TOPN=20; score=defaultdict(float); nexp=defaultdict(int); gene={}
for m in runs:
    for _,r in runs[m].head(TOPN).iterrows():
        score[r['locus']]+=(TOPN-int(r['rank'])+1); nexp[r['locus']]+=1; gene.setdefault(r['locus'],r['gene'])
cons=(pd.DataFrame([{'LocusId':l,'Gene':gene[l],'ConsensusScore':score[l],'N_exp':nexp[l]} for l in score])
      .sort_values(['ConsensusScore','N_exp'],ascending=False).reset_index(drop=True))
cons.insert(0,'Rank',range(1,len(cons)+1))
```

## Outputs

- **Shareable** → `analysis/comparisons_<region>/`:
  `consensus_top_candidates.csv` (predictions only), `comparison_report.md`,
  `overlap_shared_counts.csv`.
- **Gitignored** → `.keys/<region>_eval_report.md`: per-model + consensus key
  recovery (which keys, ranks).
- **`biomni_log.md`** (pushed): dated section with aggregate recovery counts + a
  pointer to the gitignored report; correct any earlier note that scored the wrong
  (given, not withheld) set.

## Optional: hypothesis / mechanism comparison

To compare the *science* (hypotheses tested, mechanisms proposed) rather than the
candidate lists, fan out one `general-purpose` agent per run to extract
{hypotheses tested, evidence + supported/rejected, final pathogenic signature,
scoring features, distinctive angle} from each run's `.md` (or notebooks if `.md`
absent), then synthesize into
`analysis/comparisons_<region>/<REGION>_model_hypothesis_comparison.md`
(see `analysis/comparisons_cds/CDS_model_hypothesis_comparison.md` for the shape).
Keep withheld-key identities out of this doc too.

## Notes

- Consensus dedups by **locus** (`.head(TOPN)` per model) — same locus in >1 model
  accrues score and raises `N_exp`.
- Use the same-backend runs for a fair comparison (see `biomni-slurm` skill); flag
  cross-backend or cross-harness comparators.
- Related: `biomni-slurm` (launching/right-sizing the runs), `add-biomni-region`
  (onboarding a region).
