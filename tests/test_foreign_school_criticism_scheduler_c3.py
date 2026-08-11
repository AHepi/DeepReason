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
from deepreason.workflow.criticism import ForeignCriticismTargetV1, plan_foreign_criticism


STAMP = "2026-07-16T00:00:00Z"


@pytest.fixture
def _below_public_admission(monkeypatch):
    """Keep pre-v6 component coverage below the public V6-only admission.

    Mirrors the committed test_cli_bridge idiom: the raw V6-only loading
    boundary has its own coverage in test_v6_only_manifest_loading; this
    file's subject is the v4 foreign-school criticism scheduler contract.
    """

    from pathlib import Path

    import deepreason.invariants as invariants_module
    from deepreason.run_manifest import RunManifest

    def _load(path, **_kwargs):
        return RunManifest.model_validate_json(Path(path).read_bytes())

    monkeypatch.setattr("deepreason.run_manifest.load_run_manifest", _load)
    monkeypatch.setattr(invariants_module, "load_run_manifest", _load)
    monkeypatch.setattr(
        "deepreason.runtime.launch_policy.require_v6_launch_allowed",
        lambda _subject, *, operation: None,
    )


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


def _shared_route_criticism() -> CriticismPolicyV1:
    """Same three schools as `_criticism()`, but every binding shares ONE
    seat/endpoint -- the control fixture for Step 45's regression test."""

    return CriticismPolicyV1(
        minimum_foreign_school_coverage=2,
        bindings=tuple(
            SchoolRoleBindingV1(
                school_id=f"school-{seat}",
                role="argumentative_critic",
                seat=0,
                endpoint_id="critic-route-0",
            )
            for seat in range(3)
        ),
        max_batch_size=4,
        target_eligibility="accepted_school_artifacts",
        authority="observe_only",
        allow_shared=True,
    )


def _manifest_with_criticism(config: Config, criticism_policy: CriticismPolicyV1):
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        criticism_policy=criticism_policy,
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


def test_scheduler_records_complete_distinct_foreign_school_coverage(
    tmp_path, _below_public_admission
):
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


def test_distinct_school_models_do_not_change_foreign_coverage_count():
    """Step 45 (S2d, C6, Amendment 11/R27 -- school-seat conjecture/criticism
    route diversity): `plan_foreign_criticism` selects and counts foreign
    schools by SCHOOL ID SET ARITHMETIC alone (`foreign_schools = sorted(
    set(bindings) - {owner})`, `coverage = len(covered_schools)`,
    criticism.py:357-366,406) -- binding schools to distinct provider models
    must not move that selection or count. Route/model diversity is real
    and tracked, but in the SEPARATE `distinct_route_coverage`/
    `distinct_model_coverage`/`route_diverse` fields, never in
    `foreign_school_coverage` or which schools are picked. This is the
    map's pinned invariant (`docs/map/SEAM-manifest-x-schools.md`); this
    test is its regression coverage."""

    config = _config()
    # `_criticism()` already binds all three schools to three DISTINCT
    # routes/models (seats 0-2, `critic-route-{0,1,2}`); `_shared_route_
    # criticism()` binds the identical three schools to ONE shared route.
    # Same school-id topology, only route/model diversity differs.
    shared_manifest = _manifest_with_criticism(config, _shared_route_criticism())
    distinct_manifest = _manifest_with_criticism(config, _criticism())

    targets = tuple(
        ForeignCriticismTargetV1(target_id=f"target-{i}", owner_school_id=f"school-{i}")
        for i in range(3)
    )

    shared_plan = plan_foreign_criticism(shared_manifest, targets)
    distinct_plan = plan_foreign_criticism(distinct_manifest, targets)

    shared_by_target = {plan.target_id: plan for plan in shared_plan.targets}
    distinct_by_target = {plan.target_id: plan for plan in distinct_plan.targets}
    assert set(shared_by_target) == set(distinct_by_target) == {t.target_id for t in targets}

    for target_id in shared_by_target:
        shared_plan_entry = shared_by_target[target_id]
        distinct_plan_entry = distinct_by_target[target_id]

        # Inert (Consequence-A, must stay this way): which schools count as
        # foreign coverage, and how many, is identical whether or not their
        # routes/models diverge.
        assert (
            shared_plan_entry.foreign_school_coverage
            == distinct_plan_entry.foreign_school_coverage
            == 2
        )
        assert {
            assignment.critic_school_id for assignment in shared_plan_entry.assignments
        } == {
            assignment.critic_school_id for assignment in distinct_plan_entry.assignments
        }

        # NOT inert (the documented, expected side effect -- not a
        # regression): route/model diversity is correctly tracked in its
        # own separate fields.
        assert shared_plan_entry.distinct_route_coverage == 1
        assert shared_plan_entry.distinct_model_coverage == 1
        assert shared_plan_entry.route_diverse is False
        assert (
            distinct_plan_entry.distinct_route_coverage
            == distinct_plan_entry.foreign_school_coverage
        )
        assert (
            distinct_plan_entry.distinct_model_coverage
            == distinct_plan_entry.foreign_school_coverage
        )
        assert distinct_plan_entry.route_diverse is True
