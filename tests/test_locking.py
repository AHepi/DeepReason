"""Cross-platform kernel locking and hostile lock-path regression tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import deepreason.locking as locking_module
from deepreason.locking import (
    MAKE_OPERATOR_LOCK_NAME,
    OPERATOR_LOCK_NAMES,
    RUN_OPERATOR_LOCK_NAME,
    ProcessLock,
    ProcessLockBusy,
    ProcessLockError,
    operator_locks,
)


def test_process_lock_contention_metadata_release_and_reuse(tmp_path):
    path = tmp_path / "process.lock"
    primary = ProcessLock(path, owner="primary", blocking=False)

    with primary:
        assert primary.acquired
        assert primary.metadata() == {"owner": "primary", "pid": os.getpid()}
        with pytest.raises(ProcessLockBusy):
            ProcessLock(path, owner="contender", blocking=False).acquire()

    assert not primary.acquired
    assert path.exists()
    assert path.read_bytes() == b"\0"
    assert primary.metadata() is None
    with ProcessLock(path, owner="successor", blocking=False) as successor:
        assert successor.metadata()["owner"] == "successor"


def test_operator_locks_are_exact_and_all_or_none(tmp_path):
    root = tmp_path / "run"
    held = ProcessLock(
        root / RUN_OPERATOR_LOCK_NAME,
        owner="existing-run",
        blocking=False,
    )
    held.acquire()
    try:
        with pytest.raises(ProcessLockBusy):
            operator_locks(root, owner="make", blocking=False)
        # The first sorted lock was released after the second lock contended.
        with ProcessLock(
            root / MAKE_OPERATOR_LOCK_NAME,
            owner="probe",
            blocking=False,
        ):
            pass
    finally:
        held.release()

    locks = operator_locks(root, owner="make", blocking=False)
    try:
        assert locks.acquired
        assert {lock.path.name for lock in locks.locks} == set(OPERATOR_LOCK_NAMES)
    finally:
        locks.release()
    assert all((root / name).exists() for name in OPERATOR_LOCK_NAMES)
    assert all((root / name).read_bytes() == b"\0" for name in OPERATOR_LOCK_NAMES)


def test_symlink_lock_path_is_rejected_without_touching_target(tmp_path):
    target = tmp_path / "sensitive.txt"
    target.write_text("do not change", encoding="utf-8")
    lock_path = tmp_path / "process.lock"
    try:
        lock_path.symlink_to(target)
    except OSError as error:  # pragma: no cover - restricted Windows policy
        pytest.skip(f"symlinks unavailable: {error}")

    with pytest.raises(ProcessLockError):
        ProcessLock(lock_path, owner="unsafe", blocking=False).acquire()

    assert target.read_text(encoding="utf-8") == "do not change"
    assert ProcessLock(lock_path, owner="reader").metadata() is None


def test_hardlinked_lock_path_is_rejected_without_touching_target(tmp_path):
    target = tmp_path / "sensitive.txt"
    target.write_text("do not change", encoding="utf-8")
    lock_path = tmp_path / "process.lock"
    try:
        os.link(target, lock_path)
    except OSError as error:  # pragma: no cover - filesystem-dependent
        pytest.skip(f"hardlinks unavailable: {error}")

    with pytest.raises(ProcessLockError):
        ProcessLock(lock_path, owner="unsafe", blocking=False).acquire()

    assert target.read_text(encoding="utf-8") == "do not change"


@pytest.mark.parametrize("kind", ["directory", "invalid-file"])
def test_non_lock_paths_are_rejected_without_mutation(tmp_path, kind):
    path = tmp_path / "process.lock"
    if kind == "directory":
        path.mkdir()
        before = None
    else:
        path.write_bytes(b"not-a-deepreason-lock")
        before = path.read_bytes()

    with pytest.raises(ProcessLockError):
        ProcessLock(path, owner="unsafe", blocking=False).acquire()

    assert path.is_dir() if kind == "directory" else path.read_bytes() == before


def test_windows_byte_range_backend_can_be_selected_without_fcntl(
    tmp_path, monkeypatch
):
    calls: list[tuple[int, int]] = []
    fake = SimpleNamespace(LK_LOCK=1, LK_NBLCK=2, LK_UNLCK=3)
    fake.locking = lambda _fd, mode, count: calls.append((mode, count))
    monkeypatch.setitem(sys.modules, "msvcrt", fake)

    lock = ProcessLock(
        tmp_path / "windows.lock",
        owner="windows-test",
        blocking=False,
        _platform="windows",
    )
    lock.acquire()
    assert lock.metadata() == {"owner": "windows-test", "pid": os.getpid()}
    lock.release()

    assert calls == [(fake.LK_NBLCK, 1), (fake.LK_UNLCK, 1)]
    assert lock.path.read_bytes() == b"\0"


def test_windows_blocking_lock_waits_past_lk_lock_exhaustion_until_available(
    tmp_path, monkeypatch
):
    calls: list[tuple[int, int]] = []
    sleeps: list[float] = []
    nonblocking_attempts = 0
    fake = SimpleNamespace(LK_LOCK=1, LK_NBLCK=2, LK_UNLCK=3)

    def controlled_locking(_fd, mode, count):
        nonlocal nonblocking_attempts
        calls.append((mode, count))
        if mode == fake.LK_LOCK:
            raise OSError(13, "simulated LK_LOCK retry exhaustion")
        if mode == fake.LK_NBLCK:
            nonblocking_attempts += 1
            if nonblocking_attempts < 3:
                raise OSError(13, "simulated ordinary contention")

    fake.locking = controlled_locking
    monkeypatch.setitem(sys.modules, "msvcrt", fake)
    monkeypatch.setattr(time, "sleep", sleeps.append)

    lock = ProcessLock(
        tmp_path / "blocking-windows.lock",
        owner="blocking-windows-test",
        blocking=True,
        _platform="windows",
    )
    lock.acquire()
    assert lock.acquired
    lock.release()

    assert calls == [
        (fake.LK_NBLCK, 1),
        (fake.LK_NBLCK, 1),
        (fake.LK_NBLCK, 1),
        (fake.LK_UNLCK, 1),
    ]
    assert sleeps == [
        locking_module._WINDOWS_LOCK_POLL_SECONDS,
        locking_module._WINDOWS_LOCK_POLL_SECONDS,
    ]
    assert lock.path.read_bytes() == b"\0"


def test_windows_nonblocking_lock_is_fail_fast_and_never_waits(
    tmp_path, monkeypatch
):
    calls: list[tuple[int, int]] = []
    fake = SimpleNamespace(LK_LOCK=1, LK_NBLCK=2, LK_UNLCK=3)

    def contended(_fd, mode, count):
        calls.append((mode, count))
        raise OSError(13, "simulated ordinary contention")

    fake.locking = contended
    monkeypatch.setitem(sys.modules, "msvcrt", fake)
    monkeypatch.setattr(
        time,
        "sleep",
        lambda _interval: pytest.fail("nonblocking acquisition must not wait"),
    )

    with pytest.raises(ProcessLockBusy, match="process lock is already held"):
        ProcessLock(
            tmp_path / "nonblocking-windows.lock",
            owner="nonblocking-windows-test",
            blocking=False,
            _platform="windows",
        ).acquire()

    assert calls == [(fake.LK_NBLCK, 1)]


def test_windows_noncontention_error_is_not_reclassified_as_busy(
    tmp_path, monkeypatch
):
    fake = SimpleNamespace(LK_LOCK=1, LK_NBLCK=2, LK_UNLCK=3)

    def unavailable(_fd, _mode, _count):
        raise OSError(22, "simulated unexpected operating-system failure")

    fake.locking = unavailable
    monkeypatch.setitem(sys.modules, "msvcrt", fake)

    with pytest.raises(OSError) as caught:
        ProcessLock(
            tmp_path / "unexpected-windows.lock",
            owner="unexpected-windows-test",
            blocking=False,
            _platform="windows",
        ).acquire()

    assert caught.value.errno == 22


def test_portable_modules_import_when_fcntl_is_unavailable(tmp_path):
    source_root = Path(__file__).resolve().parents[1] / "src"
    script = r'''
import builtins
import json

original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "fcntl":
        raise ImportError("simulated Windows host")
    return original(name, *args, **kwargs)
builtins.__import__ = guarded

import deepreason.brain.log
import deepreason.mcp_server
import deepreason.run_manifest
import deepreason.runtime.continuation

print(json.dumps({"imported": True}))
'''
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(source_root)

    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {"imported": True}


def test_process_death_releases_kernel_lock_and_stale_metadata_is_replaced(tmp_path):
    path = tmp_path / "crashed.lock"
    source_root = Path(__file__).resolve().parents[1] / "src"
    script = r'''
import os
import sys
from deepreason.locking import ProcessLock

ProcessLock(sys.argv[1], owner="crashed-child", blocking=False).acquire()
os._exit(0)
'''
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(source_root)
    completed = subprocess.run(
        [sys.executable, "-c", script, str(path)],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    probe = ProcessLock(path, owner="metadata-probe", blocking=False)
    assert probe.metadata()["owner"] == "crashed-child"
    with ProcessLock(path, owner="successor", blocking=False) as successor:
        assert successor.metadata()["owner"] == "successor"
    assert path.read_bytes() == b"\0"
