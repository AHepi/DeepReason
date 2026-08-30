"""The MINTING ROAD: a critic's proposed question becomes a problem, once, and
only when a per-run gate says so.

Operator, 2026-08-29: "But build the wiring to mint, with the option to switch
it on with a flag saying something like 'may cause critics to fully consume
conjecturer role'. Switch off by default."

This is the ONE producer of the SUCCESSOR spawn trigger in the tree, and where it
lives is load-bearing rather than incidental. It sits OUTSIDE
`src/deepreason/rules/` and is never reached from `scan_spawns`, so three
standing guarantees stay exactly as they were: `DR-SEAM-ontology-x-rules`'s
two-site `ProblemProvenance.model_validate` count inside `rules/`,
`DR-SEAM-rules-x-scratch`'s six-name `scan_spawns` trigger set, and H1's
deletion -- nothing mints a problem AUTOMATICALLY FROM A REFUTATION. The road
this module opens is a different one with a different authority: an OPTIONAL
proposal a critic chose to write, under a gate that is off unless a run turns
it on.

Shape copied from `calculus/operations.py::ensure_promotion_problem`, for the
same reasons: the id is a pure function of its inputs, so re-running after a
crash between two writes registers nothing new, and criteria are passed AT
REGISTRATION because `Problem` is immutable.
"""

from __future__ import annotations

import hashlib

from deepreason.canonical import canonical_json
from deepreason.ontology.problem import Problem, ProblemProvenance, SpawnTrigger
from deepreason.successor.registry import minting_enabled

# The historical short prefix for this trigger, kept rather than re-spelled: a
# committed root already carries `succ:` problem ids and `rules/conj.py`'s
# anti-relapse domain scoping names the same family. A trigger's `.value` is
# never a problem id, so reusing the prefix moves nothing.
SUCCESSOR_PROBLEM_PREFIX = "succ:"

# The receipt family; its meaning is declared once in `signals.py`.
MINT_RECEIPT = "successor-problem-minted"


def successor_problem_id(problem_id: str, target_id: str, question: str) -> str:
    """The deterministic id for this proposal. Same inputs, same problem."""
    digest = hashlib.sha256(
        canonical_json(
            {
                "schema": "deepreason-successor-problem-identity.v1",
                "problem": problem_id,
                "target": target_id,
                "question": question,
            }
        )
    ).hexdigest()
    return f"{SUCCESSOR_PROBLEM_PREFIX}{digest[:12]}"


def mint(harness, config, *, problem_id, target_id, question):
    """Register the problem this successor question proposes, once.

    Returns the registered `Problem`, or None when the gate is off, the field
    is empty, or the proposal has no problem to descend from. The gate is
    consulted FIRST, so a run that never switched it on does no work and leaves
    no trace whatever -- the default is not merely "no problem appears", it is
    "nothing happened".
    """
    if not minting_enabled(config):
        return None
    text = (question or "").strip()
    if not text or not problem_id or not target_id:
        return None
    pid = successor_problem_id(problem_id, target_id, text)
    existing = harness.state.problems.get(pid)
    if existing is not None:
        return existing
    parent = harness.state.problems.get(problem_id)
    minted = harness.register_problem(
        Problem(
            id=pid,
            description=text,
            # Inherited rather than invented: the parent's commitment ids are
            # already registered, and a problem is immutable, so a successor
            # registered without them could be addressed before anything could
            # refuse it.
            criteria=list(parent.criteria) if parent is not None else [],
            provenance=ProblemProvenance.model_validate(
                {
                    "trigger": SpawnTrigger.SUCCESSOR,
                    "from": [problem_id, target_id],
                }
            ),
        )
    )
    harness.record_measure(inputs=[MINT_RECEIPT, pid, problem_id, target_id])
    return minted
