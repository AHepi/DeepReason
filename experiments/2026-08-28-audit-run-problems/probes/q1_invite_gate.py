#!/usr/bin/env python3
"""Q1 probe B -- was the critic-side citation channel ever OPEN?

The critic's only byte-checked citation path is a PREMISE filing:
`rules/crit.py::_file_attribution` (line 1409) calls `_check_premise_citations`
(1367), which is the sole producer of the `premise-citation:<CODE>` Measure
that milestone_census.py counts for M2. `_file_attribution` returns None -- and
so files nothing, and checks nothing -- unless `_premise_invited_problem`
(crit.py:1268) finds a problem standing an invitation, which is
`premises.py::premise_work_invited` (625):

    refuted = <artifacts under this problem whose status is REFUTED>
    return refuted >= PREMISE_INVITE_AFTER      # == 2, premises.py:68
    ... and False if any attribution already stands for that problem

So the gate is a per-PROBLEM refuted count. This probe replays each committed
root with the harness's own reader and reports, per problem, how many refuted
artifacts it accumulated -- i.e. whether the gate could have opened at all.

Usage: q1_invite_gate.py <root> [<root> ...]
"""
import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, "src")
from deepreason.harness import Harness  # noqa: E402
from deepreason.premises import PREMISE_INVITE_AFTER, standing_attributions  # noqa: E402


def report(root: pathlib.Path) -> dict:
    h = Harness(root, read_only=True)
    st = h.state
    addr = dict(st.addr) if not isinstance(st.addr, dict) else dict(st.addr)
    per_problem_total = Counter()
    per_problem_refuted = Counter()
    for aid, pid in st.addr:
        per_problem_total[pid] += 1
        if str(st.status.get(aid, "")).endswith("REFUTED"):
            per_problem_refuted[pid] += 1
    try:
        standing = [(a, p) for a, p, _ in standing_attributions(h)]
    except Exception as exc:  # pragma: no cover - diagnostic only
        standing = f"unavailable: {exc!r}"
    open_problems = {p: c for p, c in per_problem_refuted.items() if c >= PREMISE_INVITE_AFTER}
    return {
        "root": root.name,
        "invite_threshold": PREMISE_INVITE_AFTER,
        "problems": len(per_problem_total),
        "artifacts_addressed": sum(per_problem_total.values()),
        "refuted_total": sum(per_problem_refuted.values()),
        "refuted_by_problem": dict(per_problem_refuted.most_common()),
        "artifacts_by_problem": dict(per_problem_total.most_common()),
        "max_refuted_on_one_problem": max(per_problem_refuted.values(), default=0),
        "problems_at_or_above_threshold": open_problems,
        "critic_citation_channel_ever_open": bool(open_problems),
        "standing_attributions": standing,
    }


if __name__ == "__main__":
    print(json.dumps([report(pathlib.Path(a)) for a in sys.argv[1:]], indent=2, sort_keys=True))
