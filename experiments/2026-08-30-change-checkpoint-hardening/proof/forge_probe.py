"""Is the stored replay verdict tamper-evident? Measured, root by root.

The security clause of the 2026-08-29 law is "tampering with a record must not
buy a resumable run".  A gate that reads REPLAY_VALIDATION.json's `valid` field
only satisfies that clause where the stored verdict is BOUND to the terminal.
This probe forges `valid: true` into a COPY of each root and asks
`derive_terminal_authority` whether it noticed.

Copies only, always: `derive_terminal_authority` is a reader, but the forge is
a write, and a committed root is evidence whose bytes never change.

    python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_probe.py

Reads census.json for the root list, writes forge.json beside itself.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CENSUS = HERE / "census.json"
OUT = HERE / "forge.json"


def probe(root: Path) -> dict:
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
    from deepreason.runtime.terminal_authority import derive_terminal_authority

    # The bound manifest is not optional: without one the derivation
    # short-circuits to `historical_read_only` for every root and every forge
    # reads as "detected", which measures the probe rather than the record.
    manifest = load_run_manifest(root / MANIFEST_NAME)
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / root.name
        shutil.copytree(root, copy, symlinks=True)
        stored = json.loads((copy / "REPLAY_VALIDATION.json").read_text())
        forged = dict(stored)
        forged["valid"] = True
        verification = dict(forged.get("verification") or {})
        verification["violations"] = []
        forged["verification"] = verification
        # Canonical bytes, because the attacker this probe models is the one
        # the law names: someone who read how the file is written. A
        # pretty-printed forge is caught by
        # TERMINAL_REPLAY_VALIDATION_NONCANONICAL on formatting alone, which
        # measures the probe rather than the binding.
        from deepreason.canonical import canonical_json

        (copy / "REPLAY_VALIDATION.json").write_bytes(
            canonical_json(forged) + b"\n"
        )
        try:
            authority = derive_terminal_authority(copy, manifest=manifest)
            return {
                "authority_status": authority.status,
                "authority_current_valid": bool(authority.current_valid),
                "authority_detail_code": authority.detail_code,
                "forge_detected": not authority.current_valid,
            }
        except Exception as error:
            return {
                "authority_error": f"{type(error).__name__}: {error}",
                "forge_detected": True,
            }


def main() -> int:
    sys.path.insert(0, str(REPO / "src"))
    census = json.loads(CENSUS.read_text())
    targets = census["A2_gap_authority_valid_but_replay_invalid"]
    rows = []
    for index, rel in enumerate(targets, 1):
        print(f"[{index}/{len(targets)}] {rel}", flush=True)
        row = {"root": rel}
        row.update(probe(REPO / rel))
        rows.append(row)
    undetected = sorted(r["root"] for r in rows if not r["forge_detected"])
    payload = {
        "population": len(rows),
        "detected": len(rows) - len(undetected),
        "undetected": undetected,
        "outcomes": dict(
            Counter(
                f"{r.get('authority_status')} / {r.get('authority_detail_code')}"
                for r in rows
            ).most_common()
        ),
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"population: {payload['population']}")
    print(f"forge DETECTED on: {payload['detected']}")
    print(f"forge UNDETECTED on: {len(undetected)}")
    for path in undetected:
        print(f"  {path}")
    print(f"outcomes: {payload['outcomes']}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
