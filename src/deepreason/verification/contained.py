"""Contained subprocess runner for model-authored ``sandboxed_python_v1``.

The declarative backend keeps model influence out of the executed program by
construction; this backend instead executes harness-validated model Python and
therefore treats the *operating-system process* as the containment boundary:

- the job runs in a fresh disposable scratch working directory, never the run
  root; the only inputs are files the harness wrote there and the only outputs
  are files read back, content-addressed, and receipted;
- the worker environment is scrubbed to a fixed allowlist — no credentials, no
  ``DEEPREASON_*`` configuration, no inherited variables;
- hard resource limits (CPU, address space, file size, descriptors, process
  count) are applied in the child before ``exec`` and failure to apply any of
  them fails CLOSED into a typed refusal, never into an unlimited run;
- network access is denied by executing the worker inside an unshared network
  namespace (``unshare --net``); when the kernel does not permit namespace
  creation the backend refuses to execute rather than running with a network.

The worker program itself is a frozen, self-contained script (its digest is
part of every execution fingerprint) so a scrubbed environment cannot break it
and no repository code is importable from inside the containment boundary.
A pinned toolchain entry (``runner="container"``) freezes the interpreter
identity; running DeepReason from a virtual environment pins that venv's
interpreter, which is a reproducibility identity — the safety properties come
from the process containment above, never from the venv.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, ClassVar, Literal

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.verification.simulation import (
    SimulationRequest,
    SimulationVerificationResult,
    _json_safe,
)

_IPC_LIMIT = 8 * 1024 * 1024
_STREAM_RETAIN_BYTES = 65_536
_NOFILE_LIMIT = 64
_NPROC_LIMIT = 2_048
_WALL_STARTUP_GRACE_MS = 2_000

# The complete containment-side runtime. It is intentionally self-contained
# (standard library only) so the scrubbed environment needs no PYTHONPATH and
# nothing inside the namespace can import repository code. Its sha256 appears
# in every execution fingerprint: a changed worker is a changed runtime
# identity, visible in each immutable receipt.
CONTAINED_WORKER_SOURCE_V1 = '''\
"""DeepReason contained simulation worker: job.json in, result.json out."""
import ast
import builtins
import json
import math
import random
import sys

IPC_LIMIT = 8 * 1024 * 1024
ALLOWED_BUILTINS = (
    "abs all any bool chr dict divmod enumerate filter float int isinstance len "
    "list map max min ord pow range reversed round set sorted str sum tuple zip"
).split()
SAFE_BUILTINS = {name: getattr(builtins, name) for name in ALLOWED_BUILTINS}


class StepExceeded(Exception):
    pass


def guard(source, label):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            raise ValueError(label + " may not import or mutate scope")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError(label + " may not traverse private attributes")
    return tree


def load_function(source, entry, label, namespace_extras):
    try:
        tree = guard(source, label)
    except (SyntaxError, ValueError) as error:
        return None, label + " unsafe or unparseable: " + str(error)
    namespace = {"__builtins__": dict(SAFE_BUILTINS)}
    namespace.update(namespace_extras)
    try:
        exec(compile(tree, "<" + label + ">", "exec"), namespace)
    except StepExceeded:
        return None, label + " exceeded step limit while loading"
    except MemoryError:
        raise
    except Exception as error:
        return None, label + " did not load: " + type(error).__name__ + ": " + str(error)
    function = namespace.get(entry)
    if not callable(function):
        return None, label + " entry " + repr(entry) + " is not defined"
    return function, None


def json_safe(value):
    if value is None or isinstance(value, (bool, str, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(json_safe(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and json_safe(item) for key, item in value.items()
        )
    return False


_ABSENT = object()


def resolve_observable(output, name):
    """Literal key first, then dotted traversal. Returns _ABSENT if neither.

    Literal-first makes this strictly widening: every name that resolved before
    dotted paths existed still resolves to exactly the same value, including a
    program that legitimately returns flat keys containing dots.
    """
    if name in output:
        return output[name]
    cursor = output
    for segment in name.split("."):
        if not isinstance(cursor, dict) or segment not in cursor:
            return _ABSENT
        cursor = cursor[segment]
    return cursor


def run(job):
    seeds = job["seeds"]
    inputs = job["inputs"]
    step_limit = job["step_limit"]
    sample_limit = job["sample_limit"]
    observables = job["observables"]
    sample_count = len(seeds) * len(inputs)
    if sample_count > sample_limit:
        return {
            "verdict": "overrun",
            "trace": {
                "error": "declared seed/input product exceeds sample limit",
                "sample_count": sample_count,
                "sample_limit": sample_limit,
            },
            "output": [],
        }
    records = []
    steps = [0]

    def tracer(_frame, event, _arg):
        if event == "line":
            steps[0] += 1
            if steps[0] > step_limit:
                raise StepExceeded()
        return tracer

    previous_trace = sys.gettrace()
    sys.settrace(tracer)
    try:
        simulation, error = load_function(
            job["source"], job["entry"], "simulation", {"math": math}
        )
        if error:
            return {"verdict": "fail", "trace": {"error": error}, "output": records}
        checker, error = load_function(job["checker_source"], "check", "checker", {})
        if error:
            return {"verdict": "overrun", "trace": {"error": error}, "output": records}
        for seed in seeds:
            for input_index, input_item in enumerate(inputs):
                rng = random.Random(seed)
                try:
                    output = simulation(input_item, rng)
                except StepExceeded:
                    return {
                        "verdict": "fail",
                        "trace": {
                            "error": "deterministic step limit exceeded",
                            "steps": steps[0],
                        },
                        "output": records,
                    }
                except MemoryError:
                    raise
                except Exception as error:
                    return {
                        "verdict": "fail",
                        "trace": {
                            "error": "simulation raised "
                            + type(error).__name__
                            + ": "
                            + str(error),
                            "seed": seed,
                            "input_index": input_index,
                        },
                        "output": records,
                    }
                if not isinstance(output, dict) or not json_safe(output):
                    return {
                        "verdict": "fail",
                        "trace": {
                            "error": "simulation output must be a finite JSON mapping",
                            "seed": seed,
                            "input_index": input_index,
                        },
                        "output": records,
                    }
                resolved = {}
                missing = []
                for name in observables:
                    value = resolve_observable(output, name)
                    if value is _ABSENT:
                        missing.append(name)
                    else:
                        resolved[name] = value
                if missing:
                    return {
                        "verdict": "fail",
                        "trace": {
                            "error": "declared observable missing",
                            "missing": missing,
                            "seed": seed,
                            "input_index": input_index,
                        },
                        "output": records,
                    }
                try:
                    checked = checker(input_item, seed, output)
                except StepExceeded:
                    return {
                        "verdict": "overrun",
                        "trace": {"error": "checker exceeded deterministic step limit"},
                        "output": records,
                    }
                except MemoryError:
                    raise
                except Exception as error:
                    return {
                        "verdict": "overrun",
                        "trace": {
                            "error": "checker raised "
                            + type(error).__name__
                            + ": "
                            + str(error)
                        },
                        "output": records,
                    }
                metrics = {}
                if isinstance(checked, bool):
                    passed = checked
                elif (
                    isinstance(checked, dict)
                    and isinstance(checked.get("pass"), bool)
                    and json_safe(checked.get("metrics", {}))
                ):
                    passed = checked["pass"]
                    metrics = checked.get("metrics", {})
                else:
                    return {
                        "verdict": "overrun",
                        "trace": {"error": "checker returned an invalid result"},
                        "output": records,
                    }
                record = {
                    "seed": seed,
                    "input_index": input_index,
                    "observables": resolved,
                    "metrics": metrics,
                    "passed": passed,
                }
                records.append(record)
                if not passed:
                    return {
                        "verdict": "fail",
                        "trace": {
                            "error": "checker rejected simulation output",
                            "seed": seed,
                            "input_index": input_index,
                            "steps": steps[0],
                        },
                        "output": records,
                    }
    finally:
        sys.settrace(previous_trace)
    return {
        "verdict": "pass",
        "trace": {"samples_passed": len(records), "steps": steps[0]},
        "output": records,
    }


def main():
    with open("job.json", "rb") as handle:
        raw = handle.read(IPC_LIMIT + 1)
    if len(raw) > IPC_LIMIT:
        result = {
            "verdict": "overrun",
            "trace": {"sandbox_abort": "job exceeds IPC limit"},
            "output": [],
        }
    else:
        try:
            result = run(json.loads(raw))
        except (MemoryError, StepExceeded):
            result = {
                "verdict": "overrun",
                "trace": {"sandbox_abort": "resource containment"},
                "output": [],
            }
        except BaseException as error:
            result = {
                "verdict": "overrun",
                "trace": {
                    "worker_error": type(error).__name__ + ": " + str(error)[:300]
                },
                "output": [],
            }
    encoded = json.dumps(
        result, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(encoded) > IPC_LIMIT:
        encoded = json.dumps(
            {
                "verdict": "overrun",
                "trace": {"sandbox_abort": "result exceeds IPC limit"},
                "output": [],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    with open("result.json", "wb") as handle:
        handle.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

CONTAINED_WORKER_SHA256 = sha256_hex(CONTAINED_WORKER_SOURCE_V1.encode("utf-8"))


class ContainmentUnavailableError(RuntimeError):
    """The host cannot provide the frozen containment envelope."""


def _contained_environment(scratch: str) -> dict[str, str]:
    """The complete worker environment: a fixed allowlist, nothing inherited."""

    return {
        "HOME": scratch,
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "TMPDIR": scratch,
    }


def _containment_limits(
    *, maximum_wall_ms: int, maximum_memory_bytes: int
) -> dict[str, int]:
    return {
        "cpu_seconds": max(1, math.ceil(maximum_wall_ms / 1_000)),
        "memory_bytes": maximum_memory_bytes,
        "fsize_bytes": _IPC_LIMIT,
        "nofile": _NOFILE_LIMIT,
        "nproc": _NPROC_LIMIT,
    }


def _apply_containment_limits(limits: dict[str, int]) -> None:
    """Apply every hard limit in the child; any failure aborts the exec.

    This intentionally inverts the local backend's best-effort posture: a
    containment limit that cannot be applied is a refused execution, not a
    softer one.
    """

    import resource

    os.setsid()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(
        resource.RLIMIT_CPU, (limits["cpu_seconds"], limits["cpu_seconds"] + 1)
    )
    resource.setrlimit(
        resource.RLIMIT_AS, (limits["memory_bytes"], limits["memory_bytes"])
    )
    resource.setrlimit(
        resource.RLIMIT_FSIZE, (limits["fsize_bytes"], limits["fsize_bytes"])
    )
    resource.setrlimit(resource.RLIMIT_NOFILE, (limits["nofile"], limits["nofile"]))
    resource.setrlimit(resource.RLIMIT_NPROC, (limits["nproc"], limits["nproc"]))


def _kill_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            process.kill()
        except ProcessLookupError:
            pass


class ContainedSimulationBackend:
    """Execute one compiled sandboxed-Python job inside the containment envelope."""

    name = "simulation-python-contained"

    # Cached probe outcome: None = not yet probed, () = unavailable,
    # otherwise the exact command prefix that denies network access.
    _containment_prefix: ClassVar[tuple[str, ...] | None] = None

    def __init__(
        self,
        toolchain_id: str | None = None,
        *,
        maximum_wall_ms: int,
        maximum_memory_bytes: int,
    ) -> None:
        self.toolchain_id = toolchain_id or (
            f"python@{sys.version_info.major}.{sys.version_info.minor}"
        )
        if not 1 <= maximum_wall_ms <= 300_000:
            raise ValueError("contained simulation wall limit must be finite and positive")
        if not 1 <= maximum_memory_bytes <= 4 * 1024 * 1024 * 1024:
            raise ValueError(
                "contained simulation memory limit must be finite and positive"
            )
        self.maximum_wall_ms = maximum_wall_ms
        self.maximum_memory_bytes = maximum_memory_bytes

    @classmethod
    def containment_prefix(cls) -> tuple[str, ...]:
        """Return the probed network-denial command prefix; () when unavailable.

        The probe runs the real interpreter inside the candidate namespace so
        availability means the exact execution shape works, not merely that an
        ``unshare`` binary exists.  The result is cached per process.
        """

        if cls._containment_prefix is not None:
            return cls._containment_prefix
        prefix: tuple[str, ...] = ()
        unshare = shutil.which("unshare")
        if unshare is not None:
            for flags in (("--map-root-user", "--net"), ("--net",)):
                candidate = (unshare, *flags, "--")
                try:
                    probe = subprocess.run(  # noqa: S603 - fixed probe command
                        [*candidate, sys.executable, "-c", "raise SystemExit(0)"],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=20,
                    )
                except (OSError, subprocess.TimeoutExpired):
                    continue
                if probe.returncode == 0:
                    prefix = candidate
                    break
        cls._containment_prefix = prefix
        return prefix

    @classmethod
    def containment_available(cls) -> bool:
        return bool(cls.containment_prefix())

    def fingerprint(self) -> dict[str, Any]:
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        return {
            "backend": self.name,
            "toolchain_id": self.toolchain_id,
            "python_version": version,
            "executable": str(Path(sys.executable).resolve()),
            "version_output_sha256": sha256_hex(version.encode()),
            "worker_sha256": CONTAINED_WORKER_SHA256,
            "network_denial": "namespace_unshared",
        }

    def resource_limits(self) -> dict[str, Any]:
        limits = _containment_limits(
            maximum_wall_ms=self.maximum_wall_ms,
            maximum_memory_bytes=self.maximum_memory_bytes,
        )
        return {
            "ipc_bytes": _IPC_LIMIT,
            "memory_bytes": limits["memory_bytes"],
            "cpu_seconds": limits["cpu_seconds"],
            "wall_ms": self.maximum_wall_ms,
            "wall_startup_grace_ms": _WALL_STARTUP_GRACE_MS,
            "fsize_bytes": limits["fsize_bytes"],
            "nofile": limits["nofile"],
            "nproc": limits["nproc"],
            "filesystem": "ephemeral scratch workdir",
            "network": False,
            "network_denial": "namespace_unshared",
        }

    def _refusal(
        self,
        request: SimulationRequest,
        blobs,
        *,
        trace: dict[str, Any],
        source_bytes: bytes,
        inputs_bytes: bytes,
        checker_bytes: bytes,
        stderr: bytes = b"",
    ) -> SimulationVerificationResult:
        return SimulationVerificationResult(
            backend=self.name,
            fingerprint=self.fingerprint(),
            verdict="overrun",
            diagnostics_ref=blobs.put(canonical_json(trace)),
            output_ref=blobs.put(b"[]"),
            trace=trace,
            source_sha256=sha256_hex(source_bytes),
            inputs_sha256=sha256_hex(inputs_bytes),
            checker_sha256=sha256_hex(checker_bytes),
            spec_sha256=sha256_hex(canonical_json(request.spec.model_dump(mode="json"))),
            stdout_ref=blobs.put(b""),
            stderr_ref=blobs.put(stderr[:_STREAM_RETAIN_BYTES]),
        )

    def verify(self, request: SimulationRequest, blobs=None) -> SimulationVerificationResult:
        if blobs is None:
            raise ValueError("contained simulation requires a content-addressed blob store")
        source_bytes = blobs.get(request.source_ref)
        inputs_bytes = blobs.get(request.spec.inputs_ref)
        checker_bytes = blobs.get(request.spec.checker_ref)
        refusal_context = {
            "source_bytes": source_bytes,
            "inputs_bytes": inputs_bytes,
            "checker_bytes": checker_bytes,
        }
        if request.spec.toolchain_id != self.toolchain_id:
            return self._refusal(
                request,
                blobs,
                trace={
                    "unavailable_toolchain": request.spec.toolchain_id,
                    "error": "declared simulation toolchain is unavailable",
                    "available": self.toolchain_id,
                },
                **refusal_context,
            )
        prefix = self.containment_prefix()
        if not prefix:
            # Fail CLOSED: no network namespace means no execution at all.
            return self._refusal(
                request,
                blobs,
                trace={
                    "sandbox_abort": "network containment unavailable",
                    "containment": "network namespace creation was refused by the host",
                },
                **refusal_context,
            )
        try:
            source = source_bytes.decode("utf-8")
            checker = checker_bytes.decode("utf-8")
            inputs = json.loads(inputs_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            return self._refusal(
                request,
                blobs,
                trace={
                    "error": f"invalid pinned simulation input: {error}",
                    "input_error": type(error).__name__,
                },
                **refusal_context,
            )
        if isinstance(inputs, dict):
            inputs = inputs.get("inputs")
        if not isinstance(inputs, list) or not _json_safe(inputs):
            return self._refusal(
                request,
                blobs,
                trace={
                    "error": "inputs_ref must contain a finite JSON list",
                    "input_error": "invalid-shape",
                },
                **refusal_context,
            )
        job = {
            "source": source,
            "checker_source": checker,
            "entry": request.spec.entry,
            "seeds": list(request.spec.seed_set),
            "inputs": inputs,
            "observables": list(request.spec.observables),
            "step_limit": request.spec.deterministic_step_limit,
            "sample_limit": request.spec.sample_limit,
        }
        job_bytes = canonical_json(job)
        if len(job_bytes) > _IPC_LIMIT:
            return self._refusal(
                request,
                blobs,
                trace={"sandbox_abort": "job exceeds IPC limit"},
                **refusal_context,
            )
        limits = _containment_limits(
            maximum_wall_ms=self.maximum_wall_ms,
            maximum_memory_bytes=self.maximum_memory_bytes,
        )
        scratch = tempfile.mkdtemp(prefix="deepreason-contained-")
        stdout = stderr = b""
        try:
            scratch_path = Path(scratch)
            (scratch_path / "worker.py").write_bytes(
                CONTAINED_WORKER_SOURCE_V1.encode("utf-8")
            )
            (scratch_path / "job.json").write_bytes(job_bytes)
            try:
                process = subprocess.Popen(  # noqa: S603 - frozen containment command
                    [*prefix, sys.executable, "worker.py"],
                    cwd=scratch,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=_contained_environment(scratch),
                    close_fds=True,
                    preexec_fn=lambda: _apply_containment_limits(limits),
                )
            except (OSError, subprocess.SubprocessError) as error:
                return self._refusal(
                    request,
                    blobs,
                    trace={
                        "sandbox_abort": "containment could not be established",
                        "containment_error": type(error).__name__,
                    },
                    **refusal_context,
                )
            try:
                stdout, stderr = process.communicate(
                    timeout=(self.maximum_wall_ms + _WALL_STARTUP_GRACE_MS) / 1_000
                )
            except subprocess.TimeoutExpired:
                _kill_group(process)
                process.communicate()
                return self._refusal(
                    request,
                    blobs,
                    trace={"sandbox_abort": "resource watchdog fired"},
                    **refusal_context,
                )
            result_path = scratch_path / "result.json"
            if process.returncode != 0 or not result_path.is_file():
                return self._refusal(
                    request,
                    blobs,
                    trace={
                        "sandbox_abort": "worker terminated by resource containment",
                        "returncode": process.returncode,
                        "stderr_sha256": sha256_hex(stderr),
                    },
                    stderr=stderr,
                    **refusal_context,
                )
            with result_path.open("rb") as handle:
                raw_result = handle.read(_IPC_LIMIT + 1)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        if len(raw_result) > _IPC_LIMIT:
            return self._refusal(
                request,
                blobs,
                trace={"sandbox_abort": "response exceeds IPC limit"},
                **refusal_context,
            )
        try:
            message = json.loads(raw_result)
            verdict = message["verdict"]
            trace = message["trace"]
            output = canonical_json(message["output"])
            if verdict not in {"pass", "fail", "overrun"} or not isinstance(trace, dict):
                raise ValueError("invalid worker result")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            return self._refusal(
                request,
                blobs,
                trace={
                    "sandbox_abort": f"invalid worker response: {type(error).__name__}"
                },
                stderr=stderr,
                **refusal_context,
            )
        try:
            sample_count = len(json.loads(output))
        except (TypeError, json.JSONDecodeError):
            sample_count = 0
        if (
            request.maximum_output_bytes is not None
            and len(output) > request.maximum_output_bytes
        ):
            generated_bytes = len(output)
            generated_sha256 = sha256_hex(output)
            output = output[: request.maximum_output_bytes]
            trace = {
                **trace,
                "output_truncated": True,
                "generated_output_bytes": generated_bytes,
                "generated_output_sha256": generated_sha256,
                "retained_output_bytes": len(output),
            }
            verdict = "overrun"
        return SimulationVerificationResult(
            backend=self.name,
            fingerprint=self.fingerprint(),
            verdict=verdict,
            diagnostics_ref=blobs.put(canonical_json(trace)),
            output_ref=blobs.put(output),
            trace=trace,
            source_sha256=sha256_hex(source_bytes),
            inputs_sha256=sha256_hex(inputs_bytes),
            checker_sha256=sha256_hex(checker_bytes),
            spec_sha256=sha256_hex(canonical_json(request.spec.model_dump(mode="json"))),
            stdout_ref=blobs.put(stdout[:_STREAM_RETAIN_BYTES]),
            stderr_ref=blobs.put(stderr[:_STREAM_RETAIN_BYTES]),
            sample_count=sample_count,
        )


__all__ = [
    "CONTAINED_WORKER_SHA256",
    "CONTAINED_WORKER_SOURCE_V1",
    "ContainedSimulationBackend",
    "ContainmentUnavailableError",
]
