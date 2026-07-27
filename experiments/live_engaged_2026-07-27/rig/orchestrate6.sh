#!/usr/bin/env bash
# Round 6: the full live proof of the tier ladder + engaged preset.
#  A) gpt-oss:20b — full battery fails -> shallow-fitness battery ->
#     durable shallow tier -> readiness ready_shallow -> shallow run.
#  B) mistral-large-3:675b — requalify under the tier+simulation battery,
#     reason (fresh question), then MCP phase 3 (scratch refs + bridge trio).
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
REPO=/home/user/DeepReason
QUESTION='How can an append-only reasoning log make silent post-crash result divergence structurally impossible, and what is the cheapest durable binding that achieves it?'
set -a; . "$LIVE/env"; set +a
log() { printf '%s %s\n' "$(date -u +%H:%M:%S)" "$*" >> "$LIVE/orchestrator6.log"; }

log "rebuilding wheel at dd0d717"
rm -rf "$LIVE/dist7" && mkdir -p "$LIVE/dist7"
"$REPO/.venv/bin/pip" wheel "$REPO" --no-deps -w "$LIVE/dist7" >> "$LIVE/orchestrator6.log" 2>&1 || { log "WHEEL FAILED"; exit 1; }
"$LIVE/venv/bin/pip" install -q --force-reinstall --no-deps "$LIVE"/dist7/deepreason-*.whl >> "$LIVE/orchestrator6.log" 2>&1
DR="$LIVE/venv/bin/deepreason"

tier_small() {
  export DEEPREASON_HOME="$LIVE/r6-small"
  mkdir -p "$DEEPREASON_HOME"
  {
    echo "=== r6 small (tier ladder) start $(date -u +%FT%TZ) ==="
    timeout 300 "$DR" setup \
      --provider ollama --endpoint https://ollama.com/v1 \
      --model "gpt-oss:20b" --model-revision "gpt-oss:20b" --family "gpt-oss" \
      --context-window-tokens 131072 --maximum-completion-tokens 8192 \
      --credential-env OLLAMA_API_KEY
    echo "setup_rc=$?"
    q0=$SECONDS
    timeout 9000 "$DR" qualify --yes --json
    echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
    echo "--- status after tiering ---"
    timeout 300 "$DR" status --json
    echo "--- full reason must still refuse ---"
    timeout 300 "$DR" reason "tier check?"
    echo "refusal_rc=$?"
    echo "--- shallow run under recorded tier ---"
    s0=$SECONDS
    timeout 5400 "$DR" reason --shallow "$QUESTION"
    echo "shallow_rc=$? shallow_seconds=$((SECONDS-s0))"
    echo "=== r6 small end $(date -u +%FT%TZ) ==="
  } >> "$LIVE/r6-small.log" 2>&1
}

tier_large() {
  export DEEPREASON_HOME="$LIVE/r6-large"
  mkdir -p "$DEEPREASON_HOME"
  {
    echo "=== r6 large start $(date -u +%FT%TZ) ==="
    timeout 300 "$DR" setup \
      --provider ollama --endpoint https://ollama.com/v1 \
      --model "mistral-large-3:675b" --model-revision "mistral-large-3:675b" --family "mistral" \
      --context-window-tokens 131072 --maximum-completion-tokens 8192 \
      --credential-env OLLAMA_API_KEY
    echo "setup_rc=$?"
    q0=$SECONDS
    timeout 9000 "$DR" qualify --yes --json
    echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
    r0=$SECONDS
    timeout 10800 "$DR" reason "$QUESTION" > "$LIVE/r6-reason.json" 2>&1
    rrc=$?
    echo "reason_rc=$rrc reason_seconds=$((SECONDS-r0))"
    run_id=$("$LIVE/venv/bin/python" -c "import json;print(json.load(open('$LIVE/r6-reason.json'))['run_id'])" 2>/dev/null)
    state=$("$LIVE/venv/bin/python" -c "import json;print(json.load(open('$LIVE/r6-reason.json'))['state'])" 2>/dev/null)
    echo "run_id=$run_id state=$state"
    if [ "$state" = "completed" ]; then
      sed -i "s#r5-large#r6-large#" "$LIVE/mcp_phase3.py"
      timeout 3600 "$LIVE/venv/bin/python" "$LIVE/mcp_phase3.py" "$run_id" > "$LIVE/r6-phase3.txt" 2> "$LIVE/r6-phase3.err"
      echo "phase3_rc=$?"
      cat "$LIVE/r6-phase3.txt"
      echo "--- simulation evidence ---"
      root=$(ls -d "$DEEPREASON_HOME"/runs/run-* | head -1)
      echo "simulation_events=$(grep -c 'simulation' "$root/log.jsonl" 2>/dev/null)"
    fi
    echo "=== r6 large end $(date -u +%FT%TZ) ==="
  } >> "$LIVE/r6-large.log" 2>&1
}

log "launching r6 small+large concurrently"
tier_small &
P1=$!
tier_large &
P2=$!
wait $P1; wait $P2
log "round 6 done"
{
  echo "round-6 summary $(date -u +%FT%TZ)"
  for slug in r6-small r6-large; do
    echo "== $slug =="
    grep -E "rc=|seconds|run_id=|tier|state=|simulation_events" "$LIVE/$slug.log" | head -12
  done
} > "$LIVE/summary6.txt" 2>&1
