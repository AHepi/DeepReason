"""Containment and integration tests for the contained sandboxed-Python runner."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.policy import SimulationCapabilityPolicyV1
from deepreason.scheduler.scheduler import Scheduler
from deepreason.v6_policy import (
    PUBLIC_CONTAINED_TOOLCHAIN_ID,
    PUBLIC_SIMULATION_TOOLCHAIN_ID,
    engaged_simulation_policy,
    engaged_simulation_toolchain,
)
from deepreason.verification.contained import (
    CONTAINED_WORKER_SHA256,
    CONTAINED_WORKER_SOURCE_V1,
    ContainedSimulationBackend,
    _contained_environment,
    _containment_limits,
)
from deepreason.verification.simulation import SimulationRequest
from deepreason.workloads.code import SimulationSpec

from tests.test_simulation_capability_v5 import (
    _adapter,
    _initial_conjecture,
    _prepare_run,
    _simulation_policy,
    _simulation_proposal,
    _simulation_turn,
    _toolchain,
    _verify_v5_component_root,
)

CONTAINMENT_AVAILABLE = ContainedSimulationBackend.containment_available()
needs_containment = pytest.mark.skipif(
    not CONTAINMENT_AVAILABLE,
    reason="host cannot create an unshared network namespace",
)

SANDBOXED_SOURCE = (
    "def simulate(inputs, rng):\n"
    "    base = inputs['parameters'].get('base', 2)\n"
    "    jitter = rng.randint(0, 0)\n"
    "    return {'value': base ** 5 + jitter, 'root': math.sqrt(base)}\n"
)
TRIVIAL_CHECKER = (
    "def check(input_item, seed, output):\n"
    "    return {'pass': True, 'metrics': {'declared_observables': len(output)}}\n"
)


class _Blobs(dict):
    def put(self, data: bytes) -> str:
        ref = hashlib.sha256(data).hexdigest()
        self[ref] = data
        return ref

    def get(self, ref: str) -> bytes:
        return self[ref]


def _request(
    blobs: _Blobs,
    *,
    source: str = SANDBOXED_SOURCE,
    step_limit: int = 100_000,
    toolchain_id: str = "python@contained-test",
) -> SimulationRequest:
    inputs = json.dumps(
        [{"parameter_set": "default", "parameters": {"base": 3}, "sealed_inputs": {}}]
    ).encode("utf-8")
    spec = SimulationSpec(
        entry="simulate",
        seed_set=(7,),
        inputs_ref=blobs.put(inputs),
        observables=("value", "root"),
        checker_ref=blobs.put(TRIVIAL_CHECKER.encode("utf-8")),
        deterministic_step_limit=step_limit,
        sample_limit=8,
        toolchain_id=toolchain_id,
    )
    return SimulationRequest(
        source_ref=blobs.put(source.encode("utf-8")),
        spec=spec,
        maximum_output_bytes=65_536,
    )


def _backend(**updates) -> ContainedSimulationBackend:
    values = {
        "toolchain_id": "python@contained-test",
        "maximum_wall_ms": 20_000,
        "maximum_memory_bytes": 512 * 1024 * 1024,
    }
    values.update(updates)
    return ContainedSimulationBackend(**values)


def test_worker_identity_is_frozen_and_fingerprinted():
    assert CONTAINED_WORKER_SHA256 == hashlib.sha256(
        CONTAINED_WORKER_SOURCE_V1.encode("utf-8")
    ).hexdigest()
    fingerprint = _backend().fingerprint()
    assert fingerprint["backend"] == "simulation-python-contained"
    assert fingerprint["worker_sha256"] == CONTAINED_WORKER_SHA256


def test_worker_environment_is_a_fixed_allowlist(monkeypatch):
    monkeypatch.setenv("DEEPREASON_RESEARCH_ALLOWLIST", "example.com")
    monkeypatch.setenv("OLLAMA_API_KEY", "secret-that-must-not-leak")
    environment = _contained_environment("/scratch/example")
    assert set(environment) == {
        "HOME",
        "LC_ALL",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONHASHSEED",
        "PYTHONNOUSERSITE",
        "TMPDIR",
    }
    assert environment["HOME"] == "/scratch/example"
    assert environment["TMPDIR"] == "/scratch/example"
    assert not any("DEEPREASON" in key or "KEY" in key for key in environment)


def test_containment_limits_cover_every_resource_class():
    """The declared numbers, pinned on the pure function that produces them.

    `ContainedSimulationBackend.resource_limits()` reads its five limit values
    straight out of `_containment_limits()`, so comparing the two puts the same
    function on both sides of the equals sign — an equality that holds whether
    or not one `setrlimit` ever reaches a child. Its `"filesystem"`, `"network"`
    and `"network_denial"` entries are dict literals
    (`src/deepreason/verification/contained.py:519-521`), which hold whether or
    not the containment works. Neither shape can fail for the reason it exists,
    so those properties are measured by EFFECT in
    `tests/test_sandbox_guard.py`:
    `test_the_contained_child_really_receives_every_declared_rlimit` reads the
    limits back out of a real child,
    `test_the_contained_backend_prefix_actually_denies_network` runs the probe
    inside and outside the prefix, and
    `test_the_contained_scratch_directory_is_the_cwd_and_does_not_survive` pins
    what is observably true of the scratch directory. See
    `docs/map/SUB-verification.md`, the self-report Trap.
    """

    limits = _containment_limits(
        maximum_wall_ms=20_000, maximum_memory_bytes=512 * 1024 * 1024
    )
    assert limits == {
        "cpu_seconds": 20,
        "memory_bytes": 512 * 1024 * 1024,
        "fsize_bytes": 8 * 1024 * 1024,
        "nofile": 64,
        "nproc": 2_048,
    }


def test_missing_network_namespace_fails_closed(monkeypatch):
    monkeypatch.setattr(ContainedSimulationBackend, "_containment_prefix", ())
    blobs = _Blobs()
    result = _backend().verify(_request(blobs), blobs)
    assert result.verdict == "overrun"
    assert result.trace["sandbox_abort"] == "network containment unavailable"
    assert blobs.get(result.output_ref) == b"[]"


def test_unappliable_resource_limits_fail_closed(monkeypatch):
    if not CONTAINMENT_AVAILABLE:
        monkeypatch.setattr(
            ContainedSimulationBackend,
            "_containment_prefix",
            ("/usr/bin/env", "--"),
        )

    def refuse(_limits):
        raise OSError("rlimit refused")

    monkeypatch.setattr(
        "deepreason.verification.contained._apply_containment_limits", refuse
    )
    blobs = _Blobs()
    result = _backend().verify(_request(blobs), blobs)
    assert result.verdict == "overrun"
    assert result.trace["sandbox_abort"] in {
        "containment could not be established",
        "worker terminated by resource containment",
    }


def test_toolchain_mismatch_is_refused_without_execution():
    blobs = _Blobs()
    result = _backend(toolchain_id="python@other").verify(_request(blobs), blobs)
    assert result.verdict == "overrun"
    assert result.trace["unavailable_toolchain"] == "python@contained-test"


@needs_containment
def test_sandboxed_python_executes_inside_the_containment_envelope(monkeypatch):
    captured = {}
    import tempfile

    real_mkdtemp = tempfile.mkdtemp

    def observing_mkdtemp(*args, **kwargs):
        captured["scratch"] = real_mkdtemp(*args, **kwargs)
        return captured["scratch"]

    monkeypatch.setattr(
        "deepreason.verification.contained.tempfile.mkdtemp", observing_mkdtemp
    )
    blobs = _Blobs()
    result = _backend().verify(_request(blobs), blobs)
    assert result.verdict == "pass"
    records = json.loads(blobs.get(result.output_ref))
    assert records[0]["observables"] == {"root": 3 ** 0.5, "value": 243}
    assert records[0]["passed"] is True
    assert result.sample_count == 1
    assert result.fingerprint["worker_sha256"] == CONTAINED_WORKER_SHA256
    # The scratch working directory is disposable: nothing survives the run.
    assert "scratch" in captured
    assert not Path(captured["scratch"]).exists()


@needs_containment
def test_runaway_sandboxed_python_hits_the_deterministic_step_budget():
    blobs = _Blobs()
    runaway = (
        "def simulate(inputs, rng):\n"
        "    total = 0\n"
        "    while True:\n"
        "        total = total + 1\n"
        "    return {'value': total, 'root': 1.0}\n"
    )
    result = _backend().verify(
        _request(blobs, source=runaway, step_limit=50_000), blobs
    )
    assert result.verdict == "fail"
    assert result.trace["error"] == "deterministic step limit exceeded"


@needs_containment
def test_memory_hungry_sandboxed_python_is_contained():
    blobs = _Blobs()
    hungry = (
        "def simulate(inputs, rng):\n"
        "    data = list(range(100_000_000))\n"
        "    return {'value': len(data), 'root': 1.0}\n"
    )
    result = _backend(maximum_memory_bytes=128 * 1024 * 1024).verify(
        _request(blobs, source=hungry, step_limit=200_000_000), blobs
    )
    assert result.verdict == "overrun"
    assert result.trace["sandbox_abort"] == "resource containment"


def test_policy_pairs_container_profile_with_contained_backend():
    with pytest.raises(ValueError, match="must pair"):
        _simulation_policy(runner_profile="simulation.container.v1")
    with pytest.raises(ValueError, match="must pair"):
        SimulationCapabilityPolicyV1(backend_identity="simulation-python-contained")
    paired = _simulation_policy(
        runner_profile="simulation.container.v1",
        backend_identity="simulation-python-contained",
    )
    assert paired.backend_identity == "simulation-python-contained"


def test_engaged_preset_default_is_the_contained_runner():
    """The default INVERTED on 2026-08-28 (execution-safety tranche).

    It was `declarative`, which refused every `sandboxed_python_v1` proposal,
    so model-authored code execution was off for any run nobody had configured
    — four live epochs' worth (commit `74d9f71ca`). The operator authorized the
    switch conditional on a safety verdict; the verdict is at
    `experiments/2026-08-27-change-execution-safety/SAFETY.md`.

    Both spellings of the default agree, so an explicit `contained` is not a
    different subject from an unset variable.
    """

    policy = engaged_simulation_policy({})
    assert policy.runner_profile == "simulation.container.v1"
    assert policy.backend_identity == "simulation-python-contained"
    assert policy.python_toolchain_identity == PUBLIC_CONTAINED_TOOLCHAIN_ID
    assert (
        engaged_simulation_policy({"DEEPREASON_SIMULATION_RUNNER": "contained"})
        == policy
    )
    toolchain = engaged_simulation_toolchain({})
    assert toolchain.runner == "container"
    assert toolchain.id == PUBLIC_CONTAINED_TOOLCHAIN_ID


def test_engaged_preset_declarative_choice_switches_subject():
    """The declarative profile survives as a NAMED choice, not a deletion.

    It is the right configuration for a host that cannot create namespaces and
    for a run that wants numeric models rather than programs. Naming it is a
    different compiled policy, hence a different qualification subject —
    exactly as the contained opt-in used to be, with the roles swapped.
    """

    environ = {"DEEPREASON_SIMULATION_RUNNER": "declarative"}
    policy = engaged_simulation_policy(environ)
    assert policy.runner_profile == "simulation.declarative.v1"
    assert policy.backend_identity == "simulation-python"
    assert policy.python_toolchain_identity == PUBLIC_SIMULATION_TOOLCHAIN_ID
    assert policy.digest != engaged_simulation_policy({}).digest
    toolchain = engaged_simulation_toolchain(environ)
    assert toolchain.runner == "local"
    assert toolchain.id == PUBLIC_SIMULATION_TOOLCHAIN_ID
    assert Path(toolchain.executable) == Path(sys.executable).resolve()


def test_an_unrecognised_runner_no_longer_refuses_at_compile():
    """It used to raise ValueError. That is a compile-time refusal of an
    otherwise-parseable configuration, which the all-configurations law
    abolished (operator, 2026-08-12: "All configurations should be allowed").
    It now resolves to the default and is DISCLOSED — see
    `tests/test_simulation_runner_default.py` for the notice itself."""

    policy = engaged_simulation_policy({"DEEPREASON_SIMULATION_RUNNER": "docker"})
    assert policy == engaged_simulation_policy({})


def _contained_component_run(tmp_path, **policy_updates):
    policy = _simulation_policy(
        runner_profile="simulation.container.v1",
        backend_identity="simulation-python-contained",
        maximum_generated_code_bytes=65_536,
        maximum_steps=200_000,
        **policy_updates,
    )
    return _prepare_run(
        tmp_path,
        policy=policy,
        toolchain=_toolchain(runner="container"),
    )


@needs_containment
def test_controller_executes_sandboxed_python_and_replay_validates(tmp_path):
    config, manifest, harness = _contained_component_run(tmp_path / "contained")
    proposal = _simulation_proposal(
        simulation_mode="sandboxed_python_v1",
        model_source=(
            "def simulate(inputs, rng):\n"
            "    weight = inputs['parameters']['weight_bytes']\n"
            "    return {'x': weight ** 2 / 2}\n"
        ),
    )
    prompts = []
    adapter, _pending = _adapter(
        manifest,
        harness,
        [
            _simulation_turn(proposal),
            {
                "abstention": {
                    "search_signal": "stuck",
                    "note": "The contained execution result is recorded.",
                }
            },
        ],
        prompts,
    )
    _initial_conjecture(harness, manifest, config, adapter)
    scheduler = Scheduler(
        harness, adapter, config, workload_profile="text", run_manifest=manifest
    )
    scheduler.step()

    lifecycles = {
        item.lifecycle for item in harness.capability_state.transitions.values()
    }
    assert CapabilityLifecycle.SUCCEEDED in lifecycles
    receipt = next(iter(harness.capability_state.receipts.values()))
    assert receipt.operational_status == "succeeded"
    attempt = receipt.attempts[-1]
    assert attempt.fingerprint["backend"] == "simulation-python-contained"
    assert attempt.fingerprint["worker_sha256"] == CONTAINED_WORKER_SHA256
    # CARRIAGE, not containment: `invariants.py`'s capability-receipt check
    # fails the replay when this field is anything but False, so the receipt
    # must keep carrying it. Whether it is TRUE is measured by effect in
    # tests/test_sandbox_guard.py::
    # test_the_contained_backend_prefix_actually_denies_network.
    assert receipt.resource_limits["network"] is False
    records = json.loads(harness.blobs.get(attempt.output_ref))
    assert records[0]["observables"] == {"x": 72.0}
    work_order = next(iter(harness.capability_state.work_orders.values()))
    assert work_order.runner_profile == "simulation.container.v1"
    # The compiled source is byte-identical to the validated semantic program.
    compiled = next(iter(harness.capability_state.compiled.values()))
    proposal_record = harness.capability_state.proposals[compiled.proposal_ref]
    assert harness.blobs.get(compiled.source_ref) == (
        proposal_record.model_source.encode("utf-8")
    )
    assert _verify_v5_component_root(harness.root, manifest)["violations"] == []


def test_contained_runner_unavailable_host_denies_typed(tmp_path, monkeypatch):
    monkeypatch.setattr(ContainedSimulationBackend, "_containment_prefix", ())
    config, manifest, harness = _contained_component_run(tmp_path / "no-netns")
    proposal = _simulation_proposal(
        simulation_mode="sandboxed_python_v1",
        model_source="def simulate(inputs, rng):\n    return {'x': 1}\n",
    )
    prompts = []
    adapter, _pending = _adapter(manifest, harness, [_simulation_turn(proposal)], prompts)
    _initial_conjecture(harness, manifest, config, adapter)
    Scheduler(
        harness, adapter, config, workload_profile="text", run_manifest=manifest
    ).step()

    transition = harness.capability_state.transitions[
        next(iter(harness.capability_state.current_transition_by_request.values()))
    ]
    assert transition.lifecycle == CapabilityLifecycle.DENIED
    assert transition.reason_code == "runner_unavailable"
    assert harness.capability_state.execution_count == 0
    assert _verify_v5_component_root(harness.root, manifest)["violations"] == []


def test_declarative_policy_still_refuses_sandboxed_python(tmp_path):
    config, manifest, harness = _prepare_run(tmp_path / "declarative-refusal")
    proposal = _simulation_proposal(
        simulation_mode="sandboxed_python_v1",
        model_source="def simulate(inputs, rng):\n    return {'x': 1}\n",
    )
    prompts = []
    adapter, _pending = _adapter(manifest, harness, [_simulation_turn(proposal)], prompts)
    _initial_conjecture(harness, manifest, config, adapter)
    Scheduler(
        harness, adapter, config, workload_profile="text", run_manifest=manifest
    ).step()

    transition = harness.capability_state.transitions[
        next(iter(harness.capability_state.current_transition_by_request.values()))
    ]
    assert transition.lifecycle == CapabilityLifecycle.DENIED
    assert transition.reason_code == "runner_profile_mismatch"
    assert _verify_v5_component_root(harness.root, manifest)["violations"] == []
