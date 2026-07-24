#!/bin/bash
#SBATCH --job-name=q05cds_s5
#SBATCH --mail-type=ALL
#SBATCH --mail-user=leizhou@ufl.edu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=48
#SBATCH --mem=420gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou

# Sonnet-5 run of the CDS task (query_05_cds.txt) against the multi-region AG
# DuckDB backend — searches for candidate pathogenic CDS trinucleotide repeats,
# in the same fashion as the 5'UTR run. Sonnet 5 ignores temperature -> runs once.
# Run from the George project root regardless of where sbatch was submitted.
cd /blue/zhou/leizhou/Agents/George

ml conda

conda activate biomni_e1

mkdir -p output/July_24_2026

echo "Running s5 CDS task (single run; temperature ignored)..."
python harness/run_biomni.py s5 --region CDS --output-dir output/July_24_2026 2>&1 | tee output/July_24_2026/q05cds_s5_$(date +%Y%m%d-%H%M%S).log

echo "s5 CDS run completed!"
