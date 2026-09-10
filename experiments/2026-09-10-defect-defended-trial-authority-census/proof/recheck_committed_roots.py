"""Re-verify every committed root that carries a defended-trial step.

Reads only. Each root is reported with its STORED verdict
(`REPLAY_VALIDATION.json`, written by the run about itself) beside the verdict
recomputed now, so a moved verdict is visible rather than inferred. No root is
edited: `Harness(..., read_only=True)` and `verify_root` open the bytes as they
stand in git.

The five roots are every git-tracked root whose `objects/` carry a
`defended_trial_step` preparation:

    git grep -l defended_trial_step -- '*/objects/*' | sed 's#/objects/.*##' | sort -u

Ordered smallest log first, so the cheap rows land before the 13k-line one.
"""
import collections
import json
import sys
from pathlib import Path

ROOTS = [
    "experiments/2026-09-02-live-p-a2-corrected/failed-epoch3-run-1b89ed64e050c354",
    "experiments/2026-09-01-live-all-modules-p-a1/run",
    "experiments/2026-09-09-fix-solo-criticism-authority/runs/home-solo/runs/run-02818acc38961781e2e820d0d6b591fb",
    "experiments/2026-09-02-live-p-a2-corrected/run",
    "experiments/2026-08-12-live-grounded-extension-expansion/run",
]


def row(path: str) -> dict:
    from deepreason.harness import Harness
    from deepreason.invariants import verify_root
    from deepreason.verification.report import verify_root_report

    root = Path(path)
    stored = None
    stored_file = root / "REPLAY_VALIDATION.json"
    if stored_file.exists():
        payload = json.loads(stored_file.read_text())
        violations = payload.get("violations")
        stored = {
            "valid": payload.get("valid"),
            "violations": len(violations) if isinstance(violations, list) else violations,
        }
    kinds = collections.Counter()
    for item in Harness(root, read_only=True).workflow_state.transaction_work.values():
        kinds[item.preparation.task_kind.value] += 1
    replay = verify_root(root)
    rendered = verify_root_report(root)
    unknown = collections.Counter()
    for finding in rendered.security:
        if "unknown v6 task kind " in finding.detail:
            unknown[finding.detail.split("unknown v6 task kind ")[1]] += 1
    return {
        "root": path,
        "stored_replay_validation": stored,
        "recomputed_verify_root_violations": len(replay["violations"]),
        "valid": rendered.valid,
        "integrity": len(rendered.integrity),
        "security": len(rendered.security),
        "completion": len(rendered.completion),
        "operational": len(rendered.operational),
        "security_checks": dict(collections.Counter(f.check for f in rendered.security)),
        "unknown_task_kinds": dict(unknown),
        "defended_trial_steps": kinds.get("defended_trial_step", 0),
        "task_kinds": dict(kinds),
    }


if __name__ == "__main__":
    wanted = sys.argv[1:] or ROOTS
    for path in wanted:
        print(json.dumps(row(path), sort_keys=True), flush=True)
