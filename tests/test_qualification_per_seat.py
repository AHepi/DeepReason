"""Rung S4 (qualification per seat): the measurement that authorizes
combination-subject qualification (SPEC.md M5), plus the per-profile
qualify loop and per-seat status this rung adds.

Regression (experiments/2026-08-06-change-qualification-per-seat-s4/,
operator amendment R11): S2's SM9 named "does a heterogeneous
manifest's battery dispatch each case to its own role's bound
endpoint" as untested. This module tests it for real.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from deepreason.cli.doctor import (
    exercise_production_contract_case,
    production_contract_pairs,
)
from deepreason.preparation import build_preparation_manifest
from deepreason.provider_profile import ProviderProfileV1
import deepreason.llm.adapter as adapter_mod


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
