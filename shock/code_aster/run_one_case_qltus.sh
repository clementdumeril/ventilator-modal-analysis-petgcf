#!/usr/bin/env bash
set -euo pipefail

CASE_ID="${1:?case id required}"
JOB_DIR="/home/qltus1/aster_jobs/carter_choc_cylindrique_v1"
SIF="/home/qltus1/OpenFOAM/apps/code_aster/code_aster_stable.sif"

cd "$JOB_DIR"
mkdir -p logs 04_RESULTATS

apptainer exec --bind /home:/home "$SIF" bash -lc "source /opt/activate.sh && cd '$JOB_DIR' && run_aster '$JOB_DIR/03_CODE_ASTER/carter_choc_${CASE_ID}.export'"
