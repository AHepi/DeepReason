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
from deepreason.seat_bindings import seat_bindings_path, write_seat_bindings


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


def test_prepare_with_no_seat_bindings_file_binds_every_role_uniformly(tmp_path):
    """R3: absent a seat-bindings file, every role uses the base profile --
    the default no-flags case must stay byte-identical to before Rung S3."""

    profile = _profile()
    profile_path = write_provider_profile(profile, tmp_path / "profile.yaml")
    calls = []
    seats_home = tmp_path / "seats-home"
    service = _service(
        tmp_path,
        calls,
        environ={
            "DEEPREASON_TEST_KEY": "super-secret-value",
            "DEEPREASON_HOME": str(seats_home),
        },
    )

    prepared = service.prepare(_request(profile_path))
    manifest = load_run_manifest(Path(prepared.root) / "run-manifest.json")
    for routes in manifest.roles.values():
        for route in routes:
            assert route.model_id == profile.model_id


def test_prepare_with_a_seat_binding_overrides_only_the_bound_role(tmp_path):
    """R2/R4/R5: a bound role's compiled route reflects the bound profile;
    every other role still uses the base profile -- SeatBinding resolution
    where leases are built, resolved at manifest-compile (mint) time."""

    profile = _profile()
    profile_path = write_provider_profile(profile, tmp_path / "profile.yaml")
    bound = _profile(model_id="model-bound")
    bound_path = write_provider_profile(bound, tmp_path / "bound.yaml")
    seats_home = tmp_path / "seats-home"
    # Match RunPreparationService.prepare's own resolution exactly:
    # DEEPREASON_HOME via `environ` (not `home`) skips the ".deepreason"
    # subdirectory `provider_state_dir` appends for the `home=` form.
    write_seat_bindings(
        {"coder": str(bound_path)},
        seat_bindings_path(environ={"DEEPREASON_HOME": str(seats_home)}),
    )
    calls = []
    service = _service(
        tmp_path,
        calls,
        environ={
            "DEEPREASON_TEST_KEY": "super-secret-value",
            "DEEPREASON_HOME": str(seats_home),
        },
    )

    prepared = service.prepare(_request(profile_path))
    manifest = load_run_manifest(Path(prepared.root) / "run-manifest.json")
    assert manifest.roles["property_designer"][0].model_id == "model-bound"
    for role, routes in manifest.roles.items():
        if role == "property_designer":
            continue
        for route in routes:
            assert route.model_id == profile.model_id


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
