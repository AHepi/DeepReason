#!/usr/bin/env python3
"""Q1 probe D -- on the dispatches where the channel WAS open, what did the
critic actually return in `premise` and `premise_evidence`?

`_check_premise_citations` (rules/crit.py:1367) returns () without recording
anything when `refs` is empty, so a zero count of `premise-citation:` Measures
is consistent with two different worlds: the seat submitted nothing, or the
seat submitted something the record dropped. This reads the raw response blob
for every critic dispatch whose PROMPT carried the invitation and reports the
two fields verbatim, which separates them.

Usage: q1_invited_replies.py <root> [<root> ...]
"""
import json
import pathlib
import sys

INVITED = 'state that presupposition in "premise"'


def blob(root, ref):
    if not ref:
        return ""
    p = root / "blobs" / ref[:2] / ref
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def scan(root: pathlib.Path):
    rows = []
    with (root / "log.jsonl").open() as fh:
        for line in fh:
            ev = json.loads(line)
            llm = ev.get("llm") or {}
            if llm.get("role") != "argumentative_critic":
                continue
            if INVITED not in blob(root, llm.get("prompt_ref")):
                continue
            raw = blob(root, llm.get("raw_ref"))
            row = {"seq": ev["seq"], "raw_ref": llm.get("raw_ref"), "raw_len": len(raw)}
            found = []
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = None
            def walk(node):
                if isinstance(node, dict):
                    if "premise" in node or "premise_evidence" in node:
                        found.append({
                            "premise": node.get("premise"),
                            "premise_evidence": node.get("premise_evidence"),
                            "attack": node.get("attack"),
                        })
                    for v in node.values():
                        walk(v)
                elif isinstance(node, list):
                    for v in node:
                        walk(v)
            walk(parsed)
            row["cases_with_premise_fields"] = found
            row["parsed"] = parsed is not None
            if parsed is None:
                row["raw_head"] = raw[:400]
            rows.append(row)
    return {"root": root.name, "invited_dispatches": rows}


if __name__ == "__main__":
    print(json.dumps([scan(pathlib.Path(a)) for a in sys.argv[1:]], indent=2))
