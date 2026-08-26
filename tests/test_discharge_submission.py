"""Discharge-required submission (REBUILD F1, R3/R4/R6/R11).

C2 in the operator's words: "a new candidate on a problem with open criticisms
must carry, per criticism handle, a typed discharge ... A submission with
undischarged handles is returned ONCE with the open list (a typed re-ask, not a
repair grant), then accepted WITH a typed undischarged disclosure -- disclose,
never die."

The two failure modes these tests exist to prevent are opposite, and both are
easy to write by accident:

- A GATE. Refusing an undischarged candidate would be the natural reading of
  "required" and is forbidden: the all-configurations law at the submission
  boundary says disclose, never die. `test_no_candidate_is_ever_refused` and
  `test_the_second_submission_is_accepted_with_a_disclosure` pin it.
- An ACKNOWLEDGMENT. ACK-required was tested externally and LOWERED final
  accuracy (Q5, "A failed compliance control"). No kind may be satisfiable by
  merely noting a criticism. `test_no_kind_is_satisfied_by_acknowledgment`
  pins it structurally rather than by wording.
"""

import pathlib

import pytest

from deepreason.config import Config
from deepreason.discharge import (
    DISCHARGE_KIND_DECLARATIONS,
    UnknownDischargeKindError,
    open_criticisms,
    record_discharges,
    resolve_policy,
    screen_submission,
)
from deepreason.llm.wire import DischargeWireV1
from deepreason.ontology import Interface, Problem, ProblemProvenance, Provenance, Status
from deepreason.ontology.artifact import RefRole
from tests.conftest import attack

ON = "discharge-required.v1"


@pytest.fixture
def policy():
    return resolve_policy(Config(DISCHARGE_POLICY=ON))


class _Turn:
    """The minimum a submission is, from the screen's point of view.

    A stand-in rather than a real `ConjecturerTurnWireV6`, because the screen
    must work on any turn shape that has candidates carrying discharges -- v4,
    v5, v6, reasoning or compact, atomic or batched. Depending on one concrete
    wire class here would pin the screen to a contract version it has no
    business knowing about.
    """

    def __init__(self, *candidates):
        self.candidates = list(candidates)


class _Candidate:
    def __init__(self, content, discharges=()):
        self.content = content
        self.discharges = list(discharges)


def _problem(harness, pid="p-tides"):
    return harness.register_problem(
        Problem(
            id=pid, description="state the tide table for this harbour", criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def _candidate(harness, problem, text="candidate: the tide is lunar only"):
    return harness.create_artifact(
        text, problem_id=problem.id, provenance=Provenance(role="conjecturer"),
        interface=Interface(refs=[]),
    )


def _scrutiny(harness, target, text="critic: the solar contribution is omitted"):
    critic = harness.create_artifact(text, provenance=Provenance(role="critic"))
    harness.record_measure(inputs=["scrutiny", target.id, critic.id])
    return critic


def _open_problem(harness, n=1):
    problem = _problem(harness)
    target = _candidate(harness, problem)
    critics = [_scrutiny(harness, target, f"critic {i}: omission {i}") for i in range(n)]
    return problem, target, critics


# --- R4: returned ONCE, then accepted with a disclosure -------------------- #


def test_an_undischarged_submission_is_returned_once_with_the_open_list(harness, policy):
    """R4. The re-ask names the handles, because a re-ask that did not would
    be an instruction to guess."""
    problem, _, critics = _open_problem(harness, n=2)
    screening = screen_submission(
        harness, problem.id, _Turn(_Candidate("a revision")), policy, reask_index=0
    )
    assert screening.verdict == "reask"
    assert set(screening.open_handles) == {c.id for c in critics}


def test_the_second_submission_is_accepted_with_a_disclosure(harness, policy):
    """R4. ONCE means once. The second time through, the same undischarged
    submission is ACCEPTED and the gap is recorded as a typed disclosure --
    disclose, never die."""
    problem, _, critics = _open_problem(harness)
    screening = screen_submission(
        harness, problem.id, _Turn(_Candidate("a revision")), policy, reask_index=1
    )
    assert screening.verdict == "accept"
    assert set(screening.undischarged) == {c.id for c in critics}


def test_a_never_reask_policy_accepts_immediately(harness):
    """R13. The re-ask behaviour is POLICY, so a preset can turn it off without
    a code edit -- which is the modularity law applied to this knob."""
    problem, _, _ = _open_problem(harness)
    once = resolve_policy(Config(DISCHARGE_POLICY=ON))
    never = once.model_copy(update={"reask": "never"})
    assert screen_submission(
        harness, problem.id, _Turn(_Candidate("c")), never, reask_index=0
    ).verdict == "accept"


def test_no_candidate_is_ever_refused(harness, policy):
    """R4's hardest line, and the one a "required" channel gets wrong.

    There is no verdict that rejects. Whatever the screen returns, the
    candidate proceeds to the ordinary gate; the only difference is whether a
    disclosure is recorded. Asserted over the whole verdict vocabulary, so a
    future third verdict cannot quietly become a refusal.
    """
    problem, _, _ = _open_problem(harness)
    for index in (0, 1, 2):
        verdict = screen_submission(
            harness, problem.id, _Turn(_Candidate("c")), policy, reask_index=index
        ).verdict
        assert verdict in {"reask", "accept"}, verdict


def test_a_fully_discharged_submission_is_accepted_with_nothing_disclosed(harness, policy):
    """The positive case, without which every assertion above could pass on a
    screen that always returned `reask`."""
    problem, _, critics = _open_problem(harness)
    turn = _Turn(
        _Candidate(
            "a revision",
            [DischargeWireV1(handle=critics[0].id, kind="revised", note="added the solar term",
                             where="paragraph 2")],
        )
    )
    screening = screen_submission(harness, problem.id, turn, policy, reask_index=0)
    assert screening.verdict == "accept"
    assert screening.undischarged == ()


def test_a_problem_with_no_open_criticism_is_never_re_asked(harness, policy):
    """The channel costs nothing where there is nothing to answer."""
    problem = _problem(harness)
    _candidate(harness, problem)
    screening = screen_submission(
        harness, problem.id, _Turn(_Candidate("c")), policy, reask_index=0
    )
    assert screening.verdict == "accept" and screening.undischarged == ()


def test_the_channel_off_screen_accepts_everything(harness):
    """A7/R10. Off is off at the submission boundary too, so a channel-off run
    behaves exactly as it did before this tranche."""
    problem, _, _ = _open_problem(harness)
    off = resolve_policy(Config())
    screening = screen_submission(
        harness, problem.id, _Turn(_Candidate("c")), off, reask_index=0
    )
    assert screening.verdict == "accept" and screening.undischarged == ()


def test_a_discharge_naming_an_unknown_handle_does_not_discharge_anything(harness, policy):
    """A handle the pack never listed cannot answer a criticism.

    Silently accepting one would make the channel satisfiable by inventing a
    string, which is the cheapest possible way to fake compliance.
    """
    problem, _, critics = _open_problem(harness)
    turn = _Turn(_Candidate("c", [DischargeWireV1(handle="not-a-handle", kind="revised",
                                                  note="n", where="w")]))
    screening = screen_submission(harness, problem.id, turn, policy, reask_index=0)
    assert screening.verdict == "reask"
    assert set(screening.open_handles) == {critics[0].id}


def test_a_discharge_missing_its_required_content_does_not_discharge(harness, policy):
    """R11's teeth. `revised` requires WHAT changed and WHERE; a `revised` with
    an empty `where` is a label with nothing behind it, which is precisely the
    acknowledgment shape Q5 measured as harmful."""
    problem, _, critics = _open_problem(harness)
    turn = _Turn(_Candidate("c", [DischargeWireV1(handle=critics[0].id, kind="revised",
                                                  note="changed it", where=None)]))
    assert screen_submission(harness, problem.id, turn, policy, reask_index=0).verdict == "reask"


def test_an_undeclared_kind_is_refused_typed(harness, policy):
    """The registry is the authority on what a kind IS."""
    problem, _, critics = _open_problem(harness)
    turn = _Turn(_Candidate("c", [DischargeWireV1(handle=critics[0].id, kind="hand_waved",
                                                  note="n")]))
    with pytest.raises(UnknownDischargeKindError):
        screen_submission(harness, problem.id, turn, policy, reask_index=0)


def test_no_kind_is_satisfied_by_acknowledgment():
    """R11, structural rather than by wording.

    Q5: "Do not add an acknowledgment requirement. Documented to hurt." So no
    declared kind may have an empty `requires` -- there is no way to discharge
    by merely noting a criticism -- and no acknowledgment-shaped name appears
    anywhere in the package.
    """
    for name, declaration in DISCHARGE_KIND_DECLARATIONS.items():
        assert declaration.requires, name

    package = pathlib.Path("src/deepreason/discharge")
    files = list(package.rglob("*.py"))
    assert files, package                                  # positive anchor
    for path in files:
        text = path.read_text().lower()
        for shape in ("acknowledg", "noted", "seen_it", "confirm_read"):
            assert shape not in text, (path, shape)


# --- R3/R6: the discharge records, and the rebuttal in the graph ----------- #


def test_a_discharge_is_recorded_as_a_measure(harness, policy):
    """R3. Attention/diagnostic, never a status -- the same vehicle gate
    decisions and evidence-citation checks already use."""
    problem, target, critics = _open_problem(harness)
    candidate = _candidate(harness, problem, "candidate: lunar plus solar")
    record_discharges(
        harness, problem.id, candidate.id,
        [DischargeWireV1(handle=critics[0].id, kind="revised", note="added it", where="p2")],
        policy,
    )
    inputs = [list(e.inputs) for e in harness.log.read() if list(e.inputs)[:1] == ["discharge:revised"]]
    assert inputs == [["discharge:revised", critics[0].id, candidate.id, problem.id]]


def test_a_recorded_discharge_closes_the_handle(harness, policy):
    """R2's other half: a handle stops rendering once it is answered, and the
    proof is read from the RECORD rather than from process state, so it
    survives a resume."""
    problem, target, critics = _open_problem(harness)
    candidate = _candidate(harness, problem, "candidate: lunar plus solar")
    assert len(open_criticisms(harness, problem.id, policy)) == 1
    record_discharges(
        harness, problem.id, candidate.id,
        [DischargeWireV1(handle=critics[0].id, kind="revised", note="added it", where="p2")],
        policy,
    )
    assert open_criticisms(harness, problem.id, policy) == ()


def test_a_rebuttal_is_itself_attackable(harness, policy):
    """R6. "a REBUTTED discharge is just a criticism artifact entering the
    ordinary graph" -- so it is an ordinary artifact, protected by nothing, and
    a critic attacks it exactly as they would attack anything else.
    """
    problem, target, critics = _open_problem(harness)
    candidate = _candidate(harness, problem, "candidate: lunar plus solar")
    registered = record_discharges(
        harness, problem.id, candidate.id,
        [DischargeWireV1(handle=critics[0].id, kind="rebutted",
                         note="the solar term is below the harbour's resolution")],
        policy,
    )
    assert len(registered) == 1
    rebuttal = registered[0]
    assert "solar term is below" in harness.state.artifacts[rebuttal].content_ref

    attack(harness, rebuttal, "the-harbour-resolves-to-centimetres")
    assert harness.state.status[rebuttal] == Status.REFUTED


def test_a_rebuttal_carries_only_mention_refs(harness, policy):
    """R6 and the law line together, as a STRUCTURE rather than a promise.

    `build_att` lifts attackers through EVIDENCE refs, not MENTION refs, so a
    mention-only rebuttal gives no edge through which a discharge could move a
    pre-existing label. Mirrors `file_departure_declaration`, which earned the
    same guarantee the same way.
    """
    problem, target, critics = _open_problem(harness)
    candidate = _candidate(harness, problem, "candidate: lunar plus solar")
    rebuttal = record_discharges(
        harness, problem.id, candidate.id,
        [DischargeWireV1(handle=critics[0].id, kind="rebutted", note="a rebuttal")],
        policy,
    )[0]
    refs = harness.state.artifacts[rebuttal].interface.refs
    assert {r.role for r in refs} == {RefRole.MENTION}
    assert {r.target for r in refs} == {critics[0].id, candidate.id}
    assert not harness.state.artifacts[rebuttal].warrants


def test_a_rebuttal_moves_no_existing_label(harness, policy):
    """R10's per-artifact half: recording a rebuttal changes no label that
    existed before it."""
    problem, target, critics = _open_problem(harness)
    candidate = _candidate(harness, problem, "candidate: lunar plus solar")
    before = dict(harness.state.status)
    record_discharges(
        harness, problem.id, candidate.id,
        [DischargeWireV1(handle=critics[0].id, kind="rebutted", note="a rebuttal")],
        policy,
    )
    after = harness.state.status
    for artifact_id, status in before.items():
        assert after[artifact_id] == status, artifact_id


def test_only_a_rebuttal_registers_an_artifact(harness, policy):
    """The other two kinds record a Measure and nothing else.

    A `revised` that registered an artifact would put a claim in the graph that
    nobody made; a `departure_declared` already has the Rung 6 protocol for
    that, and duplicating it here would create two declarations of one thing.
    """
    problem, target, critics = _open_problem(harness, n=2)
    candidate = _candidate(harness, problem, "candidate: lunar plus solar")
    registered = record_discharges(
        harness, problem.id, candidate.id,
        [
            DischargeWireV1(handle=critics[0].id, kind="revised", note="n", where="w"),
            DischargeWireV1(handle=critics[1].id, kind="departure_declared", note="n"),
        ],
        policy,
    )
    assert registered == ()
