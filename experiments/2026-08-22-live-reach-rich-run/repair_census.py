#!/usr/bin/env python3
"""Census the repair loop of one root's provider attempts (read-only).

Written for PARKED P7-reach: the reach-rich epoch-1 run terminated with
V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY, and the question that decides which
remedy applies is whether the seat ran out of COMPLETION BUDGET (the
ledgered glm-5.2 cap-burn, answered by a bigger cap) or emitted a
well-formed patch for the WRONG POINTER (answered by neither).

Reads only committed root objects and blobs; writes <root>/../<prefix>-
repair-census.json next to the tranche's other census output.

Usage:  python repair_census.py <root> [out.json]
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys


def _blob(root: pathlib.Path, digest: str) -> str | None:
    if not digest:
        return None
    path = root / "blobs" / digest[:2] / digest
    return path.read_text() if path.exists() else None


def _patch_paths(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        patch = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(patch, dict) and "path" in patch:
        return [patch["path"]]
    if isinstance(patch, list):
        return [p["path"] for p in patch if isinstance(p, dict) and "path" in p]
    return []


def census(root: pathlib.Path) -> dict:
    codes: collections.Counter = collections.Counter()
    contracts: collections.Counter = collections.Counter()
    attempts = 0
    zero_completion = 0
    with_diagnostic = 0
    off_target = []
    for path in sorted((root / "objects/workflow-provider-attempt-v1").glob("*.json")):
        data = json.loads(path.read_text())["data"]
        attempts += 1
        role = data["route_lease"]["role"]
        contracts[f"{role}::{data.get('contract_id')}"] += 1
        if data.get("completion_tokens") == 0:
            zero_completion += 1
        envelope_raw = _blob(root, data.get("diagnostic_ref", ""))
        if not envelope_raw:
            continue
        try:
            envelope = json.loads(envelope_raw)
        except json.JSONDecodeError:
            continue
        with_diagnostic += 1
        for diagnostic in envelope.get("diagnostics", []):
            codes[diagnostic.get("code")] += 1
        authorized = envelope.get("authorized_pointers") or []
        patched = _patch_paths(_blob(root, data.get("raw_ref", "")))
        if patched and authorized and not set(patched) <= set(authorized):
            off_target.append(
                {
                    "attempt_index": data.get("attempt_index"),
                    "authorized_pointers": authorized,
                    "completion_tokens": data.get("completion_tokens"),
                    "contract_id": data.get("contract_id"),
                    "patched_paths": patched,
                    "role": role,
                }
            )
    return {
        "attempts_with_repair_diagnostic": with_diagnostic,
        "attempts_with_zero_completion_tokens": zero_completion,
        "diagnostic_codes": dict(codes),
        "off_target_repairs": off_target,
        "provider_attempts": attempts,
        "provider_attempts_by_role_contract": dict(contracts),
        "root": str(root),
    }


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: repair_census.py <root> [out.json]", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1])
    result = census(root)
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) == 3 else root.parent / "repair-census.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"\nwrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
