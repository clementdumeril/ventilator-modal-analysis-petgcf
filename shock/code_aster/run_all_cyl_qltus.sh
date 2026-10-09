#!/usr/bin/env bash
set -euo pipefail

JOB_DIR="/home/qltus1/aster_jobs/carter_choc_cylindrique_v1"
cd "$JOB_DIR"
mkdir -p logs

for case_id in cyl_ymin cyl_ymax cyl_oblique_ymin_z; do
  echo "===== START ${case_id} $(date -Is) ====="
  ./03_CODE_ASTER/run_one_case_qltus.sh "$case_id" > "logs/run_${case_id}.out" 2>&1
  echo "===== END ${case_id} $(date -Is) ====="
done
