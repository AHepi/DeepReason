#!/usr/bin/env bash
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
QUESTION='When two independently generated conclusions inside a deterministic reasoning system appear to agree, by what criteria should the system decide they are the same claim rather than distinct claims that merely overlap, and what does it risk by merging too eagerly or too reluctantly?'
export DEEPREASON_HOME="$LIVE/deepseek"
{
  echo "=== deepseek RETRY start $(date -u +%FT%TZ) ==="
  # One explicit retry of the ladder: clear the durable shallow tier so
  # qualify reruns the full battery from the top (run_model.sh idiom).
  rm -f "$DEEPREASON_HOME"/qualification-cache/*.tier.json
  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  r0=$SECONDS
  timeout 14400 deepreason reason "$QUESTION" > "$LIVE/deepseek-reason.json" 2> "$LIVE/deepseek-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/deepseek-reason.json'))['run_id'])" 2>/dev/null)
  problem_id=$(python3 -c "import json;print(json.load(open('$LIVE/deepseek-reason.json'))['problem_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/deepseek-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id problem_id=$problem_id state=$state"
  if [ "$state" = "completed" ]; then
    b0=$SECONDS
    timeout 7200 python3 "$LIVE/bridge_trio.py" "$DEEPREASON_HOME" "$run_id" "$problem_id" \
      > "$LIVE/deepseek-bridge.txt" 2> "$LIVE/deepseek-bridge.err"
    echo "bridge_rc=$? bridge_seconds=$((SECONDS-b0))"
  else
    echo "second battery verdict stands; recording shallow answer for the comparison"
    timeout 7200 deepreason reason --shallow "$QUESTION" > "$LIVE/deepseek-shallow.json" 2> "$LIVE/deepseek-shallow.err"
    echo "shallow_rc=$?"
  fi
  echo "=== deepseek RETRY end $(date -u +%FT%TZ) ==="
} >> "$LIVE/deepseek-retry.log" 2>&1
