#!/usr/bin/env python3
"""OFFLINE control: the amendment's attached source must NOT satisfy the
seed problem's subject predicates by itself.

Why this check exists. Epoch 3's second lineage is created by an amendment
that attaches a document (SPEC.md M4/M5: no other amend surface produces a
root `continue` accepts). If that document's own text already satisfied
`uhi-energy-balance@v1`, `uhi-nocturnal-release@v1` and
`uhi-cross-city-modulator@v1`, then a lineage-2 artifact could clear the
seed problem's battery by QUOTING the attachment, and the reach hit would be
unattributable -- the measure would be reading the operator's document back,
not the model's own account. Cf. the census anti-pattern
(`relation_form_commitment`), where a criterion was satisfiable without
saying anything about the subject: this is the mirror failure, a SOURCE that
satisfies the criteria without the model reasoning at all.

The check is deliberately one-sided. It requires at least one FAIL, and
reports all three verdicts either way. A supplement that passes all three
is a control failure and the ladder refuses to launch on it.

No provider call, no Harness left behind, nothing written into any other
tranche's directory.

Usage:  python preflight_supplement.py [supplement.md]
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile

TRANCHE = pathlib.Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
REACH_RICH = REPO / "experiments" / "2026-08-22-live-reach-rich-run"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REACH_RICH))

from build_manifest import CRITERIA  # noqa: E402  (the three under test)
from deepreason import programs  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.ontology import Provenance  # noqa: E402

DEFAULT_SUPPLEMENT = TRANCHE / "supplement-nocturnal-collapse.md"


def main() -> int:
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) == 2 else DEFAULT_SUPPLEMENT
    if len(sys.argv) > 2:
        print("usage: preflight_supplement.py [supplement.md]", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")

    root = pathlib.Path(tempfile.mkdtemp(prefix="epoch3-supplement-"))
    try:
        harness = Harness(root)
        artifact = harness.create_artifact(text, provenance=Provenance(role="user"))
        rows = []
        for commitment in CRITERIA:
            harness.register_commitment(commitment)
            verdict, trace = programs.evaluate(commitment, artifact, harness.blobs)
            row = {
                "id": commitment.id,
                "evaluable": programs.evaluable(commitment),
                "verdict": verdict,
            }
            if "error" in trace:
                row["error"] = trace["error"][:200]
            rows.append(row)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    passing = [row["id"] for row in rows if row["verdict"] == programs.PASS]
    report = {
        "criteria": rows,
        "passing": passing,
        "supplement": str(path.relative_to(REPO)),
        "supplement_bytes": len(text.encode("utf-8")),
        "control_holds": len(passing) < len(rows),
    }
    (TRANCHE / "preflight_supplement.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    for row in rows:
        print(f"{row['id']:32} evaluable={row['evaluable']!s:5} verdict={row['verdict']}")
    print(f"\nsupplement: {report['supplement']} ({report['supplement_bytes']} bytes)")
    print(f"passing the seed's subject predicates: {passing or 'none'}")
    print(f"control holds (not all three pass): {report['control_holds']}")
    return 0 if report["control_holds"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
