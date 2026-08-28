"""The manifest discloses every Config field its engine-config echo drops.

Regression (audit run-problems 2026-08-28, finding F-A / parked P10): a
`run-config.yaml` set five "everything on" switches and the compiled manifest
carried none of them, with `compile_notices` empty -- the run executed a
different configuration than the one its builder wrote, and said nothing.
The operator law this violates (2026-08-28): "Gates are always optional: with
warnings."

The disclosure rides `compile_notices` rather than the echo on purpose: adding
a field to the echo moves `source_config_hash`, and with it every manifest
digest and every qualification subject digest (docs/ERRATA.md E44). These tests
pin BOTH halves -- the notice fires when a switch is dropped, and nothing moves
when it is not.
"""
from __future__ import annotations

import json
from pathlib import Path

from deepreason.config import Config
from deepreason.run_manifest import (
    RunManifest,
    _source_config_data,
    _unconditionally_dropped_config_fields,
    _versioned_source_config_data,
    config_from_run_manifest,
    source_config_hash,
)
from deepreason.v6_policy import engaged_criticism_policy

from tests.test_reusable_qualification import _manifest, _profile

# experiments/2026-08-27-change-technique-run/run-config.yaml:157-169 on
# branch claude/spec-to-code-technique-k5209o, verbatim.
PT1_SWITCHES = {
    "JUDGE_SEATS_ENABLED": True,
    "ADJUDICATION_STATUS_AUTHORITY_ENABLED": True,
    "ENGAGED_CRITICISM_AUTHORITY": "defended_trial",
    "LEGACY_CRITICISM_ENABLED": False,
    "SCHOOL_SEATS_ENABLED": True,
}

DISCLOSURE = "ENGINE_CONFIG_FIELD_NOT_CARRIED"

# Compiled on the tranche base (ba59bf712) before the disclosure existed. A
# config whose dropped fields are all at their defaults must still compile to
# these exact bytes, or the fix has priced every home a qualification battery.
BASE_DEFAULT_MANIFEST_SHA = (
    "de66096f79454255f3b0a4db932186c8573de9000d1ddcc881fc76c6abe45322"
)


def _pt1_manifest(**overrides):
    """Compile through build_manifest_pt1.py:307-333's exact call shape."""
    values = {
        "config_updates": PT1_SWITCHES,
        "rubric_policy": "require_cross_family",
        "concurrency": 2,
        # The P-T1 builder passes no criticism_policy at all; `_manifest`
        # supplies one by default, so it must be cleared explicitly.
        "criticism_policy": None,
    }
    values.update(overrides)
    return _manifest(_profile(), **values)


def _disclosed(manifest) -> dict[str, str]:
    return {
        notice.pointer.rsplit("/", 1)[-1]: notice.message
        for notice in (manifest.compile_notices or ())
        if notice.code == DISCLOSURE
    }


def test_pt1_builder_shape_discloses_every_uncarried_switch():
    manifest = _pt1_manifest()
    runtime = config_from_run_manifest(manifest)
    disclosed = _disclosed(manifest)

    assert set(disclosed) == set(PT1_SWITCHES), (
        "every switch the echo drops must be named in a typed notice; "
        f"named={sorted(disclosed)}"
    )
    for field, configured in PT1_SWITCHES.items():
        # The run really does take the default -- the notice is not describing
        # a loss that does not happen.
        assert getattr(runtime, field) != configured
        message = disclosed[field]
        assert repr(configured) in message, (field, message)
        assert repr(getattr(runtime, field)) in message, (field, message)


def test_default_config_compiles_byte_identically():
    manifest = _manifest(_profile())
    assert _disclosed(manifest) == {}
    assert manifest.sha256 == BASE_DEFAULT_MANIFEST_SHA


def test_source_config_hash_is_unchanged_at_every_schema_version():
    # The echo itself is untouched: the disclosure adds no field to it, so the
    # hash every qualification subject derives from cannot have moved.
    hashes = [source_config_hash(Config(), schema_version=v) for v in (1, 2, 3, 4, 5, 6)]
    assert hashes[0] == hashes[1] == (
        "6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81"
    )
    assert hashes[2] == hashes[3] == hashes[4] == hashes[5] == (
        "2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5"
    )


def test_identity_only_fields_are_silent_when_the_manifest_carries_them():
    profile = _profile()
    manifest = _manifest(
        profile,
        config_updates={
            "LEGACY_CRITICISM_ENABLED": False,
            "ENGAGED_CRITICISM_AUTHORITY": "defended_trial",
        },
        criticism_policy=engaged_criticism_policy(
            profile.endpoint_id, authority="defended_trial"
        ),
    )
    disclosed = _disclosed(manifest)
    assert "LEGACY_CRITICISM_ENABLED" not in disclosed
    assert "ENGAGED_CRITICISM_AUTHORITY" not in disclosed


def test_identity_only_field_is_disclosed_when_the_manifest_does_not_carry_it():
    # The same two switches, with the criticism policy the builder forgot.
    disclosed = _disclosed(
        _manifest(
            _profile(),
            config_updates={
                "LEGACY_CRITICISM_ENABLED": False,
                "ENGAGED_CRITICISM_AUTHORITY": "defended_trial",
            },
            criticism_policy=None,
        )
    )
    assert "LEGACY_CRITICISM_ENABLED" in disclosed
    assert "ENGAGED_CRITICISM_AUTHORITY" in disclosed


def test_a_behavioural_knob_outside_the_five_is_disclosed_too():
    # The five switches are one instance; the disclosure is over the whole
    # drop set, so a knob from an unrelated tranche discloses identically.
    disclosed = _disclosed(
        _manifest(_profile(), config_updates={"JUDGE_SUMMONS_PER_CYCLE": 3})
    )
    assert "JUDGE_SUMMONS_PER_CYCLE" in disclosed
    assert "3" in disclosed["JUDGE_SUMMONS_PER_CYCLE"]


def test_the_dropped_set_is_exactly_the_unconditional_pops():
    # Derived, never restated: a knob added to the drop list joins the
    # disclosure automatically instead of escaping it.
    source = Path("src/deepreason/run_manifest.py").read_text()
    body = source.split("def _versioned_source_config_data")[1].split("\ndef ")[0]
    popped = {
        line.split('data.pop("', 1)[1].split('"', 1)[0]
        for line in body.splitlines()
        if 'data.pop("' in line
    }
    conditional = {"scratchpad", "bridge"}  # popped only below schema v3
    assert set(_unconditionally_dropped_config_fields()) == popped - conditional


def test_every_dropped_field_is_absent_from_the_echo_it_names():
    defaults = _source_config_data(Config())
    echo = _versioned_source_config_data(Config(), 6)
    for field in _unconditionally_dropped_config_fields():
        assert field in defaults
        assert field not in echo


def test_loading_a_committed_manifest_adds_no_notice():
    # The categorical argument of FIX.md, made checkable: a committed root's
    # manifest is READ, never recompiled, so no disclosure can attach to it
    # and no stored digest or verdict can move.
    target = Path(
        "experiments/2026-08-27-pc2b-symmetric-reasoning/run/run-manifest.json"
    )
    raw = target.read_text()
    manifest = RunManifest.model_validate_json(raw)
    assert _disclosed(manifest) == {}
    assert manifest.sha256 == json.loads(raw)["sha256"] if "sha256" in json.loads(raw) else True
    # Round-tripping through the public dump is byte-stable too.
    assert RunManifest.model_validate(manifest.model_dump(mode="json")).sha256 == (
        manifest.sha256
    )
