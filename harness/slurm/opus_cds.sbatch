#!/bin/bash
#SBATCH --job-name=q05cds_opus
#SBATCH --mail-type=ALL
#SBATCH --mail-user=leizhou@ufl.edu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou

# CDS task (query_05_cds.txt) with Opus 4.8 and Opus 5, complementing the Sonnet-5
# CDS run. Both models reject the temperature param -> each runs once (sequentially,
# ~3.5h apiece). Resources right-sized from measured utilization: the 5'UTR s5 run
# peaked at 1.2 GB RAM and 13.7 min CPU over 3.6 h on 48 cores (API-bound, not
# compute-bound). 8 CPU / 64 GB is ratio-clean (HPG grants 8 GB/core) with ample
# headroom; the old 48 CPU / 420 GB was ~300x oversized and queued slowly.
# Run from the George project root regardless of where sbatch was submitted.
cd /blue/zhou/leizhou/Agents/George

ml conda

conda activate biomni_e1

mkdir -p output/July_24_2026

echo "Running CDS task with Opus 4.8 + Opus 5 (each once; temperature ignored)..."
python harness/run_biomni.py o4.8 o5 --region CDS --output-dir output/July_24_2026 2>&1 | tee output/July_24_2026/q05cds_opus_$(date +%Y%m%d-%H%M%S).log

echo "CDS Opus run completed!"
