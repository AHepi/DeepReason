#!/usr/bin/env bash
# Ladder: glm-5.2 on generalized ant automata (turmites).
#
# The question actively requires all four channels. It cannot be answered by
# recall or manipulation: the object is an infinite trajectory of a machine
# defined by a formal grammar, so the model must PARSE the rule-string
# grammar, implement the operational semantics in CODE, run it in the typed
# SIMULATION channel to learn anything at all, and use SCRATCH to carry the
# provisional mechanism that requirement 3 asks for.
#
# Thinking is OFF, per the binding rule (R4/R5): `--reasoning none`. The CLI
# refuses to launch otherwise when the provider exposes the knob.
#
# The home is FRESH and never reused. The qualification subject digest covers
# the manifest, pair inventory and provider profile but NOT the rendered
# schema bytes, so a seeded home would cache-hit and certify the contracts as
# they were BEFORE the schema sweep. This battery is therefore also the
# operator's R11 acceptance test for glm-5.2 with thinking off: before the
# sweep, scratch.link.compact.v1 scored 11/20 then 9/20 and dropped the whole
# engine to `shallow`.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/../live_research_2026-07-29/env"; set +a

QUESTION="$(cat "$LIVE/QUESTION.txt")

Work this problem under the attached capability contract. Requirement 1 is a universal claim over rule strings and is therefore refutable by a single established counterexample — file a typed sandboxed Python simulation (simulation_mode sandboxed_python_v1) that parses the rule strings, implements the dossier's exact turn/advance/move order, runs each to a long horizon, and RETURNS the rule strings showing no highway together with the evidence, not a boolean. Before any trajectory output is used as evidence, calibrate the implementation in the same channel: return a short trace of (position, facing, cell state) triples from which the specified order can be read off directly, and return a rule string for which a highway IS found with its period and displacement, so the detector is shown to be capable of firing. A simulation described in prose with an empty simulation_refs channel is an unverified claim and will be criticized as such. For requirement 2, a highway must be established on the CONFIGURATION, not the position: return the verification that the configuration at step s+(j+1)P equals the one at s+jP translated by d, over many j. For requirement 3, use the scratch channel to carry provisional mechanisms and link them to the simulations that bear on them; a mechanism that survives only the cases it was built from is worth little, so make a checkable prediction about a length you have not tested and then test it. Where published results would settle a live disagreement, file typed research proposals for specific https pages on the frozen en.wikipedia.org allowlist, and put what you fetch through the simulation channel rather than trusting it. Genuine progress in order of ambition: a structural invariant that PROVES some rule string never builds a highway; a mechanism that predicts highway formation and survives a test on rule strings it was not derived from; an established refutation of CLAIM H; or a measured account of transient lengths and periods across the enumerated space with the horizon dependence stated honestly."

export DEEPREASON_HOME="$LIVE/home"
export DEEPREASON_RESEARCH_ALLOWLIST="en.wikipedia.org"
export DEEPREASON_SIMULATION_RUNNER="contained"
export DEEPREASON_CONFIG_REFEREE="2"
mkdir -p "$DEEPREASON_HOME"
{
  echo "=== turmite ladder start $(date -u +%FT%TZ) ==="
  # completion 24576: a hard question can otherwise spend the whole cap and
  # emit nothing (recorded typed failure, V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY).
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 24576 \
    --credential-env OLLAMA_API_KEY --reasoning none
  echo "setup_rc=$?"
  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 4 --attached-evidence \
    > "$LIVE/turmite-qual.json" 2> "$LIVE/turmite-qual.err"
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  r0=$SECONDS
  timeout 21600 deepreason reason --token-budget 260000 \
    --attach "$LIVE/dossier/TURMITE_CHALLENGE.md" \
    --attach "$LIVE/dossier/CAPABILITY_CONTRACT.md" \
    --allow-partial \
    "$QUESTION" \
    > "$LIVE/turmite-reason.json" 2> "$LIVE/turmite-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/turmite-reason.json'))['run_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/turmite-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id state=$state"
  if [ -n "${run_id:-}" ]; then
    python3 - "$DEEPREASON_HOME" "$run_id" > "$LIVE/turmite-audit.json" 2> "$LIVE/turmite-audit.err" <<'PYEOF'
import json, sys
from pathlib import Path
from deepreason.harness import Harness
from deepreason.invariants import verify_root

home, run_id = sys.argv[1], sys.argv[2]
root = Path(home) / "runs" / run_id
harness = Harness(root, read_only=True)
out = {"critiques": [], "referee_transactions": [], "research": [], "simulation": [],
       "scratch": [], "citations": [], "cycles": []}
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
    elif s.startswith("scratch"):
        out["scratch"].append(row)
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
  echo "=== turmite ladder end $(date -u +%FT%TZ) ==="
} >> "$LIVE/turmite.log" 2>&1
