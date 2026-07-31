#!/usr/bin/env bash
# Ladder: glm-5.2 inventing a runtime jolt to escape its own attractors.
#
# Two credentials are in play and they are deliberately kept apart:
#
#   probe.env   the operator's DEDICATED key, used ONLY by probe.py, the fixed
#               harness-side driver that measured glm-5.2's collapse. It is
#               gitignored and is not exported into the reasoning run.
#   ../live_research_2026-07-29/env   the standing key that drives the harness.
#
# The model under study never authors code that holds a credential or opens a
# socket. `sandboxed_python_v1` runs under `unshare --net` and the backend
# fails closed without that namespace, which is the only reason executing
# model-authored Python is safe here. Rather than remove it, the live calls
# were made in advance and the RESULTS are attached as evidence.
#
# Allowlist adds ollama.com so the model can check which runtime knobs the
# provider actually documents; a mechanism resting on a knob the API does not
# expose is not implementable.
#
# Thinking is OFF per the binding rule (R4/R5). Note the tension worth reading
# in the result: the model is asked to reason about decoder-level interventions
# while its own reasoning channel is disabled.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/../live_research_2026-07-29/env"; set +a

QUESTION="$(cat "$LIVE/QUESTION.txt")

Work this problem under the attached capability contract. Requirements 2 and 3 are claims about the attached measurements, so file typed sandboxed Python simulations (simulation_mode sandboxed_python_v1) that carry the specific cells into the program text and RETURN the per-task numbers your claim rests on — never a mean across tasks and never a boolean. The measurements are attached as a document, not sealed into the simulation input catalog, so transcribe only the figures your claim actually needs. For requirement 3, diversity is trivially purchasable by raising temperature until the model stops being right: return a statistic that separates leaving an attractor from degrading, and state what it assumes rather than presenting it as neutral. For requirement 4, use the scratch channel to carry provisional mechanisms and link them to the simulations that bear on them; a mechanism assembled to fit these six tasks and nine jolts is worth little, so make a prediction about a condition NOT in the data and say how it would be checked. Where the provider's documented knobs would settle whether your mechanism is implementable at all, file typed research proposals for specific https pages on the frozen allowlist, and treat what you fetch as evidence about what is documented rather than what is true — where it disagrees with the measurements, the measurements win and the disagreement is itself a finding. Genuine progress in order of ambition: a mechanism that is structural rather than surface and says why it escapes the echo-in-a-new-voice failure this codebase already recorded; a measured separation of diversity from degradation that does not presuppose its own answer; a refutation of one of the nine measured jolts on specific tasks; or an honest account of which collapses moved and which did not, with the sample-size limits stated."

export DEEPREASON_HOME="$LIVE/home"
export DEEPREASON_RESEARCH_ALLOWLIST="en.wikipedia.org,ollama.com"
export DEEPREASON_SIMULATION_RUNNER="contained"
export DEEPREASON_CONFIG_REFEREE="2"
mkdir -p "$DEEPREASON_HOME"
{
  echo "=== jolt ladder start $(date -u +%FT%TZ) ==="
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 24576 \
    --credential-env OLLAMA_API_KEY --reasoning none
  echo "setup_rc=$?"
  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 4 --attached-evidence \
    > "$LIVE/jolt-qual.json" 2> "$LIVE/jolt-qual.err"
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  r0=$SECONDS
  # 200000 is the fixed V6 policy ceiling; anything above is refused at
  # preparation, before any provider call.
  timeout 21600 deepreason reason --token-budget 200000 \
    --attach "$LIVE/dossier/SCHOOLS_MECHANISM.md" \
    --attach "$LIVE/dossier/CAPABILITY_CONTRACT.md" \
    --attach "$LIVE/dossier/JOLT_MEASUREMENTS.md" \
    --allow-partial \
    "$QUESTION" \
    > "$LIVE/jolt-reason.json" 2> "$LIVE/jolt-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/jolt-reason.json'))['run_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/jolt-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id state=$state"
  if [ -n "${run_id:-}" ]; then
    python3 - "$DEEPREASON_HOME" "$run_id" > "$LIVE/jolt-audit.json" 2> "$LIVE/jolt-audit.err" <<'PYEOF'
import json, sys
from pathlib import Path
from deepreason.harness import Harness
from deepreason.invariants import verify_root

home, run_id = sys.argv[1], sys.argv[2]
root = Path(home) / "runs" / run_id
harness = Harness(root, read_only=True)
out = {"critiques": [], "research": [], "simulation": [], "scratch": [], "cycles": []}
for event in harness.log.read():
    if not event.inputs:
        continue
    s = str(event.inputs[0])
    row = {"seq": event.seq, "inputs": [str(v)[:110] for v in event.inputs]}
    if s.startswith("config-critique:"):
        out["critiques"].append(row)
    elif s.startswith("research-fetch:") or s.startswith("research-allowance:"):
        out["research"].append(row)
    elif s.startswith("scratch"):
        out["scratch"].append(row)
    elif s == "cycle":
        out["cycles"].append(row)
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
  echo "=== jolt ladder end $(date -u +%FT%TZ) ==="
} >> "$LIVE/jolt.log" 2>&1
