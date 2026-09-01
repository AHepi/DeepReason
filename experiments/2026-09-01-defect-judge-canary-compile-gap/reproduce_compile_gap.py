"""Offline RED reproduction for the defended-trial manifest compile gap."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from deepreason.config import Config
from deepreason.rules.crit import _resolve_authority
from deepreason.run_manifest import compile_run_manifest, config_from_run_manifest
from tests.test_v6_transaction_qualification import STAMP, _control, _route


CONSEQUENCE = "authority will resolve observe_only; trial contracts will be empty"


def build_without_criticism_policy():
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
    return compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        run_input_digest="f" * 64,
        # Deliberately no criticism_policy= argument: this is P-S1's call shape.
    )


def main() -> None:
    manifest = build_without_criticism_policy()
    runtime = config_from_run_manifest(manifest)
    trial_contracts = {
        f"{entry.role}#{entry.seat}": [grant.contract_id for grant in entry.contracts]
        for entry in manifest.route_seat_behavioral_capability_plan.entries
        if entry.role in {"defender", "judge"}
    }
    effective_authority = _resolve_authority(runtime, None, policy_call=False)
    carried_intent_notice = next(
        notice
        for notice in manifest.compile_notices or ()
        if notice.code == "ENGINE_CONFIG_FIELD_NOT_CARRIED"
        and notice.pointer == "/engine_config/ENGAGED_CRITICISM_AUTHORITY"
    )
    assert json.loads(carried_intent_notice.value) == "defended_trial"
    matching_notices = [
        notice.model_dump(mode="json")
        for notice in manifest.compile_notices or ()
        if CONSEQUENCE in notice.message
    ]
    delivered = (
        manifest.criticism_policy is not None
        and manifest.criticism_policy.authority == "defended_trial"
        and trial_contracts
        and all(trial_contracts.values())
    )
    observed = {
        "requested_authority": runtime.ENGAGED_CRITICISM_AUTHORITY,
        "carried_intent_notice": carried_intent_notice.model_dump(mode="json"),
        "stored_criticism_policy": (
            None
            if manifest.criticism_policy is None
            else manifest.criticism_policy.authority
        ),
        "effective_authority": effective_authority,
        "trial_contracts": trial_contracts,
        "matching_compile_notices": matching_notices,
        "silent_gap": not delivered and not matching_notices,
    }
    print(json.dumps(observed, indent=2, sort_keys=True))
    assert delivered, "DEFENDED_TRIAL_NOT_COMPILED: " + CONSEQUENCE


if __name__ == "__main__":
    main()
