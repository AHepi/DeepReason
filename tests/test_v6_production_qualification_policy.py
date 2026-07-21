"""Frozen production-doctor qualification authority in new v6 manifests."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.ontology import Commitment
from deepreason.run_manifest import (
    ProductionQualificationPolicyV1,
    RunManifest,
    RunManifestError,
    bind_run_manifest,
    load_run_manifest,
    write_run_manifest,
)
from tests.test_run_input_v6_commitments import _bind_v2
from tests.test_run_manifest import _compile_v6_manifest
from tests.test_v6_contract_schema_repair_policy import _pre_v6_manifest


POLICY_PAYLOAD = {
    "schema": "production-qualification-policy.v1",
    "required": True,
    "report_schema": "deepreason-production-contract-doctor-v1",
    "report_filename": "production-contract-qualification.json",
    "manifest_binding": "exact_sha256",
    "pair_inventory": "exact_manifest_pairs",
    "pair_requirement": "all_qualified",
    "repair_authority": "exact_contract_grants",
    "enforcement_point": "before_provider_dispatch",
}


def _policy_payload(**changes) -> dict:
    return {**POLICY_PAYLOAD, **changes}


def test_new_v6_manifest_contains_exact_frozen_qualification_policy():
    manifest = _compile_v6_manifest()
    policy = manifest.production_qualification_policy

    assert isinstance(policy, ProductionQualificationPolicyV1)
    assert policy.model_dump(mode="json", by_alias=True) == POLICY_PAYLOAD
    assert tuple(policy.model_dump(mode="json", by_alias=True)) == tuple(POLICY_PAYLOAD)
    assert manifest.provider_fallback is False
    with pytest.raises(ValidationError):
        policy.required = False


@pytest.mark.parametrize(
    ("field", "invalid"),
    (
        ("schema", "production-qualification-policy.v2"),
        ("required", False),
        ("required", 1),
        ("report_schema", "deepreason-production-contract-doctor-v2"),
        ("report_filename", "other-report.json"),
        ("manifest_binding", "model_and_route"),
        ("pair_inventory", "configured_pairs"),
        ("pair_requirement", "some_qualified"),
        ("repair_authority", "doctor_default"),
        ("enforcement_point", "after_provider_dispatch"),
    ),
)
def test_policy_literals_are_fixed(field, invalid):
    with pytest.raises(ValidationError):
        ProductionQualificationPolicyV1.model_validate(
            _policy_payload(**{field: invalid})
        )


@pytest.mark.parametrize(
    "filename",
    (
        "",
        "/production-contract-qualification.json",
        "../production-contract-qualification.json",
        "qualification/production-contract-qualification.json",
        r"qualification\production-contract-qualification.json",
        ".",
        "..",
    ),
)
def test_unsafe_or_noncanonical_report_filenames_are_rejected(filename):
    with pytest.raises(ValidationError):
        ProductionQualificationPolicyV1.model_validate(
            _policy_payload(report_filename=filename)
        )


def test_unknown_policy_fields_are_rejected():
    payload = _policy_payload()
    payload["report_sha256"] = "0" * 64

    with pytest.raises(ValidationError):
        ProductionQualificationPolicyV1.model_validate(payload)


@pytest.mark.parametrize("schema_version", (1, 2, 3, 4, 5))
def test_pre_v6_manifests_omit_and_reject_qualification_policy(schema_version):
    manifest = _pre_v6_manifest(schema_version)

    assert manifest.production_qualification_policy is None
    assert "production_qualification_policy" not in manifest.model_dump(mode="json")
    assert b"production_qualification_policy" not in manifest.canonical_bytes()

    payload = json.loads(manifest.canonical_bytes())
    payload["production_qualification_policy"] = POLICY_PAYLOAD
    with pytest.raises(ValidationError):
        RunManifest.model_validate(payload)


def test_historical_v6_absence_loads_and_serializes_without_inference(tmp_path):
    current = _compile_v6_manifest()
    payload = json.loads(current.canonical_bytes())
    payload.pop("production_qualification_policy")
    path = tmp_path / "historical-v6.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    historical = load_run_manifest(path, verify_hash=False)

    assert historical.production_qualification_policy is None
    assert "production_qualification_policy" not in historical.model_dump(
        mode="json"
    )
    assert b"production_qualification_policy" not in historical.canonical_bytes()
    assert historical.sha256 != current.sha256


def test_policy_round_trip_persistence_is_exact(tmp_path):
    manifest = _compile_v6_manifest("frontier")
    path, digest_path = write_run_manifest(manifest, tmp_path / "manifest.json")

    assert path.read_bytes() == manifest.canonical_bytes()
    assert digest_path.read_text(encoding="utf-8").strip() == manifest.sha256
    assert load_run_manifest(path) == manifest
    assert json.loads(path.read_bytes())["production_qualification_policy"] == (
        POLICY_PAYLOAD
    )


def test_policy_presence_changes_identity_and_binding_conflicts(tmp_path):
    run_input = _bind_v2(
        tmp_path,
        Commitment(id="production-qualification", eval="predicate:True"),
    )
    current = _compile_v6_manifest(run_input_digest=run_input.run_input_digest)
    historical_payload = json.loads(current.canonical_bytes())
    historical_payload.pop("production_qualification_policy")
    historical = RunManifest.model_validate(historical_payload)

    assert current.canonical_bytes() != historical.canonical_bytes()
    assert current.sha256 != historical.sha256
    bind_run_manifest(current, tmp_path)
    with pytest.raises(RunManifestError) as raised:
        bind_run_manifest(historical, tmp_path)
    assert raised.value.code == "RUN_MANIFEST_CONFLICT"


def test_existing_v6_authorities_are_unchanged():
    manifest = _compile_v6_manifest()

    assert manifest.provider_fallback is False
    assert manifest.compact_recovery_policy is not None
    assert manifest.contract_schema_repair_policy is not None
    assert manifest.route_seat_presentation_plan is not None
