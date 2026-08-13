"""V6 compiles defended_trial criticism authority (defended-trial-wiring
tranche, 2026-08-13): informal/trial.py's defender and judge calls are now
wired through InquiryTransactionService, so the V6_DEFENDED_TRIAL_
TRANSACTION_CONTRACT_REQUIRED refusal this file used to pin is retired.
"""

from __future__ import annotations

from deepreason.config import Config
from deepreason.run_manifest import compile_run_manifest
from tests.test_v6_transaction_qualification import (
    STAMP,
    _control,
    _criticism_policy,
    _route,
)


def test_v6_defended_trial_compiles_and_grants_defender_and_judge_contracts():
    roles = {
        "conjecturer": [_route("conjecturer-route")],
        "argumentative_critic": [
            _route(f"critic-route-{seat}", seat) for seat in range(3)
        ],
        "defender": [_route("defender-route", 0)],
        "judge": [_route("judge-a", 1), _route("judge-b", 2)],
    }
    policy = _criticism_policy().model_copy(update={"authority": "defended_trial"})

    manifest = compile_run_manifest(
        Config(N_SCHOOLS=3, roles=roles),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        criticism_policy=policy,
        run_input_digest="f" * 64,
    )

    assert manifest.criticism_policy.authority == "defended_trial"
    plan = manifest.route_seat_behavioral_capability_plan
    grants_by_role_seat = {
        (entry.role, entry.seat): {grant.contract_id for grant in entry.contracts}
        for entry in plan.entries
    }
    assert "defender.direct.v1" in grants_by_role_seat[("defender", 0)]
    assert "judgeruling.direct.v1" in grants_by_role_seat[("judge", 0)]
    assert "judgeruling.direct.v1" in grants_by_role_seat[("judge", 1)]


def test_v6_defended_trial_accepts_same_model_judges_past_the_cross_family_gate():
    """Part D2 (S16, Amendment 9 R24): the defended_trial V4 criticism-
    policy check (run_manifest.py's _validate_v4_criticism_policy) has the
    same structural same-model substitute as the rubric_policy checks and
    the runtime gate. Two IDENTICAL judge routes (same seat reused, so
    same family AND same model) must reach and pass compilation rather
    than being stopped by V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED --
    proven here by successful compilation now that the downstream
    transaction-contract gate this test used to key off is retired."""

    roles = {
        "conjecturer": [_route("conjecturer-route")],
        "argumentative_critic": [
            _route(f"critic-route-{seat}", seat) for seat in range(3)
        ],
        "defender": [_route("defender-route", 0)],
        "judge": [_route("judge-same", 9), _route("judge-same", 9)],
    }
    policy = _criticism_policy().model_copy(update={"authority": "defended_trial"})

    manifest = compile_run_manifest(
        Config(N_SCHOOLS=3, roles=roles),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        criticism_policy=policy,
        run_input_digest="f" * 64,
    )

    assert manifest.criticism_policy.authority == "defended_trial"
