"""Regression (tranche 2026-08-29-defect-managed-path-config-read, P14):
`deepreason reason` must read the operator's run configuration.

The managed path constructs its `Config` from the provider profile
(`preparation._config_for_profile`) and never opens the file `--config` names,
so a `run-config.yaml` switch is neither carried into the run nor disclosed as
uncarried. Record evidence: 41 committed managed-path run roots share ONE
engine-config echo and carry zero compile notices
(`experiments/2026-08-29-defect-managed-path-config-read/probe/echo_census.out`).

Operator law this enforces (CLAUDE.md, 2026-08-28, verbatim): "configuration of
seats need to be able to turn gates on and off at will ... Gates are always
optional: with warnings."
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from deepreason import preparation
from deepreason.cli.main import _cmd_reason, build_parser
from deepreason.config import Config, load as load_config
from deepreason.preparation import build_preparation_manifest
from deepreason.provider_profile import ProviderProfileV1
from deepreason.run_manifest import config_from_run_manifest

STAMP = datetime(2026, 7, 23, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# The five switches P-T1's own run-config.yaml set and lost, plus the two the
# 2026-08-12 operator config sets. Values are the operator's, not invented.
OPERATOR_YAML = """\
JUDGE_SEATS_ENABLED: true
ADJUDICATION_STATUS_AUTHORITY_ENABLED: true
SCHOOL_SEATS_ENABLED: true
SCOPE_MAX_NODES: 41
JUDGE_SUMMONS_PER_CYCLE: 3
"""


def _profile() -> ProviderProfileV1:
    return ProviderProfileV1.create(
        provider="openai",
        endpoint="https://api.example.com/v1",
        model_id="model-a",
        model_revision="rev-a",
        family="family-a",
        context_window_tokens=262144,
        maximum_completion_tokens=4096,
        credential_env="DEEPREASON_TEST_KEY",
    )


def _managed_manifest(profile, operator: Config | None):
    """Prepare the MANAGED manifest, optionally under the operator's Config.

    THE ONE FIX-SHAPE ASSUMPTION IN THIS FILE, stated so a fix that chooses a
    different route updates one helper instead of three tests: the managed
    manifest builder must be able to be GIVEN the operator's configuration.
    Whether the route is a `Config` object, a path, or a field on
    `RunPreparationRequestV1` is the fix's business; that some route exists is
    the defect.
    """
    if operator is None:
        return build_preparation_manifest(
            profile, question="Why is the sky blue?", compiled_at=STAMP
        )
    try:
        return build_preparation_manifest(
            profile,
            question="Why is the sky blue?",
            compiled_at=STAMP,
            config=operator,
        )
    except TypeError as error:
        pytest.fail(
            "MANAGED PATH HAS NO CONFIGURATION INPUT: build_preparation_manifest "
            f"cannot be given the operator's Config at all -- {error}"
        )


def test_reason_forwards_the_operator_config_to_preparation(tmp_path, monkeypatch):
    """`deepreason --config FILE reason Q` must let FILE reach preparation.

    Deliberately neutral about HOW: the assertion is satisfied by forwarding
    the path, or the loaded Config, or anything carrying the operator's value.
    It fails only if NOTHING about FILE reaches the preparation service, which
    is the state of the tree today.
    """
    config_path = tmp_path / "run-config.yaml"
    config_path.write_text(OPERATOR_YAML)

    seen: dict[str, object] = {}

    class _Stop(Exception):
        pass

    class _CapturingService:
        def __init__(self, *args, **kwargs):
            seen["init_args"] = args
            seen["init_kwargs"] = kwargs

        def prepare(self, request, *args, **kwargs):
            seen["request"] = request
            seen["prepare_args"] = args
            seen["prepare_kwargs"] = kwargs
            raise _Stop()

    monkeypatch.setattr(preparation, "RunPreparationService", _CapturingService)
    monkeypatch.setattr(
        "deepreason.cli.main._reasoning_disabled_refusal", lambda _profile: None
    )

    args = build_parser().parse_args(
        ["--config", str(config_path), "reason", "Why is the sky blue?"]
    )
    assert args.config == str(config_path), "the global --config flag must parse"

    with pytest.raises(_Stop):
        _cmd_reason(args)

    forwarded = repr(seen)
    assert str(config_path) in forwarded or "JUDGE_SEATS_ENABLED" in forwarded, (
        "deepreason reason discards --config: nothing about the operator's "
        f"configuration file reached RunPreparationService. Captured: {forwarded}"
    )


def test_managed_manifest_carries_or_discloses_every_operator_setting(tmp_path):
    """Field by field: carried into the run, OR disclosed as not carried.

    This is GOAL.md's success criterion verbatim, and it is the disjunction the
    2026-08-28 operator law requires -- a gate is either on because the
    configuration turned it on, or the record says why it is not.
    """
    config_path = tmp_path / "run-config.yaml"
    config_path.write_text(OPERATOR_YAML)
    operator = load_config(config_path)

    default = Config()
    configured = {
        name: getattr(operator, name)
        for name in type(default).model_fields
        if getattr(operator, name) != getattr(default, name)
    }
    assert configured, "the fixture must set something away from its default"

    profile = _profile()
    manifest = _managed_manifest(profile, operator)
    runtime = config_from_run_manifest(manifest)
    disclosed = {
        notice.pointer
        for notice in (manifest.compile_notices or ())
        if notice.code == "ENGINE_CONFIG_FIELD_NOT_CARRIED"
    }

    unanswered = [
        name
        for name, value in configured.items()
        if getattr(runtime, name, object()) != value
        and f"/engine_config/{name}" not in disclosed
    ]
    assert not unanswered, (
        f"{len(unanswered)} of {len(configured)} operator settings are neither "
        f"carried into the run nor disclosed as uncarried: {sorted(unanswered)}"
    )


def test_a_default_valued_operator_config_changes_nothing(tmp_path):
    """The half that must NOT move: reading a config costs nothing at defaults.

    Passes today (vacuously -- nothing is read) and must keep passing after the
    fix, or every existing home owes a ~14-minute qualification battery for a
    configuration that asked for nothing.
    """
    profile = _profile()
    baseline = _managed_manifest(profile, None)

    config_path = tmp_path / "run-config.yaml"
    config_path.write_text("{}\n")
    operator = load_config(config_path)
    assert operator == Config(), "an empty profile must load as the typed defaults"

    try:
        carried = build_preparation_manifest(
            profile,
            question="Why is the sky blue?",
            compiled_at=STAMP,
            config=operator,
        )
    except TypeError:
        pytest.skip(
            "no configuration route exists yet; this test pins the post-fix "
            "guarantee and is asserted by the fix tranche"
        )
    assert carried.sha256 == baseline.sha256
    assert carried.source_config_hash == baseline.source_config_hash
