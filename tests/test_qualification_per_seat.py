"""Rung S4 (qualification per seat): the measurement that authorizes
combination-subject qualification (SPEC.md M5), plus the per-profile
qualify loop and per-seat status this rung adds.

Regression (experiments/2026-08-06-change-qualification-per-seat-s4/,
operator amendment R11): S2's SM9 named "does a heterogeneous
manifest's battery dispatch each case to its own role's bound
endpoint" as untested. This module tests it for real.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    exercise_production_contract_case,
    production_contract_pairs,
    run_production_contract_doctor,
)
from deepreason.cli.main import main
from deepreason.preparation import build_preparation_manifest
from deepreason.provider_profile import (
    ProviderProfileV1,
    setup_provider_profile_path,
    write_provider_profile,
)
import deepreason.llm.adapter as adapter_mod

TRANCHE_DIR = Path(__file__).parent.parent / "experiments" / "2026-08-06-change-qualification-per-seat-s4"


def _qualified_report(manifest):
    return run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: ProductionContractCaseResultV1(
            case_id=f"case-{index + 1:03d}",
            first_pass_valid=True,
            eventual_valid=True,
            repair_count=0,
            semantic_admission=True,
        ),
    )


def _capture_test_profile(**updates):
    values = {
        "provider": "generic",
        "endpoint": "https://example.invalid/v1",
        "model_id": "capture-test-model",
        "family": "fixture",
        "context_window_tokens": 65536,
        "maximum_completion_tokens": 4096,
        "credential_env": "DEEPREASON_S4_CAPTURE_KEY",
        "output_mechanism": "native_json_schema",
    }
    values.update(updates)
    return ProviderProfileV1.create(**values)


def _profile(**updates):
    values = {
        "provider": "openai",
        "endpoint": "https://api.example.com/v1",
        "model_id": "model-default",
        "model_revision": "rev-a",
        "family": "family-a",
        "context_window_tokens": 262144,
        "maximum_completion_tokens": 4096,
        "credential_env": "DEEPREASON_TEST_KEY",
    }
    values.update(updates)
    return ProviderProfileV1.create(**values)


class _FakeEndpoint:
    """Records every dispatched model_id into a shared log; returns a
    deliberately schema-invalid stub so repair retries also get logged
    (purity must survive retries, not only the first attempt)."""

    def __init__(self, model_id, dispatch_log):
        self.model_id = model_id
        self.model = model_id
        self.name = "https://api.example.com/v1"
        self.family = "family-a"
        self.model_revision = "rev-a"
        self.context_window_tokens = 262144
        self.max_tokens = 4096
        self.last_finish_reason = None
        self.last_usage = None
        self.last_mean_surprisal = None
        self.last_transport_diagnostics = ()
        self.last_transport_attempts = 1
        self._dispatch_log = dispatch_log

    def complete(self, request, **kwargs):
        self._dispatch_log.append(self.model_id)
        return "{}"


def _heterogeneous_manifest():
    default_profile = _profile(model_id="model-default")
    profile_a = _profile(model_id="model-a")
    profile_b = _profile(model_id="model-b")
    manifest = build_preparation_manifest(
        default_profile,
        question="Why is the sky blue?",
        compiled_at=datetime(2026, 8, 6, tzinfo=timezone.utc).isoformat(),
        seat_bindings={"conjecturer": profile_a, "judge": profile_b},
    )
    pairs = production_contract_pairs(manifest)
    by_role = {}
    for pair in pairs:
        by_role.setdefault(pair.role, []).append(pair)
    return manifest, by_role


def test_heterogeneous_manifest_dispatches_with_zero_cross_contamination(
    monkeypatch,
):
    """SM9, measured (SPEC.md M5): every dispatched call for a role --
    including schema-repair retries -- targets exactly that role's own
    bound model, never another role's, in one heterogeneous manifest."""

    _manifest, by_role = _heterogeneous_manifest()
    dispatch_log = []
    monkeypatch.setattr(
        adapter_mod,
        "_endpoint_from_spec",
        lambda spec: _FakeEndpoint(spec.get("model"), dispatch_log),
    )

    for role, expected_model in (
        ("conjecturer", "model-a"),
        ("judge", "model-b"),
        ("summarizer", "model-default"),
    ):
        dispatch_log.clear()
        pair = by_role[role][0]
        assert pair.model_id == expected_model
        try:
            exercise_production_contract_case(_manifest, pair, 0)
        except Exception:
            pass  # the stub response is deliberately invalid; only dispatch matters here
        assert dispatch_log, f"role {role} never dispatched"
        assert all(m == expected_model for m in dispatch_log), (
            f"role {role} expected only {expected_model!r}, saw {dispatch_log}"
        )


def test_dispatch_purity_mutation_companion_can_actually_fail(monkeypatch):
    """Mutation companion: prove the purity assertion above is not
    vacuous by wiring judge's cases to conjecturer's endpoint and
    confirming the SAME assertion shape catches it."""

    _manifest, by_role = _heterogeneous_manifest()
    dispatch_log = []

    def cross_wired_endpoint_from_spec(spec):
        # Every call resolves to "model-a" regardless of the requested
        # spec -- simulates a hypothetical regression where role
        # identity is lost before endpoint construction.
        return _FakeEndpoint("model-a", dispatch_log)

    monkeypatch.setattr(
        adapter_mod, "_endpoint_from_spec", cross_wired_endpoint_from_spec
    )

    dispatch_log.clear()
    pair = by_role["judge"][0]
    assert pair.model_id == "model-b"
    try:
        exercise_production_contract_case(_manifest, pair, 0)
    except Exception:
        pass
    assert dispatch_log
    with pytest.raises(AssertionError):
        assert all(m == pair.model_id for m in dispatch_log)


def test_single_profile_home_qualify_output_is_byte_identical_to_pre_s4(
    tmp_path, monkeypatch, capsys
):
    """S2/R6 (SPEC.md Item S6): with no `--seat` bindings, the per-profile
    loop's combination call (seat_bindings=None) IS its one and only
    iteration -- the printed payload must be byte-identical in shape (and,
    given the same fixture inputs as the tranche's before-capture, in
    content) to `before-qualify.json`, captured before this rung's src/
    edits landed."""

    home = tmp_path / "home"
    monkeypatch.setenv("DEEPREASON_HOME", str(home))
    monkeypatch.setenv("DEEPREASON_S4_CAPTURE_KEY", "not-a-real-secret")
    write_provider_profile(
        _capture_test_profile(), setup_provider_profile_path(environ=os.environ)
    )

    with patch(
        "deepreason.qualification.default_qualification_executor",
        _qualified_report,
    ):
        main(["qualify", "--yes", "--json"])
    payload = json.loads(capsys.readouterr().out)

    before_payload = json.loads((TRANCHE_DIR / "before-qualify.json").read_text())
    assert set(payload) == set(before_payload)
    assert payload["schema"] == "deepreason-qualification-result.v1"
    assert payload == before_payload


def test_two_profile_home_qualifies_each_seat_plus_the_combination(
    tmp_path, monkeypatch, capsys
):
    """S2 (SPEC.md Item S2): a two-distinct-profile home -- the per-profile
    loop qualifies the default AND the one distinct bound profile, AND the
    existing combination call still qualifies the heterogeneous
    combination -- output names all three outcomes distinctly, none
    conflated."""

    from deepreason.seat_bindings import seat_bindings_path, write_seat_bindings

    home = tmp_path / "home"
    monkeypatch.setenv("DEEPREASON_HOME", str(home))
    monkeypatch.setenv("DEEPREASON_S4_CAPTURE_KEY", "not-a-real-secret")
    default_profile = _capture_test_profile()
    write_provider_profile(
        default_profile, setup_provider_profile_path(environ=os.environ)
    )
    bound_profile = _capture_test_profile(model_id="capture-bound-model")
    bound_path = tmp_path / "bound-profile.yaml"
    write_provider_profile(bound_profile, bound_path)
    write_seat_bindings(
        {"coder": str(bound_path)}, seat_bindings_path(environ=os.environ)
    )

    with patch(
        "deepreason.qualification.default_qualification_executor",
        _qualified_report,
    ):
        main(["qualify", "--yes", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert payload["schema"] == "deepreason-qualification-result-per-seat.v1"
    assert set(payload) == {"schema", "combination", "seats"}
    assert payload["combination"]["model_id"] == default_profile.model_id
    assert set(payload["seats"]) == {"coder"}
    assert payload["seats"]["coder"]["model_id"] == bound_profile.model_id
    # None of the three outcomes are conflated: distinct subject digests.
    digests = {
        payload["combination"]["qualification_subject_digest"],
        payload["seats"]["coder"]["qualification_subject_digest"],
    }
    assert len(digests) == 2


def test_seat_readiness_two_bound_groups_independent_of_combination(
    tmp_path, monkeypatch
):
    """S3 (SPEC.md Item S3): two bound seat groups produce 2
    SeatReadinessV1 entries with correct per-profile qualification_state
    -- independent of whether the COMBINATION itself has ever been
    qualified (it is never qualified in this test)."""

    from deepreason.preparation import qualification_subject_manifest
    from deepreason.provider_profile import provider_state_dir
    from deepreason.qualification import resolve_completed_qualification
    from deepreason.readiness import SeatReadinessV1, get_seat_readiness
    from deepreason.seat_bindings import seat_bindings_path, write_seat_bindings

    home = tmp_path / "home"
    monkeypatch.setenv("DEEPREASON_HOME", str(home))
    monkeypatch.setenv("DEEPREASON_S4_CAPTURE_KEY", "not-a-real-secret")

    default_profile = _capture_test_profile()
    write_provider_profile(
        default_profile, setup_provider_profile_path(environ=os.environ)
    )

    ready_profile = _capture_test_profile(model_id="capture-ready-model")
    ready_path = tmp_path / "ready-profile.yaml"
    write_provider_profile(ready_profile, ready_path)

    unqualified_profile = _capture_test_profile(model_id="capture-unqualified-model")
    unqualified_path = tmp_path / "unqualified-profile.yaml"
    write_provider_profile(unqualified_profile, unqualified_path)

    write_seat_bindings(
        {"coder": str(ready_path), "scratch": str(unqualified_path)},
        seat_bindings_path(environ=os.environ),
    )

    cache_dir = provider_state_dir(environ=os.environ) / "qualification-cache"
    ready_manifest = qualification_subject_manifest(ready_profile)
    resolve_completed_qualification(
        ready_manifest, ready_profile, cache_dir=cache_dir, executor=_qualified_report
    )
    # unqualified_profile's own uniform subject is deliberately never
    # qualified; neither is the (default + coder + scratch) combination.

    entries = get_seat_readiness(environ=os.environ)
    assert len(entries) == 2
    assert all(isinstance(entry, SeatReadinessV1) for entry in entries)
    by_group = {entry.group: entry for entry in entries}
    assert set(by_group) == {"coder", "scratch"}
    assert by_group["coder"].qualification_state == "ready"
    assert by_group["coder"].ready is True
    assert by_group["scratch"].qualification_state == "unqualified"
    assert by_group["scratch"].ready is False


def test_status_single_profile_home_output_is_byte_identical_to_pre_s4(
    tmp_path, monkeypatch, capsys
):
    """S4/R6 (SPEC.md Item S6): with no seat bindings, get_seat_readiness()
    returns () so `_cmd_status`'s new per-seat branch is never taken --
    output must be byte-identical to before-status.json, captured before
    this rung's src/ edits landed."""

    home = tmp_path / "home"
    monkeypatch.setenv("DEEPREASON_HOME", str(home))
    monkeypatch.setenv("DEEPREASON_S4_CAPTURE_KEY", "not-a-real-secret")
    write_provider_profile(
        _capture_test_profile(), setup_provider_profile_path(environ=os.environ)
    )

    with patch(
        "deepreason.qualification.default_qualification_executor",
        _qualified_report,
    ):
        main(["qualify", "--yes", "--json"])
        capsys.readouterr()  # discard qualify's own stdout
        main(["status", "--json"])
    payload = json.loads(capsys.readouterr().out)

    before_payload = json.loads((TRANCHE_DIR / "before-status.json").read_text())
    assert payload == before_payload


def test_status_two_seat_home_names_both_seats(tmp_path, monkeypatch, capsys):
    """S4 (SPEC.md Item S4): a two-seat home's `deepreason status --json`
    additionally names both bound groups in a "seats" key."""

    from deepreason.seat_bindings import seat_bindings_path, write_seat_bindings

    home = tmp_path / "home"
    monkeypatch.setenv("DEEPREASON_HOME", str(home))
    monkeypatch.setenv("DEEPREASON_S4_CAPTURE_KEY", "not-a-real-secret")
    write_provider_profile(
        _capture_test_profile(), setup_provider_profile_path(environ=os.environ)
    )
    bound_a = _capture_test_profile(model_id="capture-seat-a")
    bound_a_path = tmp_path / "seat-a.yaml"
    write_provider_profile(bound_a, bound_a_path)
    bound_b = _capture_test_profile(model_id="capture-seat-b")
    bound_b_path = tmp_path / "seat-b.yaml"
    write_provider_profile(bound_b, bound_b_path)
    write_seat_bindings(
        {"coder": str(bound_a_path), "scratch": str(bound_b_path)},
        seat_bindings_path(environ=os.environ),
    )

    main(["status", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert "seats" in payload
    groups = {entry["group"] for entry in payload["seats"]}
    assert groups == {"coder", "scratch"}
    models = {entry["route_identity"]["model_id"] for entry in payload["seats"]}
    assert models == {"capture-seat-a", "capture-seat-b"}
