#!/usr/bin/env python3
"""W4 Q4: assemble a stratified 30-per-root commitment-verdict sample for
HAND checking.

Why by hand, when W2 already checked all 463 mechanically. W2 re-derived
each verdict with `deepreason.programs.evaluate` -- the same evaluator that
produced the verdict in the first place. That answers "is the record
internally consistent", which it is, 463/463; it cannot answer "did the
verdict rule correctly on the artifact", because an evaluator bug would
reproduce itself identically on both sides. This sampler prepares the
inputs for an INDEPENDENT ruling: the artifact's own content bytes, the
commitment's `eval` expression, and the recorded verdict, with nothing
pre-evaluated. Every ruling in ADJUDICATION_SAMPLE.md is made against
these bytes by a reader, not by this script.

STRATIFICATION, and why it is deliberately NOT proportional. P-R1's 118
verdicts are 99 from one criterion and 8-9 each from two others, plus 2
from a non-problem commitment. A proportional 30 would spend 25 rows on
the criterion whose behaviour is already best evidenced and 1 on the rest.
The sample instead takes every row of each SMALL family and fills the
remainder from the largest one, so each criterion family gets a real test:

    P-R1  poietics-confound@v1               12 of 99
          poietics-constraint-condition@v1    8 of  9
          poietics-installation-mechanism@v1  8 of  8
          relation-form@578e42df713e          2 of  2
    P-C1  frontier-above-floor@v1            10 of 163
          frontier-claim-honest@v1           10 of 148
          frontier-wellformed@v1             10 of  34

Selection inside a family is deterministic and spread, never random: rows
are ordered by log seq and taken at even stride, so the sample covers the
run's whole timeline rather than its first cycle. No clock, no RNG -- the
same commit yields the same 60 rows.

Writes verdict_sample.json (machine inputs) and prints a per-family tally.
Roots are opened as files; no Harness is constructed and no root is
written.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
W2 = REPO / "experiments/2026-08-26-run-anatomy-w2-criticism"
OUT = HERE / "verdict_sample.json"

# W2's committed per-verdict census is the FRAME (which verdicts exist, on
# which targets, under which commitment). Its `rederived_verdict` column is
# deliberately NOT carried into the sample: importing W2's answer would let
# it anchor the hand ruling, which is the one thing this sample exists to
# avoid.
PLAN = {
    "P-R1": {
        "census": W2 / "pr1_census.json",
        "quota": {
            "poietics-confound@v1": 12,
            "poietics-constraint-condition@v1": 8,
            "poietics-installation-mechanism@v1": 8,
            "relation-form@578e42df713e": 2,
        },
    },
    "P-C1": {
        "census": W2 / "pc1_census.json",
        "quota": {
            "frontier-above-floor@v1": 10,
            "frontier-claim-honest@v1": 10,
            "frontier-wellformed@v1": 10,
        },
    },
}


_INDEX: dict[str, dict[str, Path]] = {}


def artifact_index(root: Path) -> dict[str, Path]:
    """artifact id -> its object file.

    The object store is keyed by the OBJECT digest (the hash of the stored
    record), not by the artifact id the log and the warrants refer to, so a
    direct `objects/artifact/<artifact_id>.json` lookup misses every time
    and would report all 60 sampled rows as content-unresolved. The index
    is built once per root from `data.id`.
    """
    key = str(root)
    if key not in _INDEX:
        index: dict[str, Path] = {}
        for path in (root / "objects" / "artifact").glob("*.json"):
            try:
                record = json.loads(path.read_text()).get("data", {})
            except (ValueError, OSError):
                continue
            aid = str(record.get("id") or "")
            if aid:
                index[aid] = path
        _INDEX[key] = index
    return _INDEX[key]


def artifact_content(root: Path, artifact_id: str) -> str | None:
    """The artifact's own content bytes, resolved through its content_ref.

    Two encodings appear across the roots: `inline:<text>` on the record
    itself, and a blob content ref. Both are resolved; anything else
    returns None and is reported as `content-unresolved` rather than being
    silently rendered as an empty string, which would make every predicate
    read false.
    """
    path = artifact_index(root).get(artifact_id)
    if path is None:
        return None
    record = json.loads(path.read_text()).get("data", {})
    ref = str(record.get("content_ref") or "")
    if ref.startswith("inline:"):
        return ref[len("inline:"):]
    digest = ref.split(":", 1)[-1] if ":" in ref else ref
    if len(digest) > 2:
        blob = root / "blobs" / digest[:2] / digest
        if blob.exists():
            return blob.read_text()
    return None


def stride_pick(rows: list[dict], k: int) -> list[dict]:
    """Take k rows at even stride across a seq-ordered family."""
    rows = sorted(rows, key=lambda r: (r.get("seq") or 0, r.get("warrant", "")))
    if k >= len(rows):
        return rows
    step = len(rows) / k
    return [rows[int(i * step)] for i in range(k)]


def build(name: str, spec: dict) -> dict:
    census = json.loads(spec["census"].read_text())
    root = Path(census["root"])
    families: dict[str, list[dict]] = {}
    for row in census["mechanical"]:
        families.setdefault(row["commitment"], []).append(row)
    picked: list[dict] = []
    tally: dict[str, dict] = {}
    for commitment, quota in spec["quota"].items():
        rows = families.get(commitment, [])
        chosen = stride_pick(rows, quota)
        tally[commitment] = {"available": len(rows), "sampled": len(chosen)}
        for row in chosen:
            content = artifact_content(root, row["target"])
            picked.append(
                {
                    "root": name,
                    "seq": row["seq"],
                    "commitment": commitment,
                    "eval": row["eval"],
                    "target": row["target"],
                    "recorded_verdict": row["claimed_verdict"],
                    "warrant": row["warrant"],
                    "warrant_type": row["warrant_type"],
                    "target_status_final": row["target_status"],
                    "commitment_in_target_interface": row["in_target_interface"],
                    "warrant_materialized_attack_edge": row["attacks_target_in_att"],
                    "content": content,
                    "content_resolved": content is not None,
                    "content_chars": len(content) if content is not None else 0,
                }
            )
    return {
        "root_path": str(root.relative_to(REPO)),
        "verdicts_available": len(census["mechanical"]),
        "families": tally,
        "sample": sorted(picked, key=lambda r: (r["commitment"], r["seq"])),
    }


def main() -> int:
    payload = {
        "schema": "w4.verdict-sample.v1",
        "frame": "experiments/2026-08-26-run-anatomy-w2-criticism (W2 per-verdict census)",
        "roots": {name: build(name, spec) for name, spec in PLAN.items()},
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    total = 0
    for name, row in payload["roots"].items():
        n = len(row["sample"])
        total += n
        unresolved = sum(1 for r in row["sample"] if not r["content_resolved"])
        print(f"== {name} {row['root_path']}  sampled {n}  unresolved-content {unresolved}")
        for commitment, counts in sorted(row["families"].items()):
            print(f"   {commitment:38s} {counts['sampled']:3d} of {counts['available']:3d}")
    print(f"total sampled rows: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
