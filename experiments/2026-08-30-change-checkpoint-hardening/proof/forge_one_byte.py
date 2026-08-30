"""ONE flipped byte of a recorded provider endpoint, and what each verb says.

The operator's 2026-08-29 law is about a jailbroken run. This measures the
jailbreak rather than describing it: on a COPY of one committed root, flip a
single byte inside the endpoint recorded for its first LLM call -- the
smallest edit that forges WHERE a provider call went -- and ask four surfaces
what they think of the result.

    python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_one_byte.py

Copies only, always. The original is evidence; its bytes never change.
Writes forge_one_byte.json beside itself.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "forge_one_byte.json"

ROOT = (
    "experiments/2026-08-13-defect-controller-steering-inert"
    "/failed-epoch1-run-8e22d0431fd2b98d"
)
_ENDPOINT = b'"endpoint":"https://ollama.com/v1"'
_HOST_BYTE = len(b'"endpoint":"https://oll')


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
    from deepreason.amendment.apply import _require_terminal_stop
    from deepreason.application.results import results_summary
    from deepreason.invariants import verify_root
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
    from deepreason.runtime.continuation import prepare_continuation
    from deepreason.runtime.terminal_authority import derive_terminal_authority

    manifest = load_run_manifest(root / MANIFEST_NAME)
    row: dict = {}
    row["stored_replay_valid"] = json.loads(
        (root / "REPLAY_VALIDATION.json").read_text()
    )["valid"]
    row["verify_root_violations"] = sorted(
        {item["check"] for item in verify_root(root)["violations"]}
    )
    row["terminal_authority"] = derive_terminal_authority(
        root, manifest=manifest
    ).status
    try:
        _require_terminal_stop(root, manifest)
        row["amend_gate"] = "PASSED"
    except Exception as error:  # noqa: BLE001 - the observation IS the outcome
        row["amend_gate"] = f"REFUSED {type(error).__name__}: {error}"
    row["results_terminal_default"] = results_summary(root)["terminal"][
        "valid_typed_terminal"
    ]
    row["results_terminal_verify"] = results_summary(root, verify=True)["terminal"][
        "valid_typed_terminal"
    ]
    # prepare_continuation WRITES before it can refuse, so it goes last, on a
    # copy of the copy.
    with tempfile.TemporaryDirectory() as inner:
        twice = Path(inner) / root.name
        shutil.copytree(root, twice, symlinks=True)
        try:
            record = prepare_continuation(
                twice, cycles=1, tokens=10, check_operator_lock=False
            )
            row["continue_gate"] = f"ACCEPTED seq={record.get('seq')}"
        except Exception as error:  # noqa: BLE001
            row["continue_gate"] = f"REFUSED {type(error).__name__}: {error}"
    return row


def main() -> int:
    sys.path.insert(0, str(REPO / "src"))
    source = REPO / ROOT
    payload: dict = {"root": ROOT, "arms": {}}
    for arm in ("intact", "forged"):
        with tempfile.TemporaryDirectory() as scratch:
            copy = Path(scratch) / source.name
            shutil.copytree(source, copy, symlinks=True)
            if arm == "forged":
                payload["edit"] = forge(copy / "log.jsonl")
            payload["arms"][arm] = observe(copy)
        print(f"--- {arm} ---")
        for key, value in payload["arms"][arm].items():
            print(f"  {key}: {value}")
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"edit: {payload['edit']}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
