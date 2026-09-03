#!/bin/bash
# Resume scoring in BOUNDED BATCHES.
#
# Two long-running attempts were killed part-way (at 50/167 and 65/167) with no
# error in either log -- the process disappears rather than failing. Cause not
# established; the container reaping a long-lived detached process is the
# obvious candidate and is not worth diagnosing to finish a measurement.
#
# judge.py already resumes from scores.json and skips any bid already scored,
# so the fix is simply to stop betting on one long process: run it repeatedly,
# and let each pass bank its progress to disk. A kill now costs at most the
# handful of candidates in flight.
set -u
cd /home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel
for pass in $(seq 1 40); do
  n=$(python3 -c "
import json,pathlib
p=pathlib.Path('blind/scores.json')
print(len(json.load(open(p))) if p.exists() else 0)")
  echo "### pass $pass starting at $n/167 $(date -u +%FT%TZ)"
  [ "$n" -ge 167 ] && { echo '### COMPLETE'; break; }
  python judge.py score >> blind/score_batched.log 2>&1
done
echo "### batched judging finished $(date -u +%FT%TZ)"
