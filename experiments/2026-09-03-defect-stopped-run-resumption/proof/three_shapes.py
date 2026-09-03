"""Drive the deterministic stub to each of the three terminal shapes, offline.

    python experiments/2026-09-03-defect-stopped-run-resumption/proof/three_shapes.py \
        --workdir /tmp/three-shapes [--shape clean|killed|failed]

No provider, no credential, no network: every model call is the committed
`cycle_soak.py` stub.  Each shape prints the two facts the tranche turns on —
whether the record VERIFIES (`record_verification_refusal`, the gate the
2026-08-29 security clause installed) and whether `continue` is ACCEPTED —
plus the outstanding-work census that separates the refusal's two disjuncts.

RED (before the fix): all three verify intact and all three refuse.
GREEN (after):        all three verify intact and all three resume.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOAK = REPO / "scripts" / "cycle_soak.py"
# The stub's own credential name: the soak sets it for its in-process run, so a
# later CLI verb against the same root must supply it too or the launch refuses
# RUN_CREDENTIAL_MISSING before any lifecycle predicate is reached.
STUB_ENV = {"DEEPREASON_LOOPBACK_SMOKE_KEY": "stub"}


def _env() -> dict[str, str]:
    return {**os.environ, **STUB_ENV}


def _cli(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "deepreason.cli.main", "--root", str(root), *args],
        capture_output=True, text=True, env=_env(), cwd=REPO, timeout=1800,
    )


def _census(root: Path) -> dict:
    from deepreason.harness import Harness
    from deepreason.runtime.continuation import record_verification_refusal

    state = Harness(root, read_only=True).workflow_state
    consumed = {r.source_call_seq for r in state.proposal_receipts.values()}
    status = json.loads((root / "run-status.json").read_text())
    return {
        "state": status.get("state"),
        "stop_reason": status.get("stop_reason"),
        "terminal_lifecycle_refusal": status.get("terminal_lifecycle_refusal"),
        "cycle": status.get("cycle"),
        "outstanding_work": len(state.outstanding_work_order_ids),
        "unconsumed_provider_calls": len(set(state.calls_by_seq) - consumed),
        "terminal_lifecycle_decision": state.terminal_lifecycle_decision is not None,
        "record_verification_refusal": record_verification_refusal(root),
    }


def _soak(out: Path, cycles: int, *, background: bool):
    cmd = [sys.executable, "-u", str(SOAK), "--case", "epoch3",
           "--cycles", str(cycles), "--keep", "--out", str(out)]
    if background:
        return subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=_env(), cwd=REPO, start_new_session=True,
        )
    return subprocess.run(cmd, capture_output=True, text=True, env=_env(),
                          cwd=REPO, timeout=1800)


def shape_clean(workdir: Path) -> Path:
    """Shape 3: an ordinary clean run that stops with work outstanding."""

    out = workdir / "clean"
    _soak(out, cycles=8, background=False)
    return out / "run"


def shape_killed(workdir: Path) -> Path:
    """Shape 2: SIGKILL with work in flight, then `deepreason finalize`."""

    out = workdir / "killed"
    process = _soak(out, cycles=8, background=True)
    progress = out / "run" / "progress.jsonl"
    deadline = time.time() + 900
    while time.time() < deadline:
        if progress.exists():
            lines = progress.read_text(encoding="utf-8").splitlines()
            reached = max(
                (json.loads(line).get("cycle") or 0)
                for line in lines
            ) if lines else 0
            if reached >= 2:
                break
        if process.poll() is not None:
            break
        time.sleep(2)
    # SIGKILL the whole process group: the run must die with no chance to
    # write a stop, which is precisely what a container reclaim does.
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=60)
    root = out / "run"
    print("    [killed] state before finalize:",
          json.loads((root / "run-status.json").read_text()).get("state"))
    done = _cli(root, "finalize")
    print(f"    [killed] finalize rc={done.returncode} "
          f"{done.stderr.strip().splitlines()[-1] if done.stderr.strip() else ''}")
    return root


def shape_failed(workdir: Path) -> Path:
    """Shape 1: a mid-cycle operational failure terminal.

    Driven through the same managed launch as the other two, with the stub's
    scheduler raising once the run is past its first cycle.  The raise is the
    ONLY injected element: everything downstream of it — the run-stop record,
    the checkpoint, and the refusal `text_runs.py` writes instead of a receipt
    — is the production failure path, unmodified.
    """

    out = workdir / "failed"
    script = out / "drive.py"
    out.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(REPO / 'scripts')!r})\n"
        f"sys.path.insert(0, {str(REPO)!r})\n"
        "import deepreason.ops as ops\n"
        "import cycle_soak\n"
        "_real = ops.run_scheduler\n"
        "def _fail(harness, config, cycles, token_budget, **kwargs):\n"
        "    _real(harness, config, 1, token_budget, **kwargs)\n"
        "    raise RuntimeError(\n"
        "        'V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at '\n"
        "        '/workflow/insufficient_capability_by_route_seat: route seat '\n"
        "        'has terminally exhausted its smallest authorized contract')\n"
        "ops.run_scheduler = _fail\n"
        "import deepreason.application.text_runs as tr\n"
        "tr.run_scheduler = _fail\n"
        f"sys.exit(cycle_soak.main(['--case', 'epoch3', '--cycles', '4', "
        f"'--keep', '--out', {str(out)!r}]))\n",
        encoding="utf-8",
    )
    subprocess.run([sys.executable, "-u", str(script)], capture_output=True,
                   text=True, env=_env(), cwd=REPO, timeout=1800)
    return out / "run"


SHAPES = {"clean": shape_clean, "killed": shape_killed, "failed": shape_failed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--shape", choices=sorted(SHAPES), action="append")
    parser.add_argument("--cycles", type=int, default=2,
                        help="cycles requested of `continue` on each root")
    args = parser.parse_args(argv)

    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    verdicts = {}
    for name in (args.shape or sorted(SHAPES)):
        print(f"\n=== shape: {name} ===")
        root = SHAPES[name](workdir)
        if not (root / "run-status.json").exists():
            print(f"    NO ROOT at {root}")
            verdicts[name] = {"error": "no root"}
            continue
        census = _census(root)
        for key, value in census.items():
            print(f"    {key}: {value}")
        result = _cli(root, "continue", "--budget", f"cycles={args.cycles}")
        last = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ""
        print(f"    continue rc={result.returncode} {last}")
        after = json.loads((root / "run-status.json").read_text())
        print(f"    cycle after continue: {after.get('cycle')} "
              f"(was {census['cycle']})")
        verdicts[name] = {
            **census,
            "continue_rc": result.returncode,
            "continue_stderr": last,
            "cycle_before": census["cycle"],
            "cycle_after": after.get("cycle"),
            "root": str(root),
        }
    (workdir / "verdicts.json").write_text(
        json.dumps(verdicts, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"\nverdicts -> {workdir / 'verdicts.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
