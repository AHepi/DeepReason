#!/usr/bin/env bash
# Config-referee live proof, attempt 2 (after the budget-denial fix).
# Same home (qualification cache hit) with a minimally varied question so the
# deterministic run root is fresh.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a

QUESTION='Deterministic replay in an append-only reasoning system depends on retried operations being safe to repeat. Drawing on published definitions, what exactly distinguishes an idempotent operation from a safe one, and which of the two properties must an append-only event log actually require of its writers to survive at-least-once delivery? You may propose directed research fetches of specific https pages; this run'\''s frozen domain allowlist permits only docs.python.org. Fetched pages become citable evidence blocks.'

export DEEPREASON_HOME="$LIVE/referee"
export DEEPREASON_RESEARCH_ALLOWLIST="docs.python.org"
export DEEPREASON_CONFIG_REFEREE="2"
{
  echo "=== referee ladder 2 start $(date -u +%FT%TZ) ==="
  r0=$SECONDS
  timeout 14400 deepreason reason "$QUESTION" \
    > "$LIVE/referee2-reason.json" 2> "$LIVE/referee2-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/referee2-reason.json'))['run_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/referee2-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id state=$state"
  if [ -n "${run_id:-}" ]; then
    python3 - "$DEEPREASON_HOME" "$run_id" > "$LIVE/referee2-critique-audit.json" 2> "$LIVE/referee2-critique-audit.err" <<'PYEOF'
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
    "replay_violations": validation.get("violations", ["<missing>"])[:5],
}, indent=2))
PYEOF
    echo "critique_audit_rc=$?"
  fi
  echo "=== referee ladder 2 end $(date -u +%FT%TZ) ==="
} >> "$LIVE/referee.log" 2>&1
