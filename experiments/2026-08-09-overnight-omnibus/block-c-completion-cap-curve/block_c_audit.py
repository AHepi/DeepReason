"""Block C audit: typed seat-failure, empty-emission rate,
qualification tier, run survival -- all from the typed record only.

Usage: python3 block_c_audit.py ROOT CAP SEED_IDX QUALIFY_JSON_PATH
"""

import json
import sys
from pathlib import Path

from deepreason.harness import Harness
from deepreason.invariants import verify_root

root = Path(sys.argv[1])
cap = sys.argv[2]
seed_idx = sys.argv[3]
qualify_json_path = Path(sys.argv[4])
out = {"root": str(root), "cap": cap, "seed_idx": seed_idx}

status_json = json.loads((root / "run-status.json").read_text())
out["state"] = status_json.get("state")
out["stop_reason"] = status_json.get("stop_reason")

verdict = verify_root(root)
out["verify_violations"] = [v["check"] for v in verdict["violations"]]
out["replay_valid"] = not verdict["violations"]

harness = Harness(root, read_only=True)
events = list(harness.log.read())

# -- typed seat failure: V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY --
insufficient = getattr(harness.workflow_state, "insufficient_capability_by_route_seat", None)
out["insufficient_capability_by_route_seat"] = sorted(insufficient) if insufficient else []
out["typed_seat_failure"] = bool(insufficient)

# -- empty-emission: LLM calls that spent their completion-token cap (truncated) --
llm_calls = [e.llm for e in events if e.llm is not None]
truncated_calls = [c for c in llm_calls if c.truncated]
out["llm_call_count"] = len(llm_calls)
out["truncated_call_count"] = len(truncated_calls)
out["empty_emission_rate"] = (len(truncated_calls) / len(llm_calls)) if llm_calls else None
out["truncated_calls_by_role"] = sorted({c.role for c in truncated_calls})

# -- qualification tier reached (from the qualify --json output written by the ladder) --
try:
    qualify_out = json.loads(qualify_json_path.read_text())
    out["qualification_state"] = qualify_out.get("qualification_state")
except Exception as exc:  # noqa: BLE001 -- report, don't crash the audit
    out["qualification_state"] = None
    out["qualification_read_error"] = str(exc)

# -- run survival stats --
out["events_total"] = len(events)
out["artifact_total"] = len(harness.state.artifacts)

print(json.dumps(out, indent=2, sort_keys=True))
