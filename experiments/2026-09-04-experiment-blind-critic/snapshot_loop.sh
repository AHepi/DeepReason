#!/bin/sh
# Snapshot loop: the container can roll back and take every gitignored file
# with it, so the raw call ledger is committed as it grows rather than at the
# end. Run roots are committed at the end (they are large and only complete
# once). Stops when the driver's pid is gone.
PID="$1"
cd "$(dirname "$0")/../.." || exit 1
while kill -0 "$PID" 2>/dev/null; do
  sleep 300
  git add experiments/2026-09-04-experiment-blind-critic/raw/calls.jsonl \
          experiments/2026-09-04-experiment-blind-critic/raw/driver.log 2>/dev/null
  git diff --cached --quiet || git commit -q -m "snapshot: bench calls in flight

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_0155ZmXHQdP1GQDMpB95kAKa"
  git push -q origin claude/blind-critic-experiment-synir6 2>/dev/null
done
