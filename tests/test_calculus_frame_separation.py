"""Frame-separation: Definition 7.2, and the precondition Theorem 7.3 needs.

Regression (v2 calculus program, Rung 3b, R43/R64). The mention law is
NECESSARY BUT NOT SUFFICIENT for wound persistence: in a globally connected
adjudication graph a new attack on the subject reaches the assertion through
pre-existing paths and moves its label indirectly. These tests EXHIBIT the
graph condition that closes that door -- disjoint components -- rather than
asserting the mention and inferring the rest.

R64's other half is a claim about what does NOT happen: a violation yields the
typed diagnostic and nothing else. A fabricated verdict would make the record
lie about epistemics in order to report a bug.
"""

from deepreason.calculus.separation import (
    FRAME_ENDPOINT_UNREGISTERED,
    FRAME_NOT_SEPARATED,
    adjudication_component,
    consultability,
    frame_separated,
)
from deepreason.ontology import Interface, Provenance, Ref, Status
from deepreason.ontology.artifact import RefRole
from tests.conftest import attack


def _art(harness, text, refs=()):
    return harness.create_artifact(
        text,
        interface=Interface(refs=list(refs)),
        provenance=Provenance(role="critic"),
    )


def _capture(harness):
    """Everything a manufactured refutation would have to move.

    Compared whole: an assertion naming only one of these would pass while the
    check quietly minted one of the others.
    """
    return (
        sorted(tuple(pair) for pair in harness.state.att),
        sorted(tuple(pair) for pair in harness.state.dep),
        dict(harness.state.status),
        sorted(harness.warrants),
        len((harness.root / "log.jsonl").read_text().splitlines()),
    )


def test_a_mention_leaves_the_assertion_and_its_subject_separated(harness):
    """R1/R2/R6. Mention edges need no filter to be excluded from Q_L:
    `build_dep` emits `dep` from `RefRole.DEPENDENCE` and from nothing else, so
    a mention produces no edge in either relation."""
    subject = _art(harness, "X: the tides are lunar")
    assertion = _art(
        harness,
        "rho: this problem presupposes X",
        refs=[Ref(target=subject.id, role=RefRole.MENTION)],
    )

    assert adjudication_component(harness, assertion.id) == {assertion.id}
    assert adjudication_component(harness, subject.id) == {subject.id}
    assert frame_separated(harness, assertion.id, subject.id)
    assert consultability(harness, assertion.id, subject.id).consultable


def test_wound_persistence_holds_when_the_separation_does(harness):
    """R6, Theorem 7.3 in full: L' extends L by exactly a new critic component
    whose only connection to the old graph is an attack on b, and l(f) does not
    move -- measured against the label f actually held before the extension."""
    subject = _art(harness, "X: the tides are lunar")
    assertion = _art(
        harness,
        "rho: this problem presupposes X",
        refs=[Ref(target=subject.id, role=RefRole.MENTION)],
    )
    before = dict(harness.state.status)

    critic, _nu = attack(harness, subject.id, "the tides are solar")

    assert harness.state.status[subject.id] == Status.REFUTED
    assert harness.state.status[assertion.id] == before[assertion.id] == Status.ACCEPTED
    assert adjudication_component(harness, subject.id) == {subject.id, critic.id}
    assert adjudication_component(harness, assertion.id) == {assertion.id}
    assert frame_separated(harness, assertion.id, subject.id)


def test_a_reach_case_that_depends_on_the_subject_is_unconsultable(harness):
    """R1/R3/R4/R7, the violation Definition 7.2's own sentence names: "reach
    records supporting f must mention, rather than depend on, the subject".
    M depends on X and rho depends on M, so undirected rho-M-X is one component
    while the mention law is fully obeyed -- the gap this rung closes."""
    subject = _art(harness, "X: the tides are lunar")
    case = _art(
        harness,
        "M: the reach case for rho",
        refs=[Ref(target=subject.id, role=RefRole.DEPENDENCE)],
    )
    assertion = _art(
        harness,
        "rho: this problem presupposes X, on the strength of M",
        refs=[
            Ref(target=subject.id, role=RefRole.MENTION),
            Ref(target=case.id, role=RefRole.DEPENDENCE),
        ],
    )
    before = _capture(harness)

    verdict = consultability(harness, assertion.id, subject.id)

    assert verdict.consultable is False
    assert verdict.code == FRAME_NOT_SEPARATED
    assert set(verdict.detail) == {assertion.id, case.id, subject.id}
    assert not frame_separated(harness, assertion.id, subject.id)
    assert [r.role for r in assertion.interface.refs if r.target == subject.id] == [
        RefRole.MENTION
    ]
    assert _capture(harness) == before  # R64: the diagnostic is all that happened


def test_an_unregistered_endpoint_is_unconsultable_not_silently_fine(harness):
    """R3. A literal component reading calls an assertion whose subject does
    not exist SEPARATED, hence consultable. "We could not check" must never
    look like "we checked and it was fine" (`premises.py::premise_rent_sweep`
    records the same rule for demarcation)."""
    subject = _art(harness, "X: the tides are lunar")
    before = _capture(harness)

    verdict = consultability(harness, "sha256:not-registered", subject.id)

    assert verdict.consultable is False
    assert verdict.code == FRAME_ENDPOINT_UNREGISTERED
    assert verdict.detail == ("sha256:not-registered",)
    assert _capture(harness) == before
