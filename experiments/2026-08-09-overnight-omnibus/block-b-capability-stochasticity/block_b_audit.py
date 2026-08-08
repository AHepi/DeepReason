"""Block B audit: capability-channel funnel per run, from the typed
record only. Walks each proposal's FULL transition history (not just
its current/latest transition) by following previous_transition_ref
backward from current_transition_by_request, so a proposal that was
GRANTED then later FAILED still counts as having reached GRANTED.

Usage: python3 block_b_audit.py ROOT SEED_IDX
"""

import json
import sys
from pathlib import Path

from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.harness import Harness
from deepreason.invariants import verify_root

root = Path(sys.argv[1])
seed_idx = sys.argv[2]
out = {"root": str(root), "seed_idx": seed_idx}

status_json = json.loads((root / "run-status.json").read_text())
out["state"] = status_json.get("state")
out["stop_reason"] = status_json.get("stop_reason")

verdict = verify_root(root)
out["verify_violations"] = [v["check"] for v in verdict["violations"]]
out["replay_valid"] = not verdict["violations"]

harness = Harness(root, read_only=True)
state = harness.capability_state

stages_reached_per_proposal = {}
for proposal_id in state.proposals:
    reached = set()
    ref = state.current_transition_by_request.get(proposal_id)
    seen_refs = set()  # cycle guard; a well-formed chain has none
    while ref is not None and ref not in seen_refs:
        seen_refs.add(ref)
        transition = state.transitions.get(ref)
        if transition is None:
            break
        reached.add(transition.lifecycle.value)
        ref = transition.previous_transition_ref
    stages_reached_per_proposal[proposal_id] = reached

out["proposal_count"] = len(state.proposals)
out["proposal_types"] = sorted({type(p).__name__ for p in state.proposals.values()})

funnel = {}
for stage in CapabilityLifecycle:
    funnel[stage.value] = sum(
        1 for reached in stages_reached_per_proposal.values() if stage.value in reached
    )
out["funnel_all_stages"] = funnel

primary = ["proposed", "validated", "granted", "compiled", "dispatched", "succeeded"]
out["funnel_primary"] = {stage: funnel.get(stage, 0) for stage in primary}
out["reached_succeeded"] = funnel.get("succeeded", 0) > 0
out["reached_compiled_ever"] = funnel.get("compiled", 0) > 0

out["proposals_detail"] = [
    {"proposal_id": pid, "stages_reached": sorted(reached)}
    for pid, reached in stages_reached_per_proposal.items()
]

print(json.dumps(out, indent=2, sort_keys=True))
