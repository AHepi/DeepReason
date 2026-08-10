"""V6 rejects model phases that have no transactional dispatch contract."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deepreason.config import Config
from deepreason.run_manifest import compile_run_manifest
from tests.test_v6_transaction_qualification import (
    STAMP,
    _control,
    _criticism_policy,
    _route,
)


def test_v6_defended_trial_fails_at_manifest_compile_not_during_dispatch():
    roles = {
        "conjecturer": [_route("conjecturer-route")],
        "argumentative_critic": [
            _route(f"critic-route-{seat}", seat) for seat in range(3)
        ],
        "defender": [_route("defender-route", 0)],
        "judge": [_route("judge-a", 1), _route("judge-b", 2)],
    }
    policy = _criticism_policy().model_copy(update={"authority": "defended_trial"})

    with pytest.raises(
        ValidationError,
        match="V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED",
    ):
        compile_run_manifest(
            Config(N_SCHOOLS=3, roles=roles),
            schema_version=6,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
            control_plane_policy=_control(),
            criticism_policy=policy,
            run_input_digest="f" * 64,
        )


def test_v6_defended_trial_accepts_same_model_judges_past_the_cross_family_gate():
    """Part D2 (S16, Amendment 9 R24): the defended_trial V4 criticism-
    policy check (run_manifest.py's _validate_v4_criticism_policy) gained
    the same structural same-model substitute as the rubric_policy checks
    and the runtime gate. Two IDENTICAL judge routes (same seat reused, so
    same family AND same model) must reach the NEXT check
    (V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED) rather than being
    stopped by V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED first -- the
    error TYPE that survives is the proof, same technique as
    test_configuring_school_bindings_does_not_reach_the_gate_with_two_
    families in test_prose_refutation_boundaries.py."""

    roles = {
        "conjecturer": [_route("conjecturer-route")],
        "argumentative_critic": [
            _route(f"critic-route-{seat}", seat) for seat in range(3)
        ],
        "defender": [_route("defender-route", 0)],
        "judge": [_route("judge-same", 9), _route("judge-same", 9)],
    }
    policy = _criticism_policy().model_copy(update={"authority": "defended_trial"})

    with pytest.raises(
        ValidationError,
        match="V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED",
    ):
        compile_run_manifest(
            Config(N_SCHOOLS=3, roles=roles),
            schema_version=6,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
            control_plane_policy=_control(),
            criticism_policy=policy,
            run_input_digest="f" * 64,
        )
