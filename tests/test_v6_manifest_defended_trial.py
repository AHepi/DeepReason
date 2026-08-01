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
