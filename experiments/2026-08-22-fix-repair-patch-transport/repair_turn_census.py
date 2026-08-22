#!/usr/bin/env python3
"""Census every dispatched v6 repair turn of one root (read-only).

Supersedes `experiments/2026-08-22-live-reach-rich-run/repair_census.py` for
the question "did the seat patch the pointer it was authorized to patch?".

That script paired each provider attempt's raw response with the envelope at
the attempt's own `diagnostic_ref`.  For a repair turn that field is written by
`repair_transaction._terminalize_invalid` as `trace_ref or next_diagnostic_ref`
— the diagnostic derived AFTER the response was applied.  Comparing a response
against the NEXT turn's authority makes every converging repair look
off-target.

The authority a turn was actually dispatched under is its work preparation's
`repair.semantic-task.v1` payload (`authorized_pointers`, `diagnostic_ref`,
`baseline_sha256`), which `repair_transaction` freezes before issue.  This
script joins on `provider_attempt.work_id -> preparation.id` and reports each
turn against its own dispatched authority, then replays the recorded bytes
through the live wire path to say WHY a turn was lost.

Usage:  python repair_turn_census.py <root> [out.json]
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

from deepreason.llm.repair import (
    RepairPatchV1,
    parse_one_json_value,
    tolerant_patch_value,
)


def _blob(root: pathlib.Path, digest: str) -> str | None:
    if not digest:
        return None
    path = root / "blobs" / digest[:2] / digest
    return path.read_text() if path.exists() else None


def _classify(root: pathlib.Path, raw: str | None, authorized: tuple[str, ...]) -> dict:
    """Replay one recorded response through the live transport path."""
    if raw is None:
        return {"verdict": "no_raw"}
    try:
        value = parse_one_json_value(raw).value
    except ValueError as error:
        return {"verdict": "unparseable", "detail": str(error)[:200]}
    try:
        patch = RepairPatchV1.model_validate(tolerant_patch_value(value))
    except (TypeError, ValueError) as error:
        return {
            "verdict": "wire_rejected",
            "detail": type(error).__name__,
            "response_keys": sorted(value) if isinstance(value, dict) else None,
        }
    return {
        "verdict": "applied" if patch.path in authorized else "off_target",
        "op": patch.op,
        "path": patch.path,
    }


def census(root: pathlib.Path) -> dict:
    preparations = {}
    for path in (root / "objects/workflow-work-preparation-v1").glob("*.json"):
        data = json.loads(path.read_text())["data"]
        preparations[data["id"]] = data

    turns = []
    for path in (root / "objects/workflow-provider-attempt-v1").glob("*.json"):
        attempt = json.loads(path.read_text())["data"]
        preparation = preparations.get(attempt["work_id"])
        if preparation is None or preparation.get("task_kind") != "repair":
            continue
        payload = preparation.get("task_payload_value")
        if payload is None and preparation.get("task_payload_ref"):
            payload = json.loads(_blob(root, preparation["task_payload_ref"]) or "{}")
        payload = payload or {}
        authorized = tuple(payload.get("authorized_pointers") or ())
        turns.append(
            {
                "contract_id": payload.get("contract_id"),
                "repair_index": payload.get("repair_index"),
                "mode": payload.get("mode"),
                "parent_work_id": payload.get("parent_work_id"),
                "dispatched_authorized_pointers": list(authorized),
                "completion_tokens": attempt.get("completion_tokens"),
                **_classify(root, _blob(root, attempt.get("raw_ref", "")), authorized),
            }
        )

    turns.sort(key=lambda t: (str(t["contract_id"]), str(t["parent_work_id"]), t["repair_index"] or 0))
    verdicts = collections.Counter(t["verdict"] for t in turns)
    return {
        "dispatched_repair_turns": len(turns),
        "off_target_repairs": [t for t in turns if t["verdict"] == "off_target"],
        "root": root.name,
        "turns": turns,
        "verdicts": dict(verdicts),
    }


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: repair_turn_census.py <root> [out.json]", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1])
    result = census(root)
    out = (
        pathlib.Path(sys.argv[2])
        if len(sys.argv) == 3
        else pathlib.Path(__file__).parent / "repair-turn-census.json"
    )
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"\nwrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
