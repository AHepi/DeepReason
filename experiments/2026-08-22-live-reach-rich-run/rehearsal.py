#!/usr/bin/env python3
"""OFFLINE dress rehearsal for the reach-rich live run (no provider calls).

Purpose: before spending a single token, establish which problem/artifact
SHAPES the current code can actually put through ``measures/reach.py::
reach_sweep``. The census tranche
(experiments/2026-08-21-measure-reach-firing/) proved reach fires on no
committed root and predicted that subject-substantive seed criteria would
move pairs out of E4. That prediction is about CRITERIA. This rehearsal
tests the CARRIER: which artifacts a text run can produce that do not
already carry the foreign problem's battery.

Each scenario builds a real ``Harness`` on a throwaway root, registers real
``Commitment``/``Problem`` objects through the real registration path,
creates real artifacts through ``compile_interface`` (so ``carried`` is
whatever the production path would give them), and calls the REAL
``reach_sweep``. Nothing here is a stub and nothing is asserted; the script
prints the exit each pair takes.

Usage:  python rehearsal.py            (writes rehearsal.json next to it)
"""

from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from deepreason import programs  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.measures.reach import reach_sweep  # noqa: E402
import deepreason.measures.reach as _reach  # noqa: E402
from deepreason.ontology import (  # noqa: E402
    Commitment,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
)
from deepreason.ontology.commitment import Budget  # noqa: E402
from deepreason.workloads.models import compile_interface  # noqa: E402
from deepreason.measures.hv import hv_floor_commitment  # noqa: E402
from deepreason.unification.isolation import (  # noqa: E402
    lineage_ref_commitment,
    relation_form_commitment,
)
from deepreason.config import Config  # noqa: E402

# The three commitments rules/spawn.py actually pins on an auto-spawned
# problem. Taken from the production constructors, not retyped, so the
# rehearsal cannot drift from what a live run mints.
RELATION_FORM = relation_form_commitment()
HV_FLOOR = hv_floor_commitment(Config())
LINEAGE = lineage_ref_commitment(["a" * 64])

# The exact commitment seed_reasoning_workload mints, byte for byte
# (workloads/text.py:295-299). A rehearsal that used a different budget
# would be rehearsing a different run.
WF = Commitment(
    id="reasoning-envelope-wf",
    eval="program:reasoning-envelope-wf",
    budget=Budget(steps=10_000, time_ms=2_000, extra={"max_chars": 64_000}),
)

# A minimal ReasoningEnvelopeV1 body about the rehearsal's stand-in subject.
# Envelope JSON is what rules/conj.py:2088 stores for a problem whose
# criteria include reasoning-envelope-wf, and prose is what it stores for
# every other problem (conj.py:1462 sets `reasoning` from problem.criteria).
ENVELOPE = json.dumps(
    {
        "schema": "deepreason-reasoning-envelope-v1",
        "claim": (
            "City centres stay warmer at night because dense masonry and "
            "asphalt store daytime solar gain and release it after sunset."
        ),
        "mechanism": (
            "High thermal mass and low albedo raise daytime storage; a "
            "reduced sky view factor traps outgoing longwave radiation, and "
            "the absence of evapotranspiration removes the latent-heat sink."
        ),
        "premises": [{"claim": "Urban surfaces have higher heat capacity."}],
        "counterconditions": [
            {"case": "an arid city with no vegetation shows no gap", "eval": "observation"}
        ],
    }
)
PROSE = (
    "Relation kind: shared mechanism. Both accounts turn on the same "
    "nocturnal release of stored daytime solar gain: urban surfaces combine "
    "high thermal mass with low albedo, so the same energy store drives both "
    "the centre-versus-edge gradient and the after-sunset cooling lag. "
    "REFUTED IF a city whose surfaces have low thermal mass shows the same "
    "night-time gap."
)


def _predicate(name: str, expr: str) -> Commitment:
    return Commitment(id=name, eval=f"predicate:{expr}")


P_SEED = [
    _predicate(
        "uhi-energy-balance@r1",
        "sum(1 for t in ('albedo','thermal mass','heat capacity',"
        "'evapotranspiration','longwave','sky view','anthropogenic heat',"
        "'latent heat','emissivity') if t in content.lower()) >= 2",
    ),
]
P_OTHER = [
    _predicate(
        "uhi-nocturnal-release@r1",
        "('night' in content.lower() or 'nocturnal' in content.lower()) and "
        "any(t in content.lower() for t in ('stored','storage','release','releas'))",
    ),
]


def _run(label: str, *, home_criteria, foreign_criteria, content, note,
         wf_structural: bool = False) -> dict:
    """One scenario: an artifact on HOME, a foreign problem FOREIGN, real sweep.

    ``wf_structural`` SIMULATES the already-parked fix P1
    (experiments/2026-08-21-measure-reach-firing/PARKED.md): programs.PROGRAMS
    declares reasoning-envelope-wf ``class_="structural"``, but
    measures/reach.py::_STRUCTURAL_PROGRAMS does not list it, so _substantive
    currently calls it substantive. The simulation is an in-process rebind of
    that module constant for the duration of one scenario -- src/ is never
    edited (git diff --stat proves it), and the rebind is undone in `finally`.
    """
    import deepreason.measures.reach as reach_module

    root = pathlib.Path(tempfile.mkdtemp(prefix="reach-rehearsal-"))
    shipped_structural = reach_module._STRUCTURAL_PROGRAMS
    if wf_structural:
        reach_module._STRUCTURAL_PROGRAMS = frozenset(
            shipped_structural | {"reasoning-envelope-wf"}
        )
    try:
        harness = Harness(root)
        # Register exactly the commitments this scenario names. An
        # UNREGISTERED criterion is invisible to both reach_sweep's
        # qualifying filter and compile_interface, so leaving one out
        # would silently rehearse a different pair.
        for kappa in {c.id: c for c in [*home_criteria, *foreign_criteria]}.values():
            harness.register_commitment(kappa)
        home = harness.register_problem(
            Problem(
                id="home",
                description="home problem",
                criteria=[c.id for c in home_criteria],
                provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
            )
        )
        foreign = harness.register_problem(
            Problem(
                id="foreign",
                description="foreign problem",
                criteria=[c.id for c in foreign_criteria],
                provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
            )
        )
        interface = compile_interface(harness, home, content)
        artifact = harness.create_artifact(
            content,
            interface=interface,
            provenance=Provenance(role="conjecturer"),
            problem_id=home.id,
        )
        # Nothing attacks it, so the grounded extension already labels it
        # ACCEPTED; assert that rather than forcing it, so the rehearsal
        # never rehearses a status the real run could not reach.
        assert harness.state.status[artifact.id] == Status.ACCEPTED, (
            harness.state.status[artifact.id]
        )
        assert (artifact.id, home.id) in harness.state.addr

        carried = set(artifact.interface.commitments)
        qualifying = [
            c for c in foreign.criteria
            if c in harness.commitments and _reach._substantive(harness.commitments[c])
        ]
        verdicts = {
            c: programs.evaluate(harness.commitments[c], artifact, harness.blobs)[0]
            for c in qualifying
        }
        novel = sorted(set(qualifying) - carried)
        hits = reach_sweep(harness)
        recorded = [
            e for e in harness.log.read()
            if e.rule.value == "Measure" and (e.state_diff.reach_set or e.state_diff.addr_add)
        ]
        if not foreign.criteria:
            exit_ = "E1 no-criteria"
        elif not qualifying:
            exit_ = "E2 non-qualifying"
        elif not novel:
            exit_ = "E3 no-novel"
        elif any(v != programs.PASS for v in verdicts.values()):
            exit_ = "E4 criterion-fail"
        elif len(qualifying) / len(foreign.criteria) < 0.5:
            exit_ = "E5 coverage/provisional"
        else:
            exit_ = "HIT full"
        return {
            "scenario": label,
            "wf_treated_structural": wf_structural,
            "note": note,
            "home_criteria": [c.id for c in home_criteria],
            "foreign_criteria": [c.id for c in foreign_criteria],
            "carried": sorted(carried),
            "qualifying": sorted(qualifying),
            "novel": novel,
            "verdicts": verdicts,
            "coverage": (len(qualifying) / len(foreign.criteria)) if foreign.criteria else None,
            "exit": exit_,
            "reach_sweep_hits": [list(h) for h in hits],
            "recorded_reach_events": len(recorded),
        }
    finally:
        reach_module._STRUCTURAL_PROGRAMS = shipped_structural
        shutil.rmtree(root, ignore_errors=True)


SCENARIOS = [
    # 1. What a single-seed text run actually contains: the seed problem
    #    carries wf + subject predicates, and every problem that inherits
    #    them (ra:) carries the SAME set.
    dict(
        label="S1 same-criteria (seed vs ra:)",
        home_criteria=[WF, *P_SEED],
        foreign_criteria=[WF, *P_SEED],
        content=ENVELOPE,
        note="ra:/succ: spawn with criteria=parent.criteria (rules/spawn.py:104,140)",
    ),
    # 2. The other half of a single-seed run: an artifact built for a
    #    conn:/integ: problem is PROSE, because conj.py sets `reasoning`
    #    from the problem's own criteria.
    dict(
        label="S2 prose artifact vs wf-carrying seed",
        home_criteria=[],
        foreign_criteria=[WF, *P_SEED],
        content=PROSE,
        note="conn:/integ: artifacts are prose (conj.py:1462); wf rejects prose",
    ),
    # 3. The shape the hypothesis needs: two problems that BOTH mint
    #    envelopes but carry DIFFERENT subject predicates.
    dict(
        label="S3 two seeds, different subject criteria",
        home_criteria=[WF, *P_SEED],
        foreign_criteria=[WF, *P_OTHER],
        content=ENVELOPE,
        note="the reach-rich shape: novel substantive criterion, survivable",
    ),
    # 4. Same as S3 but the foreign predicate is one the envelope fails —
    #    the control that proves the criteria are not vacuous.
    dict(
        label="S4 two seeds, foreign criterion unsatisfied",
        home_criteria=[WF, *P_SEED],
        foreign_criteria=[
            WF,
            _predicate("uhi-absent-subject@r1", "'photosynthesis' in content.lower()"),
        ],
        content=ENVELOPE,
        note="control: a subject predicate the artifact does not satisfy must NOT hit",
    ),
    # 5..7 — the rest of the problem inventory a live text run actually
    #        contains (rules/spawn.py): integ:, conn:, disc:. These are the
    #        only foreign problems whose criteria a text run mints without
    #        the operator, so they bound what reach could fire on.
    dict(
        label="S5 envelope vs integ: [relation-form]",
        home_criteria=[WF, *P_SEED],
        foreign_criteria=[RELATION_FORM],
        content=ENVELOPE,
        note="integ: coverage is 1/1; relation-form is a FORM gate (PARKED P2)",
    ),
    dict(
        label="S6 envelope vs conn: [hv,lineage,relation-form]",
        home_criteria=[WF, *P_SEED],
        foreign_criteria=[HV_FLOOR, LINEAGE, RELATION_FORM],
        content=ENVELOPE,
        note="conn: coverage is 1/3 -> provisional at best, never a full hit",
    ),
    # 8 — the decisive pair. A conn:/integ: candidate is PROSE and carries
    #     only its own structural battery, so the seed problem's subject
    #     predicates are novel to it. As shipped, reasoning-envelope-wf is
    #     also in the qualifying set and rejects prose outright (S8a). With
    #     the parked P1 fix applied, the qualifying set is exactly the
    #     subject predicates and the pair can survive (S8b).
    dict(
        label="S8a prose conn: candidate vs seed (as shipped)",
        home_criteria=[HV_FLOOR, LINEAGE, RELATION_FORM],
        foreign_criteria=[WF, *P_SEED, *P_OTHER],
        content=PROSE,
        note="as shipped: wf qualifies and rejects prose",
    ),
    dict(
        label="S8b prose conn: candidate vs seed (P1 applied)",
        home_criteria=[HV_FLOOR, LINEAGE, RELATION_FORM],
        foreign_criteria=[WF, *P_SEED, *P_OTHER],
        content=PROSE,
        wf_structural=True,
        note="P1 applied: qualifying = the subject predicates only, coverage 2/4",
    ),
    dict(
        label="S8c prose OFF-subject candidate vs seed (P1 applied)",
        home_criteria=[HV_FLOOR, LINEAGE, RELATION_FORM],
        foreign_criteria=[WF, *P_SEED, *P_OTHER],
        content=(
            "Relation kind: dependence. The second account depends on the "
            "first. REFUTED IF the dependence does not hold."
        ),
        wf_structural=True,
        note="control: an on-form but off-SUBJECT relation must still not hit",
    ),
    dict(
        label="S7 envelope vs disc: []",
        home_criteria=[WF, *P_SEED],
        foreign_criteria=[],
        content=ENVELOPE,
        note="disc: spawns with no criteria (rules/spawn.py:73-81)",
    ),
]


def main() -> int:
    rows = [_run(**scenario) for scenario in SCENARIOS]
    out = pathlib.Path(__file__).with_name("rehearsal.json")
    out.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    for row in rows:
        print(
            f"{row['scenario']:44} exit={row['exit']:26} "
            f"hits={len(row['reach_sweep_hits'])} "
            f"reach_events={row['recorded_reach_events']} "
            f"cov={row['coverage']} "
            f"novel={row['novel']}"
        )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
