#!/usr/bin/env python3
"""Every committed root that recorded a criticism event, by Crit count.

GOAL.md's own derivation, committed so the synthesis round can diff this
list against W1's inventory instead of trusting either.
"""
from __future__ import annotations
import json, pathlib, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
rows = []
for log in sorted((REPO / "experiments").rglob("log.jsonl")):
    n = 0
    for line in log.read_text(errors="replace").splitlines():
        if '"Crit"' not in line:
            continue
        try:
            if json.loads(line).get("rule") == "Crit":
                n += 1
        except Exception:  # noqa: BLE001
            pass
    if n:
        rows.append((n, str(log.parent.relative_to(REPO))))
rows.sort(reverse=True)
out = {"n_roots_with_criticism": len(rows),
       "total_criticism_events": sum(n for n, _ in rows),
       "roots": [{"crit_events": n, "root": r} for n, r in rows]}
pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "roots.json").write_text(
    json.dumps(out, indent=1))
print(f"{len(rows)} roots, {out['total_criticism_events']} criticism events")
for n, r in rows[:25]:
    print(f"  {n:6d}  {r}")
