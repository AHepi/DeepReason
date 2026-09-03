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
    """R7, as the operator finally settled it: a failure terminal IS continuable.

    This test asserted the opposite until 2026-09-03, and its own name still
    carries the question it was asking. What it used to pin --
    `terminal_lifecycle_refusal: TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL`
    and "the record's claim is TRUE: this terminal really cannot be continued"
    -- was the half-measure available before the operator ruled: the 2026-08-30
    tranche could make the un-continuable terminal HONEST but not continuable,
    and said so.

    The operator's law of 2026-08-29 (CLAUDE.md) answers it: "clean stop. with
    an assurance that continuing is possible. Too often an operational failure
    overlooks securing enough checkpoints to allow relaunches." So a failure
    terminal now takes the SAME typed STOPPED receipt a clean stop takes,
    carrying `operational_failure` as its reason, and has nothing left to
    refuse. Whether THIS root may actually be resumed is decided where the same
    law puts it -- the SECURITY-channel integrity gate at continue/amend time,
    which `tests/test_jailbreak_gate.py` owns.

    Superseded claim recorded at `docs/ERRATA.md` E-stopped-run-resumption;
    the 16 committed roots that stand in the old shape are frozen evidence of
    it and are not rewritten (old runs owe the future nothing, 2026-08-14).
    """

    root = _failed_root(tmp_path, monkeypatch, name="ordinary-failure-terminal")

    result = json.loads((root / "run-result.json").read_text())
    assert result["state"] == "failed"
    assert result["stop"]["reason"] == "operational_failure"
    # Nothing to refuse: the receipt was taken.  The v2 terminal envelope
    # serializes with exclude_none, so "no refusal" is an ABSENT key here and a
    # null in the progress record -- the same shape a clean stop publishes.
    assert result.get("terminal_lifecycle_refusal") is None

    status = json.loads((root / "run-status.json").read_text())
    assert status["stop_reason"] == "operational_failure"
    assert status["terminal_lifecycle_refusal"] is None

    # The receipt is REAL and carries the failure's own reason -- not a clean
    # reason borrowed to buy continuability.
    from deepreason.harness import Harness

    decision = Harness(root, read_only=True).workflow_state.terminal_lifecycle_decision
    assert decision is not None
    assert decision.deterministic_decision.reason == "operational_failure"

    # And the whole point: this terminal really can be continued now.
    with tempfile.TemporaryDirectory() as scratch:
        copy = _copy(root, scratch)
        prepared = prepare_continuation(
            copy, cycles=1, tokens=10, check_operator_lock=False
        )
    assert prepared["schema"] == "deepreason-continuation-v1"


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


def _run_root_prefixes(tracked: str) -> tuple[str, ...]:
    """Every committed run root, as GIT knows them -- not as the disk does.

    The index is the only source that survives the mutation this control
    exists to catch: a root whose `log.jsonl` is deleted still has one here,
    and a predicate that asks the filesystem instead loses the very file it
    needs to recognise the deletion.
    """

    return tuple(
        name[: -len("log.jsonl")]
        for name in tracked.split("\0")
        if name.endswith("/log.jsonl")
    )


def _moved_run_root_paths(status: str, tracked: str) -> list[str]:
    """The status entries that touch a committed run root, in any way.

    NUL-delimited on purpose: git quotes unusual paths in the newline form,
    and a rename entry carries its ORIGIN in the following field -- which is
    the half that names the root a rename moved a file OUT of.
    """

    roots = _run_root_prefixes(tracked)
    fields = [field for field in status.split("\0") if field]
    moved: list[str] = []
    index = 0
    while index < len(fields):
        entry = fields[index]
        index += 1
        code, path = entry[:2], entry[3:]
        paths = [path]
        if "R" in code or "C" in code:
            # `XY new\0orig` -- both sides matter, and the origin is the one a
            # rename out of a root would hide.
            if index < len(fields):
                paths.append(fields[index])
                index += 1
        for candidate in paths:
            if candidate.startswith(roots):
                moved.append(entry)
                break
    return moved


def test_committed_roots_are_byte_unchanged_by_this_module():
    """The evidence this module reads is evidence: it may never move.

    Scoped to RUN ROOTS -- anything under a directory git's index says holds a
    `log.jsonl` -- rather than to all of `experiments/`, because a tranche
    editing its own narrative documents is not a root mutation and a check
    that cannot tell the two apart goes red for the wrong reason.  Every path
    under a root counts, `blobs/` and `objects/` included: those ARE the
    record.

    Predicate arms (modify, delete a log, delete a whole root, modify content-
    addressed evidence, rename out of a root) are mutation-proven against real
    git output in
    `experiments/2026-08-30-change-checkpoint-hardening/proof/control_predicate_arms.py`;
    the earlier filesystem-keyed predicate passed on four of the five.
    """

    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    tracked = _git("ls-files", "-z", "experiments", "runs")
    # Non-vacuity: `str.startswith(())` is False for every path, so an empty
    # root set would make this control pass on any mutation whatsoever.
    roots = _run_root_prefixes(tracked)
    assert len(roots) >= 50, f"the committed run-root set collapsed: {len(roots)}"

    moved = _moved_run_root_paths(
        _git("status", "--porcelain", "--untracked-files=no", "-z",
             "experiments", "runs"),
        tracked,
    )
    assert moved == [], f"a committed root moved: {moved}"
