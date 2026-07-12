"""Pinned-seed simulation checks are deterministic and model-scoped."""

from __future__ import annotations

import json
import sys

from deepreason.storage.blobs import BlobStore
from deepreason.verification.registry import VerifierRegistry
from deepreason.verification.simulation import (
    SimulationBackend,
    SimulationRequest,
)
from deepreason.workloads.code import SimulationSpec


def _request(tmp_path, source: str, checker: str, *, seeds=(0, 7), inputs=(1, 5)):
    blobs = BlobStore(tmp_path / "blobs")
    source_ref = blobs.put(source.encode())
    inputs_ref = blobs.put(json.dumps(list(inputs)).encode())
    checker_ref = blobs.put(checker.encode())
    spec = SimulationSpec(
        entry="simulate",
        seed_set=seeds,
        inputs_ref=inputs_ref,
        observables=("value",),
        checker_ref=checker_ref,
        deterministic_step_limit=10_000,
        sample_limit=20,
        toolchain_id=f"python@{sys.version_info.major}.{sys.version_info.minor}",
    )
    return blobs, SimulationRequest(source_ref=source_ref, spec=spec)


def test_fixed_seed_replay_is_byte_stable(tmp_path):
    source = "def simulate(item, rng):\n    return {'value': item + rng.randint(0, 100)}\n"
    checker = "def check(item, seed, output):\n    return output['value'] >= item\n"
    blobs, request = _request(tmp_path, source, checker)
    backend = SimulationBackend()

    first = backend.verify(request, blobs)
    second = backend.verify(request, blobs)

    assert first.verdict == "pass"
    assert first.output_ref == second.output_ref
    assert first.diagnostics_ref == second.diagnostics_ref
    assert first.trace == second.trace
    assert first.sample_count == 4
    assert blobs.get(first.output_ref) == blobs.get(second.output_ref)


def test_checker_rejection_is_about_the_declared_model(tmp_path):
    source = "def simulate(item, rng):\n    return {'value': item - 1}\n"
    checker = "def check(item, seed, output):\n    return output['value'] >= item\n"
    blobs, request = _request(tmp_path, source, checker, seeds=(0,), inputs=(3,))

    result = SimulationBackend().verify(request, blobs)

    assert result.verdict == "fail"
    assert result.trace["error"] == "checker rejected simulation output"
    # A separate relevance claim can change independently; it cannot rewrite
    # the immutable, content-addressed simulation result.
    original_ref = result.output_ref
    relation = {"model_result": result.output_ref, "relevant_to_world": False}
    relation["relevant_to_world"] = True
    assert result.output_ref == original_ref


def test_ambient_imports_and_filesystem_are_unavailable(tmp_path):
    source = "import os\ndef simulate(item, rng):\n    return {'value': os.getenv('X')}\n"
    checker = "def check(item, seed, output):\n    return True\n"
    blobs, request = _request(tmp_path, source, checker, seeds=(0,), inputs=(1,))

    result = SimulationBackend().verify(request, blobs)

    assert result.verdict == "fail"
    assert "imports are not allowed" in result.trace["error"]


def test_deterministic_step_limit_stops_infinite_model(tmp_path):
    source = (
        "def simulate(item, rng):\n"
        "    while True:\n"
        "        item = item + 1\n"
        "    return {'value': item}\n"
    )
    checker = "def check(item, seed, output):\n    return True\n"
    blobs, request = _request(tmp_path, source, checker, seeds=(0,), inputs=(1,))

    result = SimulationBackend().verify(request, blobs)

    assert result.verdict == "fail"
    assert "step limit" in result.trace["error"]


def test_sample_limit_is_finite_and_overrun_has_no_fail_warrant(tmp_path):
    source = "def simulate(item, rng):\n    return {'value': item}\n"
    checker = "def check(item, seed, output):\n    return True\n"
    blobs, request = _request(tmp_path, source, checker, seeds=(0, 1), inputs=tuple(range(11)))

    result = SimulationBackend().verify(request, blobs)

    assert result.verdict == "overrun"
    assert result.trace["sample_limit"] == 20


def test_registry_resolves_backend_by_trusted_name(tmp_path):
    source = "def simulate(item, rng):\n    return {'value': item}\n"
    checker = "def check(item, seed, output):\n    return True\n"
    blobs, request = _request(tmp_path, source, checker, seeds=(0,), inputs=(1,))
    registry = VerifierRegistry((SimulationBackend(),))

    result = registry.verify("simulation-python", request, blobs)

    assert registry.names() == ("simulation-python",)
    assert result.verdict == "pass"
