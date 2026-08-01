#!/usr/bin/env bash
# Live config-referee proof: one fresh ladder identical to the narrow research
# run except DEEPREASON_CONFIG_REFEREE=2 — the referee reviews the dynamic
# config every 2 scheduler cycles as an ordinary critic transaction under the
# frozen config-referee.v1 contract. Enabling the referee changes the compiled
# manifest, so this is a distinct qualification behavior subject and the
# ladder requalifies from scratch.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a

QUESTION='Deterministic replay in an append-only reasoning system depends on retried operations being safe to repeat. Drawing on published definitions, what precisely distinguishes an idempotent operation from a safe one, and which of the two properties does an append-only event log actually require of its writers to survive at-least-once delivery? You may propose directed research fetches of specific https pages; this run'\''s frozen domain allowlist permits only docs.python.org. Fetched pages become citable evidence blocks.'

export DEEPREASON_HOME="$LIVE/referee"
export DEEPREASON_RESEARCH_ALLOWLIST="docs.python.org"
export DEEPREASON_CONFIG_REFEREE="2"
mkdir -p "$DEEPREASON_HOME"
{
  echo "=== referee ladder (glm-5.2, cadence=2) start $(date -u +%FT%TZ) ==="
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
  timeout 14400 deepreason reason "$QUESTION" \
    > "$LIVE/referee-reason.json" 2> "$LIVE/referee-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/referee-reason.json'))['run_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/referee-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id state=$state"
  if [ -n "${run_id:-}" ]; then
    python3 - "$DEEPREASON_HOME" "$run_id" > "$LIVE/referee-critique-audit.json" 2> "$LIVE/referee-critique-audit.err" <<'PYEOF'
import json, sys
from pathlib import Path
from deepreason.harness import Harness
from deepreason.invariants import verify_root

home, run_id = sys.argv[1], sys.argv[2]
root = Path(home) / "runs" / run_id
harness = Harness(root, read_only=True)
critiques = []
referee_work = []
for event in harness.log.read():
    if event.inputs and str(event.inputs[0]).startswith("config-critique:"):
        critiques.append({"seq": event.seq, "inputs": [str(v) for v in event.inputs]})
for item in harness.workflow_state.transaction_work.values():
    if item.preparation.contract_id == "config-referee.v1":
        referee_work.append({
            "work_id": item.preparation.id,
            "status": item.terminal.status if item.terminal else None,
            "reason": item.terminal.reason_code if item.terminal else None,
        })
validation = verify_root(root)
print(json.dumps({
    "critiques": critiques,
    "referee_transactions": referee_work,
    "replay_valid": validation["valid"],
    "violations": validation["violations"][:5],
}, indent=2))
PYEOF
    echo "critique_audit_rc=$?"
  fi
  echo "=== referee ladder end $(date -u +%FT%TZ) ==="
} >> "$LIVE/referee.log" 2>&1
