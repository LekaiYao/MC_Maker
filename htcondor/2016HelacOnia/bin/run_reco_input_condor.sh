#!/bin/bash

set -euo pipefail

CONFIG_FILE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/config/paths.sh"

if [ "$#" -ne 4 ] && [ "$#" -ne 6 ]; then
    echo "Usage: $0 <input_hlt> <output_reco> <process_name> <job_label> [skip_events max_events]"
    exit 1
fi

if [ ! -f "${CONFIG_FILE}" ]; then
    echo "Config file not found: ${CONFIG_FILE}"
    exit 1
fi

source "${CONFIG_FILE}"

INPUT_HLT="$1"
OUTPUT_RECO="$2"
PROCESS_NAME="$3"
JOB_LABEL="$4"
SKIP_EVENTS="${5:-0}"
MAX_EVENTS="${6:--1}"

if [[ ! "${JOB_LABEL}" =~ ^(job_[^_]+)_(set[0-9]+)$ ]]; then
    echo "Invalid job label format (expected job_<ProcID>_set<N>): ${JOB_LABEL}"
    exit 1
fi
JOB_DIR="${BASH_REMATCH[1]}"
SET_NAME="${BASH_REMATCH[2]}"

if [ ! -f "${INPUT_HLT}" ]; then
    echo "Input HLT ROOT not found: ${INPUT_HLT}"
    exit 1
fi

mkdir -p "$(dirname "${OUTPUT_RECO}")"

# Entering RECO(step5): remove DIGI(step3) same-set ROOT to save space.
DIGI_SET_ROOT="${DIGI_OUTPUT_BASE}/${PROCESS_NAME}/${JOB_DIR}/${SET_NAME}.root"
if [ -f "${DIGI_SET_ROOT}" ]; then
    echo "[RECO] remove n-2 ROOT before cmsRun: ${DIGI_SET_ROOT}"
    rm -f "${DIGI_SET_ROOT}"
fi

run_cms() {
    bash -lc "cmssw-el7 <<'EOF'
cd \"${SIM_CMSSW_BASE}/src\"
export SCRAM_ARCH=slc7_amd64_gcc700
cmsenv
cmsRun RECO.py inputHLT=\"file:${INPUT_HLT}\" outputRECO=\"${OUTPUT_RECO}\" skipEvents=${SKIP_EVENTS} maxEvents=${MAX_EVENTS}
EOF"
}

attempt=1
max_attempts=2
rc=0
while [ "${attempt}" -le "${max_attempts}" ]; do
    echo "[RECO] cmsRun attempt ${attempt}/${max_attempts}: ${JOB_LABEL}"
    if run_cms; then
        exit 0
    fi
    rc=$?
    echo "[RECO] cmsRun failed (attempt ${attempt}, exit=${rc}) for ${JOB_LABEL}"
    attempt=$((attempt + 1))
done

echo "[RECO] cmsRun failed after ${max_attempts} attempts for ${JOB_LABEL}"
exit "${rc}"
