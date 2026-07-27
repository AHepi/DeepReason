#!/usr/bin/env bash
# Re-run one model's ladder under the current installed battery:
# clear the durable tier conclusion, qualify, reason, bridge trio.
# Usage: run_model.sh <slug> "<question>"
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
slug="$1"; question="$2"
export DEEPREASON_HOME="$LIVE/$slug"
rm -f "$DEEPREASON_HOME"/qualification-cache/*.tier.json
{
  echo "=== $slug LADDER start $(date -u +%FT%TZ) ==="
  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  timeout 300 deepreason status --json
  r0=$SECONDS
  timeout 14400 deepreason reason "$question" > "$LIVE/$slug-reason.json" 2> "$LIVE/$slug-reason.err"
  rrc=$?
  echo "reason_rc=$rrc reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/$slug-reason.json'))['run_id'])" 2>/dev/null)
  problem_id=$(python3 -c "import json;print(json.load(open('$LIVE/$slug-reason.json'))['problem_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/$slug-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id problem_id=$problem_id state=$state"
  if [ "$state" = "completed" ]; then
    b0=$SECONDS
    timeout 7200 python3 "$LIVE/bridge_trio.py" "$DEEPREASON_HOME" "$run_id" "$problem_id" \
      > "$LIVE/$slug-bridge.txt" 2> "$LIVE/$slug-bridge.err"
    echo "bridge_rc=$? bridge_seconds=$((SECONDS-b0))"
    cat "$LIVE/$slug-bridge.txt"
  fi
  echo "=== $slug LADDER end $(date -u +%FT%TZ) ==="
} >> "$LIVE/$slug.log" 2>&1
