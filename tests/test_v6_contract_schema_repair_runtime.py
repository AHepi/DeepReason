"""Runtime qualification for manifest-owned v6 schema-repair grants."""

from __future__ import annotations

import inspect
import json

import pytest

from deepreason.harness import Harness
from deepreason.llm.budget import TokenMeter
from deepreason.llm.repair import SchemaExhaustedError
from deepreason.rules.conj import conj
from deepreason.run_manifest import (
    RunManifest,
    RunManifestError,
    _compile_route_seat_behavioral_capability_plan,
    compile_run_manifest,
    write_run_manifest,
)
from deepreason.workflow.models import WorkflowTaskKind
from deepreason.workflow.repair_transaction import repair_schema_failure
from deepreason.workflow.transaction_service import InquiryTransactionService
from tests.test_v6_live_repair_transactions import (
    STAMP,
    _config,
    _conjecture_adapter,
    _control,
    _invalid_candidate,
    _seed_problem,
    _typicality_patch,
)


def _manifest(repairs: int) -> RunManifest:
    config = _config()
    config.RETRY_MAX = repairs
    return compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        run_input_digest="f" * 64,
    )


def _without_repair_authority(
    manifest: RunManifest,
    *,
    remove_policy: bool,
) -> RunManifest:
    payload = json.loads(manifest.canonical_bytes())
    if remove_policy:
        payload.pop("contract_schema_repair_policy")
    else:
        policy = payload["contract_schema_repair_policy"]
        policy["grants"] = [
            grant
            for grant in policy["grants"]
            if grant["contract_id"] != "conjecturer.turn.v6"
        ]
    payload.pop("route_seat_behavioral_capability_plan")
    return RunManifest.model_validate(payload)


def _without_decomposition_authority(manifest: RunManifest) -> RunManifest:
    """Retain exact strong authority while freezing zero fallback edges."""

    payload = json.loads(manifest.canonical_bytes())
    payload["route_seat_contract_decomposition_plan"]["entries"] = []
    payload.pop("route_seat_behavioral_capability_plan")
    provisional = RunManifest.model_validate(payload)
    payload["route_seat_behavioral_capability_plan"] = (
        _compile_route_seat_behavioral_capability_plan(provisional).model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        )
    )
    return RunManifest.model_validate(payload)


def _run_invalid_chain(tmp_path, repairs: int):
    manifest = _without_decomposition_authority(_manifest(repairs))
    root = tmp_path / f"ceiling-{repairs}"
    root.mkdir(parents=True, exist_ok=True)
    write_run_manifest(manifest, root / "run-manifest.json")
    harness = Harness(root)
    _seed_problem(harness)
    meter = TokenMeter(100_000)
    unrelated_patch = json.dumps(
        {
            "schema": "repair.patch.v1",
            "op": "replace",
            "path": "/candidates/0/content",
            "value": "not an authorized repair",
        }
    )
    adapter, _endpoint = _conjecture_adapter(
        harness,
        manifest,
        [_invalid_candidate(), *([unrelated_patch] * repairs)],
        meter=meter,
    )

    with pytest.raises(SchemaExhaustedError) as caught:
        conj(harness, "pi-repair", adapter, _config(), run_manifest=manifest)

    return manifest, harness, adapter, caught.value


@pytest.mark.parametrize("repairs", (0, 1, 2))
def test_manifest_grant_is_the_exact_provider_call_ceiling(tmp_path, repairs):
    manifest, harness, adapter, error = _run_invalid_chain(tmp_path, repairs)
    work = tuple(harness.workflow_state.transaction_work.values())
    calls = tuple(event.llm for event in harness.log.read() if event.llm is not None)
    grant = next(
        grant
        for grant in manifest.contract_schema_repair_policy.grants
        if grant.contract_id == "conjecturer.turn.v6"
    )

    assert grant.maximum_schema_repairs == repairs
    assert grant.maximum_provider_calls == repairs + 1
    assert len(work) == len(calls) == adapter.meter.calls == repairs + 1
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.CONJECTURE,
        *([WorkflowTaskKind.REPAIR] * repairs),
    ]
    assert [item.terminal.status for item in work] == [
        *(["rejected"] * repairs),
        "schema_exhausted",
    ]
    assert len({item.preparation.id for item in work}) == repairs + 1
    assert all(
        item.preparation.route_lease == work[0].preparation.route_lease
        for item in work
    )
    assert all(item.provider_attempts for item in work)
    assert adapter.meter.reserved == 0
    assert error.transaction_terminalized is True


def test_valid_first_repair_stops_without_consuming_unused_grant(tmp_path):
    manifest = _manifest(2)
    harness = Harness(tmp_path / "first-repair-valid")
    _seed_problem(harness)
    meter = TokenMeter(100_000)
    adapter, _endpoint = _conjecture_adapter(
        harness,
        manifest,
        [_invalid_candidate(), _typicality_patch(), "must-not-dispatch"],
        meter=meter,
    )

    output = conj(harness, "pi-repair", adapter, _config(), run_manifest=manifest)
    work = tuple(harness.workflow_state.transaction_work.values())

    assert len(output) == 1
    assert meter.calls == 2
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.CONJECTURE,
        WorkflowTaskKind.REPAIR,
    ]
    assert [item.terminal.status for item in work] == ["rejected", "completed"]
    assert meter.reserved == 0


@pytest.mark.parametrize("remove_policy", (True, False))
def test_absent_policy_or_exact_contract_grant_authorizes_zero_repairs(
    tmp_path,
    remove_policy,
):
    manifest = _without_repair_authority(
        _manifest(2),
        remove_policy=remove_policy,
    )
    root = tmp_path / ("policy-absent" if remove_policy else "grant-absent")
    root.mkdir(parents=True, exist_ok=True)
    write_run_manifest(manifest, root / "run-manifest.json")
    harness = Harness(root)
    _seed_problem(harness)
    meter = TokenMeter(100_000)
    with pytest.raises(RunManifestError) as caught:
        _conjecture_adapter(
            harness,
            manifest,
            ["{invalid-json", _typicality_patch()],
            meter=meter,
        )

    assert caught.value.code == "DOCTOR_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED"
    assert tuple(harness.workflow_state.transaction_work.values()) == ()
    assert meter.calls == 0
    assert meter.reserved == 0


def test_repair_helper_has_no_caller_owned_retry_override():
    assert "retry_max" not in inspect.signature(repair_schema_failure).parameters


def test_compact_transition_belongs_only_to_final_exhausted_work(tmp_path):
    _manifest_value, harness, _adapter, _error = _run_invalid_chain(tmp_path, 2)
    work = tuple(harness.workflow_state.transaction_work.values())
    transitions = tuple(harness.workflow_state.compact_recovery_by_route_seat.values())

    assert len(transitions) == 1
    assert transitions[0].work_id == work[-1].preparation.id
    assert work[-1].terminal.compact_recovery_transition_ref == transitions[0].id
    assert all(
        item.terminal.compact_recovery_transition_ref is None
        for item in work[:-1]
    )


def test_replay_of_exhausted_repair_chain_never_redispatches(tmp_path):
    manifest, harness, _adapter, _error = _run_invalid_chain(tmp_path, 1)
    before_events = tuple(harness.log.read())
    before_transition = dict(harness.workflow_state.compact_recovery_by_route_seat)

    reopened = Harness(harness.root)
    replay_meter = TokenMeter(100_000)
    recovered = InquiryTransactionService(reopened, manifest, replay_meter)

    assert recovered.recover_incomplete() == ()
    assert tuple(reopened.log.read()) == before_events
    assert reopened.workflow_state.compact_recovery_by_route_seat == before_transition
    assert replay_meter.calls == 0
    assert replay_meter.reserved == 0
