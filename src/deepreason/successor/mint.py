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
from deepreason.successor.registry import (
    GATES,
    MINTING_GATE_ID,
    minting_enabled,
)

# The historical short prefix for this trigger, kept rather than re-spelled: a
# committed root already carries `succ:` problem ids and `rules/conj.py`'s
# anti-relapse domain scoping names the same family. A trigger's `.value` is
# never a problem id, so reusing the prefix moves nothing.
SUCCESSOR_PROBLEM_PREFIX = "succ:"

# The receipt families; their meanings are declared once in `signals.py`.
MINT_RECEIPT = "successor-problem-minted"

# Q2 ROAD B. The operator's law names the WARNING TEXT, not the idea, and the
# ungated-seats law (2026-08-28) says switching a gate on is never a refusal and
# never SILENT. Road B puts the words in the two places that survive: declared
# on the gate's registry row (`minting_notices`, the compile-time reading) and
# written to the run's OWN APPEND-ONLY RECORD here, which is the only admissible
# evidence about what a run did. Road A -- appending them to the manifest's
# stderr notice stream -- would have cost a second frozen-surface-4 line and was
# not taken; `run_manifest.py` gains nothing beyond the two `data.pop` lines of
# the Q1 grant.
GATE_WARNING_RECEIPT = "successor-minting-gate:ENABLED"


def _record_gate_warning_once(harness) -> None:
    """Write the operator's warning to the record, the first time the gate is
    consulted while ON.

    Idempotent by SEARCHING THE RECORD rather than by a flag on this module: a
    resumed run rebuilds no module state, and a warning that vanished across a
    resume would make the record say the gate was silently on for the second
    half of the run. Same reason `discharge.channel.discharged_handles` reads
    its Measures back instead of keeping a set.

    A read-only harness cannot be written to, and this is a DISCLOSURE rather
    than a decision -- refusing to read a record because the disclosure could
    not be appended would be the wrong trade, so the append is best-effort and
    its absence changes no behaviour.
    """
    for event in harness.log.read():
        if event.inputs and event.inputs[0] == GATE_WARNING_RECEIPT:
            return
    try:
        harness.record_measure(
            inputs=[GATE_WARNING_RECEIPT, GATES[MINTING_GATE_ID].warning]
        )
    except Exception:  # a read-only view: disclose where we can, never refuse
        return


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
    # The gate is ON. Disclose that on the record BEFORE anything else, and
    # before the empty-field early return below: the operator's warning is
    # about the CONFIGURATION, so a run that switched the gate on and then
    # received no proposals must still say so.
    _record_gate_warning_once(harness)
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
