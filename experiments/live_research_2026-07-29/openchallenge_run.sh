#!/usr/bin/env bash
# Open-challenge ladder: glm-5.2 works a genuinely unsolved programming
# problem — the minimal 13-input sorting network, S(13) unknown, best
# known 45 comparators — with every operator-opted capability ON and a
# question that requires each one's TYPED channel:
#   DEEPREASON_SIMULATION_RUNNER=contained  (sandboxed Python, 0-1 verify)
#   DEEPREASON_RESEARCH_ALLOWLIST=en.wikipedia.org
#   DEEPREASON_CONFIG_REFEREE=2
# Fresh DEEPREASON_HOME => fresh qualification subject (full battery).
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a

QUESTION='The attached dossier defines the open problem of the minimal 13-input sorting network: S(13) is unknown, the best known network has 45 comparators, Batcher'\''s construction gives 48, and every candidate is exactly checkable in milliseconds by the 0-1 principle (8192 binary vectors). Work the problem. Conjecture concrete search or construction strategies as rival positions, and where rivals predict different measurable outcomes — a candidate network sorting or not, a pruning rule preserving optimality at small n, one strategy reaching smaller networks than another under a fixed budget — file a typed sandboxed Python simulation (simulation_mode sandboxed_python_v1) whose program actually runs the discriminating experiment; a simulation described in prose with an empty simulation_refs channel is an unverified claim and will be criticized as such. Where the dossier'\''s bounds table or method claims need checking against published knowledge, file typed research proposals for specific https pages on the frozen en.wikipedia.org allowlist. Ground every claim about the problem state in the attached dossier blocks by citing their block ids. Genuine progress in order of ambition: a verified 13-input network of 44 or fewer comparators; a structurally novel verified 45; or a simulation-discriminated account of which structural hypothesis best explains why search stalls at 45.'

export DEEPREASON_HOME="$LIVE/openchallenge"
export DEEPREASON_RESEARCH_ALLOWLIST="en.wikipedia.org"
export DEEPREASON_SIMULATION_RUNNER="contained"
export DEEPREASON_CONFIG_REFEREE="2"
mkdir -p "$DEEPREASON_HOME"
{
  echo "=== openchallenge ladder start $(date -u +%FT%TZ) ==="
  # 24576 completion tokens, not the 8192 used elsewhere: attempt 1 failed
  # typed (V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY) because glm-5.2 spent the
  # entire 8192 cap on hidden reasoning about the combinatorial problem and
  # emitted zero text; three attempts show completion=8192 with empty
  # output. A harder question needs a deeper completion budget.
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 24576 \
    --credential-env OLLAMA_API_KEY
  echo "setup_rc=$?"
  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3 --attached-evidence
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  r0=$SECONDS
  timeout 14400 deepreason reason --token-budget 200000 \
    --attach "$LIVE/openchallenge-dossier/SORTING_NETWORK_CHALLENGE.md" \
    --attach "$LIVE/openchallenge-dossier/CAPABILITY_CONTRACT.md" \
    --allow-partial \
    "$QUESTION" \
    > "$LIVE/openchallenge-reason.json" 2> "$LIVE/openchallenge-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/openchallenge-reason.json'))['run_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/openchallenge-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id state=$state"
  if [ -n "${run_id:-}" ]; then
    python3 - "$DEEPREASON_HOME" "$run_id" > "$LIVE/openchallenge-audit.json" 2> "$LIVE/openchallenge-audit.err" <<'PYEOF'
import json, sys
from pathlib import Path
from deepreason.harness import Harness
from deepreason.invariants import verify_root

home, run_id = sys.argv[1], sys.argv[2]
root = Path(home) / "runs" / run_id
harness = Harness(root, read_only=True)
out = {"critiques": [], "referee_transactions": [], "research": [], "simulation": [],
       "citations": [], "cycles": [], "dossier_blocks": None}
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
    elif s == "cycle":
        out["cycles"].append(row)
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
out["replay_valid"] = validation.get("valid")
out["replay_violations"] = validation.get("violations", ["<missing>"])[:8]
print(json.dumps(out, indent=2))
PYEOF
    echo "audit_rc=$?"
  fi
  echo "=== openchallenge ladder end $(date -u +%FT%TZ) ==="
} >> "$LIVE/openchallenge.log" 2>&1
