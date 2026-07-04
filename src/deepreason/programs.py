"""Budgeted test programs tau_kappa (spec §1).

V(kappa, c) = U^{<=beta}(tau_kappa, c) in {pass, fail, overrun}: extensional,
budgeted, decidable. ``eval:program|predicate`` verdicts are computed here
(reliable). ``eval:rubric`` verdicts exist only downstream of the trial
guard (§3, §10 — P5) and raise NotEvaluable here.

P1 budget honesty: predicates run to completion and the elapsed time is
checked afterwards (overrun is reported, not preempted); registry programs
receive the budget and may enforce it internally.
"""

import json
import re
import time

from deepreason.ontology.artifact import Artifact
from deepreason.ontology.commitment import Commitment

PASS, FAIL, OVERRUN = "pass", "fail", "overrun"


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


def _json_wf(text: str, budget) -> tuple[str, dict]:
    try:
        json.loads(text)
        return PASS, {"parsed": True}
    except Exception as e:  # noqa: BLE001 - verdicts must not crash the harness
        return FAIL, {"error": str(e)}


def _skeleton_wf(text: str, budget) -> tuple[str, dict]:
    from deepreason.informal.skeleton import skeleton_wf_program

    return skeleton_wf_program(text, budget)


# Named program registry. hv_floor is deliberately NOT here: it needs the
# variator (measures/hv.py), and keeping it out makes B0 stratification
# structural (spec §7).
PROGRAMS = {
    "json-wf": _json_wf,
    "skeleton_wf": _skeleton_wf,
}


def evaluable(commitment: Commitment) -> bool:
    kind, _, arg = commitment.eval.partition(":")
    return kind == "predicate" or (kind == "program" and arg in PROGRAMS)


def evaluate(commitment: Commitment, artifact: Artifact, blobs) -> tuple[str, dict]:
    """Run tau_kappa on the artifact's real bytes; return (verdict, trace)."""
    kind, _, arg = commitment.eval.partition(":")
    text = content_text(artifact, blobs)
    started = time.monotonic()
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
            verdict = PASS if bool(eval(arg, namespace)) else FAIL
            detail: dict = {}
        except Exception as e:  # noqa: BLE001 - a predicate error is a failed verdict
            verdict, detail = FAIL, {"error": str(e)}
    elif kind == "program":
        fn = PROGRAMS.get(arg)
        if fn is None:
            raise NotEvaluable(f"unknown program: {arg}")
        verdict, detail = fn(text, commitment.budget)
    elif kind == "rubric":
        raise NotEvaluable("rubric verdicts require the trial protocol (spec §3/§10, P5)")
    else:
        raise NotEvaluable(f"unknown eval kind: {commitment.eval}")
    elapsed_ms = int((time.monotonic() - started) * 1000)
    if commitment.budget.time_ms is not None and elapsed_ms > commitment.budget.time_ms:
        verdict = OVERRUN
    trace = {
        "commitment": commitment.id,
        "eval": commitment.eval,
        "verdict": verdict,
        "elapsed_ms": elapsed_ms,
        **detail,
    }
    return verdict, trace
