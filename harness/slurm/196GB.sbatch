#!/bin/bash
#SBATCH --job-name=q05_gpt5.2
#SBATCH --mail-type=ALL 
#SBATCH --mail-user=leizhou@ufl.edu 
#SBATCH --nodes=1 
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24
#SBATCH --mem=512gb 
#SBATCH --time=24:00:00
#SBATCH --qos=zhou-b 

ml conda

conda activate biomni_e1

# Submit from the George project root:  sbatch harness/slurm/196GB.sbatch
mkdir -p output
python harness/run_biomni.py 2>&1 | tee output/run_$(date +%Y%m%d-%H%M%S).log
