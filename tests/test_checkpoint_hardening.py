"""Continuation is integrity-gated, and a stop that cannot be continued says so.

Operator law, 2026-08-29 (CLAUDE.md, "Exhaustion is a clean stop, every stop
secures continuation, and continuation is integrity-gated"): "checkpoints need
to be hardned. I don't want a jailbroken run to be continuable."

Regression (committed root
`experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d`,
and the 16 committed roots whose own REPLAY_VALIDATION.json says
`valid: false` while `derive_terminal_authority` calls them
`current_valid_committed`): before this tranche neither `continue` nor `amend`
consulted the replay verdict at any point.  One flipped byte in `log.jsonl`
rewriting the recorded provider endpoint made `verify_root` report
`frozen-route` and `attempt-route` -- both SECURITY-channel findings -- while
`amend` still PASSED and `continue` still refused only for the unrelated
`CONTINUE_TYPED_STOP_REQUIRED`.  The tampered root and the intact root were
indistinguishable to both verbs.

Committed roots are evidence: every root here is COPIED before it is touched,
because `prepare_continuation` opens a writable Harness and writes
`run-stops/` before it can refuse.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from deepreason.amendment.apply import _require_terminal_stop
from deepreason.amendment.state import AmendmentError
from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
from deepreason.runtime.continuation import prepare_continuation

from tests.test_lifecycle_operation_parity import (
    _bind_v6_root,
    _launch_through_cli,
)

# The differential root: 64 events, stored verdict `valid: true`, `verify_root`
# ~3s.  Small enough to re-derive twice inside a gate run, real enough that its
# refusal is not asserted into existence.
DIFFERENTIAL_ROOT = Path(
    "experiments/2026-08-13-defect-controller-steering-inert"
    "/failed-epoch1-run-8e22d0431fd2b98d"
)

# The recorded provider endpoint of this root's first LLM call.  Flipping one
# byte of the host is the smallest edit that forges WHERE a call went.
_ENDPOINT_FIELD = b'"endpoint":"https://ollama.com/v1"'
_HOST_BYTE_OFFSET = len(b'"endpoint":"https://oll')


def _forge_one_endpoint_byte(log: Path) -> tuple[int, str, str]:
    """Flip exactly one byte of the first recorded endpoint. Returns the edit."""

    raw = bytearray(log.read_bytes())
    offset = bytes(raw).index(_ENDPOINT_FIELD) + _HOST_BYTE_OFFSET
    before = chr(raw[offset])
    after = "7" if before != "7" else "6"
    raw[offset] = ord(after)
    log.write_bytes(bytes(raw))
    return offset, before, after


def _copy(root: Path, scratch: str) -> Path:
    copy = Path(scratch) / root.name
    shutil.copytree(root, copy, symlinks=True)
    return copy


def test_one_flipped_log_byte_turns_a_continue_into_a_typed_integrity_refusal():
    """One byte, one root, two typed codes -- and the byte is the only difference.

    A fixture that synthesised a "broken" record would prove nothing about the
    committed population; this drives the SAME committed root twice and lets
    the single edited byte carry the whole difference.
    """

    assert DIFFERENTIAL_ROOT.exists(), "the differential root left the record"

    with tempfile.TemporaryDirectory() as scratch:
        intact = _copy(DIFFERENTIAL_ROOT, scratch)
        with pytest.raises(ValueError) as passed_the_gate:
            prepare_continuation(intact, cycles=1, tokens=10, check_operator_lock=False)
        # The intact record REACHES its pre-existing later refusal, which is
        # what proves the new gate is not refusing everything it is shown.
        assert str(passed_the_gate.value) == "CONTINUE_TYPED_STOP_REQUIRED"

    with tempfile.TemporaryDirectory() as scratch:
        forged = _copy(DIFFERENTIAL_ROOT, scratch)
        offset, before, after = _forge_one_endpoint_byte(forged / "log.jsonl")
        assert before != after
        assert (
            len((forged / "log.jsonl").read_bytes())
            == len((DIFFERENTIAL_ROOT / "log.jsonl").read_bytes())
        ), "the forge must change one byte, not the file's length"
        with pytest.raises(ValueError) as refused:
            prepare_continuation(forged, cycles=1, tokens=10, check_operator_lock=False)
        message = str(refused.value)
        assert message.startswith("CONTINUE_RECORD_NOT_VERIFIED: "), (
            f"byte {offset} {before!r}->{after!r} bought a continuation: {message}"
        )
        # The refusal names what failed, so an operator is not left guessing.
        assert "frozen-route" in message and "attempt-route" in message


def test_one_flipped_log_byte_turns_an_amend_into_a_typed_integrity_refusal():
    """The same byte, the same root, the other verb.

    `derive_terminal_authority` calls the forged root `current_valid_committed`
    -- the forgery is invisible to amend's only pre-existing precondition -- so
    this refusal can come from nowhere but the new integrity gate.
    """

    manifest = load_run_manifest(DIFFERENTIAL_ROOT / MANIFEST_NAME)

    with tempfile.TemporaryDirectory() as scratch:
        intact = _copy(DIFFERENTIAL_ROOT, scratch)
        _require_terminal_stop(intact, manifest)  # passes; raising would fail

    with tempfile.TemporaryDirectory() as scratch:
        forged = _copy(DIFFERENTIAL_ROOT, scratch)
        _forge_one_endpoint_byte(forged / "log.jsonl")
        from deepreason.runtime.terminal_authority import derive_terminal_authority

        authority = derive_terminal_authority(forged, manifest=manifest)
        assert authority.current_valid is True, (
            "this test is only meaningful while the forgery is invisible to "
            "amend's pre-existing authority check"
        )
        with pytest.raises(AmendmentError) as refused:
            _require_terminal_stop(forged, manifest)
    assert refused.value.code == "AMEND_RECORD_NOT_VERIFIED"
    assert "frozen-route" in str(refused.value)


def _replay_invalid_committed_roots() -> list[tuple[Path, int]]:
    """Committed roots whose OWN published verdict says the record is invalid.

    Selected by the PROPERTY that causes the refusal, not from a list of names:
    a root that is repaired, retired or reclassified leaves the set by itself,
    and a set that empties trips the guard below instead of leaving an
    assertion passing over nothing.
    """

    tracked = subprocess.run(
        ["git", "ls-files", "experiments", "runs"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    roots = sorted(
        {Path(p).parent for p in tracked if p.endswith("/REPLAY_VALIDATION.json")}
    )
    witnesses = []
    for root in roots:
        verdict = json.loads((root / "REPLAY_VALIDATION.json").read_text())
        if verdict.get("valid"):
            continue
        log = root / "log.jsonl"
        events = sum(1 for _ in log.open(encoding="utf-8")) if log.exists() else 0
        witnesses.append((root, events))
    return sorted(witnesses, key=lambda item: item[1])


# A RUNTIME BUDGET, not the property: `verify_root` is O(run length) (measured
# 0.69s at 27 events to 32.4s at 594), and the smallest witnesses answer the
# same question as the largest.  The guard above runs over the FULL population.
_MAX_DRIVEN_EVENTS = 300


def test_every_replay_invalid_committed_root_is_refused_by_both_verbs():
    """The 16-root gap, driven rather than read.

    Measured before this tranche: `amend` PASSED on 6 of 6 driven replay-invalid
    committed roots, and `continue` ACCEPTED 3 of the 6 outright.
    """

    witnesses = _replay_invalid_committed_roots()
    assert witnesses, (
        "no committed root publishes an invalid replay verdict any more; "
        "the integrity gate has lost its witnesses"
    )

    driven = [(root, events) for root, events in witnesses if events <= _MAX_DRIVEN_EVENTS]
    assert driven, (
        f"every replay-invalid witness is over the {_MAX_DRIVEN_EVENTS}-event "
        "runtime budget; raise the budget rather than skipping the proof"
    )

    for root, _events in driven:
        manifest = load_run_manifest(root / MANIFEST_NAME)
        with tempfile.TemporaryDirectory() as scratch:
            copy = _copy(root, scratch)
            with pytest.raises(ValueError) as refused:
                prepare_continuation(
                    copy, cycles=1, tokens=10, check_operator_lock=False
                )
            assert str(refused.value).startswith("CONTINUE_RECORD_NOT_VERIFIED: "), (
                f"{root} publishes valid:false and continue answered "
                f"{refused.value}"
            )
        with tempfile.TemporaryDirectory() as scratch:
            copy = _copy(root, scratch)
            with pytest.raises(AmendmentError) as amend_refused:
                _require_terminal_stop(copy, manifest)
            assert amend_refused.value.code == "AMEND_RECORD_NOT_VERIFIED", (
                f"{root} publishes valid:false and amend answered "
                f"{amend_refused.value.code}"
            )


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
    """The evidence this module reads is evidence: it may never move."""

    # `--untracked-files=no`: a tranche's own NEW files are not a mutation of
    # a committed root, and this assertion is about mutation.
    dirty = subprocess.run(
        [
            "git", "status", "--porcelain", "--untracked-files=no",
            "experiments", "runs",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert dirty == "", f"a committed root moved: {dirty}"
