#!/usr/bin/env bash
# Tri-model live run: three frontier Ollama Cloud models, three
# harness-design problems, fully concurrent (one single-threaded root per
# model respects the account-wide 3-concurrent-request cap).
# Per model: setup -> qualify -> reason -> bridge trio (Stage A + Stage B).
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a

log() { printf '%s %s\n' "$(date -u +%H:%M:%S)" "$*" >> "$LIVE/orchestrator.log"; }

# Resolve the exact hosted model ids up front; fail loudly if absent.
python3 - "$LIVE" <<'EOF'
import json, os, sys, urllib.request
live = sys.argv[1]
req = urllib.request.Request(
    "https://ollama.com/v1/models",
    headers={"Authorization": "Bearer " + os.environ["OLLAMA_API_KEY"]},
)
with urllib.request.urlopen(req, timeout=60) as fh:
    ids = [m["id"] for m in json.load(fh)["data"]]
wanted = {"glm": "glm-5.2", "kimi": "kimi-k2.6", "deepseek": "deepseek-v4-pro"}
resolved = {}
for slug, prefix in wanted.items():
    match = sorted(m for m in ids if m == prefix or m.startswith(prefix + ":"))
    if not match:
        sys.exit(f"model {prefix} not found in /v1/models: {ids}")
    resolved[slug] = match[0]
with open(os.path.join(live, "models.json"), "w") as fh:
    json.dump(resolved, fh)
print(json.dumps(resolved))
EOF
[ $? -eq 0 ] || { log "MODEL RESOLUTION FAILED"; exit 1; }

model_for() { python3 -c "import json;print(json.load(open('$LIVE/models.json'))['$1'])"; }

run_one() {
  slug="$1"; family="$2"; question="$3"
  model="$(model_for "$slug")"
  export DEEPREASON_HOME="$LIVE/$slug"
  mkdir -p "$DEEPREASON_HOME"
  {
    echo "=== $slug ($model) start $(date -u +%FT%TZ) ==="
    timeout 300 deepreason setup \
      --provider ollama --endpoint https://ollama.com/v1 \
      --model "$model" --model-revision "$model" --family "$family" \
      --context-window-tokens 131072 --maximum-completion-tokens 8192 \
      --credential-env OLLAMA_API_KEY
    echo "setup_rc=$?"
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
    echo "=== $slug end $(date -u +%FT%TZ) ==="
  } >> "$LIVE/$slug.log" 2>&1
}

log "launching glm + kimi + deepseek concurrently"
run_one glm      glm      'When a bounded reasoning run halts because its token budget is exhausted, under what exact conditions can it be resumed later without corrupting the append-only identity of what was already recorded, and when must resumption stay forbidden?' &
P1=$!
run_one kimi     kimi     'If a crashed process leaves a deterministic per-problem workspace occupied without a terminal record, what is the safest reclamation protocol that can never silently displace completed evidence, and what must it durably record?' &
P2=$!
run_one deepseek deepseek 'Should the fetch budget of a replayable autonomous research agent be denominated in requests, bytes, or both, and how must exhaustion be recorded so it remains a typed auditable terminal instead of a silent degradation?' &
P3=$!
wait $P1; wait $P2; wait $P3
log "tri-run done"
{
  echo "tri-run summary $(date -u +%FT%TZ)"
  for slug in glm kimi deepseek; do
    echo "== $slug =="
    grep -E "rc=|seconds|run_id=|state=|tier|passed" "$LIVE/$slug.log" | head -14
  done
} > "$LIVE/summary.txt" 2>&1
