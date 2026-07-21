#!/bin/bash
#SBATCH --job-name=ag_etl_5utr
#SBATCH --mail-type=ALL
#SBATCH --mail-user=leizhou@ufl.edu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=250gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou

# Phase 4 ETL: build the AlphaGenome DuckDB/Parquet backend (db/AG_DB_DESIGN.md).
# Submit from the George project root:  sbatch db/etl/build_ag_db.sbatch
#
# Builds data/ag_db/{dims,ag_scores}. Dims are built from the 2x file only
# (tracks/scorers/genes/output_types are identical across expansions); the fact
# is built once per expansion in its own process so memory is released between
# the three ~30 GB files. Idempotent: reruns overwrite dims and drop+rewrite
# each expansion's partitions.

# Always run from the George project root so relative paths resolve, regardless
# of the directory sbatch was submitted from.
cd /blue/zhou/leizhou/Agents/George

# conda's activate.d MKL script references unset vars, so activate BEFORE
# enabling `nounset`. `-u` is intentionally omitted (it breaks conda).
ml conda
conda activate biomni_e1
set -eo pipefail

# Give DuckDB most of the RAM for in-memory hash joins; still allow disk spill.
export AG_THREADS=32
export AG_MEM=200GB
export AG_TMP=db/etl/duck_tmp
mkdir -p "$AG_TMP" data/ag_db

echo "===== $(date) : node $(hostname) : dims ====="
python db/etl/etl.py dims

for E in 2 5 20; do
  echo "===== $(date) : fact ${E}x ====="
  python db/etl/etl.py fact --expansion "$E"
done

echo "===== $(date) : sizes ====="
du -sh data/ag_db data/ag_db/dims data/ag_db/ag_scores

echo "===== $(date) : ETL done. Validate with: python db/etl/validate.py ====="
