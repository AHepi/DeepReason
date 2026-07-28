#!/usr/bin/env bash
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
QUESTION='When two independently generated conclusions inside a deterministic reasoning system appear to agree, by what criteria should the system decide they are the same claim rather than distinct claims that merely overlap, and what does it risk by merging too eagerly or too reluctantly?'
export DEEPREASON_HOME="$LIVE/glm2"
mkdir -p "$DEEPREASON_HOME"
{
  echo "=== glm2 (glm-5.2, fresh root after bridge-dead glm) start $(date -u +%FT%TZ) ==="
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 8192 \
    --credential-env OLLAMA_API_KEY
  echo "setup_rc=$?"
  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  r0=$SECONDS
  timeout 14400 deepreason reason "$QUESTION" > "$LIVE/glm2-reason.json" 2> "$LIVE/glm2-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/glm2-reason.json'))['run_id'])" 2>/dev/null)
  problem_id=$(python3 -c "import json;print(json.load(open('$LIVE/glm2-reason.json'))['problem_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/glm2-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id problem_id=$problem_id state=$state"
  if [ "$state" = "completed" ]; then
    b0=$SECONDS
    timeout 7200 python3 "$LIVE/bridge_trio.py" "$DEEPREASON_HOME" "$run_id" "$problem_id" \
      > "$LIVE/glm2-bridge.txt" 2> "$LIVE/glm2-bridge.err"
    echo "bridge_rc=$? bridge_seconds=$((SECONDS-b0))"
    cat "$LIVE/glm2-bridge.txt"
  fi
  echo "=== glm2 end $(date -u +%FT%TZ) ==="
} >> "$LIVE/glm2.log" 2>&1
