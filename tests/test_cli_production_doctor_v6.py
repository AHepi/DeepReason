"""Qualification doctor for exact RunManifest-v6 production contracts."""

from __future__ import annotations

import json

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    ProductionContractDoctorReportV1,
    _admit_production_probe_output,
    _contract_schema_repair_grant,
    _is_scope_violation,
    _pair_report,
    _production_probe_contract,
    exercise_production_contract_case,
    load_production_contract_report,
    production_contract_pairs,
    run_production_contract_doctor,
    validate_production_contract_qualification,
    write_production_contract_report,
)
from deepreason.cli.main import main
from deepreason.config import BridgeConfig, Config
from deepreason.harness import Harness
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    RunManifest,
    RunManifestError,
    ScratchAuthoringPolicyV1,
    SchoolExecutionPolicyV1,
    compile_run_manifest,
    write_run_manifest,
)
from deepreason.workflow.transaction_service import InquiryTransactionService


STAMP = "2026-07-17T00:00:00Z"


def _route(
    name: str,
    *,
    model_profile: str | None = None,
    qualified_capacity: bool = True,
) -> dict:
    route = {
        "endpoint_id": name,
        "endpoint": f"mock://{name}",
        "model": f"offline-{name}",
        "provider": "mock",
        "family": f"family-{name}",
        "max_tokens": 64,
    }
    if qualified_capacity:
        route["context_window_tokens"] = 262_144
    if model_profile is not None:
        route["model_profile"] = model_profile
    return route


def _manifest(
    *,
    schema_version: int = 6,
    scratch_authoring: bool = False,
    grounding_review: bool = True,
    grounding_repair_attempts: int = 4,
    schema_repair_attempts: int = 2,
    shared_schema_repair_attempts: int = 2,
    route_profiles: dict[str, str] | None = None,
    qualified_capacity: bool = True,
):
    route_profiles = route_profiles or {}
    roles = {
        "conjecturer": _route(
            "conjecturer", model_profile=route_profiles.get("conjecturer"),
            qualified_capacity=qualified_capacity,
        ),
        "argumentative_critic": _route(
            "critic", model_profile=route_profiles.get("argumentative_critic"),
            qualified_capacity=qualified_capacity,
        ),
        "summarizer": _route(
            "ledger", model_profile=route_profiles.get("summarizer"),
            qualified_capacity=qualified_capacity,
        ),
        "thesis": _route(
            "composer", model_profile=route_profiles.get("thesis"),
            qualified_capacity=qualified_capacity,
        ),
        "judge": _route(
            "reviewer", model_profile=route_profiles.get("judge"),
            qualified_capacity=qualified_capacity,
        ),
    }
    if scratch_authoring:
        roles["synthesizer"] = _route(
            "scratch-link", qualified_capacity=qualified_capacity
        )
    config = Config(
        RETRY_MAX=shared_schema_repair_attempts,
        roles=roles,
        scratchpad={"enabled": scratch_authoring},
        bridge=BridgeConfig(
            mode="grounded_two_stage",
            grounding_review=grounding_review,
            max_schema_repair_attempts=schema_repair_attempts,
            max_grounding_repair_attempts=grounding_repair_attempts,
        ),
    )
    if schema_version != 6:
        return compile_run_manifest(
            config,
            schema_version=schema_version,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
        )
    control = ControlPlanePolicyV3(
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
        scratch_authoring=(
            ScratchAuthoringPolicyV1(
                enabled=True,
                maximum_new_blocks_per_turn=2,
                maximum_revisions_per_turn=2,
                maximum_links_per_turn=2,
                maximum_unresolved_questions_per_turn=2,
                maximum_cluster_suggestions_per_turn=2,
                maximum_total_bytes=64 * 1024,
            )
            if scratch_authoring
            else ScratchAuthoringPolicyV1()
        ),
    )
    return compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
        run_input_digest="f" * 64,
    )


def _with_contract_grant(
    manifest: RunManifest,
    contract_id: str,
    repairs: int,
) -> RunManifest:
    payload = json.loads(manifest.canonical_bytes())
    grant = next(
        grant
        for grant in payload["contract_schema_repair_policy"]["grants"]
        if grant["contract_id"] == contract_id
    )
    grant["maximum_schema_repairs"] = repairs
    grant["maximum_provider_calls"] = repairs + 1
    for entry in payload["route_seat_behavioral_capability_plan"]["entries"]:
        for behavioral in entry["contracts"]:
            if behavioral["contract_id"] == contract_id:
                behavioral["schema_repair"] = dict(grant)
    return RunManifest.model_validate(payload)


def _without_repair_authority(
    manifest: RunManifest,
    *,
    contract_id: str | None = None,
) -> RunManifest:
    payload = json.loads(manifest.canonical_bytes())
    if contract_id is None:
        payload.pop("contract_schema_repair_policy")
    else:
        policy = payload["contract_schema_repair_policy"]
        policy["grants"] = [
            grant
            for grant in policy["grants"]
            if grant["contract_id"] != contract_id
        ]
    # Historical documents lacking the behavioral plan remain readable, but
    # neither a missing repair policy nor a partial policy can gain doctor
    # authority through inference.
    payload.pop("route_seat_behavioral_capability_plan")
    return RunManifest.model_validate(payload)


def _admitted_case(case_index: int, *, repairs: int = 0):
    return ProductionContractCaseResultV1(
        case_id=f"case-{case_index + 1:03d}",
        first_pass_valid=repairs == 0,
        eventual_valid=True,
        repair_count=repairs,
        semantic_admission=True,
    )


def _case(case_index: int, *, alias_failure: bool = False):
    eventual = case_index < 19
    repaired = eventual and (case_index == 1 or alias_failure)
    return ProductionContractCaseResultV1(
        case_id=f"case-{case_index + 1:03d}",
        first_pass_valid=eventual and not repaired,
        eventual_valid=eventual,
        repair_count=1 if repaired else 0,
        alias_failures=1 if alias_failure else 0,
        scope_violations=0,
        semantic_admission=eventual,
        failure_code=None if eventual else "SCHEMA_EXHAUSTED",
    )


def _exercise_grounding_verdict_case(monkeypatch, manifest, responses):
    calls = []
    scripted = iter(responses)

    def respond(prompt):
        calls.append(prompt)
        return next(scripted)

    route = manifest.roles["judge"][0]
    endpoint = MockEndpoint(
        respond,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    monkeypatch.setattr(
        "deepreason.llm.adapter._endpoint_from_spec",
        lambda _spec: endpoint,
    )
    pair = next(
        item
        for item in production_contract_pairs(manifest)
        if item.contract_id == "groundingverdictwirev1.direct.v1"
    )
    result = exercise_production_contract_case(manifest, pair, 0)
    return result, calls


_VALID_GROUNDING_VERDICT = json.dumps({"finding": "supported"})
_INVALID_BLANK_MESSAGE = json.dumps({"finding": "supported", "message": ""})
_STILL_INVALID_MESSAGE_PATCH = json.dumps(
    {
        "schema": "repair.patch.v1",
        "op": "replace",
        "path": "/message",
        "value": "",
    }
)
_REMOVE_INVALID_MESSAGE = json.dumps(
    {"schema": "repair.patch.v1", "op": "remove", "path": "/message"}
)


def test_doctor_zero_ceiling_rejects_initial_invalid_without_repair(
    monkeypatch,
):
    manifest = _with_contract_grant(
        _manifest(schema_repair_attempts=2),
        "groundingverdictwirev1.direct.v1",
        0,
    )
    result, calls = _exercise_grounding_verdict_case(
        monkeypatch,
        manifest,
        [json.dumps({"finding": "supported", "retry_max": 2})],
    )

    pair = next(
        pair
        for pair in production_contract_pairs(manifest)
        if pair.contract_id == "groundingverdictwirev1.direct.v1"
    )
    assert manifest.bridge_policy.max_schema_repair_attempts == 2
    assert _contract_schema_repair_grant(manifest, pair).maximum_schema_repairs == 0
    assert result.eventual_valid is False
    assert result.repair_count == 0
    assert len(calls) == 1


def test_doctor_one_ceiling_allows_exactly_one_successful_repair(monkeypatch):
    manifest = _with_contract_grant(
        _manifest(schema_repair_attempts=0),
        "groundingverdictwirev1.direct.v1",
        1,
    )
    result, calls = _exercise_grounding_verdict_case(
        monkeypatch,
        manifest,
        [
            _INVALID_BLANK_MESSAGE,
            _REMOVE_INVALID_MESSAGE,
        ],
    )

    assert manifest.bridge_policy.max_schema_repair_attempts == 0
    assert result.eventual_valid is True
    assert result.first_pass_valid is False
    assert result.repair_count == 1
    assert len(calls) == 2


def test_doctor_one_ceiling_does_not_issue_second_required_repair(monkeypatch):
    manifest = _with_contract_grant(
        _manifest(schema_repair_attempts=2),
        "groundingverdictwirev1.direct.v1",
        1,
    )
    result, calls = _exercise_grounding_verdict_case(
        monkeypatch,
        manifest,
        [
            _INVALID_BLANK_MESSAGE,
            _STILL_INVALID_MESSAGE_PATCH,
            _REMOVE_INVALID_MESSAGE,
        ],
    )

    assert result.eventual_valid is False
    assert result.repair_count == 1
    assert len(calls) == 2


def test_doctor_two_ceiling_allows_second_required_repair(monkeypatch):
    manifest = _with_contract_grant(
        _manifest(schema_repair_attempts=0),
        "groundingverdictwirev1.direct.v1",
        2,
    )
    result, calls = _exercise_grounding_verdict_case(
        monkeypatch,
        manifest,
        [
            _INVALID_BLANK_MESSAGE,
            _STILL_INVALID_MESSAGE_PATCH,
            _REMOVE_INVALID_MESSAGE,
        ],
    )

    assert result.eventual_valid is True
    assert result.first_pass_valid is False
    assert result.repair_count == 2
    assert len(calls) == 3


def test_doctor_valid_initial_response_consumes_no_repairs(monkeypatch):
    manifest = _with_contract_grant(
        _manifest(schema_repair_attempts=2),
        "groundingverdictwirev1.direct.v1",
        0,
    )
    result, calls = _exercise_grounding_verdict_case(
        monkeypatch,
        manifest,
        [_VALID_GROUNDING_VERDICT],
    )

    assert result.first_pass_valid is True
    assert result.eventual_valid is True
    assert result.repair_count == 0
    assert len(calls) == 1


def test_doctor_preserves_different_contract_grants_in_one_manifest():
    manifest = _with_contract_grant(
        _manifest(
            scratch_authoring=True,
            schema_repair_attempts=0,
            shared_schema_repair_attempts=2,
        ),
        "groundingverdictwirev1.direct.v1",
        1,
    )
    expected_repairs = {
        "batch-critic.v2": 2,
        "bridge.composition-batch.v1": 0,
        "bridge.composition.v2": 0,
        "bridge.ledger-batch.v1": 0,
        "bridge.ledger.v3": 0,
        "conjecturer.atomic-candidate.v1": 2,
        "conjecturer.turn.v6": 2,
        "critic.atomic-target.v1": 2,
        "groundingrepairwirev1.direct.v1": 0,
        "groundingverdictwirev1.direct.v1": 1,
        "scratch.block.compact.v1": 2,
        "scratch.block.minimal.v1": 2,
        "scratch.cluster-guide.compact.v1": 2,
        "scratch.cluster-guide.minimal.v1": 2,
        "scratch.link.compact.v1": 2,
        "scratch.link.minimal.v1": 2,
    }
    observed = {}

    def execute(bound_manifest, pair, case_index):
        grant = _contract_schema_repair_grant(bound_manifest, pair)
        observed[pair.contract_id] = grant.maximum_schema_repairs
        return _admitted_case(
            case_index,
            repairs=expected_repairs[pair.contract_id],
        )

    report = run_production_contract_doctor(manifest, case_executor=execute)

    assert observed == expected_repairs
    assert report.summary.qualified is True
    assert report.summary.repair_count == 20 * sum(expected_repairs.values())


def test_doctor_and_runtime_resolve_identical_exact_contract_grants(tmp_path):
    manifest = _with_contract_grant(
        _manifest(
            scratch_authoring=True,
            schema_repair_attempts=0,
            shared_schema_repair_attempts=2,
        ),
        "groundingverdictwirev1.direct.v1",
        1,
    )
    runtime = InquiryTransactionService(
        Harness(tmp_path / "runtime-grants"),
        manifest,
        TokenMeter(),
    )

    for pair in production_contract_pairs(manifest):
        doctor_grant = _contract_schema_repair_grant(manifest, pair)
        assert runtime.resolve_schema_repair_grant(pair.contract_id) == doctor_grant


@pytest.mark.parametrize("missing_contract", (None, "bridge.ledger.v3"))
def test_missing_policy_or_active_grant_fails_before_case_execution(
    missing_contract,
):
    manifest = _without_repair_authority(
        _manifest(),
        contract_id=missing_contract,
    )
    calls = []

    with pytest.raises(RunManifestError) as caught:
        run_production_contract_doctor(
            manifest,
            case_executor=lambda _manifest, _pair, index: (
                calls.append(index) or _admitted_case(index)
            ),
        )

    assert calls == []
    assert caught.value.code == "DOCTOR_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED"
    assert caught.value.pointer == "/route_seat_behavioral_capability_plan"


def test_offline_executor_cannot_claim_more_repairs_than_manifest_grant():
    manifest = _with_contract_grant(
        _manifest(),
        "batch-critic.v2",
        0,
    )
    calls = []

    def overclaim(_manifest, pair, case_index):
        calls.append((pair.contract_id, case_index))
        return _admitted_case(case_index, repairs=1)

    with pytest.raises(RunManifestError) as caught:
        run_production_contract_doctor(manifest, case_executor=overclaim)

    assert calls == [("batch-critic.v2", 0)]
    assert caught.value.code == "DOCTOR_CONTRACT_REPAIR_GRANT_EXCEEDED"
    assert caught.value.pointer == "/contract_schema_repair_policy/grants"


def test_constructed_contract_mismatch_fails_before_provider_execution(
    monkeypatch,
):
    manifest = _manifest()
    pairs = production_contract_pairs(manifest)
    review_pair = next(
        pair
        for pair in pairs
        if pair.contract_id == "groundingverdictwirev1.direct.v1"
    )
    conjecture_pair = next(
        pair for pair in pairs if pair.contract_id == "conjecturer.turn.v6"
    )
    wrong_contract, request = _production_probe_contract(
        manifest,
        conjecture_pair,
        0,
    )
    endpoint_calls = []
    monkeypatch.setattr(
        "deepreason.cli.doctor._production_probe_contract",
        lambda _manifest, _pair, _index: (wrong_contract, request),
    )
    monkeypatch.setattr(
        "deepreason.llm.adapter._endpoint_from_spec",
        lambda _spec: endpoint_calls.append(True),
    )

    with pytest.raises(RunManifestError) as caught:
        exercise_production_contract_case(manifest, review_pair, 0)

    assert caught.value.code == "DOCTOR_PRODUCTION_CONTRACT_MISMATCH"
    assert endpoint_calls == []


def test_matrix_preserves_core_pairs_and_adds_enabled_grounding_pairs():
    manifest = _manifest()
    pairs = production_contract_pairs(manifest)
    assert [(item.contract_id, item.role, item.seat) for item in pairs] == [
        ("batch-critic.v2", "argumentative_critic", 0),
        ("bridge.composition-batch.v1", "thesis", 0),
        ("bridge.composition.v2", "thesis", 0),
        ("bridge.ledger-batch.v1", "summarizer", 0),
        ("bridge.ledger.v3", "summarizer", 0),
        ("conjecturer.atomic-candidate.v1", "conjecturer", 0),
        ("conjecturer.turn.v6", "conjecturer", 0),
        ("critic.atomic-target.v1", "argumentative_critic", 0),
        ("groundingrepairwirev1.direct.v1", "judge", 0),
        ("groundingverdictwirev1.direct.v1", "judge", 0),
    ]
    assert all(item.pair_id.startswith("sha256:") for item in pairs)
    assert all(len(item.route_sha256) == 64 for item in pairs)


def test_doctor_pairs_are_exact_projection_of_behavioral_plan():
    manifest = _manifest(scratch_authoring=True)
    expected = sorted(
        (
            contract.contract_id,
            entry.role,
            entry.seat,
            entry.endpoint_id,
            entry.route_sha256,
        )
        for entry in manifest.route_seat_behavioral_capability_plan.entries
        for contract in entry.contracts
    )
    actual = [
        (
            pair.contract_id,
            pair.role,
            pair.seat,
            pair.endpoint_id,
            pair.route_sha256,
        )
        for pair in production_contract_pairs(manifest)
    ]
    assert actual == expected


def test_doctor_requires_complete_route_envelope_before_scripted_case():
    manifest = _manifest(qualified_capacity=False)
    calls = []

    with pytest.raises(
        RunManifestError, match="DOCTOR_REQUEST_ENVELOPE_CAPACITY_REQUIRED"
    ):
        run_production_contract_doctor(
            manifest,
            case_executor=lambda _manifest, _pair, index: (
                calls.append(index) or _admitted_case(index)
            ),
        )

    assert calls == []


def test_report_computes_19_of_20_gate_and_all_metrics():
    manifest = _manifest()
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _case(index),
    )
    assert report.summary.pair_count == 10
    assert report.summary.case_count == 200
    assert report.summary.eventual_valid_count == 190
    assert report.summary.first_pass_valid_count == 180
    assert report.summary.repair_count == 10
    assert report.summary.semantic_admission_count == 190
    assert report.summary.alias_failures == 0
    assert report.summary.scope_violations == 0
    assert report.summary.qualified is True
    assert all(item.qualified for item in report.pairs)


def test_alias_or_scope_violation_fails_gate_even_with_eventual_admission():
    manifest = _manifest()
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, pair, index: _case(
            index,
            alias_failure=(pair.contract_id == "conjecturer.turn.v6" and index == 0),
        ),
    )
    assert report.summary.alias_failures == 1
    assert report.summary.qualified is False
    conjecturer = next(
        item
        for item in report.pairs
        if item.pair.contract_id == "conjecturer.turn.v6"
    )
    assert conjecturer.eventual_valid_count == 19
    assert conjecturer.qualified is False


def test_cli_writes_deterministic_report_and_keeps_legacy_doctor_mode(
    tmp_path, monkeypatch, capsys
):
    manifest = _manifest()
    manifest_path = tmp_path / "run-manifest.json"
    output = tmp_path / "qualification.json"
    write_run_manifest(manifest, manifest_path)

    monkeypatch.setattr(
        "deepreason.cli.doctor.exercise_production_contract_case",
        lambda _manifest, _pair, index: _case(index),
    )
    argv = [
        "doctor",
        "--run-manifest",
        str(manifest_path),
        "--production-contracts",
        "--out",
        str(output),
    ]
    assert main(argv) == 0
    first = output.read_bytes()
    payload = json.loads(first)
    assert payload["schema"] == "deepreason-production-contract-doctor-v1"
    assert payload["run_manifest_sha256"] == manifest.sha256
    assert payload["summary"]["qualified"] is True
    assert json.loads(capsys.readouterr().out) == payload

    assert main(argv) == 0
    assert output.read_bytes() == first


def test_cli_production_mode_fails_closed_without_complete_arguments(
    tmp_path, capsys
):
    output = tmp_path / "qualification.json"
    assert main(["doctor", "--run-manifest", "missing.json", "--out", str(output)]) == 1
    assert "DOCTOR_PRODUCTION_ARGUMENTS_REQUIRED" in capsys.readouterr().err
    assert not output.exists()



def test_cli_writes_failed_gate_report_and_returns_nonzero(tmp_path, monkeypatch):
    manifest = _manifest()
    manifest_path = tmp_path / "run-manifest.json"
    output = tmp_path / "qualification.json"
    write_run_manifest(manifest, manifest_path)
    monkeypatch.setattr(
        "deepreason.cli.doctor.exercise_production_contract_case",
        lambda _manifest, pair, index: _case(
            index,
            alias_failure=(
                pair.contract_id == "conjecturer.turn.v6" and index == 0
            ),
        ),
    )

    assert main(
        [
            "doctor",
            "--run-manifest",
            str(manifest_path),
            "--production-contracts",
            "--out",
            str(output),
        ]
    ) == 1
    assert (
        json.loads(output.read_text(encoding="utf-8"))["summary"]["qualified"]
        is False
    )

def test_cli_production_mode_rejects_non_v6_without_output(tmp_path, capsys):
    manifest = _manifest(schema_version=3)
    manifest_path = tmp_path / "run-manifest.json"
    output = tmp_path / "qualification.json"
    write_run_manifest(manifest, manifest_path)
    assert main(
        [
            "doctor",
            "--run-manifest",
            str(manifest_path),
            "--production-contracts",
            "--out",
            str(output),
        ]
    ) == 1
    assert "DOCTOR_RUN_MANIFEST_V6_REQUIRED" in capsys.readouterr().err
    assert not output.exists()


def test_cli_rejects_mixing_endpoint_and_manifest_doctor_modes(tmp_path, capsys):
    manifest = _manifest()
    manifest_path = tmp_path / "run-manifest.json"
    output = tmp_path / "qualification.json"
    write_run_manifest(manifest, manifest_path)
    assert main(
        [
            "doctor",
            "--endpoint",
            "mock://route",
            "--model",
            "model",
            "--run-manifest",
            str(manifest_path),
            "--production-contracts",
            "--out",
            str(output),
        ]
    ) == 1
    assert "DOCTOR_MODE_CONFLICT" in capsys.readouterr().err
    assert not output.exists()


def test_enabled_optional_pairs_have_exact_offline_probes_and_twenty_cases_each():
    manifest = _manifest(scratch_authoring=True)
    pairs = production_contract_pairs(manifest)
    assert [(item.contract_id, item.role, item.seat) for item in pairs] == [
        ("batch-critic.v2", "argumentative_critic", 0),
        ("bridge.composition-batch.v1", "thesis", 0),
        ("bridge.composition.v2", "thesis", 0),
        ("bridge.ledger-batch.v1", "summarizer", 0),
        ("bridge.ledger.v3", "summarizer", 0),
        ("conjecturer.atomic-candidate.v1", "conjecturer", 0),
        ("conjecturer.turn.v6", "conjecturer", 0),
        ("critic.atomic-target.v1", "argumentative_critic", 0),
        ("groundingrepairwirev1.direct.v1", "judge", 0),
        ("groundingverdictwirev1.direct.v1", "judge", 0),
        ("scratch.block.compact.v1", "conjecturer", 0),
        ("scratch.block.minimal.v1", "conjecturer", 0),
        ("scratch.cluster-guide.compact.v1", "summarizer", 0),
        ("scratch.cluster-guide.minimal.v1", "summarizer", 0),
        ("scratch.link.compact.v1", "synthesizer", 0),
        ("scratch.link.minimal.v1", "synthesizer", 0),
    ]

    probes = {}
    for pair in pairs:
        contract, request = _production_probe_contract(manifest, pair, 0)
        assert contract.contract_id == pair.contract_id
        assert request
        probes[pair.contract_id] = (contract, request)

    assert set(probes["scratch.block.compact.v1"][0].aliases.aliases) == set()
    assert set(probes["scratch.link.compact.v1"][0].aliases.aliases) == {
        "SCR_001",
        "SCR_002",
    }
    assert set(
        probes["scratch.cluster-guide.compact.v1"][0].aliases.aliases
    ) == {"SCR_001", "SCR_002"}
    for contract_id in (
        "scratch.block.compact.v1",
        "scratch.block.minimal.v1",
        "scratch.link.compact.v1",
        "scratch.link.minimal.v1",
        "scratch.cluster-guide.compact.v1",
        "scratch.cluster-guide.minimal.v1",
    ):
        prompt = probes[contract_id][1].lower()
        assert "scratch" in prompt
        assert "advisory" in prompt or "non-authoritative" in prompt

    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _case(index),
    )
    assert report.summary.pair_count == 16
    assert report.summary.case_count == 320
    assert all(len(item.cases) == 20 for item in report.pairs)
    assert all(
        [case.case_id for case in item.cases]
        == [f"case-{index:03d}" for index in range(1, 21)]
        for item in report.pairs
    )


def test_doctor_probe_uses_each_pairs_exact_route_seat_base_profile(monkeypatch):
    manifest = _manifest(
        route_profiles={
            "summarizer": "frontier",
            "judge": "compact",
        }
    )
    observed = []

    def capture_prompt(role, *, profile, **_kwargs):
        observed.append((role, profile))
        return f"{role}:{profile}"

    monkeypatch.setattr("deepreason.llm.roles.render_role_prompt", capture_prompt)
    pairs = production_contract_pairs(manifest)
    ledger = next(item for item in pairs if item.contract_id == "bridge.ledger.v3")
    review = next(
        item
        for item in pairs
        if item.contract_id == "groundingverdictwirev1.direct.v1"
    )

    _production_probe_contract(manifest, ledger, 0)
    _production_probe_contract(manifest, review, 0)

    assert observed == [
        ("bridge_ledger", "frontier"),
        ("bridge_review", "compact"),
    ]


def test_disabled_optional_families_are_omitted_instead_of_probed():
    no_grounding = production_contract_pairs(
        _manifest(grounding_review=False)
    )
    assert [item.contract_id for item in no_grounding] == [
        "batch-critic.v2",
        "bridge.composition-batch.v1",
        "bridge.composition.v2",
        "bridge.ledger-batch.v1",
        "bridge.ledger.v3",
        "conjecturer.atomic-candidate.v1",
        "conjecturer.turn.v6",
        "critic.atomic-target.v1",
    ]

    review_only = production_contract_pairs(
        _manifest(grounding_review=True, grounding_repair_attempts=0)
    )
    review_contracts = {item.contract_id for item in review_only}
    assert "groundingverdictwirev1.direct.v1" in review_contracts
    assert "groundingrepairwirev1.direct.v1" not in review_contracts
    assert not any(contract.startswith("scratch.") for contract in review_contracts)



def test_grounding_repair_semantic_scope_fails_closed():
    manifest = _manifest()
    pair = next(
        item
        for item in production_contract_pairs(manifest)
        if item.contract_id == "groundingrepairwirev1.direct.v1"
    )
    contract, _request = _production_probe_contract(manifest, pair, 0)
    output = contract.compile(
        contract.validate_value(
            {
                "action": "correct_wording",
                "replacement_text": "A schema-valid but unauthorized edit.",
            }
        )
    )
    with pytest.raises(ValueError) as caught:
        _admit_production_probe_output(pair, output)
    assert _is_scope_violation(caught.value)


def _qualified_report(manifest):
    return run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _case(index),
    )


def test_persisted_report_round_trip_loads_deterministically_and_qualifies(
    tmp_path,
):
    manifest = _manifest(
        scratch_authoring=True,
        route_profiles={
            "conjecturer": "compact",
            "summarizer": "frontier",
            "judge": "compact",
        },
    )
    report = _qualified_report(manifest)
    target = tmp_path / "production-contract-report.json"

    assert write_production_contract_report(report, target) == target
    first = load_production_contract_report(target)
    second = load_production_contract_report(str(target))

    assert first == second == report
    assert first is not report
    assert validate_production_contract_qualification(first, manifest) is first
    assert tuple(item.pair for item in first.pairs) == production_contract_pairs(
        manifest
    )
    assert target.read_bytes().endswith(b"\n")
    assert not target.read_bytes().endswith(b"\n\n")


def test_report_loader_distinguishes_missing_symlink_and_nonregular_paths(
    tmp_path,
):
    missing = tmp_path / "missing.json"
    with pytest.raises(RunManifestError) as caught:
        load_production_contract_report(missing)
    assert caught.value.code == "DOCTOR_REPORT_MISSING"

    report = _qualified_report(_manifest())
    regular = tmp_path / "regular.json"
    write_production_contract_report(report, regular)
    link = tmp_path / "linked.json"
    link.symlink_to(regular)
    with pytest.raises(RunManifestError) as caught:
        load_production_contract_report(link)
    assert caught.value.code == "DOCTOR_REPORT_UNSAFE"

    directory = tmp_path / "directory.json"
    directory.mkdir()
    with pytest.raises(RunManifestError) as caught:
        load_production_contract_report(directory)
    assert caught.value.code == "DOCTOR_REPORT_UNSAFE"


def test_report_loader_rejects_oversized_input_before_json_parsing(tmp_path):
    target = tmp_path / "oversized.json"
    target.write_bytes(b"{" + b" " * (4 * 1024 * 1024))

    with pytest.raises(RunManifestError) as caught:
        load_production_contract_report(target)

    assert caught.value.code == "DOCTOR_REPORT_TOO_LARGE"


@pytest.mark.parametrize(
    ("payload_factory", "expected_code"),
    (
        (lambda _report, _raw: b"{not-json}\n", "DOCTOR_REPORT_INVALID"),
        (
            lambda _report, _raw: (
                b'{"schema":"deepreason-production-contract-doctor-v1",'
                b'"schema":"deepreason-production-contract-doctor-v1"}\n'
            ),
            "DOCTOR_REPORT_INVALID",
        ),
        (
            lambda report, _raw: (
                json.dumps(
                    {
                        **report.model_dump(mode="json", by_alias=True),
                        "unknown": True,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
                + b"\n"
            ),
            "DOCTOR_REPORT_INVALID",
        ),
        (
            lambda report, _raw: (
                json.dumps(
                    report.model_dump(mode="json", by_alias=True),
                    indent=2,
                ).encode()
                + b"\n"
            ),
            "DOCTOR_REPORT_NONCANONICAL",
        ),
        (lambda _report, raw: raw.removesuffix(b"\n"), "DOCTOR_REPORT_NONCANONICAL"),
        (lambda _report, raw: raw + b"\n", "DOCTOR_REPORT_NONCANONICAL"),
    ),
    ids=(
        "malformed",
        "duplicate-key",
        "unknown-field",
        "noncanonical-whitespace",
        "missing-newline",
        "extra-newline",
    ),
)
def test_report_loader_rejects_invalid_or_noncanonical_bytes(
    tmp_path,
    payload_factory,
    expected_code,
):
    report = _qualified_report(_manifest())
    canonical_path = tmp_path / "canonical.json"
    write_production_contract_report(report, canonical_path)
    target = tmp_path / "candidate.json"
    target.write_bytes(payload_factory(report, canonical_path.read_bytes()))

    with pytest.raises(RunManifestError) as caught:
        load_production_contract_report(target)

    assert caught.value.code == expected_code
    assert "conjecturer.turn.v6" not in str(caught.value)


def test_qualification_rejects_manifest_and_route_seat_plan_mismatch():
    manifest = _manifest()
    report = _qualified_report(manifest)
    changed = _manifest(route_profiles={"judge": "compact"})

    assert changed.sha256 != manifest.sha256
    with pytest.raises(RunManifestError) as caught:
        validate_production_contract_qualification(report, changed)

    assert caught.value.code == "DOCTOR_REPORT_MANIFEST_MISMATCH"
    assert caught.value.pointer == "/run_manifest_sha256"


def test_qualification_rejects_report_manifest_digest_mismatch():
    manifest = _manifest()
    qualified = _qualified_report(manifest)
    report = qualified.model_copy(
        update={"run_manifest_sha256": "0" * 64}
    )

    with pytest.raises(RunManifestError) as caught:
        validate_production_contract_qualification(report, manifest)

    assert caught.value.code == "DOCTOR_REPORT_MANIFEST_MISMATCH"

    wrong_version = qualified.model_copy(
        update={"run_manifest_schema_version": 5}
    )
    with pytest.raises(RunManifestError) as caught:
        validate_production_contract_qualification(wrong_version, manifest)
    assert caught.value.code == "DOCTOR_REPORT_SCHEMA_VERSION_MISMATCH"


@pytest.mark.parametrize(
    "mutation",
    (
        "missing",
        "added",
        "reordered",
        "role",
        "seat",
        "endpoint",
        "route",
        "contract",
        "model",
        "revision",
        "provider",
        "family",
        "output-mechanism",
    ),
)
def test_qualification_rejects_inexact_pair_inventory(mutation):
    manifest = _manifest()
    report = _qualified_report(manifest)
    reports = list(report.pairs)
    if mutation == "missing":
        reports.pop()
    elif mutation == "added":
        reports.append(reports[0])
    elif mutation == "reordered":
        reports.reverse()
    else:
        pair = reports[0].pair
        updates = {
            "role": {"role": "conjecturer"},
            "seat": {"seat": pair.seat + 1},
            "endpoint": {"endpoint_id": pair.endpoint_id + "-foreign"},
            "route": {"route_sha256": "0" * 64},
            "contract": {"contract_id": "conjecturer.turn.v6"},
            "model": {"model_id": pair.model_id + "-foreign"},
            "revision": {"model_revision": "foreign-revision"},
            "provider": {"provider": pair.provider + "-foreign"},
            "family": {"family": pair.family + "-foreign"},
            "output-mechanism": {"output_mechanism": "grammar"},
        }[mutation]
        reports[0] = reports[0].model_copy(
            update={"pair": pair.model_copy(update=updates)}
        )
    altered = report.model_copy(update={"pairs": tuple(reports)})

    with pytest.raises(RunManifestError) as caught:
        validate_production_contract_qualification(altered, manifest)

    assert caught.value.code == "DOCTOR_REPORT_PAIR_INVENTORY_MISMATCH"


def test_qualification_rejects_case_exceeding_exact_manifest_grant():
    manifest = _with_contract_grant(_manifest(), "batch-critic.v2", 0)
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(index),
    )
    pair_index = next(
        index
        for index, item in enumerate(report.pairs)
        if item.pair.contract_id == "batch-critic.v2"
    )
    pair_report = report.pairs[pair_index]
    cases = list(pair_report.cases)
    cases[0] = _admitted_case(0, repairs=1)
    changed_pair = _pair_report(pair_report.pair, tuple(cases))
    pairs = list(report.pairs)
    pairs[pair_index] = changed_pair
    summary = report.summary.model_copy(
        update={
            "first_pass_valid_count": report.summary.first_pass_valid_count - 1,
            "repair_count": report.summary.repair_count + 1,
        }
    )
    altered = ProductionContractDoctorReportV1(
        run_manifest_sha256=manifest.sha256,
        pairs=tuple(pairs),
        summary=summary,
    )

    with pytest.raises(RunManifestError) as caught:
        validate_production_contract_qualification(altered, manifest)

    assert caught.value.code == "DOCTOR_REPORT_REPAIR_GRANT_EXCEEDED"


def test_qualification_rejects_unqualified_pair_and_false_summary():
    manifest = _manifest()
    unqualified = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, pair, index: _case(
            index,
            alias_failure=(
                pair.contract_id == "conjecturer.turn.v6" and index == 0
            ),
        ),
    )
    with pytest.raises(RunManifestError) as caught:
        validate_production_contract_qualification(unqualified, manifest)
    assert caught.value.code == "DOCTOR_REPORT_PAIR_UNQUALIFIED"

    qualified = _qualified_report(manifest)
    false_summary = qualified.model_copy(
        update={
            "summary": qualified.summary.model_copy(update={"qualified": False})
        }
    )
    with pytest.raises(RunManifestError) as caught:
        validate_production_contract_qualification(false_summary, manifest)
    assert caught.value.code == "DOCTOR_REPORT_SUMMARY_UNQUALIFIED"


def test_qualification_rejects_false_qualified_pair_count():
    manifest = _manifest()
    report = _qualified_report(manifest)
    altered = report.model_copy(
        update={
            "summary": report.summary.model_copy(
                update={
                    "qualified_pair_count": report.summary.qualified_pair_count - 1
                }
            )
        }
    )

    with pytest.raises(RunManifestError) as caught:
        validate_production_contract_qualification(altered, manifest)

    assert caught.value.code == "DOCTOR_REPORT_QUALIFIED_PAIR_COUNT_MISMATCH"


def test_loading_and_validation_never_construct_a_provider(tmp_path, monkeypatch):
    manifest = _manifest()
    report = _qualified_report(manifest)
    target = tmp_path / "offline-report.json"
    write_production_contract_report(report, target)
    monkeypatch.setattr(
        "deepreason.llm.adapter._endpoint_from_spec",
        lambda _spec: pytest.fail("loader or validator attempted provider setup"),
    )

    loaded = load_production_contract_report(target)

    assert validate_production_contract_qualification(loaded, manifest) == report


def test_qualification_requires_v6_manifest():
    report = _qualified_report(_manifest())

    with pytest.raises(RunManifestError) as caught:
        validate_production_contract_qualification(
            report,
            _manifest(schema_version=3),
        )

    assert caught.value.code == "DOCTOR_REPORT_MANIFEST_V6_REQUIRED"
