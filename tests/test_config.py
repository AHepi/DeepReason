"""One configuration schema, partial profiles, and shared overrides."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from deepreason.config import (
    Config,
    apply_overrides,
    load,
    parse_overrides,
    parse_value,
    role_api_key_envs,
)

ROOT = Path(__file__).resolve().parents[1]


def test_built_in_and_empty_default_profile_are_identical(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "hostile-home"))
    monkeypatch.setenv("DEEPREASON_PROFILE", str(tmp_path / "ambient.yaml"))
    (tmp_path / "engine.yaml").write_text("N_SCHOOLS: 99\n")
    (tmp_path / "ambient.yaml").write_text("N_SCHOOLS: 98\n")

    assert load() == Config()
    assert load(ROOT / "config" / "default.yaml") == Config()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("ARGUMENTATIVE_AUTHORITY", "legacy_direct"),
        ("TEXT_RUBRIC_AUTHORITY", "legacy_status"),
        ("PAIRWISE_AUTHORITY", "legacy_status"),
        ("INFRASTRUCTURE_REVIEW_AUTHORITY", "legacy_status"),
    ],
)
def test_historical_authority_values_are_rejected_by_the_typed_config(field, value):
    with pytest.raises(ValidationError):
        Config.model_validate({field: value})


def test_deepseek_is_a_partial_profile_over_typed_defaults():
    raw = yaml.safe_load((ROOT / "config" / "deepseek.yaml").read_text())
    configured = load(ROOT / "config" / "deepseek.yaml")

    assert set(raw) < set(Config.model_fields)
    assert configured.HV_MIN == 0.5
    assert configured.N_SCHOOLS == 2
    assert configured.RECRIT_STANDING is Config().RECRIT_STANDING
    assert configured.PROP_PROBATION_EVENTS == Config().PROP_PROBATION_EVENTS
    assert configured.roles["conjecturer"]["max_tokens"] == 4000


def test_unknown_knobs_and_endpoint_fields_fail_loudly():
    with pytest.raises(ValidationError, match="EXTRA_KNOB"):
        Config.model_validate({"EXTRA_KNOB": 1})
    with pytest.raises(ValidationError, match="timeout_seconds"):
        Config.model_validate(
            {
                "roles": {
                    "conjecturer": {
                        "endpoint": "https://example.invalid",
                        "model": "m",
                        "timeout_seconds": 10,
                    }
                }
            }
        )


def test_overrides_share_yaml_parsing_and_full_schema_validation():
    configured = Config(
        roles={
            "conjecturer": {
                "endpoint": "https://example.invalid",
                "model": "m",
                "api_key_env": "MODEL_KEY",
            },
            "judge": [
                {"endpoint": "https://example.invalid", "model": "a"},
                {"endpoint": "https://example.invalid", "model": "b"},
            ],
        }
    )
    values = parse_overrides(
        [
            "N_SCHOOLS=2",
            "SPEC_INJECTION=true",
            "roles.conjecturer.reasoning=none",
            "roles.judge.1.model=c",
        ]
    )
    overridden = apply_overrides(configured, values)

    assert overridden.N_SCHOOLS == 2
    assert overridden.SPEC_INJECTION is True
    assert overridden.roles["conjecturer"]["reasoning"] == "none"
    assert overridden.roles["judge"][1]["model"] == "c"
    assert role_api_key_envs(overridden) == {"MODEL_KEY"}
    assert parse_value("1200") == 1200

    added = apply_overrides(
        Config(),
        {"roles.researcher": {"endpoint": "https://example.invalid", "model": "r"}},
    )
    assert added.roles["researcher"]["model"] == "r"

    with pytest.raises(ValueError, match="unknown config path"):
        apply_overrides(configured, {"NOT_A_KNOB": 1})
    with pytest.raises(ValidationError, match="greater than 0"):
        apply_overrides(configured, {"roles.conjecturer.max_tokens": 0})


def test_timeout_s_is_a_validated_role_knob():
    """The transport read timeout is role-table config (a run died on the
    old hardcoded 120s with no knob to turn): settable per role, dotted-path
    overridable, and rejected when non-positive."""
    configured = Config(
        roles={
            "variator": {
                "endpoint": "https://example.invalid",
                "model": "m",
                "timeout_s": 600,
            }
        }
    )
    assert configured.roles["variator"]["timeout_s"] == 600
    overridden = apply_overrides(configured, {"roles.variator.timeout_s": 900})
    assert overridden.roles["variator"]["timeout_s"] == 900
    with pytest.raises(ValidationError, match="greater than 0"):
        apply_overrides(configured, {"roles.variator.timeout_s": 0})


def test_config_assignment_is_validated():
    configured = Config()
    with pytest.raises(ValidationError):
        configured.N_SCHOOLS = "not-an-integer"


def test_cli_renders_the_complete_effective_config(capsys):
    from deepreason.cli.main import main

    assert main(["config"]) == 0
    rendered = yaml.safe_load(capsys.readouterr().out)

    assert rendered == Config().model_dump(mode="json")
    assert "PROP_PROBATION_EVENTS" in rendered


def test_single_purpose_adapter_resolves_only_its_configured_role():
    from deepreason.llm.adapter import build_adapter

    configured = Config(
        roles={
            "conjecturer": {"endpoint": "https://unused.invalid", "model": "gen"},
            "thesis": {"endpoint": "https://used.invalid", "model": "writer"},
        }
    )
    adapter = build_adapter(configured, None, only_roles={"thesis"})

    assert set(adapter.endpoints) == {"thesis"}
    assert adapter.endpoints["thesis"].model == "writer"
