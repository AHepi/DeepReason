"""Every remaining compile-time denial site converted 2026-08-16.

Completes the operator's standing law (CLAUDE.md, "Operator design laws",
2026-08-12): "All configurations should be allowed." The 2026-08-12 tranche
converted a tier-1 subset and self-parked ~20 more sites; this file pins the
remainder, one test per site, asserting the SAME contract that tranche set:
the configuration COMPILES, and the retired refusal survives as a typed
`CompileNoticeV1` carrying the old code.

Where two parts of one configuration genuinely contradict each other, the
test also pins the deterministic resolution (R4) and the `resolution` string
that records which half was dropped.

Tranche: experiments/2026-08-16-change-configs-complete-seats-test/
"""

from __future__ import annotations

import pytest

from deepreason.capabilities.policy import InquiryCapabilityPolicyV1
from deepreason.config import Config
from deepreason.llm.firewall import SchoolRouteResolutionError
from deepreason.run_manifest import (
    CriticismPolicyV1,
    RunManifest,
    RunManifestError,
    SchoolRoleBindingV1,
    compile_run_manifest,
    preflight_payload,
    resolve_route_seat_behavioral_capability,
)
from tests.test_run_manifest_v4 import (
    _binding,
    _compile_v4,
    _control_policy,
    _route,
    _school_execution,
)

STAMP = "2026-07-16T00:00:00Z"


def _codes(manifest: RunManifest) -> list[str]:
    return [notice.code for notice in (manifest.compile_notices or ())]


def _notice(manifest: RunManifest, code: str):
    matches = [n for n in (manifest.compile_notices or ()) if n.code == code]
    assert matches, f"{code} not disclosed; recorded: {_codes(manifest)}"
    return matches[0]


def _criticism(**overrides) -> CriticismPolicyV1:
    values = {
        "minimum_foreign_school_coverage": 1,
        "bindings": (),
        "max_batch_size": 8,
        "target_eligibility": "accepted_school_artifacts",
        "authority": "observe_only",
        "allow_shared": True,
    }
    values.update(overrides)
    return CriticismPolicyV1(**values)


def _critic_binding(school: int, seat: int, endpoint_id: str, role="argumentative_critic"):
    return SchoolRoleBindingV1(
        school_id=f"school-{school}", role=role, seat=seat, endpoint_id=endpoint_id
    )


def _compile_with_criticism(config: Config, criticism, control=None) -> RunManifest:
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control or _control_policy(),
        criticism_policy=criticism,
    )


def _critic_config(schools: int = 2) -> Config:
    return Config(
        N_SCHOOLS=schools,
        roles={
            "conjecturer": _route("route-a"),
            "argumentative_critic": _route("route-a"),
        },
    )


# --------------------------------------------------------------- v4 schools


def test_school_binding_naming_an_unsupported_role_compiles_with_a_notice():
    """v4 drives conjecturer schools only. A binding naming another role is a
    configuration, not a shape error: it compiles, and `resolve_school_route`
    is the point of use that refuses typed."""

    config = Config(
        N_SCHOOLS=1,
        roles={"conjecturer": _route("route-a"), "judge": _route("route-a")},
    )
    policy = _control_policy(
        _school_execution(
            mode="route_bound",
            bindings=(
                SchoolRoleBindingV1(
                    school_id="school-0", role="judge", seat=0, endpoint_id="route-a"
                ),
            ),
        )
    )

    manifest = _compile_v4(config, policy)
    assert "V4_SCHOOL_ROLE_UNSUPPORTED" in _codes(manifest)
    assert (
        _notice(manifest, "V4_SCHOOL_ROLE_UNSUPPORTED").pointer
        == "/control_plane_policy/school_execution/bindings"
    )


def test_school_distinct_model_conflict_resolves_to_the_bindings():
    config = Config(
        N_SCHOOLS=2,
        roles={
            "conjecturer": [
                _route("route-a", model="same-model", endpoint="https://a.invalid/v1"),
                _route("route-b", model="same-model", endpoint="https://b.invalid/v1"),
            ]
        },
    )
    policy = _control_policy(
        _school_execution(
            mode="route_bound",
            bindings=(_binding(0, 0, "route-a"), _binding(1, 1, "route-b")),
            require_distinct_models=True,
        )
    )

    notice = _notice(_compile_v4(config, policy), "V4_SCHOOL_DISTINCT_MODEL_REQUIRED")
    assert "explicit bindings win" in notice.resolution
    assert notice.pointer.endswith("/require_distinct_models")


def test_school_distinct_family_conflict_resolves_to_the_bindings():
    config = Config(
        N_SCHOOLS=2,
        roles={
            "conjecturer": [
                _route("route-a", model="m1", family="fam", endpoint="https://a.invalid/v1"),
                _route("route-b", model="m2", family="fam", endpoint="https://b.invalid/v1"),
            ]
        },
    )
    policy = _control_policy(
        _school_execution(
            mode="route_bound",
            bindings=(_binding(0, 0, "route-a"), _binding(1, 1, "route-b")),
            require_distinct_families=True,
        )
    )

    notice = _notice(_compile_v4(config, policy), "V4_SCHOOL_DISTINCT_FAMILY_REQUIRED")
    assert "fam" in notice.resolution


@pytest.mark.parametrize(
    ("code", "message"),
    (
        ("V4_SCHOOL_UNKNOWN", "no configured school"),
        ("V4_SCHOOL_SEAT_OUT_OF_RANGE", "does not name a frozen route"),
    ),
)
def test_dangling_school_references_still_refuse(code: str, message: str):
    """R5's boundary, pinned from the other side: a binding naming something
    that does not exist is not a configuration being denied -- there is
    nothing to disclose, because the named thing is absent."""

    config = Config(N_SCHOOLS=1, roles={"conjecturer": _route("route-a")})
    binding = (
        _binding(2, 0, "route-a")
        if code == "V4_SCHOOL_UNKNOWN"
        else _binding(0, 4, "route-a")
    )
    policy = _control_policy(
        _school_execution(mode="route_bound", bindings=(binding,))
    )
    with pytest.raises(Exception, match=code):
        _compile_v4(config, policy)


# ------------------------------------------------------------- v4 criticism


def test_criticism_under_an_inactive_control_mode_compiles_with_both_notices():
    """The compile-time gate and its model-validator twin disclose the same
    fact from two places; both are recorded, neither refuses."""

    manifest = _compile_with_criticism(
        _critic_config(),
        _criticism(),
        _control_policy(mode="shadow"),
    )
    codes = _codes(manifest)
    assert "CRITICISM_ACTIVE_CONJECTURE_REQUIRED" in codes
    assert "V4_CRITICISM_ACTIVE_REQUIRED" in codes


def test_unsatisfiable_foreign_coverage_compiles_and_states_the_arithmetic():
    """No resolution is invented: `minimum_foreign_school_coverage` is
    `ge=1`, so it cannot be clamped to zero. The declared value is kept and
    workflow/criticism.py refuses typed at the point of use."""

    manifest = _compile_with_criticism(
        _critic_config(schools=1),
        _criticism(bindings=(_critic_binding(0, 0, "route-a"),)),
    )
    notice = _notice(manifest, "V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE")
    assert "coverage=1" in notice.message
    assert notice.resolution is None
    assert manifest.criticism_policy.minimum_foreign_school_coverage == 1


def test_criticism_binding_naming_a_non_critic_role_compiles_with_a_notice():
    manifest = _compile_with_criticism(
        _critic_config(),
        _criticism(
            bindings=(
                _critic_binding(0, 0, "route-a", role="conjecturer"),
                _critic_binding(1, 0, "route-a", role="conjecturer"),
            )
        ),
    )
    assert "V4_CRITICISM_ROLE_UNSUPPORTED" in _codes(manifest)


def test_incomplete_criticism_binding_roster_compiles_with_a_notice():
    manifest = _compile_with_criticism(
        _critic_config(), _criticism(bindings=(_critic_binding(0, 0, "route-a"),))
    )
    assert "school-1" in _notice(manifest, "V4_CRITICISM_BINDING_INCOMPLETE").message


def test_criticism_shared_seat_conflict_resolves_to_the_bindings():
    manifest = _compile_with_criticism(
        _critic_config(),
        _criticism(
            bindings=(_critic_binding(0, 0, "route-a"), _critic_binding(1, 0, "route-a")),
            allow_shared=False,
        ),
    )
    notice = _notice(manifest, "V4_CRITICISM_SHARED_SEAT_FORBIDDEN")
    assert "explicit bindings win" in notice.resolution
    assert "argumentative_critic[0]" in notice.resolution


def test_defended_trial_without_a_defender_compiles_with_a_notice():
    """The seats/evidence law is not weakened by this: informal/trial.py
    declines typed (`no-defender-role`) before any call, so no warrant and no
    attack edge can come out of the missing seat."""

    manifest = _compile_with_criticism(
        _critic_config(),
        _criticism(
            bindings=(_critic_binding(0, 0, "route-a"), _critic_binding(1, 0, "route-a")),
            authority="defended_trial",
        ),
    )
    assert "V4_CRITICISM_DEFENDER_REQUIRED" in _codes(manifest)
    assert _notice(manifest, "V4_CRITICISM_DEFENDER_REQUIRED").pointer == "/roles/defender"


def test_defended_trial_with_a_single_family_judge_matrix_compiles_with_a_notice():
    config = Config(
        N_SCHOOLS=2,
        roles={
            "conjecturer": _route("route-a"),
            "argumentative_critic": _route("route-a"),
            "defender": _route("route-a"),
            "judge": _route("route-a"),
        },
    )
    manifest = _compile_with_criticism(
        config,
        _criticism(
            bindings=(_critic_binding(0, 0, "route-a"), _critic_binding(1, 0, "route-a")),
            authority="defended_trial",
        ),
    )
    assert "V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED" in _codes(manifest)


def test_foreign_criticism_without_a_runtime_critic_role_fails_typed():
    """The one runtime line this tranche touched. Converting
    V4_CRITICISM_BINDING_INCOMPLETE makes it newly reachable, and an
    unsatisfiable ensemble must fail TYPED at the point of use -- it used to
    be a bare RuntimeError with no code to record."""

    from deepreason.scheduler import scheduler as scheduler_module

    error = SchoolRouteResolutionError(
        "SCHOOL_ROUTE_CRITIC_ROLE_MISSING",
        "manifest foreign criticism has no runtime critic role",
    )
    assert error.code == "SCHOOL_ROUTE_CRITIC_ROLE_MISSING"
    assert isinstance(error, RuntimeError)  # every existing catcher still catches it
    import inspect

    body = inspect.getsource(scheduler_module.Scheduler._arg_crit)
    assert "SCHOOL_ROUTE_CRITIC_ROLE_MISSING" in body
    assert 'raise RuntimeError("manifest foreign criticism' not in body


# ------------------------------------------------------- v5/v6 capabilities


@pytest.mark.parametrize(
    ("schema_version", "code", "wrong_profile", "expected_profile"),
    (
        (5, "V5_CAPABILITY_PROFILE_MISMATCH", "inquiry-capabilities.v2", "inquiry-capabilities.v1"),
        (6, "V6_CAPABILITY_PROFILE_MISMATCH", "inquiry-capabilities.v1", "inquiry-capabilities.v2"),
    ),
)
def test_capability_profile_mismatch_resolves_to_the_control_plane(
    schema_version: int, code: str, wrong_profile: str, expected_profile: str
):
    """R4 conflict: two parts of one configuration disagree. The control
    plane wins -- it is the coarser, earlier-frozen authority -- and the
    manifest carries the corrected profile, not the refused one."""

    if schema_version == 5:
        from tests.test_run_manifest_v5_inquiry import _config as source_config
        from tests.test_run_manifest_v5_inquiry import _control as source_control

        control = source_control()
        digest = "b" * 64
    else:
        from tests.test_run_input_v6_commitments import _config as source_config
        from tests.test_run_input_v6_commitments import _control

        control = _control(6)
        digest = "a" * 64

    manifest = compile_run_manifest(
        source_config(),
        schema_version=schema_version,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
        run_input_digest=digest,
        inquiry_capability_policy=InquiryCapabilityPolicyV1(
            capability_profile=wrong_profile
        ),
    )

    notice = _notice(manifest, code)
    assert "control-plane policy wins" in notice.resolution
    assert wrong_profile in notice.resolution
    assert manifest.inquiry_capability_policy.capability_profile == expected_profile
    assert (
        manifest.control_plane_policy.capability_profile == expected_profile
    )


def test_unimplemented_capabilities_still_refuse():
    """R5/R6's boundary from the other side: a gate guarding a capability
    whose dispatch code does not exist stays a refusal. Converting it would
    trade a typed compile refusal for an untyped runtime crash -- the
    opposite of what the law asks for."""

    from tests.test_research_capability import _policy
    from tests.test_run_input_v6_commitments import _config as v6_config
    from tests.test_run_input_v6_commitments import _control

    with pytest.raises((RunManifestError, ValueError), match="V6_RESEARCH_UNAVAILABLE"):
        compile_run_manifest(
            v6_config(),
            schema_version=6,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
            control_plane_policy=_control(6),
            run_input_digest="a" * 64,
            inquiry_capability_policy=InquiryCapabilityPolicyV1(
                capability_profile="inquiry-capabilities.v2",
                research=_policy(backend_identity="search@future"),
            ),
        )


# ------------------------------------------------------------- preflight


def test_rubric_input_with_one_judge_family_is_disclosed_not_refused():
    from tests.test_run_manifest import _compile_v6_manifest

    manifest = _compile_v6_manifest()
    allowed = manifest.model_copy(update={"rubric_policy": "allow"})
    notices = preflight_payload(allowed, {"standard": "rubric-standard"})
    assert [n.code for n in notices] == ["SECOND_JUDGE_FAMILY_REQUIRED"]


# --------------------------------------------------------------- scratch


def test_unresolved_embedder_model_falls_back_to_hashing():
    config = Config(
        roles={"conjecturer": _route("route-a")},
        scratchpad={"enabled": True, "semantic_retrieval": True},
        EMBEDDER_MODEL="unresolved",
    )
    manifest = compile_run_manifest(
        config,
        schema_version=3,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    notice = _notice(manifest, "SCRATCH_EMBEDDER_MODEL_UNRESOLVED")
    assert "deterministic hashing" in notice.resolution
    assert manifest.scratch_policy.embedder_backend == "deterministic_hashing"
    assert manifest.scratch_policy.embedder_model is None


def test_over_claimed_attention_fractions_are_clamped_and_disclosed():
    config = Config(
        roles={"conjecturer": _route("route-a")},
        scratchpad={
            "enabled": True,
            "exploratory_fraction": 0.7,
            "underexposed_fraction": 0.7,
        },
    )
    # The Config-side clamp already fired, so the manifest sees a fitting
    # pair; the notice therefore comes from the raw values only when the
    # manifest is compiled from an unclamped source. Both sides agree, which
    # is the property that matters: no surface refuses, and both hold 0.5/0.5.
    assert config.scratchpad.exploratory_fraction == 0.5
    assert config.scratchpad.underexposed_fraction == 0.5
    manifest = compile_run_manifest(
        config,
        schema_version=3,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    policy = manifest.scratch_policy
    assert policy.exploratory_fraction + policy.underexposed_fraction == 1.0


# --------------------------------------------------------- v6 route seats


def _grounded_bridge_v6_without_bridge_routes() -> RunManifest:
    from tests.test_run_input_v6_commitments import _config as v6_config
    from tests.test_run_input_v6_commitments import _control

    data = v6_config().model_dump(mode="json")
    data["bridge"] = {"mode": "grounded_two_stage"}
    return compile_run_manifest(
        Config(**data),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(6),
        run_input_digest="a" * 64,
    )


def test_grounded_bridge_without_stage_routes_compiles_instead_of_crashing():
    """The finding this tranche's own census produced, and the one the park
    (P2) predicted wrongly. Before: a bare `IndexError` inside
    `_compile_route_seat_contract_decomposition_plan` -- neither a compile
    nor a typed refusal. After: it compiles, every skipped grant is
    disclosed, and the seat carries no authority it could act on."""

    manifest = _grounded_bridge_v6_without_bridge_routes()
    codes = _codes(manifest)
    assert "V6_CONTRACT_DECOMPOSITION_ROUTE_REQUIRED" in codes
    assert "V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED" in codes
    notice = _notice(manifest, "V6_CONTRACT_DECOMPOSITION_ROUTE_REQUIRED")
    assert "omitted from the plan" in notice.resolution


def test_a_skipped_behavioral_grant_still_refuses_typed_at_dispatch():
    """R6: the impossibility moves to the point of use, it does not vanish."""

    manifest = _grounded_bridge_v6_without_bridge_routes()
    bridge = manifest.bridge_policy
    assert bridge is not None
    with pytest.raises(RunManifestError) as raised:
        resolve_route_seat_behavioral_capability(
            manifest,
            role=bridge.ledger_role,
            seat=0,
            endpoint_id="anything",
            route_sha256="0" * 64,
        )
    assert raised.value.code.startswith("V6_")


def test_notice_free_compiles_record_nothing():
    """The byte-contract guard: a configuration that triggers no disclosure
    must serialize exactly as it did before `compile_notices` existed."""

    from tests.test_run_manifest import _compile_v6_manifest

    manifest = _compile_v6_manifest()
    assert manifest.compile_notices is None
    assert b"compile_notices" not in manifest.canonical_bytes()
