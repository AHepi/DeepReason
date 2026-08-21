"""Fresh re-derivation of the all-configs-allowed parked remainder (R2).

For each parked denial site: construct the configuration the old gate
refuses and report the OBSERVED outcome on the current tree. Output is
pasted verbatim into SPEC.md.
"""
from __future__ import annotations

import json
import re
import sys
import traceback

sys.path.insert(0, "/home/user/DeepReason")

from pydantic import ValidationError

from deepreason.config import Config
from deepreason.run_manifest import (
    ControlPlanePolicyV1,
    CriticismPolicyV1,
    RunManifest,
    RunManifestError,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    compile_run_manifest,
    preflight_payload,
)
from tests.test_run_manifest_v4 import (
    _binding,
    _compile_v4,
    _control_policy,
    _route,
    _school_execution,
)

STAMP = "2026-07-16T00:00:00Z"
RESULTS: list[tuple[str, str, str]] = []


def probe(label: str):
    def deco(fn):
        try:
            value = fn()
        except Exception as error:  # noqa: BLE001 - the probe records everything
            code = getattr(error, "code", None)
            if code is None:
                blob = " ".join(str(error).split())
                hit = re.search(r"[A-Z][A-Z0-9_]{8,}", blob)
                code = hit.group(0) if hit else blob[:110]
            kind = "REFUSES" if isinstance(error, (RunManifestError, ValidationError, ValueError)) else "CRASHES UNTYPED"
            RESULTS.append((label, kind, f"{type(error).__name__}: {code[:110]}"))
        else:
            if isinstance(value, tuple):
                notices = value
            else:
                notices = (
                    getattr(value, "compile_notices", None)
                    if value is not None
                    else None
                )
            if notices:
                codes = ",".join(n.code for n in notices)
                RESULTS.append((label, "COMPILES+NOTICE", codes[:300]))
            else:
                RESULTS.append((label, "COMPILES (no notice)", repr(value)[:80]))
        return fn

    return deco


def _crit_policy(**kw):
    base = dict(
        minimum_foreign_school_coverage=1,
        bindings=(),
        max_batch_size=8,
        target_eligibility="accepted_school_artifacts",
        authority="observe_only",
        allow_shared=True,
    )
    base.update(kw)
    return CriticismPolicyV1(**base)


def _crit_binding(school: int, seat: int, endpoint_id: str, role="argumentative_critic"):
    return SchoolRoleBindingV1(
        school_id=f"school-{school}", role=role, seat=seat, endpoint_id=endpoint_id
    )


def _v4_with_criticism(config, criticism, control=None):
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control or _control_policy(),
        criticism_policy=criticism,
    )


# ---------------------------------------------------------------- A1 school
@probe("A1 V4_SCHOOL_ROLE_UNSUPPORTED")
def _():
    config = Config(N_SCHOOLS=1, roles={"conjecturer": _route("route-a"), "judge": _route("route-a")})
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
    return _compile_v4(config, policy)


@probe("A2 V4_SCHOOL_BINDING_INCOMPLETE")
def _():
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
        _school_execution(mode="route_bound", bindings=(_binding(0, 0, "route-a"),))
    )
    return _compile_v4(config, policy)


@probe("A3 V4_SCHOOL_SHARED_SEAT_FORBIDDEN")
def _():
    config = Config(N_SCHOOLS=2, roles={"conjecturer": _route("route-a")})
    policy = _control_policy(
        _school_execution(
            mode="route_bound",
            bindings=(_binding(0, 0, "route-a"), _binding(1, 0, "route-a")),
            allow_shared=False,
        )
    )
    return _compile_v4(config, policy)


@probe("A4 V4_SCHOOL_DISTINCT_MODEL_REQUIRED")
def _():
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
    return _compile_v4(config, policy)


@probe("A5 V4_SCHOOL_DISTINCT_FAMILY_REQUIRED")
def _():
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
    return _compile_v4(config, policy)


# ------------------------------------------------------------- A6 criticism
@probe("A6 CRITICISM_ACTIVE_CONJECTURE_REQUIRED (compile_run_manifest)")
def _():
    config = Config(N_SCHOOLS=2, roles={"conjecturer": _route("route-a"),
                                        "argumentative_critic": _route("route-a")})
    control = _control_policy(mode="shadow")
    return _v4_with_criticism(config, _crit_policy(), control)


@probe("A7 V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE")
def _():
    config = Config(N_SCHOOLS=1, roles={"conjecturer": _route("route-a"),
                                        "argumentative_critic": _route("route-a")})
    return _v4_with_criticism(
        config,
        _crit_policy(
            minimum_foreign_school_coverage=1,
            bindings=(_crit_binding(0, 0, "route-a"),),
        ),
    )


@probe("A8 V4_CRITICISM_ROLE_UNSUPPORTED")
def _():
    config = Config(N_SCHOOLS=2, roles={"conjecturer": _route("route-a"),
                                        "argumentative_critic": _route("route-a")})
    return _v4_with_criticism(
        config,
        _crit_policy(
            bindings=(
                _crit_binding(0, 0, "route-a", role="conjecturer"),
                _crit_binding(1, 0, "route-a", role="conjecturer"),
            )
        ),
    )


@probe("A9 V4_CRITICISM_BINDING_INCOMPLETE")
def _():
    config = Config(N_SCHOOLS=2, roles={"conjecturer": _route("route-a"),
                                        "argumentative_critic": _route("route-a")})
    return _v4_with_criticism(
        config, _crit_policy(bindings=(_crit_binding(0, 0, "route-a"),))
    )


@probe("A10 V4_CRITICISM_SHARED_SEAT_FORBIDDEN")
def _():
    config = Config(N_SCHOOLS=2, roles={"conjecturer": _route("route-a"),
                                        "argumentative_critic": _route("route-a")})
    return _v4_with_criticism(
        config,
        _crit_policy(
            bindings=(_crit_binding(0, 0, "route-a"), _crit_binding(1, 0, "route-a")),
            allow_shared=False,
        ),
    )


@probe("A11 V4_CRITICISM_DEFENDER_REQUIRED")
def _():
    config = Config(N_SCHOOLS=2, roles={"conjecturer": _route("route-a"),
                                        "argumentative_critic": _route("route-a")})
    return _v4_with_criticism(
        config,
        _crit_policy(
            bindings=(_crit_binding(0, 0, "route-a"), _crit_binding(1, 0, "route-a")),
            authority="defended_trial",
        ),
    )


@probe("A12 V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED")
def _():
    config = Config(
        N_SCHOOLS=2,
        roles={
            "conjecturer": _route("route-a"),
            "argumentative_critic": _route("route-a"),
            "defender": _route("route-a"),
            "judge": _route("route-a"),
        },
    )
    return _v4_with_criticism(
        config,
        _crit_policy(
            bindings=(_crit_binding(0, 0, "route-a"), _crit_binding(1, 0, "route-a")),
            authority="defended_trial",
        ),
    )


# ------------------------------------------------------------- A13/A14 v5/v6
@probe("A13 V5_CAPABILITY_PROFILE_MISMATCH")
def _():
    from tests.test_run_manifest_v5_inquiry import _config as v5_config
    from tests.test_run_manifest_v5_inquiry import _control as v5_control
    from deepreason.run_manifest import InquiryCapabilityPolicyV1

    control = v5_control()
    return compile_run_manifest(
        v5_config(),
        schema_version=5,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
        run_input_digest="b" * 64,
        inquiry_capability_policy=InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2"
        ),
    )


@probe("A14 V6_CAPABILITY_PROFILE_MISMATCH")
def _():
    from tests.test_run_input_v6_commitments import _config as v6_config
    from tests.test_run_input_v6_commitments import _control
    from deepreason.run_manifest import InquiryCapabilityPolicyV1

    return compile_run_manifest(
        v6_config(),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(6),
        run_input_digest="a" * 64,
        inquiry_capability_policy=InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v1"
        ),
    )


# ----------------------------------------------------------- A15-A17 preflight
@probe("A15 RUBRIC_INPUT_FORBIDDEN (preflight_payload)")
def _():
    from tests.test_run_manifest import _compile_v6_manifest

    manifest = _compile_v6_manifest()
    return preflight_payload(manifest, {"standard": "rubric-standard"})


@probe("A16 SECOND_JUDGE_FAMILY_REQUIRED (preflight_payload)")
def _():
    from tests.test_run_manifest import _compile_v6_manifest

    manifest = _compile_v6_manifest()
    allowed = manifest.model_copy(update={"rubric_policy": "allow"})
    return preflight_payload(allowed, {"standard": "rubric-standard"})


@probe("A17 PROPERTY_RUBRIC_TRIAL_FORBIDDEN (preflight_harness)")
def _():
    import inspect
    from deepreason.run_manifest import preflight_harness

    source = inspect.getsource(preflight_harness)
    return f"raises_PROPERTY_RUBRIC_TRIAL_FORBIDDEN={'PROPERTY_RUBRIC_TRIAL_FORBIDDEN' in source and 'raise' in source}"


@probe("A17b RUBRIC_INPUT_FORBIDDEN (preflight_harness)")
def _():
    import inspect
    from deepreason.run_manifest import preflight_harness

    source = inspect.getsource(preflight_harness)
    return f"raise_count={source.count('raise RunManifestError')}"


# -------------------------------------------------------------- A18 scratch
@probe("A18 SCRATCH_EMBEDDER_MODEL_UNRESOLVED")
def _():
    config = Config(
        roles={"conjecturer": _route("route-a")},
        scratchpad={"enabled": True, "semantic_retrieval": True},
        EMBEDDER_MODEL="unresolved",
    )
    return compile_run_manifest(
        config,
        schema_version=3,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )


@probe("A19 ScratchpadConfig reserved attention fractions")
def _():
    config = Config(
        roles={"conjecturer": _route("route-a")},
        scratchpad={"enabled": True, "exploratory_fraction": 0.7,
                    "underexposed_fraction": 0.7},
    )
    pad = config.scratchpad
    return (
        f"CLAMPED 0.7,0.7 -> {pad.exploratory_fraction},{pad.underexposed_fraction}"
    )


# --------------------------------------------------------------- A20 intake
@probe("A20 INTAKE_CYCLES_CEILING_EXCEEDED")
def _():
    from deepreason.intake_form import IntakeFormV1, PUBLIC_MAX_CYCLES

    form = IntakeFormV1(question="q?", cycles=PUBLIC_MAX_CYCLES + 1)
    return f"CLAMPED {PUBLIC_MAX_CYCLES + 1} -> {form.cycles}"


# ------------------------------------------------- A21 v6 behavioral contract
@probe("A21 V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED")
def _():
    from tests.test_run_input_v6_commitments import _config as v6_config
    from tests.test_run_input_v6_commitments import _control

    config = v6_config()
    data = config.model_dump(mode="json")
    data["bridge"] = {"mode": "grounded_two_stage"}
    roles = dict(data["roles"])
    roles.pop("judge", None)
    data["roles"] = roles
    return compile_run_manifest(
        Config(**data),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(6),
        run_input_digest="a" * 64,
    )


# ------------------------------------------------ A22 already-converted checks
@probe("A22 already-done? CALIBRATION_RECEIPT_* (_preflight_text_authority)")
def _():
    import inspect
    from deepreason.run_manifest import _preflight_text_authority

    source = inspect.getsource(_preflight_text_authority)
    raises = "raise" in source
    return f"raises={raises}"


@probe("A23 already-done? V6_LAUNCH_DISABLED (runtime/launch_policy.py)")
def _():
    import inspect
    from deepreason.runtime import launch_policy

    source = inspect.getsource(launch_policy.require_v6_launch_allowed)
    return f"raises={'raise' in source}"


for label, verdict, detail in RESULTS:
    print(f"{label:<62} | {verdict:<20} | {detail}")
