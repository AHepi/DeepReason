"""Merge (spec §14, P3): compatible set-union + re-adjudicate.

Everything is append-only and content-addressed. Identical records dedupe by
id; a same-id schema or byte conflict is rejected rather than resolved by
merge order. School-policy artifacts union like any artifact (the scheduler
reconciles rosters from the roster() replay). The merge walks the SOURCE log
in order and emits one Merge event per source event that contributed anything
new, preserving the complete contribution and LLM provenance — so addr/carry
pairs and Measure payloads reconstruct, and the merged log remains a faithful
replayable history. Adjudication recomputes after every Merge event (Adj:
after any registration).

Dangling refs/warrant-targets from either side materialize as edges when
the union supplies the missing endpoint — that is the CRDT doing its job.

Session namespaces: a session IS a harness root directory (`--root`);
merge unions another session into the current one.
"""

from pathlib import Path

from deepreason.log.event_log import EventLog
from deepreason.ontology import Rule


class ControlEventMergeError(ValueError):
    """A source authority trace cannot be truthfully rewritten as Merge."""


def _known(harness, oid: str) -> bool:
    return (
        oid in harness.state.artifacts
        or oid in harness.state.problems
        or oid in harness.commitments
        or oid in harness.warrants
    )


def _signature(event) -> tuple:
    """Content signature of an event's contribution, independent of rule/seq
    (a source Conj becomes a target Merge). Set-union semantics:
    identical contributions collapse, so a re-merge or shared prefix is a
    no-op — but a re-measurement (same key, new value) is a distinct
    signature and is preserved, so the latest value wins in source order."""
    return (
        tuple(event.inputs),
        tuple(event.outputs),
        tuple(sorted(event.state_diff.hv_set.items())),
        tuple(sorted(event.state_diff.reach_set.items())),
        tuple(event.state_diff.addr_add),
        tuple(event.state_diff.carry_add),
        event.llm.model_dump_json() if event.llm is not None else None,
    )


def merge(harness, source_root: Path) -> dict:
    """Union the session at source_root into harness. Returns stats.

    Every source event that carries a contribution not already present is
    re-emitted as a Merge event preserving its inputs, outputs, state payload,
    and LLM record — so addr/carry relations reconstruct even when an artifact
    is already known, diagnostic Measure events survive, and hv/reach
    re-estimates apply in order (latest wins)."""
    from deepreason.harness import Harness

    harness._ensure_writable()
    source_root = Path(source_root)

    # A Merge event deliberately rewrites the source rule while preserving a
    # formal set contribution.  That is sound for ontology history, but not
    # for authority transitions: rewriting Control as Merge would discard its
    # typed payload and make the destination claim a process history it never
    # replayed.  Scan the complete source log before opening object/blob copy
    # loops so rejection cannot partially mutate the destination.
    source_events = tuple(
        EventLog(source_root / "log.jsonl", read_only=True).read()
    )
    if any(event.rule == Rule.CONTROL for event in source_events):
        raise ControlEventMergeError(
            "cannot merge a source containing Control events; "
            "workflow authority must retain its original process branch"
        )
    if any(
        event.llm is not None and event.llm.work_order_id is not None
        for event in source_events
    ):
        raise ControlEventMergeError(
            "cannot merge a source containing a work-bound provider call; "
            "workflow authority must retain its original process branch"
        )

    source = Harness(source_root, read_only=True)
    # Blob union: content-addressed files, so copy-if-absent is the union.
    blobs_copied = 0
    for path in source.blobs.root.rglob("*"):
        if not path.is_file():
            continue
        dest = harness.blobs.root / path.relative_to(source.blobs.root)
        if not dest.exists():
            harness.blobs.put(path.read_bytes())
            blobs_copied += 1

    # Existing contributions (this session's own history) are already merged.
    seen = {
        _signature(e)
        for e in harness.log.read()
    }

    merged_events = 0
    merged_objects = 0
    for event in source_events:
        sig = _signature(event)
        if sig in seen:
            continue  # already present (re-merge / shared prefix)
        seen.add(sig)
        new_outputs = []
        for oid in event.outputs:
            schema, obj = source.objects.get(oid)
            is_new = not _known(harness, oid)
            # put() is also the immutable same-ID equality check.
            harness.objects.put(schema, obj)
            if is_new:
                new_outputs.append(oid)
        # Full outputs (not just the new ones): _apply_event re-forms addr
        # pairs from (artifact output, problem input), which requires the
        # known artifact to be present in the event's outputs.
        harness._commit(
            Rule.MERGE,
            inputs=list(event.inputs),
            outputs=list(event.outputs),
            llm=event.llm,
            hv_set=dict(event.state_diff.hv_set),
            reach_set=dict(event.state_diff.reach_set),
            addr_add=list(event.state_diff.addr_add),
            carry_add=list(event.state_diff.carry_add),
        )
        merged_events += 1
        merged_objects += len(new_outputs)
    return {
        "merged_events": merged_events,
        "merged_objects": merged_objects,
        "blobs_copied": blobs_copied,
    }


__all__ = ["ControlEventMergeError", "merge"]
