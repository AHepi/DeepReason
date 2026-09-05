#!/bin/bash
# Same bounded-batch pattern as run_judging.sh, for the same reason: two long
# scoring processes were killed part-way earlier in this tranche with no error
# in either log. judge_replication.py resumes from blind-r/scores.json and
# skips any bid already scored, so repeated passes each bank their progress and
# a kill costs at most the handful of candidates in flight.
set -u
cd /home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel
N=$(wc -l < blind-r/candidates.jsonl)
for pass in $(seq 1 40); do
  n=$(python3 -c "
import json,pathlib
p=pathlib.Path('blind-r/scores.json')
print(len(json.load(open(p))) if p.exists() else 0)")
  echo "### pass $pass starting at $n/$N $(date -u +%FT%TZ)"
  [ "$n" -ge "$N" ] && { echo '### COMPLETE'; break; }
  python3 judge_replication.py score >> blind-r/score.log 2>&1
done
echo "### replicate judging finished $(date -u +%FT%TZ)"
