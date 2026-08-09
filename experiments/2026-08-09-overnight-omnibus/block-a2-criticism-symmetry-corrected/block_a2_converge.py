"""Block A-2's convergence driver: run `deepreason reason`, then
`deepreason --root <root> continue --budget cycles=2` up to twice,
until replay_valid=true or a non-resumable stop_reason, per
PREREG-A2.yaml's convergence_protocol. Reads DEEPREASON_HOME from the
environment (same convention as the CLI itself).

Usage: python3 block_a2_converge.py QUESTION OUT_PREFIX
Prints a JSON summary to stdout; per-call raw output goes to
OUT_PREFIX-reason.json/.err and OUT_PREFIX-continueN.json/.err.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from deepreason.invariants import verify_root
from deepreason.workflow.lifecycle import RESUMABLE_STOP_REASONS

MAX_CONTINUES = 2


def run_cmd(args, out_path, err_path):
    with open(out_path, "w") as out, open(err_path, "w") as err:
        proc = subprocess.run(args, stdout=out, stderr=err)
    return proc.returncode


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:  # noqa: BLE001
        return {}


def status_of(root: Path) -> dict:
    return read_json(root / "run-status.json")


def replay_valid(root: Path) -> bool:
    verdict = verify_root(root)
    return not verdict["violations"]


def main() -> None:
    question = sys.argv[1]
    out_prefix = sys.argv[2]
    home = Path(os.environ["DEEPREASON_HOME"])

    rc = run_cmd(
        ["deepreason", "reason", question, "--cycles", "10", "--token-budget", "195000", "--allow-partial"],
        f"{out_prefix}-reason.json",
        f"{out_prefix}-reason.err",
    )
    reason_out = read_json(f"{out_prefix}-reason.json")
    run_id = reason_out.get("run_id")
    summary = {"reason_rc": rc, "run_id": run_id, "continuation_count": 0}

    if not run_id:
        summary["outcome"] = "no_run_id"
        print(json.dumps(summary, indent=2))
        return

    root = home / "runs" / run_id
    summary["root"] = str(root)

    continuations = 0
    while True:
        status = status_of(root)
        stop_reason = status.get("stop_reason")
        valid = replay_valid(root)
        summary["last_stop_reason"] = stop_reason
        summary["last_replay_valid"] = valid
        if valid:
            summary["outcome"] = "replay_valid"
            break
        if stop_reason not in RESUMABLE_STOP_REASONS:
            summary["outcome"] = "non_resumable_not_valid"
            break
        if continuations >= MAX_CONTINUES:
            summary["outcome"] = "max_continues_exhausted_not_valid"
            break
        continuations += 1
        crc = run_cmd(
            ["deepreason", "--root", str(root), "continue", "--budget", "cycles=2"],
            f"{out_prefix}-continue{continuations}.json",
            f"{out_prefix}-continue{continuations}.err",
        )
        summary[f"continue{continuations}_rc"] = crc

    summary["continuation_count"] = continuations
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
