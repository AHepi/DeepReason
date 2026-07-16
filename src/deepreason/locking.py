"""Shared cross-platform process locks for one DeepReason run root.

Lock files are operational coordination records, never canonical reasoning
inputs.  They are retained after release so no process can race an unlink and
lock a different inode.  Platform-specific modules are imported only while a
lock is acquired, keeping package and MCP imports portable.
"""

from __future__ import annotations

import json
import os
import stat
import unicodedata
from pathlib import Path
from typing import BinaryIO, Iterable


MAKE_OPERATOR_LOCK_NAME = ".make-operator.lock"
RUN_OPERATOR_LOCK_NAME = ".run-operator.lock"
RUN_MANIFEST_LOCK_NAME = ".run-manifest.lock"
RUN_INPUT_LOCK_NAME = ".run-input.lock"
OPERATOR_LOCK_NAMES = tuple(
    sorted({MAKE_OPERATOR_LOCK_NAME, RUN_OPERATOR_LOCK_NAME})
)

_LOCK_SENTINEL = b"\0"
_MAX_OWNER_CHARS = 128
_MAX_METADATA_BYTES = 1_024


class ProcessLockError(RuntimeError):
    """Base class for stable process-lock failures."""


class ProcessLockBusy(ProcessLockError):
    """The requested lock is currently held by another process or thread."""


class ProcessLockUnavailable(ProcessLockError):
    """The host has no supported process-lock backend."""


def _validated_owner(owner: str) -> str:
    if (
        not isinstance(owner, str)
        or not owner.strip()
        or len(owner) > _MAX_OWNER_CHARS
        or any(unicodedata.category(char).startswith("C") for char in owner)
    ):
        raise ValueError(
            f"lock owner must be printable non-blank text up to {_MAX_OWNER_CHARS} characters"
        )
    return owner


def _metadata(owner: str) -> bytes:
    payload = json.dumps(
        {"owner": owner, "pid": os.getpid()},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(payload) > _MAX_METADATA_BYTES:  # defensive after the owner bound
        raise ValueError("lock metadata exceeds its fixed bound")
    return payload + b"\n"


def _open_lock_file(path: Path) -> BinaryIO:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = path.lstat()
    except FileNotFoundError:
        existing = None
    if existing is not None and not stat.S_ISREG(existing.st_mode):
        raise ProcessLockError("lock path must be a regular non-symlink file")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as error:
        raise ProcessLockError("lock path could not be opened safely") from error
    stream = os.fdopen(descriptor, "r+b", buffering=0)
    try:
        opened = os.fstat(stream.fileno())
        try:
            current = path.lstat()
        except FileNotFoundError as error:
            raise ProcessLockError("lock path changed while it was opened") from error
        if (
            not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(current.st_mode)
            or opened.st_nlink != 1
            or current.st_nlink != 1
        ):
            raise ProcessLockError("lock path must be a regular non-symlink file")
        if (
            opened.st_ino
            and current.st_ino
            and (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino)
        ):
            raise ProcessLockError("lock path changed while it was opened")
        if opened.st_size == 0:
            stream.write(_LOCK_SENTINEL)
            os.fsync(stream.fileno())
        else:
            stream.seek(0)
            if stream.read(1) != _LOCK_SENTINEL:
                raise ProcessLockError("existing lock file has an invalid sentinel")
        stream.seek(0)
        return stream
    except BaseException:
        stream.close()
        raise


def _posix_acquire(stream: BinaryIO, *, blocking: bool) -> None:
    try:
        import fcntl
    except ImportError as error:  # pragma: no cover - exercised by import simulation
        raise ProcessLockUnavailable("POSIX process locking is unavailable") from error
    flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
    try:
        fcntl.flock(stream.fileno(), flags)
    except BlockingIOError as error:
        raise ProcessLockBusy("process lock is already held") from error
    except OSError as error:
        if not blocking and error.errno in {11, 13, 35}:
            raise ProcessLockBusy("process lock is already held") from error
        raise


def _posix_release(stream: BinaryIO) -> None:
    import fcntl

    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _windows_acquire(stream: BinaryIO, *, blocking: bool) -> None:
    try:
        import msvcrt
    except ImportError as error:  # pragma: no cover - non-Windows hosts
        raise ProcessLockUnavailable("Windows process locking is unavailable") from error
    stream.seek(0)
    mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
    try:
        msvcrt.locking(stream.fileno(), mode, 1)
    except OSError as error:
        if not blocking or error.errno in {13, 36}:
            raise ProcessLockBusy("process lock is already held") from error
        raise


def _windows_release(stream: BinaryIO) -> None:
    import msvcrt

    stream.seek(0)
    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


class ProcessLock:
    """One kernel-backed exclusive process lock with bounded owner metadata."""

    def __init__(
        self,
        path: Path | str,
        *,
        owner: str,
        blocking: bool = True,
        _platform: str | None = None,
    ) -> None:
        self.path = Path(path)
        self.owner = _validated_owner(owner)
        self.blocking = bool(blocking)
        self._platform = _platform or ("windows" if os.name == "nt" else "posix")
        if self._platform not in {"posix", "windows"}:
            raise ValueError("lock platform must be posix or windows")
        self._stream: BinaryIO | None = None

    @property
    def acquired(self) -> bool:
        return self._stream is not None

    def _write_metadata(self, stream: BinaryIO) -> None:
        # Byte zero is reserved for Windows' byte-range lock.  Metadata starts
        # at byte one and is never treated as canonical state.
        stream.seek(1)
        stream.truncate(1)
        stream.write(_metadata(self.owner))
        os.fsync(stream.fileno())

    @staticmethod
    def _clear_metadata(stream: BinaryIO) -> None:
        stream.seek(1)
        stream.truncate(1)
        os.fsync(stream.fileno())

    def acquire(self) -> ProcessLock:
        if self._stream is not None:
            raise ProcessLockError("process lock instance is already acquired")
        stream = _open_lock_file(self.path)
        try:
            if self._platform == "windows":
                _windows_acquire(stream, blocking=self.blocking)
            else:
                _posix_acquire(stream, blocking=self.blocking)
            self._write_metadata(stream)
        except BaseException:
            stream.close()
            raise
        self._stream = stream
        return self

    def release(self) -> None:
        stream = self._stream
        if stream is None:
            return
        self._stream = None
        try:
            self._clear_metadata(stream)
        finally:
            try:
                if self._platform == "windows":
                    _windows_release(stream)
                else:
                    _posix_release(stream)
            finally:
                stream.close()

    def metadata(self) -> dict[str, object] | None:
        """Read bounded operational metadata without using it as lock authority."""

        try:
            observed = self.path.lstat()
        except FileNotFoundError:
            return None
        if (
            not stat.S_ISREG(observed.st_mode)
            or observed.st_nlink != 1
            or observed.st_size > _MAX_METADATA_BYTES + 1
        ):
            return None
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_BINARY", 0)
        )
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(self.path, flags)
        except OSError:
            return None
        with os.fdopen(descriptor, "rb", buffering=0) as stream:
            opened = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or opened.st_size > _MAX_METADATA_BYTES + 1
            ):
                return None
            payload = stream.read(_MAX_METADATA_BYTES + 2)
        try:
            current = self.path.lstat()
        except FileNotFoundError:
            return None
        if not stat.S_ISREG(current.st_mode) or current.st_nlink != 1:
            return None
        if (
            opened.st_ino
            and current.st_ino
            and (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino)
        ):
            return None
        if len(payload) > _MAX_METADATA_BYTES + 1:
            return None
        if not payload.startswith(_LOCK_SENTINEL):
            return None
        raw = payload[1:].strip() if payload.startswith(_LOCK_SENTINEL) else b""
        if not raw:
            return None
        try:
            value = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def __enter__(self) -> ProcessLock:
        return self if self.acquired else self.acquire()

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.release()


class ProcessLockSet:
    """Acquire multiple locks in stable order, or retain none of them."""

    def __init__(self, locks: Iterable[ProcessLock]) -> None:
        values = sorted(locks, key=lambda lock: str(lock.path))
        if not values:
            raise ValueError("a process lock set cannot be empty")
        if len({lock.path for lock in values}) != len(values):
            raise ValueError("a process lock set cannot contain duplicate paths")
        self.locks = tuple(values)
        self._acquired: list[ProcessLock] = []

    @property
    def acquired(self) -> bool:
        return len(self._acquired) == len(self.locks)

    def acquire(self) -> ProcessLockSet:
        if self._acquired:
            raise ProcessLockError("process lock set is already acquired")
        try:
            for lock in self.locks:
                lock.acquire()
                self._acquired.append(lock)
        except BaseException:
            self.release()
            raise
        return self

    def release(self) -> None:
        while self._acquired:
            self._acquired.pop().release()

    def __enter__(self) -> ProcessLockSet:
        return self if self.acquired else self.acquire()

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.release()


def operator_locks(
    root: Path | str,
    *,
    owner: str,
    blocking: bool = False,
) -> ProcessLockSet:
    """Claim both legacy operator lock names for one run root."""

    root_path = Path(root)
    group = ProcessLockSet(
        ProcessLock(root_path / name, owner=owner, blocking=blocking)
        for name in OPERATOR_LOCK_NAMES
    )
    return group.acquire()


__all__ = [
    "MAKE_OPERATOR_LOCK_NAME",
    "OPERATOR_LOCK_NAMES",
    "ProcessLock",
    "ProcessLockBusy",
    "ProcessLockError",
    "ProcessLockSet",
    "ProcessLockUnavailable",
    "RUN_MANIFEST_LOCK_NAME",
    "RUN_INPUT_LOCK_NAME",
    "RUN_OPERATOR_LOCK_NAME",
    "operator_locks",
]
