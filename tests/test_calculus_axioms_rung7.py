"""The axiom ledger Rung 7 answers for (§5b): A6 and A9 PRESERVED.

Implements G7 (v2 calculus program, Rung 7). The LADDER's own rule is that
"every rung's gate names the axioms it PROVES and the axioms it PRESERVES — an
axiom nobody answers for is an axiom nobody is testing." Rung 7 proves none of
the eleven: it inherits A6 from Rung 3b and A9's render half from Rung 6, and
its job is to show that the frame entry, the succession pack and the trial
record did not break either.

A third thing is asserted here and it is an ABSENCE rather than an axiom: D-1
was answered A, and A is defined by what it does NOT build.
"""

import ast
import inspect
import pathlib

from deepreason.calculus import operations
from deepreason.calculus.standing import (
    fallen_frames,
    unseparated_fallen_frames,
)
from deepreason.ontology import Interface, Problem, ProblemProvenance, Provenance, Ref
from deepreason.ontology.artifact import RefRole
from deepreason.premises import batch_translation_offers, premise_orphaned
from tests.conftest import attack


TIDES = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}


def _art(harness, text, refs=()):
    return harness.create_artifact(
        text, interface=Interface(refs=list(refs)),
        provenance=Provenance(role="critic"),
    )


def _problem(harness, pid, description):
    return harness.register_problem(
        Problem(
            id=pid, description=description, criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    ).id


# --- A6: consulted frame assertions satisfy frame-separation ----------------

def test_a6_the_frame_entry_uses_rung_3bs_own_predicate(harness):
    """A6 preserved, structurally. The entry does not re-derive the graph
    condition: it CALLS `separation.consultability`, so there is one definition
    of the invariant and no way for the cascade and the consult path to mean
    different things by "separated"."""
    from deepreason.calculus import standing

    source = inspect.getsource(standing._fallen)
    assert "consultability(" in source
    # and it does not roll its own component walk
    assert "adjudication_component" not in source
    assert "state.att" not in source and "state.dep" not in source


def test_a6_an_unseparated_fall_moves_nothing(harness):
    """A6 preserved, behaviourally. R64: a violation makes the assertion
    unconsultable "and does nothing else — no attack edge, no warrant, no label
    change". Rung 7 adds a fourth thing it must not do: no MARK."""
    subject = _art(harness, "b: the lunar theory of tides")
    case = _art(
        harness, "reach record: derived from the lunar theory itself",
        refs=[Ref(target=subject.id, role=RefRole.DEPENDENCE)],
    )
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse the lunar theory"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=subject.id, scope=TIDES,
        reach_case_refs=(case.id,), departure_protocol="declare it",
    )
    inside = _problem(harness, "tides-0", "what governs the tides")
    before = (dict(harness.state.status), list(harness.state.att),
              list(harness.state.dep))
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")

    assert fallen_frames(harness) == ()
    assert [f.assertion_id for f in unseparated_fallen_frames(harness)] == [
        assertion.id
    ]
    assert inside not in premise_orphaned(harness)
    # Restricted to artifacts that EXISTED before the attack: the critic and
    # its validity node are new NODES, and the claim is that the violation
    # perturbs nothing already on the graph.
    moved = {
        aid for aid, was in before[0].items()
        if harness.state.status.get(aid) != was
    }
    assert moved == {assertion.id}, moved
    # and no pre-existing edge was rewritten either
    assert set(before[1]) <= set(harness.state.att)
    assert list(harness.state.dep) == before[2]


# --- A9: render, measures and diagnostics act ONLY through attention --------

def test_a9_the_succession_render_and_the_trial_hold_no_mutator(harness):
    """A9 preserved. `succession.py` is a render plus a diagnostic, and exactly
    ONE function in it may write: `record_succession_trial`, which registers an
    ordinary attackable artifact and a measure. Nothing else can reach a
    mutator, and nothing anywhere in it can move a label."""
    from deepreason.calculus import succession

    tree = ast.parse(pathlib.Path(succession.__file__).read_text())
    writers = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        body = ast.unparse(node)
        if any(
            f"{verb}" in body
            for verb in ("create_artifact", "register_", "record_measure")
        ):
            writers.add(node.name)
    assert writers == {"record_succession_trial"}, writers
    source = pathlib.Path(succession.__file__).read_text()
    for forbidden in ("state.status[", "state.att.append", "state.dep.append",
                      "Warrant(", "_adjudicate"):
        assert forbidden not in source, forbidden


def test_a9_the_diagnostics_reach_no_label(harness):
    """The behavioural half, over all three of Rung 7's readouts: the batch
    offers, the trial record and the cascade marks. Computing every one of them
    leaves every label exactly as it was."""
    from deepreason.calculus.succession import record_succession_trial

    subject = _art(harness, "b: the lunar theory of tides")
    case = _art(harness, "reach record: three lineages cite the lunar theory")
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse the lunar theory"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=subject.id, scope=TIDES,
        reach_case_refs=(case.id,), departure_protocol="declare it",
    )
    _problem(harness, "tides-0", "what governs the tides")
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")

    before = dict(harness.state.status)
    premise_orphaned(harness)
    batch_translation_offers(harness)
    record_succession_trial(harness, "not-a-succession-problem")
    assert dict(harness.state.status) == before


def test_a9_the_trial_record_is_an_artifact_not_a_label(harness):
    """The distinction A9 turns on. The trial WRITES — a diagnostic nobody can
    attack is a diagnostic nobody can correct — but what it writes is an
    ordinary artifact and a measure, never a status, an edge or a warrant."""
    from deepreason.calculus import succession

    source = inspect.getsource(succession.record_succession_trial)
    assert "create_artifact" in source and "record_measure" in source
    assert "Warrant" not in source
    assert "status" not in source


# --- the ABSENCE D-1 decided -------------------------------------------------

def test_no_crisis_problem_spawn_trigger_was_built(harness):
    """D-1 answered A: crisis is a RENDER STATE ONLY. Road B would have minted
    a crisis problem from a consulted assertion under attack — the shape H1
    deleted, one layer up. Nothing in the tree does it, and nothing in the tree
    names it."""
    src = pathlib.Path("src/deepreason")
    assert not [p for p in src.rglob("*.py") if "crisis_problem" in p.read_text()]
    # `SpawnTrigger` gained no member for it either
    from deepreason.ontology import SpawnTrigger

    assert not [m for m in SpawnTrigger if "crisis" in m.value]


def test_the_wound_count_is_attention_and_reaches_no_label(harness):
    """What D-1's answer DID ask for, and its limit. The rank term is a count
    over the warrant table; it decides which problem a cycle looks at next and
    nothing else."""
    from deepreason.calculus.nomination import promotion_wound_counts

    source = inspect.getsource(promotion_wound_counts)
    for forbidden in ("create_artifact", "register_", "record_", "status["):
        assert forbidden not in source, forbidden
    tree = ast.parse(source)
    assert not [
        n for n in ast.walk(tree) if isinstance(n, ast.Assign)
        and any(k in ast.unparse(g) for g in n.targets
                for k in ("state.status", "state.att", "state.dep"))
    ]
