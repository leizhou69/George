#!/bin/bash
#SBATCH --job-name=q05b_s5
#SBATCH --mail-type=ALL
#SBATCH --mail-user=leizhou@ufl.edu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou-b

# 5UTR task with Sonnet 5 (rejects temperature -> runs once; --temperatures 0.5
# pins the Tmp0.5 label to match prior other models' runs).
cd /blue/zhou/leizhou/Agents/George
ml conda
conda activate biomni_e1
# Fail the job (not "COMPLETED") if the harness fails; set after conda activate,
# and without -u, because conda's activate scripts reference unset vars.
set -eo pipefail
mkdir -p output/Nov_11_2026_remasked
python harness/run_george.py s5 --region 5UTR --temperatures 0.5 --output-dir output/Nov_11_2026_remasked \
  2>&1 | tee output/Nov_11_2026_remasked/q05b_s5_$(date +%Y%m%d-%H%M%S).log
echo "5UTR Sonnet 5 run completed!"
