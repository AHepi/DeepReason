#!/usr/bin/env python3
"""Q3 probe -- was the wander cap present and did it BIND, and where does the
off-subject work descend from?

The cap (F3, 2026-08-26) is `src/deepreason/wander.py`, selected by
`Config.ATTENTION_ALLOCATION_POLICY` (config.py:310, default "wander-cap.v1")
against `Config.SEED_PROBLEM_BUDGET_FLOOR` (config.py:295, default 0.5). Both
are dropped from the manifest's engine-config echo (run_manifest.py:2386-2388),
so a manifest-launched run takes their DEFAULTS -- which is how this run got
the cap at all. It emits two signals (wander.py:44):

    allocation.seed-lineage-share.v1     the reading
    allocation.wander-throttled.v1       emitted when the throttle engaged

This reads both out of the record, and separately counts every problem by its
spawn prefix and its provenance, so "off-subject" can be attributed to a
generator rather than asserted.

Usage: q3_wander_and_subject.py <root> [<root> ...]
"""
import json
import pathlib
import sys
from collections import Counter


def rows(root: pathlib.Path):
    out = []
    with (root / "log.jsonl").open() as fh:
        for line in fh:
            ev = json.loads(line)
            ins = [i for i in (ev.get("inputs") or []) if isinstance(i, str)]
            if any(i.startswith("allocation.") for i in ins):
                out.append({"seq": ev["seq"], "rule": ev.get("rule"), "inputs": ins})
    return out


def problems(root: pathlib.Path):
    pdir = root / "objects" / "problem"
    by_prefix = Counter()
    by_trigger = Counter()
    detail = []
    if not pdir.exists():
        return by_prefix, by_trigger, detail
    for path in sorted(pdir.rglob("*")):
        if not path.is_file():
            continue
        try:
            body = json.loads(path.read_text())
        except Exception:
            continue
        pid = body.get("id") or path.stem
        prefix = pid.split(":", 1)[0] if ":" in pid else ("seed" if pid.startswith("question-") else "?")
        by_prefix[prefix] += 1
        prov = body.get("provenance") or {}
        trigger = prov.get("trigger") or ("seed" if prefix == "seed" else "?")
        by_trigger[str(trigger)] += 1
        detail.append({"id": pid, "prefix": prefix, "trigger": str(trigger),
                       "from": prov.get("from")})
    return by_prefix, by_trigger, detail


def report(root: pathlib.Path) -> dict:
    by_prefix, by_trigger, detail = problems(root)
    return {
        "root": root.name,
        "allocation_events": rows(root),
        "problem_count": sum(by_prefix.values()),
        "problems_by_prefix": dict(by_prefix.most_common()),
        "problems_by_trigger": dict(by_trigger.most_common()),
        "problem_detail": detail,
    }


if __name__ == "__main__":
    print(json.dumps([report(pathlib.Path(a)) for a in sys.argv[1:]], indent=2))
