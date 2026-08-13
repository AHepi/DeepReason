#!/usr/bin/env python3
"""Typed steering evidence from a run root — the same census DIAGNOSIS.md ran
against the grounded root, so the two are directly comparable.

Judges only typed outcomes: the controller-authority record, the policy
artifacts, and the cap trajectory those policies describe. Prints the census
whatever it finds; an empty result is a recorded negative, not an error.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
log = root / "log.jsonl"
events = [json.loads(line) for line in log.open()]

rules = collections.Counter(e.get("rule") for e in events)
authority = [e for e in events if (e.get("inputs") or [""])[0] == "controller-authority"]
policies = []
artifacts_inline: dict[str, str] = {}
for e in events:
    for out in e.get("outputs") or ():
        artifacts_inline.setdefault(out, "")

# Policy bodies live inline in the artifact content_ref; read them off the
# objects the Refl events emitted.
for e in events:
    if e.get("rule") != "Refl":
        continue
    for out in e.get("outputs") or ():
        for candidate in root.glob(f"objects/**/{out}.json"):
            try:
                body = json.loads(candidate.read_text())
            except (OSError, ValueError):
                continue
            content = body.get("content_ref", "")
            if isinstance(content, str) and content.startswith("inline:"):
                try:
                    parsed = json.loads(content[len("inline:"):])
                except ValueError:
                    continue
                if isinstance(parsed, dict) and isinstance(parsed.get("knobs"), dict):
                    policies.append((e["seq"], parsed))

status = json.loads((root / "run-status.json").read_text())

print(f"root                : {root}")
print(f"run_id              : {status.get('run_id')}")
print(f"state / stop_reason : {status.get('state')} / {status.get('stop_reason')}")
print(f"cycles / tokens     : {status.get('cycle')} / {status.get('token_spend')}"
      f" of {status.get('token_limit')}")
print(f"events              : {len(events)}")
print(f"rule census         : {dict(rules.most_common())}")
print()
print(f"controller-authority records : {len(authority)}")
for e in authority:
    print(f"  seq {e['seq']}: scope={e['inputs'][1]}")
    print(f"    {e['inputs'][2]}")
print()
print(f"controller policy artifacts  : {len(policies)}")
trajectory: dict[str, list] = collections.defaultdict(list)
for seq, body in policies:
    print(f"  seq {seq} cycle {body.get('cycle')}: {json.dumps(body['knobs'], sort_keys=True)}")
    for knob, value in body["knobs"].items():
        trajectory[knob].append(value)
print()
print("cap trajectory (per knob, in policy order):")
if not trajectory:
    print("  (none — no knob moved)")
for knob in sorted(trajectory):
    print(f"  {knob:32} 16384 -> {' -> '.join(str(v) for v in trajectory[knob])}")

# The trap DIAGNOSIS.md recorded: Control events are workflow transactions.
controls = collections.Counter(
    (e.get("control") or {}).get("action")
    for e in events
    if isinstance(e.get("control"), dict)
)
print()
print(f"rule=Control events are workflow transactions, NOT steering: "
      f"{dict(controls.most_common(5))}")
