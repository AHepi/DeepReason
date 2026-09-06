"""ARM M — mini.flow.isolation.v1 through the managed shallow entry.

PREREG_D8.md §2. Everything is the managed path (`run_shallow_question` with
the STANDARD frozen input) except one thing, disclosed there: the endpoint
factory is replaced with `reasoning_endpoint.endpoint_from_profile`, which
returns the same HttpEndpoint plus the `reasoning: none` request field mini's
transport does not forward (P10). Prints the shallow result JSON, then runs
the five terminal instruments over the root.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "mini"))

import deepreason.shallow as shallow  # noqa: E402
from reasoning_endpoint import endpoint_from_profile  # noqa: E402

CYCLES = 3
TOKEN_BUDGET = 400_000


def main() -> int:
    assert os.environ.get("DEEPREASON_MINI_FLOW") == "mini.flow.isolation.v1", "flow not selected"
    shallow._endpoint = endpoint_from_profile  # the one override, see module docstring
    run_input_root = HERE.parent / "runs" / "input-d8"
    result = shallow.run_shallow_question(
        run_input_root=run_input_root, cycles=CYCLES, token_budget=TOKEN_BUDGET
    )
    out = HERE / "armM"
    out.mkdir(exist_ok=True)
    (out / "ARMM_RESULT.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("ARMM_RESULT", json.dumps(result, indent=1), flush=True)

    from deepreason.invariants import verify_root
    from minireason.log import replay
    from minireason.loop import Session
    from minireason.records import mini_records

    root = shallow._shallow_runs_dir() / result["run_id"]
    session = Session(root)
    report = verify_root(root)
    live = session.state.digest()
    replayed = replay(root).digest()
    kinds = [r.kind for r in mini_records(session)]
    terminal = {
        "schema": "d8-armM-terminal.v1",
        "root": str(root),
        "completed": result["completed"],
        "stop": result["summary"]["stop"],
        "cycles": result["summary"]["cycles"],
        "flow": result["summary"]["flow"],
        "problems": result["summary"]["problems"],
        "refuted": result["summary"]["refuted"],
        "meter_equals_log": result["summary"]["meter_equals_log"],
        "logged_tokens_this_run": result["summary"]["logged_tokens_this_run"],
        "records_by_kind": {k: kinds.count(k) for k in sorted(set(kinds))},
        "events": len(session.state.events),
        "verify_root_violations": len(report["violations"]),
        "verify_root_first": report["violations"][:3],
        "replay_digest_equals_live": replayed == live,
        "digest": live,
    }
    ok = (
        terminal["completed"]
        and terminal["stop"] in ("max-cycles", "queue-exhausted", "budget")
        and terminal["meter_equals_log"]
        and terminal["verify_root_violations"] == 0
        and terminal["replay_digest_equals_live"]
    )
    terminal["TYPED_TERMINAL"] = "COMPLETE" if ok else "FAILED"
    (out / "ARMM_TERMINAL.json").write_text(json.dumps(terminal, indent=1), encoding="utf-8")
    print("ARMM_TERMINAL", json.dumps(terminal, indent=1), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
