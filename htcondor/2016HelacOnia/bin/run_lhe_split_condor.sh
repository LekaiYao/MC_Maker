#!/bin/bash

set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <process> <procid>"
  exit 1
fi

PROCESS="$1"
PROCID="$2"

BASE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia"
PREP_SCRIPT="${BASE}/bin/prepare_lhe_inputs.py"

python3 "${PREP_SCRIPT}" --process "${PROCESS}" --procid "${PROCID}" --force
