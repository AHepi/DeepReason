import pytest
import yaml

from deepreason.config import Config, load as load_config
from deepreason.provider_profile import (
    PROFILE_ENV,
    ProviderProfileError,
    ProviderProfileV1,
    credential_present,
    resolve_provider_profile,
    setup_provider_profile_path,
    write_provider_profile,
)


def _profile(**updates):
    values = {
        "provider": "openai",
        "endpoint": "https://api.example.com/v1",
        "model_id": "model-a",
        "model_revision": "2026-07-01",
        "family": "family-a",
        "context_window_tokens": 131072,
        "maximum_completion_tokens": 4096,
        "credential_env": "DEEPREASON_TEST_KEY",
    }
    values.update(updates)
    return ProviderProfileV1.create(**values)


def test_resolution_precedence_is_explicit_then_environment_then_setup(tmp_path):
    home = tmp_path / "home"
    setup = setup_provider_profile_path(home=home, environ={})
    environment = tmp_path / "environment.yaml"
    explicit = tmp_path / "explicit.yaml"
    write_provider_profile(_profile(model_id="setup"), setup)
    write_provider_profile(_profile(model_id="environment"), environment)
    write_provider_profile(_profile(model_id="explicit"), explicit)

    variables = {PROFILE_ENV: str(environment)}
    selected = resolve_provider_profile(explicit, environ=variables, home=home)
    assert (selected.source, selected.profile.model_id) == ("explicit", "explicit")

    selected = resolve_provider_profile(environ=variables, home=home)
    assert (selected.source, selected.profile.model_id) == (
        "environment",
        "environment",
    )

    selected = resolve_provider_profile(environ={}, home=home)
    assert (selected.source, selected.profile.model_id) == ("setup", "setup")


def test_config_load_none_remains_pure_under_hostile_ambient_files(
    tmp_path, monkeypatch
):
    home = tmp_path / "home"
    cwd = tmp_path / "unrelated"
    cwd.mkdir()
    write_provider_profile(_profile(), setup_provider_profile_path(home=home, environ={}))
    (cwd / "engine.yaml").write_text("FLOOR: 999\n")
    monkeypatch.chdir(cwd)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv(PROFILE_ENV, str(cwd / "missing-profile.yaml"))

    assert load_config(None) == Config()


@pytest.mark.parametrize(
    "updates",
    [
        {"context_window_tokens": 0},
        {"context_window_tokens": True},
        {"context_window_tokens": "131072"},
        {"maximum_completion_tokens": 0},
        {"maximum_completion_tokens": True},
        {"maximum_completion_tokens": "4096"},
        {"context_window_tokens": 4096, "maximum_completion_tokens": 4096},
        {"temperature": float("nan")},
        {"temperature": float("inf")},
    ],
)
def test_profile_rejects_nonfinite_or_malformed_capacity(updates):
    with pytest.raises(ValueError):
        _profile(**updates)


def test_profile_and_errors_never_expose_credential_values(tmp_path, monkeypatch):
    secret = "sk-do-not-disclose-very-secret"
    monkeypatch.setenv("DEEPREASON_TEST_KEY", secret)
    target = write_provider_profile(_profile(), tmp_path / "profile.yaml")

    assert secret not in target.read_text()
    assert credential_present(_profile()) is True
    assert secret not in repr(_profile())
    assert secret not in _profile().model_dump_json()

    malformed = tmp_path / "malformed.yaml"
    malformed.write_text(
        yaml.safe_dump(
            {
                "schema": "deepreason-provider-profile.v1",
                "provider": "openai",
                "plaintext_api_key": secret,
            }
        )
    )
    with pytest.raises(ProviderProfileError) as caught:
        resolve_provider_profile(malformed)
    assert caught.value.code == "PROVIDER_PROFILE_MALFORMED"
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value)


def test_missing_profile_is_stable_and_does_not_use_working_directory(
    tmp_path, monkeypatch
):
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    write_provider_profile(_profile(), cwd / "provider.yaml")
    monkeypatch.chdir(cwd)

    with pytest.raises(ProviderProfileError) as caught:
        resolve_provider_profile(environ={}, home=tmp_path / "empty-home")

    assert caught.value.code == "PROVIDER_PROFILE_MISSING"


def test_credential_presence_is_boolean_only(monkeypatch):
    profile = _profile()
    monkeypatch.delenv(profile.credential_env, raising=False)
    assert credential_present(profile) is False
    monkeypatch.setenv(profile.credential_env, "secret")
    assert credential_present(profile) is True
    assert type(credential_present(profile)) is bool
