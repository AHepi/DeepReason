#!/usr/bin/env python3
"""Q5/P8 probe -- every repair task payload the record holds, replayed against
the authority check that killed epoch 5.

`workflow/nonconjecture_recovery.py:1001-1002`:

    mode = payload.get("mode")
    _authority(mode in {"patch", "full"}, "repair mode is invalid")

P8 says a payload reached that check carrying a mode that is neither. This
pulls every `repair.semantic-task.v1` payload out of each root's workflow state
and reports its `mode`, `repair_index`, `authorized_pointers` and contract, so
the offending value is read rather than guessed, and epoch 6's four surviving
repairs can be compared shape-for-shape against epoch 5's.

Usage: q5_repair_payloads.py <root> [<root> ...]
"""
import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, "src")
from deepreason.harness import Harness  # noqa: E402

LEGAL_MODES = {"patch", "full"}


def report(root: pathlib.Path) -> dict:
    ws = Harness(root, read_only=True).workflow_state
    rows = []
    modes = Counter()
    for work_id, item in (ws.transaction_work or {}).items():
        payload = getattr(item.preparation, "task_payload_value", None)
        if not isinstance(payload, dict):
            continue
        if payload.get("schema") != "repair.semantic-task.v1":
            continue
        mode = payload.get("mode")
        modes[repr(mode)] += 1
        rows.append({
            "work_id": work_id[:16],
            "mode": mode,
            "mode_is_legal": mode in LEGAL_MODES,
            "repair_index": payload.get("repair_index"),
            "attempt_index": item.preparation.attempt_index,
            "contract_id": payload.get("contract_id"),
            "authorized_pointers": payload.get("authorized_pointers"),
            "pointers_canonical": (
                isinstance(payload.get("authorized_pointers"), (list, tuple))
                and tuple(payload.get("authorized_pointers") or ())
                == tuple(sorted(set(payload.get("authorized_pointers") or ())))
            ),
            "terminal_status": getattr(getattr(item, "terminal", None), "status", None),
        })
    rows.sort(key=lambda r: (str(r["contract_id"]), r["repair_index"] or 0))
    return {
        "root": root.name,
        "repair_payloads": len(rows),
        "mode_values": dict(modes),
        "illegal_modes": [r for r in rows if not r["mode_is_legal"]],
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps([report(pathlib.Path(a)) for a in sys.argv[1:]], indent=2))
