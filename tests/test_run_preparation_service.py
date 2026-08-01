import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from deepreason.application.models import RunBudgetIntentV1
from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    run_production_contract_doctor,
)
from deepreason.evidence.models import RunInputManifestV2
from deepreason.evidence.state import load_evidence_dossier, load_run_input
from deepreason.preparation import (
    RunPreparationError,
    RunPreparationRequestV1,
    RunPreparationService,
    load_preparation_record,
)
from deepreason.provider_profile import (
    ProviderProfileError,
    ProviderProfileV1,
    write_provider_profile,
)
from deepreason.qualification import QualificationError
from deepreason.run_manifest import load_run_manifest
from deepreason.runtime.launch_policy import require_v6_production_qualification


STAMP = datetime(2026, 7, 23, tzinfo=timezone.utc)


def _profile(**updates):
    values = {
        "provider": "openai",
        "endpoint": "https://api.example.com/v1",
        "model_id": "model-a",
        "model_revision": "rev-a",
        "family": "family-a",
        "context_window_tokens": 262144,
        "maximum_completion_tokens": 4096,
        "credential_env": "DEEPREASON_TEST_KEY",
    }
    values.update(updates)
    return ProviderProfileV1.create(**values)


def _qualified_report(manifest):
    return run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: (
            ProductionContractCaseResultV1(
                case_id=f"case-{index + 1:03d}",
                first_pass_valid=True,
                eventual_valid=True,
                repair_count=0,
                semantic_admission=True,
            )
        ),
    )


def _request(profile_path, question="Why is the sky blue?", **updates):
    values = {
        "question": question,
        "budget": RunBudgetIntentV1(cycles=3, token_budget=2000),
        "profile_path": str(profile_path),
    }
    values.update(updates)
    return RunPreparationRequestV1(**values)


def _service(tmp_path, calls, *, environ=None, executor=True):
    def execute(manifest):
        calls.append(manifest.sha256)
        return _qualified_report(manifest)

    return RunPreparationService(
        runs_dir=tmp_path / "runs",
        qualification_cache_dir=tmp_path / "qualification-cache",
        environ=(
            {"DEEPREASON_TEST_KEY": "super-secret-value"}
            if environ is None
            else environ
        ),
        qualification_executor=execute if executor else None,
        clock=lambda: STAMP,
    )


def test_question_only_preparation_binds_exact_v6_input_and_qualification(tmp_path):
    profile_path = write_provider_profile(_profile(), tmp_path / "profile.yaml")
    calls = []
    service = _service(tmp_path, calls)

    prepared = service.prepare(_request(profile_path))
    root = Path(prepared.root)
    run_input = load_run_input(root)
    dossier = load_evidence_dossier(root)
    manifest = load_run_manifest(root / "run-manifest.json")
    record = load_preparation_record(root)

    assert isinstance(run_input, RunInputManifestV2)
    assert run_input.problem.description == "Why is the sky blue?"
    assert dossier.sources == ()
    assert dossier.problem_ref == run_input.problem.id
    assert manifest.schema_version == 6
    assert manifest.run_input_digest == run_input.run_input_digest
    assert prepared.manifest_digest == manifest.sha256 == record.run_manifest_sha256
    assert record.run_input_digest == run_input.run_input_digest
    assert record.dossier_digest == dossier.dossier_digest
    report_path = root / "production-contract-qualification.json"
    assert record.qualification_report_sha256 == hashlib.sha256(
        report_path.read_bytes()
    ).hexdigest()
    assert prepared.workload.problem.description == run_input.problem.description
    assert calls == [manifest.sha256]
    report = require_v6_production_qualification(
        manifest, root=root, operation="prepared-run test"
    )
    assert report.run_manifest_sha256 == manifest.sha256


def test_preparation_is_idempotent_without_requalification_or_rewrites(tmp_path):
    profile_path = write_provider_profile(_profile(), tmp_path / "profile.yaml")
    calls = []
    service = _service(tmp_path, calls)
    request = _request(profile_path)

    first = service.prepare(request)
    root = Path(first.root)
    before = {path.name: path.stat().st_mtime_ns for path in root.iterdir()}
    second = service.prepare(request)
    after = {path.name: path.stat().st_mtime_ns for path in root.iterdir()}

    assert second == first
    assert calls == [first.manifest_digest]
    assert after == before


def test_different_questions_reuse_completed_qualification_without_provider_call(
    tmp_path,
):
    profile_path = write_provider_profile(_profile(), tmp_path / "profile.yaml")
    calls = []
    service = _service(tmp_path, calls)

    first = service.prepare(_request(profile_path, question="Question one"))
    second = service.prepare(_request(profile_path, question="Question two"))

    assert first.root != second.root
    assert first.manifest_digest != second.manifest_digest
    assert first.qualification_subject_digest == second.qualification_subject_digest
    assert calls == [first.manifest_digest]


def test_explicit_managed_identity_rejects_conflicting_input_without_mutation(tmp_path):
    profile_path = write_provider_profile(_profile(), tmp_path / "profile.yaml")
    calls = []
    service = _service(tmp_path, calls)
    first = service.prepare(
        _request(profile_path, question="Question one", managed_run_id="stable-run")
    )
    root = Path(first.root)
    before = {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()}

    with pytest.raises(RunPreparationError) as caught:
        service.prepare(
            _request(profile_path, question="Question two", managed_run_id="stable-run")
        )

    assert caught.value.code == "PREPARATION_INPUT_CONFLICT"
    assert {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()} == before
    assert len(calls) == 1


@pytest.mark.parametrize("failure", ["missing-profile", "credential", "qualification"])
def test_preconditions_fail_before_run_filesystem_mutation(tmp_path, failure):
    runs_dir = tmp_path / "runs"
    calls = []
    profile_path = tmp_path / "profile.yaml"
    if failure != "missing-profile":
        write_provider_profile(_profile(), profile_path)
    environment = (
        {} if failure == "credential" else {"DEEPREASON_TEST_KEY": "secret"}
    )
    service = RunPreparationService(
        runs_dir=runs_dir,
        qualification_cache_dir=tmp_path / "qualification-cache",
        environ=environment,
        qualification_executor=None,
        clock=lambda: STAMP,
    )

    expected = {
        "missing-profile": ProviderProfileError,
        "credential": RunPreparationError,
        "qualification": QualificationError,
    }[failure]
    with pytest.raises(expected):
        service.prepare(_request(profile_path))

    assert not runs_dir.exists()
    assert calls == []


def test_malformed_capacity_fails_before_run_filesystem_mutation(tmp_path):
    profile_path = tmp_path / "profile.yaml"
    payload = _profile().model_dump(mode="json", by_alias=True)
    payload["context_window_tokens"] = "unlimited"
    profile_path.write_text(yaml.safe_dump(payload))
    runs_dir = tmp_path / "runs"
    service = RunPreparationService(
        runs_dir=runs_dir,
        qualification_cache_dir=tmp_path / "qualification-cache",
        environ={"DEEPREASON_TEST_KEY": "secret"},
        qualification_executor=None,
    )

    with pytest.raises(ProviderProfileError) as caught:
        service.prepare(_request(profile_path))

    assert caught.value.code == "PROVIDER_PROFILE_MALFORMED"
    assert not runs_dir.exists()


def test_secret_never_appears_in_prepared_artifacts_or_errors(tmp_path):
    secret = "sk-plaintext-must-never-appear"
    profile_path = write_provider_profile(_profile(), tmp_path / "profile.yaml")
    calls = []
    service = _service(
        tmp_path,
        calls,
        environ={"DEEPREASON_TEST_KEY": secret},
    )

    prepared = service.prepare(_request(profile_path))

    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert secret.encode() not in path.read_bytes()
    with pytest.raises(RunPreparationError) as caught:
        _service(tmp_path, [], environ={}).prepare(_request(profile_path))
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value)
