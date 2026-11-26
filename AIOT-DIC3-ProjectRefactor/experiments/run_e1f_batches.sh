#!/bin/bash
# Run the E1f LLM experiment on the Gemini free tier until every sampled incident is done.
# Each pass resumes from experiments/results/e1f_llm_cache.jsonl, so quota limits (429) or
# overload (503) only pause the run. caffeinate keeps the Mac awake while it runs.
#
# Usage (from AIOT-DIC3-ProjectRefactor/):
#   caffeinate -i bash experiments/run_e1f_batches.sh 50 150
# Arguments: number of validation incidents, number of test incidents.
set -u
N_VAL=${1:-50}
N_TEST=${2:-150}
MODEL=${MODEL:-gemini-3.5-flash}
INTERVAL=${INTERVAL:-12}
PAUSE=${PAUSE:-600}        # seconds to wait after a quota/overload stop
MAX_PASSES=${MAX_PASSES:-300}  # safety stop (about 2+ days of pauses)
PASSES=0
LOG=experiments/results/e1f_run.log
PY=../.venv/bin/python

done_count() {  # number of incidents with both modes cached for this split's sample
  $PY - "$1" "$2" "$MODEL" <<'EOF'
import json, sys
from pathlib import Path
split, n, model = sys.argv[1], int(sys.argv[2]), sys.argv[3]
s = Path(f"experiments/results/e1f_keys_{split}.txt")
if not s.exists():
    print(0); sys.exit()
keys = s.read_text().split()[:n]
c = Path("experiments/results/e1f_llm_cache.jsonl")
have = {}
if c.exists():
    for line in c.read_text().splitlines():
        r = json.loads(line)
        if r["model"] == model:
            have.setdefault(r["incident"], set()).add(r["mode"])
print(sum(1 for k in keys if have.get(k, set()) >= {"llm_only", "agent"}))
EOF
}

for SPLIT_N in "val $N_VAL" "test $N_TEST"; do
  set -- $SPLIT_N
  SPLIT=$1; N=$2
  while true; do
    D=$(done_count "$SPLIT" "$N")
    echo "$(date '+%F %T') $SPLIT: $D/$N incidents done" | tee -a "$LOG"
    [ "$D" -ge "$N" ] && break
    $PY -W ignore experiments/e1f_llm.py --split "$SPLIT" --n "$N" --model "$MODEL" --interval "$INTERVAL" \
      2>&1 | grep -E '^\[|quota|overloaded|incidents_done|Traceback|Error' | tee -a "$LOG"
    D2=$(done_count "$SPLIT" "$N")
    [ "$D2" -ge "$N" ] && continue
    PASSES=$((PASSES + 1))
    if [ "$PASSES" -ge "$MAX_PASSES" ]; then echo "$(date '+%F %T') stopping after $PASSES passes" | tee -a "$LOG"; exit 1; fi
    echo "$(date '+%F %T') pausing ${PAUSE}s before resuming" | tee -a "$LOG"
    sleep "$PAUSE"
  done
done
echo "$(date '+%F %T') ALL DONE" | tee -a "$LOG"
