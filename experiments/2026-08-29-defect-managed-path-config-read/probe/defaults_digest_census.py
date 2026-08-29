"""Defaults-only digest census: nothing this tranche adds may move these."""
from datetime import datetime, timezone

from deepreason.config import Config
from deepreason.preparation import (
    RunPreparationRequestV1,
    _request_digest,
    build_preparation_manifest,
    qualification_subject_manifest,
)
from deepreason.provider_profile import ProviderProfileV1
from deepreason.qualification import qualification_subject_digest

STAMP = datetime(2026, 7, 23, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
QUESTION = "Why is the sky blue?"

PINS = {
    "baseline manifest sha256":
        "37e3fa54edb75346a5b180d54b77d032a749c9c87da4ec5db5f3c21652327d06",
    "baseline source_config_hash":
        "76e35e1604b6e4f090860d07ac6e87dfca29985f1e88de05b8bed793f8e850f1",
    "baseline qualification subject":
        "7c0ba0a174fdc2d93256d25a61079e5ca519e356487b3cdd692f35757fb76c62",
    "defaults-Config manifest sha256":
        "37e3fa54edb75346a5b180d54b77d032a749c9c87da4ec5db5f3c21652327d06",
    "defaults-Config qualification subject":
        "7c0ba0a174fdc2d93256d25a61079e5ca519e356487b3cdd692f35757fb76c62",
    "question-only request digest":
        "7ea3afd5a387993d19999918ea26698529245bbf1c1ba23dc5ac6a22e03c93e9",
}

profile = ProviderProfileV1.create(
    provider="openai",
    endpoint="https://api.example.com/v1",
    model_id="model-a",
    model_revision="rev-a",
    family="family-a",
    context_window_tokens=262144,
    maximum_completion_tokens=4096,
    credential_env="DEEPREASON_TEST_KEY",
)

baseline = build_preparation_manifest(profile, question=QUESTION, compiled_at=STAMP)
defaults = build_preparation_manifest(
    profile, question=QUESTION, compiled_at=STAMP, config=Config()
)
measured = {
    "baseline manifest sha256": baseline.sha256,
    "baseline source_config_hash": baseline.source_config_hash,
    "baseline qualification subject": qualification_subject_digest(baseline, profile),
    "defaults-Config manifest sha256": defaults.sha256,
    "defaults-Config qualification subject": qualification_subject_digest(
        defaults, profile
    ),
    "question-only request digest": _request_digest(
        RunPreparationRequestV1(question=QUESTION), profile
    ),
}

failures = 0
for name, pin in PINS.items():
    got = measured[name]
    verdict = "UNCHANGED" if got == pin else "MOVED"
    failures += got != pin
    print(f"  {name:<40} {verdict}  {got}")

extra = qualification_subject_digest(
    qualification_subject_manifest(profile), profile
) == qualification_subject_digest(
    qualification_subject_manifest(profile, config=Config()), profile
)
print(f"  {'qualify subject: none vs Config()':<40} "
      f"{'IDENTICAL' if extra else 'DIVERGED'}")
print(f"  verdict: {failures} of {len(PINS)} committed pins MOVED")
raise SystemExit(1 if failures or not extra else 0)
