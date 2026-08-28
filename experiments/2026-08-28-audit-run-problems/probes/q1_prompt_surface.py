#!/usr/bin/env python3
"""Q1 probe C -- what every critic dispatch was actually SHOWN about the
byte-checked citation channel, read from the prompt bytes the call was made on.

Method. Every provider call in the record carries `llm.prompt_ref`, the sha256
of the prompt blob under `blobs/`. This walks every call with
`role == argumentative_critic`, opens its prompt blob, and tests three markers:

  invited        the premise invitation paragraph ("state that presupposition
                 in \"premise\"") -- emitted only when the problem is standing
                 an invitation, so its presence proves the gate was open FOR
                 THIS CALL, not merely open somewhere in the run.
  evidence_ask   the sentence naming premise_evidence as a citable channel.
  schema_field   the string `premise_evidence` anywhere in the prompt (it lives
                 in the wire schema, so it can be present while the invitation
                 is absent -- that difference is the whole question).
  citable_list   the CITABLE EVIDENCE BLOCKS legend.

Reported per root: how many critic dispatches saw each, and the seqs.

Usage: q1_prompt_surface.py <root> [<root> ...]
"""
import json
import pathlib
import sys

INVITED = 'state that presupposition in "premise"'
EVIDENCE_ASK = 'cite it in "premise_evidence"'
SCHEMA_FIELD = "premise_evidence"
CITABLE = "CITABLE EVIDENCE BLOCKS"


def blob(root: pathlib.Path, ref: str) -> str:
    path = root / "blobs" / ref[:2] / ref
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def survey(root: pathlib.Path) -> dict:
    per_role = {}
    with (root / "log.jsonl").open() as fh:
        for line in fh:
            ev = json.loads(line)
            llm = ev.get("llm")
            if not llm:
                continue
            role = llm.get("role") or "?"
            ref = llm.get("prompt_ref")
            bucket = per_role.setdefault(
                role,
                {"dispatches": 0, "invited": [], "evidence_ask": [], "schema_field": 0,
                 "citable_list": 0, "no_prompt_blob": 0},
            )
            bucket["dispatches"] += 1
            text = blob(root, ref) if ref else ""
            if not text:
                bucket["no_prompt_blob"] += 1
                continue
            if INVITED in text:
                bucket["invited"].append(ev["seq"])
            if EVIDENCE_ASK in text:
                bucket["evidence_ask"].append(ev["seq"])
            if SCHEMA_FIELD in text:
                bucket["schema_field"] += 1
            if CITABLE in text:
                bucket["citable_list"] += 1
    for bucket in per_role.values():
        bucket["invited_count"] = len(bucket["invited"])
        bucket["evidence_ask_count"] = len(bucket["evidence_ask"])
    return {"root": root.name, "by_role": per_role}


if __name__ == "__main__":
    print(json.dumps([survey(pathlib.Path(a)) for a in sys.argv[1:]], indent=2, sort_keys=True))
