#!/bin/bash
# Rollback insurance for the D8 arms: commit and push whatever the arms wrote
# under THIS tranche every five minutes, until the watched driver is gone.
# Path-scoped copy of experiments/live_research_2026-07-29/snapshot_loop.sh.
set -u
DRIVER="${1:-run_chain.sh}"
cd /home/user/DeepReason || exit 1
REL=experiments/2026-09-06-change-writers-room-limits-and-forms
BRANCH=claude/mini-isolation-t3-t5-7tsc6d
while true; do
  sleep 300
  git add -A "$REL" >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$REL" 2>/dev/null; then
    git commit -q -m "WR snapshot ($(date -u +%FT%TZ))" -- "$REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  pgrep -f "$DRIVER" >/dev/null 2>&1 || break
done
echo "snapshot loop finished: $DRIVER no longer running"
