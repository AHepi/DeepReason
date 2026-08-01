#!/usr/bin/env bash
# Open-challenge ladder: glm-5.2 on the rank of the 3x3 matrix
# multiplication tensor. R(3,3,3) is unknown — best known 23 since
# Laderman 1976, best proved lower bound 19 — and every candidate answer
# is exactly decidable by checking 729 integer tensor entries.
#
# Every operator-opted capability is ON and the question requires each
# one's TYPED channel:
#   DEEPREASON_SIMULATION_RUNNER=contained  (sandboxed Python, exact verify)
#   DEEPREASON_RESEARCH_ALLOWLIST=en.wikipedia.org
#   DEEPREASON_CONFIG_REFEREE=2
#
# QUALIFICATION IS SKIPPED by reusing the openchallenge home, whose
# provider profile (glm-5.2, context 131072, completion 24576) is
# byte-identical to the one this ladder sets up. Same home + same profile
# + same opt-ins => same qualification subject digest => cache hit in
# about a second instead of the ~14-minute, ~1160-call battery. The
# qualification is real and already completed; it is not bypassed.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a

QUESTION='The attached dossier defines an open problem: the tensor rank of 3x3 matrix multiplication. R(3,3,3) is unknown — the best known construction uses 23 scalar multiplications (Laderman 1976, unbeaten for ~47 years including by large automated searches), the best proved lower bound is 19, and whether 22 is achievable is open. Every candidate answer is exactly decidable in milliseconds by integer arithmetic: a rank-r decomposition is r triples of 3x3 coefficient matrices, and correctness is 729 integer tensor-entry comparisons with no tolerance and no sampling. Work the problem. Conjecture concrete constructions or structural obstructions as rival positions, and where rivals predict different measurable outcomes — a candidate decomposition verifying or not, a symmetry-restricted class being empty or not, an approximate method residual approaching zero without reaching it, a solution existing modulo a small prime but not lifting — file a typed sandboxed Python simulation (simulation_mode sandboxed_python_v1) whose program actually runs the discriminating experiment. A simulation described in prose with an empty simulation_refs channel is an unverified claim and will be criticized as such. Before any verifier verdict is offered as evidence, calibrate it in the sandbox: show it accepts Strassen rank-7 at 2x2 and rejects a corrupted copy. Where the dossier bounds table or its attributions need checking against published knowledge, file typed research proposals for specific https pages on the frozen en.wikipedia.org allowlist; the dossier states its bounds from memory and flags them as unverified. Ground every claim about the problem state in the attached dossier blocks by citing their block ids. Genuine progress in order of ambition: a sandbox-verified 3x3 decomposition with 22 or fewer multiplications; a sandbox-verified structurally novel 23; a simulation-discriminated account of which structural hypothesis best explains the stall at 23; or an exhaustive refutation at a decidable smaller format of a structural lemma proposed here.'

export DEEPREASON_HOME="$LIVE/openchallenge"
export DEEPREASON_RESEARCH_ALLOWLIST="en.wikipedia.org"
export DEEPREASON_SIMULATION_RUNNER="contained"
export DEEPREASON_CONFIG_REFEREE="2"
mkdir -p "$DEEPREASON_HOME"
{
  echo "=== tensorrank ladder start $(date -u +%FT%TZ) ==="
  # completion 24576, not 8192: a hard combinatorial question can spend the
  # whole cap on hidden reasoning and emit nothing (recorded typed failure,
  # openchallenge attempt 1, V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY).
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 24576 \
    --credential-env OLLAMA_API_KEY
  echo "setup_rc=$?"
  q0=$SECONDS
  # Expected to be a cache hit against the existing completed battery.
  timeout 14400 deepreason qualify --yes --json --concurrency 3 --attached-evidence
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  r0=$SECONDS
  timeout 14400 deepreason reason --token-budget 200000 \
    --attach "$LIVE/tensorrank-dossier/TENSOR_RANK_CHALLENGE.md" \
    --attach "$LIVE/tensorrank-dossier/CAPABILITY_CONTRACT.md" \
    --allow-partial \
    "$QUESTION" \
    > "$LIVE/tensorrank-reason.json" 2> "$LIVE/tensorrank-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/tensorrank-reason.json'))['run_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/tensorrank-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id state=$state"
  if [ -n "${run_id:-}" ]; then
    python3 - "$DEEPREASON_HOME" "$run_id" > "$LIVE/tensorrank-audit.json" 2> "$LIVE/tensorrank-audit.err" <<'PYEOF'
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
  echo "=== tensorrank ladder end $(date -u +%FT%TZ) ==="
} >> "$LIVE/tensorrank.log" 2>&1
