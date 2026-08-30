"""What the two continuation verbs do TODAY with a replay-invalid record.

The A2 claim is that neither verb consults the replay verdict. This measures
it rather than reading it out of the source: it takes committed roots whose
own published REPLAY_VALIDATION.json says `valid: false`, and drives both
gates.

Copies only, always: `prepare_continuation` opens a WRITABLE harness and
writes `run-stops/` before it can refuse, and a committed root is evidence
whose bytes never change.

    python experiments/2026-08-30-change-checkpoint-hardening/proof/gate_probe.py

Reads census.json for the witness list, writes gate_probe.json beside itself.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CENSUS = HERE / "census.json"
OUT = HERE / "gate_probe.json"

# Runtime budget, not a property: the smallest witnesses answer the same
# question as the largest ones, and `verify_root` is O(run length).
MAX_EVENTS = 600


def drive(root: Path) -> dict:
    from deepreason.amendment.apply import _require_terminal_stop
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
    from deepreason.runtime.continuation import prepare_continuation

    out: dict = {}
    manifest = load_run_manifest(root / MANIFEST_NAME)
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / root.name
        shutil.copytree(root, copy, symlinks=True)
        try:
            _require_terminal_stop(copy, manifest)
            out["amend_gate"] = "PASSED"
        except Exception as error:
            out["amend_gate"] = f"REFUSED {type(error).__name__}: {error}"
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / root.name
        shutil.copytree(root, copy, symlinks=True)
        try:
            record = prepare_continuation(
                copy, cycles=1, tokens=10, check_operator_lock=False
            )
            out["continue_gate"] = f"ACCEPTED seq={record.get('seq')}"
        except Exception as error:
            out["continue_gate"] = f"REFUSED {type(error).__name__}: {error}"
    return out


def verify_cost(root: Path) -> dict:
    from deepreason.invariants import verify_root

    started = time.monotonic()
    verdict = verify_root(root)
    elapsed = time.monotonic() - started
    return {
        "verify_root_seconds": round(elapsed, 2),
        "verify_root_violations": [v.get("check") for v in verdict["violations"]],
    }


def main() -> int:
    sys.path.insert(0, str(REPO / "src"))
    census = json.loads(CENSUS.read_text())
    by_root = {r["root"]: r for r in census["rows"]}
    witnesses = []
    for rel in census["A2_gap_authority_valid_but_replay_invalid"]:
        log = REPO / rel / "log.jsonl"
        events = sum(1 for _ in log.open()) if log.exists() else 0
        witnesses.append((events, rel))
    witnesses.sort()
    rows = []
    for events, rel in witnesses:
        if events > MAX_EVENTS:
            rows.append({"root": rel, "events": events, "skipped": "over MAX_EVENTS"})
            continue
        print(f"driving {rel} ({events} events)", flush=True)
        row = {"root": rel, "events": events}
        row.update(by_root[rel])
        row.update(drive(REPO / rel))
        row.update(verify_cost(REPO / rel))
        rows.append(row)
        print(f"  amend: {row['amend_gate']}", flush=True)
        print(f"  continue: {row['continue_gate']}", flush=True)
        print(
            f"  verify_root: {row['verify_root_seconds']}s "
            f"violations={row['verify_root_violations']}",
            flush=True,
        )
    payload = {
        "max_events": MAX_EVENTS,
        "witness_population": len(witnesses),
        "driven": len([r for r in rows if "amend_gate" in r]),
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
