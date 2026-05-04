#!/bin/bash

set -euo pipefail

CONFIG_FILE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/config/paths.sh"

if [ "$#" -ne 4 ] && [ "$#" -ne 6 ]; then
    echo "Usage: $0 <input_miniaod> <output_ntuple> <process_name> <job_label> [skip_events max_events]"
    exit 1
fi

source "${CONFIG_FILE}"

INPUT_MINIAOD="$1"
OUTPUT_NTUPLE="$2"
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

if [ ! -f "${INPUT_MINIAOD}" ]; then
    echo "Input MINIAOD ROOT not found: ${INPUT_MINIAOD}"
    exit 1
fi

mkdir -p "$(dirname "${OUTPUT_NTUPLE}")"

# Entering NTUPLE(step7): remove RECO(step5) same-set ROOT to save space.
RECO_SET_ROOT="${RECO_OUTPUT_BASE}/${PROCESS_NAME}/${JOB_DIR}/${SET_NAME}.root"
if [ -f "${RECO_SET_ROOT}" ]; then
    echo "[NTUPLE] remove n-2 ROOT before cmsRun: ${RECO_SET_ROOT}"
    rm -f "${RECO_SET_ROOT}"
fi

run_cms() {
    bash -lc "cmssw-el7 <<'EOF2'
cd \"${NTUPLE_CMSSW_BASE}/src\"
export SCRAM_ARCH=slc7_amd64_gcc700
cmsenv
cd NtupleMaker/NtupleMaker/test
cmsRun NTUPLE.py inputMINIAOD=\"file:${INPUT_MINIAOD}\" outputNTUPLE=\"${OUTPUT_NTUPLE}\" skipEvents=${SKIP_EVENTS} maxEvents=${MAX_EVENTS}
EOF2"
}

attempt=1
max_attempts=2
rc=0
while [ "${attempt}" -le "${max_attempts}" ]; do
    echo "[NTUPLE] cmsRun attempt ${attempt}/${max_attempts}: ${JOB_LABEL}"
    if run_cms; then
        exit 0
    fi
    rc=$?
    echo "[NTUPLE] cmsRun failed (attempt ${attempt}, exit=${rc}) for ${JOB_LABEL}"
    attempt=$((attempt + 1))
done

echo "[NTUPLE] cmsRun failed after ${max_attempts} attempts for ${JOB_LABEL}"
exit "${rc}"
