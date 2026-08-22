"""Consequence probe (READ-ONLY) for the parked finding P1.

`measures/reach.py::_substantive` is shared by two consumers: the reach
sweep, and `rules/warrants.py::formally_backed` (the prose-immunity guard).
`programs.PROGRAMS` declares 13 programs `class_="structural"`;
`_STRUCTURAL_PROGRAMS` hand-lists 8 of them. This measures what the five
missing ones do in the committed corpus: how many candidate artifacts are
formally backed (prose-immune) whose ONLY substantive commitments are
declared-structural programs the reach set does not know about.

Never writes; opens every root read-only and calls the real
`formally_backed`.
"""

import collections
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]


def probe(root: pathlib.Path) -> dict:
    from deepreason.harness import Harness
    from deepreason.measures.reach import _STRUCTURAL_PROGRAMS, _substantive
    from deepreason.ontology.state import Status
    from deepreason.programs import programs_by_class
    from deepreason.rules.warrants import formally_backed

    declared = set(programs_by_class().get("structural", ()))
    widened = _STRUCTURAL_PROGRAMS | declared

    harness = Harness(root, read_only=True)
    state = harness.state
    addressed = {aid for aid, _pid in state.addr}
    counts = collections.Counter()
    culprits = collections.Counter()

    for aid, status in state.status.items():
        if status != Status.ACCEPTED or aid not in addressed:
            continue
        counts["candidates"] += 1
        backed = formally_backed(harness, aid)
        counts["formally_backed"] += bool(backed)
        if not backed:
            continue
        substantive = [
            cid for cid in state.artifacts[aid].interface.commitments
            if (k := harness.commitments.get(cid)) is not None and _substantive(k)
        ]
        under_widened = [
            cid for cid in substantive
            if (k := harness.commitments[cid]).eval.partition(":")[2] not in widened
            or not k.eval.startswith("program:")
        ]
        if not under_widened:
            counts["backed_only_by_declared_structural"] += 1
            for cid in substantive:
                culprits[harness.commitments[cid].eval] += 1
    return {"root": str(root.relative_to(REPO)), **dict(counts),
            "_culprits": dict(culprits)}


if __name__ == "__main__":
    roots = sorted({p.parent for p in (REPO / "experiments").rglob("log.jsonl")})
    rows, totals, culprits = [], collections.Counter(), collections.Counter()
    for root in roots:
        try:
            row = probe(root)
        except Exception as error:
            row = {"root": str(root.relative_to(REPO)),
                   "open_error": f"{type(error).__name__}: {error}"}
        rows.append(row)
        for key, value in row.items():
            if isinstance(value, int):
                totals[key] += value
        for key, value in (row.get("_culprits") or {}).items():
            culprits[key] += value
    path = pathlib.Path(__file__).with_name("probe_immunity.json")
    path.write_text(json.dumps(
        {"roots": rows, "totals": dict(sorted(totals.items())),
         "culprit_evals": dict(culprits.most_common())}, indent=2) + "\n")
    print("=== TOTALS ===")
    for key, value in sorted(totals.items()):
        print(f"  {key:44} {value}")
    print("=== culprit commitment evals ===")
    for key, value in culprits.most_common(10):
        print(f"  {value:8} {key[:120]}")
    print(f"\nwrote {path}")
