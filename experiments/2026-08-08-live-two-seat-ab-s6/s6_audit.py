"""Rung S6 audit: prove (a) work attribution, (b) the stamp matches what
setup bound, (c) verify_root green, (d) continuation preserves bindings
or refuses typed -- from the typed record alone. Model prose is never
evidence here.
"""

import json
import sys
from pathlib import Path

from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.run_manifest import load_run_manifest
from deepreason.seat_events import recorded_seat_bindings, seat_bindings_for_run

root = Path(sys.argv[1])
out = {}

status = json.loads((root / "run-status.json").read_text())
out["state"] = status.get("state")
out["stop_reason"] = status.get("stop_reason")

verdict = verify_root(root)
out["verify_violations"] = [v["check"] for v in verdict["violations"]]
out["replay_valid"] = not verdict["violations"]

harness = Harness(root, read_only=True)
manifest = load_run_manifest(root / "run-manifest.json")

# (b) the seat stamp matches what setup bound.
stamps = recorded_seat_bindings(harness)
out["seat_bindings_stamp_count"] = len(stamps)
out["seat_bindings_stamps"] = [
    {
        "digest": s.digest,
        "bindings": [
            {"group": b.group, "provider": b.provider, "model_id": b.model_id}
            for b in s.bindings
        ],
    }
    for s in stamps
]
projected = seat_bindings_for_run(harness, manifest)
out["seat_bindings_for_run"] = [
    {"group": b.group, "provider": b.provider, "model_id": b.model_id}
    for b in projected
]

# (a) which seat produced every attempt -- group every LLM call by role,
# list the distinct models each role actually dispatched to.
events = list(harness.log.read())
by_role = {}
for event in events:
    call = event.llm
    if call is None:
        continue
    by_role.setdefault(call.role, set()).add(call.model)
out["llm_calls_by_role"] = {
    role: sorted(models) for role, models in sorted(by_role.items())
}
out["llm_call_count"] = sum(1 for e in events if e.llm is not None)
out["property_designer_calls"] = len(by_role.get("property_designer", ()))

# Cross-check: every role NOT bound to "coder" should show only the
# default (glm-5.2) model; property_designer (the coder group's sole
# role) should show only gemma4:31b, if it fired at all.
mismatches = []
for role, models in by_role.items():
    expected = {"gemma4:31b"} if role == "property_designer" else {"glm-5.2"}
    if models != expected:
        mismatches.append({"role": role, "expected": sorted(expected), "actual": sorted(models)})
out["attribution_mismatches"] = mismatches
out["attribution_clean"] = not mismatches

out["events"] = len(events)
out["artifacts"] = len(harness.state.artifacts)
out["att_edges"] = len(harness.state.att)

print(json.dumps(out, indent=2, sort_keys=True))
