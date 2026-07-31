#!/usr/bin/env bash
# Ladder: glm-5.2 on deciding canonicity of a coin system.
#
# The question is the one put to the provider natively in QUESTION.txt,
# verbatim, plus the capability framing this harness adds. The dossier
# states definitions and rules of evidence ONLY — no bounds, no example
# systems, no prior results — so the harness runs on the same knowledge
# the native call had, and only the process differs.
#
# Every operator-opted capability is ON:
#   DEEPREASON_SIMULATION_RUNNER=contained  (sandboxed Python, exact)
#   DEEPREASON_RESEARCH_ALLOWLIST=en.wikipedia.org
#   DEEPREASON_CONFIG_REFEREE=2
#
# The home is seeded with the openchallenge provider profile and
# qualification cache. Same profile + same opt-ins => same qualification
# subject digest => cache hit in about a second instead of the ~14-minute,
# ~1160-call battery. The qualification is real and already completed.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/../live_research_2026-07-29/env"; set +a

QUESTION="$(cat "$LIVE/QUESTION.txt")

Work this problem under the attached capability contract. The bound in requirement 2 is the mathematical content and it is exactly the kind of claim this run can refute rather than assert: any candidate bound W(C) is a universal claim over coin systems, and a single enumerated system whose smallest counterexample exceeds W(C) refutes it outright. Before relying on ANY bound — including one you are confident of, and including one recovered from published knowledge — file a typed sandboxed Python simulation (simulation_mode sandboxed_python_v1) that enumerates small coin systems, decides each by brute-force dynamic programming, and RETURNS the systems that violate the candidate bound together with their smallest counterexamples. Calibrate the brute-force oracle in the same channel before its verdicts are used: show it finds a counterexample for at least one system and none for another, and return both. A simulation described in prose with an empty simulation_refs channel is an unverified claim and will be criticized as such. Where published bounds or complexity results would settle a live disagreement, file typed research proposals for specific https pages on the frozen en.wikipedia.org allowlist; treat what is fetched as evidence about what is published, not as established truth, and put it through the simulation channel too. Genuine progress in order of ambition: a decision procedure polynomial in n alone, stated precisely and differentially tested against the oracle with the disagreements returned; a proved and simulation-survived search bound with a pseudo-polynomial procedure built on it; a refutation, by enumerated counterexample, of a bound that looks right; or a measured account of where smallest counterexamples actually sit across the enumerated space."

export DEEPREASON_HOME="$LIVE/home"
export DEEPREASON_RESEARCH_ALLOWLIST="en.wikipedia.org"
export DEEPREASON_SIMULATION_RUNNER="contained"
export DEEPREASON_CONFIG_REFEREE="2"
mkdir -p "$DEEPREASON_HOME"
{
  echo "=== coin ladder start $(date -u +%FT%TZ) ==="
  # completion 24576, not 8192: glm-5.2 is a reasoning model and a hard
  # question can spend the whole cap on hidden reasoning and emit nothing
  # (recorded typed failure, V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY).
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
    --attach "$LIVE/dossier/COIN_CANONICITY_CHALLENGE.md" \
    --attach "$LIVE/dossier/CAPABILITY_CONTRACT.md" \
    --allow-partial \
    "$QUESTION" \
    > "$LIVE/coin-reason.json" 2> "$LIVE/coin-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/coin-reason.json'))['run_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/coin-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id state=$state"
  if [ -n "${run_id:-}" ]; then
    python3 - "$DEEPREASON_HOME" "$run_id" > "$LIVE/coin-audit.json" 2> "$LIVE/coin-audit.err" <<'PYEOF'
import json, sys
from pathlib import Path
from deepreason.harness import Harness
from deepreason.invariants import verify_root

home, run_id = sys.argv[1], sys.argv[2]
root = Path(home) / "runs" / run_id
harness = Harness(root, read_only=True)
out = {"critiques": [], "referee_transactions": [], "research": [], "simulation": [],
       "citations": [], "cycles": []}
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
        "request": getattr(proposal, "request_identifier", None),
        "observables": list(getattr(proposal, "requested_observables", ()) or ()),
        "lifecycle": transition.lifecycle.value if transition else None,
        "reason": transition.reason_code if transition else None,
    })
validation = verify_root(root)
out["replay_valid"] = validation.get("valid")
out["replay_violations"] = validation.get("violations", ["<missing>"])[:8]
print(json.dumps(out, indent=2))
PYEOF
    echo "audit_rc=$?"
  fi
  echo "=== coin ladder end $(date -u +%FT%TZ) ==="
} >> "$LIVE/coin.log" 2>&1
