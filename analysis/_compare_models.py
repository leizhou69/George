#!/usr/bin/env python
"""Cross-model comparison for one region: s5 / o4.8 / o5 / o5.5.

Adds the Oct-2026 Opus-5.5 runs to the July-2026 three-model comparison, per the
`compare-biomni-output` skill. For each region it writes:

  shareable  -> analysis/comparisons_<region>/   (predictions only, NO key column)
  gitignored -> .keys/<region>_eval_report.md    (which withheld key, which rank)

Usage:  python analysis/_compare_models.py 5UTR
        python analysis/_compare_models.py CDS
"""
import glob
import itertools
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
TARGET = "Top_Candidate_Pathogenic_repeats.csv"

REGIONS = {
    "5UTR": dict(
        qid="q05b",
        keys=REPO / ".keys" / "5UTR_Keys",
        outdir=REPO / "analysis" / "comparisons_5utr",
        report=REPO / ".keys" / "5utr_eval_report.md",
    ),
    "CDS": dict(
        qid="q05cds",
        keys=REPO / ".keys" / "cds_keys",
        outdir=REPO / "analysis" / "comparisons_cds",
        report=REPO / ".keys" / "cds_eval_report.md",
    ),
}

# model key -> which dated output dir to search. o5.5 is the new Oct-2026 run.
RUN_DIRS = {
    "s5": "output/July_24_2026",
    "o4.8": "output/July_24_2026",
    "o5": "output/July_24_2026",
    "o5.5": "output/Oct_31_2026",
}

ID_COLS = ["LocusId", "locus_id", "variant_id", "original_variant_id"]
GENE_COLS = ["GeneName", "GencodeGeneName", "host_gene_name", "gene_name"]
RANK_COLS = ["Rank", "rank", "candidate_rank"]
TOPN_OVERLAP = 50
TOPN_CONSENSUS = 20


def pick(df, cands):
    return next((c for c in cands if c in df.columns), None)


def load(csv):
    """Normalize a run's candidate CSV to locus / gene / rank."""
    df = pd.read_csv(csv)
    i, g, r = pick(df, ID_COLS), pick(df, GENE_COLS), pick(df, RANK_COLS)
    if i is None:
        raise ValueError(f"no id column in {csv} (cols={list(df.columns)})")
    out = pd.DataFrame({"locus": df[i].astype(str).str.strip()})
    out["gene"] = df[g].astype(str).str.strip() if g else ""
    out["rank"] = df[r].values if r else range(1, len(df) + 1)
    return out.reset_index(drop=True)


def main(region):
    cfg = REGIONS[region]
    cfg["outdir"].mkdir(parents=True, exist_ok=True)

    # ---- resolve each model's candidate CSV -------------------------------
    runs, paths = {}, {}
    for model, subdir in RUN_DIRS.items():
        pat = str(REPO / subdir / f"{cfg['qid']}_{model}_Tmp*" / TARGET)
        hits = sorted(glob.glob(pat))
        if not hits:
            print(f"  {model:5s} MISSING  {pat}")
            continue
        paths[model] = hits[-1]  # newest if a model was run more than once
        runs[model] = load(hits[-1])
        print(f"  {model:5s} {len(runs[model]):>3d} rows  {Path(hits[-1]).parent.name}")
    if not runs:
        sys.exit(f"no runs found for {region}")
    models = list(runs)

    # ---- (a) withheld-key recovery  [EVAL METRIC, gitignored output] ------
    keys = pd.read_csv(cfg["keys"], sep="\t")
    key_loci = dict(
        zip(keys["LocusId"].astype(str).str.strip(),
            keys["GencodeGeneName"].astype(str).str.strip())
    )
    recovery = {}
    for m, d in runs.items():
        recovery[m] = {
            key_loci[row.locus]: int(row.rank)
            for row in d.itertuples() if row.locus in key_loci
        }

    # ---- (b) pairwise top-N overlap ---------------------------------------
    sets = {m: set(runs[m]["locus"].head(TOPN_OVERLAP)) for m in models}
    shared = pd.DataFrame(index=models, columns=models, dtype=int)
    jacc = pd.DataFrame(index=models, columns=models, dtype=float)
    for a, b in itertools.product(models, models):
        inter, union = sets[a] & sets[b], sets[a] | sets[b]
        shared.loc[a, b] = len(inter)
        jacc.loc[a, b] = len(inter) / len(union) if union else 0.0
    in_all = sorted(
        {runs[m].set_index("locus").loc[l, "gene"]
         for l in set.intersection(*sets.values()) for m in [models[0]]}
    )

    # ---- (c) rank-weighted consensus --------------------------------------
    score, nexp, gene, where = defaultdict(float), defaultdict(int), {}, defaultdict(dict)
    for m in models:
        for row in runs[m].head(TOPN_CONSENSUS).itertuples():
            score[row.locus] += TOPN_CONSENSUS - int(row.rank) + 1
            nexp[row.locus] += 1
            where[row.locus][m] = int(row.rank)
            gene.setdefault(row.locus, row.gene)
    cons = (
        pd.DataFrame([
            {"LocusId": l, "Gene": gene[l], "ConsensusScore": score[l], "N_exp": nexp[l]}
            for l in score
        ])
        .sort_values(["ConsensusScore", "N_exp"], ascending=False)
        .reset_index(drop=True)
    )
    cons.insert(0, "Rank", range(1, len(cons) + 1))
    cons_keys = [key_loci[l] for l in cons["LocusId"] if l in key_loci]

    # ---- shareable outputs (NO answer key) --------------------------------
    cons.to_csv(cfg["outdir"] / "consensus_top_candidates.csv", index=False)
    shared.to_csv(cfg["outdir"] / "overlap_shared_counts.csv")
    agg = ", ".join(f"{m} {len(recovery[m])}/{len(key_loci)}" for m in models)
    lines = [
        f"# {region} Cross-Model Comparison ({' / '.join(models)})",
        f"_Generated {datetime.now():%Y-%m-%d %H:%M}. "
        f"Adds the Opus-5.5 run to the July-2026 three-model comparison._",
        "",
        "## Recovery of withheld evaluation keys (aggregate)",
        f"Withheld-key recovery (identities in gitignored {cfg['report'].name}): "
        f"{agg}; consensus {len(set(cons_keys))}/{len(key_loci)}.",
        "",
        f"## Pairwise top-{TOPN_OVERLAP} overlap (shared candidates)",
        "",
        shared.to_markdown(),
        "",
        f"Jaccard similarity:",
        "",
        jacc.round(2).to_markdown(),
        "",
        f"Genes in all {len(models)} top-{TOPN_OVERLAP} ({len(in_all)}): {', '.join(in_all)}",
        "",
        f"## Consensus top-15 (rank-weighted over each model's top-{TOPN_CONSENSUS}; predictions only)",
        "",
        cons.head(15).to_markdown(index=False),
        "",
    ]
    (cfg["outdir"] / "comparison_report.md").write_text("\n".join(lines))

    # ---- gitignored key-level detail --------------------------------------
    hdr = "| key gene | " + " | ".join(models) + " |"
    sep = "|---|" + "---|" * len(models)
    rows = [
        f"| {g} | " + " | ".join(str(recovery[m].get(g, "-")) for m in models) + " |"
        for g in key_loci.values()
    ]
    cfg["report"].write_text("\n".join([
        f"# {region} withheld-key recovery (GITIGNORED — do not commit)",
        f"_Generated {datetime.now():%Y-%m-%d %H:%M}. Keys: {sorted(key_loci.values())}_",
        "",
        "| model | recovered | detail (gene: rank) |",
        "|---|---|---|",
        *[f"| {m} | {len(recovery[m])}/{len(key_loci)} | {recovery[m]} |" for m in models],
        "",
        f"Consensus recovers {len(set(cons_keys))}/{len(key_loci)}: {sorted(set(cons_keys))}",
        "",
        "Per-key rank across models:",
        "",
        hdr, sep, *rows, "",
    ]))

    print(f"\n{region}: {agg}; consensus {len(set(cons_keys))}/{len(key_loci)}")
    print("wrote", cfg["outdir"], "and", cfg["report"])
    return shared, cons, recovery


if __name__ == "__main__":
    for region in (sys.argv[1:] or ["5UTR", "CDS"]):
        print(f"=== {region} ===")
        main(region)
