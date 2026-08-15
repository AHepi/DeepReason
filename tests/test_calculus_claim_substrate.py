"""The typed claim substrate: closed bodies, one compiler, companion subjects.

Regression (v2 calculus program, Rung 3c). Two guarantees travel together and
neither works alone: the schema set is CLOSED, so no prose predicate becomes
quasi-ontology, and ONE controller-owned compiler assigns every ref role, so no
model ever decides whether an endpoint is a mention, a dependence, or evidence.
"""

import json

import pytest

from deepreason.calculus import (
    CLAIM_SCHEMAS,
    ClaimDecodeError,
    PremiseAttributionV1,
    ProblemSubjectV1,
    compile_interface,
    decode,
    encode,
    ensure_problem_subject,
    problem_status,
    problem_subject_missing,
    problem_subject_of,
)
from deepreason.calculus.operations import problem_subject_body
from deepreason.calculus.programs import PROBLEM_SUBJECT_COMMITMENT
from deepreason.ontology import Interface, Problem, ProblemProvenance, Status
from deepreason.ontology.artifact import RefRole
from tests.conftest import attack


def _problem(harness, pid="pi-tides", *, criteria=(), trigger="seed", sources=()):
    return harness.register_problem(
        Problem(
            id=pid,
            description="explain the tides",
            criteria=list(criteria),
            provenance=ProblemProvenance.model_validate(
                {"trigger": trigger, "from": list(sources)}
            ),
        )
    )


# --- C1: the union is closed ------------------------------------------------


def test_an_open_predicate_cannot_enter():
    """D-a. The whole point of a closed set: `RelationClaim(predicate=...)`
    would let arbitrary prose become quasi-ontology, and every such predicate
    would need its interaction with att, dep, replay and status re-proven."""
    with pytest.raises(ClaimDecodeError) as caught:
        decode(json.dumps({"schema": "poietic.whatever-i-like.v1", "x": 1}))
    assert caught.value.code == "claim-schema-unknown"


def test_a_declared_but_unbuilt_schema_is_refused_with_its_reason():
    """Declared names without producers are refused, not quietly accepted.

    Shipping body models nobody creates is the E28 pattern; closing the NAME
    set is what stops the ontology drifting, and it does not require the bodies
    to exist yet.
    """
    assert "poietic.succession.v1" in CLAIM_SCHEMAS
    with pytest.raises(ClaimDecodeError) as caught:
        decode(json.dumps({"schema": "poietic.succession.v1"}))
    assert caught.value.code == "claim-schema-not-implemented"


def test_a_body_round_trips_through_its_canonical_encoding(harness):
    body = ProblemSubjectV1(
        problem_id="pi", description="d", criteria=["k"], trigger="seed", sources=[]
    )
    assert decode(encode(body)) == body
    # Canonical: the artifact id is a content address over this text, so two
    # encodings of one claim would be two artifacts.
    assert encode(body) == encode(decode(encode(body)))


# --- C2: one compiler owns the roles ----------------------------------------


def test_no_body_field_names_a_ref_role():
    """D-d. A body says WHAT it relates; the controller says HOW."""
    for model in (ProblemSubjectV1, PremiseAttributionV1):
        fields = " ".join(model.model_fields)
        assert "mention" not in fields and "dependence" not in fields
        assert "evidence" not in fields and "role" not in fields


def test_an_attribution_mentions_its_premise_and_never_depends_on_it():
    """D-e. The mention law, enforced at COMPILE time rather than checked after.

    An attribution that depended on its premise would be suspended by pass two
    the moment the premise fell, erasing the relation that identifies the
    orphan.
    """
    body = PremiseAttributionV1(
        problem_subject_ref="subject", premise_ref="X", derivation_manifest_ref="M"
    )
    roles = {ref.target: ref.role for ref in compile_interface(body).refs}

    assert roles["X"] == RefRole.MENTION
    assert roles["subject"] == RefRole.MENTION
    # The manifest IS load-bearing: if what the attribution rests on falls, the
    # attribution should lose its support. That is the only dependence here.
    assert roles["M"] == RefRole.DEPENDENCE


def test_a_problem_subject_rests_on_nothing():
    body = ProblemSubjectV1(
        problem_id="pi", description="d", criteria=[], trigger="seed", sources=[]
    )
    assert list(compile_interface(body).refs) == []


def test_the_compiler_is_the_only_authority_on_ref_roles():
    """C9/C2, checked structurally rather than by reading prose.

    The generic synthesizer compiles every connected endpoint as DEPENDENCE,
    which is exactly wrong for an attribution. The fix is a dedicated compiler,
    not a synthesizer taught to guess -- so the calculus package must neither
    import nor call it, and every `RefRole` decision in the package must live in
    `compiler.py`.
    """
    import ast
    import pathlib

    package = pathlib.Path("src/deepreason/calculus")
    role_sites = set()
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                assert "synth" not in ast.unparse(node), path.name
            if (
                isinstance(node, ast.Attribute)
                and getattr(node.value, "id", "") == "RefRole"
            ):
                role_sites.add(path.name)

    assert role_sites == {"compiler.py"}, role_sites


# --- C3/C4: the companion, and the six conditions ---------------------------


def test_ensure_problem_subject_is_idempotent(harness):
    """D-c. Twice ⇒ one artifact, one event. This is what makes the crash gap
    between the two writes recoverable by simply running it again."""
    problem = _problem(harness)
    before = len(list(harness.log.read()))

    first = ensure_problem_subject(harness, problem)
    after_first = len(list(harness.log.read()))
    second = ensure_problem_subject(harness, problem)

    assert first.id == second.id
    assert len(list(harness.log.read())) == after_first
    assert after_first > before


@pytest.mark.parametrize(
    "break_it",
    ["body", "problem_id", "copies", "commitment", "addr", "refs"],
)
def test_each_recognition_condition_is_required(harness, break_it):
    """D-b. Six conditions; break any one and the artifact is not a subject."""
    problem = _problem(harness, criteria=[])
    harness.register_commitment(PROBLEM_SUBJECT_COMMITMENT)
    body = problem_subject_body(problem)
    text = encode(body)
    interface = compile_interface(body)
    problem_id = problem.id

    if break_it == "body":
        text = "not a claim at all"
    elif break_it == "problem_id":
        text = encode(body.model_copy(update={"problem_id": "pi-other"}))
    elif break_it == "copies":
        text = encode(body.model_copy(update={"description": "a different question"}))
    elif break_it == "commitment":
        interface = Interface(commitments=[], refs=[])
    elif break_it == "addr":
        problem_id = None
    elif break_it == "refs":
        from deepreason.ontology import Ref

        other = harness.create_artifact("something else")
        interface = Interface(
            commitments=list(interface.commitments),
            refs=[Ref(target=other.id, role=RefRole.MENTION)],
        )

    harness.create_artifact(
        text, codec="json", interface=interface, problem_id=problem_id
    )

    assert problem_subject_of(harness, problem.id) is None, break_it


def test_a_well_formed_companion_is_recognised(harness):
    problem = _problem(harness, criteria=[], trigger="seed", sources=[])
    subject = ensure_problem_subject(harness, problem)

    assert problem_subject_of(harness, problem.id).id == subject.id
    assert problem_status(harness, problem.id) == Status.ACCEPTED


# --- C6/C7: the derived view, and ordinary criticism -------------------------


def test_criticising_the_companion_moves_the_problems_standing(harness):
    """D-f. Critics attack the companion exactly as they attack anything else —
    no new attack species, no new authority — and the `Problem` record itself
    is untouched."""
    problem = _problem(harness)
    ensure_problem_subject(harness, problem)
    before = harness.state.problems[problem.id]

    attack(harness, problem_subject_of(harness, problem.id).id, "a category error")

    assert problem_status(harness, problem.id) == Status.REFUTED
    assert harness.state.problems[problem.id] == before   # the record is immutable
    assert problem.id in harness.state.problems           # nothing is deleted


def test_the_missing_companion_diagnostic_names_the_gap_and_clears(harness):
    """D-g. A crash between the two writes shows up HERE, and the repair is to
    run the operation again — not to change event atomicity."""
    problem = _problem(harness)

    assert problem_subject_missing(harness) == [problem.id]

    ensure_problem_subject(harness, problem)

    assert problem_subject_missing(harness) == []


# --- C5: nothing was added to the frozen records -----------------------------


def test_no_field_was_added_to_problem_state_or_event():
    """D-h/C5. The companion is computed from the record that already exists
    and found through `addr`. Adding `subject_artifact_id` to `Problem` would
    alter persisted records and pull this into the frozen-surface zone."""
    from deepreason.ontology import Problem as P
    from deepreason.ontology.state import EpistemicState

    assert set(P.model_fields) == {"id", "description", "criteria", "provenance"}
    assert "subject_artifact_id" not in P.model_fields
    assert not [f for f in vars(EpistemicState()) if "subject" in f or "claim" in f]
