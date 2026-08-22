"""Before/after consequence measurement for the reach structural-set fix.

Runs the COMMITTED probe from
``experiments/2026-08-21-measure-reach-firing/probe_immunity.py`` verbatim --
its ``probe()`` is imported, never copied -- and writes the result into THIS
tranche's directory so the 08-21 artifact it re-runs is never overwritten.

The decisive number is ``formally_backed`` per root: the fix narrows what
``_substantive`` admits, and ``rules/warrants.py::formally_backed`` shares
that predicate, so a moved count would mean a committed root's prose-immunity
verdict changed. ``backed_only_by_declared_structural`` = 0 in the committed
pre-fix probe predicts it cannot.

Usage:  python immunity_delta.py <before|after>
"""

import collections
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROBE = REPO / "experiments/2026-08-21-measure-reach-firing/probe_immunity.py"

spec = importlib.util.spec_from_file_location("_probe_immunity", PROBE)
probe_immunity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe_immunity)


def main(label: str) -> int:
    roots = sorted({p.parent for p in (REPO / "experiments").rglob("log.jsonl")})
    rows, totals, culprits = [], collections.Counter(), collections.Counter()
    for root in roots:
        try:
            row = probe_immunity.probe(root)
        except Exception as error:
            row = {"root": str(root.relative_to(REPO)),
                   "open_error": f"{type(error).__name__}: {error}"}
        rows.append(row)
        for key, value in row.items():
            if isinstance(value, int):
                totals[key] += value
        for key, value in (row.get("_culprits") or {}).items():
            culprits[key] += value

    from deepreason.measures.reach import _STRUCTURAL_PROGRAMS
    from deepreason.programs import programs_by_class
    declared = set(programs_by_class().get("structural", ()))

    out = HERE / f"immunity_{label}.json"
    out.write_text(json.dumps({
        "label": label,
        "declared_structural": sorted(declared),
        "reach_structural_set": sorted(_STRUCTURAL_PROGRAMS),
        "declared_minus_reach": sorted(declared - set(_STRUCTURAL_PROGRAMS)),
        "roots": rows,
        "totals": dict(sorted(totals.items())),
        "culprit_evals": dict(culprits.most_common()),
    }, indent=2) + "\n")
    print(f"=== {label.upper()} TOTALS ===")
    for key, value in sorted(totals.items()):
        print(f"  {key:44} {value}")
    print(f"declared_minus_reach: {sorted(declared - set(_STRUCTURAL_PROGRAMS))}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "before"))
