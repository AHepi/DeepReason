"""THE LAW LINE for successor questions (operator law, 2026-08-29).

Stated in the tranche's SPEC.md R1 and repeated here because a test file is
where a law becomes falsifiable:

    The successor-question field is OPTIONAL on criticism output -- never
    required, never penalized. No successor field, destination row, receipt or
    minted problem may feed a label, a warrant, a rank, an admission decision,
    or any adjudication pass. Filling the field earns a critic nothing and
    leaving it empty costs a critic nothing.

This is the operator's standing seats guardrail -- "seats change how content is
GENERATED, never what counts as EVIDENCE" (CLAUDE.md) -- and the
formalism-optional law (`DR-CON-conjecture-kinds`'s R-g) applied to this
channel: nothing may weight an outcome on the KIND of a contribution, and a
proposed question is a kind of contribution.

Pinned four ways, because each closes a different route in:

1. an ABSENCE over the four packages that decide anything, on the model
   `tests/test_discharge_law_line.py` established;
2. the destination declaration record has no numeric field, so there is no
   weight to set;
3. admission is byte-identical with and without a routed successor question;
4. no status label differs between a field-filled and a field-absent run on one
   graph.

Pin 1 is mutation-proved (`experiments/2026-08-30-change-successor-questions/
proof/law_line_pin1_red.txt`): the field wired into the scheduler's own rank
key turns it red.
"""

from __future__ import annotations

import pathlib

import pytest

from deepreason.harness import Harness
from deepreason.llm.contracts import ArgumentativeCriticOutput, BatchCase
from deepreason.ontology import Interface, Problem, ProblemProvenance, Provenance
from deepreason.rules.guards import anti_relapse
from deepreason.successor import resolve, route
from deepreason.successor.registry import (
    DESTINATIONS,
    GATES,
    SuccessorDeclaration,
    declaration_field_types,
)


class _Config:
    """The shipped defaults, read the way the registry reads any config.

    Deliberately NOT `deepreason.config.Config`: the two per-run fields are
    parked behind a frozen-surface grant, and this channel must be correct
    before they exist. `resolve` reads its selector by `getattr`, so an object
    that carries neither field is exactly the default case.
    """


# The packages that DECIDE something: what a status is, what a problem is worth
# working on, whether a candidate is admitted, whether a prose case survives a
# trial. There is NO permitted exception, and that is the point: this channel's
# dispatch lives outside `rules/` by construction, so a name appearing here is
# either a mistake or an operator decision that has not been written down.
DECIDING_PACKAGES = (
    pathlib.Path("src/deepreason/scheduler"),
    pathlib.Path("src/deepreason/adjudication"),
    pathlib.Path("src/deepreason/informal"),
    pathlib.Path("src/deepreason/rules"),
)
PERMITTED: tuple[pathlib.Path, ...] = ()

FORBIDDEN_NAMES = (
    "successor_question",
    "deepreason.successor",
    "SuccessorDeclaration",
    "SUCCESSOR_QUESTION_DESTINATION",
    "SUCCESSOR_MINTING_ENABLED",
    "successor-question:",
    "successor-problem-minted",
    "minting_enabled",
    "minting_notices",
    "unknown_destination_notices",
    "SpawnTrigger.SUCCESSOR",
)


# --- pin 1: the absence ---------------------------------------------------- #


def test_nothing_that_labels_ranks_or_admits_reads_a_successor_question():
    """R1. No module that decides anything may name the successor machinery.

    Every negative check is paired with a POSITIVE ANCHOR on the same tree
    (`DR-SCHEMA` check-writing rule 1): a moved or renamed package would
    otherwise make this vacuous rather than failing.

    The bare word "successor" is deliberately NOT forbidden -- `rules/conj.py`
    already uses it to describe `succ:*` problems as attention objects, and
    forbidding an English word would make this test about spelling instead of
    about coupling.
    """
    anchored = 0
    offenders = []
    for package in DECIDING_PACKAGES:
        files = [p for p in package.rglob("*.py") if p not in PERMITTED]
        assert files, package                              # positive anchor
        anchored += len(files)
        for path in files:
            text = path.read_text()
            for name in FORBIDDEN_NAMES:
                if name in text:
                    offenders.append((str(path), name))
    assert anchored > 20, anchored                         # positive anchor
    assert not offenders, offenders


def test_the_channel_has_no_permitted_exception_inside_a_deciding_package():
    """The exception list is EMPTY, and emptiness is the claim.

    The premise channel needed `rules/crit.py` because its dispatch is a
    criticism act. This channel's dispatch site is an open operator question
    (the tranche's Q3: may the criticism side write to the workshop?), so until
    that is answered nothing inside `rules/` may name it. If Q3 is answered
    "yes, crit.py dispatches", the test above goes red and THIS list is where
    the answer gets written down -- which is the alarm working, not failing.
    """
    assert PERMITTED == ()


# --- pin 2: no weight exists to be set ------------------------------------- #


def test_a_successor_declaration_carries_no_number():
    """R1, structurally. The absence is the guarantee.

    A rank, weight, priority or score field here is what would let a proposed
    question reach a decision, and no configuration can set a field that does
    not exist. Checked over the MODEL rather than over today's rows, so a
    destination added tomorrow cannot introduce one.
    """
    numeric = [
        name
        for name, annotation in declaration_field_types().items()
        if annotation in (int, float)
    ]
    assert not numeric, numeric
    assert set(declaration_field_types()) == {
        "id", "routes", "default", "enforcement", "authority", "warning",
    }
    # Every shipped row is an instance of that model, so no row can carry a
    # field the model does not declare.
    for row in (*DESTINATIONS.values(), *GATES.values()):
        assert isinstance(row, SuccessorDeclaration), row


def test_the_contract_field_is_optional_on_both_criticism_outputs():
    """R1's other half: absent-legal, and absent means unchanged bytes.

    `None` rather than `""` so a criticism that proposed nothing canonicalises
    to exactly the bytes it always did under `exclude_none` -- an empty string
    would add a key to every critic output ever recorded.
    """
    for model in (ArgumentativeCriticOutput, BatchCase):
        field = model.model_fields["successor_question"]
        assert field.default is None, (model.__name__, field.default)
        assert not field.is_required(), model.__name__
    bare = ArgumentativeCriticOutput(attack=False)
    assert "successor_question" not in bare.model_dump(exclude_none=True)
    filled = BatchCase(target="t", attack=False, successor_question="what next?")
    assert filled.model_dump(exclude_none=True)["successor_question"] == "what next?"


# --- pin 3: admission cannot see a successor question ---------------------- #


def _problem(harness, pid="p-tides"):
    return harness.register_problem(
        Problem(
            id=pid, description="state the tide table for this harbour", criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def _candidate(harness, problem, text):
    return harness.create_artifact(
        text, problem_id=problem.id, provenance=Provenance(role="conjecturer"),
        interface=Interface(refs=[]),
    )


def test_admission_is_byte_identical_with_and_without_a_successor_question(harness):
    """R1, behaviourally. The gate decides on CONTENT, and a proposed question
    is not content: the same candidate must receive the same verdict and the
    same reason string whether a successor question was routed beside it or not.

    The reason string matters as much as the boolean -- Measure inputs are
    compared against recorded roots, so a verdict that stayed True while its
    reason changed would still move the record.
    """
    problem = _problem(harness)
    artifact = _candidate(harness, problem, "candidate: the tide is lunar plus solar")
    first = anti_relapse.check(artifact, [], harness)

    routed = route(
        harness, _Config(), problem_id=problem.id,
        question="what would settle whether the solar term is measurable here?",
    )
    assert routed is not None
    second = anti_relapse.check(artifact, [], harness)
    assert first == second, (first, second)


# --- pin 4: no label differs, field on vs field off ------------------------ #


def _graph(harness, *, successor_question):
    """One identical graph, built twice; the only difference is the field.

    Returns the final labels over the artifacts BOTH runs contain.
    """
    problem = _problem(harness)
    target = _candidate(harness, problem, "candidate: the tide is lunar only")
    critic = harness.create_artifact("critic: omits the solar contribution",
                                     provenance=Provenance(role="critic"))
    harness.record_measure(inputs=["scrutiny", target.id, critic.id])
    if successor_question:
        route(harness, _Config(), problem_id=problem.id, question=successor_question)
    shared = {target.id, critic.id}
    return {a: s for a, s in harness.state.status.items() if a in shared}, shared


def test_no_label_differs_between_a_filled_and_an_empty_field(tmp_path):
    """R1. "Never penalized" means the graph cannot tell the difference.

    The comparison is over the artifacts BOTH runs contain. The filled run also
    holds one advisory scratch block and one Measure, and those are the DELTA
    -- stated here rather than hidden, because a comparison that quietly
    dropped the new records would be measuring its own filter.
    """
    off_labels, shared = _graph(Harness(tmp_path / "off"), successor_question=None)
    on_harness = Harness(tmp_path / "on")
    on_labels, _ = _graph(on_harness, successor_question="what would settle it?")

    assert off_labels == on_labels, (off_labels, on_labels)

    # The delta, stated. A routed question adds a scratch block and a Measure;
    # it adds no artifact and no attack edge, which is why the equality above
    # holds by construction rather than by luck.
    assert set(on_harness.state.artifacts) == shared
    assert len(on_harness.scratch_state.blocks) == 1
    assert set(on_harness.state.att) == set(Harness(tmp_path / "off").state.att)


def test_a_routed_question_is_not_an_attack_edge(tmp_path):
    """The sharpest form of pin 4, and the one a careless implementation fails.

    Routing appends a Measure. A Measure that somehow minted an attack edge
    would move labels while every other test here still passed, so this asserts
    the edge set directly.
    """
    harness = Harness(tmp_path / "run")
    problem = _problem(harness)
    target = _candidate(harness, problem, "candidate: lunar only")
    critic = harness.create_artifact("critic: omits the solar term",
                                     provenance=Provenance(role="critic"))
    harness.record_measure(inputs=["scrutiny", target.id, critic.id])
    before = set(harness.state.att)
    route(harness, _Config(), problem_id=problem.id, question="what settles it?")
    assert set(harness.state.att) == before


def test_the_shipped_default_needs_no_config_field_to_be_correct():
    """The channel is correct BEFORE its two per-run switches exist.

    `resolve` reads its selector by `getattr`, so an object carrying neither
    field selects the shipped default. This is what lets the destination
    registry land while the `Config` fields wait behind a frozen-surface grant,
    and it is asserted rather than assumed.
    """
    assert resolve(_Config()).id == "scratchpad.v1"
    assert DESTINATIONS["scratchpad.v1"].default is True
    assert GATES["minting.v1"].default is False


@pytest.fixture
def harness(tmp_path):
    return Harness(tmp_path / "run")
