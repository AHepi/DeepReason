"""Frozen route-seat presentation authority for newly compiled v6 manifests."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.config import Config
from deepreason.llm.capabilities import CapabilityCache, ModelCapabilities
from deepreason.ontology import Commitment
from deepreason.run_manifest import (
    RouteSeatPresentationPlanV1,
    RunManifest,
    RunManifestError,
    bind_run_manifest,
    compile_run_manifest,
    load_run_manifest,
    write_run_manifest,
)
from tests.test_run_input_v6_commitments import _control


STAMP = "2026-07-20T00:00:00Z"
DIGEST = "6" * 64


def _route(
    endpoint_id: str,
    *,
    model_profile: str | None = None,
    family: str = "offline",
) -> dict:
    route = {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": f"model-{endpoint_id}",
        "provider": "mock",
        "family": family,
        "max_tokens": 64,
        "context_window_tokens": 262_144,
    }
    if model_profile is not None:
        route["model_profile"] = model_profile
    return route


def _compile(
    roles: dict,
    *,
    model_profile: str | None = None,
    capability_cache=None,
    run_input_digest: str = DIGEST,
):
    config_values = {"roles": roles}
    if model_profile is not None:
        config_values["model_profile"] = model_profile
    return compile_run_manifest(
        Config(**config_values),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        capability_cache=capability_cache,
        control_plane_policy=_control(6),
        run_input_digest=run_input_digest,
    )


def _entries(manifest) -> dict[tuple[str, int], tuple[str, str, str]]:
    plan = manifest.route_seat_presentation_plan
    assert isinstance(plan, RouteSeatPresentationPlanV1)
    return {
        (entry.role, entry.seat): (
            entry.endpoint_id,
            entry.base_profile,
            entry.selection_basis,
        )
        for entry in plan.entries
    }


def test_v6_plan_covers_every_concrete_seat_with_independent_defaults():
    manifest = _compile(
        {
            "conjecturer": _route("conj"),
            "argumentative_critic": [_route("critic-a"), _route("critic-b")],
            "summarizer": _route("summary"),
        },
        model_profile="frontier",
    )

    assert _entries(manifest) == {
        ("argumentative_critic", 0): (
            "critic-a", "frontier", "manifest_default"
        ),
        ("argumentative_critic", 1): (
            "critic-b", "frontier", "manifest_default"
        ),
        ("conjecturer", 0): ("conj", "frontier", "manifest_default"),
        ("summarizer", 0): ("summary", "frontier", "manifest_default"),
    }
    keys = tuple((entry.role, entry.seat) for entry in manifest.route_seat_presentation_plan.entries)
    assert keys == tuple(sorted(keys))


def test_endpoint_overrides_create_heterogeneous_authority_without_drift():
    manifest = _compile(
        {
            "conjecturer": _route("conj", model_profile="compact"),
            "argumentative_critic": [
                _route("critic-a", model_profile="standard"),
                _route("critic-b", model_profile="frontier"),
            ],
            "summarizer": _route("summary", model_profile="compact"),
            "thesis": _route("thesis", model_profile="frontier"),
        },
        model_profile="standard",
    )

    entries = _entries(manifest)
    assert entries[("conjecturer", 0)] == (
        "conj", "compact", "explicit_endpoint"
    )
    assert entries[("argumentative_critic", 0)] == (
        "critic-a", "standard", "explicit_endpoint"
    )
    assert entries[("argumentative_critic", 1)] == (
        "critic-b", "frontier", "explicit_endpoint"
    )
    assert entries[("summarizer", 0)] == (
        "summary", "compact", "explicit_endpoint"
    )
    assert entries[("thesis", 0)] == (
        "thesis", "frontier", "explicit_endpoint"
    )
    assert manifest.model_profile == "standard"


def test_one_endpoint_override_changes_only_its_own_entry():
    roles = {
        "conjecturer": _route("conj"),
        "argumentative_critic": _route("critic"),
    }
    baseline = _compile(roles)
    changed_roles = json.loads(json.dumps(roles))
    changed_roles["conjecturer"]["model_profile"] = "compact"
    changed = _compile(changed_roles)

    before = _entries(baseline)
    after = _entries(changed)
    assert after[("conjecturer", 0)] == (
        "conj", "compact", "explicit_endpoint"
    )
    assert after[("argumentative_critic", 0)] == before[
        ("argumentative_critic", 0)
    ]
    assert baseline.sha256 != changed.sha256


def test_v6_capability_cache_cannot_select_global_presentation(tmp_path):
    cache = CapabilityCache(tmp_path / "capabilities.json")
    cache.put(
        ModelCapabilities(
            provider="mock",
            endpoint="mock://conj",
            model="model-conj",
            native_json_schema=True,
        )
    )

    manifest = _compile({"conjecturer": _route("conj")}, capability_cache=cache)

    assert manifest.model_profile == "standard"
    assert _entries(manifest)[("conjecturer", 0)] == (
        "conj", "standard", "manifest_default"
    )
    # Transport-mechanism qualification remains independently frozen.
    assert manifest.roles["conjecturer"][0].output_mechanism == "native_json_schema"


@pytest.mark.parametrize(
    "mutation",
    (
        lambda plan: plan["entries"].pop(),
        lambda plan: plan["entries"].append(
            {
                "role": "conjecturer",
                "seat": 1,
                "endpoint_id": "extra",
                "base_profile": "standard",
                "selection_basis": "manifest_default",
            }
        ),
        lambda plan: plan["entries"].append(dict(plan["entries"][0])),
        lambda plan: plan["entries"].reverse(),
        lambda plan: plan["entries"][0].update(endpoint_id="foreign"),
        lambda plan: plan["entries"][0].update(base_profile="tiny"),
        lambda plan: plan["entries"][0].update(selection_basis="cache"),
        lambda plan: plan["entries"][0].update(unexpected=True),
    ),
    ids=(
        "missing",
        "extra",
        "duplicate",
        "unsorted",
        "wrong-endpoint",
        "bad-profile",
        "bad-basis",
        "unknown-field",
    ),
)
def test_v6_plan_rejects_malformed_or_inexact_coverage(mutation):
    manifest = _compile(
        {
            "conjecturer": _route("conj"),
            "argumentative_critic": _route("critic"),
        }
    )
    payload = json.loads(manifest.canonical_bytes())
    mutation(payload["route_seat_presentation_plan"])

    with pytest.raises(ValidationError):
        RunManifest.model_validate(payload)


def test_historical_v6_absence_is_stable_and_grants_no_override():
    current = _compile({"conjecturer": _route("conj", model_profile="compact")})
    payload = json.loads(current.canonical_bytes())
    payload.pop("route_seat_presentation_plan")
    payload.pop("route_seat_behavioral_capability_plan")
    expected = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()

    historical = RunManifest.model_validate(payload)

    assert historical.route_seat_presentation_plan is None
    assert "route_seat_presentation_plan" not in historical.model_dump(mode="json")
    assert historical.canonical_bytes() == expected
    assert historical.sha256 != current.sha256


@pytest.mark.parametrize("schema_version", (1, 2, 3, 4, 5))
def test_pre_v6_compilation_rejects_endpoint_profile_override(schema_version):
    with pytest.raises(RunManifestError) as raised:
        compile_run_manifest(
            Config(
                roles={
                    "conjecturer": _route("conj", model_profile="compact")
                }
            ),
            schema_version=schema_version,
            workload_profile="text" if schema_version >= 2 else None,
            rubric_policy="forbid",
            compiled_at=STAMP,
        )

    assert raised.value.code == "ROUTE_SEAT_PRESENTATION_MANIFEST_V6_REQUIRED"


def test_pre_v6_manifest_rejects_explicit_plan_field():
    current = _compile({"conjecturer": _route("conj")})
    payload = json.loads(current.canonical_bytes())
    payload["schema_version"] = 5

    with pytest.raises(ValidationError, match="v1-v5 manifests cannot carry"):
        RunManifest.model_validate(payload)


def test_serialization_reload_and_binding_include_exact_plan(tmp_path):
    from tests.test_run_input_v6_commitments import _bind_v2

    root = tmp_path / "root"
    run_input = _bind_v2(
        root, Commitment(id="gate-6a-binding", eval="predicate:True")
    )
    standard = _compile(
        {"conjecturer": _route("conj")},
        run_input_digest=run_input.run_input_digest,
    )
    explicit = _compile(
        {"conjecturer": _route("conj", model_profile="standard")},
        run_input_digest=run_input.run_input_digest,
    )
    assert standard.route_seat_presentation_plan != explicit.route_seat_presentation_plan
    assert standard.canonical_bytes() != explicit.canonical_bytes()
    assert standard.sha256 != explicit.sha256

    path, _digest = write_run_manifest(standard, tmp_path / "manifest.json")
    assert load_run_manifest(path) == standard
    bind_run_manifest(standard, root)
    with pytest.raises(RunManifestError) as raised:
        bind_run_manifest(explicit, root)
    assert raised.value.code == "RUN_MANIFEST_CONFLICT"


def test_existing_v6_authority_policies_are_unchanged():
    manifest = _compile({"conjecturer": _route("conj")})

    assert manifest.provider_fallback is False
    assert manifest.compact_recovery_policy is not None
    assert manifest.contract_schema_repair_policy is not None
