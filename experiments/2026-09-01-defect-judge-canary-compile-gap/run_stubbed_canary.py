#!/usr/bin/env python3
"""One-cycle offline canary for v6 defended-trial provider reachability."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    run_production_contract_doctor,
)
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import (
    JudgeEnsemblePolicyError,
    JudgeSchoolEnsemblePolicyError,
    SchoolRouteResolutionError,
    leases_from_manifest,
)
from deepreason.ontology import Problem, ProblemProvenance, Provenance
from deepreason.rules.warrants import formally_backed
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    CriticismPolicyV1,
    RunManifestError,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.transaction import WorkBudgetDenied


STAMP = "2026-09-01T00:00:00Z"
CASE = "The proposal omits the boundary condition required by its own mechanism."
DEFENCE = "The boundary condition is enforced by the mechanism."
DECISIVE_POINT = "boundary condition"
TARGET = "A mechanism whose validity depends on an explicit boundary condition."
CRITICAL_SEQUENCE = [
    "argumentative_critic[0]",
    "defender[0]",
    "judge[0]",
    "judge[1]",
]
TYPED_REFUSALS = (
    RunManifestError,
    SchoolRouteResolutionError,
    JudgeEnsemblePolicyError,
    JudgeSchoolEnsemblePolicyError,
    WorkflowAuthorizationError,
    WorkBudgetDenied,
)


def _route(endpoint_id: str, role: str, seat: int = 0) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": f"offline-{role}-{seat}",
        "provider": "mock",
        "family": f"offline-{role}-{seat}",
        "max_tokens": 256,
        "context_window_tokens": 262_144,
    }


def _control() -> ControlPlanePolicyV3:
    return ControlPlanePolicyV3(
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
        contract_versions=ContractVersionPolicyV3(),
    )


def _config_and_policy() -> tuple[Config, CriticismPolicyV1]:
    config = Config(
        N_SCHOOLS=2,
        RETRY_MAX=0,
        VS_K=1,
        FUZZ_N=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        RECRIT_STANDING=False,
        NEAR_DUP_EPS=None,
        ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ENGAGED_CRITICISM_AUTHORITY="defended_trial",
        LEGACY_CRITICISM_ENABLED=False,
        JUDGE_SEATS_ENABLED=True,
        roles={
            "conjecturer": [_route("conjecturer-route", "conjecturer")],
            "argumentative_critic": [_route("critic-route", "critic")],
            "defender": [_route("defender-route", "defender")],
            "judge": [
                _route("judge-0-route", "judge", 0),
                _route("judge-1-route", "judge", 1),
            ],
        },
    )
    policy = CriticismPolicyV1(
        minimum_foreign_school_coverage=1,
        bindings=tuple(
            SchoolRoleBindingV1(
                school_id=f"school-{school}",
                role="argumentative_critic",
                seat=0,
                endpoint_id="critic-route",
            )
            for school in range(config.N_SCHOOLS)
        ),
        max_batch_size=4,
        target_eligibility="accepted_school_artifacts",
        authority="defended_trial",
        allow_shared=True,
    )
    return config, policy


def _bind_classification(harness: Harness, manifest) -> None:
    def admitted(_manifest, _pair, index):
        return ProductionContractCaseResultV1(
            case_id=f"case-{index + 1:03d}",
            first_pass_valid=True,
            eventual_valid=True,
            repair_count=0,
            semantic_admission=True,
        )

    harness.bind_model_classification(
        manifest,
        run_production_contract_doctor(manifest, case_executor=admitted),
    )


def _endpoint(route, label: str, calls: list[str], response: str) -> MockEndpoint:
    def respond(_prompt: str) -> str:
        calls.append(label)
        return response

    return MockEndpoint(
        respond,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )


def _typed_work(harness: Harness) -> list[dict]:
    rows = []
    for item in harness.workflow_state.transaction_work.values():
        role = item.preparation.route_lease.role
        if role not in {"argumentative_critic", "defender", "judge"}:
            continue
        provider = item.provider_attempts.get(item.preparation.attempt_index)
        rows.append(
            {
                "dispatch": f"{role}[{item.preparation.route_lease.seat}]",
                "task_kind": item.preparation.task_kind.value,
                "step": item.preparation.task_payload_value.get(
                    "step", item.preparation.task_payload_value.get("phase")
                ),
                "provider_outcome": None if provider is None else provider.outcome,
                "authorized": item.authorization is not None,
                "terminal": None if item.terminal is None else item.terminal.status,
            }
        )
    order = {label: index for index, label in enumerate(CRITICAL_SEQUENCE)}
    return sorted(rows, key=lambda row: order[row["dispatch"]])


def run_canary(home: Path) -> dict:
    if home.exists():
        raise ValueError(f"canary DEEPREASON_HOME must be fresh: {home}")
    home.mkdir(parents=True)
    previous_home = os.environ.get("DEEPREASON_HOME")
    os.environ["DEEPREASON_HOME"] = str(home)
    calls: list[str] = []
    manifest = None
    harness = None
    try:
        config, policy = _config_and_policy()
        manifest = compile_run_manifest(
            config,
            schema_version=6,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
            control_plane_policy=_control(),
            criticism_policy=policy,
            run_input_digest="f" * 64,
        )
        harness = Harness(home / "stubbed-canary")
        _bind_classification(harness, manifest)
        harness.register_problem(
            Problem(
                id="pi-judge-canary",
                description="exercise one defended-trial criticism cycle",
                provenance=ProblemProvenance(trigger="seed", **{"from": []}),
            )
        )
        target = harness.create_artifact(
            TARGET,
            provenance=Provenance(role="conjecturer", school="school-0"),
        )
        target_status_before = harness.state.status[target.id].value
        target_formally_backed = formally_backed(harness, target.id)
        critic_response = json.dumps(
            {
                "cases": [
                    {"target_alias": "SRC_001", "attack": True, "case": CASE}
                ]
            }
        )
        routes = manifest.roles
        endpoints = {
            "conjecturer": _endpoint(
                routes["conjecturer"][0],
                "conjecturer[0]",
                calls,
                json.dumps(
                    {"candidates": [{"content": TARGET, "typicality": 0.5}]}
                ),
            ),
            "argumentative_critic": [
                _endpoint(
                    routes["argumentative_critic"][0],
                    "argumentative_critic[0]",
                    calls,
                    critic_response,
                )
            ],
            "defender": [
                _endpoint(
                    routes["defender"][0],
                    "defender[0]",
                    calls,
                    json.dumps({"answer": DEFENCE}),
                )
            ],
            "judge": [
                _endpoint(
                    route,
                    f"judge[{seat}]",
                    calls,
                    json.dumps(
                        {"verdict": "fail", "decisive_point": DECISIVE_POINT}
                    ),
                )
                for seat, route in enumerate(routes["judge"])
            ],
        }
        adapter = LLMAdapter(
            endpoints,
            harness.blobs,
            retry_max=0,
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
            transaction_authority_required=True,
            meter=TokenMeter(1_000_000),
        )
        Scheduler(
            harness,
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        ).step()
        critical = [call for call in calls if call in CRITICAL_SEQUENCE]
        return {
            "manifest_sha256": manifest.sha256,
            "policy_authority": manifest.criticism_policy.authority,
            "trial_contracts": {
                f"{entry.role}[{entry.seat}]": sorted(
                    grant.contract_id for grant in entry.contracts
                )
                for entry in manifest.route_seat_behavioral_capability_plan.entries
                if entry.role in {"defender", "judge"}
            },
            "provider_calls": calls,
            "critical_sequence": critical,
            "typed_work": _typed_work(harness),
            "target_status_before": target_status_before,
            "target_formally_backed": target_formally_backed,
            "target_status": harness.state.status[target.id].value,
            "first_refusal": None,
        }
    except TYPED_REFUSALS as error:
        return {
            "manifest_sha256": None if manifest is None else manifest.sha256,
            "provider_calls": calls,
            "critical_sequence": [call for call in calls if call in CRITICAL_SEQUENCE],
            "typed_work": [] if harness is None else _typed_work(harness),
            "first_refusal": str(error),
            "first_refusal_type": type(error).__name__,
        }
    finally:
        if previous_home is None:
            os.environ.pop("DEEPREASON_HOME", None)
        else:
            os.environ["DEEPREASON_HOME"] = previous_home


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path)
    args = parser.parse_args()
    if args.home is not None:
        result = run_canary(args.home)
    else:
        with tempfile.TemporaryDirectory(prefix="deepreason-judge-canary-") as directory:
            result = run_canary(Path(directory) / "home")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
