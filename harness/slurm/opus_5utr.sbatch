#!/bin/bash
#SBATCH --job-name=q05b_o5_o48
#SBATCH --mail-type=ALL
#SBATCH --mail-user=leizhou@ufl.edu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou

# 5'UTR task (query_05_b.txt, GCN-scoped) with Opus 5 and Opus 4.8, to compare
# against the existing Sonnet-5 5'UTR run. Both o5 and o4.8 reject the temperature
# param, so each runs exactly once; --temperatures 0.5 just pins the Tmp0.5 label
# to match the s5 comparator. Resources right-sized per the biomni-slurm skill
# (measured: these runs peak ~1-3 GB RAM, <1% CPU).
# Run from the George project root regardless of where sbatch was submitted.
cd /blue/zhou/leizhou/Agents/George

ml conda

conda activate biomni_e1

mkdir -p output/July_24_2026

echo "Running 5'UTR task with Opus 5 + Opus 4.8 (each once at Tmp0.5)..."
python harness/run_biomni.py o5 o4.8 --region 5UTR --temperatures 0.5 --output-dir output/July_24_2026 2>&1 | tee output/July_24_2026/q05b_o5_o48_$(date +%Y%m%d-%H%M%S).log

echo "5'UTR Opus run completed!"
