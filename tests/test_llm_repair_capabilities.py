"""Deterministic setup probes and bounded schema repair."""

import json

import pytest

from deepreason.llm.adapter import LLMAdapter, SchemaRepairError
from deepreason.llm.capabilities import CapabilityCache, ModelCapabilities, probe_capabilities
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.endpoints import EndpointError, MockEndpoint, OpenAICompatEndpoint
from deepreason.llm.repair import (
    OutputMechanism,
    diagnostic_from_error,
    merge_subtree,
    minimal_skeleton,
    parse_one_json_value,
    select_output_mechanism,
)
from deepreason.run_manifest import RouteSecretError
from deepreason.storage.blobs import BlobStore


def test_normalization_removes_only_transport_wrappers():
    parsed = parse_one_json_value('```json\n{"x":[1,"2"]}\n```')
    assert parsed.value == {"x": [1, "2"]}
    assert parsed.text == '{"x":[1,"2"]}'
    assert parse_one_json_value('prefix: {"x":1}  ').value == {"x": 1}
    with pytest.raises(ValueError):
        parse_one_json_value("there is no value")


@pytest.mark.parametrize(
    "raw",
    [
        '{"x":1} {"y":2}',
        'prefix: {"x":1} {"y":2}',
        '{"x":1} trailing prose',
        '```json\n{"x":1}\n``` trailing prose',
    ],
)
def test_normalization_rejects_multiple_values_and_trailing_content(raw):
    with pytest.raises(ValueError):
        parse_one_json_value(raw)


def test_subtree_merge_is_copying_and_exact():
    original = {"a": [{"b": 3}], "keep": [1, 2]}
    merged = merge_subtree(original, "/a/0/b", 4)
    assert merged == {"a": [{"b": 4}], "keep": [1, 2]}
    assert original["a"][0]["b"] == 3


def test_minimal_skeleton_resolves_nested_schema_refs():
    from deepreason.llm.wire import DirectWireContract

    contract = DirectWireContract(ConjecturerOutput)
    schema = contract.model_json_schema()
    skeleton = minimal_skeleton(schema)
    assert contract.validate_value(skeleton)
    diagnostic = diagnostic_from_error("conjecturer.direct.v1", ValueError("bad"), schema)
    assert diagnostic.skeleton == skeleton


def test_adapter_repairs_only_invalid_field_on_attempt_two(tmp_path):
    endpoint = MockEndpoint(
        [
            '{"candidates":[{"content":"keep","typicality":2}]}',
            '{"candidates":[{"content":"keep","typicality":3}]}',
            "0.4",
        ]
    )
    blobs = BlobStore(tmp_path / "blobs")
    adapter = LLMAdapter({"conjecturer": endpoint}, blobs, retry_max=9)
    output, call = adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert output.candidates[0].content == "keep"
    assert output.candidates[0].typicality == 0.4
    assert call.attempts == 3  # retry_max cannot open a fourth repair path
    repair_prompt = blobs.get(call.prompt_ref).decode()
    assert "/candidates/0/typicality" in repair_prompt
    assert "Return ONLY the replacement JSON value" in repair_prompt
    assert blobs.get(call.raw_ref).decode() == "0.4"
    assert len(call.attempt_trace) == call.attempts == 3
    assert sum(item.tokens for item in call.attempt_trace) == call.tokens
    assert [item.valid for item in call.attempt_trace] == [False, False, True]
    assert blobs.get(call.attempt_trace[0].raw_ref).decode() == (
        '{"candidates":[{"content":"keep","typicality":2}]}'
    )
    first_diagnostic = json.loads(
        blobs.get(call.attempt_trace[0].diagnostic_ref)
    )
    assert first_diagnostic["contract"] == call.attempt_trace[0].contract_id
    assert call.attempt_trace[0].route_sha256
    assert call.attempt_trace[0].endpoint_id == "mock"


def test_repair_exhaustion_is_bounded_even_with_large_retry_max(tmp_path):
    endpoint = MockEndpoint(["bad", "bad", "bad", "would-be-fourth"])
    adapter = LLMAdapter(
        {"conjecturer": endpoint}, BlobStore(tmp_path / "blobs"), retry_max=99
    )
    with pytest.raises(SchemaRepairError) as caught:
        adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert caught.value.spend.attempts == 3
    assert endpoint._responses == ["would-be-fourth"]
    assert [item.valid for item in caught.value.spend.attempt_trace] == [
        False,
        False,
        False,
    ]


def test_zero_usage_transport_failure_is_still_replayable(tmp_path):
    def fail(_prompt):
        raise EndpointError("timeout after bounded retries")

    endpoint = MockEndpoint(fail, name="mock://timeout", model="model-timeout")
    blobs = BlobStore(tmp_path / "blobs")
    adapter = LLMAdapter({"conjecturer": endpoint}, blobs)

    with pytest.raises(EndpointError) as caught:
        adapter.call("conjecturer", "PACK", ConjecturerOutput)

    spend = caught.value.spend
    assert spend is not None
    assert spend.tokens == 0
    assert spend.attempts == 1
    assert len(spend.attempt_trace) == 1
    attempt = spend.attempt_trace[0]
    assert attempt.usage_unknown and not attempt.valid and not attempt.raw_ref
    assert blobs.get(attempt.prompt_ref)
    diagnostic = json.loads(blobs.get(attempt.diagnostic_ref))
    assert diagnostic["contract"] == attempt.contract_id
    assert "timeout" in diagnostic["error"]


def test_output_mechanism_priority_is_fixed():
    caps = ModelCapabilities(provider="p", endpoint="e", model="m", grammar=True)
    assert select_output_mechanism(caps) == OutputMechanism.GRAMMAR
    caps = ModelCapabilities(
        provider="p", endpoint="e", model="m", native_json_schema=True, grammar=True
    )
    assert select_output_mechanism(caps) == OutputMechanism.NATIVE_JSON_SCHEMA


def test_capability_cache_and_probe_reject_credential_endpoint_before_io(tmp_path):
    secret = "cache-do-not-echo"
    unsafe = f"https://user:{secret}@example.invalid/v1"
    cache = CapabilityCache(tmp_path / "capabilities.json")

    with pytest.raises(RouteSecretError) as get_error:
        cache.get("provider", unsafe, "model")
    with pytest.raises(RouteSecretError) as put_error:
        cache.put(ModelCapabilities(provider="provider", endpoint=unsafe, model="model"))

    calls = []
    endpoint = MockEndpoint(
        lambda _prompt: calls.append(True) or "{}",
        name=unsafe,
        model="model",
    )
    with pytest.raises(RouteSecretError) as probe_error:
        probe_capabilities(endpoint, cache=cache)

    assert calls == []
    assert not cache.path.exists()
    for error in (get_error, put_error, probe_error):
        assert secret not in str(error.value)


def test_capability_cache_does_not_rewrite_poisoned_route(tmp_path):
    secret = "persist-do-not-echo"
    cache = CapabilityCache(tmp_path / "capabilities.json")
    original = json.dumps({
        "untrusted": {
            "provider": "provider",
            "endpoint": f"https://user:{secret}@example.invalid/v1",
            "model": "model",
        }
    })
    cache.path.write_text(original)

    safe = ModelCapabilities(
        provider="provider",
        endpoint="https://example.invalid/v1",
        model="safe-model",
    )
    with pytest.raises(RouteSecretError) as raised:
        cache.put(safe)

    assert secret not in str(raised.value)
    assert cache.path.read_text() == original


def test_endpoint_body_uses_selected_mechanism_without_fallback():
    endpoint = OpenAICompatEndpoint("https://example.invalid/v1", "m", json_mode=True)
    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    native = endpoint.build_body(
        "p", response_schema=schema, output_mechanism="native_json_schema"
    )
    assert native["response_format"]["type"] == "json_schema"
    grammar = endpoint.build_body("p", response_schema=schema, output_mechanism="grammar")
    assert "grammar" in grammar and "response_format" not in grammar
    text = endpoint.build_body("p", response_schema=schema, output_mechanism="json_text")
    assert "response_format" not in text and "grammar" not in text


def test_adapter_uses_frozen_lease_mechanism(tmp_path):
    endpoint = MockEndpoint(
        ['{"candidates":[{"content":"x","typicality":0.5}]}']
    )
    endpoint.output_mechanism = "native_json_schema"
    adapter = LLMAdapter(
        {"conjecturer": endpoint}, BlobStore(tmp_path / "blobs")
    )
    adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert endpoint.last_kwargs["output_mechanism"] == OutputMechanism.NATIVE_JSON_SCHEMA
    assert endpoint.last_kwargs["response_schema"]["additionalProperties"] is False


def test_runtime_cannot_change_frozen_lease_mechanism(tmp_path):
    endpoint = MockEndpoint([])
    adapter = LLMAdapter(
        {"conjecturer": endpoint}, BlobStore(tmp_path / "blobs")
    )
    with pytest.raises(ValueError, match="frozen by endpoint lease"):
        adapter.call(
            "conjecturer",
            "PACK",
            ConjecturerOutput,
            output_mechanism="grammar",
        )


class _ProbeEndpoint:
    name = "mock://probe"
    model = "model-r1"
    provider = "mock"
    max_reliable_output_tokens = 4096

    def __init__(self):
        self.calls = 0

    def complete(self, prompt, **kwargs):
        self.calls += 1
        if "word READY" in prompt:
            return "READY"
        if "OUTPUT_LENGTH_PROBE" in prompt:
            count = int(prompt.split("chars=", 1)[1].split(".", 1)[0])
            return json.dumps({"payload": "x" * count})
        if "outer" in prompt:
            return json.dumps(
                {
                    "outer": {"inner": {"label": "kept"}},
                    "items": [{"id": "x", "enabled": True}, {"id": "y", "enabled": False}],
                }
            )
        if "[1,2,3,4,5,6]" in prompt:
            return '{"items":[1,2,3,4,5,6]}'
        if "marker=retain-4f92" in prompt:
            return '{"marker":"retain-4f92"}'
        if "gamma" in prompt:
            return '{"choice":"beta","keep":7}'
        if "choice" in prompt:
            return '{"choice":"beta"}'
        return '{"answer":"ok"}'


def test_capability_probes_are_deterministic_and_cached_by_revision(tmp_path):
    endpoint = _ProbeEndpoint()
    cache = CapabilityCache(tmp_path / "capabilities.json")
    first = probe_capabilities(endpoint, revision="r1", cache=cache)
    assert first.native_json_schema and first.grammar
    assert first.nested_object_reliability == 1.0
    assert first.max_reliable_output_tokens == 4096
    calls = endpoint.calls
    second = probe_capabilities(endpoint, revision="r1", cache=cache)
    assert second == first and endpoint.calls == calls
    probe_capabilities(endpoint, revision="r2", cache=cache)
    assert endpoint.calls > calls


class _IntermittentProbeEndpoint(_ProbeEndpoint):
    def __init__(self):
        super().__init__()
        self.enum_calls = 0

    def complete(self, prompt, **kwargs):
        if "choice must be alpha or beta" in prompt:
            self.calls += 1
            self.enum_calls += 1
            return (
                '{"choice":"gamma"}'
                if self.enum_calls == 1
                else '{"choice":"beta"}'
            )
        return super().complete(prompt, **kwargs)


def test_reliability_probes_measure_repeated_adherence():
    capabilities = probe_capabilities(_IntermittentProbeEndpoint())
    assert capabilities.enum_adherence == pytest.approx(2 / 3)
    assert capabilities.nested_object_reliability == 1.0
