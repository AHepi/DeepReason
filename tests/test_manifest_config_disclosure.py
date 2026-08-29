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
    CompileNoticeV1,
    RunManifest,
    RunManifestError,
    _CARRIAGE_NOTICE_CODE,
    _source_config_data,
    _unconditionally_dropped_config_fields,
    _versioned_source_config_data,
    config_from_run_manifest,
    source_config_hash,
)
from deepreason.qualification import qualification_subject_digest
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


def test_pt1_builder_shape_carries_and_discloses_every_dropped_switch():
    """Road A's acceptance test (P15): the notice is the carrier.

    Was `..._discloses_every_uncarried_switch`, and asserted
    `getattr(runtime, field) != configured` -- the silent revert. Carriage
    inverts exactly that assertion; the disclosure half is unchanged.
    """

    manifest = _pt1_manifest()
    runtime = config_from_run_manifest(manifest)
    disclosed = _disclosed(manifest)

    assert set(disclosed) == set(PT1_SWITCHES), (
        "every switch the echo drops must be named in a typed notice; "
        f"named={sorted(disclosed)}"
    )
    for field, configured in PT1_SWITCHES.items():
        # The configured value REACHES the run. This is the limb of the
        # 2026-08-28 law the disclosure tranche could not deliver.
        assert getattr(runtime, field) == configured, (
            field, getattr(runtime, field), configured
        )
        assert repr(configured) in disclosed[field], (field, disclosed[field])


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


def test_a_field_whose_effect_is_compiled_is_still_carried_and_still_named():
    """Was `..._are_silent_when_the_manifest_carries_them`.

    That silence WAS the defect for these two fields, and it is the one B1's
    residual finding named: `LEGACY_CRITICISM_ENABLED` was neither carried nor
    disclosed. Under road A the notice IS the carrier, so suppressing it means
    "not carried" -- `_dropped_field_effect_is_compiled` is therefore deleted,
    and a compiled effect no longer buys silence. The typed policy field it
    pointed at survives as the notice's `resolution`.
    """

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
    runtime = config_from_run_manifest(manifest)

    assert "LEGACY_CRITICISM_ENABLED" in disclosed
    assert "ENGAGED_CRITICISM_AUTHORITY" in disclosed
    assert runtime.LEGACY_CRITICISM_ENABLED is False
    assert runtime.ENGAGED_CRITICISM_AUTHORITY == "defended_trial"

    # The effect the old suppression pointed at is still named, as the
    # notice's resolution rather than as a reason to say nothing.
    resolutions = {
        n.pointer.rsplit("/", 1)[-1]: n.resolution
        for n in (manifest.compile_notices or ())
        if n.code == DISCLOSURE
    }
    assert resolutions["LEGACY_CRITICISM_ENABLED"] == "/criticism_policy"
    assert resolutions["ENGAGED_CRITICISM_AUTHORITY"] == "/criticism_policy/authority"

    # And the priced switch says its price, in the message a person reads.
    assert "requalifies" in disclosed["LEGACY_CRITICISM_ENABLED"]


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


# --- carriage: the notice is the road back (P15) --------------------------- #
#
# The 2026-08-28 tranche fixed the SILENCE, which is the first limb of the
# operator's law ("Gates are always optional: with warnings"). It did not fix
# the second: 22 behavioural switches still could not be turned ON by any
# route. Road A makes the disclosure notice the CARRIER as well.


def _carried(manifest):
    return {
        n.pointer.rsplit("/", 1)[-1]: n.value
        for n in (manifest.compile_notices or ())
        if n.code == _CARRIAGE_NOTICE_CODE
    }


def test_every_dropped_field_the_managed_path_can_set_round_trips():
    """R1. At HEAD before this tranche the answer was 0 of 25."""

    dropped = _unconditionally_dropped_config_fields()
    explicit = {
        "ATTENTION_ALLOCATION_POLICY": "wander-cap.v1-probe",
        "CAPTURE14_SC_CEILING": 0.75,
        "DISCHARGE_POLICY": "discharge-required.v1-probe",
        "ENGAGED_CRITICISM_AUTHORITY": "defended_trial",
        "SEED_PROBLEM_BUDGET_FLOOR": 0.75,
        "SPLIT_BUDGET_SEAT_PROTOCOL": "on",
    }
    carried = 0
    for field in dropped:
        # CHANNELS_DISABLED is host-owned on the managed path (parked P21) and
        # is exercised by its own test below, not here.
        if field == "CHANNELS_DISABLED":
            continue
        default = getattr(Config(), field)
        if field in explicit:
            want = explicit[field]
        elif isinstance(default, bool):
            want = not default
        else:
            want = default + 1
        manifest = _manifest(_profile(), config_updates={field: want})
        assert getattr(config_from_run_manifest(manifest), field) == want, field
        carried += 1
    assert carried == len(dropped) - 1 == 24


def test_carriage_moves_no_qualification_subject_digest_it_did_not_already_move():
    """R2. The carrier rides a notice `qualification_subject_payload` strips.

    So the digest a home requalifies on cannot move because of carriage. The
    one field that DOES move it moved it before this tranche too, because
    `preparation` compiles a criticism policy for it -- carriage adds no
    battery anywhere.
    """

    profile = _profile()
    base = _manifest(profile)
    for field, want in (
        ("JUDGE_SEATS_ENABLED", True),
        ("SCHOOL_SEATS_ENABLED", True),
        ("ADJUDICATION_STATUS_AUTHORITY_ENABLED", True),
        ("K_FRAME", 3),
    ):
        moved = _manifest(profile, config_updates={field: want})
        assert _carried(moved)[field] is not None, field
        assert qualification_subject_digest(moved, profile) == (
            qualification_subject_digest(base, profile)
        ), field


def test_the_priced_switch_compiles_with_its_price_visible():
    """R3. Never a refusal, and never silent about what it costs."""

    profile = _profile()
    manifest = _manifest(
        profile, config_updates={"LEGACY_CRITICISM_ENABLED": False}
    )
    disclosed = _disclosed(manifest)

    assert config_from_run_manifest(manifest).LEGACY_CRITICISM_ENABLED is False
    assert "requalifies" in disclosed["LEGACY_CRITICISM_ENABLED"]
    assert "qualification subject" in disclosed["LEGACY_CRITICISM_ENABLED"]


def test_a_manifest_with_no_carriage_notice_behaves_exactly_as_before():
    """R4. Nothing retroactive: all 72 committed manifests carry no notice."""

    manifest = _manifest(_profile())
    assert manifest.compile_notices in (None, ())
    assert _carried(manifest) == {}
    # And the absent `value` is absent from the BYTES, not merely null --
    # a `"value": null` on an unrelated notice would move every digest that
    # manifest feeds, because the subject payload keeps non-carriage notices.
    other = CompileNoticeV1(code="SOME_OTHER_NOTICE", message="m", pointer="/p")
    assert "value" not in other.model_dump(mode="json")


def test_a_tampered_carriage_notice_is_refused_typed_never_defaulted():
    """Continuation-integrity law (2026-08-29): editing a record must not buy
    a working run. Silently defaulting is the defect being repaired."""

    profile = _profile()
    base = _manifest(profile, config_updates={"JUDGE_SEATS_ENABLED": True})

    for notice, code in (
        (CompileNoticeV1(code=_CARRIAGE_NOTICE_CODE, message="m",
                         pointer="/somewhere_else/X", value="true"),
         "CARRIED_CONFIG_POINTER_INVALID"),
        (CompileNoticeV1(code=_CARRIAGE_NOTICE_CODE, message="m",
                         pointer="/engine_config/NOT_A_DROPPED_FIELD", value="true"),
         "CARRIED_CONFIG_FIELD_UNKNOWN"),
        (CompileNoticeV1(code=_CARRIAGE_NOTICE_CODE, message="m",
                         pointer="/engine_config/JUDGE_SEATS_ENABLED", value="{bad"),
         "CARRIED_CONFIG_VALUE_INVALID"),
    ):
        tampered = base.model_copy(update={"compile_notices": (notice,)})
        try:
            config_from_run_manifest(tampered)
        except RunManifestError as error:
            assert error.code == code, (code, error.code)
        else:
            raise AssertionError(f"expected {code}, got a silent default")


def test_the_priced_field_table_is_data_not_a_branch():
    """R5. A future priced field is a row, never a code edit."""

    from deepreason.run_manifest import _CARRIAGE_REQUALIFIES

    assert set(_CARRIAGE_REQUALIFIES) == {"LEGACY_CRITICISM_ENABLED"}
    assert set(_CARRIAGE_REQUALIFIES) <= set(_unconditionally_dropped_config_fields())
