#!/usr/bin/env python3
"""Select the fixed target set: 120 accepted conjectures from six committed roots.

Deterministic and rerunnable. No randomness, no LLM calls, no writes to any
committed root -- every artifact is COPIED out by content, and the roots are
opened read-only (a writable open repairs, i.e. destroys, the evidence).

Selection rule, fixed before any call (SPEC S5): every eligible artifact in
every source root, ordered by sha256 of its artifact id, first 120 taken. The
first 60 of that order are PLANTED, the last 60 CLEAN. The ordering key is the
artifact id's digest rather than the id itself so that the split cannot track
anything the harness assigns in sequence -- ids are already content-addressed,
but their ORDER in a root is not, and sorting on the raw id would let the
split correlate with content.

Eligible = ACCEPTED, not import-role bookkeeping, provenance role
`conjecturer`, a JSON body carrying a non-empty `claim`, a non-empty
`mechanism` and a `scope` object, AND at least one recorded objection against
it. The body clauses are what the planting mutators need (SPEC S6); an
artifact missing one of them could not carry every defect class, and a pool
whose members can carry different class sets would confound class with target.

The history clause is SPEC Amendment A9, and it is a power requirement rather
than a taste: without it, 25 of the 60 planted targets would have had no
history to show or withhold, so cell C01 would have rendered byte-identical to
C00 for them and factor F2 would have been measured on 70 observations per
level against the 99 its own arithmetic demands. 137 of 238 qualify; 120 are
taken.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent

# The six roots named in SPEC.md M1: P-A2's own run, and the five candidate
# roots of the history experiment this tranche continues.
SOURCE_ROOTS = (
    "experiments/2026-09-02-live-p-a2-corrected/run",
    "experiments/2026-09-03-change-provenance-history-channel/runs/home-m3/runs/run-7a8fc89b33f8e055a212fafa09acd83f",
    "experiments/2026-09-03-change-provenance-history-channel/runs/home-m3/runs/run-5565bd1ef7011e3d25fef3197bdf1cdb",
    "experiments/2026-09-03-change-provenance-history-channel/runs/home-m1/runs/run-f23da86ddfd5ab820957221cfebe4b2e",
    "experiments/2026-09-03-change-provenance-history-channel/runs/home-m1/runs/run-ad41064484366337ed61a9d5a58de58f",
    "experiments/2026-09-03-change-provenance-history-channel/runs/home-default/runs/run-fe00609058e10605590206d51ab2b7a0",
)

TOTAL = 120
PLANTED = 60


def _body(harness, artifact):
    ref = artifact.content_ref
    raw = ref[len("inline:"):] if ref.startswith("inline:") else harness.blobs.get(ref)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def _history(harness, target_id: str) -> list[dict]:
    """Objections already recorded against this target, and their outcome.

    BOTH channels, in the order `DR-CON-discharge-channel` fixes: scrutiny
    Measures (an objection that warranted nothing -- the abundant case, PARKED
    P7 CORRECTED) and `att` edges (an objection that landed). Read from the
    source root's own log, never invented, so cell C01's brief carries the
    history the record actually holds for this artifact.
    """
    state = harness.state
    rows: list[dict] = []
    seq = 0
    for line in (harness.root / "log.jsonl").open(encoding="utf-8"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        inputs = event.get("inputs") or []
        if event.get("rule") == "Measure" and inputs[:1] == ["scrutiny"] and len(inputs) >= 3:
            if str(inputs[1]) != target_id:
                continue
            seq += 1
            critic = state.artifacts.get(str(inputs[2]))
            rows.append({
                "seq": seq,
                "objection": _text_of(harness, critic),
                "landed": False,
            })
    for attacker, target in state.att:
        if target != target_id:
            continue
        seq += 1
        rows.append({
            "seq": seq,
            "objection": _text_of(harness, state.artifacts.get(attacker)),
            "landed": True,
        })
    return [row for row in rows if row["objection"]]


def _text_of(harness, artifact) -> str:
    if artifact is None:
        return ""
    ref = artifact.content_ref
    raw = ref[len("inline:"):] if ref.startswith("inline:") else harness.blobs.get(ref)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if not raw:
        return ""
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return " ".join(str(raw).split())
    if isinstance(parsed, dict):
        for key in ("case", "claim", "content"):
            if parsed.get(key):
                return " ".join(str(parsed[key]).split())
        return ""
    return " ".join(str(parsed).split())


def eligible():
    from deepreason.harness import Harness
    from deepreason.ontology.state import counts_as_survivor

    rows = []
    for rel in SOURCE_ROOTS:
        root = REPO / rel
        harness = Harness(root, read_only=True)
        state = harness.state
        for artifact_id in sorted(state.artifacts):
            artifact = state.artifacts[artifact_id]
            if not counts_as_survivor(state, artifact_id):
                continue
            if artifact.provenance.role.value != "conjecturer":
                continue
            body = _body(harness, artifact)
            if not isinstance(body, dict):
                continue
            if not body.get("claim") or not body.get("mechanism"):
                continue
            if not isinstance(body.get("scope"), dict):
                continue
            history = _history(harness, artifact_id)
            if not history:
                continue
            rows.append({
                "artifact_id": artifact_id,
                "source_root": rel,
                "school": artifact.provenance.school,
                "role": artifact.provenance.role.value,
                "event_seq": artifact.provenance.event_seq,
                "body": body,
                "history": history,
            })
    return rows


def select(rows):
    ordered = sorted(rows, key=lambda r: hashlib.sha256(r["artifact_id"].encode()).hexdigest())
    chosen = ordered[:TOTAL]
    for index, row in enumerate(chosen):
        row["target_id"] = "T%03d" % (index + 1)
        row["arm"] = "planted" if index < PLANTED else "clean"
    return chosen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    rows = eligible()
    chosen = select(rows)
    assert len(chosen) == TOTAL, len(chosen)
    assert sum(r["arm"] == "planted" for r in chosen) == PLANTED
    assert len({r["artifact_id"] for r in chosen}) == TOTAL, "duplicate artifact id"

    payload = {
        "schema": "blind-critic-selection.v1",
        "total": TOTAL,
        "planted": PLANTED,
        "eligible_seen": len(rows),
        "source_roots": list(SOURCE_ROOTS),
        "rule": "sha256(artifact_id) ascending; first 120; first 60 planted",
        "targets": chosen,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if args.write:
        (HERE / "SELECTION.json").write_text(text, encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    (HERE / "SELECTION.sha256").write_text(f"{digest}  SELECTION.json\n", encoding="utf-8")
    print(f"{len(chosen)} selected")
    print(f"eligible seen: {len(rows)}")
    print(f"with recorded history: {sum(1 for r in chosen if r['history'])}")
    print(f"SELECTION.sha256: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
