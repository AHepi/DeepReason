#!/usr/bin/env bash
# Self-study ladder: glm-5.2 examines DeepReason's own school system and
# criticism mechanism, framed as a combined simulation + coding + research
# challenge, with the full mechanism documentation attached as admitted
# evidence (exercising the document parser end to end).
#
# All three operator-opted capabilities are ON, so this is a fresh
# qualification behavior subject:
#   DEEPREASON_SIMULATION_RUNNER=contained  (sandboxed Python, contained runner)
#   DEEPREASON_RESEARCH_ALLOWLIST=en.wikipedia.org
#   DEEPREASON_CONFIG_REFEREE=2
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
REPO="$(cd "$LIVE/../.." && pwd)"

QUESTION='The attached documentation specifies DeepReason'\''s school system (conditioning-only schools sharing frozen provider seats) and its criticism mechanism (foreign-school argumentative criticism with per-target warrants, coverage debt, batch criticism, criticism-weighted attention). Treat this as a combined simulation, coding, and research challenge: identify concrete weaknesses in how schools generate rival positions and how criticism retires them — in live runs rivalry has grown from 18 to roughly 60 accepted rival positions while criticism retired almost none — and propose specific, criticizable optimisations. Where a claim about coverage or retirement dynamics can be tested numerically, propose a sandboxed Python simulation (simulation_mode sandboxed_python_v1) that discriminates between rival predictions, for example about how coverage debt grows with rivalry size under batched criticism. Where published work bears on the design, propose directed research fetches of specific https pages; this run'\''s frozen allowlist permits only en.wikipedia.org (ensemble methods, peer review, Popperian critical rationalism are all in scope). Ground every claim about the current mechanism in the attached evidence blocks by citing their block ids.'

export DEEPREASON_HOME="$LIVE/selfstudy"
export DEEPREASON_RESEARCH_ALLOWLIST="en.wikipedia.org"
export DEEPREASON_SIMULATION_RUNNER="contained"
export DEEPREASON_CONFIG_REFEREE="2"
mkdir -p "$DEEPREASON_HOME"
{
  echo "=== selfstudy ladder start $(date -u +%FT%TZ) ==="
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 8192 \
    --credential-env OLLAMA_API_KEY
  echo "setup_rc=$?"
  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3 --attached-evidence
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  r0=$SECONDS
  timeout 14400 deepreason reason --token-budget 200000 \
    --attach "$REPO/docs/harness-spec-v1.3.md" \
    --attach "$REPO/docs/harness-spec-v1.5-amendment.md" \
    --attach "$REPO/docs/STATE_OF_THE_THEORY.md" \
    --attach "$REPO/docs/TOKEN_ECONOMY.md" \
    --attach "$REPO/docs/BASIN_REPORT.md" \
    --allow-partial \
    "$QUESTION" \
    > "$LIVE/selfstudy-reason.json" 2> "$LIVE/selfstudy-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/selfstudy-reason.json'))['run_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/selfstudy-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id state=$state"
  if [ -n "${run_id:-}" ]; then
    python3 - "$DEEPREASON_HOME" "$run_id" > "$LIVE/selfstudy-audit.json" 2> "$LIVE/selfstudy-audit.err" <<'PYEOF'
import json, sys
from pathlib import Path
from deepreason.harness import Harness
from deepreason.invariants import verify_root

home, run_id = sys.argv[1], sys.argv[2]
root = Path(home) / "runs" / run_id
harness = Harness(root, read_only=True)
out = {"critiques": [], "referee_transactions": [], "research": [], "simulation": [],
       "citations": [], "dossier_blocks": None}
for event in harness.log.read():
    if not event.inputs:
        continue
    s = str(event.inputs[0])
    row = {"seq": event.seq, "inputs": [str(v)[:110] for v in event.inputs]}
    if s.startswith("config-critique:"):
        out["critiques"].append(row)
    elif s.startswith("research-fetch:") or s.startswith("research-allowance:"):
        out["research"].append(row)
    elif s.startswith("evidence-citation:"):
        out["citations"].append(row)
for item in harness.workflow_state.transaction_work.values():
    if item.preparation.contract_id == "config-referee.v1":
        out["referee_transactions"].append({
            "status": item.terminal.status if item.terminal else None,
            "reason": item.terminal.reason_code if item.terminal else None,
        })
state = harness.capability_state
for proposal in state.proposals.values():
    ref = state.current_transition_by_request.get(proposal.id)
    transition = state.transitions[ref] if ref else None
    out["simulation"].append({
        "mode": getattr(proposal, "simulation_mode", None),
        "kind": type(proposal).__name__,
        "lifecycle": transition.lifecycle.value if transition else None,
        "reason": transition.reason_code if transition else None,
    })
try:
    from deepreason.evidence import load_evidence_dossier
    dossier = load_evidence_dossier(root)
    out["dossier_blocks"] = {
        "sources": len(dossier.sources),
        "total_bytes": dossier.total_byte_count,
    }
except Exception as error:
    out["dossier_blocks"] = f"unavailable: {type(error).__name__}"
validation = verify_root(root)
out["replay_violations"] = validation.get("violations", ["<missing>"])[:6]
print(json.dumps(out, indent=2))
PYEOF
    echo "audit_rc=$?"
  fi
  echo "=== selfstudy ladder end $(date -u +%FT%TZ) ==="
} >> "$LIVE/selfstudy.log" 2>&1
