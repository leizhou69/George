#!/bin/bash
#SBATCH --job-name=q05_s5_o4.8
#SBATCH --mail-type=ALL
#SBATCH --mail-user=leizhou@ufl.edu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=48
#SBATCH --mem=420gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou

ml conda

conda activate biomni_e1

# Submit from the George project root:  sbatch harness/slurm/512GB.sbatch
mkdir -p output/July_20_2026

echo "Running s5 and o4.8 (all temps)..."
python harness/run_biomni.py s5 o4.8 --output-dir output/July_20_2026 2>&1 | tee output/July_20_2026/q05_s5_o4.8_$(date +%Y%m%d-%H%M%S).log

echo "s5 and o4.8 run completed!"
