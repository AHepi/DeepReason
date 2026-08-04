"""Compare the two rung-5 arms on TYPED outcomes only.

Model prose is never evidence here: this reads run state, stop reason,
verify_root's verdict, the recorded module fingerprint, and counts derived
from the append-only log.
"""

import json
import sys
from pathlib import Path

from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.module_events import recorded_module_fingerprints

live = Path(sys.argv[1])
out = {}

for arm, home in (("default", "ab-home"), ("roundrobin", "rr-home")):
    summary = {}
    payload_path = live / f"{arm}-reason.json"
    try:
        payload = json.loads(payload_path.read_text())
    except Exception as error:
        out[arm] = {"error": f"{type(error).__name__}: {error}"}
        continue
    run_id = payload.get("run_id")
    summary["run_id"] = run_id
    summary["state"] = payload.get("state")
    summary["stop_reason"] = payload.get("stop_reason")
    root = live / home / "runs" / str(run_id)
    summary["root_exists"] = root.exists()
    if not root.exists():
        out[arm] = summary
        continue

    harness = Harness(root, read_only=True)
    events = list(harness.log.read())
    stamps = recorded_module_fingerprints(harness)
    summary["module_backend"] = (
        stamps[0].modules[0].module_id if stamps else None
    )
    summary["events"] = len(events)
    summary["llm_calls"] = sum(1 for e in events if e.llm is not None)
    summary["artifacts"] = len(harness.state.artifacts)
    summary["problems"] = len(harness.state.problems)
    summary["att_edges"] = len(harness.state.att)
    schools_seen = {
        a.provenance.school
        for a in harness.state.artifacts.values()
        if a.provenance.school
    }
    summary["schools_with_artifacts"] = sorted(s for s in schools_seen if s)
    verdict = verify_root(root)
    summary["verify_violations"] = [v["check"] for v in verdict["violations"]]
    summary["replay_valid"] = not verdict["violations"]
    out[arm] = summary

both = [out.get(a, {}) for a in ("default", "roundrobin")]
if all(b.get("root_exists") for b in both):
    out["comparison"] = {
        "backends_differ": both[0].get("module_backend")
        != both[1].get("module_backend"),
        "both_replay_valid": all(b.get("replay_valid") for b in both),
        "event_delta": both[1].get("events", 0) - both[0].get("events", 0),
        "llm_call_delta": both[1].get("llm_calls", 0) - both[0].get("llm_calls", 0),
        "artifact_delta": both[1].get("artifacts", 0) - both[0].get("artifacts", 0),
    }
print(json.dumps(out, indent=2, sort_keys=True))
