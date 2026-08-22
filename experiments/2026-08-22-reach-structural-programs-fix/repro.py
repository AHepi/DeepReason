#!/usr/bin/env python3
"""Reproduction for DIAGNOSIS.md, offline, NO in-process rebind of anything.

Three checks, each printing PASS/FAIL against the invariant the module's own
docstring states ("structural well-formedness programs ... never ground
reach"). Every one FAILS at HEAD 0e8e0f6a6 and must PASS after the fix.

  R1  the two sets agree                 -- the drift itself
  R2  a DECLARED-structural gate is not substantive, and so does not enter
      reach_sweep's qualifying set: the S8a shape from
      experiments/2026-08-22-live-reach-rich-run/rehearsal.json, run against
      a real Harness and the real reach_sweep with NOTHING monkeypatched
  R3  a DECLARED-structural gate confers no prose immunity -- the second
      consumer, rules/warrants.py::formally_backed, which imports
      _substantive directly (warrants.py:96)

Usage:  python repro.py     (exit 0 iff all three hold; writes repro.json)
"""

from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from deepreason.harness import Harness  # noqa: E402
from deepreason.measures.reach import (  # noqa: E402
    _STRUCTURAL_PROGRAMS,
    _substantive,
    reach_sweep,
)
from deepreason import programs  # noqa: E402
from deepreason.ontology import (  # noqa: E402
    Commitment,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
)
from deepreason.ontology.commitment import Budget  # noqa: E402
from deepreason.programs import programs_by_class  # noqa: E402
from deepreason.rules.warrants import formally_backed  # noqa: E402
from deepreason.workloads.models import compile_interface  # noqa: E402
from deepreason.config import Config  # noqa: E402
from deepreason.measures.hv import hv_floor_commitment  # noqa: E402
from deepreason.unification.isolation import (  # noqa: E402
    lineage_ref_commitment,
    relation_form_commitment,
)

# The three commitments rules/spawn.py pins on an auto-spawned conn:/integ:
# problem, taken from the production constructors rather than retyped -- an
# auto-spawned candidate's home battery is exactly these, and that is what
# makes the seed's subject predicates novel to it.
RELATION_FORM = relation_form_commitment()
HV_FLOOR = hv_floor_commitment(Config())
LINEAGE = lineage_ref_commitment(["a" * 64])

# Byte-for-byte the commitment seed_reasoning_workload mints
# (workloads/text.py:295-299): a reproduction using a different budget would
# be reproducing a different run.
WF = Commitment(
    id="reasoning-envelope-wf",
    eval="program:reasoning-envelope-wf",
    budget=Budget(steps=10_000, time_ms=2_000, extra={"max_chars": 64_000}),
)
ENVELOPE = json.dumps({
    "schema": "deepreason-reasoning-envelope-v1",
    "claim": ("City centres stay warmer at night because dense masonry and "
              "asphalt store daytime solar gain and release it after sunset."),
    "mechanism": ("High thermal mass and low albedo raise daytime storage; a "
                  "reduced sky view factor traps outgoing longwave radiation."),
    "premises": [{"claim": "Urban surfaces have higher heat capacity."}],
    "counterconditions": [
        {"case": "an arid city with no vegetation shows no gap",
         "eval": "observation"}],
})
# A conn:/integ: candidate is PROSE (rules/conj.py:1462), so it carries only
# its own structural battery and the seed's subject predicates are novel to it.
PROSE = ("Relation kind: shared mechanism. Both accounts turn on the same "
         "nocturnal release of stored daytime solar gain: urban surfaces "
         "combine high thermal mass with low albedo. REFUTED IF a city whose "
         "surfaces have low thermal mass shows the same night-time gap.")
P_SEED = Commitment(id="uhi-energy-balance@r1",
                    eval="predicate:'thermal mass' in content.lower()")
P_OTHER = Commitment(id="uhi-nocturnal-release@r1",
                     eval="predicate:'nocturnal' in content.lower() or "
                          "'after sunset' in content.lower()")


def _problem(harness, pid, criteria):
    return harness.register_problem(Problem(
        id=pid, description=f"problem {pid}", criteria=[c.id for c in criteria],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))


def r1_sets_agree() -> dict:
    declared = set(programs_by_class()["structural"])
    hand = set(_STRUCTURAL_PROGRAMS)
    return {
        "check": "R1 declared structural class == reach's structural set",
        "declared_minus_reach": sorted(declared - hand),
        "reach_minus_declared": sorted(hand - declared),
        "holds": declared == hand,
    }


def r2_wf_gate_does_not_gate_reach() -> dict:
    """The S8a shape from rehearsal.json, with NOTHING monkeypatched: a prose
    conn: candidate whose own battery is the three auto-spawn structural
    commitments, against a seed problem carrying the wf gate plus two subject
    predicates the candidate genuinely satisfies."""
    root = pathlib.Path(tempfile.mkdtemp(prefix="reach-repro-"))
    try:
        harness = Harness(root)
        for kappa in (RELATION_FORM, HV_FLOOR, LINEAGE, WF, P_SEED, P_OTHER):
            harness.register_commitment(kappa)
        home = _problem(harness, "home", [RELATION_FORM, HV_FLOOR, LINEAGE])
        foreign = _problem(harness, "foreign", [WF, P_SEED, P_OTHER])
        artifact = harness.create_artifact(
            PROSE, provenance=Provenance(role="conjecturer"), problem_id=home.id,
            interface=compile_interface(harness, home, PROSE),
        )
        # Nothing attacks it, so the grounded extension already labels it
        # ACCEPTED. Assert rather than force: a forced status would reproduce
        # a state the real run cannot reach.
        assert harness.state.status[artifact.id] == Status.ACCEPTED
        assert (artifact.id, home.id) in harness.state.addr
        qualifying = [c for c in foreign.criteria
                      if c in harness.commitments
                      and _substantive(harness.commitments[c])]
        verdicts = {c: programs.evaluate(harness.commitments[c], artifact,
                                         harness.blobs)[0] for c in qualifying}
        hits = [tuple(h) for h in reach_sweep(harness)]
        recorded = [e for e in harness.log.read() if e.rule.value == "Measure"
                    and (e.state_diff.reach_set or e.state_diff.addr_add)]
        return {
            "check": "R2 a declared-structural gate never enters reach's "
                     "qualifying set, so it can neither ground nor veto a hit",
            "carried": sorted(artifact.interface.commitments),
            "qualifying": sorted(qualifying),
            "verdicts": verdicts,
            "coverage": len(qualifying) / len(foreign.criteria),
            "wf_in_qualifying": WF.id in qualifying,
            "hits": [list(h) for h in hits],
            "recorded_reach_events": len(recorded),
            "holds": (WF.id not in qualifying
                      and hits == [(artifact.id, foreign.id)]
                      and len(recorded) == 1),
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def r3_wf_gate_confers_no_prose_immunity() -> dict:
    """The second consumer. An artifact whose ONLY commitment is a passing
    declared-structural gate must not be prose-immune."""
    root = pathlib.Path(tempfile.mkdtemp(prefix="reach-repro-immunity-"))
    try:
        harness = Harness(root)
        harness.register_commitment(WF)
        problem = _problem(harness, "wf-only", [WF])
        artifact = harness.create_artifact(
            ENVELOPE, provenance=Provenance(role="conjecturer"),
            problem_id=problem.id,
            interface=compile_interface(harness, problem, ENVELOPE),
        )
        verdict, _ = programs.evaluate(WF, artifact, harness.blobs)
        backed = formally_backed(harness, artifact.id)
        return {
            "check": "R3 a passing declared-structural gate confers no "
                     "formally_backed prose immunity",
            "commitments": sorted(artifact.interface.commitments),
            "wf_verdict": verdict,
            "formally_backed": backed,
            "holds": verdict == "pass" and backed is False,
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    rows = [r1_sets_agree(), r2_wf_gate_does_not_gate_reach(),
            r3_wf_gate_confers_no_prose_immunity()]
    out = pathlib.Path(__file__).with_name("repro.json")
    out.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    for row in rows:
        print(f"{'HOLDS' if row['holds'] else 'VIOLATED'}  {row['check']}")
        for key, value in sorted(row.items()):
            if key not in ("check", "holds"):
                print(f"           {key} = {value}")
    print(f"\nwrote {out}")
    return 0 if all(row["holds"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
