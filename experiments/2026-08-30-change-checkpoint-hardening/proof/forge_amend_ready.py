"""The full jailbreak, end to end: forge one byte, then amend AND continue.

`forge_one_byte.py` measures the same forgery on a FAILED root, where
`continue` refuses for a reason that has nothing to do with the record
(`CONTINUE_TYPED_STOP_REQUIRED`).  That leaves the operator's clause -- "I
don't want a jailbroken run to be continuable" -- half measured: the refusal
seen there is not the gate working.  This probe closes that hole by driving
the SAME one-byte forgery through the same two verbs on an `amend_ready`
root, in the order an operator would use them: amend, then continue.

    python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_amend_ready.py

Copies only, always. The original is evidence; its bytes never change. Both
verbs WRITE, so each arm gets its own copy and is thrown away after.

Written 2026-08-30 in the skeptic pass, as the acceptance target PARKED.md F9
must clear: the gate is shipped when the forged arm below refuses BOTH verbs.
Writes forge_amend_ready.json beside itself.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "forge_amend_ready.json"

ROOT = "experiments/2026-08-27-pc2b-symmetric-reasoning/run"
_ENDPOINT = b'"endpoint":"https://ollama.com/v1"'
_HOST_BYTE = len(b'"endpoint":"https://oll')
QUESTION = "SKEPTIC PROBE: does a forged record still buy an amendment epoch?"


def forge(log: Path) -> dict:
    """Flip one byte of the first recorded provider endpoint, same length."""

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
    from deepreason.amendment.apply import amend_run
    from deepreason.application.results import results_summary
    from deepreason.invariants import verify_root
    from deepreason.runtime.continuation import prepare_continuation

    row: dict = {}
    row["stored_replay_valid"] = json.loads(
        (root / "REPLAY_VALIDATION.json").read_text()
    )["valid"]
    row["verify_root_violations"] = sorted(
        {item["check"] for item in verify_root(root)["violations"]}
    )
    summary = results_summary(root)
    row["results_amend_ready_default"] = summary["terminal"]["amend_ready"]
    row["results_amend_ready_verify"] = results_summary(root, verify=True)[
        "terminal"
    ]["amend_ready"]
    try:
        record = amend_run(root, reshape_question=QUESTION)
        row["amend"] = f"ACCEPTED epoch={record.get('epoch')}"
    except Exception as error:  # noqa: BLE001 - the observation IS the outcome
        row["amend"] = f"REFUSED {type(error).__name__}: {error}"
    # Deliberately after `amend`: `prepare_continuation` requires the
    # amendment committed, so this is the operator's real sequence and the
    # only order in which the whole jailbreak is visible.
    try:
        continuation = prepare_continuation(
            root, cycles=1, tokens=10, check_operator_lock=False
        )
        row["continue"] = f"ACCEPTED seq={continuation.get('seq')}"
    except Exception as error:  # noqa: BLE001
        row["continue"] = f"REFUSED {type(error).__name__}: {error}"
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
    forged = payload["arms"]["forged"]
    payload["jailbreak_open"] = forged["amend"].startswith("ACCEPTED") and forged[
        "continue"
    ].startswith("ACCEPTED")
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"edit: {payload['edit']}")
    print(f"jailbreak_open: {payload['jailbreak_open']}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
