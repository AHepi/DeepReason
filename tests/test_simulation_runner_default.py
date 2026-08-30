"""The switched-on default: model-authored Python executes without a code edit.

Operator, 2026-08-27: "model authored code execution switched off. I need to
know if it's safe to switch on. Same with simulation. If so switch both on."
The switch was conditional on a safety verdict; the verdict is at
``experiments/2026-08-27-change-execution-safety/SAFETY.md`` (NOT PROVEN on
2026-08-27, SAFE on 2026-08-28 after the attribute-boundary escape was closed).

What this file pins, requirement by requirement:

* **R4** the enabled state is reachable with NO code edit and NO environment
  variable — it is the default; the declarative profile survives as a named
  configuration choice; the toolchain always pairs with the profile; an
  unrecognised value COMPILES and is disclosed rather than refused.
* **R5** a ``sandboxed_python_v1`` proposal is accepted, dispatched and
  EXECUTED end to end on the enabled configuration, under the R2 containment.
"""

from __future__ import annotations

import pytest

from deepreason.config import Config
from deepreason.v6_policy import (
    DEFAULT_SIMULATION_RUNNER,
    PUBLIC_CONTAINED_TOOLCHAIN_ID,
    PUBLIC_SIMULATION_TOOLCHAIN_ID,
    SIMULATION_RUNNERS,
    engaged_simulation_policy,
    engaged_simulation_toolchain,
    simulation_runner_notices,
)
from deepreason.verification.contained import ContainedSimulationBackend

needs_containment = pytest.mark.skipif(
    not ContainedSimulationBackend.containment_available(),
    reason="host cannot create an unshared network namespace",
)


# --- R4: on by default, as configuration ------------------------------------ #


def test_model_authored_python_is_the_default_with_no_environment_at_all():
    """The whole point. An empty environment gets the runner that EXECUTES
    model-authored Python — no code edit, no variable to remember.

    Regression (execution-safety tranche): the default was `declarative`, under
    which `SimulationCapabilityController` denied every `sandboxed_python_v1`
    proposal with terminal reason `runner_profile_mismatch`. Four live epochs
    were read as model reluctance before the record said otherwise.
    """

    assert DEFAULT_SIMULATION_RUNNER == "contained"
    policy = engaged_simulation_policy({})
    assert policy.enabled is True
    assert policy.runner_profile == "simulation.container.v1"
    assert policy.backend_identity == "simulation-python-contained"
    assert policy.python_toolchain_identity == PUBLIC_CONTAINED_TOOLCHAIN_ID
    assert policy.maximum_simulation_executions > 0
    assert policy.maximum_generated_code_bytes > 0


def test_the_declarative_profile_survives_as_a_named_choice():
    """Kept, not deleted: it is the right shape for a host without namespaces,
    and for a run that wants numeric models rather than programs."""

    policy = engaged_simulation_policy({"DEEPREASON_SIMULATION_RUNNER": "declarative"})
    assert policy.enabled is True
    assert policy.runner_profile == "simulation.declarative.v1"
    assert policy.backend_identity == "simulation-python"
    assert policy.python_toolchain_identity == PUBLIC_SIMULATION_TOOLCHAIN_ID


def test_the_toolchain_always_pairs_with_the_runner_profile():
    """No configuration may carry a toolchain its runner cannot dispatch to —
    the shape commit 74d9f71ca reported. Checked on BOTH branches, because a
    pairing that holds on one is not a pairing."""

    for named, profile, toolchain_id, runner in (
        ({}, "simulation.container.v1", PUBLIC_CONTAINED_TOOLCHAIN_ID, "container"),
        (
            {"DEEPREASON_SIMULATION_RUNNER": "declarative"},
            "simulation.declarative.v1",
            PUBLIC_SIMULATION_TOOLCHAIN_ID,
            "local",
        ),
    ):
        policy = engaged_simulation_policy(named)
        entry = engaged_simulation_toolchain(named)
        assert policy.runner_profile == profile, named
        assert policy.python_toolchain_identity == toolchain_id, named
        assert entry.id == toolchain_id, named
        assert entry.runner == runner, named
        assert entry.network is False, named


def test_an_unknown_runner_compiles_and_is_disclosed_never_refused():
    """The all-configurations law (operator, 2026-08-12: "All configurations
    should be allowed"). This USED to raise ValueError — a compile-time refusal
    of an otherwise-parseable configuration.

    Silence would be just as wrong as a refusal: it is how an operator believes
    a runner is selected when it is not.
    """

    typo = {"DEEPREASON_SIMULATION_RUNNER": "containd"}
    policy = engaged_simulation_policy(typo)
    assert policy.enabled is True
    assert policy.runner_profile == "simulation.container.v1"

    (notice,) = simulation_runner_notices(typo)
    assert notice.code == "SIMULATION_RUNNER_UNKNOWN"
    assert "containd" in notice.message
    assert all(runner in (notice.resolution or "") for runner in SIMULATION_RUNNERS)


def test_a_well_formed_configuration_on_an_equipped_host_discloses_nothing():
    """Notices must discriminate. A disclosure that fires on every run is noise
    a reader learns to skip, which is the same as no disclosure."""

    if not ContainedSimulationBackend.containment_available():
        pytest.skip("host cannot create an unshared network namespace")
    assert simulation_runner_notices({}) == ()
    assert simulation_runner_notices({"DEEPREASON_SIMULATION_RUNNER": "declarative"}) == ()


def test_an_unequipped_host_compiles_and_discloses_the_severed_road(monkeypatch):
    """The channel is ON and the ROAD is severed — `DR-INV-evidence-channels`'s
    first Trap, reported instead of left for a reader to infer from an empty
    result. It still COMPILES: impossibility surfaces typed at the point of
    use, never at compile."""

    monkeypatch.setattr(
        "deepreason.sandbox_os.network_denial_available", lambda: False
    )
    policy = engaged_simulation_policy({})
    assert policy.enabled is True and policy.runner_profile == "simulation.container.v1"

    codes = [n.code for n in simulation_runner_notices({})]
    assert codes == ["SIMULATION_RUNNER_UNAVAILABLE"]
    (notice,) = simulation_runner_notices({})
    assert "declarative" in (notice.resolution or "")


def test_turning_the_channel_off_still_wins_over_the_runner_default():
    """The channel decides WHETHER; the setting decides WHICH. Off is off, and
    an off channel compiles to the all-zero policy rather than refusing."""

    off = engaged_simulation_policy({}, config=Config(CHANNELS_DISABLED=("simulation",)))
    assert off.enabled is False
    assert off.runner_profile == "simulation.declarative.v1"
    assert simulation_runner_notices(
        {}, config=Config(CHANNELS_DISABLED=("simulation",))
    ) == ()


# --- R5: accepted, dispatched, EXECUTED ------------------------------------- #


@needs_containment
def test_a_sandboxed_python_proposal_executes_on_the_default_configuration():
    """R5 end to end on the configuration a run actually gets.

    Not a fixture standing in for the policy: the policy comes from
    `engaged_simulation_policy({})` — the same call `preparation` makes — and
    the backend is built from that policy's own bounds and toolchain identity.
    If the default reverts to `declarative`, the profile assertion fails before
    a line of the program runs.
    """

    import hashlib
    import json

    from deepreason.verification.simulation import SimulationRequest
    from deepreason.workloads.code import SimulationSpec

    class Blobs(dict):
        def put(self, data: bytes) -> str:
            ref = hashlib.sha256(data).hexdigest()
            self[ref] = data
            return ref

        def get(self, ref: str) -> bytes:
            return self[ref]

    policy = engaged_simulation_policy({})
    assert policy.runner_profile == "simulation.container.v1"

    blobs = Blobs()
    source = (
        "def simulate(inputs, rng):\n"
        "    base = inputs['parameters']['base']\n"
        "    total = 0\n"
        "    for step in range(1, 5):\n"
        "        total = total + step * base\n"
        "    return {'value': total, 'root': math.sqrt(base)}\n"
    )
    checker = (
        "def check(input_item, seed, output):\n"
        "    return {'pass': output['value'] > 0, 'metrics': {'v': output['value']}}\n"
    )
    inputs = json.dumps(
        [{"parameter_set": "default", "parameters": {"base": 4}, "sealed_inputs": {}}]
    ).encode()

    spec = SimulationSpec(
        entry="simulate",
        seed_set=policy.fixed_seed_set,
        inputs_ref=blobs.put(inputs),
        observables=("value", "root"),
        checker_ref=blobs.put(checker.encode()),
        deterministic_step_limit=policy.maximum_steps,
        sample_limit=policy.maximum_samples,
        toolchain_id=policy.python_toolchain_identity,
    )
    backend = ContainedSimulationBackend(
        toolchain_id=policy.python_toolchain_identity,
        maximum_wall_ms=policy.maximum_wall_ms,
        maximum_memory_bytes=policy.maximum_memory_bytes,
    )
    result = backend.verify(
        SimulationRequest(
            source_ref=blobs.put(source.encode()),
            spec=spec,
            maximum_output_bytes=policy.maximum_output_bytes,
        ),
        blobs,
    )

    assert result.verdict == "pass", result.trace
    assert result.backend == "simulation-python-contained"

    records = json.loads(blobs.get(result.output_ref))
    assert records[0]["observables"] == {"value": 40, "root": 2.0}
    assert records[0]["passed"] is True

    # Containment is not assertable from here. `resource_limits()["network"]`,
    # `["network_denial"]` and `fingerprint()["network_denial"]` are dict
    # literals in `contained.py` (:502, :520, :521) that consult neither the
    # probe nor the launch, so they hold whether or not the containment works.
    # That property is measured by effect in tests/test_sandbox_guard.py:
    # test_the_contained_backend_prefix_actually_denies_network and
    # test_the_contained_worker_argv_really_carries_the_probed_prefix.


@needs_containment
def test_the_default_policy_admits_dispatches_and_executes_end_to_end(tmp_path):
    """R5 in its strongest form: the DEFAULT policy, through the real
    controller, to a SUCCEEDED lifecycle and a replay-valid root.

    This is the exact path that was closed. `SimulationCapabilityController`
    derives an expected runner profile from the proposal's mode and denies with
    terminal reason `runner_profile_mismatch` when it differs from the policy's.
    For `sandboxed_python_v1` under the old default those could never agree, so
    a validated proposal died at admission — the lifecycle recorded at commit
    `74d9f71ca` was proposed, validated, DENIED.

    The policy here is `engaged_simulation_policy({})`, the same call
    `preparation.build_preparation_manifest` makes, so a reverted default fails
    this test at admission rather than anywhere downstream.
    """

    import json

    from deepreason.capabilities.enums import CapabilityLifecycle
    from deepreason.scheduler.scheduler import Scheduler

    from tests.test_simulation_capability_v5 import (
        _adapter,
        _initial_conjecture,
        _prepare_run,
        _simulation_proposal,
        _simulation_turn,
        _verify_v5_component_root,
    )

    policy = engaged_simulation_policy({})
    assert policy.runner_profile == "simulation.container.v1", (
        "the default reverted; sandboxed_python_v1 cannot be admitted"
    )

    config, manifest, harness = _prepare_run(
        tmp_path / "default-on",
        policy=policy,
        # The REAL toolchain entry, from the same builder preparation uses --
        # not a test double. That is what makes the pairing part of the proof:
        # policy and toolchain both come from the shipped default.
        toolchain=engaged_simulation_toolchain({}),
    )
    proposal = _simulation_proposal(
        simulation_mode="sandboxed_python_v1",
        model_source=(
            "def simulate(inputs, rng):\n"
            "    weight = inputs['parameters']['weight_bytes']\n"
            "    return {'x': weight * weight / 2}\n"
        ),
    )
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
        [],
    )
    _initial_conjecture(harness, manifest, config, adapter)
    Scheduler(
        harness, adapter, config, workload_profile="text", run_manifest=manifest
    ).step()

    lifecycles = {
        item.lifecycle for item in harness.capability_state.transitions.values()
    }
    assert CapabilityLifecycle.SUCCEEDED in lifecycles, lifecycles
    assert CapabilityLifecycle.DENIED not in lifecycles, lifecycles

    receipt = next(iter(harness.capability_state.receipts.values()))
    assert receipt.operational_status == "succeeded"
    attempt = receipt.attempts[-1]
    assert attempt.fingerprint["backend"] == "simulation-python-contained"
    # CARRIAGE, not containment -- see the same note in
    # tests/test_contained_simulation_runner.py: `invariants.py` fails the
    # replay when this field is anything but False.
    assert receipt.resource_limits["network"] is False

    records = json.loads(harness.blobs.get(attempt.output_ref))
    assert records[0]["observables"] == {"x": 72.0}

    work_order = next(iter(harness.capability_state.work_orders.values()))
    assert work_order.runner_profile == "simulation.container.v1"

    # The record the run wrote replays clean: the typed outcome, not prose.
    assert _verify_v5_component_root(harness.root, manifest)["violations"] == []
