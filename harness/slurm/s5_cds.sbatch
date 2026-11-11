#!/bin/bash
#SBATCH --job-name=q05cds_s5
#SBATCH --mail-type=ALL
#SBATCH --mail-user=leizhou@ufl.edu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou

# Sonnet-5 run of the CDS task (query_05_cds.txt) against the multi-region AG
# DuckDB backend — searches for candidate pathogenic CDS trinucleotide repeats,
# in the same fashion as the 5'UTR run. Sonnet 5 ignores temperature -> runs once.
# Run from the George project root regardless of where sbatch was submitted.
cd /blue/zhou/leizhou/Agents/George

ml conda

conda activate biomni_e1
# Fail the job (not "COMPLETED") if the harness fails; set after conda activate,
# and without -u, because conda's activate scripts reference unset vars.
set -eo pipefail

mkdir -p output/Nov_11_2026_remasked

echo "Running s5 CDS task (single run; temperature ignored)..."
python harness/run_george.py s5 --region CDS --output-dir output/Nov_11_2026_remasked 2>&1 | tee output/Nov_11_2026_remasked/q05cds_s5_$(date +%Y%m%d-%H%M%S).log

echo "s5 CDS run completed!"
