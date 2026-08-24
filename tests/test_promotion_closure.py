"""Remark 9.5's default-consult closure, both halves (S9, R7, R12).

    "Criteria instantiated at registration generate demonstrative program
    warrants BEFORE the renderer's next consultation; the renderer consults
    only assertions addressed to promotion problems."

The hole this shuts is specific and would otherwise be silent: a frame
assertion nobody happened to attack is ACCEPTED, and an accepted assertion
addressed to a promotion problem is CONSULTED -- so an unexamined claim would
frame every problem in its scope simply by having been registered first. The
closure is not a new rule; it is an ORDER. The criteria fire, a `fail` mints a
demonstrative warrant through the tree's one warrant constructor, the assertion
stops being unrefuted, and `consultability_of` declines it.

`overrun` mints NOTHING, and that asymmetry is the whole reason the criteria
distinguish the two verdicts: a criterion that could not be evaluated must not
refuse a candidate by default, or "we could not check" becomes a refutation.
"""

import pytest

from deepreason.calculus import nomination, operations, promotion
from deepreason.calculus.standing import (
    FRAME_NOT_ADDRESSED_TO_PROMOTION,
    FRAME_NOT_UNREFUTED,
    consultability_of,
    consulted,
)
from deepreason.config import Config
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    SpawnTrigger,
    Status,
)

SCOPE_ALL = {"schema": "declarative-scope.v1", "predicate": {"const": True}}


def _problem(harness, pid, *, trigger=SpawnTrigger.SEED, criteria=()):
    return harness.register_problem(
        Problem(
            id=pid, description=f"problem {pid}", criteria=list(criteria),
            provenance=ProblemProvenance.model_validate(
                {"trigger": trigger, "from": []}
            ),
        )
    )


@pytest.fixture
def nominated(harness):
    kappa = Commitment(id="k-left", eval="predicate:len(content) > 0")
    harness.register_commitment(kappa)
    left = _problem(harness, "question-left", criteria=[kappa.id])
    right = _problem(harness, "question-right", criteria=[kappa.id])
    subject = harness.create_artifact(
        "b: one account of both domains",
        interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer"), problem_id=left.id,
    )
    harness.record_measure(reach={subject.id: 1.0}, addr=[(subject.id, right.id)])
    problem = nomination.nominate(harness, Config(K_FRAME=2))[0]
    certificate = next(
        a for a in harness.state.artifacts.values()
        if "claim:reach-certificate-wf@v1" in a.interface.commitments
    )
    return subject, problem, certificate


def _assertion(harness, problem, subject_ref, cases):
    return operations.file_frame_assertion(
        harness, problem=problem, subject_ref=subject_ref, scope=SCOPE_ALL,
        departure_protocol="cite this id", reach_case_refs=list(cases),
    )


# --- half one: only assertions addressed to a promotion problem are consulted -


def test_an_assertion_registered_elsewhere_is_an_ordinary_artifact(nominated, harness):
    """R12's first clause. Registered against an ordinary problem, it is
    accepted, it is on the graph, and the renderer does not see it."""
    subject, problem, certificate = nominated
    ordinary = harness.state.problems["question-left"]
    stray = _assertion(harness, ordinary, subject.id, [certificate.id])
    assert harness.state.status[stray.id] is Status.ACCEPTED
    verdict = consultability_of(harness, stray.id)
    assert not verdict.consultable
    assert verdict.code == FRAME_NOT_ADDRESSED_TO_PROMOTION
    assert stray.id not in {g.assertion_id for g in consulted(harness)}


# --- half two: an UNATTACKED assertion does not silently frame its scope ------


def test_an_unattacked_assertion_does_not_frame_because_its_criteria_fire_first(
    nominated, harness
):
    """R12's second clause, and the hole the closure exists to shut.

    Nothing attacks this assertion. Before the sweep it is accepted and
    therefore consulted -- which is the silent framing. After the sweep it is
    refuted by a demonstrative program warrant its own problem's criteria
    minted, and the renderer declines it.
    """
    subject, problem, certificate = nominated
    # No reach case at all: `promotion_reach_integrity` fails on it.
    naked = _assertion(harness, problem, subject.id, [])
    assert harness.state.status[naked.id] is Status.ACCEPTED
    assert consultability_of(harness, naked.id).consultable, (
        "before the sweep an unattacked assertion frames its scope -- this is "
        "the condition Remark 9.5 exists to remove"
    )

    minted = promotion.promotion_criteria_sweep(harness, Config())
    assert minted, "the criteria fired"
    assert harness.state.status[naked.id] is Status.REFUTED
    verdict = consultability_of(harness, naked.id)
    assert not verdict.consultable
    assert verdict.code == FRAME_NOT_UNREFUTED
    assert naked.id not in {g.assertion_id for g in consulted(harness)}


def test_the_warrant_is_demonstrative_and_names_the_criterion(nominated, harness):
    """The refusal is legible: a reader asking WHY an assertion is not framing
    gets a criterion id, not a bare status."""
    from deepreason.ontology.warrant import WarrantType

    subject, problem, certificate = nominated
    naked = _assertion(harness, problem, subject.id, [])
    promotion.promotion_criteria_sweep(harness, Config())
    against = [w for w in harness.warrants.values() if w.target == naked.id]
    assert against
    assert all(w.type is WarrantType.DEMONSTRATIVE for w in against)
    assert any(promotion.REACH_INTEGRITY in (w.commitment or "") for w in against)


def test_an_overrun_criterion_mints_nothing(nominated, harness):
    """The asymmetry that makes the closure honest. `subject_demarcation`
    overruns here -- the `load` reading needs the variator seat and nomination
    had none -- and an unobtainable verdict is pending, never a refutation
    (`DR-SEAM-evaluation-x-rules`: only a `fail` becomes an epistemic move)."""
    subject, problem, certificate = nominated
    candidate = _assertion(harness, problem, subject.id, [certificate.id])
    promotion.promotion_criteria_sweep(harness, Config())
    against = [w for w in harness.warrants.values() if w.target == candidate.id]
    assert not any(
        promotion.SUBJECT_DEMARCATION in (w.commitment or "") for w in against
    ), [w.commitment for w in against]


def test_the_sweep_is_idempotent(nominated, harness):
    subject, problem, certificate = nominated
    _assertion(harness, problem, subject.id, [])
    first = promotion.promotion_criteria_sweep(harness, Config())
    assert first
    assert promotion.promotion_criteria_sweep(harness, Config()) == []


def test_the_sweep_leaves_non_frame_artifacts_alone(nominated, harness):
    """The promotion problem's own paperwork -- its companion subject, the
    certificate -- is addressed to it and makes no frame claim. A sweep that
    refused those would mint warrants against the problem's own evidence."""
    subject, problem, certificate = nominated
    operations.ensure_problem_subject(harness, problem)
    promotion.promotion_criteria_sweep(harness, Config())
    for aid in (certificate.id,):
        assert not [w for w in harness.warrants.values() if w.target == aid]
