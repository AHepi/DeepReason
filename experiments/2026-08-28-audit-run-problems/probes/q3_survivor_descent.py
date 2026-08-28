#!/usr/bin/env python3
"""Q3 probe C -- where accepted work is ADDRESSED, by role and by problem.

CLAUDE.md's census invariant: import-role admission records never count as
survivors, and the seed question wins scheduler rank ties. This counts accepted
artifacts by provenance role and by the problem they are addressed to, so
"off-subject" is attributed to a generator rather than asserted from prose.

Usage: q3_survivor_descent.py <root> [<root> ...]
"""
import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, "src")
from deepreason.harness import Harness  # noqa: E402


def report(root: pathlib.Path) -> dict:
    h = Harness(root, read_only=True)
    st = h.state
    addr = {aid: pid for aid, pid in st.addr}
    by_role = Counter()
    accepted_by_role = Counter()
    accepted_by_problem_role = Counter()
    for aid, artifact in st.artifacts.items():
        role = getattr(getattr(artifact, "provenance", None), "role", None) or "?"
        by_role[role] += 1
        if str(st.status.get(aid, "")).endswith("ACCEPTED"):
            accepted_by_role[role] += 1
            pid = addr.get(aid)
            bucket = "seed" if (pid or "").startswith("question-") else (
                (pid or "unaddressed").split(":", 1)[0] if pid else "unaddressed")
            accepted_by_problem_role[f"{role}/{bucket}"] += 1
    return {
        "root": root.name,
        "artifacts_total": len(st.artifacts),
        "by_role": dict(by_role.most_common()),
        "accepted_by_role": dict(accepted_by_role.most_common()),
        "accepted_conjecturer_by_problem_class": {
            k.split("/", 1)[1]: v for k, v in accepted_by_problem_role.items()
            if k.startswith("conjecturer/")
        },
        "accepted_by_role_and_problem_class": dict(accepted_by_problem_role.most_common()),
    }


if __name__ == "__main__":
    print(json.dumps([report(pathlib.Path(a)) for a in sys.argv[1:]], indent=2))
