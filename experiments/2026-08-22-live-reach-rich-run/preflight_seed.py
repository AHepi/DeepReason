#!/usr/bin/env python3
"""OFFLINE preflight for the frozen workload (no provider calls).

Three things this proves before a token is spent:

  1. ``seed_reasoning_workload`` actually attaches this tranche's three
     subject criteria to the seeded problem (plus the ``reasoning-envelope-wf``
     gate it pins unconditionally), so the criteria under test really do
     reach the run.
  2. Each predicate survives ``programs._validate_predicate`` and evaluates
     to a verdict rather than an error -- a predicate that raises is a
     silent FAIL on every artifact (programs.py:437).
  3. The criteria DISCRIMINATE. Each is evaluated against an on-subject
     answer and an off-subject one. A criterion that passes both is a form
     gate wearing a subject's clothes, which is the exact anti-pattern
     the census diagnosed (relation_form_commitment).

Usage:  python preflight_seed.py <root-with-problem.json>
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

from deepreason import programs  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.ontology import Provenance  # noqa: E402
from deepreason.workloads.text import (  # noqa: E402
    ReasoningWorkloadSpec,
    seed_reasoning_workload,
)

ON_SUBJECT = (
    "Cities stay warmer after sunset because their surfaces have far higher "
    "heat capacity than soil and vegetation, and a low albedo, so they store "
    "solar gain through the day and release it slowly at night. A reduced "
    "sky view factor inside street canyons traps outgoing longwave "
    "radiation, and the loss of evapotranspiration removes the latent-heat "
    "sink that cools rural air. The gap is larger where built density is "
    "greater and vegetation is scarcer."
)
OFF_SUBJECT = (
    "The claim follows from the premises by a straightforward derivation. "
    "Its scope covers the stated cases and excludes the rest. It would be "
    "refuted if the derivation were shown to be invalid, and the mechanism "
    "is described in full above."
)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: preflight_seed.py <root>", file=sys.stderr)
        return 2
    payload = json.loads((pathlib.Path(sys.argv[1]) / "problem.json").read_text())
    spec = ReasoningWorkloadSpec.model_validate(payload)

    root = pathlib.Path(tempfile.mkdtemp(prefix="reach-preflight-"))
    try:
        harness = Harness(root)
        problem = seed_reasoning_workload(harness, spec)
        report = {
            "problem_id": problem.id,
            "seeded_criteria": list(problem.criteria),
            "criteria": [],
        }
        for cid in problem.criteria:
            kappa = harness.commitments[cid]
            row = {"id": cid, "eval": kappa.eval, "evaluable": programs.evaluable(kappa)}
            for label, text in (("on_subject", ON_SUBJECT), ("off_subject", OFF_SUBJECT)):
                artifact = harness.create_artifact(
                    text, provenance=Provenance(role="user")
                )
                verdict, trace = programs.evaluate(kappa, artifact, harness.blobs)
                row[label] = verdict
                if "error" in trace:
                    row[f"{label}_error"] = trace["error"][:200]
            row["discriminates"] = (
                row["on_subject"] == programs.PASS
                and row["off_subject"] != programs.PASS
            )
            report["criteria"].append(row)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    out = TRANCHE / "preflight_seed.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for row in report["criteria"]:
        print(
            f"{row['id']:32} evaluable={row['evaluable']!s:5} "
            f"on={row['on_subject']:8} off={row['off_subject']:8} "
            f"discriminates={row['discriminates']}"
        )
    print(f"\nseeded criteria: {report['seeded_criteria']}")
    print(f"wrote {out}")
    # The wf gate is expected to fail BOTH samples (neither is envelope
    # JSON); only the three subject criteria are required to discriminate.
    subject = [r for r in report["criteria"] if r["id"] != "reasoning-envelope-wf"]
    return 0 if subject and all(r["discriminates"] for r in subject) else 1


if __name__ == "__main__":
    raise SystemExit(main())
