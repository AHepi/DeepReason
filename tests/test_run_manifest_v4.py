"""RunManifest v4 control-plane policy and historical compatibility contract."""

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
    RunManifest,
    RunManifestError,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    compile_run_manifest,
)


STAMP = "2026-07-16T00:00:00Z"


def _route(
    endpoint_id: str = "shared-endpoint",
    *,
    model: str = "shared-model",
    family: str = "family-a",
    endpoint: str = "https://models.invalid/v1",
) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": endpoint,
        "model": model,
        "provider": "fixture",
        "family": family,
        "api_key_env": "FIXTURE_API_KEY",
    }


def _historical_config() -> Config:
    return Config(roles={"conjecturer": _route()})


def _school_execution(
    *,
    mode: str = "conditioning_only",
    bindings: tuple[SchoolRoleBindingV1, ...] = (),
    allow_shared: bool = True,
    require_distinct_models: bool = False,
    require_distinct_families: bool = False,
) -> SchoolExecutionPolicyV1:
    return SchoolExecutionPolicyV1(
        mode=mode,
        bindings=bindings,
        allow_shared=allow_shared,
        require_distinct_models=require_distinct_models,
        require_distinct_families=require_distinct_families,
    )


def _control_policy(
    school_execution: SchoolExecutionPolicyV1 | None = None,
    *,
    mode: str = "active_conjecture",
    workflow_profile: str | None = None,
) -> ControlPlanePolicyV1:
    profile = workflow_profile or {
        "legacy": "legacy.scheduler.v1",
        "shadow": "conjecture.shadow.v1",
        "active_conjecture": "conjecture.active.v1",
    }[mode]
    active = mode == "active_conjecture"
    controlled = mode != "legacy"
    return ControlPlanePolicyV1(
        controller_version=(
            "workflow.controller.v1" if mode != "legacy" else "legacy.scheduler.v1"
        ),
        mode=mode,
        workflow_profile=profile,
        school_execution=school_execution or _school_execution(),
        conjecture_context=ConjectureContextPolicyV1(
            mode="harness_plus_model_request" if active else "disabled",
            initial_max_blocks=8 if active else 0,
            initial_max_guides=2 if active else 0,
            max_context_expansion_requests=1 if active else 0,
            max_extra_blocks=4 if active else 0,
            permitted_retrieval_channels=(
                ("focus", "exploratory", "coverage") if active else ()
            ),
            coverage_slot_mandatory=active,
            exploration_slot_mandatory=active,
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


def _compile_v4(
    config: Config,
    policy: ControlPlanePolicyV1,
) -> RunManifest:
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=policy,
    )


def _binding(
    school: int,
    seat: int,
    endpoint_id: str,
) -> SchoolRoleBindingV1:
    return SchoolRoleBindingV1(
        school_id=f"school-{school}",
        role="conjecturer",
        seat=seat,
        endpoint_id=endpoint_id,
    )


@pytest.mark.parametrize(
    ("schema_version", "workload_profile", "expected_hash", "expected_fields"),
    (
        (
            1,
            None,
            "a1ced1bbadaf85b28d6b280a8448d28c63aef875b2e8462275d2585ca9dce1f8",
            {
                "schema_version",
                "engine_profile",
                "model_profile",
                "roles",
                "rubric_policy",
                "provider_fallback",
                "concurrency",
                "pack_profile",
                "output_profile",
                "source_config_hash",
                "compiled_at",
                "engine_config_json",
            },
        ),
        (
            2,
            "text",
            "e352cba40c7059e93829a5952acb89000629ff4cbdfad64c912456b20bb0337b",
            {
                "schema_version",
                "engine_profile",
                "model_profile",
                "workload_profile",
                "roles",
                "rubric_policy",
                "provider_fallback",
                "concurrency",
                "pack_profile",
                "output_profile",
                "toolchains",
                "budget_policy",
                "stop_policy",
                "memory_policy",
                "source_config_hash",
                "compiled_at",
                "engine_config_json",
            },
        ),
        (
            3,
            "text",
            "2616fd5ee11ea405a5d803d731a370235e36a915379ab1fdd4fea13195e656ae",
            {
                "schema_version",
                "engine_profile",
                "model_profile",
                "workload_profile",
                "roles",
                "rubric_policy",
                "provider_fallback",
                "concurrency",
                "pack_profile",
                "output_profile",
                "toolchains",
                "budget_policy",
                "stop_policy",
                "memory_policy",
                "scratch_policy",
                "bridge_policy",
                "source_config_hash",
                "compiled_at",
                "engine_config_json",
            },
        ),
    ),
)
def test_v1_v2_v3_canonical_shapes_and_hashes_remain_byte_identical(
    schema_version: int,
    workload_profile: str | None,
    expected_hash: str,
    expected_fields: set[str],
):
    manifest = compile_run_manifest(
        _historical_config(),
        schema_version=schema_version,
        workload_profile=workload_profile,
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    payload = json.loads(manifest.canonical_bytes())

    assert manifest.sha256 == expected_hash
    assert set(payload) == expected_fields
    assert "control_plane_policy" not in payload


@pytest.mark.parametrize("schema_version", (1, 2, 3))
def test_historical_manifests_reject_v4_control_policy_fields(schema_version: int):
    manifest = compile_run_manifest(
        _historical_config(),
        schema_version=schema_version,
        workload_profile="text" if schema_version >= 2 else None,
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    payload = manifest.model_dump(mode="json")
    payload["control_plane_policy"] = _control_policy().model_dump(
        mode="json", by_alias=True
    )

    with pytest.raises(ValidationError, match="v1/v2/v3|v4 control|control_plane"):
        RunManifest.model_validate(payload)


def test_v4_requires_one_complete_control_policy():
    with pytest.raises(
        (RunManifestError, ValidationError),
        match="CONTROL_PLANE_POLICY_REQUIRED|requires control_plane_policy",
    ):
        compile_run_manifest(
            _historical_config(),
            schema_version=4,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
        )


def test_v4_round_trips_canonically_and_freezes_complete_policy():
    manifest = _compile_v4(_historical_config(), _control_policy())
    reopened = RunManifest.model_validate_json(manifest.canonical_bytes())
    payload = json.loads(manifest.canonical_bytes())

    assert reopened == manifest
    assert reopened.canonical_bytes() == manifest.canonical_bytes()
    assert reopened.sha256 == manifest.sha256
    assert payload["control_plane_policy"] == manifest.control_plane_policy.model_dump(
        mode="json", by_alias=True
    )
    assert payload["control_plane_policy"]["contract_versions"] == {
        "bridge_ledger_wire_contract": "bridge.ledger.v2",
        "conjecturer_turn_contract": "conjecturer.turn.v4",
        "control_event_schema": "control.event.v1",
    }
    assert payload["control_plane_policy"]["workflow_retry"]["schema"] == (
        "bridge.workflow-retry-policy.v1"
    )
    assert (
        manifest.bridge_policy.workflow_policy(
            ledger_contract_version="v2"
        ).ledger_contract_version
        == "v2"
    )


def test_school_binding_and_workflow_profile_changes_change_manifest_digest():
    config = Config(
        N_SCHOOLS=2,
        roles={
            "conjecturer": [
                _route("route-a", model="model-a", endpoint="https://a.invalid/v1"),
                _route("route-b", model="model-b", endpoint="https://b.invalid/v1"),
            ]
        },
    )
    original_execution = _school_execution(
        mode="route_bound",
        bindings=(_binding(0, 0, "route-a"), _binding(1, 1, "route-b")),
        allow_shared=False,
    )
    swapped_execution = _school_execution(
        mode="route_bound",
        bindings=(_binding(0, 1, "route-b"), _binding(1, 0, "route-a")),
        allow_shared=False,
    )
    original = _compile_v4(config, _control_policy(original_execution))
    swapped = _compile_v4(config, _control_policy(swapped_execution))
    shadow = _compile_v4(
        config,
        _control_policy(original_execution, mode="shadow"),
    )

    assert swapped.sha256 != original.sha256
    assert shadow.control_plane_policy.workflow_profile == "conjecture.shadow.v1"
    assert shadow.sha256 != original.sha256


def test_conditioning_only_keeps_many_schools_on_one_shared_route():
    manifest = _compile_v4(
        Config(N_SCHOOLS=4, roles={"conjecturer": _route()}),
        _control_policy(
            _school_execution(
                mode="conditioning_only",
                allow_shared=True,
                require_distinct_models=False,
                require_distinct_families=False,
            )
        ),
    )

    policy = manifest.control_plane_policy.school_execution
    assert policy.mode == "conditioning_only"
    assert policy.bindings == ()
    assert policy.allow_shared is True
    assert len(manifest.roles["conjecturer"]) == 1
    assert json.loads(manifest.engine_config_json)["N_SCHOOLS"] == 4


def test_route_bound_fails_closed_when_one_school_binding_is_missing():
    config = Config(
        N_SCHOOLS=2,
        roles={
            "conjecturer": [
                _route("route-a", endpoint="https://a.invalid/v1"),
                _route("route-b", endpoint="https://b.invalid/v1"),
            ]
        },
    )
    policy = _control_policy(
        _school_execution(
            mode="route_bound",
            bindings=(_binding(0, 0, "route-a"),),
            allow_shared=True,
        )
    )

    with pytest.raises(
        (RunManifestError, ValidationError),
        match="V4_SCHOOL_BINDING_INCOMPLETE|missing.*binding|every configured school",
    ):
        _compile_v4(config, policy)


def test_route_bound_fails_closed_on_out_of_range_seat():
    config = Config(
        N_SCHOOLS=2,
        roles={"conjecturer": _route("route-a")},
    )
    policy = _control_policy(
        _school_execution(
            mode="route_bound",
            bindings=(
                _binding(0, 0, "route-a"),
                _binding(1, 1, "does-not-exist"),
            ),
            allow_shared=True,
        )
    )

    with pytest.raises(
        (RunManifestError, ValidationError),
        match="V4_SCHOOL_SEAT_OUT_OF_RANGE|seat.*out of range|does not exist",
    ):
        _compile_v4(config, policy)


@pytest.mark.parametrize(
    ("bindings", "allow_shared", "message"),
    (
        (
            (
                _binding(0, 0, "route-a"),
                _binding(2, 1, "route-b"),
            ),
            True,
            "V4_SCHOOL_UNKNOWN",
        ),
        (
            (
                _binding(0, 0, "route-a"),
                SchoolRoleBindingV1(
                    school_id="school-1",
                    role="unregistered_role",
                    seat=0,
                    endpoint_id="route-a",
                ),
            ),
            True,
            "V4_SCHOOL_ROLE_UNKNOWN",
        ),
        (
            (
                _binding(0, 0, "wrong-endpoint"),
                _binding(1, 1, "route-b"),
            ),
            True,
            "V4_SCHOOL_ENDPOINT_MISMATCH",
        ),
        (
            (
                _binding(0, 0, "route-a"),
                _binding(0, 1, "route-b"),
                _binding(1, 1, "route-b"),
            ),
            True,
            "V4_SCHOOL_BINDING_DUPLICATE",
        ),
        (
            (
                _binding(0, 0, "route-a"),
                _binding(1, 0, "route-a"),
            ),
            False,
            "V4_SCHOOL_SHARED_SEAT_FORBIDDEN",
        ),
    ),
)
def test_route_bound_rejects_invalid_binding_topology(
    bindings: tuple[SchoolRoleBindingV1, ...],
    allow_shared: bool,
    message: str,
):
    config = Config(
        N_SCHOOLS=2,
        roles={
            "conjecturer": [
                _route("route-a", endpoint="https://a.invalid/v1"),
                _route("route-b", endpoint="https://b.invalid/v1"),
            ]
        },
    )
    policy = _control_policy(
        _school_execution(
            mode="route_bound",
            bindings=bindings,
            allow_shared=allow_shared,
        )
    )

    with pytest.raises((RunManifestError, ValidationError), match=message):
        _compile_v4(config, policy)


@pytest.mark.parametrize(
    (
        "routes",
        "require_distinct_models",
        "require_distinct_families",
    ),
    (
        (
            (
                _route(
                    "route-a", model="model-a", family="family-a",
                    endpoint="https://a.invalid/v1",
                ),
                _route(
                    "route-b", model="model-b", family="family-a",
                    endpoint="https://b.invalid/v1",
                ),
            ),
            True,
            False,
        ),
        (
            (
                _route(
                    "route-a", model="same-model", family="family-a",
                    endpoint="https://a.invalid/v1",
                ),
                _route(
                    "route-b", model="same-model", family="family-b",
                    endpoint="https://b.invalid/v1",
                ),
            ),
            False,
            True,
        ),
    ),
)
def test_route_bound_model_and_family_diversity_can_be_required_independently(
    routes: tuple[dict, dict],
    require_distinct_models: bool,
    require_distinct_families: bool,
):
    policy = _control_policy(
        _school_execution(
            mode="route_bound",
            bindings=(_binding(0, 0, "route-a"), _binding(1, 1, "route-b")),
            allow_shared=False,
            require_distinct_models=require_distinct_models,
            require_distinct_families=require_distinct_families,
        )
    )

    manifest = _compile_v4(
        Config(N_SCHOOLS=2, roles={"conjecturer": list(routes)}),
        policy,
    )

    frozen = manifest.control_plane_policy.school_execution
    assert frozen.require_distinct_models is require_distinct_models
    assert frozen.require_distinct_families is require_distinct_families


@pytest.mark.parametrize(
    ("routes", "require_distinct_models", "require_distinct_families", "message"),
    (
        (
            (
                _route(
                    "route-a", model="same-model", family="family-a",
                    endpoint="https://a.invalid/v1",
                ),
                _route(
                    "route-b", model="same-model", family="family-b",
                    endpoint="https://b.invalid/v1",
                ),
            ),
            True,
            False,
            "SCHOOL_DISTINCT_MODEL|distinct model",
        ),
        (
            (
                _route(
                    "route-a", model="model-a", family="same-family",
                    endpoint="https://a.invalid/v1",
                ),
                _route(
                    "route-b", model="model-b", family="same-family",
                    endpoint="https://b.invalid/v1",
                ),
            ),
            False,
            True,
            "SCHOOL_DISTINCT_FAMILY|distinct famil",
        ),
    ),
)
def test_route_bound_independent_diversity_requirements_reject_only_own_collision(
    routes: tuple[dict, dict],
    require_distinct_models: bool,
    require_distinct_families: bool,
    message: str,
):
    policy = _control_policy(
        _school_execution(
            mode="route_bound",
            bindings=(_binding(0, 0, "route-a"), _binding(1, 1, "route-b")),
            allow_shared=False,
            require_distinct_models=require_distinct_models,
            require_distinct_families=require_distinct_families,
        )
    )

    with pytest.raises((RunManifestError, ValidationError), match=message):
        _compile_v4(
            Config(N_SCHOOLS=2, roles={"conjecturer": list(routes)}),
            policy,
        )


def test_v4_control_policy_is_deeply_immutable():
    manifest = _compile_v4(_historical_config(), _control_policy())
    policy = manifest.control_plane_policy

    with pytest.raises(ValidationError, match="frozen"):
        policy.mode = "legacy"
    with pytest.raises(ValidationError, match="frozen"):
        policy.school_execution.allow_shared = False
    with pytest.raises(ValidationError, match="frozen"):
        policy.conjecture_context.initial_max_blocks = 999
    with pytest.raises(ValidationError, match="frozen"):
        policy.workflow_retry.max_workflow_retries = 1
    with pytest.raises(ValidationError, match="frozen"):
        policy.contract_versions.bridge_ledger_wire_contract = "bridge.ledger.v1"
