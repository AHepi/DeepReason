"""Two things are called "the re-derived verdict", and they disagree.

MEASUREMENTS.md M4/M5 said "on all six the re-derived verdict AGREES with the
root's own stored `valid: false`".  That is true of ONE re-derivation and false
of the other, and this tranche used each in a different place:

  * `verify_root(root)["violations"]` -- EVERY channel.  What `gate_probe.py`
    measured, and what the parked integrity gate (S1/S2) refused on.
  * `verify_root_report(root).summary_payload()["valid"]` -- integrity and
    security findings only.  What `application/results.py::_verification`
    publishes under `--verify`, and what the withdrawn S7 fed to `_terminal`.

A completion or epistemic finding (`foreign-criticism`, say) makes the first
say "violations" and leaves the second saying `valid: true`.  Since S1/S2 and
S7 were reasoned about as though these were one predicate, the disagreement is
worth a number rather than a caveat.

    python experiments/2026-08-30-change-checkpoint-hardening/proof/two_predicates.py

Read-only: no copy is needed because neither call writes.  Reads
gate_probe.json for the witness list, writes two_predicates.json beside itself.
Written 2026-08-30, skeptic pass.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
WITNESSES = HERE / "gate_probe.json"
OUT = HERE / "two_predicates.json"


def main() -> int:
    sys.path.insert(0, str(REPO / "src"))
    from deepreason.invariants import verify_root
    from deepreason.verification.report import verify_root_report

    # The DRIVEN witnesses only -- the six M4/M5 speaks about. The other
    # ten rows carry `skipped: over MAX_EVENTS` and were never measured
    # there, so re-deriving them would answer a question nobody asked.
    roots = [
        row["root"]
        for row in json.loads(WITNESSES.read_text())["rows"]
        if "skipped" not in row
    ]
    rows = []
    for rel in roots:
        root = REPO / rel
        stored = json.loads((root / "REPLAY_VALIDATION.json").read_text())["valid"]
        violations = verify_root(root)["violations"]
        summary = verify_root_report(root, allow_missing_terminal=True).summary_payload()
        rows.append({
            "root": rel,
            "stored_valid": stored,
            "verify_root_violations": len(violations),
            "verify_root_checks": sorted({item["check"] for item in violations}),
            "report_summary_valid": summary["valid"],
            "finding_counts": summary["finding_counts"],
        })
        print(
            f"{rel.split('/')[-1][:40]:42s} stored={stored} "
            f"viol={len(violations)} summary_valid={summary['valid']} "
            f"counts={summary['finding_counts']}",
            flush=True,
        )
    agree_violations = sum(
        1 for r in rows if (r["verify_root_violations"] > 0) == (not r["stored_valid"])
    )
    agree_summary = sum(1 for r in rows if r["report_summary_valid"] == r["stored_valid"])
    payload = {
        "population": len(rows),
        "agree_with_stored_under_verify_root_violations": agree_violations,
        "agree_with_stored_under_report_summary_valid": agree_summary,
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        f"\nagrees with stored under verify_root(violations non-empty): "
        f"{agree_violations}/{len(rows)}"
    )
    print(
        f"agrees with stored under verify_root_report(...).summary_payload()['valid']: "
        f"{agree_summary}/{len(rows)}"
    )
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
