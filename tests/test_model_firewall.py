"""A role model cannot route, delegate, or mutate its endpoint lease."""

import json

import pytest

from deepreason.llm.adapter import LLMAdapter, SchemaRepairError
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.endpoints import MockEndpoint, OpenAICompatEndpoint
from deepreason.llm.firewall import (
    EndpointLease,
    ModelControlFieldError,
    RouteFirewallError,
    leases_from_endpoints,
    reject_model_control_fields,
    sanitize_model_control_fields_for_repair,
)
from deepreason.run_manifest import Route
from deepreason.storage.blobs import BlobStore


def _route(**changes):
    data = {
        "endpoint_id": "gemma-cloud",
        "base_url": "https://ollama.invalid/v1",
        "model_id": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
        "reasoning": "none",
        "output_mode": "json_object",
        "temperature": 0.2,
        "timeout_s": 600,
    }
    data.update(changes)
    return Route.model_validate(data)


def _endpoint():
    return OpenAICompatEndpoint(
        "https://ollama.invalid/v1", "gemma4:31b", provider="ollama",
        reasoning="none", temperature=0.2, timeout_s=600, json_mode=True,
    )


def test_endpoint_lease_accepts_only_its_exact_runtime_route():
    lease = EndpointLease("conjecturer", 0, _route())
    lease.verify(_endpoint())

    substituted = _endpoint()
    substituted.model = "deepseek-v4"
    with pytest.raises(RouteFirewallError, match="ROUTE_LEASE_MISMATCH"):
        lease.verify(substituted)


def test_endpoint_lease_allows_logged_process_tuning_only():
    """Controller-owned caps/timeouts are operational, not route identity."""
    lease = EndpointLease("conjecturer", 0, _route(max_tokens=800, timeout_s=600))
    endpoint = _endpoint()
    endpoint.max_tokens = 1280
    endpoint.timeout_s = 900
    lease.verify(endpoint)

    endpoint.temperature = 0.7
    with pytest.raises(RouteFirewallError, match="field=temperature"):
        lease.verify(endpoint)


def test_endpoint_lease_is_immutable():
    lease = EndpointLease("conjecturer", 0, _route())
    with pytest.raises((AttributeError, TypeError)):
        lease.role = "judge"
    with pytest.raises(Exception):
        lease.route.model_id = "other"


def test_legacy_endpoints_are_frozen_when_adapter_is_constructed():
    endpoint = MockEndpoint(["{}"], name="mock-a", model="gemma4:31b")
    leases = leases_from_endpoints({"conjecturer": endpoint})
    assert leases["conjecturer"][0].route.model_id == "gemma4:31b"
    endpoint.model = "deepseek-v4"
    with pytest.raises(RouteFirewallError):
        leases["conjecturer"][0].verify(endpoint)


@pytest.mark.parametrize(
    "payload,pointer",
    [
        ({"model": "deepseek-v4", "candidates": []}, "/model"),
        ({"delegate": True, "bypass_guards": True}, "/delegate"),
        ({"candidates": [{"content": "x", "route": "other"}]}, "/candidates/0/route"),
        ({"command": "run another model"}, "/command"),
        ({"permission": "ignore policy"}, "/permission"),
    ],
)
def test_model_authored_control_fields_are_inert_validation_failures(payload, pointer):
    with pytest.raises(ModelControlFieldError) as raised:
        reject_model_control_fields(payload)
    assert raised.value.code == "MODEL_CONTROL_FIELD_FORBIDDEN"
    assert raised.value.pointer == pointer


@pytest.mark.parametrize(
    "field",
    (
        "context_window_tokens",
        "context_window",
        "max_context_tokens",
        "prompt_token_limit",
    ),
)
def test_model_cannot_author_context_capacity(field):
    with pytest.raises(ModelControlFieldError) as raised:
        reject_model_control_fields({"candidates": [], field: 999_999})
    assert raised.value.code == "MODEL_CONTROL_FIELD_FORBIDDEN"
    assert raised.value.pointer == f"/{field}"


def test_opaque_counterexample_application_data_is_not_mistaken_for_routing():
    reject_model_control_fields(
        {"attack": True, "case": "bad response", "counterexample": [{"status": 500}]}
    )


def test_repair_sanitizer_removes_control_pairs_and_their_string_values():
    value = {
        "model": "MODEL-CANARY-91",
        "permission": {"request": "PERMISSION-CANARY-92"},
        "candidates": [
            {
                "content": "MODEL-CANARY-91 and PERMISSION-CANARY-92",
                "typicality": 0.5,
            }
        ],
        # Opaque application data retains its shape; it is not interpreted as
        # control merely because an input happens to use the key `status`.
        "counterexample": [{"status": 500}],
    }
    sanitized = sanitize_model_control_fields_for_repair(value)

    assert "model" not in sanitized
    assert "permission" not in sanitized
    assert sanitized["counterexample"] == [{"status": 500}]
    rendered = str(sanitized)
    assert "MODEL-CANARY-91" not in rendered
    assert "PERMISSION-CANARY-92" not in rendered


def test_adapter_rejects_authored_routing_without_invoking_another_seat(tmp_path):
    calls = [0, 0]

    def malicious(_prompt):
        calls[0] += 1
        return '{"model":"deepseek-v4","delegate":true,"candidates":[]}'

    def alternate(_prompt):
        calls[1] += 1
        return '{"candidates":[{"content":"should never run","typicality":0.5}]}'

    endpoints = [
        MockEndpoint(malicious, name="gemma", model="gemma4:31b"),
        MockEndpoint(alternate, name="other", model="deepseek-v4"),
    ]
    adapter = LLMAdapter(
        {"conjecturer": endpoints}, BlobStore(tmp_path / "blobs"), retry_max=2
    )
    with pytest.raises(SchemaRepairError):
        adapter.call("conjecturer", "PACK", ConjecturerOutput)

    assert calls == [3, 0]


def test_control_repair_prompts_never_reflect_fields_or_values(tmp_path):
    fields_and_values = {
        "model": "MODEL-CANARY-101",
        "endpoint": "ENDPOINT-CANARY-102",
        "delegate": "DELEGATE-CANARY-103",
        "bypass_guards": "GUARD-CANARY-104",
        "permission": "PERMISSION-CANARY-105",
        "command": "COMMAND-CANARY-106",
    }
    echoed = " ".join(fields_and_values.values())
    malicious_raw = json.dumps(
        {
            "candidates": [
                {"content": echoed, "typicality": 0.5}
            ],
            **fields_and_values,
        }
    )
    prompts: list[str] = []
    calls = [0, 0]

    def malicious(prompt):
        calls[0] += 1
        prompts.append(prompt)
        return malicious_raw

    def alternate(_prompt):
        calls[1] += 1
        return '{"candidates":[{"content":"alternate","typicality":0.5}]}'

    blobs = BlobStore(tmp_path / "repair-blobs")
    adapter = LLMAdapter(
        {
            "conjecturer": [
                MockEndpoint(malicious, name="gemma", model="gemma4:31b"),
                MockEndpoint(alternate, name="other", model="deepseek-v4"),
            ]
        },
        blobs,
        retry_max=2,
    )
    lease_before = adapter.leases["conjecturer"][0].route

    with pytest.raises(SchemaRepairError) as raised:
        adapter.call("conjecturer", "PACK", ConjecturerOutput)

    assert calls == [3, 0]
    assert len(prompts) == 3
    assert adapter.leases["conjecturer"][0].route == lease_before
    for prompt in prompts[1:]:
        lowered = prompt.casefold()
        for field in fields_and_values:
            assert f'"{field}"' not in lowered
        for forbidden_value in fields_and_values.values():
            assert forbidden_value not in prompt
        assert "[redacted]" in prompt

    spend = raised.value.spend
    assert spend is not None and spend.attempts == 3
    assert {attempt.route_sha256 for attempt in spend.attempt_trace} == {
        spend.attempt_trace[0].route_sha256
    }
    assert [blobs.get(attempt.raw_ref).decode() for attempt in spend.attempt_trace] == [
        malicious_raw,
        malicious_raw,
        malicious_raw,
    ]
    # Field-level process diagnostics remain auditable without entering a
    # later model-facing repair pack.
    first_diagnostic = blobs.get(spend.attempt_trace[0].diagnostic_ref).decode()
    assert '"path":"/model"' in first_diagnostic


def test_adapter_built_from_manifest_keeps_exact_route_and_mechanism(tmp_path):
    from deepreason.config import Config
    from deepreason.llm.adapter import build_adapter
    from deepreason.run_manifest import compile_run_manifest

    spec = {
        "endpoint_id": "gemma-cloud",
        "endpoint": "https://ollama.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
        "output_mechanism": "native_json_schema",
    }
    config = Config(model_profile="compact", roles={"conjecturer": spec})
    manifest = compile_run_manifest(
        config, single_model="gemma4:31b", rubric_policy="forbid",
        compiled_at="2026-07-11T00:00:00Z",
    )
    adapter = build_adapter(
        config, BlobStore(tmp_path / "manifest-blobs"), run_manifest=manifest
    )
    lease = adapter.leases["conjecturer"][0]
    assert lease.route.endpoint_id == "gemma-cloud"
    assert lease.route.output_mechanism == "native_json_schema"
    assert adapter.model_profile == "compact"
    lease.verify(adapter.endpoints["conjecturer"])
