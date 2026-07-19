"""End-to-end qualification for separately authorized v6 schema repair."""

from __future__ import annotations

import json

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, select_lease
from deepreason.llm.repair import SchemaExhaustedError
from deepreason.ontology import (
    Commitment,
    Problem,
    ProblemProvenance,
    Provenance,
)
from deepreason.rules.conj import conj
from deepreason.rules.crit import _v6_transactional_batch_call
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    CriticismPolicyV1,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    ScratchAuthoringPolicyV1,
    compile_run_manifest,
)
from deepreason.workflow.models import WorkflowTaskKind
from deepreason.workflow.transaction import WorkBudgetDenied


STAMP = "2026-07-17T00:00:00Z"


def _route(endpoint_id: str, seat: int = 0) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": f"offline-model-{seat}",
        "provider": "mock",
        "family": f"offline-family-{seat}",
        "max_tokens": 64,
    }


def _config(*, critics: bool = False) -> Config:
    roles = {"conjecturer": [_route("conjecturer-route")]}
    if critics:
        roles["argumentative_critic"] = [_route(f"critic-route-{seat}", seat) for seat in range(3)]
    return Config(N_SCHOOLS=3 if critics else 0, roles=roles)


def _control() -> ControlPlanePolicyV3:
    return ControlPlanePolicyV3(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="disabled",
            initial_max_blocks=0,
            initial_max_guides=0,
            max_context_expansion_requests=0,
            max_extra_blocks=0,
            permitted_retrieval_channels=(),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(),
        scratch_authoring=ScratchAuthoringPolicyV1(),
    )


def _criticism_policy() -> CriticismPolicyV1:
    return CriticismPolicyV1(
        minimum_foreign_school_coverage=2,
        bindings=tuple(
            SchoolRoleBindingV1(
                school_id=f"school-{seat}",
                role="argumentative_critic",
                seat=seat,
                endpoint_id=f"critic-route-{seat}",
            )
            for seat in range(3)
        ),
        max_batch_size=4,
        target_eligibility="accepted_school_artifacts",
        authority="observe_only",
        allow_shared=False,
    )


def _manifest(*, critics: bool = False):
    return compile_run_manifest(
        _config(critics=critics),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        criticism_policy=_criticism_policy() if critics else None,
        run_input_digest="f" * 64,
    )


def _seed_problem(harness: Harness) -> None:
    harness.register_commitment(Commitment(id="k-repair", eval="predicate:len(content) > 0"))
    harness.register_problem(
        Problem(
            id="pi-repair",
            description="Invent one provisional mechanism.",
            criteria=["k-repair"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def _conjecture_adapter(harness, manifest, responses, *, meter=None):
    route = manifest.roles["conjecturer"][0]
    endpoint = MockEndpoint(
        responses,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=0,
        meter=meter or TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    return adapter, endpoint


def _invalid_candidate() -> str:
    return json.dumps({"candidates": [{"content": "preserve this mechanism", "typicality": 2.0}]})


def _typicality_patch() -> str:
    return json.dumps(
        {
            "schema": "repair.patch.v1",
            "op": "replace",
            "path": "/candidates/0/typicality",
            "value": 0.5,
        }
    )


def test_conjecture_patch_is_a_distinct_authorized_work_item(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "eventual-valid")
    _seed_problem(harness)
    adapter, _endpoint = _conjecture_adapter(
        harness,
        manifest,
        [_invalid_candidate(), _typicality_patch()],
    )

    artifacts = conj(
        harness,
        "pi-repair",
        adapter,
        _config(),
        run_manifest=manifest,
    )

    assert len(artifacts) == 1
    assert artifacts[0].content_ref == "inline:preserve this mechanism"
    work = list(harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.CONJECTURE,
        WorkflowTaskKind.REPAIR,
    ]
    assert [item.terminal.status for item in work] == ["rejected", "completed"]
    assert len({item.preparation.id for item in work}) == 2
    assert len({item.reservation.id for item in work}) == 2
    assert len({item.authorization.id for item in work}) == 2
    assert work[1].preparation.contract_id == work[0].preparation.contract_id
    assert work[1].preparation.route_lease == work[0].preparation.route_lease
    assert work[1].preparation.task_payload_value["mode"] == "patch"
    calls = [event.llm for event in harness.log.read() if event.llm is not None]
    assert len(calls) == 2
    assert {call.work_order_id for call in calls} == {item.preparation.id for item in work}


def test_unrelated_patch_is_rejected_without_changing_valid_claim_text(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "scope-rejected")
    _seed_problem(harness)
    unrelated = json.dumps(
        {
            "schema": "repair.patch.v1",
            "op": "replace",
            "path": "/candidates/0/content",
            "value": "laundered replacement",
        }
    )
    adapter, _endpoint = _conjecture_adapter(
        harness,
        manifest,
        [_invalid_candidate(), unrelated, _typicality_patch()],
    )

    artifacts = conj(
        harness,
        "pi-repair",
        adapter,
        _config(),
        run_manifest=manifest,
    )

    assert artifacts[0].content_ref == "inline:preserve this mechanism"
    work = list(harness.workflow_state.transaction_work.values())
    assert [item.terminal.status for item in work] == [
        "rejected",
        "rejected",
        "completed",
    ]
    assert work[1].admissions[1].outcome == "rejected"
    assert work[1].admissions[1].authorized_pointers == ("/candidates/0/typicality",)


def test_repair_budget_denial_has_no_repair_exposure_or_dispatch(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "repair-budget-denied")
    _seed_problem(harness)
    meter = TokenMeter()
    calls = []
    adapter = None

    def respond(_prompt: str) -> str:
        calls.append(True)
        assert adapter is not None
        adapter.meter.budget = 1
        return _invalid_candidate()

    adapter, _endpoint = _conjecture_adapter(
        harness,
        manifest,
        respond,
        meter=meter,
    )
    with pytest.raises(WorkBudgetDenied):
        conj(
            harness,
            "pi-repair",
            adapter,
            _config(),
            run_manifest=manifest,
        )

    assert calls == [True]
    work = list(harness.workflow_state.transaction_work.values())
    assert [item.terminal.status for item in work] == [
        "rejected",
        "budget_denied",
    ]
    assert work[1].preparation.task_kind == WorkflowTaskKind.REPAIR
    assert not work[1].issued
    assert work[1].exposure is None
    assert work[1].authorization is None
    assert len([event for event in harness.log.read() if event.llm is not None]) == 1


def test_unparseable_retry_exhausts_as_typed_schema_failure(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "syntax-exhausted")
    _seed_problem(harness)
    adapter, _endpoint = _conjecture_adapter(
        harness,
        manifest,
        ["{broken", "{still-broken"],
    )

    with pytest.raises(SchemaExhaustedError) as caught:
        conj(
            harness,
            "pi-repair",
            adapter,
            _config(),
            run_manifest=manifest,
        )

    assert caught.value.code == "schema_exhausted"
    assert caught.value.transaction_terminalized
    assert caught.value.spend is None
    work = list(harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.CONJECTURE,
        WorkflowTaskKind.REPAIR,
    ]
    assert [item.terminal.status for item in work] == [
        "rejected",
        "schema_exhausted",
    ]
    assert work[1].preparation.task_payload_value["mode"] == "whole_object_syntax"
    assert len([event for event in harness.log.read() if event.llm is not None]) == 2


def test_criticism_uses_the_same_separately_authorized_patch_service(tmp_path):
    manifest = _manifest(critics=True)
    harness = Harness(tmp_path / "critic-eventual-valid")
    target = harness.create_artifact(
        "target",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    route = manifest.roles["argumentative_critic"][1]
    responses = [
        json.dumps(
            {
                "cases": [
                    {
                        "target_alias": "SRC_001",
                        "attack": "not-a-boolean",
                        "case": "",
                        "counterexample": None,
                    }
                ]
            }
        ),
        json.dumps(
            {
                "schema": "repair.patch.v1",
                "op": "replace",
                "path": "/cases/0/attack",
                "value": False,
            }
        ),
    ]
    endpoint = MockEndpoint(
        responses,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    endpoints = [MockEndpoint([]) for _seat in range(3)]
    endpoints[1] = endpoint
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint([]),
            "argumentative_critic": endpoints,
        },
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    lease = select_lease(adapter.leases, "argumentative_critic", 1)

    output, _call = _v6_transactional_batch_call(
        harness,
        adapter,
        manifest,
        endpoint_lease=lease,
        critic_school_id="school-1",
        target_ids=(target.id,),
        assignment_refs=("assignment:school-1",),
        coverage_attempt_index=0,
        phase="primary",
        caller_trigger_ref=None,
        pack_factory=lambda: "SRC_001: target",
    )

    assert len(output.cases) == 1
    assert output.cases[0].target == target.id
    assert output.cases[0].attack is False
    work = list(harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.CRITICISM,
        WorkflowTaskKind.REPAIR,
    ]
    assert [item.terminal.status for item in work] == ["rejected", "completed"]
    assert len({item.authorization.id for item in work}) == 2
