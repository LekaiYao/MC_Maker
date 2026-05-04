#!/bin/bash

set -euo pipefail

CONFIG_FILE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/config/paths.sh"

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <process_name> <job_tag>"
    exit 1
fi

if [ ! -f "${CONFIG_FILE}" ]; then
    echo "Config file not found: ${CONFIG_FILE}"
    exit 1
fi

source "${CONFIG_FILE}"

PROCESS_NAME="$1"
JOB_TAG="$2"
if [[ ! "${JOB_TAG}" =~ ^(job_[^_]+)_(set[0-9]+)$ ]]; then
    echo "Invalid job tag format (expected job_<ProcID>_set<N>): ${JOB_TAG}"
    exit 1
fi
JOB_DIR="${BASH_REMATCH[1]}"
SET_NAME="${BASH_REMATCH[2]}"

INPUT_LHE="${LHE_OUTPUT_BASE}/${PROCESS_NAME}/${JOB_DIR}/${SET_NAME}.lhe"
OUTPUT_DIR="${GEN_OUTPUT_BASE}/${PROCESS_NAME}/${JOB_DIR}"
OUTPUT_ROOT="${OUTPUT_DIR}/${SET_NAME}.root"

if [ ! -f "${INPUT_LHE}" ]; then
    echo "Input LHE not found: ${INPUT_LHE}"
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

run_cms() {
    bash -lc "cmssw-el7 <<'EOF'
cd \"${CMSSW_BASE}/src\"
export SCRAM_ARCH=slc7_amd64_gcc700
cmsenv
cmsRun GEN.py inputLHE=\"file:${INPUT_LHE}\" outputROOT=\"${OUTPUT_ROOT}\"
EOF"
}

attempt=1
max_attempts=2
rc=0
while [ "${attempt}" -le "${max_attempts}" ]; do
    echo "[GEN] cmsRun attempt ${attempt}/${max_attempts}: ${JOB_TAG}"
    if run_cms; then
        exit 0
    fi
    rc=$?
    echo "[GEN] cmsRun failed (attempt ${attempt}, exit=${rc}) for ${JOB_TAG}"
    attempt=$((attempt + 1))
done

echo "[GEN] cmsRun failed after ${max_attempts} attempts for ${JOB_TAG}"
exit "${rc}"
