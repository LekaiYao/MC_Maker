#!/bin/bash

set -euo pipefail

CONFIG_FILE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/config/paths.sh"

if [ "$#" -ne 4 ] && [ "$#" -ne 6 ]; then
    echo "Usage: $0 <input_gen> <output_sim> <process_name> <job_label> [skip_events max_events]"
    exit 1
fi

if [ ! -f "${CONFIG_FILE}" ]; then
    echo "Config file not found: ${CONFIG_FILE}"
    exit 1
fi

source "${CONFIG_FILE}"

INPUT_GEN="$1"
OUTPUT_SIM="$2"
PROCESS_NAME="$3"
JOB_LABEL="$4"
SKIP_EVENTS="${5:-0}"
MAX_EVENTS="${6:--1}"

if [ ! -f "${INPUT_GEN}" ]; then
    echo "Input GEN ROOT not found: ${INPUT_GEN}"
    exit 1
fi

mkdir -p "$(dirname "${OUTPUT_SIM}")"

run_cms() {
    bash -lc "cmssw-el7 <<'INNER_EOF'
cd \"${SIM_CMSSW_BASE}/src\"
export SCRAM_ARCH=slc7_amd64_gcc700
cmsenv
cmsRun SIM.py inputGEN=\"file:${INPUT_GEN}\" outputSIM=\"${OUTPUT_SIM}\" skipEvents=${SKIP_EVENTS} maxEvents=${MAX_EVENTS}
INNER_EOF"
}

attempt=1
max_attempts=2
rc=0
while [ "${attempt}" -le "${max_attempts}" ]; do
    echo "[SIM] cmsRun attempt ${attempt}/${max_attempts}: ${JOB_LABEL}"
    if run_cms; then
        exit 0
    fi
    rc=$?
    echo "[SIM] cmsRun failed (attempt ${attempt}, exit=${rc}) for ${JOB_LABEL}"
    attempt=$((attempt + 1))
done

echo "[SIM] cmsRun failed after ${max_attempts} attempts for ${JOB_LABEL}"
exit "${rc}"
