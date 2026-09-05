#!/usr/bin/env python3
"""The number R13 says is the point: how much of the committed record ever
survived anything.

Runs the SHIPPED reader — `deepreason.views.evidence_states`, not a second
implementation of it — over every committed run root and tables the four
readings, both over all admitted artifacts and over the published FRONTIER,
which is the set a reader of `deepreason results` actually looks at.

Every root is opened READ-ONLY and discovered from `git ls-files`, so the table
is re-derivable by anyone holding the commit and cannot silently include a
session-local root that will not exist tomorrow.

    python experiments/2026-09-04-change-evidence-states/census.py
    python experiments/2026-09-04-change-evidence-states/census.py --root <one root>
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
STATES = ("open", "supported", "refuted", "contested")


def committed_roots() -> list[pathlib.Path]:
    """Every git-tracked run root, newest path order deterministic by sort."""

    listed = subprocess.run(
        ["git", "ls-files", "--", "*/log.jsonl"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.split()
    # A run ROOT is a log beside an object store. `.swarm/log.jsonl` is the
    # treadle board — a different kind of log entirely — and counting it as an
    # unreadable run root would report a category error as a finding.
    return sorted(
        REPO / line
        for line in listed
        if line.endswith("log.jsonl") and (REPO / line).parent.joinpath("objects").is_dir()
    )


def read(root: pathlib.Path) -> dict | None:
    from deepreason.harness import Harness
    from deepreason.views.evidence_states import evidence_states, evidence_state_summary

    try:
        harness = Harness(root, read_only=True)
        summary = evidence_state_summary(harness)
        readings = evidence_states(harness)
    except Exception as exc:  # noqa: BLE001 - a legacy root may defeat the reader
        return {"unreadable": f"{type(exc).__name__}: {exc}"}

    frontier: list[str] = []
    result = root / "run-result.json"
    if result.is_file():
        try:
            frontier = list(json.loads(result.read_text()).get("frontier") or ())
        except ValueError:
            frontier = []
    frontier_counts = collections.Counter(
        readings[aid].value if aid in readings else "not-admitted" for aid in frontier
    )
    return {
        "counts": summary["counts"],
        "frontier": dict(frontier_counts),
        "frontier_size": len(frontier),
        "declared": not summary["completeness"].get("absent", False),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", default=None)
    args = parser.parse_args()

    roots = (
        [REPO / r / "log.jsonl" for r in args.root] if args.root else committed_roots()
    )
    total = collections.Counter()
    frontier_total = collections.Counter()
    unreadable: list[str] = []
    declaring = 0
    rows: list[tuple[str, dict]] = []

    for log in roots:
        root = log.parent
        name = str(root.relative_to(REPO))
        reading = read(root)
        if reading is None or "unreadable" in reading:
            unreadable.append(f"{name}: {(reading or {}).get('unreadable')}")
            continue
        total.update(reading["counts"])
        frontier_total.update(reading["frontier"])
        declaring += bool(reading["declared"])
        rows.append((name, reading))

    print(f"# Evidence-state census over {len(rows)} committed run roots")
    print()
    print("| root | open | supported | refuted | contested | frontier o/s/r/c |")
    print("|---|---|---|---|---|---|")
    for name, reading in rows:
        counts, front = reading["counts"], reading["frontier"]
        print(
            f"| `{name}` | {counts['open']} | {counts['supported']} | "
            f"{counts['refuted']} | {counts['contested']} | "
            + "/".join(str(front.get(s, 0)) for s in STATES)
            + " |"
        )
    print()
    print("## Totals")
    print()
    admitted = sum(total[s] for s in STATES)
    print(f"- admitted artifacts read: **{admitted}**")
    for state in STATES:
        share = (100.0 * total[state] / admitted) if admitted else 0.0
        print(f"  - {state}: **{total[state]}** ({share:.1f}%)")
    frontier_read = sum(frontier_total[s] for s in STATES)
    print(f"- frontier artifacts read: **{frontier_read}**")
    for state in STATES:
        share = (100.0 * frontier_total[state] / frontier_read) if frontier_read else 0.0
        print(f"  - {state}: **{frontier_total[state]}** ({share:.1f}%)")
    print(f"- roots carrying a criticism-dispatch declaration: "
          f"**{declaring}** of {len(rows)}")
    if unreadable:
        print()
        print("## Roots the replay reader could not rebuild")
        print()
        for line in unreadable:
            print(f"- `{line}`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
