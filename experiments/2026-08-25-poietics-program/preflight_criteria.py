#!/usr/bin/env python3
"""OFFLINE control: do P-R1's three subject predicates DISCRIMINATE?

Two questions, both answered before any provider call, because a criterion
that cannot fail measures nothing and a criterion the attached record
satisfies by itself measures the operator's document rather than the model's
reasoning (the epoch-3 tranche's `preflight_supplement.py` names that second
failure; this is its analogue for a run whose dossier IS the subject).

  CONTROL 1 -- NEGATIVE. An off-subject text must FAIL at least two of the
  three. A battery that passes prose about anything is a battery about
  nothing.

  CONTROL 2 -- DOSSIER LEAKAGE, reported not enforced. Each of the twelve
  committed record files is evaluated on its own. Where a file passes a
  criterion, an artifact could clear that criterion by quoting it. This is
  measured and written into PREREG.md rather than designed away: a term
  predicate cannot tell a quotation from an account, and pretending
  otherwise would be the stronger claim.

No provider call, no Harness left behind, nothing written outside this
tranche.

Usage:  python preflight_criteria.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile

TRANCHE = pathlib.Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(TRANCHE))

from build_manifest_pr1 import CRITERIA  # noqa: E402
from deepreason import programs  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.ontology import Provenance  # noqa: E402

OFF_SUBJECT = (
    "The urban heat island effect is driven by the thermal mass of the "
    "built environment. Cities store solar energy during the day in "
    "asphalt and concrete and release it slowly after sunset, which is "
    "why the night-time gap is larger in dense, dry cities than in green, "
    "humid ones."
)

ON_SUBJECT = (
    "A test constrains its subject only if it can fail when the subject "
    "changes; it merely describes the subject when it was written by "
    "reading the code and asserting what it does, because then it agrees "
    "by construction and goes on agreeing after the code stops being "
    "right. That condition is a property of how the guard was INSTALLED, "
    "not of what it asserts. The record's distribution is the evidence: "
    "compile.py, whose guards were installed only after each was shown to "
    "fail on a planted violation, lost 1 of 9 mutations, while every "
    "ordinarily-guarded module lost 4/4 to 6/7. The 3 of 26 headline is "
    "not established as typical, however -- it is one repository, one "
    "author, one week, and the registry size is arbitrary, so the "
    "magnitude remains untested even where the direction does not."
)


def _evaluate(label: str, text: str) -> dict:
    root = pathlib.Path(tempfile.mkdtemp(prefix="pr1-criteria-"))
    try:
        harness = Harness(root)
        artifact = harness.create_artifact(text, provenance=Provenance(role="user"))
        rows = []
        for commitment in CRITERIA:
            harness.register_commitment(commitment)
            verdict, trace = programs.evaluate(commitment, artifact, harness.blobs)
            row = {"id": commitment.id, "verdict": verdict}
            if "error" in trace:
                row["error"] = trace["error"][:200]
            rows.append(row)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    passing = [r["id"] for r in rows if r["verdict"] == programs.PASS]
    return {"label": label, "rows": rows, "passing": passing,
            "pass_count": len(passing)}


def main() -> int:
    report: dict = {"criteria": [c.id for c in CRITERIA], "cases": []}

    negative = _evaluate("off-subject control", OFF_SUBJECT)
    positive = _evaluate("on-subject control", ON_SUBJECT)
    report["cases"] += [negative, positive]

    leakage = []
    record = TRANCHE / "record"
    for path in sorted(p for p in record.rglob("*") if p.is_file()):
        text = path.read_text(encoding="utf-8", errors="replace")
        case = _evaluate(str(path.relative_to(TRANCHE)), text)
        leakage.append(case)
    report["dossier_leakage"] = leakage

    # CONTROL 1: the off-subject text must fail at least two of three, and
    # the on-subject text must pass all three, or the battery is measuring
    # form rather than subject.
    report["control_1_negative_holds"] = negative["pass_count"] <= 1
    report["control_1_positive_holds"] = positive["pass_count"] == len(CRITERIA)
    report["control_1_holds"] = (
        report["control_1_negative_holds"] and report["control_1_positive_holds"]
    )
    # CONTROL 2 is REPORTED, never enforced.
    report["dossier_files_passing_all_three"] = [
        c["label"] for c in leakage if c["pass_count"] == len(CRITERIA)
    ]
    report["dossier_max_pass_count"] = max(c["pass_count"] for c in leakage)

    (TRANCHE / "preflight_criteria.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    for case in (negative, positive):
        print(f"{case['label']:24} passing {case['pass_count']}/{len(CRITERIA)} "
              f"{case['passing'] or '-'}")
    print()
    print("dossier leakage (a file passing a criterion is a criterion an "
          "artifact could clear by quoting):")
    for case in leakage:
        print(f"  {case['label']:52} {case['pass_count']}/{len(CRITERIA)} "
              f"{case['passing'] or '-'}")
    print()
    print(f"CONTROL 1 negative (off-subject fails >=2): "
          f"{report['control_1_negative_holds']}")
    print(f"CONTROL 1 positive (on-subject passes 3/3): "
          f"{report['control_1_positive_holds']}")
    print(f"files passing all three: "
          f"{report['dossier_files_passing_all_three'] or 'none'}")
    return 0 if report["control_1_holds"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
