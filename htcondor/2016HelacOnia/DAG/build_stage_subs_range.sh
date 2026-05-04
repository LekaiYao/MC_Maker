#!/bin/bash

set -euo pipefail

BASE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia"

usage() {
  cat <<'EOF'
Usage:
  bash build_stage_subs_range.sh <process> <start> <end> [skip_list]

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
SKIP_RAW="${4:-}"

if ! [[ "$START" =~ ^[0-9]+$ ]]; then
  echo "ERROR: start must be integer, got: $START"
  exit 1
fi
if ! [[ "$END" =~ ^[0-9]+$ ]]; then
  echo "ERROR: end must be integer, got: $END"
  exit 1
fi
if [ "$START" -gt "$END" ]; then
  echo "ERROR: start ($START) > end ($END)"
  exit 1
fi

declare -A SKIP_MAP=()
if [ -n "$SKIP_RAW" ]; then
  IFS=',' read -r -a TOKENS <<< "$SKIP_RAW"
  for token in "${TOKENS[@]}"; do
    t="${token// /}"
    [ -z "$t" ] && continue
    if [[ "$t" =~ ^job_([0-9]+)$ ]]; then
      pid="${BASH_REMATCH[1]}"
    elif [[ "$t" =~ ^[0-9]+$ ]]; then
      pid="$t"
    else
      echo "ERROR: invalid skip item: $t"
      exit 1
    fi
    SKIP_MAP["$pid"]=1
  done
fi

STAGES=(
  "GEN/make_gen_submit.py"
  "SIM/make_sim_submit.py"
  "DIGI/make_digi_submit.py"
  "HLT/make_hlt_submit.py"
  "RECO/make_reco_submit.py"
  "MINIAOD/make_miniaod_submit.py"
  "NTUPLE/make_ntuple_submit.py"
)

generated=0
skipped=0

for ((pid=START; pid<=END; pid++)); do
  if [[ -n "${SKIP_MAP[$pid]:-}" ]]; then
    echo "[SKIP] job_${pid}"
    skipped=$((skipped+1))
    continue
  fi

  echo "[BUILD] ${PROCESS} job_${pid}"
  export DAG_PROCESS="${PROCESS}"
  export DAG_PROCID="${pid}"
  for stage_script in "${STAGES[@]}"; do
    python3 "${BASE}/${stage_script}"
  done
  generated=$((generated+1))
done

unset DAG_PROCESS
unset DAG_PROCID

echo "Done. generated=${generated}, skipped=${skipped}"
