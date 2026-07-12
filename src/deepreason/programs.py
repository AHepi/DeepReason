"""Budgeted test programs tau_kappa (spec §1).

V(kappa, c) = U^{<=beta}(tau_kappa, c) in {pass, fail, overrun}: extensional,
budgeted, decidable. ``eval:program|predicate`` verdicts are computed here
(reliable). ``eval:rubric`` verdicts exist only downstream of the trial
guard (§3, §10 — P5) and raise NotEvaluable here.

Budget honesty (§0 determinism): a verdict is a pure function of content,
so wall-clock time never drives it. Registry programs receive the budget
and may enforce a DETERMINISTIC bound (e.g. step count) internally; the
``overrun`` verdict is reserved for those (see measures/hv.py).
"""

import ast
import json
import re

from deepreason.ontology.artifact import Artifact
from deepreason.ontology.commitment import Commitment

PASS, FAIL, OVERRUN = "pass", "fail", "overrun"


class UnsafePredicate(ValueError):
    """A predicate expression reaches for dunder internals (the object-
    subclasses sandbox-escape surface) or names outside the safe set."""


def _validate_predicate(expr: str) -> None:
    """Defense-in-depth for the predicate eval() (stress-campaign RCE).
    eval() with __builtins__={} is escapable via `().__class__.__base__.
    __subclasses__()` — every such escape needs a dunder attribute or
    name. Reject any Attribute or Name touching an underscore-prefixed
    identifier, which blocks the entire escape family while leaving every
    legitimate predicate (len(content) > 120, 'x' in content.lower(),
    comprehensions over content.split()) untouched. Parse errors are
    unsafe by default."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise UnsafePredicate(f"unparseable predicate: {e}") from e
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise UnsafePredicate(f"dunder attribute access: .{node.attr}")
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise UnsafePredicate(f"underscore name: {node.id}")
        # No legitimate boolean predicate exponentiates; ** is only useful
        # here as an integer bomb (9**9**9). Cheap to forbid.
        if isinstance(node, ast.Pow):
            raise UnsafePredicate("exponentiation not allowed in a predicate")


class NotEvaluable(ValueError):
    """The commitment cannot be program-computed (e.g. rubric pre-P5)."""


def content_text(artifact: Artifact, blobs) -> str:
    if artifact.content_ref.startswith("inline:"):
        return artifact.content_ref[len("inline:"):]
    try:
        return blobs.get(artifact.content_ref).decode("utf-8", errors="replace")
    except KeyError:
        return ""


_SAFE_NAMES = {
    "len": len, "any": any, "all": all, "min": min, "max": max, "abs": abs,
    "sum": sum, "str": str, "int": int, "float": float, "sorted": sorted,
    "re": re, "json": json,
}


def _json_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    try:
        json.loads(text)
        return PASS, {"parsed": True}
    except Exception as e:  # noqa: BLE001 - verdicts must not crash the harness
        return FAIL, {"error": str(e)}


def _skeleton_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    from deepreason.informal.skeleton import skeleton_wf_program

    return skeleton_wf_program(text, budget)


def _exec_oracle(text: str, budget, artifact=None) -> tuple[str, dict]:
    """The acting evaluator (oracle.py): RUN the candidate against fixed tests
    and take the verdict from the result — criticism grounded in execution, not
    in a rubric judge or a well-formedness check. Deterministic + sandboxed."""
    from deepreason.oracle import run_from_spec

    return run_from_spec(text, budget)


def _property_oracle(text: str, budget, artifact=None) -> tuple[str, dict]:
    """Reference-free acting evaluator (oracle.py): RUN the candidate on fixed
    inputs and check each output with the spec's `def check(inp, out)` — no
    expected outputs anywhere, so the harness can pose problems nobody has
    solved, and critics can ground refutations in NEW inputs (counterexamples).
    Deterministic + sandboxed, same as exec_oracle."""
    from deepreason.oracle import run_property_from_spec

    return run_property_from_spec(text, budget)


def _generator_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    """Adjudicate an experimenter-proposed input generator BY ITS FRUITS
    (oracle.py): compile under the guard, enumerate, and PASS iff it yields
    enough gate-valid inputs including at least one novel one. Deterministic;
    a generator never decides refutations, so this well-formedness verdict is
    the ONLY adjudication a generator needs."""
    from deepreason.oracle import check_generator_from_spec

    return check_generator_from_spec(text, budget)


def _checker_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    """Mechanical admission for a PROPOSED property checker (oracle.py):
    compiles under the guard, bounded, and non-vacuous (rejects at least one
    degenerate output). Deliberately narrow: whether the property FOLLOWS
    FROM THE PROBLEM is an informal claim and goes to the relevance trial
    (rules/experiment.py), never to a program."""
    from deepreason.oracle import check_checker_from_spec

    return check_checker_from_spec(text, budget)


def _lineage_ref(text: str, budget, artifact=None) -> tuple[str, dict]:
    """Structural born-connected check (§7 L1): a candidate on a connection
    problem must carry a `dependence` ref into the problem's declared lineage
    (its isolated node or a ranked neighbour), frozen into budget.extra by
    unification.isolation.lineage_ref_commitment. This catches 'abstraction
    escape' — a skeleton imported from nowhere, unconnected to the graph — at
    the PROGRAM level, before it reaches a rubric judge and while criticism
    debt is high. It does NOT adjudicate on semantics (§0): the verdict is a
    pure function of interface STRUCTURE, which is part of the artifact's
    content-addressed identity, so it is replay-deterministic."""
    from deepreason.ontology.artifact import RefRole

    allowed = {e for e in str(budget.extra.get("endpoints", "")).split(",") if e}
    if not allowed or artifact is None:
        return PASS, {"endpoints": len(allowed)}  # nothing to enforce
    for ref in artifact.interface.refs:
        if ref.role == RefRole.DEPENDENCE and any(
            ref.target == e or ref.target.startswith(e) or e.startswith(ref.target)
            for e in allowed
        ):
            return PASS, {"connected_to": ref.target[:12]}
    return FAIL, {"reason": "no dependence ref into the connection lineage"}


# Named program registry. hv_floor is deliberately NOT here: it needs the
# variator (measures/hv.py), and keeping it out makes B0 stratification
# structural (spec §7).
def _manifest_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    from deepreason.manifest import manifest_wf

    return manifest_wf(text, budget, artifact)


def _component_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    from deepreason.manifest import component_wf

    return component_wf(text, budget, artifact)


def _integration_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    from deepreason.manifest import integration_wf

    return integration_wf(text, budget, artifact)


def _reasoning_envelope_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    from deepreason.workloads.text import reasoning_wf_program

    return reasoning_wf_program(text, budget, artifact)


def _reasoning_observation_pending(text: str, budget, artifact=None) -> tuple[str, dict]:
    return OVERRUN, {"reason": "observation requires registered evidence"}


PROGRAMS = {
    "json-wf": _json_wf,
    "skeleton_wf": _skeleton_wf,
    "lineage_ref": _lineage_ref,
    "exec_oracle": _exec_oracle,
    "property_oracle": _property_oracle,
    "generator_wf": _generator_wf,
    "checker_wf": _checker_wf,
    # Chunked website builds (manifest.py): the design's component manifest,
    # the per-chunk fragment contract, and assembled-page coherence. All
    # static, deterministic functions of content + frozen spec.
    "manifest_wf": _manifest_wf,
    "component_wf": _component_wf,
    "integration_wf": _integration_wf,
    "reasoning-envelope-wf": _reasoning_envelope_wf,
    "reasoning_observation_pending": _reasoning_observation_pending,
}


def evaluable(commitment: Commitment) -> bool:
    kind, _, arg = commitment.eval.partition(":")
    return kind == "predicate" or (kind == "program" and arg in PROGRAMS)


def evaluate(commitment: Commitment, artifact: Artifact, blobs) -> tuple[str, dict]:
    """Run tau_kappa on the artifact's real bytes; return (verdict, trace)."""
    kind, _, arg = commitment.eval.partition(":")
    text = content_text(artifact, blobs)
    if kind == "predicate":
        # Safe names go in GLOBALS: comprehension bodies inside eval resolve
        # free names via globals, so locals-only namespaces break e.g.
        # [len(w) for w in ...].
        namespace = {
            "__builtins__": {},
            **_SAFE_NAMES,
            "content": text,
            "codec": artifact.codec,
        }
        try:
            _validate_predicate(arg)  # reject sandbox-escape shapes first
            verdict = PASS if bool(eval(arg, namespace)) else FAIL
            detail: dict = {}
        except Exception as e:  # noqa: BLE001 - a predicate error is a failed verdict
            verdict, detail = FAIL, {"error": str(e)}
    elif kind == "program":
        fn = PROGRAMS.get(arg)
        if fn is None:
            raise NotEvaluable(f"unknown program: {arg}")
        # Programs receive the artifact too: structural checks (lineage_ref)
        # read interface.refs, which is part of the content-addressed id, so
        # the verdict stays a pure function of the artifact (§0).
        verdict, detail = fn(text, commitment.budget, artifact)
    elif kind == "rubric":
        raise NotEvaluable("rubric verdicts require the trial protocol (spec §3/§10, P5)")
    else:
        raise NotEvaluable(f"unknown eval kind: {commitment.eval}")
    # Verdicts are a deterministic function of content (§0): wall-clock must
    # never drive them, and no wall-clock value may enter the content-
    # addressed trace, or two runs from identical inputs would fork the log.
    trace = {
        "commitment": commitment.id,
        "eval": commitment.eval,
        "verdict": verdict,
        **detail,
    }
    return verdict, trace
