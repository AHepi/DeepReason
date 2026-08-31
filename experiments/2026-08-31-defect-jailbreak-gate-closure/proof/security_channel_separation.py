"""Does the SECURITY-channel predicate separate a forged record from lawful ones?

The gate this tranche lands refuses `continue` and `amend` when the record's
RE-DERIVED replay verdict carries a finding on the SECURITY channel.  That
narrowing is only defensible if the predicate actually SEPARATES: non-empty on
a tampered record, empty on records that are merely incomplete, mid-repair, or
written by an older version.

    python experiments/2026-08-31-defect-jailbreak-gate-closure/proof/security_channel_separation.py

Copies only.  The forged arm is a one-byte flip of the first recorded provider
endpoint, same length, on a throwaway copytree -- committed roots are evidence
and their bytes never change.

Writes security_channel_separation.json beside itself.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "security_channel_separation.json"

FORGE_ROOT = "experiments/2026-08-27-pc2b-symmetric-reasoning/run"
_ENDPOINT = b'"endpoint":"https://ollama.com/v1"'
_HOST_BYTE = len(b'"endpoint":"https://oll')

# Lawful committed roots, smallest first: each is a record the product supports
# on purpose.  None may trip the predicate.
LAWFUL = [
    "experiments/2026-08-26-pc2-rematch/run_h3",
    "experiments/2026-08-26-pc2-rematch/retired-transport-timeout180-run-42ad288038dd606c",
    "experiments/2026-08-26-pc2-rematch/retired-truncation-cap32768-run-58fb0d20488be869",
    "experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d",
    "experiments/2026-08-13-defect-controller-steering-inert/failed-epoch3-run-8e22d0431fd2b98d",
    "experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch4-run-9175f0ecb055e57455af3c50df153c5a",
    "experiments/live_research_2026-07-29/referee/runs/run-e542c3c1fc266943e0260c5aa8d7c107",
]


def forge(log: Path) -> dict:
    raw = bytearray(log.read_bytes())
    before = len(raw)
    offset = bytes(raw).index(_ENDPOINT) + _HOST_BYTE
    was = chr(raw[offset])
    now = "7" if was != "7" else "6"
    raw[offset] = ord(now)
    log.write_bytes(bytes(raw))
    assert len(log.read_bytes()) == before
    return {"offset": offset, "from": was, "to": now}


def observe(root: Path) -> dict:
    """Evaluate the shipped predicate, or its definition, on one root."""

    from deepreason.invariants import verify_root

    try:  # the shipped helper once the gate has landed
        from deepreason.runtime.continuation import security_channel_violations

        shipped = True
    except ImportError:  # before the gate lands, evaluate its definition
        from deepreason.verification.report import _SECURITY_CHECKS

        shipped = False

        def security_channel_violations(root: Path) -> list[str]:
            verdict = verify_root(root)
            return sorted(
                {
                    str(item.get("check"))
                    for item in (verdict.get("violations") or [])
                    if str(item.get("check")) in _SECURITY_CHECKS
                }
            )

    started = time.monotonic()
    all_checks = sorted(
        {str(i.get("check")) for i in (verify_root(root).get("violations") or [])}
    )
    security = security_channel_violations(root)
    return {
        "predicate_source": "shipped" if shipped else "definition",
        "seconds": round(time.monotonic() - started, 2),
        "all_verify_root_checks": all_checks,
        "security_channel": security,
        "gate_refuses": bool(security),
    }


def main() -> int:
    sys.path.insert(0, str(REPO / "src"))
    payload: dict = {"lawful": {}, "tampered": {}}

    for relative in LAWFUL:
        root = REPO / relative
        if not (root / "run-status.json").exists():
            payload["lawful"][relative] = {"skipped": "no run-status.json"}
            continue
        payload["lawful"][relative] = observe(root)
        row = payload["lawful"][relative]
        print(f"LAWFUL   refuses={row['gate_refuses']!s:<5} {relative}")
        print(f"         all={row['all_verify_root_checks']} sec={row['security_channel']}")

    source = REPO / FORGE_ROOT
    for arm in ("intact", "forged"):
        with tempfile.TemporaryDirectory() as scratch:
            copy = Path(scratch) / source.name
            shutil.copytree(source, copy, symlinks=True)
            if arm == "forged":
                payload["edit"] = forge(copy / "log.jsonl")
            payload["tampered"][arm] = observe(copy)
        row = payload["tampered"][arm]
        print(f"{arm.upper():<9}refuses={row['gate_refuses']!s:<5} {FORGE_ROOT}")
        print(f"         all={row['all_verify_root_checks']} sec={row['security_channel']}")

    lawful_rows = [r for r in payload["lawful"].values() if "gate_refuses" in r]
    payload["separates"] = (
        not any(r["gate_refuses"] for r in lawful_rows)
        and not payload["tampered"]["intact"]["gate_refuses"]
        and payload["tampered"]["forged"]["gate_refuses"]
    )
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"separates: {payload['separates']}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
