#!/usr/bin/env python3
"""Show the defect on the COMMITTED P-R1 root. No live run, no provider call.

Reads `experiments/2026-08-25-poietics-program/run` READ-ONLY (dr-drive-harness
§5: a writable open repairs, i.e. destroys, the evidence) and prints three
facts, each from the record rather than from prose:

  1. what `deepreason results` reports as the survivor count today;
  2. how that set partitions by `provenance.role` over replayed state;
  3. that every IMPORT member was registered and accepted BEFORE the first
     LLM-bearing event in the log -- so it survived no criticism at all.

Exit 0 always: this is an instrument, not a gate. The assertion that inverts
after the fix lives in `tests/test_import_role_survivors.py`.

Usage:  python experiments/2026-08-25-fix-import-role-survivors/repro.py
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
ROOT = REPO / "experiments" / "2026-08-25-poietics-program" / "run"


def main() -> int:
    sys.path.insert(0, str(REPO / "src"))
    from deepreason.application.results import results_summary
    from deepreason.harness import Harness
    from deepreason.ontology.artifact import ProvenanceRole

    summary = results_summary(ROOT)
    reported = summary["artifacts"]["survivor_count"]
    print(f"deepreason results        survivor_count = {reported}")
    print(f"                          frontier       = "
          f"{summary['artifacts']['frontier']['count']}")

    harness = Harness(ROOT, read_only=True)
    state = harness.state
    stored = json.loads((ROOT / "run-result.json").read_text())["survivors"]
    by_role = collections.Counter(
        state.artifacts[aid].provenance.role.value for aid in stored
    )
    print(f"stored survivor set       {len(stored)} ids -> " + ", ".join(
        f"{n} {role}" for role, n in sorted(by_role.items())
    ))

    imports = [
        aid for aid in stored
        if state.artifacts[aid].provenance.role == ProvenanceRole.IMPORT
    ]
    registered = {}
    first_llm = None
    for event in harness.log.read():
        if event.rule == "Register" and event.outputs and event.outputs[0] in set(imports):
            registered[event.outputs[0]] = event.seq
        if first_llm is None and event.llm is not None:
            first_llm = event.seq
    seqs = sorted(registered.values())
    print(f"IMPORT members registered at log seqs {seqs[0]}-{seqs[-1]}; "
          f"first LLM-bearing event is seq {first_llm}")
    print(f"                          -> all {len(imports)} were accepted "
          f"{'BEFORE' if seqs[-1] < first_llm else 'after'} any model was consulted")

    addressed = collections.Counter(pid for aid, pid in state.addr if aid in set(imports))
    print(f"IMPORT members address    {dict(addressed)}")
    print()
    print(f"DEFECT: the invariant says import-role admission records never "
          f"count as survivors.\n        The surface counts {len(imports)} of "
          f"them, reporting {reported} where the record supports "
          f"{len(stored) - len(imports)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
