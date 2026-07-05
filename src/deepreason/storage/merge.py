"""Merge (spec §14, P3): componentwise set-union + re-adjudicate.

G-Set CRDT — no conflicts possible: everything is append-only and
content-addressed. Identical artifacts dedupe by id; school-policy
artifacts union like any artifact (the scheduler reconciles rosters from
the roster() replay). The merge walks the SOURCE log in order and emits
one Merge event per source event that contributed anything new, preserving
inputs — so addr pairs and Measure payloads reconstruct, and the merged
log remains a faithful replayable history. Adjudication recomputes after
every Merge event (Adj: after any registration).

Dangling refs/warrant-targets from either side materialize as edges when
the union supplies the missing endpoint — that is the CRDT doing its job.

Session namespaces: a session IS a harness root directory (`--root`);
merge unions another session into the current one.
"""

import shutil
from pathlib import Path

from deepreason.ontology import Rule


def _known(harness, oid: str) -> bool:
    return (
        oid in harness.state.artifacts
        or oid in harness.state.problems
        or oid in harness.commitments
        or oid in harness.warrants
    )


def _signature(inputs, outputs, hv_set, reach_set) -> tuple:
    """Content signature of an event's contribution, independent of rule/seq
    (a source Conj becomes a target Merge). Union semantics (G-Set CRDT):
    identical contributions collapse, so a re-merge or shared prefix is a
    no-op — but a re-measurement (same key, new value) is a distinct
    signature and is preserved, so the latest value wins in source order."""
    return (
        tuple(inputs),
        tuple(outputs),
        tuple(sorted(hv_set.items())),
        tuple(sorted(reach_set.items())),
    )


def merge(harness, source_root: Path) -> dict:
    """Union the session at source_root into harness. Returns stats.

    Every source event that carries a contribution not already present is
    re-emitted as a Merge event preserving its full inputs and outputs — so
    addr (artifact-addresses-problem) pairs reconstruct even when the
    artifact itself is already known, diagnostic Measure events survive, and
    hv/reach re-estimates apply in order (latest wins)."""
    from deepreason.harness import Harness

    source = Harness(source_root)
    # Blob union: content-addressed files, so copy-if-absent is the union.
    blobs_copied = 0
    for path in source.blobs.root.rglob("*"):
        if not path.is_file():
            continue
        dest = harness.blobs.root / path.relative_to(source.blobs.root)
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            blobs_copied += 1

    # Existing contributions (this session's own history) are already merged.
    seen = {
        _signature(e.inputs, e.outputs, e.state_diff.hv_set, e.state_diff.reach_set)
        for e in harness.log.read()
    }

    merged_events = 0
    merged_objects = 0
    for event in source.log.read():
        sig = _signature(
            event.inputs, event.outputs, event.state_diff.hv_set, event.state_diff.reach_set
        )
        if sig in seen:
            continue  # already present (re-merge / shared prefix)
        seen.add(sig)
        new_outputs = [oid for oid in event.outputs if not _known(harness, oid)]
        for oid in new_outputs:
            schema, obj = source.objects.get(oid)
            harness.objects.put(schema, obj)
        # Full outputs (not just the new ones): _apply_event re-forms addr
        # pairs from (artifact output, problem input), which requires the
        # known artifact to be present in the event's outputs.
        harness._commit(
            Rule.MERGE,
            inputs=list(event.inputs),
            outputs=list(event.outputs),
            hv_set=dict(event.state_diff.hv_set),
            reach_set=dict(event.state_diff.reach_set),
        )
        merged_events += 1
        merged_objects += len(new_outputs)
    return {
        "merged_events": merged_events,
        "merged_objects": merged_objects,
        "blobs_copied": blobs_copied,
    }
