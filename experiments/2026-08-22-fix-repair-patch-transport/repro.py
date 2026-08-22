#!/usr/bin/env python3
"""Smallest offline demonstration of the diagnosed cause (read-only).

Replays the six repair responses the epoch-1 run discarded, verbatim from the
committed root's blobs, through the live transport path
(`tolerant_patch_value` -> `RepairPatchV1`).  Prints, for each, whether the
harness can read it and whether its pointer was authorized.

Exit 1 while the defect is present (a lossless spelling is discarded);
exit 0 once every response whose loss is purely a spelling is applied.

Usage:  python repro.py [<root>]
"""
from __future__ import annotations

import json
import pathlib
import sys

from deepreason.llm.repair import (
    RepairPatchV1,
    parse_one_json_value,
    tolerant_patch_value,
)

DEFAULT_ROOT = (
    pathlib.Path(__file__).resolve().parents[1]
    / "2026-08-22-live-reach-rich-run"
    / "failed-epoch1-run-40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c"
)

# The one response whose loss is NOT a spelling: it offers "old"/"new" where
# the contract requires "value", so reading it would be an inference about
# intent rather than a rename of a field the harness itself supplied.
SUBSTANTIVE_LOSS = ("conjecturer.atomic-candidate.v1", 1)


def _blob(root: pathlib.Path, digest: str) -> str | None:
    if not digest:
        return None
    path = root / "blobs" / digest[:2] / digest
    return path.read_text() if path.exists() else None


def _turns(root: pathlib.Path):
    preparations = {}
    for path in (root / "objects/workflow-work-preparation-v1").glob("*.json"):
        data = json.loads(path.read_text())["data"]
        preparations[data["id"]] = data
    for path in (root / "objects/workflow-provider-attempt-v1").glob("*.json"):
        attempt = json.loads(path.read_text())["data"]
        preparation = preparations.get(attempt["work_id"])
        if preparation is None or preparation.get("task_kind") != "repair":
            continue
        payload = preparation.get("task_payload_value") or json.loads(
            _blob(root, preparation.get("task_payload_ref", "")) or "{}"
        )
        yield payload, _blob(root, attempt.get("raw_ref", ""))


def main() -> int:
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROOT
    lost = []
    for payload, raw in sorted(
        _turns(root), key=lambda t: (str(t[0].get("contract_id")), t[0].get("repair_index") or 0)
    ):
        key = (payload.get("contract_id"), payload.get("repair_index"))
        authorized = tuple(payload.get("authorized_pointers") or ())
        value = tolerant_patch_value(parse_one_json_value(raw).value)
        try:
            patch = RepairPatchV1.model_validate(value)
        except (TypeError, ValueError):
            verdict = "DISCARDED at the wire"
            if key != SUBSTANTIVE_LOSS:
                lost.append(key)
        else:
            verdict = (
                f"applied {patch.op} {patch.path}"
                if patch.path in authorized
                else f"OFF TARGET {patch.path}"
            )
        print(f"{key[0]:32s} #{key[1]}  {verdict}")

    print()
    if lost:
        print(f"DEFECT PRESENT: {len(lost)} lossless spellings discarded: {lost}")
        return 1
    print("no lossless spelling is discarded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
