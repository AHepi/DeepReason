#!/usr/bin/env bash
# Native-vs-DeepReason comparison: one harness-design question, three
# frontier Ollama Cloud models.  Native baselines are one-shot with
# thinking on; DeepReason ladders run strictly sequentially because
# qualification itself now dispatches 3 concurrent cases (the
# account-wide concurrent-request cap).
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a

QUESTION='When two independently generated conclusions inside a deterministic reasoning system appear to agree, by what criteria should the system decide they are the same claim rather than distinct claims that merely overlap, and what does it risk by merging too eagerly or too reluctantly?'

log() { printf '%s %s\n' "$(date -u +%H:%M:%S)" "$*" >> "$LIVE/orchestrator.log"; }

log "native one-shots"
python3 "$LIVE/native_oneshot.py" >> "$LIVE/orchestrator.log" 2>&1

run_one() {
  slug="$1"; family="$2"; model="$3"; completion="$4"
  export DEEPREASON_HOME="$LIVE/$slug"
  mkdir -p "$DEEPREASON_HOME"
  {
    echo "=== $slug ($model) start $(date -u +%FT%TZ) ==="
    timeout 300 deepreason setup \
      --provider ollama --endpoint https://ollama.com/v1 \
      --model "$model" --model-revision "$model" --family "$family" \
      --context-window-tokens 131072 --maximum-completion-tokens "$completion" \
      --credential-env OLLAMA_API_KEY
    echo "setup_rc=$?"
    q0=$SECONDS
    timeout 14400 deepreason qualify --yes --json --concurrency 3
    echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
    timeout 300 deepreason status --json
    r0=$SECONDS
    timeout 14400 deepreason reason "$QUESTION" \
      > "$LIVE/$slug-reason.json" 2> "$LIVE/$slug-reason.err"
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
    echo "=== $slug end $(date -u +%FT%TZ) ==="
  } >> "$LIVE/$slug.log" 2>&1
}

log "glm ladder"
run_one glm glm glm-5.2 8192
log "kimi ladder"
run_one kimi kimi kimi-k2.6 16384
log "deepseek ladder"
run_one deepseek deepseek deepseek-v4-pro 8192
log "compare-run done"

{
  echo "compare-run summary $(date -u +%FT%TZ)"
  for slug in glm kimi deepseek; do
    echo "== $slug =="
    grep -E "rc=|seconds|run_id=|state=|tier|passed" "$LIVE/$slug.log" | head -14
  done
} > "$LIVE/summary.txt" 2>&1
