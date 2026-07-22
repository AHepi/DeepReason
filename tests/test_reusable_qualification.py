import json

import pytest

from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    run_production_contract_doctor,
    validate_production_contract_qualification,
)
from deepreason.preparation import _config_for_profile, _records_for_question
from deepreason.provider_profile import ProviderProfileV1
from deepreason.qualification import (
    QualificationError,
    ReusableQualificationPairV1,
    completed_bundle_from_report,
    load_completed_qualification,
    project_qualification_report,
    qualification_cache_path,
    qualification_subject_digest,
    resolve_completed_qualification,
)
from deepreason.run_manifest import compile_run_manifest
from deepreason.v6_policy import conservative_control_plane_policy_v3


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


def _manifest(
    profile=None,
    *,
    question="Question A",
    compiled_at="2026-07-23T00:00:00Z",
    config_updates=None,
    **compile_updates,
):
    profile = profile or _profile()
    _dossier, run_input, _workload = _records_for_question(question)
    config = _config_for_profile(profile)
    if config_updates:
        config = config.model_copy(update=config_updates)
    values = {
        "schema_version": 6,
        "workload_profile": "text",
        "rubric_policy": "forbid",
        "compiled_at": compiled_at,
        "control_plane_policy": conservative_control_plane_policy_v3(),
        "run_input_digest": run_input.run_input_digest,
    }
    values.update(compile_updates)
    return compile_run_manifest(config, **values)


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


@pytest.mark.parametrize(
    "updates",
    [
        {"provider": "other-provider"},
        {"endpoint": "https://other.example.com/v1"},
        {"model_id": "model-b"},
        {"model_revision": "rev-b"},
        {"family": "family-b"},
        {"context_window_tokens": 131072},
        {"maximum_completion_tokens": 2048},
        {"credential_env": "OTHER_TEST_KEY"},
        {"model_profile": "compact"},
        {"reasoning": "high"},
        {"output_mode": "text"},
        {"output_mechanism": "native_json_schema"},
        {"temperature": 0.5},
        {"timeout_s": 240},
        {"logprobs": True},
    ],
)
def test_subject_digest_mutates_for_every_provider_behavior_field(updates):
    baseline_profile = _profile()
    changed_profile = _profile(**updates)

    baseline = qualification_subject_digest(
        _manifest(baseline_profile), baseline_profile
    )
    changed = qualification_subject_digest(
        _manifest(changed_profile), changed_profile
    )

    assert changed != baseline


@pytest.mark.parametrize(
    ("manifest_updates", "config_updates"),
    [
        ({"pack_profile": "reasoning.text.changed.v1"}, None),
        ({"output_profile": "changed-output"}, None),
        ({"concurrency": 2}, None),
        ({"budget_policy": {"provider_calls": 7}}, None),
        ({"stop_policy": {"mode": "bounded"}}, None),
        ({"memory_policy": {"mode": "bounded"}}, None),
        ({}, {"RETRY_MAX": 1}),
        ({}, {"PACK_TOKEN_BUDGET": 2048}),
    ],
)
def test_subject_digest_mutates_for_manifest_contract_presentation_and_output(
    manifest_updates, config_updates
):
    profile = _profile()
    baseline = qualification_subject_digest(_manifest(profile), profile)
    changed = qualification_subject_digest(
        _manifest(
            profile,
            config_updates=config_updates,
            **manifest_updates,
        ),
        profile,
    )

    assert changed != baseline


def test_subject_digest_is_invariant_only_to_question_and_compile_time():
    profile = _profile()
    first = _manifest(
        profile,
        question="Question A",
        compiled_at="2026-07-23T00:00:00Z",
    )
    second = _manifest(
        profile,
        question="A completely different question",
        compiled_at="2026-07-24T12:34:56Z",
    )

    assert first.sha256 != second.sha256
    assert qualification_subject_digest(first, profile) == (
        qualification_subject_digest(second, profile)
    )


def test_incomplete_cache_is_never_reusable(tmp_path):
    profile = _profile()
    manifest = _manifest(profile)
    subject = qualification_subject_digest(manifest, profile)
    target = qualification_cache_path(tmp_path, subject)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"status": "incomplete"}))

    with pytest.raises(QualificationError) as caught:
        load_completed_qualification(tmp_path, subject)

    assert caught.value.code == "QUALIFICATION_INCOMPLETE"


def test_complete_label_cannot_make_an_unqualified_case_set_reusable():
    profile = _profile()
    manifest = _manifest(profile)
    bundle = completed_bundle_from_report(_qualified_report(manifest), manifest, profile)
    pair = bundle.pairs[0]
    cases = tuple(
        ProductionContractCaseResultV1(
            case_id=f"case-{index + 1:03d}",
            first_pass_valid=index < 18,
            eventual_valid=index < 18,
            repair_count=0,
            semantic_admission=index < 18,
            failure_code=None if index < 18 else "SCHEMA_EXHAUSTED",
        )
        for index in range(20)
    )

    with pytest.raises(ValueError):
        ReusableQualificationPairV1(
            **pair.model_dump(exclude={"cases"}),
            cases=cases,
        )


def test_malformed_cache_error_suppresses_untrusted_payload(tmp_path):
    profile = _profile()
    manifest = _manifest(profile)
    subject = qualification_subject_digest(manifest, profile)
    target = qualification_cache_path(tmp_path, subject)
    secret = "cache-contained-secret"
    target.write_text(
        json.dumps(
            {
                "status": "complete",
                "subject_digest": subject,
                "plaintext_secret": secret,
            }
        )
    )

    with pytest.raises(QualificationError) as caught:
        load_completed_qualification(tmp_path, subject)

    assert caught.value.code == "QUALIFICATION_CACHE_INVALID"
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value)
    assert caught.value.__cause__ is None


def test_completed_cache_reuse_makes_zero_additional_provider_calls(tmp_path):
    profile = _profile()
    first = _manifest(profile, question="Question A")
    second = _manifest(
        profile,
        question="Question B",
        compiled_at="2026-07-24T00:00:00Z",
    )
    calls = []

    def execute(manifest):
        calls.append(manifest.sha256)
        return _qualified_report(manifest)

    first_bundle = resolve_completed_qualification(
        first, profile, cache_dir=tmp_path, executor=execute
    )
    second_bundle = resolve_completed_qualification(
        second, profile, cache_dir=tmp_path, executor=execute
    )

    assert first_bundle == second_bundle
    assert calls == [first.sha256]
    first_report = project_qualification_report(first_bundle, first, profile)
    second_report = project_qualification_report(second_bundle, second, profile)
    assert first_report.run_manifest_sha256 == first.sha256
    assert second_report.run_manifest_sha256 == second.sha256
    assert first_report.run_manifest_sha256 != second_report.run_manifest_sha256
    assert validate_production_contract_qualification(first_report, first) is first_report
    assert validate_production_contract_qualification(second_report, second) is second_report


def test_missing_cache_without_injected_executor_fails_closed(tmp_path):
    profile = _profile()
    manifest = _manifest(profile)

    with pytest.raises(QualificationError) as caught:
        resolve_completed_qualification(manifest, profile, cache_dir=tmp_path)

    assert caught.value.code == "QUALIFICATION_NOT_CONFIGURED"


def test_injected_executor_failure_redacts_provider_exception(tmp_path):
    profile = _profile()
    manifest = _manifest(profile)
    secret = "provider-response-containing-sk-secret"

    def fail(_manifest):
        raise RuntimeError(secret)

    with pytest.raises(QualificationError) as caught:
        resolve_completed_qualification(
            manifest, profile, cache_dir=tmp_path, executor=fail
        )

    assert caught.value.code == "QUALIFICATION_EXECUTION_FAILED"
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value)
    assert caught.value.__cause__ is None
