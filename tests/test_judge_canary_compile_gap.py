"""Regression proofs for defended-trial policy derivation at manifest compile."""

from __future__ import annotations

from deepreason.config import Config
from deepreason.preparation import _config_for_profile, _records_for_question
from deepreason.qualification import qualification_subject_digest
from deepreason.run_manifest import (
    CriticismPolicyV1,
    SchoolRoleBindingV1,
    compile_run_manifest,
)
from deepreason.v6_policy import (
    engaged_control_plane_policy_v3,
    engaged_criticism_policy,
)
from tests.test_reusable_qualification import _manifest, _profile
from tests.test_run_manifest_v4 import _control_policy as _v4_control
from tests.test_v6_transaction_qualification import STAMP, _control, _route


def _defended_four_school_fixture():
    profile = _profile()
    config = _config_for_profile(profile)
    base_route = dict(profile.endpoint_spec())
    roles = dict(config.roles)
    roles["judge"] = [
        {
            **base_route,
            "endpoint_id": "judge-1",
            "model": "judge-m1",
            "model_revision": "judge-m1",
            "family": "judge-f1",
        },
        {
            **base_route,
            "endpoint_id": "judge-2",
            "model": "judge-m2",
            "model_revision": "judge-m2",
            "family": "judge-f2",
        },
    ]
    config = config.model_copy(
        update={
            "roles": roles,
            "ENGAGED_CRITICISM_AUTHORITY": "defended_trial",
            "LEGACY_CRITICISM_ENABLED": False,
            "ADJUDICATION_STATUS_AUTHORITY_ENABLED": True,
            "JUDGE_SEATS_ENABLED": True,
        }
    )
    _dossier, run_input, _workload = _records_for_question("Question A")
    kwargs = {
        "schema_version": 6,
        "workload_profile": "text",
        "rubric_policy": "forbid",
        "compiled_at": "2026-07-23T00:00:00Z",
        "control_plane_policy": engaged_control_plane_policy_v3(),
        "run_input_digest": run_input.run_input_digest,
    }
    return profile, config, kwargs


def test_omitted_defended_policy_matches_explicit_and_controls_stay_pinned():
    profile, config, kwargs = _defended_four_school_fixture()
    default_observe = _manifest(profile)
    explicit_observe = compile_run_manifest(
        config,
        criticism_policy=engaged_criticism_policy(profile.endpoint_id),
        **kwargs,
    )
    explicit_defended = compile_run_manifest(
        config,
        criticism_policy=engaged_criticism_policy(
            profile.endpoint_id, authority="defended_trial"
        ),
        **kwargs,
    )
    omitted_defended = compile_run_manifest(config, **kwargs)

    assert (default_observe.sha256, qualification_subject_digest(default_observe, profile)) == (
        "de66096f79454255f3b0a4db932186c8573de9000d1ddcc881fc76c6abe45322",
        "02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713",
    )
    assert (
        explicit_observe.sha256,
        qualification_subject_digest(explicit_observe, profile),
    ) == (
        "2fb3ab698ee6777f038adcb9833fb32b628e1b3ec822946fd34975e162f2c58c",
        "c4b7ab8ccb3bd123372d9f434b1788a1d257004c22fbba3a63a82baf99d11ab8",
    )
    assert explicit_observe.criticism_policy.authority == "observe_only"
    assert (
        explicit_defended.sha256,
        qualification_subject_digest(explicit_defended, profile),
    ) == (
        "0299510d31e292900b36a7d4e20ad9ab9dee9f976a3b9f69b3cca558a3a41fbb",
        "de322caa1c8b9d4fefb598bc158ada98376f9f922191409e6168cfc7450057bb",
    )
    assert omitted_defended.model_dump(mode="json") == explicit_defended.model_dump(
        mode="json"
    )
    assert omitted_defended.sha256 == explicit_defended.sha256
    assert qualification_subject_digest(omitted_defended, profile) == (
        qualification_subject_digest(explicit_defended, profile)
    )


def test_three_school_omission_derives_matching_policy_and_trial_grants():
    roles = {
        "conjecturer": [_route("conjecturer-route")],
        "argumentative_critic": [
            _route(f"critic-route-{seat}", seat) for seat in range(3)
        ],
        "defender": [_route("defender-route")],
        "judge": [_route("judge-a", 1), _route("judge-b", 2)],
    }
    config = Config(
        N_SCHOOLS=3,
        roles=roles,
        ENGAGED_CRITICISM_AUTHORITY="defended_trial",
        LEGACY_CRITICISM_ENABLED=False,
        ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        JUDGE_SEATS_ENABLED=True,
    )
    expected_policy = CriticismPolicyV1(
        minimum_foreign_school_coverage=1,
        bindings=tuple(
            SchoolRoleBindingV1(
                school_id=f"school-{school}",
                role="argumentative_critic",
                seat=0,
                endpoint_id="critic-route-0",
            )
            for school in range(3)
        ),
        max_batch_size=4,
        target_eligibility="accepted_school_artifacts",
        authority="defended_trial",
        allow_shared=True,
    )
    kwargs = {
        "schema_version": 6,
        "workload_profile": "text",
        "rubric_policy": "forbid",
        "compiled_at": STAMP,
        "control_plane_policy": _control(),
        "run_input_digest": "f" * 64,
    }
    omitted = compile_run_manifest(config, **kwargs)
    explicit = compile_run_manifest(config, criticism_policy=expected_policy, **kwargs)

    assert omitted.model_dump(mode="json") == explicit.model_dump(mode="json")
    assert omitted.sha256 == explicit.sha256
    assert omitted.criticism_policy == expected_policy
    grants = {
        (entry.role, entry.seat): {contract.contract_id for contract in entry.contracts}
        for entry in omitted.route_seat_behavioral_capability_plan.entries
    }
    assert "defender.direct.v1" in grants[("defender", 0)]
    assert "judgeruling.direct.v1" in grants[("judge", 0)]
    assert "judgeruling.direct.v1" in grants[("judge", 1)]


def test_default_legacy_omission_stays_policy_free():
    config = Config(roles={"conjecturer": [_route("conjecturer-route")]})
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        run_input_digest="f" * 64,
    )

    assert config.LEGACY_CRITICISM_ENABLED is True
    assert config.ENGAGED_CRITICISM_AUTHORITY == "observe_only"
    assert manifest.criticism_policy is None
    assert all(
        "defender.direct.v1" not in {contract.contract_id for contract in entry.contracts}
        and "judgeruling.direct.v1"
        not in {contract.contract_id for contract in entry.contracts}
        for entry in manifest.route_seat_behavioral_capability_plan.entries
    )


def test_pre_v6_omission_does_not_derive_policy():
    config = Config(
        N_SCHOOLS=3,
        roles={
            "conjecturer": [_route("conjecturer-route")],
            "argumentative_critic": [_route("critic-route-0")],
        },
        ENGAGED_CRITICISM_AUTHORITY="defended_trial",
        LEGACY_CRITICISM_ENABLED=False,
        ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
    )
    manifest = compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_v4_control(),
    )

    assert manifest.criticism_policy is None
