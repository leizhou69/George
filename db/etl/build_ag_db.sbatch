#!/bin/bash
#SBATCH --job-name=ag_etl_multiregion
#SBATCH --mail-type=ALL
#SBATCH --mail-user=leizhou@ufl.edu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=250gb
#SBATCH --time=24:00:00
#SBATCH --qos=zhou

# ETL: build the multi-region AlphaGenome DuckDB/Parquet backend
# (db/db_construction.md, db/AG_DB_DESIGN.md). Regions + their input TSVs are
# declared in db/etl/regions.json (5UTR + CDS + 3UTR, masked catalogs, no
# pathogenic info). Submit from the George root:
#
#     sbatch db/etl/build_ag_db.sbatch
#
# Builds data/ag_db/{dims,ag_scores} for EVERY region in the manifest. Because
# the dimension surrogate keys (variant_id/gene_id/scorer_id/track_id) are shared
# across regions, this is a FULL rebuild, not an incremental append: all regions'
# AG TSVs must be present (the `preflight` stage fails fast and lists any misses).
#
# Dims are built once from each region's 2x file (tracks/scorers/genes/
# output_types are identical across expansions); the fact is built once per
# (region, expansion) in its own process so memory is released between the
# ~46-293 GB files. Idempotent: reruns overwrite dims and drop+rewrite each
# (region, expansion) partition set.

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

echo "===== $(date) : node $(hostname) : preflight ====="
python db/etl/etl.py preflight

REGIONS=$(python db/etl/etl.py regions)
echo "===== regions to build: ${REGIONS} ====="

echo "===== $(date) : dims (shared, all regions) ====="
python db/etl/etl.py dims

for R in ${REGIONS}; do
  for E in 2 5 20; do
    echo "===== $(date) : fact ${R} ${E}x ====="
    python db/etl/etl.py fact --region "$R" --expansion "$E"
  done
done

echo "===== $(date) : sizes ====="
du -sh data/ag_db data/ag_db/dims data/ag_db/ag_scores

echo "===== $(date) : ETL done. Validate with: python db/etl/validate.py ====="
