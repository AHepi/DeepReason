"""Deterministic route-seat classification from exact doctor evidence."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deepreason.application.models import derive_model_execution_summary
from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    ProductionContractDoctorReportV1,
    derive_route_seat_model_classification,
    run_production_contract_doctor,
    validate_production_contract_qualification,
)
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.report import eval_report
from deepreason.config import Config
from deepreason.run_manifest import RunManifestError, write_run_manifest
from tests.test_cli_production_doctor_v6 import _admitted_case, _manifest


def test_classification_is_exact_per_route_seat_and_deterministic():
    manifest = _manifest(
        route_profiles={
            "conjecturer": "compact",
            "argumentative_critic": "frontier",
            "summarizer": "standard",
        }
    )
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(index),
    )
    plan = report.route_seat_model_classification
    assert plan is not None
    assert plan.manifest_digest == manifest.sha256
    assert plan.algorithm == "exact-production-contract-qualification.v1"
    assert plan.algorithm_version == 1
    assert all(
        entry.selected_class == "qualified_exact_behavior"
        for entry in plan.entries
        if entry.authorized_contract_ids
    )
    assert tuple(
        (entry.role, entry.seat, entry.endpoint_id, entry.route_sha256)
        for entry in plan.entries
    ) == tuple(
        sorted(
            (entry.role, entry.seat, entry.endpoint_id, entry.route_sha256)
            for entry in plan.entries
        )
    )
    assert derive_route_seat_model_classification(
        manifest,
        pairs=report.pairs,
        summary=report.summary,
    ) == plan
    assert validate_production_contract_qualification(report, manifest) is report


def test_unqualified_exact_route_never_becomes_launch_authority():
    manifest = _manifest()

    def cases(_manifest, pair, index):
        if pair.role == "conjecturer":
            return ProductionContractCaseResultV1(
                case_id=f"case-{index + 1:03d}",
                first_pass_valid=False,
                eventual_valid=False,
                repair_count=0,
                semantic_admission=False,
                failure_code="SCHEMA_EXHAUSTED",
            )
        return _admitted_case(index)

    report = run_production_contract_doctor(manifest, case_executor=cases)
    plan = report.route_seat_model_classification
    assert plan is not None
    conjecturer = next(entry for entry in plan.entries if entry.role == "conjecturer")
    assert conjecturer.selected_class == "unqualified_exact_behavior"
    with pytest.raises(RunManifestError, match="DOCTOR_REPORT_PAIR_UNQUALIFIED"):
        validate_production_contract_qualification(report, manifest)


def test_classification_cannot_be_changed_without_changing_canonical_identity():
    manifest = _manifest()
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(index),
    )
    plan = report.route_seat_model_classification
    assert plan is not None
    changed_entry = plan.entries[0].model_copy(
        update={"selected_class": "unqualified_exact_behavior"}
    )
    forged = plan.model_copy(update={"entries": (changed_entry, *plan.entries[1:])})

    with pytest.raises(ValidationError, match="workflow record id"):
        ProductionContractDoctorReportV1.model_validate(
            {
                **report.model_dump(mode="json", by_alias=True),
                "route_seat_model_classification": forged.model_dump(
                    mode="json", by_alias=True
                ),
            }
        )


def test_validated_classification_binds_exactly_once_and_replays(tmp_path):
    manifest = _manifest()
    root = tmp_path / "classification-binding"
    write_run_manifest(manifest, root / "run-manifest.json")
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(index),
    )
    validate_production_contract_qualification(report, manifest)
    harness = Harness(root)

    binding = harness.bind_model_classification(manifest, report)
    assert harness.bind_model_classification(manifest, report) == binding
    assert sum(
        event.control is not None
        and event.control.action == "classification_bound"
        for event in harness.log.read()
    ) == 1

    reopened = Harness(root)
    assert reopened.workflow_state.route_seat_model_classification == (
        report.route_seat_model_classification
    )
    assert reopened.workflow_state.model_classification_binding == binding

    first = derive_model_execution_summary(harness, manifest)
    second = derive_model_execution_summary(reopened, manifest)
    assert first == second
    assert tuple(
        (item.role, item.seat, item.endpoint_id, item.route_sha256)
        for item in first.route_seat_model_classifications
    ) == tuple(
        (entry.role, entry.seat, entry.endpoint_id, entry.route_sha256)
        for entry in report.route_seat_model_classification.entries
    )
    assert {
        item.qualification_evidence_sha256
        for item in first.route_seat_model_classifications
    } == {report.route_seat_model_classification.qualification_evidence_sha256}
    assert {
        item.classification_plan_ref
        for item in first.route_seat_model_classifications
    } == {report.route_seat_model_classification.id}
    assert {
        item.classification_binding_ref
        for item in first.route_seat_model_classifications
    } == {binding.id}
    process = eval_report(reopened, Config())["process"]
    assert process["model_execution"] == first.model_dump(
        mode="json", by_alias=True
    )
    assert not any(
        item["check"] in {
            "model-classification-authority",
            "attempt-model-classification",
            "workflow-decision",
        }
        for item in verify_root(root)["violations"]
    )


def test_later_qualified_evidence_cannot_replace_bound_selection(tmp_path):
    manifest = _manifest()
    root = tmp_path / "classification-conflict"
    write_run_manifest(manifest, root / "run-manifest.json")
    initial = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(index),
    )
    changed = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(
            index, repairs=1
        ),
    )
    validate_production_contract_qualification(initial, manifest)
    validate_production_contract_qualification(changed, manifest)
    harness = Harness(root)
    harness.bind_model_classification(manifest, initial)
    before = tuple(harness.log.read())

    with pytest.raises(ValueError, match="classification authority already differs"):
        harness.bind_model_classification(manifest, changed)

    assert tuple(harness.log.read()) == before
