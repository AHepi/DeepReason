"""The durable qualification tier ladder: full -> shallow -> unqualified.

Qualification always concludes with a durable tier for the exact behavior
subject.  Full evidence stays the write-once reusable bundle; the two lower
rungs live in a tier record keyed by the same subject digest, so the same
subject changes invalidate every rung the same way.  Readiness, `qualify`,
and full `reason` all project the recorded tier truthfully.
"""

from __future__ import annotations

import json

import pytest

from deepreason.cli.main import main
from deepreason.preparation import (
    RunPreparationRequestV1,
    RunPreparationService,
    qualification_subject_manifest,
)
from deepreason.provider_profile import write_provider_profile
from deepreason.qualification import (
    SHALLOW_FITNESS_CASES,
    QualificationError,
    QualificationTierRecordV1,
    ShallowFitnessCaseResultV1,
    load_qualification_tier,
    qualification_subject_digest,
    qualification_tier_path,
    resolve_completed_qualification,
    resolve_qualification_tier,
    shallow_tier_record_from_cases,
    write_qualification_tier,
)
from deepreason.readiness import get_readiness
from deepreason.shallow_fitness import (
    SHALLOW_FITNESS_MAX_PROVIDER_CALLS,
    run_shallow_fitness_battery,
    shallow_fitness_maximum_provider_calls,
)
from minireason.call import EndpointError, MockEndpoint
from tests.test_public_v6_facade import _configure, _profile, _qualify


def _cases(valid: int = SHALLOW_FITNESS_CASES, *, repairs: int = 0):
    results = []
    for index in range(SHALLOW_FITNESS_CASES):
        if index < valid:
            results.append(
                ShallowFitnessCaseResultV1(
                    case_id=f"case-{index + 1:03d}",
                    first_pass_valid=repairs == 0,
                    eventual_valid=True,
                    repair_count=repairs,
                )
            )
        else:
            results.append(
                ShallowFitnessCaseResultV1(
                    case_id=f"case-{index + 1:03d}",
                    first_pass_valid=False,
                    eventual_valid=False,
                    repair_count=2,
                    failure_code="SCHEMA_REPAIR_ERROR",
                )
            )
    return tuple(results)


def _subject(profile):
    return qualification_subject_digest(
        qualification_subject_manifest(profile), profile
    )


def _write_tier(state, profile, *, valid: int):
    subject = _subject(profile)
    record = shallow_tier_record_from_cases(
        _cases(valid), subject_digest=subject, profile=profile
    )
    write_qualification_tier(record, state / "qualification-cache")
    return subject, record


def _stub_battery(monkeypatch, *, valid: int, calls=None):
    def battery(_profile):
        if calls is not None:
            calls.append(valid)
        return _cases(valid)

    monkeypatch.setattr(
        "deepreason.shallow_fitness.run_shallow_fitness_battery", battery
    )


def _fail_full_battery(monkeypatch):
    monkeypatch.setattr(
        "deepreason.qualification.default_qualification_executor",
        lambda _manifest: (_ for _ in ()).throw(RuntimeError("provider body")),
    )


# --------------------------------------------------------------------------
# Record identity and gate discipline


def test_tier_record_gate_matches_the_shallow_minimum():
    profile = _profile()
    shallow = shallow_tier_record_from_cases(
        _cases(5), subject_digest="a" * 64, profile=profile
    )
    floor = shallow_tier_record_from_cases(
        _cases(4), subject_digest="a" * 64, profile=profile
    )
    assert shallow.tier == "shallow"
    assert floor.tier == "unqualified"
    with pytest.raises(ValueError, match="shallow-fitness gate"):
        QualificationTierRecordV1.create(
            subject_digest=shallow.subject_digest,
            provider_profile_digest=shallow.provider_profile_digest,
            policy_preset_digest=shallow.policy_preset_digest,
            tier="unqualified",
            shallow_contract_id=shallow.shallow_contract_id,
            cases=shallow.cases,
        )


def test_tier_record_round_trips_and_rejects_foreign_subject(tmp_path):
    profile = _profile()
    record = shallow_tier_record_from_cases(
        _cases(6), subject_digest="b" * 64, profile=profile
    )
    write_qualification_tier(record, tmp_path)
    assert load_qualification_tier(tmp_path, "b" * 64) == record
    with pytest.raises(QualificationError) as caught:
        load_qualification_tier(tmp_path, "c" * 64)
    assert caught.value.code == "QUALIFICATION_TIER_NOT_RECORDED"
    # A record parked under another subject's key is a mismatch, not a hit.
    target = qualification_tier_path(tmp_path, "c" * 64)
    target.write_bytes(qualification_tier_path(tmp_path, "b" * 64).read_bytes())
    with pytest.raises(QualificationError) as mismatched:
        load_qualification_tier(tmp_path, "c" * 64)
    assert mismatched.value.code == "QUALIFICATION_TIER_SUBJECT_MISMATCH"


def test_tampered_tier_record_fails_closed(tmp_path):
    profile = _profile()
    record = shallow_tier_record_from_cases(
        _cases(6), subject_digest="d" * 64, profile=profile
    )
    path = write_qualification_tier(record, tmp_path)
    payload = json.loads(path.read_bytes())
    payload["tier"] = "unqualified"
    path.write_text(json.dumps(payload))
    with pytest.raises(QualificationError) as caught:
        load_qualification_tier(tmp_path, "d" * 64)
    assert caught.value.code == "QUALIFICATION_TIER_INVALID"
    # Non-canonical but valid JSON is also refused.
    path.write_bytes(
        json.dumps(record.model_dump(mode="json", by_alias=True), indent=2).encode()
        + b"\n"
    )
    with pytest.raises(QualificationError) as noncanonical:
        load_qualification_tier(tmp_path, "d" * 64)
    assert noncanonical.value.code == "QUALIFICATION_TIER_NONCANONICAL"


def test_resolve_tier_prefers_full_evidence(tmp_path, monkeypatch):
    state, profile = _configure(monkeypatch, tmp_path)
    cache = state / "qualification-cache"
    subject, _record = _write_tier(state, profile, valid=6)
    assert resolve_qualification_tier(cache, subject) == "shallow"
    _qualify(state, profile)
    assert resolve_qualification_tier(cache, subject) == "full"


def test_resolve_tier_defaults_to_unqualified_without_records(tmp_path, monkeypatch):
    state, profile = _configure(monkeypatch, tmp_path)
    assert (
        resolve_qualification_tier(state / "qualification-cache", _subject(profile))
        == "unqualified"
    )


# --------------------------------------------------------------------------
# The qualify ladder


def test_qualify_concludes_shallow_tier_durably_and_reuses_it(
    tmp_path, monkeypatch, capsys
):
    state, _profile_value = _configure(monkeypatch, tmp_path)
    _fail_full_battery(monkeypatch)
    battery_calls = []
    _stub_battery(monkeypatch, valid=6, calls=battery_calls)

    assert main(["qualify", "--yes", "--json"]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["tier"] == "shallow"
    assert first["qualification_state"] == "ready_shallow"
    assert first["cache_reused"] is False
    assert first["next_action"] == 'deepreason reason --shallow "YOUR QUESTION"'
    assert battery_calls == [6]
    record = load_qualification_tier(
        state / "qualification-cache", first["qualification_subject_digest"]
    )
    assert record.tier == "shallow"

    # Reuse: the durable shallow conclusion costs zero further calls.
    assert main(["qualify", "--yes", "--json"]) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["tier"] == "shallow"
    assert second["cache_reused"] is True
    assert second["maximum_expected_provider_calls"] == 0
    assert battery_calls == [6]


def test_qualify_concludes_unqualified_when_both_batteries_fail(
    tmp_path, monkeypatch, capsys
):
    state, _profile_value = _configure(monkeypatch, tmp_path)
    _fail_full_battery(monkeypatch)
    _stub_battery(monkeypatch, valid=2)

    assert main(["qualify", "--yes", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["tier"] == "unqualified"
    assert payload["qualification_state"] == "unqualified"
    assert payload["next_action"] == "deepreason qualify"
    record = load_qualification_tier(
        state / "qualification-cache", payload["qualification_subject_digest"]
    )
    assert record.tier == "unqualified"


def test_qualify_rerun_after_unqualified_retries_and_can_upgrade(
    tmp_path, monkeypatch, capsys
):
    state, _profile_value = _configure(monkeypatch, tmp_path)
    _fail_full_battery(monkeypatch)
    _stub_battery(monkeypatch, valid=1)
    assert main(["qualify", "--yes", "--json"]) == 1
    capsys.readouterr()
    # The model (or provider) improved: an explicit rerun retries the ladder
    # and lawfully replaces the durable floor with a shallow conclusion.
    _stub_battery(monkeypatch, valid=6)
    assert main(["qualify", "--yes", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tier"] == "shallow"
    subject = payload["qualification_subject_digest"]
    assert load_qualification_tier(state / "qualification-cache", subject).tier == (
        "shallow"
    )


def test_qualify_announces_both_battery_ceilings(tmp_path, monkeypatch, capsys):
    _configure(monkeypatch, tmp_path)
    monkeypatch.setattr("sys.stdin", type("NoTty", (), {"isatty": staticmethod(lambda: False)})())
    assert main(["qualify"]) == 1
    err = capsys.readouterr().err
    # 840 base calls plus the bounded flake re-exercise allowance: the three
    # most expensive pair blocks may each be redrawn once. Seating the
    # reviewer role adds its contract to the pair inventory, and the ceiling
    # is the direct price of that seat: 1100 -> 1140.
    assert "maximum expected provider calls: 1140." in err
    assert f"at most {SHALLOW_FITNESS_MAX_PROVIDER_CALLS} further calls" in err
    assert shallow_fitness_maximum_provider_calls() == 18


def test_full_tier_qualify_payload_names_its_tier(tmp_path, monkeypatch, capsys):
    state, profile = _configure(monkeypatch, tmp_path)
    _qualify(state, profile)
    assert main(["qualify", "--yes", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tier"] == "full"
    assert payload["qualification_state"] == "ready"
    assert payload["cache_reused"] is True


# --------------------------------------------------------------------------
# Readiness projection


def test_readiness_projects_the_recorded_tier(tmp_path, monkeypatch):
    state, profile = _configure(monkeypatch, tmp_path)
    unqualified = get_readiness()
    assert unqualified.qualification_state == "unqualified"

    _write_tier(state, profile, valid=6)
    shallow = get_readiness()
    assert shallow.ready is False
    assert shallow.qualification_state == "ready_shallow"
    assert shallow.next_action == 'deepreason reason --shallow "YOUR QUESTION"'

    _write_tier(state, profile, valid=3)
    floor = get_readiness()
    assert floor.ready is False
    assert floor.qualification_state == "unqualified"
    assert floor.next_action == "deepreason qualify"

    _qualify(state, profile)
    full = get_readiness()
    assert full.ready is True
    assert full.qualification_state == "ready"


def test_tier_record_is_invalidated_by_subject_changes(tmp_path, monkeypatch):
    state, profile = _configure(monkeypatch, tmp_path)
    _write_tier(state, profile, valid=6)
    assert get_readiness().qualification_state == "ready_shallow"
    # A changed provider behavior subject must not inherit the old tier.
    changed = _profile(model_id="model-public-v6-changed")
    write_provider_profile(
        changed, state / "provider.yaml"
    )
    monkeypatch.setenv("DEEPREASON_PUBLIC_TEST_KEY", "never-print-this-secret")
    assert get_readiness().qualification_state == "unqualified"


# --------------------------------------------------------------------------
# Full `reason` refuses a shallow-tier subject with a typed error


def test_full_reason_refuses_shallow_tier_with_typed_error(tmp_path, monkeypatch):
    state, profile = _configure(monkeypatch, tmp_path)
    _write_tier(state, profile, valid=6)
    service = RunPreparationService()
    with pytest.raises(QualificationError) as caught:
        service.prepare(
            RunPreparationRequestV1(question="A full question on a shallow tier?")
        )
    assert caught.value.code == "QUALIFICATION_TIER_SHALLOW"
    assert "shallow" in str(caught.value)
    assert 'deepreason reason --shallow "YOUR QUESTION"' in str(caught.value)
    assert not (state / "runs").exists()


def test_full_reason_cli_prints_the_tier_refusal(tmp_path, monkeypatch, capsys):
    state, profile = _configure(monkeypatch, tmp_path)
    _write_tier(state, profile, valid=6)
    assert main(["reason", "A full question on a shallow tier?"]) == 1
    err = capsys.readouterr().err
    assert "QUALIFICATION_TIER_SHALLOW" in err
    assert 'deepreason reason --shallow "YOUR QUESTION"' in err


def test_recorded_unqualified_tier_keeps_qualify_as_next_action(
    tmp_path, monkeypatch
):
    state, profile = _configure(monkeypatch, tmp_path)
    _write_tier(state, profile, valid=2)
    manifest = qualification_subject_manifest(profile)
    with pytest.raises(QualificationError) as caught:
        resolve_completed_qualification(
            manifest, profile, cache_dir=state / "qualification-cache"
        )
    assert caught.value.code == "QUALIFICATION_TIER_UNQUALIFIED"
    assert "deepreason qualify" in str(caught.value)


# --------------------------------------------------------------------------
# The live shallow-fitness battery protocol (scripted endpoint, no network)


def _valid_response() -> str:
    return json.dumps(
        {
            "candidates": [
                {"content": "A bounded criticizable mechanism.", "typicality": 0.4},
                {"content": "A rival bounded mechanism.", "typicality": 0.3},
            ]
        }
    )


def test_battery_records_first_pass_and_repaired_cases():
    profile = _profile()
    dispatched = []

    def respond(prompt: str) -> str:
        dispatched.append(prompt)
        # The second case needs one whole-object repair; everything else
        # validates first pass.
        if len(dispatched) == 2:
            return "never json"
        return _valid_response()

    cases = run_shallow_fitness_battery(
        profile, endpoint=MockEndpoint(respond, model=profile.model_id)
    )
    assert len(cases) == SHALLOW_FITNESS_CASES
    assert cases[0].first_pass_valid is True
    assert cases[1].first_pass_valid is False
    assert cases[1].eventual_valid is True
    assert cases[1].repair_count == 1
    assert all(case.eventual_valid for case in cases)
    # 6 cases + 1 repair; the wire schema and example are advertised.
    assert len(dispatched) == SHALLOW_FITNESS_CASES + 1
    assert "JSON Schema" in dispatched[0]
    assert "Shallow-fitness case 001" in dispatched[0]


def test_battery_bounds_repairs_per_minis_protocol():
    profile = _profile()
    dispatched = []

    def respond(prompt: str) -> str:
        dispatched.append(prompt)
        return "never json"

    cases = run_shallow_fitness_battery(
        profile, endpoint=MockEndpoint(respond, model=profile.model_id)
    )
    assert all(not case.eventual_valid for case in cases)
    assert all(case.repair_count == 2 for case in cases)
    assert all(case.failure_code is not None for case in cases)
    # Initial + exactly two bounded repairs per case, never more.
    assert len(dispatched) == SHALLOW_FITNESS_CASES * 3
    assert len(dispatched) == SHALLOW_FITNESS_MAX_PROVIDER_CALLS


def test_battery_aborts_on_transport_failure_without_recording_a_tier():
    profile = _profile()

    def respond(_prompt: str) -> str:
        raise EndpointError("HTTP 503: provider outage with secret body")

    with pytest.raises(QualificationError) as caught:
        run_shallow_fitness_battery(
            profile, endpoint=MockEndpoint(respond, model=profile.model_id)
        )
    assert caught.value.code == "QUALIFICATION_SHALLOW_EXECUTION_FAILED"
    assert "secret body" not in str(caught.value)
    assert caught.value.__cause__ is None
