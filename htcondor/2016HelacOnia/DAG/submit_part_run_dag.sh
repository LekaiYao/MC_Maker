#!/bin/bash

set -euo pipefail

BASE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia"

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <process> <procid>"
  exit 1
fi

PROCESS="$1"
PROCID="$2"
RUN_TAG="${PROCESS}_job_${PROCID}"
RUN_DIR="${BASE}/DAG/part_runs/${RUN_TAG}"
DAG_FILE="${RUN_DIR}/part_run_${RUN_TAG}.dag"

python3 "${BASE}/DAG/build_part_run_dag.py" "${PROCESS}" "${PROCID}"

if [ ! -f "${DAG_FILE}" ]; then
  echo "ERROR: DAG file not found: ${DAG_FILE}"
  exit 1
fi

cd "${RUN_DIR}"
condor_submit_dag "${DAG_FILE}"
