#!/usr/bin/env python3
"""The structural sweep: over EVERY root that recorded criticism, does the
causal channel criticism would need even exist?

GOAL.md dimension 3, widened.  The two priority roots hold 666 of the 2 639
criticism events in the tree; a finding about them is a finding about 25% of
the evidence.  This sweep asks the cheap structural question of all 60:

  * what authority were criticism dispatches given (`observe_only` cannot
    mint a warrant, so it cannot move a Status);
  * what kinds of warrant were minted at all;
  * was ANY critic-role artifact ever exposed to a later conjecture
    dispatch — the only path by which a criticism could change what the
    run does next.

Reads object files directly rather than replaying, so it is cheap enough to
run over the whole tree; it therefore reports STRUCTURE, not status labels.

Usage:  python sweep.py <roots.json> <out.json>
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]


def _objs(root: pathlib.Path, kind: str):
    d = root / "objects" / kind
    if not d.is_dir():
        return
    for p in d.glob("*.json"):
        try:
            yield json.load(p.open())["data"]
        except Exception:  # noqa: BLE001 - an unreadable object is an absence
            continue


def survey(root: pathlib.Path) -> dict:
    role: dict[str, str] = {}
    for a in _objs(root, "artifact"):
        r = str(((a.get("provenance") or {}).get("role")) or "")
        role[a.get("id")] = r.split(".")[-1].lower()

    wtypes = collections.Counter()
    wverdicts = collections.Counter()
    for w in _objs(root, "warrant"):
        wtypes[w.get("type")] += 1
        wverdicts[w.get("verdict")] += 1

    preps = {}
    kinds = collections.Counter()
    auth = collections.Counter()
    for p in _objs(root, "workflow-work-preparation-v1"):
        preps[p.get("id")] = p
        kinds[p.get("task_kind")] += 1
        if p.get("task_kind") == "criticism":
            auth[((p.get("task_payload_value") or {}).get("dispatch_authority"))] += 1

    shown: set[str] = set()
    exposures = 0
    for e in _objs(root, "workflow-context-exposure-v2"):
        prep = preps.get(e.get("work_id"))
        if not prep:
            continue
        exposures += 1
        if prep.get("task_kind") != "conjecture":
            continue
        for it in e.get("exposed_items") or []:
            if role.get(it.get("object_ref")) == "critic":
                shown.add(it["object_ref"])

    return {
        "n_artifacts": len(role),
        "n_critic_artifacts": sum(1 for v in role.values() if v == "critic"),
        "warrant_types": dict(wtypes),
        "warrant_verdicts": dict(wverdicts),
        "task_kinds": dict(kinds),
        "criticism_dispatch_authority": {str(k): v for k, v in auth.items()},
        "n_context_exposures_joined": exposures,
        "critic_artifacts_shown_to_conjecture": len(shown),
        "has_workflow_objects": bool(preps),
    }


def main() -> int:
    roots = json.loads(pathlib.Path(sys.argv[1]).read_text())["roots"]
    out = []
    for row in roots:
        root = REPO / row["root"]
        try:
            out.append({**row, **survey(root)})
        except Exception as e:  # noqa: BLE001
            out.append({**row, "error": str(e)})
    totals = {
        "roots": len(out),
        "criticism_events": sum(r["crit_events"] for r in out),
        "roots_with_workflow_objects": sum(1 for r in out if r.get("has_workflow_objects")),
        "roots_where_a_criticism_reached_a_conjecturer": sum(
            1 for r in out if r.get("critic_artifacts_shown_to_conjecture", 0)
        ),
        "critic_artifacts_shown_to_conjecture_total": sum(
            r.get("critic_artifacts_shown_to_conjecture", 0) for r in out
        ),
        "critic_artifacts_total": sum(r.get("n_critic_artifacts", 0) for r in out),
        "warrant_types": dict(collections.Counter(
            t for r in out for t, n in (r.get("warrant_types") or {}).items() for _ in range(n)
        )),
        "criticism_dispatch_authority": dict(collections.Counter(
            a for r in out for a, n in (r.get("criticism_dispatch_authority") or {}).items()
            for _ in range(n)
        )),
    }
    pathlib.Path(sys.argv[2]).write_text(
        json.dumps({"totals": totals, "roots": out}, indent=1))
    print(json.dumps(totals, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
