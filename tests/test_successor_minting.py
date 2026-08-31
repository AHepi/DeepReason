"""The MINTING ROAD is built, and it is OFF unless a run switches it on.

Operator law, 2026-08-29 (CLAUDE.md): "But build the wiring to mint, with the
option to switch it on with a flag saying something like 'may cause critics to
fully consume conjecturer role'. Switch off by default."

Four claims, each with a command behind it:

- with the gate OFF -- the default, and the default is what an unconfigured run
  gets -- a filled successor question mints NOTHING and the problem set is
  byte-unchanged;
- with the gate ON exactly one problem is minted, and minting the same proposal
  twice mints once (the re-registration trap in `DR-SEAM-ontology-x-rules`: a
  second registration under the same id is a WellFormednessError, never an
  update);
- the minted problem carries `SpawnTrigger.SUCCESSOR` and names BOTH parents in
  its provenance `from`;
- switching the gate on DISCLOSES, in the operator's own words, and never
  refuses and never stays silent (the ungated-seats law, 2026-08-28).

What did NOT change, asserted here in BOTH halves rather than assumed: the
producer lives outside `src/deepreason/rules/` (a check on LOCATION and on two
literals absent from `scan_spawns`' source), and refuting a candidate and
rescanning mints no `SpawnTrigger.SUCCESSOR` problem (a check on what the sweep
DOES, which is what a relapse spelled around those literals would break). So
H1's deletion -- nothing mints a problem AUTOMATICALLY FROM A REFUTATION --
stands exactly as it was. The frontier-wide version of the same guarantee is
`tests/test_h1_no_spawn_from_refutation.py`, which predates this trigger's
revival.
"""

from __future__ import annotations

import inspect

import pytest

from deepreason.harness import Harness
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.ontology.problem import SpawnTrigger
from deepreason.ontology.event import Rule
from deepreason.successor import mint, minting_notices
from deepreason.successor.mint import successor_problem_id

PROBLEM_ID = "pi-successor-mint"
TARGET_ID = "artifact-under-criticism"
QUESTION = "what would settle whether the solar term is measurable at all?"

WARNING = "may cause critics to fully consume conjecturer role"


class _Off:
    """The default: no run said anything about minting."""


class _On:
    SUCCESSOR_MINTING_ENABLED = True


def _seed(harness) -> Problem:
    # The parent carries a REAL criterion. Without one, `parent.criteria` is
    # `[]` and the inheritance assertion below degenerates to `[] == []`, which
    # holds for an implementation that inherits nothing -- the exact behaviour
    # the comment at that assertion calls dangerous.
    harness.register_commitment(
        Commitment(id="k-tide", eval="predicate:'tide' in content")
    )
    return harness.register_problem(
        Problem(
            id=PROBLEM_ID,
            description="explain the tide table for this harbour",
            criteria=["k-tide"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def _gate_warning_receipts(harness):
    return [
        list(event.inputs)
        for event in harness.log.read()
        if event.rule == Rule.MEASURE
        and event.inputs
        and event.inputs[0] == "successor-minting-gate:ENABLED"
    ]


def _mint_receipts(harness):
    return [
        list(event.inputs)
        for event in harness.log.read()
        if event.rule == Rule.MEASURE
        and event.inputs
        and event.inputs[0] == "successor-problem-minted"
    ]


# --- the gate is OFF by default -------------------------------------------- #


def test_the_gate_is_off_by_default_and_mints_nothing(tmp_path):
    """A configuration that says nothing about minting mints nothing, and does
    so without touching the log at all: the default is not "no problem
    appears", it is "nothing happened"."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    before = set(harness.state.problems)
    seq = harness._next_seq

    assert mint(harness, _Off(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
                question=QUESTION) is None
    assert set(harness.state.problems) == before
    assert harness._next_seq == seq
    assert _mint_receipts(harness) == []


def test_the_default_config_object_has_the_gate_off():
    """Read through the same accessor production uses, so the guarantee does
    not depend on the two per-run switches having landed yet."""
    from deepreason.successor import minting_enabled

    assert minting_enabled(_Off()) is False
    from deepreason.config import Config

    assert minting_enabled(Config()) is False


# --- the gate ON mints once, and once only --------------------------------- #


def test_the_gate_on_mints_exactly_one_problem_and_is_idempotent(tmp_path):
    """Deterministic id, idempotent registration. Re-running after a crash
    between two writes must register nothing new -- the same reason
    `ensure_promotion_problem` is shaped this way."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    before = set(harness.state.problems)

    first = mint(harness, _On(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
                 question=QUESTION)
    assert first is not None
    grew = set(harness.state.problems) - before
    assert grew == {first.id}
    assert first.id == successor_problem_id(PROBLEM_ID, TARGET_ID, QUESTION)
    assert first.id.startswith("succ:")

    second = mint(harness, _On(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
                  question=QUESTION)
    assert second is not None and second.id == first.id
    assert set(harness.state.problems) - before == {first.id}
    assert _mint_receipts(harness) == [
        ["successor-problem-minted", first.id, PROBLEM_ID, TARGET_ID]
    ]


def test_the_minted_problem_carries_the_trigger_and_names_both_parents(tmp_path):
    """The provenance IS the audit trail: which problem the question was
    proposed under, and which artifact was being criticised when it was."""
    harness = Harness(tmp_path / "run")
    parent = _seed(harness)
    minted = mint(harness, _On(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
                  question=QUESTION)

    assert minted.provenance.trigger == SpawnTrigger.SUCCESSOR
    assert list(minted.provenance.from_) == [PROBLEM_ID, TARGET_ID]
    assert minted.description == QUESTION
    # Criteria are inherited AT REGISTRATION because `Problem` is immutable: a
    # successor registered without them could be addressed before anything
    # could refuse it.
    assert list(parent.criteria) == ["k-tide"]            # the comparison is real
    assert list(minted.criteria) == list(parent.criteria)


@pytest.mark.parametrize("empty", [None, "", "   "])
def test_an_unfilled_field_mints_nothing_even_with_the_gate_on(tmp_path, empty):
    """"Not enforceable" cuts both ways: an open gate does not manufacture a
    proposal nobody made."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    before = set(harness.state.problems)
    assert mint(harness, _On(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
                question=empty) is None
    assert set(harness.state.problems) == before


def test_a_different_question_mints_a_different_problem(tmp_path):
    """The id is a pure function of the proposal, so idempotence is about the
    same proposal and not about the channel being one-shot."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    first = mint(harness, _On(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
                 question=QUESTION)
    other = mint(harness, _On(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
                 question="what would refute the lunar-only account instead?")
    assert other is not None and other.id != first.id


# --- switching it on DISCLOSES, in the operator's own words ---------------- #


def test_enabling_the_gate_discloses_the_operators_own_warning():
    """Never a refusal and never silence. The text is the operator's, carried
    verbatim rather than paraphrased, so a reader checking this against
    CLAUDE.md finds the same words."""
    notices = minting_notices(_On())
    assert len(notices) == 1, notices
    assert notices[0].code == "SUCCESSOR_MINTING_ENABLED"
    assert WARNING in notices[0].message
    assert notices[0].resolution


def test_a_run_that_left_the_gate_off_is_told_nothing():
    """A run that changed nothing has nothing to disclose; a notice here would
    be noise in every record that never used the channel."""
    assert minting_notices(_Off()) == ()


def test_the_warning_text_is_the_operators_words_on_the_registry_row():
    """The row is where the text LIVES, so re-aiming or re-declaring the gate
    cannot quietly drop the warning it is required to carry."""
    from deepreason.successor.registry import GATES

    assert GATES["minting.v1"].warning == WARNING
    assert GATES["minting.v1"].default is False


# --- H1's deletion stands: the producer is outside the spawn rules --------- #


def test_the_producer_is_outside_scan_spawns(tmp_path):
    """The road P9 opens is a DIFFERENT road with a different authority: the
    mint site is a module outside `rules/`, reached only by an explicit call
    carrying an explicit proposal.

    Scope, stated because the earlier wording overclaimed it: this test pins
    the producer's LOCATION and the absence of two literals from the sweep's
    source. It is a spelling check, and a relapse written around those literals
    passes it. `test_scan_spawns_mints_no_successor_from_a_refutation` below is
    the behavioural half.
    """
    from deepreason.rules.spawn import scan_spawns

    source = inspect.getsource(scan_spawns)
    assert "SpawnTrigger.SUCCESSOR" not in source
    # The word itself DOES appear there, in the comment recording why the
    # branch was deleted, so the check is on the machinery and not on spelling.
    assert "deepreason.successor" not in source
    assert "H1" in source                                  # positive anchor

    producer = inspect.getsourcefile(mint).replace("\\", "/")
    assert producer.endswith("/deepreason/successor/mint.py"), producer
    assert "/deepreason/rules/" not in producer


def test_scan_spawns_mints_no_successor_from_a_refutation(tmp_path):
    """H1's deletion, RUN rather than spelled.

    Refute the only candidate on the seed problem, rescan every structural
    trigger, and assert no problem carrying `SpawnTrigger.SUCCESSOR` exists.
    This is the assertion an H1 relapse cannot evade by choosing its spelling:
    a loop reinstated as `SpawnTrigger("successor")` leaves the location and
    literal checks above green and dies here.
    """
    from deepreason.config import Config
    from deepreason.ontology import Status
    from deepreason.rules.spawn import scan_spawns
    from tests.conftest import attack

    harness = Harness(tmp_path / "run")
    _seed(harness)
    candidate = harness.create_artifact(
        "the tide follows the moon", problem_id=PROBLEM_ID
    )
    scan_spawns(harness, Config())
    before = set(harness.state.problems)

    attack(harness, candidate.id, "ignores solar forcing")
    assert harness.state.status[candidate.id] == Status.REFUTED
    scan_spawns(harness, Config())

    minted = sorted(
        pid
        for pid, problem in harness.state.problems.items()
        if problem.provenance.trigger == SpawnTrigger.SUCCESSOR
    )
    assert minted == [], minted
    assert set(harness.state.problems) == before


# --- Q2 ROAD B: the warning reaches the run's OWN RECORD -------------------- #


def test_switching_the_gate_on_writes_the_operators_warning_to_the_record(tmp_path):
    """Q2 ROAD B, the durable half. `minting_notices` is the COMPILE-time
    reading of the same declaration and has no production caller; the record is
    the only admissible evidence about what a run did, so the words have to
    land there or the disclosure is a promise rather than a fact.

    The receipt carries the operator's text VERBATIM, because the law names the
    text and not the idea.
    """
    harness = Harness(tmp_path / "run")
    _seed(harness)

    mint(harness, _On(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
         question=QUESTION)

    receipts = _gate_warning_receipts(harness)
    assert receipts == [["successor-minting-gate:ENABLED", WARNING]], receipts


def test_the_warning_is_written_even_when_no_question_was_ever_proposed(tmp_path):
    """The warning is about the CONFIGURATION, not about any proposal. A run
    that switched the gate on and received nothing must still say so, or the
    record understates the configuration in exactly the case where a reader
    would most want to know it was open."""
    harness = Harness(tmp_path / "run")
    _seed(harness)

    assert mint(harness, _On(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
                question="   ") is None
    assert _mint_receipts(harness) == []
    assert _gate_warning_receipts(harness) == [
        ["successor-minting-gate:ENABLED", WARNING]
    ]


def test_the_warning_is_written_exactly_once_however_often_the_gate_is_consulted(tmp_path):
    """Idempotent by SEARCHING THE RECORD, not by module state: a resumed run
    rebuilds no flag, and a warning that vanished across a resume would make
    the record say the gate was silently on for the second half."""
    harness = Harness(tmp_path / "run")
    _seed(harness)

    for question in (QUESTION, QUESTION + " really?", "", QUESTION + " and?"):
        mint(harness, _On(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
             question=question)

    assert len(_gate_warning_receipts(harness)) == 1, _gate_warning_receipts(harness)


def test_a_run_that_left_the_gate_off_writes_no_warning_to_the_record(tmp_path):
    """Never silence when a gate is switched ON; never noise when it is not.
    An absent receipt is what says the gate was off."""
    harness = Harness(tmp_path / "run")
    _seed(harness)

    mint(harness, _Off(), problem_id=PROBLEM_ID, target_id=TARGET_ID,
         question=QUESTION)

    assert _gate_warning_receipts(harness) == []


def test_the_recorded_warning_and_the_declared_warning_are_the_same_string():
    """Two places carry the operator's words -- the registry row and the
    record -- and this is what stops them drifting apart. Neither is allowed to
    paraphrase: a reader checking either against CLAUDE.md must find the same
    sentence."""
    from deepreason.successor.registry import GATES, MINTING_GATE_ID

    declared = GATES[MINTING_GATE_ID].warning
    assert declared == WARNING
    assert WARNING in minting_notices(_On())[0].message
