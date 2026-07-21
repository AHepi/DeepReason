"""Compiled source config: concrete, immutable, secret-free routes."""

import json
import pytest

from deepreason.config import Config, EndpointSpec
from deepreason.harness import Harness
from deepreason.locking import operator_locks
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.run_manifest import (
    CompactRecoveryPolicyV1,
    Route,
    RouteSecretError,
    RunManifest,
    RunManifestError,
    ToolchainEntry,
    TerminalCommitmentPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
    config_from_run_manifest,
    load_run_manifest,
    persist_run_manifest,
    preflight_harness,
    preflight_payload,
    role_matrix,
    write_run_manifest,
)
from deepreason.llm.firewall import route_fingerprint


STAMP = "2026-07-11T00:00:00Z"


def _route(model="gemma4:31b", *, family="gemma", endpoint="https://ollama.invalid/v1"):
    return {
        "endpoint": endpoint,
        "model": model,
        "provider": "ollama",
        "family": family,
        "api_key_env": "OLLAMA_API_KEY",
        "temperature": 0.2,
        "reasoning": "none",
        "json_mode": True,
    }


def _config():
    route = _route()
    return Config(
        roles={
            "conjecturer": route,
            "argumentative_critic": route,
            "defender": route,
            "variator": route,
            "judge": [route, route],
            "summarizer": route,
            "synthesizer": route,
        }
    )


def _compile_v6_manifest(
    model_profile: str = "standard",
    *,
    run_input_digest: str = "a" * 64,
):
    from tests.test_run_input_v6_commitments import _config as v6_config
    from tests.test_run_input_v6_commitments import _control

    return compile_run_manifest(
        v6_config(),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        model_profile=model_profile,
        control_plane_policy=_control(6),
        run_input_digest=run_input_digest,
    )


def _compact_recovery_policy_payload() -> dict:
    return {
        "schema": "compact-recovery-policy.v1",
        "trigger": "schema_exhausted",
        "source_profiles": ["standard", "frontier"],
        "target_profile": "compact",
        "scope": "route_seat",
        "sticky": True,
        "applies_to": "all_subsequent_model_calls",
        "retry_failed_work": False,
    }


@pytest.mark.parametrize("model_profile", ("standard", "frontier", "compact"))
def test_new_v6_manifest_freezes_exact_compact_recovery_policy(model_profile):
    manifest = _compile_v6_manifest(model_profile)

    assert manifest.compact_recovery_policy is not None
    assert manifest.compact_recovery_policy.model_dump(
        mode="json", by_alias=True
    ) == _compact_recovery_policy_payload()
    assert manifest.provider_fallback is False


@pytest.mark.parametrize("schema_version", (1, 2, 3, 4, 5))
def test_pre_v6_manifests_omit_compact_recovery_policy(schema_version):
    if schema_version <= 3:
        manifest = compile_run_manifest(
            _config(),
            single_model="gemma4:31b",
            model_profile="standard",
            rubric_policy="forbid",
            compiled_at=STAMP,
            schema_version=schema_version,
            workload_profile="text" if schema_version >= 2 else None,
        )
    elif schema_version == 4:
        from tests.test_run_manifest_v4 import (
            _compile_v4,
            _control_policy,
            _historical_config,
        )

        manifest = _compile_v4(_historical_config(), _control_policy())
    else:
        from tests.test_run_manifest_v5_inquiry import _compile

        manifest = _compile("b" * 64)

    assert manifest.compact_recovery_policy is None
    assert "compact_recovery_policy" not in manifest.model_dump(mode="json")
    assert b"compact_recovery_policy" not in manifest.canonical_bytes()
    assert manifest.route_seat_presentation_plan is None
    assert "route_seat_presentation_plan" not in manifest.model_dump(mode="json")
    assert b"route_seat_presentation_plan" not in manifest.canonical_bytes()
    assert manifest.terminal_commitment_policy is None
    assert "terminal_commitment_policy" not in manifest.model_dump(mode="json")
    assert b"terminal_commitment_policy" not in manifest.canonical_bytes()
    with pytest.raises(ValueError, match="terminal commitment policy"):
        RunManifest.model_validate(
            {
                **manifest.model_dump(mode="json", by_alias=True),
                "terminal_commitment_policy": TerminalCommitmentPolicyV1().model_dump(
                    mode="json", by_alias=True
                ),
            }
        )


def test_historical_v6_without_policy_loads_without_authority(tmp_path):
    current = _compile_v6_manifest()
    payload = json.loads(current.canonical_bytes())
    payload.pop("compact_recovery_policy")
    payload.pop("route_seat_behavioral_capability_plan")
    path = tmp_path / "historical-v6.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    historical = load_run_manifest(path, verify_hash=False)

    assert historical.compact_recovery_policy is None
    assert "compact_recovery_policy" not in historical.model_dump(mode="json")
    assert b"compact_recovery_policy" not in historical.canonical_bytes()
    assert historical.sha256 != current.sha256


def test_compact_recovery_policy_serializes_hashes_and_reloads_exactly(tmp_path):
    manifest = _compile_v6_manifest("frontier")
    path, digest_path = write_run_manifest(manifest, tmp_path / "v6.json")

    assert path.read_bytes() == manifest.canonical_bytes()
    assert digest_path.read_text(encoding="utf-8").strip() == manifest.sha256
    assert load_run_manifest(path) == manifest
    assert json.loads(path.read_text(encoding="utf-8"))[
        "compact_recovery_policy"
    ] == _compact_recovery_policy_payload()


def test_compact_recovery_policy_presence_changes_binding_identity(tmp_path):
    from tests.test_run_input_v6_commitments import _bind_v2

    run_input = _bind_v2(
        tmp_path,
        Commitment(id="k-compact-recovery", eval="predicate:True"),
    )
    manifest = _compile_v6_manifest(run_input_digest=run_input.run_input_digest)
    historical_payload = json.loads(manifest.canonical_bytes())
    historical_payload.pop("compact_recovery_policy")
    historical_payload.pop("route_seat_behavioral_capability_plan")
    historical = RunManifest.model_validate(historical_payload)

    assert historical.compact_recovery_policy is None
    assert historical.sha256 != manifest.sha256
    bind_run_manifest(manifest, tmp_path)
    with pytest.raises(RunManifestError) as raised:
        bind_run_manifest(historical, tmp_path)
    assert raised.value.code == "RUN_MANIFEST_CONFLICT"


@pytest.mark.parametrize(
    ("field", "invalid"),
    (
        ("schema", "compact-recovery-policy.v2"),
        ("trigger", "model_requested"),
        ("source_profiles", ["standard", "compact"]),
        ("target_profile", "standard"),
        ("scope", "run"),
        ("sticky", False),
        ("applies_to", "next_model_call"),
        ("retry_failed_work", True),
    ),
)
def test_compact_recovery_policy_rejects_invalid_authority(field, invalid):
    payload = _compact_recovery_policy_payload()
    payload[field] = invalid

    with pytest.raises(ValueError):
        CompactRecoveryPolicyV1.model_validate(payload)


def test_compact_recovery_policy_rejects_unknown_fields():
    payload = _compact_recovery_policy_payload()
    payload["model_may_enable"] = True

    with pytest.raises(ValueError):
        CompactRecoveryPolicyV1.model_validate(payload)


@pytest.mark.parametrize(
    "schema_version,workload_profile,expected_manifest_hash",
    [
        (
            1,
            None,
            "0db633fcd924f213c4e00f0a2f1a16077100aef569a1b283dba8bdc0f58d3ac9",
        ),
        (
            2,
            "formal",
            "3448c0c2b8127dfcc86678476ebecb309949508f934693e00b6c482f6144a23a",
        ),
    ],
)
def test_legacy_manifest_hashes_are_stable_after_v3_install(
    schema_version, workload_profile, expected_manifest_hash
):
    manifest = compile_run_manifest(
        _config(),
        single_model="gemma4:31b",
        model_profile="compact",
        rubric_policy="forbid",
        compiled_at=STAMP,
        schema_version=schema_version,
        workload_profile=workload_profile,
    )

    assert manifest.sha256 == expected_manifest_hash
    assert manifest.source_config_hash == (
        "9ba01ebe9d81353776348348a8b850a7a76330f0099299b5f6c321b22677b7ae"
    )


def test_single_model_compiles_one_exact_route_for_every_active_role(monkeypatch):
    # Concrete single-model compilation must never perform discovery.
    monkeypatch.setattr(
        "deepreason.llm.endpoints.list_models",
        lambda *_args: pytest.fail("model discovery was called"),
    )
    manifest = compile_run_manifest(
        _config(), single_model="gemma4:31b", model_profile="compact",
        rubric_policy="forbid", compiled_at=STAMP,
    )

    rows = role_matrix(manifest)
    assert {row["model_id"] for row in rows} == {"gemma4:31b"}
    assert {row["endpoint_id"] for row in rows} == {rows[0]["endpoint_id"]}
    assert all(len(routes) == 1 for routes in manifest.roles.values() if routes)
    assert manifest.provider_fallback is False
    assert manifest.model_profile == "compact"
    assert {row["output_mechanism"] for row in rows} == {"json_text"}


def test_decoy_provider_is_not_resolved_or_copied_in_single_model_mode(monkeypatch):
    configured = _config().model_copy(deep=True)
    configured.roles["thesis"] = {
        "endpoint": "https://api.deepseek.invalid",
        "model": "auto",
        "provider": "deepseek",
        "api_key_env": "DEEPSEEK_API_KEY",
    }
    calls = []
    monkeypatch.setattr(
        "deepreason.run_manifest.resolve_model",
        lambda model, endpoint, key: calls.append((model, endpoint)) or model,
    )

    manifest = compile_run_manifest(
        configured, single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )

    assert calls and all(endpoint == "https://ollama.invalid/v1" for _, endpoint in calls)
    assert manifest.roles["thesis"][0].provider == "ollama"
    rebuilt = config_from_run_manifest(manifest)
    assert "deepseek" not in json.dumps(rebuilt.roles).lower()


def test_auto_is_resolved_once_during_non_single_compile(monkeypatch):
    configured = Config(roles={"conjecturer": _route(model="auto")})
    calls = []
    monkeypatch.setattr(
        "deepreason.run_manifest.resolve_model",
        lambda model, endpoint, key: calls.append((model, endpoint, key)) or "gemma4:31b",
    )
    monkeypatch.setenv("OLLAMA_API_KEY", "not-written")

    manifest = compile_run_manifest(
        configured, rubric_policy="forbid", compiled_at=STAMP,
    )

    assert calls == [("auto", "https://ollama.invalid/v1", "not-written")]
    assert manifest.roles["conjecturer"][0].model_id == "gemma4:31b"
    assert "not-written" not in manifest.canonical_bytes().decode()


@pytest.mark.parametrize(
    "endpoint,secret",
    [
        ("https://route-user:do-not-echo@example.invalid/v1", "do-not-echo"),
        ("https://example.invalid/v1?foo=sk-do-not-echo", "sk-do-not-echo"),
        ("https://example.invalid/v1#token=do-not-echo", "do-not-echo"),
    ],
)
def test_compile_rejects_credential_bearing_route_before_resolution(
    monkeypatch, endpoint, secret
):
    monkeypatch.setattr(
        "deepreason.run_manifest.resolve_model",
        lambda *_args: pytest.fail("route resolution was called"),
    )
    configured = Config(roles={"conjecturer": _route(endpoint=endpoint)})

    with pytest.raises(RunManifestError) as raised:
        compile_run_manifest(
            configured,
            single_model="gemma4:31b",
            rubric_policy="forbid",
            compiled_at=STAMP,
        )

    assert raised.value.code == "ROUTE_URL_CREDENTIAL_FORBIDDEN"
    assert secret not in str(raised.value)


def test_direct_route_validation_rejects_secret_without_echoing_value():
    secret = "direct-do-not-echo"
    with pytest.raises(RouteSecretError) as raised:
        Route(
            endpoint_id="unsafe",
            base_url=f"https://user:{secret}@example.invalid/v1",
            model_id="gemma4:31b",
            provider="ollama",
            family="gemma",
        )
    assert raised.value.code == "ROUTE_URL_CREDENTIAL_FORBIDDEN"
    assert secret not in str(raised.value)


@pytest.mark.parametrize("model", [EndpointSpec, Route])
def test_api_key_reference_must_be_an_env_identifier_without_echoing(model):
    secret = "credential.value-that-must-not-appear"
    values = {"api_key_env": secret}
    if model is Route:
        values.update(
            endpoint_id="route",
            base_url="https://example.invalid/v1",
            model_id="gemma4:31b",
            provider="ollama",
            family="gemma",
        )
    with pytest.raises(ValueError) as raised:
        model(**values)
    assert "environment-variable name" in str(raised.value)
    assert secret not in str(raised.value)


def test_config_does_not_echo_an_invalid_credential_reference():
    secret = "credential.value-that-must-not-appear"
    with pytest.raises(ValueError) as raised:
        Config(roles={
            "conjecturer": {
                "endpoint": "https://example.invalid/v1",
                "model": "gemma4:31b",
                "api_key_env": secret,
            }
        })
    error = str(raised.value)
    assert "environment-variable name" in error
    assert "must-not-appear" not in error


def test_single_model_route_is_rejected_when_model_id_is_ambiguous():
    first = _route(endpoint="https://cloud-a.invalid/v1")
    second = _route(endpoint="https://cloud-b.invalid/v1")
    configured = Config(roles={
        "conjecturer": first,
        "argumentative_critic": second,
    })
    with pytest.raises(RunManifestError) as raised:
        compile_run_manifest(
            configured,
            single_model="gemma4:31b",
            rubric_policy="forbid",
            compiled_at=STAMP,
        )
    assert raised.value.code == "SINGLE_MODEL_ROUTE_AMBIGUOUS"


def test_single_model_allows_role_specific_knobs_on_one_exact_endpoint():
    first = _route()
    second = _route()
    second.update(temperature=0.0, max_tokens=1234)
    manifest = compile_run_manifest(
        Config(roles={
            "conjecturer": first,
            "argumentative_critic": second,
        }),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    assert manifest.roles["conjecturer"][0] == manifest.roles["argumentative_critic"][0]
    assert manifest.roles["conjecturer"][0].temperature == first["temperature"]


def test_context_window_tokens_are_frozen_and_round_trip():
    route = _route()
    route.update(max_tokens=256, context_window_tokens=8192)
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    frozen = manifest.roles["conjecturer"][0]

    assert frozen.context_window_tokens == 8192
    assert frozen.endpoint_spec()["context_window_tokens"] == 8192
    rebuilt = config_from_run_manifest(manifest)
    assert rebuilt.roles["conjecturer"]["context_window_tokens"] == 8192

    changed_route = _route()
    changed_route.update(max_tokens=256, context_window_tokens=8193)
    changed = compile_run_manifest(
        Config(roles={"conjecturer": changed_route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    assert changed.sha256 != manifest.sha256
    assert route_fingerprint(changed.roles["conjecturer"][0]) != route_fingerprint(
        frozen
    )


def test_invalid_context_window_combinations_are_rejected():
    with pytest.raises(ValueError, match="requires a finite max_tokens"):
        EndpointSpec(context_window_tokens=8192)
    with pytest.raises(ValueError, match="greater than max_tokens"):
        EndpointSpec(max_tokens=256, context_window_tokens=256)
    with pytest.raises(ValueError, match="requires a finite max_tokens"):
        Route(
            endpoint_id="invalid",
            base_url="mock://invalid",
            model_id="offline-invalid",
            provider="mock",
            family="offline",
            context_window_tokens=8192,
        )
    with pytest.raises(ValueError, match="greater than max_tokens"):
        Route(
            endpoint_id="invalid",
            base_url="mock://invalid",
            model_id="offline-invalid",
            provider="mock",
            family="offline",
            max_tokens=256,
            context_window_tokens=128,
        )


def test_single_model_routes_with_different_context_capacity_are_ambiguous():
    first = _route()
    first.update(max_tokens=256, context_window_tokens=8192)
    second = _route()
    second.update(max_tokens=256, context_window_tokens=16384)
    with pytest.raises(RunManifestError) as raised:
        compile_run_manifest(
            Config(
                roles={
                    "conjecturer": first,
                    "argumentative_critic": second,
                }
            ),
            single_model="gemma4:31b",
            rubric_policy="forbid",
            compiled_at=STAMP,
        )
    assert raised.value.code == "SINGLE_MODEL_ROUTE_AMBIGUOUS"


def test_output_mechanism_is_explicitly_frozen_from_source():
    route = _route()
    route["output_mechanism"] = "native_json_schema"
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b", rubric_policy="forbid", compiled_at=STAMP,
    )
    assert manifest.roles["conjecturer"][0].output_mechanism == "native_json_schema"
    rebuilt = config_from_run_manifest(manifest)
    assert rebuilt.roles["conjecturer"]["output_mechanism"] == "native_json_schema"


def test_measured_output_mechanism_is_selected_once_at_compile(tmp_path):
    from deepreason.llm.capabilities import CapabilityCache, ModelCapabilities

    cache = CapabilityCache(tmp_path / "capabilities.json")
    cache.put(
        ModelCapabilities(
            provider="ollama",
            endpoint="https://ollama.invalid/v1",
            model="gemma4:31b",
            native_json_schema=True,
        )
    )
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": _route()}),
        single_model="gemma4:31b", rubric_policy="forbid",
        capability_cache=cache, compiled_at=STAMP,
    )
    assert manifest.roles["conjecturer"][0].output_mechanism == "native_json_schema"
    assert manifest.model_profile == "compact"

    explicit = compile_run_manifest(
        Config(model_profile="frontier", roles={"conjecturer": _route()}),
        single_model="gemma4:31b", rubric_policy="forbid",
        capability_cache=cache, compiled_at=STAMP,
    )
    assert explicit.model_profile == "frontier"


def test_source_profiles_compile_orthogonally_and_reconstruct():
    compact = Config(
        engine_profile="full", model_profile="compact",
        roles={"conjecturer": _route()},
    )
    manifest = compile_run_manifest(
        compact, single_model="gemma4:31b", rubric_policy="forbid", compiled_at=STAMP
    )
    assert manifest.engine_profile == "full"
    assert manifest.model_profile == "compact"
    assert manifest.concurrency == 1
    rebuilt = config_from_run_manifest(manifest)
    assert rebuilt.engine_profile == "full"
    assert rebuilt.model_profile == "compact"
    assert rebuilt.VS_K == 4
    assert rebuilt.PACK_TOKEN_BUDGET <= 1200

    frontier = compile_run_manifest(
        compact, single_model="gemma4:31b", model_profile="frontier",
        rubric_policy="forbid", compiled_at=STAMP,
    )
    assert frontier.concurrency == 4


def test_cross_family_rubric_policy_fails_preflight_for_one_family():
    with pytest.raises(RunManifestError, match="SECOND_JUDGE_FAMILY_REQUIRED") as raised:
        compile_run_manifest(
            _config(), single_model="gemma4:31b",
            rubric_policy="require_cross_family", compiled_at=STAMP,
        )
    assert raised.value.code == "SECOND_JUDGE_FAMILY_REQUIRED"


def test_second_explicit_family_is_allowed_without_fallback():
    configured = _config().model_copy(deep=True)
    configured.roles["judge"] = [
        _route(),
        {
            "endpoint": "https://second.invalid/v1",
            "endpoint_id": "second-route",
            "model": "qwen3:32b",
            "provider": "generic",
            "family": "qwen",
        },
    ]
    manifest = compile_run_manifest(
        configured, single_model="gemma4:31b", judge_family="second-route",
        rubric_policy="require_cross_family", compiled_at=STAMP,
    )
    assert [route.family for route in manifest.roles["judge"]] == ["gemma", "qwen"]
    assert manifest.provider_fallback is False


def test_rubric_forbid_rejects_rubric_input_before_runtime():
    manifest = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    with pytest.raises(RunManifestError, match="RUBRIC_INPUT_FORBIDDEN"):
        preflight_payload(
            manifest,
            {"problem": {"description": "judge prose"},
             "commitments": [{"id": "k", "eval": "rubric:std"}]},
        )


def _materialized_problem(harness, commitment):
    harness.register_commitment(commitment)
    harness.register_problem(Problem(
        id="pi-active",
        description="active materialized workload",
        criteria=[commitment.id],
        provenance=ProblemProvenance.model_validate(
            {"trigger": "seed", "from": []}
        ),
    ))


def test_materialized_rubric_reference_is_preflighted_on_resume(tmp_path):
    manifest = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    harness = Harness(tmp_path / "run")
    _materialized_problem(harness, Commitment(id="k-rubric", eval="rubric:std"))
    with pytest.raises(RunManifestError) as raised:
        preflight_harness(manifest, harness, config_from_run_manifest(manifest))
    assert raised.value.code == "RUBRIC_INPUT_FORBIDDEN"


def test_property_proposal_rubric_path_fails_before_any_model_call(tmp_path):
    configured = _config().model_copy(deep=True)
    configured.roles["property_designer"] = _route()
    manifest = compile_run_manifest(
        configured, single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    harness = Harness(tmp_path / "run")
    _materialized_problem(
        harness,
        Commitment(id="k-property", eval="program:property_oracle"),
    )
    with pytest.raises(RunManifestError) as raised:
        preflight_harness(manifest, harness, config_from_run_manifest(manifest))
    assert raised.value.code == "PROPERTY_RUBRIC_TRIAL_FORBIDDEN"


def test_manifest_is_immutable_canonical_and_hash_verified(tmp_path):
    manifest = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    path, digest_path = persist_run_manifest(manifest, tmp_path)
    assert path.name == "run-manifest.json"
    assert digest_path.name == "run-manifest.sha256"
    assert digest_path.read_text().strip() == manifest.sha256
    assert load_run_manifest(path) == manifest
    with pytest.raises(TypeError, match="immutable"):
        manifest.roles["judge"] = ()

    changed = json.loads(path.read_text())
    changed["concurrency"] = 2
    path.write_text(json.dumps(changed))
    with pytest.raises(RunManifestError, match="MANIFEST_HASH_MISMATCH"):
        load_run_manifest(path)


def test_load_rejects_conflicting_digest_even_when_first_sidecar_matches(tmp_path):
    manifest = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    path, fixed_digest = persist_run_manifest(manifest, tmp_path)
    path.with_suffix(path.suffix + ".sha256").write_text(manifest.sha256 + "\n")
    fixed_digest.write_text("f" * 64 + "\n")

    with pytest.raises(RunManifestError, match="MANIFEST_HASH_MISMATCH") as raised:
        load_run_manifest(path)
    assert raised.value.pointer == "/run-manifest.sha256"


@pytest.mark.parametrize("unsafe_part", ["manifest", "json-sidecar", "fixed-sidecar"])
def test_manifest_load_rejects_symlinked_control_files_without_leaking_target(
    tmp_path, unsafe_part
):
    manifest = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    path, json_digest = write_run_manifest(manifest, tmp_path / "input.json")
    fixed_digest = tmp_path / "run-manifest.sha256"
    secret = "credential-like-secret-must-not-leak"
    target = tmp_path / "sensitive.txt"
    target.write_text(secret, encoding="utf-8")
    unsafe = {
        "manifest": path,
        "json-sidecar": json_digest,
        "fixed-sidecar": fixed_digest,
    }[unsafe_part]
    if unsafe.exists():
        unsafe.unlink()
    try:
        unsafe.symlink_to(target)
    except OSError as error:  # pragma: no cover - restricted Windows policy
        pytest.skip(f"symlinks unavailable: {error}")

    with pytest.raises(RunManifestError) as raised:
        load_run_manifest(path)

    assert raised.value.code == "MANIFEST_FILE_UNSAFE"
    assert secret not in str(raised.value)
    assert target.read_text(encoding="utf-8") == secret


def test_same_inputs_and_timestamp_compile_to_same_bytes_and_source_hash():
    first = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    second = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.source_config_hash == second.source_config_hash


def test_v1_canonical_bytes_and_hash_exclude_v2_defaults():
    manifest = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP, schema_version=1,
    )
    payload = manifest.model_dump(mode="json")
    for field in (
        "workload_profile", "toolchains", "budget_policy", "stop_policy", "memory_policy"
    ):
        payload.pop(field)
    expected = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    assert manifest.canonical_bytes() == expected


def test_v2_manifest_is_immutable_replayable_and_toolchains_are_resolved(tmp_path):
    toolchain = ToolchainEntry(
        id="lean4@4.19.0",
        runner="local",
        executable="/usr/bin/lean",
        version_output_sha256="a" * 64,
        lock_digest=None,
        network=False,
        environment={"LANG": "C"},
        allowed_programs=("lean_kernel",),
    )
    manifest = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP, schema_version=2, workload_profile="formal",
        model_profile="compact",
        toolchains=(toolchain,), budget_policy={"cycles": {"mode": "unlimited", "value": None}},
        stop_policy={"enabled": True}, memory_policy={"enabled": False},
    )
    assert manifest.schema_version == 2
    assert manifest.pack_profile == "reasoning.formal.v1"
    assert manifest.output_profile == "compact.v2"
    path, _ = persist_run_manifest(manifest, tmp_path)
    assert load_run_manifest(path) == manifest
    with pytest.raises(TypeError, match="immutable"):
        manifest.budget_policy["cycles"] = {}
    with pytest.raises(ValueError, match="resolved"):
        ToolchainEntry(
            id="lean4@4.x", runner="local", executable="unresolved",
            version_output_sha256="b" * 64, network=False,
        )


def test_run_root_binding_is_idempotent_and_never_overwrites_conflict(tmp_path):
    first = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    different = first.model_copy(update={"concurrency": first.concurrency + 1})
    path, digest = bind_run_manifest(first, tmp_path)
    original_bytes = path.read_bytes()
    original_digest = digest.read_bytes()

    assert bind_run_manifest(first, tmp_path) == (path, digest)
    with pytest.raises(RunManifestError, match="RUN_MANIFEST_CONFLICT"):
        bind_run_manifest(different, tmp_path)

    assert path.read_bytes() == original_bytes
    assert digest.read_bytes() == original_digest
    assert load_run_manifest(path) == first


def test_run_root_binding_recovers_only_a_missing_fixed_sidecar(tmp_path):
    manifest = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    path, digest = bind_run_manifest(manifest, tmp_path)
    digest.unlink()
    assert bind_run_manifest(manifest, tmp_path) == (path, digest)
    assert digest.read_text().strip() == manifest.sha256


def test_run_root_binding_honors_orphaned_digest_record(tmp_path):
    manifest = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "run-manifest.sha256").write_text("0" * 64 + "\n")
    with pytest.raises(RunManifestError, match="RUN_MANIFEST_CONFLICT"):
        bind_run_manifest(manifest, tmp_path)
    assert not (tmp_path / "run-manifest.json").exists()


def test_cli_compile_inspect_and_make_dry_run(tmp_path, monkeypatch, capsys):
    from deepreason.cli.main import main

    config_path = tmp_path / "gemma.yaml"
    config_path.write_text(
        "roles:\n"
        "  conjecturer:\n"
        "    endpoint_id: gemma-cloud\n"
        "    endpoint: https://ollama.invalid/v1\n"
        "    model: gemma4:31b\n"
        "    provider: ollama\n"
        "    family: gemma\n"
    )
    manifest_path = tmp_path / "manifest.json"
    assert main(
        [
            "--config", str(config_path), "config", "compile",
            "--single-model", "gemma4:31b", "--profile", "compact",
            "--rubric-policy", "forbid", "--out", str(manifest_path),
        ]
    ) == 0
    compiled = capsys.readouterr().out
    assert "conjecturer[0]" in compiled and "model=gemma4:31b" in compiled
    assert manifest_path.exists()

    assert main(["config", "inspect", "--run-manifest", str(manifest_path)]) == 0
    inspected = capsys.readouterr().out
    assert "sha256=" in inspected and '"provider_fallback": false' in inspected

    monkeypatch.setattr(
        "deepreason.easy.make", lambda *_a, **_k: pytest.fail("dry-run invoked make")
    )
    assert main(
        [
            "--root", str(tmp_path / "run"), "make", "DNA page",
            "--run-manifest", str(manifest_path), "--dry-run",
        ]
    ) == 0
    assert "gemma4:31b" in capsys.readouterr().out


def test_cli_make_resume_uses_bound_manifest_and_rejects_replacement(
    tmp_path, monkeypatch, capsys
):
    from deepreason.cli.main import main
    from deepreason.run_manifest import write_run_manifest

    run_root = tmp_path / "run"
    bound = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    bind_run_manifest(bound, run_root)
    monkeypatch.setattr(
        "deepreason.run_manifest.compile_run_manifest",
        lambda *_a, **_k: pytest.fail("resume recompiled source configuration"),
    )
    assert main(["--root", str(run_root), "make", "DNA page", "--dry-run"]) == 0
    assert "gemma4:31b" in capsys.readouterr().out

    replacement = bound.model_copy(update={"concurrency": bound.concurrency + 1})
    replacement_path, _ = write_run_manifest(replacement, tmp_path / "replacement.json")
    monkeypatch.setattr(
        "deepreason.easy.make", lambda *_a, **_k: pytest.fail("conflict invoked make")
    )
    assert main(
        [
            "--root", str(run_root), "make", "DNA page",
            "--run-manifest", str(replacement_path),
        ]
    ) == 1
    assert "RUN_MANIFEST_CONFLICT" in capsys.readouterr().err
    assert load_run_manifest(run_root / "run-manifest.json") == bound


def test_cli_run_resume_uses_bound_manifest_and_rejects_replacement(
    tmp_path, monkeypatch, capsys
):
    from deepreason.cli.main import main
    from deepreason.run_manifest import write_run_manifest

    run_root = tmp_path / "scheduler-run"
    bound = compile_run_manifest(
        _config(), single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at=STAMP,
    )
    bind_run_manifest(bound, run_root)
    monkeypatch.setattr(
        "deepreason.run_manifest.compile_run_manifest",
        lambda *_a, **_k: pytest.fail("run resume recompiled source configuration"),
    )
    assert main(
        ["--root", str(run_root), "run", "--budget", "1", "--dry-run"]
    ) == 0
    assert "gemma4:31b" in capsys.readouterr().out

    replacement = bound.model_copy(update={"concurrency": bound.concurrency + 1})
    replacement_path, _ = write_run_manifest(replacement, tmp_path / "run-new.json")
    assert main(
        [
            "--root", str(run_root), "run", "--budget", "1",
            "--run-manifest", str(replacement_path), "--dry-run",
        ]
    ) == 1
    assert "RUN_MANIFEST_CONFLICT" in capsys.readouterr().err
    assert load_run_manifest(run_root / "run-manifest.json") == bound


def test_direct_cli_make_run_and_reason_respect_operator_contention(
    tmp_path, monkeypatch, capsys
):
    from deepreason.cli.main import main

    root = tmp_path / "full-run"
    manifest = compile_run_manifest(
        _config(),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    bind_run_manifest(manifest, root)
    monkeypatch.setattr(
        "deepreason.easy.make",
        lambda *_args, **_kwargs: pytest.fail("contended make executed"),
    )
    locks = operator_locks(root, owner="test-holder", blocking=False)
    try:
        assert main(["--root", str(root), "make", "locked site"]) == 1
        assert "MAKE_ALREADY_RUNNING" in capsys.readouterr().err
        assert main(["--root", str(root), "run", "--budget", "1"]) == 1
        assert "RUN_ALREADY_RUNNING" in capsys.readouterr().err
    finally:
        locks.release()

    text_root = tmp_path / "text-run"
    text_manifest = compile_run_manifest(
        _config(),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at=STAMP,
        schema_version=2,
        workload_profile="text",
    )
    bind_run_manifest(text_manifest, text_root)
    locks = operator_locks(text_root, owner="test-holder", blocking=False)
    try:
        assert (
            main(
                [
                    "--root",
                    str(text_root),
                    "reason",
                    "--text",
                    "What follows?",
                    "--cycles",
                    "1",
                ]
            )
            == 1
        )
        assert "RUN_ALREADY_RUNNING" in capsys.readouterr().err
    finally:
        locks.release()


def test_doctor_dry_run_resolves_configured_endpoint_alias(tmp_path, capsys):
    from deepreason.cli.main import main

    config_path = tmp_path / "gemma.yaml"
    config_path.write_text(
        "roles:\n"
        "  conjecturer:\n"
        "    endpoint_id: gemma-cloud\n"
        "    endpoint: https://ollama.invalid/v1\n"
        "    model: gemma4:31b\n"
        "    provider: ollama\n"
    )
    assert main(
        [
            "--config", str(config_path), "doctor", "--endpoint", "gemma-cloud",
            "--model", "gemma4:31b", "--dry-run",
        ]
    ) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["endpoint_id"] == "gemma-cloud"
    assert result["contacted"] is False


@pytest.mark.parametrize(
    "endpoint,secret",
    [
        ("https://doctor-user:doctor-secret@example.invalid/v1", "doctor-secret"),
        ("https://example.invalid/v1?token=doctor-secret", "doctor-secret"),
    ],
)
def test_doctor_rejects_credential_url_before_contact_or_output(
    tmp_path, monkeypatch, capsys, endpoint, secret
):
    from deepreason.cli.main import main

    monkeypatch.setattr(
        "deepreason.llm.endpoints.list_models",
        lambda *_args: pytest.fail("credential-bearing endpoint was contacted"),
    )
    assert main(
        [
            "--root", str(tmp_path / "doctor"), "doctor",
            "--endpoint", endpoint, "--model", "gemma4:31b",
        ]
    ) == 1
    captured = capsys.readouterr()
    assert secret not in captured.out
    assert secret not in captured.err
    assert "ROUTE_URL_CREDENTIAL_FORBIDDEN" in captured.err
    assert not (tmp_path / "doctor" / "capabilities.json").exists()


def test_doctor_records_capability_recommendation(tmp_path, monkeypatch, capsys):
    from deepreason.cli.main import main
    from deepreason.llm.capabilities import ModelCapabilities

    probed = {}

    monkeypatch.setattr(
        "deepreason.llm.endpoints.list_models", lambda *_args: ["gemma4:31b"]
    )
    def fake_probe(endpoint, **_kwargs):
        probed.update(
            temperature=endpoint.temperature,
            reasoning=endpoint.reasoning,
            max_tokens=endpoint.max_tokens,
            json_mode=endpoint.json_mode,
        )
        return ModelCapabilities(
            provider=endpoint.provider,
            endpoint=endpoint.name,
            model=endpoint.model,
            nested_object_reliability=0.2,
            array_reliability=0.2,
            enum_adherence=0.5,
        )

    monkeypatch.setattr("deepreason.llm.capabilities.probe_capabilities", fake_probe)
    assert main(
        [
            "--root", str(tmp_path / "doctor"), "doctor",
            "--endpoint", "https://ollama.invalid/v1", "--model", "gemma4:31b",
            "--provider", "ollama",
        ]
    ) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["recommended_model_profile"] == "compact"
    assert result["selected_output_mechanism"] == "json_text"
    assert probed == {
        "temperature": 0.0,
        "reasoning": "none",
        "max_tokens": 5000,
        "json_mode": False,
    }


def test_cli_make_implicit_manifest_is_persisted_and_drives_easy(tmp_path, monkeypatch):
    from deepreason.cli.main import main

    config_path = tmp_path / "gemma.yaml"
    config_path.write_text(
        "model_profile: compact\n"
        "roles:\n"
        "  conjecturer:\n"
        "    endpoint: https://ollama.invalid/v1\n"
        "    model: gemma4:31b\n"
        "    provider: ollama\n"
    )
    run_root = tmp_path / "run"
    received = []
    monkeypatch.setattr(
        "deepreason.easy.make", lambda *args, **kwargs: received.append((args, kwargs)) or []
    )

    assert main(
        [
            "--root", str(run_root), "--config", str(config_path),
            "make", "DNA page", "--cycles", "2", "--token-budget", "0",
        ]
    ) == 0

    assert (run_root / "run-manifest.json").exists()
    assert (run_root / "run-manifest.sha256").exists()
    assert received[0][1]["root"] == str(run_root)
    assert received[0][1]["config"] == str(run_root / ".run-manifest-config.json")
    materialized = json.loads((run_root / ".run-manifest-config.json").read_text())
    assert materialized["roles"]["conjecturer"]["model"] == "gemma4:31b"
    assert materialized["model_profile"] == "compact"
