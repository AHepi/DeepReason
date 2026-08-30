"""The DEFAULT successor-question destination: one advisory scratch block.

Operator, 2026-08-29: "If it is filled in, it goes to scratchpad by default,
linked to the problem it was proposed under and visible by conjecturers." The
link is `ScratchProvenanceV1.origin`, which is a free string outside the
block's `body_hash`, so carrying it costs no stored block id; the visibility is
the ordinary attention pack, which selects the block like any other.

Two rules this module inherits rather than invents:

- An UNINVITED dispatch records NOTHING (`DR-CON-criticism-source`). A
  criticism that left the field empty leaves no receipt at all, so silence in
  the record means "nothing was proposed" and not "something was dropped".
- A destination that cannot accept the question DISCLOSES rather than
  discarding it, and never refuses (the all-configurations law).

The writer is REGISTERED against its declaration rather than named in a
branch, so a second destination is a registration and not an edit here.
"""

from __future__ import annotations

from deepreason.successor.registry import (
    DEFAULT_DESTINATION_ID,
    DESTINATIONS,
    register_destination,
    resolve,
    writer_for,
)

# The receipt family. Its meaning is declared once in `signals.py` under
# `DR-REC-add-signal` and never restated at an emit site.
RECEIPT_PREFIX = "successor-question:"


class SuccessorDestinationUnavailable(RuntimeError):
    """The selected destination cannot accept a question in this run.

    Typed at the point of USE, never at compile: an unreachable destination is
    an impossibility where it is consumed, not a configuration that should have
    been refused (the all-configurations law).
    """


def _write_scratch_block(harness, config, *, problem_id, question, llm_call=None):
    # Imported at call time so the registry stays importable without the
    # workspace, exactly as `rules/crit.py` imports `premises` late.
    from deepreason.scratch.errors import ScratchReadOnly
    from deepreason.scratch.models import ScratchProvenanceV1
    from deepreason.scratch.service import ScratchService

    # The run's own scratch policy, read at the CONFIGURATION layer like every
    # other decision in this package: a manifest-launched run has this
    # reconstructed onto its Config from the compiled policy, so there is one
    # answer rather than two that can disagree. A configuration that carries no
    # scratch policy at all says nothing, and silence is not a refusal.
    policy = getattr(config, "scratchpad", None)
    if policy is not None and not getattr(policy, "enabled", False):
        raise SuccessorDestinationUnavailable(
            "this run's scratch workspace is disabled"
        )
    service = ScratchService(harness)
    try:
        return service.create_block(
            # `unfinished` rather than a new body field: adding one moved every
            # stored block id (measured ff609dcc -> 248b3201 for the same
            # content), and this is the shape `scratch/authoring.py` already
            # uses for an unresolved question.
            {"content": question, "unfinished": "Successor question"},
            # `llm` is the only actor an interpretive scratch action may carry;
            # the event validator refuses a harness-authored BLOCK_CREATED.
            ScratchProvenanceV1(actor="llm", origin=problem_id),
            llm=llm_call,
        )
    except ScratchReadOnly as exc:
        raise SuccessorDestinationUnavailable("this scratch view is read-only") from exc


register_destination(DESTINATIONS[DEFAULT_DESTINATION_ID], _write_scratch_block)


def route(harness, config, *, problem_id, question, llm_call=None):
    """Send one proposed successor question to the destination this run selects.

    Returns whatever the destination's writer returned, or None when nothing
    was routed. Exactly one typed receipt is recorded per FILLED question and
    none at all for an empty one.
    """
    text = (question or "").strip()
    if not text:
        return None
    destination = resolve(config)
    if not problem_id:
        # The law's own condition -- "linked to the problem it was proposed
        # under" -- cannot be met, so nothing is routed and the absence is
        # recorded rather than inferred.
        harness.record_measure(inputs=[f"{RECEIPT_PREFIX}UNLINKED", destination.id])
        return None
    writer = writer_for(destination.id)
    if writer is None:
        harness.record_measure(
            inputs=[f"{RECEIPT_PREFIX}UNAVAILABLE", destination.id, problem_id]
        )
        return None
    try:
        written = writer(
            harness, config, problem_id=problem_id, question=text, llm_call=llm_call
        )
    except SuccessorDestinationUnavailable:
        harness.record_measure(
            inputs=[f"{RECEIPT_PREFIX}UNAVAILABLE", destination.id, problem_id]
        )
        return None
    harness.record_measure(
        inputs=[f"{RECEIPT_PREFIX}ROUTED", destination.id, problem_id]
    )
    return written
