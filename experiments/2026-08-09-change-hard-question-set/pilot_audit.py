"""Pilot audit (R16/R10/PREREG.md): typed-record-only reader for the two
live pilot runs. Reads run-status.json, verify_root, and
`deepreason findings --json`'s `positions.accepted` claims -- never model
prose framing, only the typed fields the harness itself commits.

Usage:
    python pilot_audit.py <root> [--checker PATH]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from deepreason.invariants import verify_root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--checker", default=None,
                     help="Tier V checker script; tried against every accepted claim")
    args = ap.parse_args()
    root = Path(args.root)
    out = {}

    status = json.loads((root / "run-status.json").read_text())
    out["state"] = status.get("state")
    out["stop_reason"] = status.get("stop_reason")

    verdict = verify_root(root)
    out["verify_violations"] = [v["check"] for v in verdict["violations"]]
    out["replay_valid"] = not verdict["violations"]

    findings_proc = subprocess.run(
        ["deepreason", "--root", str(root), "findings", "--json"],
        capture_output=True, text=True)
    out["findings_rc"] = findings_proc.returncode
    findings = {}
    if findings_proc.returncode == 0:
        try:
            findings = json.loads(findings_proc.stdout)
        except json.JSONDecodeError:
            findings = {"_parse_error": findings_proc.stdout[:500]}
    else:
        findings = {"_stderr": findings_proc.stderr[:500]}

    accepted = (findings.get("positions") or {}).get("accepted", [])
    out["accepted_count"] = len(accepted)
    out["accepted_claims_preview"] = [
        {"id": row.get("id"), "claim": str(row.get("claim", ""))[:300]}
        for row in accepted
    ]

    if args.checker:
        checker_results = []
        for row in accepted:
            candidate = str(row.get("claim", ""))
            r = subprocess.run(["python", args.checker, candidate],
                                capture_output=True, text=True)
            checker_results.append({
                "artifact_id": row.get("id"),
                "candidate_preview": candidate[:200],
                "rc": r.returncode,
                "stdout": r.stdout.strip(),
            })
        out["checker_results"] = checker_results
        out["checker_any_pass"] = any(c["rc"] == 0 for c in checker_results)

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
