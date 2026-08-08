"""Per-root audit for the corpus-enrichment pilot's Phase 1 runs.
Same shape as S6's s6_audit.py (typed record only, model prose is never
evidence) plus one addition: a candidate-checker commitment count, since
this pilot's own prereg treats "zero candidate-checker commitments" as
the expected, reported outcome (v7 is registration-only, P-CEPP-1; the
encoder role has zero callers regardless, additional_finding in prereg).
"""

import json
import sys
from pathlib import Path

from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.run_manifest import load_run_manifest
from deepreason.seat_events import recorded_seat_bindings, seat_bindings_for_run

root = Path(sys.argv[1])
out = {"root": str(root)}

status = json.loads((root / "run-status.json").read_text())
out["state"] = status.get("state")
out["stop_reason"] = status.get("stop_reason")

verdict = verify_root(root)
out["verify_violations"] = [v["check"] for v in verdict["violations"]]
out["replay_valid"] = not verdict["violations"]

harness = Harness(root, read_only=True)
manifest = load_run_manifest(root / "run-manifest.json")

out["conjecturer_turn_contract"] = (
    manifest.control_plane_policy.contract_versions.conjecturer_turn_contract
)

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

events = list(harness.log.read())
by_role = {}
for event in events:
    call = event.llm
    if call is None:
        continue
    by_role.setdefault(call.role, set()).add(call.model)
out["llm_calls_by_role"] = {role: sorted(models) for role, models in sorted(by_role.items())}
out["llm_call_count"] = sum(1 for e in events if e.llm is not None)
out["property_designer_calls"] = len(by_role.get("property_designer", ()))
out["encoder_calls"] = len(by_role.get("encoder", ()))

# Candidate-checker commitment count: any commitment whose eval kind is
# the new dual-mode kind. Zero is the prereg's expected value.
candidate_checker_count = sum(
    1 for c in harness.commitments.values() if c.eval == "program:candidate_checker"
)
out["candidate_checker_commitment_count"] = candidate_checker_count

out["events"] = len(events)
out["artifacts"] = len(harness.state.artifacts)
out["att_edges"] = len(harness.state.att)
out["accepted_artifacts"] = sum(1 for s in harness.state.status.values() if s.value == "accepted")

print(json.dumps(out, indent=2, sort_keys=True))
