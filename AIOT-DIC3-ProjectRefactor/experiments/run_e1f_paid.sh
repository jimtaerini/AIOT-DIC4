#!/bin/bash
# Run the E1f LLM experiment on the paid Gemini tier with parallel calls.
# Resumable: cached results in experiments/results/e1f_llm_cache.jsonl are reused.
# Usage (from AIOT-DIC3-ProjectRefactor/):  caffeinate -i bash experiments/run_e1f_paid.sh 50 150
set -u
MODEL=${MODEL:-gemini-3.8-flash}
WORKERS=${WORKERS:-8}
for SPLIT_N in "val ${1:-50}" "test ${2:-150}"; do
  read -r SPLIT N <<< "$SPLIT_N"
  for PASS in 1 2 3; do
    ../.venv/bin/python -W ignore experiments/e1f_llm.py --split "$SPLIT" --n "$N" --model "$MODEL" \
      --interval 0.2 --workers "$WORKERS" > "experiments/results/e1f_${SPLIT}_summary.json.log" 2>&1
    grep -q "\"incidents_done\": $N," "experiments/results/e1f_${SPLIT}_summary.json.log" && break
    sleep 60
  done
  echo "$(date '+%F %T') $SPLIT pass $PASS"; grep -E 'quota|overloaded|incidents_done|Error' "experiments/results/e1f_${SPLIT}_summary.json.log"
done
