"""Manifest-bound foreign-school criticism policy and pure planning."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    CriticismPolicyV1,
    RunManifestError,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    compile_run_manifest,
)
from deepreason.workflow.criticism import (
    ForeignCriticismTargetV1,
    plan_foreign_criticism,
)


STAMP = "2026-07-16T00:00:00Z"


def _route(
    endpoint_id: str,
    *,
    model: str | None = None,
    family: str = "critic-family",
) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"https://{endpoint_id}.invalid/v1",
        "model": model or endpoint_id,
        "provider": "fixture",
        "family": family,
        "api_key_env": "FIXTURE_API_KEY",
    }


def _control(mode: str = "active_conjecture") -> ControlPlanePolicyV1:
    active = mode == "active_conjecture"
    controlled = mode != "legacy"
    return ControlPlanePolicyV1(
        controller_version=(
            "workflow.controller.v1" if controlled else "legacy.scheduler.v1"
        ),
        mode=mode,
        workflow_profile={
            "legacy": "legacy.scheduler.v1",
            "shadow": "conjecture.shadow.v1",
            "active_conjecture": "conjecture.active.v1",
        }[mode],
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="harness_plus_model_request" if active else "disabled",
            initial_max_blocks=4 if active else 0,
            initial_max_guides=1 if active else 0,
            max_context_expansion_requests=1 if active else 0,
            max_extra_blocks=2 if active else 0,
            permitted_retrieval_channels=("focus",) if active else (),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract=(
                "bridge.ledger.v2" if active else "bridge.ledger.v1"
            ),
            conjecturer_turn_contract=(
                "conjecturer.turn.v4" if active else "conjecturer.legacy.v1"
            ),
            control_event_schema="control.event.v1" if controlled else "none",
        ),
        capability_profile="conjecture-control.v1" if controlled else "legacy.v1",
    )


def _binding(school: int, seat: int, endpoint_id: str) -> SchoolRoleBindingV1:
    return SchoolRoleBindingV1(
        school_id=f"school-{school}",
        role="argumentative_critic",
        seat=seat,
        endpoint_id=endpoint_id,
    )


def _policy(
    bindings: tuple[SchoolRoleBindingV1, ...],
    *,
    coverage: int = 1,
    batch: int = 2,
    authority: str = "observe_only",
    allow_shared: bool = True,
) -> CriticismPolicyV1:
    return CriticismPolicyV1(
        minimum_foreign_school_coverage=coverage,
        bindings=bindings,
        max_batch_size=batch,
        target_eligibility="accepted_school_artifacts",
        authority=authority,
        allow_shared=allow_shared,
    )


def _manifest(
    *,
    critic_routes: list[dict],
    bindings: tuple[SchoolRoleBindingV1, ...],
    schools: int = 3,
    coverage: int = 1,
    batch: int = 2,
    authority: str = "observe_only",
    allow_shared: bool = True,
    extra_roles: dict[str, object] | None = None,
    control_mode: str = "active_conjecture",
):
    roles: dict[str, object] = {
        "conjecturer": _route("conjecturer"),
        "argumentative_critic": critic_routes,
    }
    roles.update(extra_roles or {})
    return compile_run_manifest(
        Config(N_SCHOOLS=schools, roles=roles),
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(control_mode),
        criticism_policy=_policy(
            bindings,
            coverage=coverage,
            batch=batch,
            authority=authority,
            allow_shared=allow_shared,
        ),
    )


def test_absent_policy_preserves_existing_v4_canonical_shape_and_round_trip():
    manifest = compile_run_manifest(
        Config(N_SCHOOLS=0, roles={"conjecturer": _route("conjecturer")}),
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
    )
    payload = json.loads(manifest.canonical_bytes())

    assert "criticism_policy" not in payload
    assert "criticism_policy" not in manifest.model_dump(mode="json")
    assert manifest.canonical_bytes() == manifest.model_validate_json(
        manifest.canonical_bytes()
    ).canonical_bytes()


def test_criticism_policy_is_v4_active_only():
    policy = _policy((_binding(0, 0, "critic"), _binding(1, 0, "critic")))
    with pytest.raises(RunManifestError, match="CRITICISM_MANIFEST_V4_REQUIRED"):
        compile_run_manifest(
            Config(N_SCHOOLS=2, roles={"argumentative_critic": _route("critic")}),
            schema_version=3,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
            criticism_policy=policy,
        )
    with pytest.raises(RunManifestError, match="ACTIVE_CONJECTURE_REQUIRED"):
        _manifest(
            critic_routes=[_route("critic")],
            bindings=policy.bindings,
            schools=2,
            control_mode="shadow",
        )


@pytest.mark.parametrize(
    ("bindings", "coverage", "message"),
    (
        ((_binding(0, 0, "critic-a"),), 1, "BINDING_INCOMPLETE"),
        (
            (
                _binding(0, 0, "critic-a"),
                SchoolRoleBindingV1(
                    school_id="school-1",
                    role="conjecturer",
                    seat=0,
                    endpoint_id="critic-a",
                ),
            ),
            1,
            "ROLE_UNSUPPORTED",
        ),
        (
            (_binding(0, 0, "critic-a"), _binding(1, 1, "missing")),
            1,
            "SEAT_OUT_OF_RANGE",
        ),
        (
            (_binding(0, 0, "critic-a"), _binding(1, 0, "critic-a")),
            2,
            "COVERAGE_IMPOSSIBLE",
        ),
    ),
)
def test_policy_rejects_incomplete_or_impossible_topology(bindings, coverage, message):
    with pytest.raises(ValidationError, match=message):
        _manifest(
            critic_routes=[_route("critic-a")],
            bindings=bindings,
            schools=2,
            coverage=coverage,
        )


def test_shared_critic_seat_requires_explicit_permission():
    bindings = (
        _binding(0, 0, "critic"),
        _binding(1, 0, "critic"),
    )
    with pytest.raises(ValidationError, match="SHARED_SEAT_FORBIDDEN"):
        _manifest(
            critic_routes=[_route("critic")],
            bindings=bindings,
            schools=2,
            allow_shared=False,
        )
    assert _manifest(
        critic_routes=[_route("critic")],
        bindings=bindings,
        schools=2,
        allow_shared=True,
    ).criticism_policy.allow_shared


def test_defended_trial_requires_defender_and_cross_family_judges():
    critic_routes = [_route("critic")]
    bindings = (_binding(0, 0, "critic"), _binding(1, 0, "critic"))
    with pytest.raises(ValidationError, match="DEFENDER_REQUIRED"):
        _manifest(
            critic_routes=critic_routes,
            bindings=bindings,
            schools=2,
            authority="defended_trial",
        )
    with pytest.raises(ValidationError, match="CROSS_FAMILY_JUDGES_REQUIRED"):
        _manifest(
            critic_routes=critic_routes,
            bindings=bindings,
            schools=2,
            authority="defended_trial",
            extra_roles={
                "defender": _route("defender"),
                "judge": [_route("judge-a"), _route("judge-b")],
            },
        )
    manifest = _manifest(
        critic_routes=critic_routes,
        bindings=bindings,
        schools=2,
        authority="defended_trial",
        extra_roles={
            "defender": _route("defender"),
            "judge": [
                _route("judge-a", family="family-a"),
                _route("judge-b", family="family-b"),
            ],
        },
    )
    assert manifest.criticism_policy.authority == "defended_trial"


def test_planner_gives_each_target_distinct_foreign_school_coverage():
    manifest = _manifest(
        critic_routes=[_route("critic-a"), _route("critic-b"), _route("critic-c")],
        bindings=(
            _binding(0, 0, "critic-a"),
            _binding(1, 1, "critic-b"),
            _binding(2, 2, "critic-c"),
        ),
        coverage=2,
        allow_shared=False,
    )
    plan = plan_foreign_criticism(
        manifest,
        (
            ForeignCriticismTargetV1(target_id="target-b", owner_school_id="school-1"),
            ForeignCriticismTargetV1(target_id="target-a", owner_school_id="school-0"),
        ),
    )

    assert [target.target_id for target in plan.targets] == ["target-a", "target-b"]
    for target in plan.targets:
        critics = {assignment.critic_school_id for assignment in target.assignments}
        assert target.owner_school_id not in critics
        assert target.foreign_school_coverage == len(critics) == 2


def test_shared_models_count_school_coverage_without_claiming_route_diversity():
    manifest = _manifest(
        critic_routes=[
            _route("critic-a", model="shared-model"),
            _route("critic-b", model="shared-model"),
        ],
        bindings=(
            _binding(0, 0, "critic-a"),
            _binding(1, 1, "critic-b"),
            _binding(2, 0, "critic-a"),
        ),
        coverage=2,
        allow_shared=True,
    )
    target = plan_foreign_criticism(
        manifest,
        (ForeignCriticismTargetV1(target_id="target", owner_school_id="school-0"),),
    ).targets[0]

    assert target.foreign_school_coverage == 2
    assert target.distinct_route_coverage == 2
    assert target.distinct_model_coverage == 1
    assert target.route_diverse is False


def test_planner_resumes_partial_coverage_without_repeating_a_completed_school():
    manifest = _manifest(
        critic_routes=[_route("critic-a"), _route("critic-b"), _route("critic-c")],
        bindings=(
            _binding(0, 0, "critic-a"),
            _binding(1, 1, "critic-b"),
            _binding(2, 2, "critic-c"),
        ),
        coverage=2,
    )
    partial = ForeignCriticismTargetV1(
        target_id="target",
        owner_school_id="school-0",
        completed_critic_school_ids=("school-1",),
    )

    resumed = plan_foreign_criticism(manifest, (partial,)).targets[0]

    assert resumed.completed_critic_school_ids == ("school-1",)
    assert [item.critic_school_id for item in resumed.assignments] == ["school-2"]
    assert resumed.foreign_school_coverage == 2
    complete = partial.model_copy(
        update={"completed_critic_school_ids": ("school-1", "school-2")}
    )
    assert plan_foreign_criticism(manifest, (complete,)).batches == ()


def test_planner_batches_deterministically_within_the_manifest_cap():
    manifest = _manifest(
        critic_routes=[_route("critic-a"), _route("critic-b"), _route("critic-c")],
        bindings=(
            _binding(0, 0, "critic-a"),
            _binding(1, 1, "critic-b"),
            _binding(2, 2, "critic-c"),
        ),
        batch=2,
    )
    targets = tuple(
        ForeignCriticismTargetV1(
            target_id=f"target-{index}", owner_school_id="school-0"
        )
        for index in range(5)
    )

    forward = plan_foreign_criticism(manifest, targets)
    reverse = plan_foreign_criticism(manifest, tuple(reversed(targets)))

    assert forward == reverse
    assert all(1 <= len(batch.target_ids) <= 2 for batch in forward.batches)
    assert sum(len(batch.target_ids) for batch in forward.batches) == len(targets)
