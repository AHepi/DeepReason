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


def merge(harness, source_root: Path) -> dict:
    """Union the session at source_root into harness. Returns stats."""
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

    merged_events = 0
    merged_objects = 0
    for event in source.log.read():
        new_outputs = [oid for oid in event.outputs if not _known(harness, oid)]
        hv_new = {
            k: v for k, v in event.state_diff.hv_set.items() if k not in harness.state.hv
        }
        reach_new = {
            k: v
            for k, v in event.state_diff.reach_set.items()
            if k not in harness.state.reach
        }
        if not new_outputs and not hv_new and not reach_new:
            continue
        for oid in new_outputs:
            schema, obj = source.objects.get(oid)
            harness.objects.put(schema, obj)
        harness._commit(
            Rule.MERGE,
            inputs=list(event.inputs),
            outputs=new_outputs,
            hv_set=hv_new,
            reach_set=reach_new,
        )
        merged_events += 1
        merged_objects += len(new_outputs)
    return {
        "merged_events": merged_events,
        "merged_objects": merged_objects,
        "blobs_copied": blobs_copied,
    }
