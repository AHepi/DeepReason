#!/usr/bin/env python3
"""Which (accepted artifact, foreign problem) pairs could the seed problem
have been the FOREIGN side of? Read-only over one root.

The reach census reports the exit each pair takes but not WHOSE criteria were
on the foreign side, and the reach-rich tranche's whole hypothesis is about
one specific foreign side: the SEED problem, carrying operator-authored
subject predicates. This walks reach_sweep's own pair construction
(measures/reach.py::reach_sweep lines 108-124) and reports, for the seed
problem specifically, how many accepted-and-addressed artifacts ever reached
its criteria at all.

Opens the root READ-ONLY (dr-drive-harness section 5: a writable open
repairs, i.e. destroys, the evidence).

Usage:  python carrier_probe.py <root> [out.json]
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from deepreason.harness import Harness  # noqa: E402
from deepreason.measures.reach import _substantive  # noqa: E402
from deepreason.ontology.state import Status  # noqa: E402

SEED_CRITERIA = {
    "uhi-energy-balance@v1",
    "uhi-nocturnal-release@v1",
    "uhi-cross-city-modulator@v1",
}


def probe(root: pathlib.Path) -> dict:
    harness = Harness(root, read_only=True)
    state = harness.state

    addressed: dict[str, set[str]] = {}
    for aid, pid in state.addr:
        addressed.setdefault(aid, set()).add(pid)

    seed_pids = [
        pid
        for pid, problem in state.problems.items()
        if SEED_CRITERIA & set(problem.criteria)
    ]

    accepted = [
        aid
        for aid, status in state.status.items()
        if status == Status.ACCEPTED
    ]
    swept = [aid for aid in accepted if aid in addressed]

    # Of the artifacts reach_sweep actually walks, how many are addressed to
    # something OTHER than a seed-criteria problem -- i.e. could have the seed
    # problem on the foreign side at all?
    non_seed_carriers = [
        aid for aid in swept if not set(addressed[aid]) & set(seed_pids)
    ]

    # For those, does the seed pair survive reach_sweep's novelty gate?
    novelty_survivors = []
    for aid in non_seed_carriers:
        carried = set(state.artifacts[aid].interface.commitments)
        for pid in seed_pids:
            problem = state.problems[pid]
            qualifying = [
                c
                for c in problem.criteria
                if c in harness.commitments and _substantive(harness.commitments[c])
            ]
            if qualifying and (set(qualifying) - carried):
                novelty_survivors.append(
                    {
                        "artifact": aid,
                        "coverage": len(qualifying) / len(problem.criteria),
                        "novel": sorted(set(qualifying) - carried),
                        "problem": pid,
                        "qualifying": sorted(qualifying),
                    }
                )

    return {
        "accepted_artifacts": len(accepted),
        "accepted_artifacts_addressed": len(swept),
        "artifacts_that_could_have_seed_as_foreign": len(non_seed_carriers),
        "pairs_surviving_reach_novelty_gate_against_seed": novelty_survivors,
        "problems_carrying_seed_criteria": seed_pids,
        "problems_total": len(state.problems),
        "root": str(root),
    }


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: carrier_probe.py <root> [out.json]", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1])
    result = probe(root)
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) == 3 else root.parent / "carrier-probe.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"\nwrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
