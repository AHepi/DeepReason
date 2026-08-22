"""The scope predicate sigma: D-5's fixed finite DSL, and C1 determinism.

Implements R5 (v2 calculus program, Rung 4). `docs/COMPUTABLE_CALCULUS.md`
Def 9.2 requires sigma to be "a total computable predicate over problem
records", deterministic, and DECISIONS.md D-5 answered **A**: a fixed finite
DSL reusing `declarative_numeric_v1`'s shape (spec v1.6), never a free-form
predicate language.

The determinism claim is the load-bearing one, and it is asserted against a
RE-MATERIALIZED harness rather than a repeated call in one process: a predicate
that read anything outside the `Problem` record would still answer twice the
same way inside one interpreter.
"""

import pytest

from deepreason.calculus.scope import ScopeError, compile_scope, scope_admits
from deepreason.harness import Harness
from deepreason.ontology import Problem, ProblemProvenance, SpawnTrigger


def _problem(pid="pi-1", description="why do tides follow the moon",
             criteria=(), trigger=SpawnTrigger.SEED, sources=()):
    return Problem(
        id=pid,
        description=description,
        criteria=list(criteria),
        provenance=ProblemProvenance(trigger=trigger, **{"from": list(sources)}),
    )


def _doc(predicate):
    return {"schema": "declarative-scope.v1", "predicate": predicate}


def test_scope_evaluates_on_problem_metadata_alone():
    """R5. Every leaf the DSL offers reads the `Problem` record and nothing
    else -- no artifact, no status, no log. All five fields are reachable."""
    sigma = compile_scope(_doc({"op": "and", "args": [
        {"op": "contains", "args": [{"field": "description"}, {"text": "tides"}]},
        {"op": "eq", "args": [{"field": "trigger"}, {"text": "seed"}]},
        {"op": "starts_with", "args": [{"field": "id"}, {"text": "pi-"}]},
        {"op": "member", "args": [{"list": "criteria"}, {"text": "c-1"}]},
        {"op": "empty", "args": [{"list": "sources"}]},
    ]}))
    assert scope_admits(sigma, _problem(criteria=["c-1"])) is True
    assert scope_admits(sigma, _problem(description="why is the sky blue",
                                        criteria=["c-1"])) is False
    assert scope_admits(sigma, _problem(criteria=[])) is False
    assert scope_admits(sigma, _problem(criteria=["c-1"], sources=["a-1"])) is False


def test_the_op_vocabulary_is_closed():
    """R5/D-5. An operation outside the fixed set is refused with a typed code,
    not evaluated and not guessed at. This is what makes the language FINITE
    rather than merely small today."""
    with pytest.raises(ScopeError) as caught:
        compile_scope(_doc({"op": "regex_match",
                            "args": [{"field": "description"}, {"text": ".*"}]}))
    assert caught.value.code == "scope-op-unsupported"


def test_the_same_problem_and_state_give_the_same_answer(tmp_path):
    """R5, C1 determinism. Asserted across a RE-MATERIALIZED harness, because a
    predicate reading anything outside the `Problem` record would still answer
    twice the same way inside one process."""
    document = _doc({"op": "contains",
                     "args": [{"field": "description"}, {"text": "tides"}]})
    problem = _problem()
    harness = Harness(tmp_path / "run")
    harness.register_problem(problem)
    first = scope_admits(compile_scope(document), harness.state.problems[problem.id])

    reopened = Harness(tmp_path / "run", read_only=True)
    second = scope_admits(compile_scope(document), reopened.state.problems[problem.id])
    assert first is second is True


def test_a_free_form_predicate_is_refused():
    """R5/D-5 road B, refused. Authored source -- Python, a lambda, a string
    expression -- never becomes a membership test: the tree already refuses
    model-authored Python without a certified container, and D-5 declined to
    import that refusal into scope membership."""
    for body in ("lambda p: True", {"python": "p.id == 'pi-1'"}, ["and", True]):
        with pytest.raises(ScopeError):
            compile_scope(_doc(body))
    with pytest.raises(ScopeError) as caught:
        compile_scope({"schema": "python-scope.v1", "predicate": {"const": True}})
    assert caught.value.code == "scope-schema-unknown"
