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

What did NOT change, and is asserted here rather than assumed: the producer
lives outside `src/deepreason/rules/` and is never reached from `scan_spawns`,
so H1's deletion -- nothing mints a problem AUTOMATICALLY FROM A REFUTATION --
stands exactly as it was.
"""

from __future__ import annotations

import inspect

import pytest

from deepreason.harness import Harness
from deepreason.ontology import Problem, ProblemProvenance
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
    return harness.register_problem(
        Problem(
            id=PROBLEM_ID,
            description="explain the tide table for this harbour",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


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
    """The road P9 opens is a DIFFERENT road with a different authority. H1
    forbade minting AUTOMATICALLY FROM A REFUTATION inside `scan_spawns`, and
    that is untouched: the mint site is a module outside `rules/`, reached only
    by an explicit call carrying an explicit proposal."""
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
