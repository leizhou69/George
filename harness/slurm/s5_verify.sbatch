#!/bin/bash
#SBATCH --job-name=q05_s5_verify
#SBATCH --mail-type=ALL
#SBATCH --mail-user=leizhou@ufl.edu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=48
#SBATCH --mem=420gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou

# Sonnet-5-only verification run: repeats the last s5 run (query_05_b) against the
# new multi-region AG DuckDB backend to confirm the ag_db works end-to-end.
# Sonnet 5 ignores temperature, so it runs exactly once.
# Run from the George project root regardless of where sbatch was submitted.
cd /blue/zhou/leizhou/Agents/George

ml conda

conda activate biomni_e1

mkdir -p output/July_24_2026

echo "Running s5 verification (single run; temperature ignored)..."
python harness/run_biomni.py s5 --output-dir output/July_24_2026 2>&1 | tee output/July_24_2026/q05_s5_verify_$(date +%Y%m%d-%H%M%S).log

echo "s5 verification run completed!"
