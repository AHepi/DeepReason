"""Disposable subprocess transport for :mod:`deepreason.oracle`.

This module has no epistemic policy. It starts a fresh interpreter, applies
emergency OS resource limits, exchanges size-bounded JSON, and reports whether
the worker returned normally. The oracle layer decides how an unavailable
worker maps to its public no-verdict APIs.
"""

import json
import math
import os
import signal
import subprocess
import sys

from deepreason.canonical import canonical_json

MEMORY_CAP_BYTES = 512 * 1024 * 1024
IPC_CAP_BYTES = 8 * 1024 * 1024
CPU_SECONDS_MIN = 2
CPU_SECONDS_MAX = 30
STEPS_PER_CPU_SECOND = 1_000_000
WALL_GRACE_SECONDS = 3


class _ResourceAbort(Exception):
    """Emergency child-process resource containment fired."""


class SandboxAborted(RuntimeError):
    """The isolated worker died before producing a deterministic result."""


class WorkerError(RuntimeError):
    """Trusted oracle machinery failed inside the isolated worker."""


def _cpu_seconds(step_limit: int, units: int) -> int:
    estimate = math.ceil(max(1, step_limit) * max(1, units) / STEPS_PER_CPU_SECOND)
    return max(CPU_SECONDS_MIN, min(CPU_SECONDS_MAX, estimate))


def _worker_environment() -> dict[str, str]:
    """Minimal environment plus the exact package root running in the parent."""
    keep = (
        "PATH",
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
        "SYSTEMROOT",
        "WINDIR",
        "VIRTUAL_ENV",
    )
    env = {key: os.environ[key] for key in keep if key in os.environ}
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inherited_path = os.environ.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        package_root + (os.pathsep + inherited_path if inherited_path else "")
    )
    env.update(
        {
            "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LC_ALL": "C.UTF-8",
        }
    )
    return env


def _kill_worker(process: subprocess.Popen) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass


def run_isolated(
    operation: str,
    payload: dict,
    *,
    step_limit: int,
    units: int = 1,
):
    """Run one complete oracle operation in a fresh interpreter."""
    cpu_seconds = _cpu_seconds(step_limit, units)
    request = canonical_json(
        {
            "protocol": 1,
            "operation": operation,
            "payload": payload,
            "cpu_seconds": cpu_seconds,
        }
    )
    if len(request) > IPC_CAP_BYTES:
        raise SandboxAborted("request exceeds sandbox IPC limit")
    process = subprocess.Popen(  # noqa: S603 - fixed interpreter/module command
        [sys.executable, "-m", "deepreason.oracle_sandbox", "--worker"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_worker_environment(),
        close_fds=True,
        start_new_session=(os.name == "posix"),
    )
    try:
        stdout, stderr = process.communicate(
            request, timeout=cpu_seconds + WALL_GRACE_SECONDS
        )
    except subprocess.TimeoutExpired as e:
        _kill_worker(process)
        process.communicate()
        raise SandboxAborted("sandbox resource watchdog fired") from e
    if len(stdout) > IPC_CAP_BYTES:
        raise SandboxAborted("response exceeds sandbox IPC limit")
    if process.returncode != 0 and not stdout:
        raise SandboxAborted("sandbox worker terminated by resource containment")
    try:
        message = json.loads(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        diagnostic = stderr.decode("utf-8", errors="replace")[:400]
        raise WorkerError(f"invalid sandbox response: {diagnostic}") from e
    kind = message.get("kind")
    if kind == "abort":
        raise SandboxAborted(str(message.get("reason", "resource containment")))
    if kind == "error":
        raise WorkerError(str(message.get("error", "unknown worker error")))
    if kind != "ok" or not isinstance(message.get("result"), list):
        raise WorkerError("malformed sandbox response")
    return tuple(message["result"])


def _apply_worker_limits(cpu_seconds: int) -> None:
    try:
        import resource
    except ImportError:
        return

    def _bounded_limit(kind, requested: int) -> None:
        _soft, hard = resource.getrlimit(kind)
        ceiling = requested if hard == resource.RLIM_INFINITY else min(requested, hard)
        resource.setrlimit(kind, (ceiling, ceiling))

    try:
        _bounded_limit(resource.RLIMIT_AS, MEMORY_CAP_BYTES)
    except (AttributeError, ValueError, OSError):
        pass
    try:
        soft = max(1, cpu_seconds)
        hard = soft + 1
        _old_soft, old_hard = resource.getrlimit(resource.RLIMIT_CPU)
        if old_hard != resource.RLIM_INFINITY:
            hard = min(hard, old_hard)
            soft = min(soft, hard)
        resource.setrlimit(resource.RLIMIT_CPU, (soft, hard))
        if hasattr(signal, "SIGXCPU"):

            def _cpu_abort(_signum, _frame):
                raise _ResourceAbort("cpu limit")

            signal.signal(signal.SIGXCPU, _cpu_abort)
    except (AttributeError, ValueError, OSError):
        pass


def _write_worker_message(message: dict) -> None:
    try:
        data = canonical_json(message)
    except (MemoryError, TypeError, ValueError):
        data = canonical_json({"kind": "abort", "reason": "unserializable result"})
    if len(data) > IPC_CAP_BYTES:
        data = canonical_json({"kind": "abort", "reason": "result exceeds IPC limit"})
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def _worker_main() -> int:
    raw = sys.stdin.buffer.read(IPC_CAP_BYTES + 1)
    if len(raw) > IPC_CAP_BYTES:
        _write_worker_message({"kind": "abort", "reason": "request exceeds IPC limit"})
        return 0
    try:
        request = json.loads(raw)
        if request.get("protocol") != 1:
            raise ValueError("unsupported worker protocol")
        operation = request["operation"]
        payload = request["payload"]
        cpu_seconds = int(request["cpu_seconds"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
        _write_worker_message({"kind": "error", "error": f"bad worker request: {e}"})
        return 0
    _apply_worker_limits(cpu_seconds)
    try:
        from deepreason.oracle import _LOCAL_OPERATIONS

        result = _LOCAL_OPERATIONS[operation](**payload)
        _write_worker_message({"kind": "ok", "result": result})
    except (MemoryError, _ResourceAbort):
        _write_worker_message({"kind": "abort", "reason": "resource containment"})
    except BaseException as e:  # noqa: BLE001 - serialize trusted worker defects
        _write_worker_message(
            {"kind": "error", "error": f"{type(e).__name__}: {str(e)[:400]}"}
        )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through subprocess APIs
    if sys.argv[1:] != ["--worker"]:
        raise SystemExit("oracle_sandbox.py is internal; expected --worker")
    raise SystemExit(_worker_main())
