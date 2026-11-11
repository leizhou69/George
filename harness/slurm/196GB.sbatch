#!/bin/bash
#SBATCH --job-name=q05_gpt5.2
#SBATCH --mail-type=ALL 
#SBATCH --mail-user=leizhou@ufl.edu 
#SBATCH --nodes=1 
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou-b 

# Run from the George project root regardless of where sbatch was submitted.
cd /blue/zhou/leizhou/Agents/George

ml conda

conda activate biomni_e1
# Fail the job (not "COMPLETED") if the harness fails; set after conda activate,
# and without -u, because conda's activate scripts reference unset vars.
set -eo pipefail

mkdir -p output
python harness/run_george.py 2>&1 | tee output/run_$(date +%Y%m%d-%H%M%S).log
