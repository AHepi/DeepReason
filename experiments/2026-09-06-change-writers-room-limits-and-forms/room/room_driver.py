"""The live writer's-room run. PREREG_CENSUS.md.

The managed shallow entry with the STANDARD frozen input the D8 measure
used, `mini.flow.room.v1` selected by DEEPREASON_MINI_FLOW, and the one
disclosed override the predecessor's ARM M ran through: the endpoint
subclass that adds `reasoning: none` (P10, still parked). Prints the shallow
result and the five terminal instruments, then the census.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "mini"))

import deepreason.shallow as shallow  # noqa: E402
from reasoning_endpoint import endpoint_from_profile  # noqa: E402

CYCLES = 3
TOKEN_BUDGET = 400_000
RUN_INPUT = HERE.parents[1] / "2026-09-05-change-mini-isolation-programme" / "runs" / "input-d8"


def main() -> int:
    assert os.environ.get("DEEPREASON_MINI_FLOW") == "mini.flow.room.v1", "flow not selected"
    shallow._endpoint = endpoint_from_profile
    result = shallow.run_shallow_question(run_input_root=RUN_INPUT, cycles=CYCLES, token_budget=TOKEN_BUDGET)
    (HERE / "ROOM_RESULT.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("ROOM_RESULT", json.dumps({k: v for k, v in result.items() if k != "seat_plugins"}, indent=1), flush=True)

    from deepreason.invariants import verify_root
    from minireason.log import replay
    from minireason.loop import Session
    from minireason.records import mini_records

    root = shallow._shallow_runs_dir() / result["run_id"]
    session = Session(root)
    report = verify_root(root)
    kinds = [r.kind for r in mini_records(session)]
    terminal = {
        "schema": "wr-room-terminal.v1", "root": str(root),
        "completed": result["completed"], "stop": result["summary"]["stop"],
        "cycles": result["summary"]["cycles"], "flow": result["summary"]["flow"],
        "model_profile": result["summary"]["model_profile"],
        "problems": result["summary"]["problems"], "refuted": result["summary"]["refuted"],
        "meter_equals_log": result["summary"]["meter_equals_log"],
        "logged_tokens_this_run": result["summary"]["logged_tokens_this_run"],
        "records_by_kind": {k: kinds.count(k) for k in sorted(set(kinds))},
        "events": len(session.state.events),
        "verify_root_violations": len(report["violations"]),
        "replay_digest_equals_live": replay(root).digest() == session.state.digest(),
        "digest": session.state.digest(),
    }
    ok = (terminal["completed"] and terminal["stop"] in ("max-cycles", "queue-exhausted", "budget")
          and terminal["meter_equals_log"] and terminal["verify_root_violations"] == 0
          and terminal["replay_digest_equals_live"])
    terminal["TYPED_TERMINAL"] = "COMPLETE" if ok else "FAILED"
    (HERE / "ROOM_TERMINAL.json").write_text(json.dumps(terminal, indent=1), encoding="utf-8")
    print("ROOM_TERMINAL", json.dumps(terminal, indent=1), flush=True)
    subprocess.run([sys.executable, str(HERE.parent / "tools" / "census.py"), str(root), "--json", str(HERE / "CENSUS.json")], check=False)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
