"""Qualification doctor for exact RunManifest-v6 production contracts."""

from __future__ import annotations

import json

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    _production_probe_contract,
    _admit_production_probe_output,
    _is_scope_violation,
    exercise_production_contract_case,
    production_contract_pairs,
    run_production_contract_doctor,
)
from deepreason.cli.main import main
from deepreason.config import BridgeConfig, Config
from deepreason.llm.endpoints import MockEndpoint
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    ScratchAuthoringPolicyV1,
    SchoolExecutionPolicyV1,
    compile_run_manifest,
    write_run_manifest,
)


STAMP = "2026-07-17T00:00:00Z"


def _route(name: str) -> dict:
    return {
        "endpoint_id": name,
        "endpoint": f"mock://{name}",
        "model": f"offline-{name}",
        "provider": "mock",
        "family": f"family-{name}",
        "max_tokens": 64,
    }


def _manifest(
    *,
    schema_version: int = 6,
    scratch_authoring: bool = False,
    grounding_review: bool = True,
    grounding_repair_attempts: int = 4,
    schema_repair_attempts: int = 2,
):
    roles = {
        "conjecturer": _route("conjecturer"),
        "argumentative_critic": _route("critic"),
        "summarizer": _route("ledger"),
        "thesis": _route("composer"),
        "judge": _route("reviewer"),
    }
    if scratch_authoring:
        roles["synthesizer"] = _route("scratch-link")
    config = Config(
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
    manifest = _manifest(schema_repair_attempts=0)
    result, calls = _exercise_grounding_verdict_case(
        monkeypatch,
        manifest,
        [json.dumps({"finding": "supported", "retry_max": 2})],
    )

    assert manifest.bridge_policy.max_schema_repair_attempts == 0
    assert result.eventual_valid is False
    assert result.repair_count == 0
    assert len(calls) == 1


def test_doctor_one_ceiling_allows_exactly_one_successful_repair(monkeypatch):
    manifest = _manifest(schema_repair_attempts=1)
    result, calls = _exercise_grounding_verdict_case(
        monkeypatch,
        manifest,
        [
            _INVALID_BLANK_MESSAGE,
            _REMOVE_INVALID_MESSAGE,
        ],
    )

    assert manifest.bridge_policy.max_schema_repair_attempts == 1
    assert result.eventual_valid is True
    assert result.first_pass_valid is False
    assert result.repair_count == 1
    assert len(calls) == 2


def test_doctor_one_ceiling_does_not_issue_second_required_repair(monkeypatch):
    manifest = _manifest(schema_repair_attempts=1)
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
    manifest = _manifest(schema_repair_attempts=2)
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
    manifest = _manifest(schema_repair_attempts=0)
    result, calls = _exercise_grounding_verdict_case(
        monkeypatch,
        manifest,
        [_VALID_GROUNDING_VERDICT],
    )

    assert result.first_pass_valid is True
    assert result.eventual_valid is True
    assert result.repair_count == 0
    assert len(calls) == 1


def test_matrix_preserves_core_pairs_and_adds_enabled_grounding_pairs():
    manifest = _manifest()
    pairs = production_contract_pairs(manifest)
    assert [(item.contract_id, item.role, item.seat) for item in pairs] == [
        ("batch-critic.v2", "argumentative_critic", 0),
        ("bridge.composition.v2", "thesis", 0),
        ("bridge.ledger.v3", "summarizer", 0),
        ("conjecturer.turn.v6", "conjecturer", 0),
        ("groundingrepairwirev1.direct.v1", "judge", 0),
        ("groundingverdictwirev1.direct.v1", "judge", 0),
    ]
    assert all(item.pair_id.startswith("sha256:") for item in pairs)
    assert all(len(item.route_sha256) == 64 for item in pairs)


def test_report_computes_19_of_20_gate_and_all_metrics():
    manifest = _manifest()
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _case(index),
    )
    assert report.summary.pair_count == 6
    assert report.summary.case_count == 120
    assert report.summary.eventual_valid_count == 114
    assert report.summary.first_pass_valid_count == 108
    assert report.summary.repair_count == 6
    assert report.summary.semantic_admission_count == 114
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
        ("bridge.composition.v2", "thesis", 0),
        ("bridge.ledger.v3", "summarizer", 0),
        ("conjecturer.turn.v6", "conjecturer", 0),
        ("groundingrepairwirev1.direct.v1", "judge", 0),
        ("groundingverdictwirev1.direct.v1", "judge", 0),
        ("scratch.block.compact.v1", "conjecturer", 0),
        ("scratch.cluster-guide.compact.v1", "summarizer", 0),
        ("scratch.link.compact.v1", "synthesizer", 0),
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
        "scratch.link.compact.v1",
        "scratch.cluster-guide.compact.v1",
    ):
        prompt = probes[contract_id][1].lower()
        assert "scratch" in prompt
        assert "advisory" in prompt or "non-authoritative" in prompt

    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _case(index),
    )
    assert report.summary.pair_count == 9
    assert report.summary.case_count == 180
    assert all(len(item.cases) == 20 for item in report.pairs)
    assert all(
        [case.case_id for case in item.cases]
        == [f"case-{index:03d}" for index in range(1, 21)]
        for item in report.pairs
    )


def test_disabled_optional_families_are_omitted_instead_of_probed():
    no_grounding = production_contract_pairs(
        _manifest(grounding_review=False)
    )
    assert [item.contract_id for item in no_grounding] == [
        "batch-critic.v2",
        "bridge.composition.v2",
        "bridge.ledger.v3",
        "conjecturer.turn.v6",
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
