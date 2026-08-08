"""Block D audit: per-pair eventual-valid and scope-violation rates
for one qualification battery sample, from the typed record only.

The detailed per-pair doctor report is written under
$DEEPREASON_HOME/qualification-cache/ in one of two shapes depending
on outcome (2026-08-09 research pass, this tranche):
  - FAILURE/degraded path: "<digest>.unqualified-doctor.json" --
    ProductionContractDoctorReportV1 with ready-made pair aggregates
    (pairs[i].eventual_valid_count, pairs[i].scope_violations).
  - SUCCESS path: "<digest>.json" -- a stripped
    ReusableQualificationBundleV1 with pairs[i].cases[*] only; the
    per-pair aggregates must be summed from case-level
    eventual_valid/scope_violations fields ourselves.
This script tries the failure-path file first (it has the richer,
ready-made aggregates) and falls back to reconstructing from the
success-path bundle.

Usage: python3 block_d_audit.py DEEPREASON_HOME QUALIFY_JSON_PATH CAP SAMPLE_IDX
"""

import json
import sys
from pathlib import Path

home = Path(sys.argv[1])
qualify_json_path = Path(sys.argv[2])
cap = sys.argv[3]
sample_idx = sys.argv[4]
out = {"home": str(home), "cap": cap, "sample_idx": sample_idx}

try:
    top = json.loads(qualify_json_path.read_text())
except Exception as exc:  # noqa: BLE001
    out["qualify_json_read_error"] = str(exc)
    top = {}

out["qualification_state"] = top.get("qualification_state")
out["tier"] = top.get("tier")
out["qualification_subject_digest"] = top.get("qualification_subject_digest")
out["cache_reused"] = top.get("cache_reused")

digest = top.get("qualification_subject_digest")
cache_dir = home / "qualification-cache"
pairs_out = []

if digest:
    failure_path = cache_dir / f"{digest}.unqualified-doctor.json"
    success_path = cache_dir / f"{digest}.json"
    if failure_path.exists():
        out["doctor_report_path"] = str(failure_path)
        out["doctor_report_source"] = "failure_path_ready_made_aggregates"
        report = json.loads(failure_path.read_text())
        for p in report["pairs"]:
            pair = p["pair"]
            pairs_out.append({
                "pair_id": pair.get("pair_id") or f"{pair.get('role')}/{pair.get('contract_id')}/{pair.get('model_id')}",
                "role": pair.get("role"),
                "contract_id": pair.get("contract_id"),
                "model_id": pair.get("model_id"),
                "eventual_valid_count": p["eventual_valid_count"],
                "scope_violations": p["scope_violations"],
            })
        out["summary_eventual_valid_count"] = report["summary"]["eventual_valid_count"]
        out["summary_scope_violations"] = report["summary"]["scope_violations"]
        out["summary_qualified"] = report["summary"]["qualified"]
    elif success_path.exists():
        out["doctor_report_path"] = str(success_path)
        out["doctor_report_source"] = "success_path_reconstructed_from_cases"
        bundle = json.loads(success_path.read_text())
        total_eventual_valid = 0
        total_scope_violations = 0
        for p in bundle.get("pairs", []):
            cases = p.get("cases", [])
            eventual_valid_count = sum(1 for c in cases if c.get("eventual_valid"))
            scope_violations = sum(c.get("scope_violations", 0) for c in cases)
            total_eventual_valid += eventual_valid_count
            total_scope_violations += scope_violations
            pairs_out.append({
                "pair_id": p.get("pair_subject_digest"),
                "role": p.get("role"),
                "contract_id": p.get("contract_id"),
                "model_id": p.get("model_id"),
                "eventual_valid_count": eventual_valid_count,
                "scope_violations": scope_violations,
                "case_count": len(cases),
            })
        out["summary_eventual_valid_count"] = total_eventual_valid
        out["summary_scope_violations"] = total_scope_violations
        out["summary_qualified"] = total_scope_violations == 0
    else:
        out["doctor_report_path"] = None
        out["doctor_report_source"] = "not_found"

out["pairs"] = pairs_out
out["pairs_with_scope_violations"] = [p["pair_id"] for p in pairs_out if p["scope_violations"] > 0]

print(json.dumps(out, indent=2, sort_keys=True))
