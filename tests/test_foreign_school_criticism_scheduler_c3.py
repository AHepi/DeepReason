"""C3 scheduler enactment of manifest-bound foreign-school criticism."""

from __future__ import annotations

import json

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import (
    SchoolRouteResolutionError,
    leases_from_manifest,
)
from deepreason.ontology import Problem, ProblemProvenance, Status
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    CriticismPolicyV1,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler


STAMP = "2026-07-16T00:00:00Z"


def _route(endpoint_id: str, seat: int) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": f"critic-model-{seat}",
        "provider": "mock",
        "family": f"critic-family-{seat}",
        "max_tokens": 256,
    }


def _config() -> Config:
    return Config(
        N_SCHOOLS=3,
        VS_K=1,
        FLOOR=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        FUZZ_N=0,
        RECRIT_STANDING=False,
        NEAR_DUP_EPS=None,
        model_profile="standard",
        roles={
            "conjecturer": [
                {
                    "endpoint_id": "conjecturer-route",
                    "endpoint": "mock://conjecturer-route",
                    "model": "conjecturer-model",
                    "provider": "mock",
                    "family": "conjecturer-family",
                    "max_tokens": 256,
                }
            ],
            "argumentative_critic": [
                _route(f"critic-route-{seat}", seat) for seat in range(3)
            ],
        },
    )


def _control() -> ControlPlanePolicyV1:
    return ControlPlanePolicyV1(
        controller_version="workflow.controller.v1",
        mode="active_conjecture",
        workflow_profile="conjecture.active.v1",
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
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v2",
            conjecturer_turn_contract="conjecturer.turn.v4",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )


def _criticism() -> CriticismPolicyV1:
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


def _manifest(config: Config):
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        criticism_policy=_criticism(),
    )


def _seed(harness: Harness) -> None:
    harness.register_problem(
        Problem(
            id="pi-foreign-criticism",
            description="generate school-owned candidates for foreign review",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def _adapter(manifest, harness, critic_calls, critic_prompts):
    candidates = iter(
        json.dumps(
            {
                "candidates": [
                    {
                        "content": f"school mechanism {index}",
                        "typicality": 0.5,
                    }
                ]
            }
        )
        for index in range(3)
    )
    conjecturer_route = manifest.roles["conjecturer"][0]
    critic_endpoints = []
    for seat, route in enumerate(manifest.roles["argumentative_critic"]):
        def respond(prompt: str, *, critic_seat=seat) -> str:
            critic_calls[critic_seat] += 1
            critic_prompts[critic_seat].append(prompt)
            return json.dumps({"attack": False, "case": ""})

        critic_endpoints.append(
            MockEndpoint(
                respond,
                name=route.base_url,
                model=route.model_id,
                max_tokens=route.max_tokens,
            )
        )
    return LLMAdapter(
        {
            "conjecturer": MockEndpoint(
                lambda _prompt: next(candidates),
                name=conjecturer_route.base_url,
                model=conjecturer_route.model_id,
                max_tokens=conjecturer_route.max_tokens,
            ),
            "argumentative_critic": critic_endpoints,
        },
        harness.blobs,
        retry_max=0,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )


def test_scheduler_records_complete_distinct_foreign_school_coverage(tmp_path):
    config = _config()
    manifest = _manifest(config)
    harness = Harness(tmp_path / "run")
    bind_run_manifest(manifest, harness.root)
    _seed(harness)
    critic_calls = [0, 0, 0]
    critic_prompts = [[], [], []]
    adapter = _adapter(manifest, harness, critic_calls, critic_prompts)

    Scheduler(harness, adapter, config, run_manifest=manifest).run(1)

    targets = {
        artifact.id: artifact.provenance.school
        for artifact in harness.state.artifacts.values()
        if artifact.provenance is not None
        and artifact.provenance.role == "conjecturer"
    }
    assert len(targets) == 3
    coverage = {}
    for event in harness.log.read():
        if event.inputs[:1] != ["foreign-criticism-coverage.v1"]:
            continue
        coverage.setdefault(event.inputs[1], set()).add(
            event.inputs[3].removeprefix("critic:")
        )
        source_seq = int(event.inputs[4].removeprefix("source:"))
        source = next(item for item in harness.log.read() if item.seq == source_seq)
        assert source.seq < event.seq
        assert source.llm.school_route.school_id in coverage[event.inputs[1]]
    assert set(coverage) == set(targets)
    assert all(len(schools) == 2 for schools in coverage.values())
    assert all(targets[target_id] not in schools for target_id, schools in coverage.items())
    assert sum(critic_calls) == 6
    for seat, prompts in enumerate(critic_prompts):
        assert all(f"school: school-{seat}" in prompt for prompt in prompts)
        assert all("semantic stance only" in prompt for prompt in prompts)
    assert all(harness.state.status[target_id] == Status.ACCEPTED for target_id in targets)
    assert verify_root(harness.root)["violations"] == []


def test_batch_route_failure_is_detected_before_any_critic_dispatch(
    tmp_path,
    monkeypatch,
):
    config = _config()
    manifest = _manifest(config)
    harness = Harness(tmp_path / "run")
    bind_run_manifest(manifest, harness.root)
    _seed(harness)
    critic_calls = [0, 0, 0]
    critic_prompts = [[], [], []]
    adapter = _adapter(manifest, harness, critic_calls, critic_prompts)
    scheduler = Scheduler(harness, adapter, config, run_manifest=manifest)
    original = __import__(
        "deepreason.scheduler.scheduler", fromlist=["resolve_school_role_lease"]
    ).resolve_school_role_lease
    resolutions = 0

    def fail_second(*args, **kwargs):
        nonlocal resolutions
        resolutions += 1
        if resolutions == 2:
            raise SchoolRouteResolutionError(
                "INJECTED_CRITIC_BINDING_FAILURE",
                "second critic binding failed",
            )
        return original(*args, **kwargs)

    monkeypatch.setattr(
        "deepreason.scheduler.scheduler.resolve_school_role_lease",
        fail_second,
    )
    # Seed one canonical accepted school artifact without spending Conj.
    harness.create_artifact(
        "school-owned target",
        provenance={"role": "conjecturer", "school": "school-0"},
    )

    with pytest.raises(
        SchoolRouteResolutionError,
        match="INJECTED_CRITIC_BINDING_FAILURE",
    ):
        scheduler._foreign_arg_crit()

    assert critic_calls == [0, 0, 0]
    assert not any(
        event.llm is not None and event.llm.role == "argumentative_critic"
        for event in harness.log.read()
    )
