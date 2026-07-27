#!/usr/bin/env bash
# Retry the full qualification ladder for pipelines whose first battery
# failed on one stochastic pair (glm: /pairs/3, deepseek: /pairs/10).
# The durable shallow tier record is cleared first: an explicit qualify
# rerun then retries the ladder from the top, as _cmd_qualify documents.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a

log() { printf '%s %s\n' "$(date -u +%H:%M:%S)" "$*" >> "$LIVE/orchestrator.log"; }

run_one() {
  slug="$1"; question="$2"
  export DEEPREASON_HOME="$LIVE/$slug"
  rm -f "$DEEPREASON_HOME"/qualification-cache/*.tier.json
  {
    echo "=== $slug RETRY start $(date -u +%FT%TZ) ==="
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
    echo "=== $slug RETRY end $(date -u +%FT%TZ) ==="
  } >> "$LIVE/$slug.log" 2>&1
}

log "retrying glm + deepseek qualification ladder"
run_one glm 'When a bounded reasoning run halts because its token budget is exhausted, under what exact conditions can it be resumed later without corrupting the append-only identity of what was already recorded, and when must resumption stay forbidden?' &
P1=$!
run_one deepseek 'Should the fetch budget of a replayable autonomous research agent be denominated in requests, bytes, or both, and how must exhaustion be recorded so it remains a typed auditable terminal instead of a silent degradation?' &
P2=$!
wait $P1; wait $P2
log "retry done"
