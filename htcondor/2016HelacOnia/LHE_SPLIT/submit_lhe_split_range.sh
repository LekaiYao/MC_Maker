#!/bin/bash

set -euo pipefail

BASE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia"
MAKE_SCRIPT="${BASE}/LHE_SPLIT/make_lhe_split_submit.py"
SUBMIT_DIR="${BASE}/LHE_SPLIT/submit"

usage() {
  cat <<'EOF'
Usage:
  bash submit_lhe_split_range.sh <process> <start> <end> [skip_list]

Arguments:
  process    e.g. ggpsi1psi1 or ggpsi1psi1g
  start      integer ProcID start (inclusive)
  end        integer ProcID end (inclusive)
  skip_list  optional, comma-separated; supports:
             1,4,9
             job_1,job_4
EOF
}

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  usage
  exit 1
fi

PROCESS="$1"
START="$2"
END="$3"
SKIP="${4:-}"

python3 "${MAKE_SCRIPT}" --process "${PROCESS}" --start "${START}" --end "${END}" --skip "${SKIP}"

SUB_FILE="${SUBMIT_DIR}/${PROCESS}_jobs_${START}_${END}.sub"
if [ ! -f "${SUB_FILE}" ]; then
  echo "ERROR: submit file not found: ${SUB_FILE}"
  exit 1
fi

echo "Submitting ${SUB_FILE}"
cd "${BASE}/LHE_SPLIT"
condor_submit "${SUB_FILE}"
