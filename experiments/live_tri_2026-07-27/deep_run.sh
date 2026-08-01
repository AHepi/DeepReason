#!/usr/bin/env bash
# Deep pass: one model, policy-maximum budget (12 cycles, 200k tokens),
# fresh deterministic root, then the bridge trio.
# Usage: deep_run.sh <slug> "<question>"
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
slug="$1"; question="$2"
export DEEPREASON_HOME="$LIVE/$slug"
{
  echo "=== $slug DEEP start $(date -u +%FT%TZ) ==="
  r0=$SECONDS
  timeout 14400 deepreason reason --cycles 12 --token-budget 200000 "$question" \
    > "$LIVE/$slug-deep-reason.json" 2> "$LIVE/$slug-deep-reason.err"
  rrc=$?
  echo "reason_rc=$rrc reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/$slug-deep-reason.json'))['run_id'])" 2>/dev/null)
  problem_id=$(python3 -c "import json;print(json.load(open('$LIVE/$slug-deep-reason.json'))['problem_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/$slug-deep-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id problem_id=$problem_id state=$state"
  if [ "$state" = "completed" ]; then
    b0=$SECONDS
    timeout 7200 python3 "$LIVE/bridge_trio.py" "$DEEPREASON_HOME" "$run_id" "$problem_id" \
      > "$LIVE/$slug-deep-bridge.txt" 2> "$LIVE/$slug-deep-bridge.err"
    echo "bridge_rc=$? bridge_seconds=$((SECONDS-b0))"
    cat "$LIVE/$slug-deep-bridge.txt"
  fi
  echo "=== $slug DEEP end $(date -u +%FT%TZ) ==="
} >> "$LIVE/$slug.log" 2>&1
