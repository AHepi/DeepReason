"""Deterministic, model-scoped Python simulation backend.

The candidate implements ``entry(input_item, rng)`` and returns a mapping that
contains every declared observable.  ``rng`` is a fresh ``random.Random`` made
from the current pinned seed; no global randomness is available.  The pinned
checker implements ``check(input_item, seed, output)`` and returns either a
boolean or ``{"pass": bool, "metrics": {...}}``.

Candidate and checker imports, file access, environment access, clocks, network
access, underscore/dunder traversal and unbounded exponentiation are excluded by
the AST and builtin boundary.  The complete operation runs in a disposable
subprocess.  Deterministic step/sample limits produce ordinary traces; an OS
watchdog or resource kill is containment only and returns ``overrun``.

A passing result says only that this executable model satisfied this checker on
these inputs and seeds.  This module creates no real-world relevance relation
and never mutates graph status.
"""

from __future__ import annotations

import ast
import builtins
import json
import math
import os
import random
import signal
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.verification.models import VerificationResult
from deepreason.workloads.code import SimulationSpec

_INT_LITERAL_CAP = 1_000_000
_IPC_LIMIT = 8 * 1024 * 1024
_MEMORY_LIMIT = 512 * 1024 * 1024
_CPU_SECONDS = 20
_WALL_GRACE_SECONDS = 3
_ALLOWED_BUILTINS = (
    "abs all any bool chr dict divmod enumerate filter float int isinstance len "
    "list map max min ord range reversed round set sorted str sum tuple zip"
).split()
_SAFE_BUILTINS = {name: getattr(builtins, name) for name in _ALLOWED_BUILTINS}


class SimulationRequest(BaseModel):
    """A source artifact plus its frozen simulation interface."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_ref: str = Field(pattern=r"^[0-9a-f]{64}$")
    spec: SimulationSpec


class SimulationVerificationResult(VerificationResult):
    backend: Literal["simulation-python"] = "simulation-python"
    source_sha256: str
    inputs_sha256: str
    checker_sha256: str
    spec_sha256: str
    stdout_ref: str
    stderr_ref: str
    sample_count: int = 0


class _StepExceeded(Exception):
    pass


@contextmanager
def _step_budget(limit: int):
    steps = [0]

    def tracer(_frame, event, _arg):
        if event == "line":
            steps[0] += 1
            if steps[0] > limit:
                raise _StepExceeded()
        return tracer

    previous = sys.gettrace()
    sys.settrace(tracer)
    try:
        yield steps
    finally:
        sys.settrace(previous)


def _guard(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("imports are not allowed")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError(f"underscore attribute .{node.attr}")
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise ValueError(f"underscore name {node.id}")
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            raise ValueError("global/nonlocal is not allowed")
        if isinstance(node, ast.Pow):
            raise ValueError("exponentiation is not allowed")
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, int)
            and abs(node.value) > _INT_LITERAL_CAP
        ):
            raise ValueError(f"integer literal exceeds {_INT_LITERAL_CAP}")


def _compile(source: str, entry: str, label: str):
    try:
        tree = ast.parse(source)
        _guard(tree)
    except (SyntaxError, ValueError) as error:
        return None, f"{label} unsafe or unparseable: {error}"
    namespace = {"__builtins__": dict(_SAFE_BUILTINS)}
    try:
        exec(compile(tree, f"<{label}>", "exec"), namespace)  # noqa: S102 - guarded+isolated
    except _StepExceeded:
        return None, f"{label} exceeded step limit while loading"
    except MemoryError:
        raise
    except Exception as error:  # noqa: BLE001 - deterministic user-code diagnostic
        return None, f"{label} did not load: {type(error).__name__}: {error}"
    function = namespace.get(entry)
    if not callable(function):
        return None, f"{label} entry {entry!r} is not defined"
    return function, None


def _json_safe(value: Any) -> bool:
    if value is None or isinstance(value, (bool, str, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_json_safe(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _json_safe(item) for key, item in value.items())
    return False


def _local_run(
    source: str,
    checker_source: str,
    entry: str,
    seeds: list[int],
    inputs: list[Any],
    observables: list[str],
    step_limit: int,
    sample_limit: int,
) -> dict[str, Any]:
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
    records: list[dict[str, Any]] = []
    with _step_budget(step_limit) as steps:
        simulation, error = _compile(source, entry, "simulation")
        if error:
            return {"verdict": "fail", "trace": {"error": error}, "output": records}
        checker, error = _compile(checker_source, "check", "checker")
        if error:
            return {"verdict": "overrun", "trace": {"error": error}, "output": records}
        for seed in seeds:
            for input_index, input_item in enumerate(inputs):
                rng = random.Random(seed)
                try:
                    output = simulation(input_item, rng)
                except _StepExceeded:
                    return {
                        "verdict": "fail",
                        "trace": {"error": "deterministic step limit exceeded", "steps": steps[0]},
                        "output": records,
                    }
                except MemoryError:
                    raise
                except Exception as error:  # noqa: BLE001 - candidate failure
                    return {
                        "verdict": "fail",
                        "trace": {
                            "error": f"simulation raised {type(error).__name__}: {error}",
                            "seed": seed,
                            "input_index": input_index,
                        },
                        "output": records,
                    }
                if not isinstance(output, dict) or not _json_safe(output):
                    return {
                        "verdict": "fail",
                        "trace": {
                            "error": "simulation output must be a finite JSON mapping",
                            "seed": seed,
                            "input_index": input_index,
                        },
                        "output": records,
                    }
                missing = [name for name in observables if name not in output]
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
                except _StepExceeded:
                    return {
                        "verdict": "overrun",
                        "trace": {"error": "checker exceeded deterministic step limit"},
                        "output": records,
                    }
                except MemoryError:
                    raise
                except Exception as error:  # noqa: BLE001 - broken pinned checker
                    return {
                        "verdict": "overrun",
                        "trace": {"error": f"checker raised {type(error).__name__}: {error}"},
                        "output": records,
                    }
                metrics: dict[str, Any] = {}
                if isinstance(checked, bool):
                    passed = checked
                elif (
                    isinstance(checked, dict)
                    and isinstance(checked.get("pass"), bool)
                    and _json_safe(checked.get("metrics", {}))
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
                    "observables": {name: output[name] for name in observables},
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
    return {
        "verdict": "pass",
        "trace": {"samples_passed": len(records), "steps": steps[0]},
        "output": records,
    }


def _worker_environment() -> dict[str, str]:
    package_root = Path(__file__).resolve().parents[2]
    return {
        "LC_ALL": "C.UTF-8",
        "PATH": os.environ.get("PATH", os.defpath),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPATH": str(package_root),
    }


def _kill(process: subprocess.Popen[bytes]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass


def _run_worker(payload: dict[str, Any]) -> tuple[Literal["pass", "fail", "overrun"], dict, bytes]:
    request = canonical_json(payload)
    if len(request) > _IPC_LIMIT:
        return "overrun", {"sandbox_abort": "request exceeds IPC limit"}, b"[]"
    process = subprocess.Popen(  # noqa: S603 - fixed interpreter/module command
        [sys.executable, "-m", "deepreason.verification.simulation", "--worker"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_worker_environment(),
        close_fds=True,
        start_new_session=(os.name == "posix"),
    )
    try:
        stdout, stderr = process.communicate(request, timeout=_CPU_SECONDS + _WALL_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        _kill(process)
        process.communicate()
        return "overrun", {"sandbox_abort": "resource watchdog fired"}, b"[]"
    if process.returncode != 0 and not stdout:
        return (
            "overrun",
            {
                "sandbox_abort": "worker terminated by resource containment",
                "stderr_sha256": sha256_hex(stderr),
            },
            b"[]",
        )
    if len(stdout) > _IPC_LIMIT:
        return "overrun", {"sandbox_abort": "response exceeds IPC limit"}, b"[]"
    try:
        message = json.loads(stdout)
        verdict = message["verdict"]
        trace = message["trace"]
        output = canonical_json(message["output"])
        if verdict not in {"pass", "fail", "overrun"} or not isinstance(trace, dict):
            raise ValueError("invalid worker result")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        return (
            "overrun",
            {"sandbox_abort": f"invalid worker response: {type(error).__name__}"},
            b"[]",
        )
    return verdict, trace, output


def _apply_worker_limits() -> None:
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (_MEMORY_LIMIT, _MEMORY_LIMIT))
        resource.setrlimit(resource.RLIMIT_CPU, (_CPU_SECONDS, _CPU_SECONDS + 1))
    except (ImportError, OSError, ValueError):
        pass


def _worker_main() -> int:
    raw = sys.stdin.buffer.read(_IPC_LIMIT + 1)
    if len(raw) > _IPC_LIMIT:
        sys.stdout.buffer.write(canonical_json({
            "verdict": "overrun",
            "trace": {"sandbox_abort": "request exceeds IPC limit"},
            "output": [],
        }))
        return 0
    _apply_worker_limits()
    try:
        payload = json.loads(raw)
        result = _local_run(**payload)
    except (MemoryError, _StepExceeded):
        result = {
            "verdict": "overrun",
            "trace": {"sandbox_abort": "resource containment"},
            "output": [],
        }
    except BaseException as error:  # noqa: BLE001 - trusted worker defect transport
        result = {
            "verdict": "overrun",
            "trace": {"worker_error": f"{type(error).__name__}: {str(error)[:300]}"},
            "output": [],
        }
    sys.stdout.buffer.write(canonical_json(result))
    sys.stdout.buffer.flush()
    return 0


class SimulationBackend:
    name = "simulation-python"

    def __init__(self, toolchain_id: str | None = None) -> None:
        self.toolchain_id = toolchain_id or (
            f"python@{sys.version_info.major}.{sys.version_info.minor}"
        )

    def fingerprint(self) -> dict[str, Any]:
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        executable = str(Path(sys.executable).resolve())
        return {
            "backend": self.name,
            "toolchain_id": self.toolchain_id,
            "python_version": version,
            "executable": executable,
            "version_output_sha256": sha256_hex(version.encode()),
        }

    def verify(self, request: SimulationRequest, blobs=None) -> SimulationVerificationResult:
        if blobs is None:
            raise ValueError("simulation verification requires a content-addressed blob store")
        source_bytes = blobs.get(request.source_ref)
        inputs_bytes = blobs.get(request.spec.inputs_ref)
        checker_bytes = blobs.get(request.spec.checker_ref)
        if request.spec.toolchain_id != self.toolchain_id:
            diagnostics = canonical_json(
                {
                    "error": "declared simulation toolchain is unavailable",
                    "declared": request.spec.toolchain_id,
                    "available": self.toolchain_id,
                }
            )
            return SimulationVerificationResult(
                fingerprint=self.fingerprint(),
                verdict="overrun",
                diagnostics_ref=blobs.put(diagnostics),
                output_ref=blobs.put(b"[]"),
                trace={"unavailable_toolchain": request.spec.toolchain_id},
                source_sha256=sha256_hex(source_bytes),
                inputs_sha256=sha256_hex(inputs_bytes),
                checker_sha256=sha256_hex(checker_bytes),
                spec_sha256=sha256_hex(
                    canonical_json(request.spec.model_dump(mode="json"))
                ),
                stdout_ref=blobs.put(b""),
                stderr_ref=blobs.put(b""),
            )
        try:
            source = source_bytes.decode("utf-8")
            checker = checker_bytes.decode("utf-8")
            inputs = json.loads(inputs_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            diagnostics = canonical_json({"error": f"invalid pinned simulation input: {error}"})
            empty = b"[]"
            return SimulationVerificationResult(
                fingerprint=self.fingerprint(),
                verdict="overrun",
                diagnostics_ref=blobs.put(diagnostics),
                output_ref=blobs.put(empty),
                trace={"input_error": type(error).__name__},
                source_sha256=sha256_hex(source_bytes),
                inputs_sha256=sha256_hex(inputs_bytes),
                checker_sha256=sha256_hex(checker_bytes),
                spec_sha256=sha256_hex(canonical_json(request.spec.model_dump(mode="json"))),
                stdout_ref=blobs.put(b""),
                stderr_ref=blobs.put(b""),
            )
        if isinstance(inputs, dict):
            inputs = inputs.get("inputs")
        if not isinstance(inputs, list) or not _json_safe(inputs):
            diagnostics = canonical_json({"error": "inputs_ref must contain a finite JSON list"})
            return SimulationVerificationResult(
                fingerprint=self.fingerprint(),
                verdict="overrun",
                diagnostics_ref=blobs.put(diagnostics),
                output_ref=blobs.put(b"[]"),
                trace={"input_error": "invalid-shape"},
                source_sha256=sha256_hex(source_bytes),
                inputs_sha256=sha256_hex(inputs_bytes),
                checker_sha256=sha256_hex(checker_bytes),
                spec_sha256=sha256_hex(canonical_json(request.spec.model_dump(mode="json"))),
                stdout_ref=blobs.put(b""),
                stderr_ref=blobs.put(b""),
            )
        payload = {
            "source": source,
            "checker_source": checker,
            "entry": request.spec.entry,
            "seeds": list(request.spec.seed_set),
            "inputs": inputs,
            "observables": list(request.spec.observables),
            "step_limit": request.spec.deterministic_step_limit,
            "sample_limit": request.spec.sample_limit,
        }
        verdict, trace, output = _run_worker(payload)
        diagnostics = canonical_json(trace)
        return SimulationVerificationResult(
            fingerprint=self.fingerprint(),
            verdict=verdict,
            diagnostics_ref=blobs.put(diagnostics),
            output_ref=blobs.put(output),
            trace=trace,
            source_sha256=sha256_hex(source_bytes),
            inputs_sha256=sha256_hex(inputs_bytes),
            checker_sha256=sha256_hex(checker_bytes),
            spec_sha256=sha256_hex(canonical_json(request.spec.model_dump(mode="json"))),
            stdout_ref=blobs.put(b""),
            stderr_ref=blobs.put(b""),
            sample_count=len(json.loads(output)),
        )


if __name__ == "__main__":  # pragma: no cover - exercised through backend APIs
    if sys.argv[1:] != ["--worker"]:
        raise SystemExit("simulation.py is an internal worker; expected --worker")
    raise SystemExit(_worker_main())
