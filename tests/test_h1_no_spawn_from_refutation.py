"""H1: a failed conjecture mints nothing.

Regression (v2 calculus program, Rung 3a). `rules/spawn.py::scan_spawns` used
to mint a SUCCESSOR problem for every REFUTED artifact addressing a problem.
That is the doctrine defect H1 deletes: refutation may redirect ATTENTION, and
a problem is replaced only by an adjudicated `translate` resolution.

The decisive test is the external advice's, verbatim in shape — refute, rescan,
assert the frontier is unchanged. A deletion is exactly the change whose test
passes vacuously, so this file also MUTATION-PROVES itself: it reinstates the
old loop in-process and asserts the same test then fails.
"""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import (
    Commitment,
    Problem,
    ProblemProvenance,
    SpawnTrigger,
    Status,
)
from deepreason.rules.spawn import scan_spawns
from tests.conftest import attack


def _seeded(tmp_path):
    """A problem with one addressed candidate, and a criterion it passes."""
    harness = Harness(tmp_path / "run")
    harness.register_commitment(
        Commitment(id="k-moon", eval="predicate:'moon' in content")
    )
    harness.register_problem(
        Problem(
            id="pi-tides",
            description="explain the tides",
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    candidate = harness.create_artifact("the moon pulls the sea", problem_id="pi-tides")
    return harness, candidate


def test_refutation_alone_cannot_grow_the_problem_frontier(tmp_path):
    """The advice's decisive regression. Nothing about it is subtle."""
    harness, candidate = _seeded(tmp_path)
    scan_spawns(harness, Config())

    before = set(harness.state.problems)
    attack(harness, candidate.id, "ignores solar forcing")
    assert harness.state.status[candidate.id] == Status.REFUTED
    scan_spawns(harness, Config())

    assert set(harness.state.problems) == before


def test_the_regression_would_catch_the_old_loop(tmp_path):
    """The mutation proof.

    Reinstates the deleted branch in-process — the same code, minting the same
    `succ:<id>` problem — and asserts the regression above FAILS against it. A
    test that cannot fail is not a regression, and for a deletion that is the
    easiest failure mode to ship by accident.
    """
    harness, candidate = _seeded(tmp_path)
    scan_spawns(harness, Config())
    before = set(harness.state.problems)
    attack(harness, candidate.id, "ignores solar forcing")

    # The deleted loop, restored verbatim in behaviour.
    state = harness.state
    for aid, pid in sorted(state.addr):
        if state.status.get(aid) != Status.REFUTED:
            continue
        parent = state.problems[pid]
        root_desc = parent.description.rsplit("Original problem: ", 1)[-1]
        harness.register_problem(
            Problem(
                id=f"succ:{aid[:12]}",
                description=(
                    f"supersede refuted candidate {aid[:12]} on {pid}. "
                    f"Original problem: {root_desc}"
                ),
                criteria=list(parent.criteria),
                # The deleted loop stamped SpawnTrigger.SUCCESSOR here. That
                # member is gone with the decommissioned pipeline that was its
                # last producer, so the mutation reinstates the loop's SHAPE --
                # a problem minted from a refutation -- which is the thing H1
                # forbids. The trigger it wore is not what the test is about.
                provenance=ProblemProvenance.model_validate(
                    {"trigger": "remove-arbitrariness", "from": [aid, pid]}
                ),
            )
        )

    assert set(harness.state.problems) != before
    assert any(p.startswith("succ:") for p in harness.state.problems)


def test_every_other_structural_trigger_still_fires(tmp_path):
    """N4 — "nothing spawns" must not be able to masquerade as success.

    The frontier still grows by every route except refutation: two survivors on
    one problem produce a discrimination problem, and the ordinary connection
    and debt sweeps are untouched code paths that this rung did not enter.
    """
    harness, first = _seeded(tmp_path)
    second = harness.create_artifact("lunar tidal forcing", problem_id="pi-tides")
    assert harness.state.status[first.id] == Status.ACCEPTED
    assert harness.state.status[second.id] == Status.ACCEPTED

    before = set(harness.state.problems)
    scan_spawns(harness, Config())
    grew = set(harness.state.problems) - before

    triggers = {harness.state.problems[pid].provenance.trigger for pid in grew}

    assert SpawnTrigger.DISCRIMINATION in triggers, "two survivors, no rivalry"
    assert triggers, "the frontier must still grow by the structural routes"
    # The route that closed cannot even be named any more: the trigger was
    # deleted with the decommissioned pipeline that was its last producer.
    assert not hasattr(SpawnTrigger, "SUCCESSOR")


def test_the_successor_trigger_is_gone_entirely(tmp_path):
    """RETIRED AND REPLACED — operator ruling 2026-08-15: "There was a website development pipeline that I decommissioned a while ago. That needs to stay decommissioned.""

    The earlier form of this test asserted that `SpawnTrigger.SUCCESSOR`
    SURVIVED, because `easy.py::seed_component` still stamped it on a
    staged-pipeline component repair problem. The operator's ruling reframed
    that producer as a REMNANT of an already-decommissioned pipeline rather
    than a feature to preserve, so the producer went, and with producers at
    zero the member went too.

    Retirement is the correct disposition here, not a weakening: the property
    the old test protected (nothing breaks by deleting the member) was true
    only while a producer existed, and asserting it now would be asserting the
    remnant back into place.
    """
    from deepreason.ontology import SpawnTrigger

    assert not hasattr(SpawnTrigger, "SUCCESSOR")
    assert "successor" not in {t.value for t in SpawnTrigger}
