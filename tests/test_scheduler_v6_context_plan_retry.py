"""Regression (episode-config arm A, run-cd878ff440f61294de34bea1fd45f8ad):
a v6 run whose conjecture context went stale died instead of retrying.

The scheduler zeroed the context plan for v6 before its first Conj dispatch,
because v6 plans context inside Conj after durable work preparation and raises
on a pre-made one. The ConjectureContextStale handler then re-planned with a
second, separate expression that carried no v6 rule, so the retry handed Conj
exactly what it refuses. The live run stopped `operational_failure` at cycle 0
with `v6 conjecture context must be planned after durable work preparation`,
71,323 tokens in, and the failure terminal took no continuation receipt.

Two tests, because the defect had two halves. The behaviour test pins what the
rule is; the structural test pins that BOTH dispatch sites obey it, which is
the half that actually broke -- a behaviour test alone passes happily while a
call site bypasses the rule entirely.
"""

import ast
import inspect
import pathlib

from deepreason.scheduler.scheduler import Scheduler

# Resolved from the imported module, so the test reads the file that actually
# ran rather than a path guessed from the package name.
SOURCE = pathlib.Path(inspect.getsourcefile(Scheduler))


class _Manifest:
    def __init__(self, schema_version):
        self.schema_version = schema_version


class _Stub:
    """A Scheduler with only what the plan rule reads."""

    def __init__(self, manifest):
        self.run_manifest = manifest
        self.delegated = []

    def _plan_conjecture_context(self, problem, school_id):
        self.delegated.append((problem, school_id))
        return {"plan": "from-the-planner"}

    dispatch = Scheduler._dispatch_conjecture_context_plan


def test_v6_dispatch_never_carries_a_premade_context_plan():
    stub = _Stub(_Manifest(6))
    assert stub.dispatch("problem-1", "school-a") is None
    # Not merely discarded after the fact: the planner is never run, so a v6
    # retry cannot spend work building a plan that Conj will refuse.
    assert stub.delegated == []


def test_pre_v6_dispatch_still_delegates_to_the_planner():
    for version in (4, 5):
        stub = _Stub(_Manifest(version))
        assert stub.dispatch("problem-1", "school-a") == {"plan": "from-the-planner"}
        assert stub.delegated == [("problem-1", "school-a")]


def test_manifestless_dispatch_still_delegates():
    stub = _Stub(None)
    assert stub.dispatch("problem-1", None) == {"plan": "from-the-planner"}
    assert stub.delegated == [("problem-1", None)]


def _call_sites(tree, attribute):
    """Every `self.<attribute>(...)` call, as (enclosing function name, node)."""
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Attribute)
                and inner.func.attr == attribute
                and isinstance(inner.func.value, ast.Name)
                and inner.func.value.id == "self"
            ):
                sites.append((node.name, inner))
    return sites


def test_only_the_dispatch_rule_may_plan_conjecture_context():
    """The rule has exactly one owner, so the two sites cannot drift again.

    Bound by AST, not by grepping for the name: the method name appears in
    prose in this module's own docstrings, and a string search would call a
    comment a call site.
    """

    tree = ast.parse(SOURCE.read_text())
    owners = {
        name
        for name, _ in _call_sites(tree, "_plan_conjecture_context")
        # The innermost enclosing function is listed last by ast.walk order over
        # nested defs, so collect every enclosing name and require the owner.
    }
    assert owners == {"_dispatch_conjecture_context_plan"}, (
        "_plan_conjecture_context is reachable from "
        f"{sorted(owners)}; dispatch-time planning has exactly one owner"
    )


def test_conj_dispatch_uses_the_rule_at_every_site():
    """Every `conjecture_context_plan=` argument comes from the owner's result."""

    tree = ast.parse(SOURCE.read_text())
    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id == "context_plan" for t in node.targets
        )
    ]
    assert assignments, "no context_plan assignment found; test has gone stale"
    for node in assignments:
        assert isinstance(node.value, ast.Call), ast.dump(node.value)
        assert isinstance(node.value.func, ast.Attribute)
        assert node.value.func.attr == "_dispatch_conjecture_context_plan", (
            "context_plan assigned from "
            f"{node.value.func.attr} at line {node.lineno}; the stale-retry "
            "site bypassing the rule is exactly what killed arm A"
        )
