"""Small terminal renderer for the stable progress protocol."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import TextIO

from deepreason.ui.status import read_run_status

_PULSES = ("·", "•", "●", "•")
_TERMINAL = {"completed", "failed", "cancelled", "paused"}


def render_terminal_status(status: dict, *, pulse: int = 0) -> str:
    state = str(status.get("state", "not-started"))
    marker = _PULSES[pulse % len(_PULSES)] if state in {"starting", "running"} else "■"
    workload = status.get("workload", "-")
    phase = status.get("phase", "-")
    activity = status.get("activity", "-")
    cycle = status.get("cycle", 0)
    focus = status.get("problem_id") or status.get("artifact_id") or "-"
    token_limit = status.get("token_limit")
    tokens = f"{status.get('token_spend', 0)}/{token_limit if token_limit else 'unlimited'}"
    labels = (
        f"A:{status.get('accepted', 0)} R:{status.get('refuted', 0)} "
        f"S:{status.get('suspended', 0)}"
    )
    queues = (
        f"checks:{status.get('queued_checks', 0)} "
        f"criticism:{status.get('queued_criticism', 0)}"
    )
    stop = status.get("stop_reason") or (status.get("stop") or {}).get("reason") or "-"
    return (
        f"{marker} {state}  {workload} · {phase} · {activity}\n"
        f"cycle {cycle}  focus {focus}\n"
        f"frontier {status.get('frontier_size', 0)}  {labels}  {queues}\n"
        f"tokens {tokens}  stop {stop}"
    )


def watch_run(
    root: Path | str,
    *,
    interval: float = 0.25,
    once: bool = False,
    output: TextIO | None = None,
) -> dict:
    if interval <= 0:
        raise ValueError("watch interval must be positive")
    output = output or sys.stdout
    pulse = 0
    while True:
        status = read_run_status(root)
        rendered = render_terminal_status(status, pulse=pulse)
        if once or not getattr(output, "isatty", lambda: False)():
            print(rendered, file=output, flush=True)
        else:
            print("\x1b[2J\x1b[H" + rendered, end="", file=output, flush=True)
        if once or status.get("state") in _TERMINAL:
            return status
        pulse += 1
        time.sleep(interval)
