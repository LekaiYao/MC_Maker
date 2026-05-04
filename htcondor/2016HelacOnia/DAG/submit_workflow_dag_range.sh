#!/bin/bash

set -euo pipefail

BASE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia"
SINGLE_SUBMIT="${BASE}/DAG/submit_workflow_dag.sh"

usage() {
  cat <<'EOF'
Usage:
  bash submit_workflow_dag_range.sh <process> <start> <end> [skip_list]

Arguments:
  process    e.g. ggpsi1psi1
  start      integer ProcID start (inclusive)
  end        integer ProcID end (inclusive)
  skip_list  optional, comma-separated.
             supports forms like:
             - 1,4,9
             - job_1,job_4,job_9
             - 1,job_4,9

Example:
  bash submit_workflow_dag_range.sh ggpsi1psi1 0 20 3,7,job_12
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

if [ ! -x "$SINGLE_SUBMIT" ]; then
  echo "ERROR: single DAG submit script is not executable: $SINGLE_SUBMIT"
  exit 1
fi

echo "Batch DAG submit:"
echo "  process = $PROCESS"
echo "  range   = job_${START} .. job_${END}"
if [ -n "$SKIP_RAW" ]; then
  echo "  skip    = $SKIP_RAW"
else
  echo "  skip    = (none)"
fi
echo

submitted=0
skipped=0

for ((pid=START; pid<=END; pid++)); do
  if [[ -n "${SKIP_MAP[$pid]:-}" ]]; then
    echo "[SKIP] job_${pid}"
    skipped=$((skipped+1))
    continue
  fi

  echo "[SUBMIT] job_${pid}"
  bash "$SINGLE_SUBMIT" "$PROCESS" "$pid"
  submitted=$((submitted+1))
done

echo
echo "Done. submitted=${submitted}, skipped=${skipped}"
