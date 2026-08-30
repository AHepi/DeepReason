"""A stop that cannot be continued RECORDS that fact, typed.

Operator law, 2026-08-29 (CLAUDE.md, "Exhaustion is a clean stop, every stop
secures continuation, and continuation is integrity-gated"): "Too often an
operational failure ... forgets to ensure continuing is possible that trigger
corrupted stops."

Regression (16 of 59 committed roots, measured 2026-08-30 and censused in
`experiments/2026-08-30-change-checkpoint-hardening/proof/census.json`): a
failure terminal writes every checkpoint FILE, takes no STOPPED lifecycle
receipt, and said NOTHING about either fact -- so `deepreason results`
reported `lifecycle_refusal: ABSENT:NO_LIFECYCLE_REFUSAL_RECORD` on a root
`continue` refuses.  The no-harness terminal was worse: `run-result.json` and
nothing else, no stop record and no checkpoint at all.

NOT here, and deliberately: the integrity gate the same law asks for.  It was
built and measured in this tranche and PARKED -- see that tranche's PARKED.md
F9 and proof/gate_collisions.md.

Committed roots are evidence: every root read here is COPIED before it is
touched.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from deepreason.runtime.continuation import prepare_continuation

from tests.test_lifecycle_operation_parity import (
    _bind_v6_root,
    _launch_through_cli,
)

def _copy(root: Path, scratch: str) -> Path:
    copy = Path(scratch) / root.name
    shutil.copytree(root, copy, symlinks=True)
    return copy


def _failed_root(tmp_path, monkeypatch, *, name):
    """Drive the real run path to its ORDINARY worker-failure terminal.

    The failure is injected at `terminalize_text_run` because what is under
    test is the except branch's own record, and no offline fixture reaches that
    branch by running out of anything.
    """

    root, manifest, _spec, problem_file = _bind_v6_root(tmp_path, name=name)

    def _explode(*_args, **_kwargs):
        raise RuntimeError("SIMULATED worker failure after the last event")

    monkeypatch.setattr(
        "deepreason.application.text_runs.terminalize_text_run", _explode
    )
    assert _launch_through_cli(root, manifest, problem_file, monkeypatch) != 0
    return root


def test_a_failure_terminal_records_why_it_cannot_be_continued(tmp_path, monkeypatch):
    """R7: a stop that cannot assure continuability is a defect unless it SAYS so.

    This terminal writes every checkpoint FILE -- run-stop.json, checkpoint.json,
    run-result.json, a progress line -- and takes no STOPPED lifecycle receipt,
    so `continue` refuses CONTINUE_TYPED_STOP_REQUIRED.  Before this tranche the
    record said nothing about that; 16 committed roots stand in exactly that
    state.
    """

    root = _failed_root(tmp_path, monkeypatch, name="ordinary-failure-terminal")

    result = json.loads((root / "run-result.json").read_text())
    assert result["state"] == "failed"
    refusal = result["terminal_lifecycle_refusal"]
    assert refusal["schema"] == "deepreason-terminal-lifecycle-refusal-v1"
    assert refusal["code"] == "TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL"
    assert refusal["stop_reason"] == "operational_failure"
    assert refusal["continue_refusal"] == "CONTINUE_TYPED_STOP_REQUIRED"

    status = json.loads((root / "run-status.json").read_text())
    assert status["stop_reason"] == "operational_failure"
    assert (
        status["terminal_lifecycle_refusal"]
        == "TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL"
    )

    # The record's claim is TRUE: this terminal really cannot be continued.
    with tempfile.TemporaryDirectory() as scratch:
        copy = _copy(root, scratch)
        with pytest.raises(ValueError) as raised:
            prepare_continuation(copy, cycles=1, tokens=10, check_operator_lock=False)
    assert str(raised.value) == refusal["continue_refusal"]


def test_a_terminal_that_wrote_no_checkpoint_records_that_fact(tmp_path, monkeypatch):
    """The corrupted stop in its purest form: no stop record, no checkpoint.

    When the worker cannot open its own harness there is nothing to write a
    stop record with, so the root gets `run-result.json` and nothing else.
    Before this tranche it did not say so either.
    """

    root, manifest, _spec, problem_file = _bind_v6_root(
        tmp_path, name="no-checkpoint-terminal"
    )

    # DECLARED LIMIT: the failure is injected at the worker's WRITABLE harness
    # open, because that is the only door into this branch -- `start_manifest_run`
    # opens the same root READ-ONLY first, so a genuinely unreadable log kills
    # the launch instead and never reaches the worker at all.  What is under
    # test is the branch's own record, and the branch is entered exactly as a
    # real open failure (a full disk, a revoked mode bit) would enter it.
    from deepreason.harness import Harness

    real_init = Harness.__init__
    armed = [True]

    def _cannot_open(self, root_arg, *args, read_only=None, **kwargs):
        # Once only: the worker's own writable open is the FIRST one after
        # arming, and the CLI opens the same root again afterwards to read the
        # terminal this branch just wrote.
        if armed[0] and read_only is not True and Path(root_arg) == root:
            armed[0] = False
            raise RuntimeError("SIMULATED: the run root could not be opened")
        return real_init(self, root_arg, *args, read_only=read_only, **kwargs)

    monkeypatch.setattr(Harness, "__init__", _cannot_open)
    # A failed run must not report success; the exit code is the operator's
    # first signal and this branch is the one that has nothing else to give.
    assert _launch_through_cli(root, manifest, problem_file, monkeypatch) != 0

    assert not (root / "run-stop.json").exists()
    assert not (root / "checkpoint.json").exists()

    result = json.loads((root / "run-result.json").read_text())
    assert result["state"] == "failed"
    refusal = result["terminal_lifecycle_refusal"]
    assert refusal["schema"] == "deepreason-terminal-lifecycle-refusal-v1"
    assert refusal["code"] == "TERMINAL_NO_CHECKPOINT_WRITTEN"
    assert refusal["error_type"] == result["error_type"]

    status = json.loads((root / "run-status.json").read_text())
    assert status["terminal_lifecycle_refusal"] == "TERMINAL_NO_CHECKPOINT_WRITTEN"


def test_committed_roots_are_byte_unchanged_by_this_module():
    """The evidence this module reads is evidence: it may never move.

    Scoped to RUN ROOTS -- a tracked file whose own directory carries a
    `log.jsonl` -- rather than to all of `experiments/`, because a tranche
    editing its own narrative documents is not a root mutation and a check
    that cannot tell the two apart goes red for the wrong reason.
    """

    changed = subprocess.run(
        [
            "git", "status", "--porcelain", "--untracked-files=no",
            "experiments", "runs",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split("\n")
    moved = [
        line
        for line in changed
        if line.strip() and (Path(line[3:].strip()).parent / "log.jsonl").exists()
    ]
    assert moved == [], f"a committed root moved: {moved}"
