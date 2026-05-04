#!/bin/bash

set -euo pipefail

BASE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia"
TEMPLATE_DAG_FILE="${BASE}/DAG/workflow.dag"
LOG_DIR="${BASE}/DAG/logs"

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <process> <procid>"
  exit 1
fi

PROCESS="$1"
PROCID="$2"
RUN_TAG="${PROCESS}_job_${PROCID}"
RUN_DIR="${BASE}/DAG/runs/${RUN_TAG}"
RUN_DAG_FILE="${RUN_DIR}/workflow_${RUN_TAG}.dag"
RUN_STAGE_SUB="${RUN_DIR}/stage_driver_${RUN_TAG}.sub"

mkdir -p "${LOG_DIR}" "${RUN_DIR}"

cat > "${RUN_STAGE_SUB}" <<EOF
universe = scheduler
executable = ${BASE}/bin/dag_stage_driver.py
arguments = \$(stage)
output = ${LOG_DIR}/${RUN_TAG}_\$(stage).out
error = ${LOG_DIR}/${RUN_TAG}_\$(stage).err
log = ${LOG_DIR}/${RUN_TAG}_\$(stage).log
getenv = True
should_transfer_files = NO
queue
EOF

sed "s|${BASE}/DAG/submit/stage_driver.sub|${RUN_STAGE_SUB}|g" "${TEMPLATE_DAG_FILE}" > "${RUN_DAG_FILE}"

cd "${RUN_DIR}"
condor_submit_dag -append "environment = \"DAG_PROCESS=${PROCESS} DAG_PROCID=${PROCID}\"" "${RUN_DAG_FILE}"
