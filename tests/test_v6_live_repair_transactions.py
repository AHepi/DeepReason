"""End-to-end qualification for separately authorized v6 schema repair."""

from __future__ import annotations

import json

import pytest

from deepreason.application.models import derive_model_execution_summary
from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.endpoints import EndpointError
from deepreason.llm.firewall import leases_from_manifest, select_lease
from deepreason.ontology import (
    Commitment,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
)
from deepreason.rules.conj import conj
from deepreason.rules.crit import _v6_transactional_batch_call, crit_argumentative_batch
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    CriticismPolicyV1,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    ScratchAuthoringPolicyV1,
    compile_run_manifest,
    write_run_manifest,
)
from deepreason.workflow.models import WorkflowTaskKind
from deepreason.workflow.transaction import WorkBudgetDenied
from tests.test_v6_compact_recovery_transition import _bind_classification


STAMP = "2026-07-17T00:00:00Z"


def _route(endpoint_id: str, seat: int = 0) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": f"offline-model-{seat}",
        "provider": "mock",
        "family": f"offline-family-{seat}",
        "max_tokens": 64,
        "context_window_tokens": 16_384,
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
    _bind_classification(harness, manifest)
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
        transaction_authority_required=True,
    )
    adapter.bind_v6_authority(harness, manifest)
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
    conjecture_grant = next(
        grant
        for grant in manifest.contract_schema_repair_policy.grants
        if grant.contract_id == "conjecturer.turn.v6"
    )
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
    assert conjecture_grant.maximum_schema_repairs == 2
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
        [
            "{broken",
            "{still-broken",
            *(
                json.dumps(
                    {
                        "candidate": {
                            "content": f"atomic mechanism {index}",
                            "typicality": 0.5,
                            "neighbours": [],
                        }
                    }
                )
                for index in range(6)
            ),
        ],
    )

    artifacts = conj(
        harness,
        "pi-repair",
        adapter,
        _config(),
        run_manifest=manifest,
    )

    assert len(artifacts) == 6
    work = list(harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work[:2]] == [
        WorkflowTaskKind.CONJECTURE,
        WorkflowTaskKind.REPAIR,
    ]
    assert [item.terminal.status for item in work[:2]] == [
        "rejected",
        "schema_exhausted",
    ]
    assert len(work) == 8
    assert all(
        item.preparation.contract_id == "conjecturer.atomic-candidate.v1"
        and item.terminal.status == "completed"
        for item in work[2:]
    )
    compact = tuple(harness.workflow_state.compact_recovery_by_route_seat.values())
    assert len(compact) == 1
    assert work[1].terminal.compact_recovery_transition_ref == compact[0].id
    assert compact[0].work_id == work[1].preparation.id
    assert work[1].preparation.task_payload_value["mode"] == "whole_object_syntax"
    decomposition = harness.workflow_state.contract_decomposition_by_source_work
    assert tuple(decomposition) == (work[1].preparation.id,)
    assert len([event for event in harness.log.read() if event.llm is not None]) == 8


def test_criticism_uses_the_same_separately_authorized_patch_service(tmp_path):
    manifest = _manifest(critics=True)
    criticism_grant = next(
        grant
        for grant in manifest.contract_schema_repair_policy.grants
        if grant.contract_id == "batch-critic.v2"
    )
    harness = Harness(tmp_path / "critic-eventual-valid")
    _bind_classification(harness, manifest)
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
        transaction_authority_required=True,
    )
    adapter.bind_v6_authority(harness, manifest)
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
    assert criticism_grant.maximum_schema_repairs == 2
    assert output.cases[0].target == target.id
    assert output.cases[0].attack is False
    work = list(harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.CRITICISM,
        WorkflowTaskKind.REPAIR,
    ]
    assert [item.terminal.status for item in work] == ["rejected", "completed"]
    assert len({item.authorization.id for item in work}) == 2


def test_public_criticism_decomposes_exhausted_batch_into_exact_targets(tmp_path):
    manifest = _manifest(critics=True)
    harness = Harness(tmp_path / "critic-atomic")
    _bind_classification(harness, manifest)
    targets = [
        harness.create_artifact(
            f"target-{index}",
            provenance=Provenance(role="conjecturer", school="school-0"),
        )
        for index in range(2)
    ]
    route = manifest.roles["argumentative_critic"][1]
    responses = [
        "{broken",
        "{still-broken",
        json.dumps(
            {
                "attack": False,
                "target_alias": "SRC_001",
                "claim": "",
                "grounds": "",
                "cited_input_aliases": [],
                "counterexample": None,
            }
        ),
        json.dumps(
            {
                "attack": False,
                "target_alias": "SRC_001",
                "claim": "",
                "grounds": "",
                "cited_input_aliases": [],
                "counterexample": None,
            }
        ),
    ]
    endpoints = [MockEndpoint([]) for _seat in range(3)]
    endpoints[1] = MockEndpoint(
        responses,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
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
        transaction_authority_required=True,
    )
    adapter.bind_v6_authority(harness, manifest)
    lease = select_lease(adapter.leases, "argumentative_critic", 1)

    critics = crit_argumentative_batch(
        harness,
        [target.id for target in targets],
        adapter,
        _config(critics=True),
        endpoint_lease=lease,
        critic_school_id="school-1",
        critic_school_context={
            "id": "school-1",
            "stance_text": "probe hidden boundary assumptions",
        },
        argumentative_authority="observe_only",
        run_manifest=manifest,
        transaction_assignment_refs=("assignment:school-1",),
    )

    assert critics == []
    work = list(harness.workflow_state.transaction_work.values())
    exhausted = [item for item in work if item.terminal.status == "schema_exhausted"]
    atomic = [
        item
        for item in work
        if item.preparation.contract_id == "critic.atomic-target.v1"
    ]
    assert len(exhausted) == 1
    assert len(atomic) == 2
    assert all(item.terminal.status == "completed" for item in atomic)
    assert [item.preparation.target_refs for item in atomic] == [
        (target.id,) for target in targets
    ]
    transition = harness.workflow_state.contract_decomposition_by_source_work[
        exhausted[0].preparation.id
    ]
    assert all(
        item.preparation.task_payload_value["decomposition_transition_ref"]
        == transition.id
        for item in atomic
    )


def test_atomic_conjecture_restart_recovers_children_without_redispatch(tmp_path):
    manifest = _manifest()
    root = tmp_path / "conjecture-atomic-restart"
    root.mkdir()
    write_run_manifest(manifest, root / "run-manifest.json")
    harness = Harness(root)
    _seed_problem(harness)
    calls = []
    responses = iter(
        [
            "{broken",
            "{still-broken",
            *(
                json.dumps(
                    {
                        "candidate": {
                            "content": f"restart mechanism {index}",
                            "typicality": 0.5,
                            "neighbours": [],
                        }
                    }
                )
                for index in range(6)
            ),
        ]
    )

    def respond(_prompt):
        calls.append(True)
        return next(responses)

    adapter, _endpoint = _conjecture_adapter(harness, manifest, respond)
    original_complete = harness.complete_contract_decomposition

    def crash_before_completion(*_args, **_kwargs):
        raise RuntimeError("crash-before-decomposition-completion")

    harness.complete_contract_decomposition = crash_before_completion
    with pytest.raises(RuntimeError, match="crash-before-decomposition-completion"):
        conj(harness, "pi-repair", adapter, _config(), run_manifest=manifest)
    assert len(calls) == 8
    harness.complete_contract_decomposition = original_complete
    transition = next(
        iter(harness.workflow_state.contract_decomposition_by_source_work.values())
    )
    with pytest.raises(ValueError, match="exact semantic effects"):
        original_complete(
            manifest,
            transition,
            admitted_effect_refs=("sha256:" + "0" * 64,),
        )
    assert (
        harness.workflow_state.contract_decomposition_completion_by_transition
        == {}
    )

    restarted = Harness(root)
    restarted_adapter, _endpoint = _conjecture_adapter(restarted, manifest, respond)
    artifacts = conj(
        restarted,
        "pi-repair",
        restarted_adapter,
        _config(),
        run_manifest=manifest,
    )

    assert len(artifacts) == 6
    assert len(calls) == 8
    assert len(
        restarted.workflow_state.contract_decomposition_completion_by_transition
    ) == 1
    assert len(
        [event for event in restarted.log.read() if event.llm is not None]
    ) == 8
    summary = derive_model_execution_summary(restarted, manifest)
    assert len(summary.contract_decompositions) == 1
    projection = summary.contract_decompositions[0]
    assert projection.source_status == "schema_exhausted"
    assert projection.source_contract_id == "conjecturer.turn.v6"
    assert projection.atomic_contract_id == "conjecturer.atomic-candidate.v1"
    assert len(projection.child_work_ids) == 6
    assert set(projection.admitted_effect_refs) == {item.id for item in artifacts}
    decomposition_checks = {
        item["check"]
        for item in verify_root(root)["violations"]
        if "decomposition" in item["check"]
    }
    assert decomposition_checks == set()


def test_atomic_critic_restart_recovers_children_without_redispatch(tmp_path):
    manifest = _manifest(critics=True)
    root = tmp_path / "critic-atomic-restart"
    root.mkdir()
    write_run_manifest(manifest, root / "run-manifest.json")
    harness = Harness(root)
    _bind_classification(harness, manifest)
    targets = [
        harness.create_artifact(
            f"restart-target-{index}",
            provenance=Provenance(role="conjecturer", school="school-0"),
        )
        for index in range(2)
    ]
    calls = []
    responses = iter(
        [
            "{broken",
            "{still-broken",
            *(
                json.dumps(
                    {
                        "attack": True,
                        "target_alias": "SRC_001",
                        "claim": f"bounded restart criticism {_index}",
                        "grounds": "the target omits one stated boundary",
                        "cited_input_aliases": [],
                        "counterexample": None,
                    }
                )
                for _index in range(2)
            ),
        ]
    )

    def respond(_prompt):
        calls.append(True)
        return next(responses)

    route = manifest.roles["argumentative_critic"][1]
    endpoint = MockEndpoint(
        respond,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    endpoints = [MockEndpoint([]) for _seat in range(3)]
    endpoints[1] = endpoint
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([]), "argumentative_critic": endpoints},
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    adapter.bind_v6_authority(harness, manifest)
    lease = select_lease(adapter.leases, "argumentative_critic", 1)
    original_complete = harness.complete_contract_decomposition
    harness.complete_contract_decomposition = (
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("crash-before-decomposition-completion")
        )
    )
    kwargs = dict(
        endpoint_lease=lease,
        critic_school_id="school-1",
        critic_school_context={
            "id": "school-1",
            "stance_text": "probe hidden boundary assumptions",
        },
        argumentative_authority="observe_only",
        run_manifest=manifest,
        transaction_assignment_refs=("assignment:school-1",),
    )
    with pytest.raises(RuntimeError, match="crash-before-decomposition-completion"):
        crit_argumentative_batch(
            harness,
            [target.id for target in targets],
            adapter,
            _config(critics=True),
            **kwargs,
        )
    assert len(calls) == 4
    scrutiny_before = len(
        [
            event
            for event in harness.log.read()
            if event.rule == Rule.MEASURE
            and event.inputs
            and event.inputs[0] == "scrutiny"
        ]
    )
    harness.complete_contract_decomposition = original_complete
    transition = next(
        iter(harness.workflow_state.contract_decomposition_by_source_work.values())
    )
    exact_effects = tuple(
        event.inputs[2]
        for event in harness.log.read()
        if event.rule == Rule.MEASURE
        and len(event.inputs) == 3
        and event.inputs[:2]
        == ["contract-decomposition-effect", transition.id]
    )
    assert len(exact_effects) == 2
    unrelated = harness.create_artifact(
        "unrelated later artifact",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    with pytest.raises(ValueError, match="exact chronological effect markers"):
        original_complete(
            manifest,
            transition,
            admitted_effect_refs=(*exact_effects, unrelated.id),
        )

    restarted = Harness(root)
    restarted_endpoint = MockEndpoint(
        respond,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    restarted_endpoints = [MockEndpoint([]) for _seat in range(3)]
    restarted_endpoints[1] = restarted_endpoint
    restarted_adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint([]),
            "argumentative_critic": restarted_endpoints,
        },
        restarted.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    restarted_adapter.bind_v6_authority(restarted, manifest)
    restarted_lease = select_lease(
        restarted_adapter.leases, "argumentative_critic", 1
    )
    critics = crit_argumentative_batch(
        restarted,
        [target.id for target in targets],
        restarted_adapter,
        _config(critics=True),
        **{**kwargs, "endpoint_lease": restarted_lease},
    )

    assert len(critics) == 2
    assert len(calls) == 4
    assert len(
        [
            event
            for event in restarted.log.read()
            if event.rule == Rule.MEASURE
            and event.inputs
            and event.inputs[0] == "scrutiny"
        ]
    ) == scrutiny_before
    assert len(
        restarted.workflow_state.contract_decomposition_completion_by_transition
    ) == 1


def test_atomic_child_transport_failure_is_terminalized_and_not_redispatched(
    tmp_path,
):
    manifest = _manifest()
    root = tmp_path / "atomic-transport-terminal"
    root.mkdir()
    write_run_manifest(manifest, root / "run-manifest.json")
    harness = Harness(root)
    _seed_problem(harness)
    calls = []
    responses = iter(["{broken", "{still-broken"])

    def respond(_prompt):
        calls.append(True)
        if len(calls) <= 2:
            return next(responses)
        raise EndpointError("atomic transport unavailable")

    adapter, _endpoint = _conjecture_adapter(harness, manifest, respond)
    with pytest.raises(EndpointError):
        conj(harness, "pi-repair", adapter, _config(), run_manifest=manifest)

    atomic = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.contract_id == "conjecturer.atomic-candidate.v1"
    ]
    assert len(atomic) == 1
    assert atomic[0].terminal is not None
    assert atomic[0].terminal.status == "transport_failed"
    assert atomic[0].provider_attempts[0].outcome == "transport_failure"
    assert len(calls) == 3

    restarted = Harness(root)
    restarted_adapter, _endpoint = _conjecture_adapter(
        restarted, manifest, respond
    )
    with pytest.raises(ValueError, match="terminally failed"):
        conj(
            restarted,
            "pi-repair",
            restarted_adapter,
            _config(),
            run_manifest=manifest,
        )
    assert len(calls) == 3


def test_atomic_conjecture_child_uses_manifest_repair_and_replays(tmp_path):
    manifest = _manifest()
    root = tmp_path / "atomic-child-repair"
    root.mkdir()
    write_run_manifest(manifest, root / "run-manifest.json")
    harness = Harness(root)
    _seed_problem(harness)
    responses = [
        "{broken",
        "{still-broken",
        json.dumps(
            {
                "candidate": {
                    "content": "repaired atomic mechanism",
                    "typicality": 2.0,
                    "neighbours": [],
                }
            }
        ),
        json.dumps(
            {
                "schema": "repair.patch.v1",
                "op": "replace",
                "path": "/candidate/typicality",
                "value": 0.5,
            }
        ),
        *(
            json.dumps(
                {
                    "candidate": {
                        "content": f"atomic peer {index}",
                        "typicality": 0.5,
                        "neighbours": [],
                    }
                }
            )
            for index in range(5)
        ),
    ]
    adapter, _endpoint = _conjecture_adapter(harness, manifest, responses)

    artifacts = conj(
        harness,
        "pi-repair",
        adapter,
        _config(),
        run_manifest=manifest,
    )

    assert len(artifacts) == 6
    repairs = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.REPAIR
        and item.preparation.contract_id == "conjecturer.atomic-candidate.v1"
    ]
    assert len(repairs) == 1
    assert repairs[0].terminal.status == "completed"
    assert Harness(root).workflow_state.digest == harness.workflow_state.digest
