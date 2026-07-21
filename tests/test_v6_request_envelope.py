"""Focused total-request-envelope qualification for frozen v6 routes."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from deepreason.llm.adapter import LLMAdapter, RequestEnvelopeExceeded
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import EndpointLease, route_fingerprint
from deepreason.run_manifest import Route
from deepreason.storage.blobs import BlobStore


class _Output(BaseModel):
    value: str


def _route(*, capacity: int | None) -> Route:
    return Route(
        endpoint_id="envelope-route",
        base_url="mock://envelope-route",
        model_id="offline-envelope-model",
        provider="mock",
        family="offline-envelope-family",
        max_tokens=32,
        context_window_tokens=capacity,
    )


def _adapter(
    tmp_path,
    *,
    capacity: int | None,
    response='{"value":"ok"}',
    retry_max: int = 0,
    meter: TokenMeter | None = None,
):
    route = _route(capacity=capacity)
    endpoint = MockEndpoint(
        response if callable(response) else [response],
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    endpoint.context_window_tokens = capacity
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        BlobStore(tmp_path / f"blobs-{capacity}"),
        retry_max=retry_max,
        meter=meter,
        leases={
            "conjecturer": (
                EndpointLease(role="conjecturer", seat=0, route=route),
            )
        },
    )
    return adapter, endpoint


def _unqualified_prompt(tmp_path, pack: str) -> str:
    adapter, _endpoint = _adapter(tmp_path, capacity=None)
    prompt, _contract, _lease, _maximum = adapter.preview_request(
        "conjecturer", pack, _Output
    )
    return prompt


def test_complete_envelope_can_exceed_when_pack_itself_fits(tmp_path):
    pack = "tiny pack"
    prompt = _unqualified_prompt(tmp_path, pack)
    capacity = len(pack.encode("utf-8")) + 32 + 8
    assert capacity < len(prompt.encode("utf-8")) + 32
    adapter, _endpoint = _adapter(tmp_path, capacity=capacity)

    with pytest.raises(RequestEnvelopeExceeded) as raised:
        adapter.preview_request("conjecturer", pack, _Output)

    assert raised.value.code == "REQUEST_ENVELOPE_EXCEEDED"
    assert raised.value.role == "conjecturer"
    assert raised.value.route_seat == 0


def test_exact_capacity_passes_and_one_unit_overflow_fails(tmp_path):
    pack = "exact boundary"
    prompt = _unqualified_prompt(tmp_path, pack)
    exact_capacity = len(prompt.encode("utf-8")) + 32
    exact, endpoint = _adapter(tmp_path, capacity=exact_capacity)

    preview = exact.preview_request("conjecturer", pack, _Output)
    assert preview[0] == prompt
    assert preview[3] == 32
    result, _call = exact.call("conjecturer", pack, _Output)
    assert result.value == "ok"
    assert endpoint.last_transport_attempts == 1

    overflow, _endpoint = _adapter(tmp_path, capacity=exact_capacity - 1)
    with pytest.raises(RequestEnvelopeExceeded) as raised:
        overflow.preview_request("conjecturer", pack, _Output)
    assert raised.value.prompt_upper_bound == len(prompt.encode("utf-8"))
    assert raised.value.completion_bound == 32
    assert raised.value.total_bound == exact_capacity
    assert raised.value.context_capacity == exact_capacity - 1


def test_multibyte_utf8_uses_a_conservative_byte_upper_bound(tmp_path):
    pack = "possibility 🧪✨" * 40
    prompt = _unqualified_prompt(tmp_path, pack)
    prompt_bytes = len(prompt.encode("utf-8"))
    assert prompt_bytes > len(prompt)
    adapter, _endpoint = _adapter(tmp_path, capacity=prompt_bytes + 31)

    with pytest.raises(RequestEnvelopeExceeded) as raised:
        adapter.preview_request("conjecturer", pack, _Output)

    assert raised.value.prompt_upper_bound == prompt_bytes
    assert raised.value.total_bound == prompt_bytes + 32


def test_pre_rendered_request_cannot_bypass_envelope_check(tmp_path):
    rendered = "already rendered 🧪 request"
    total = len(rendered.encode("utf-8")) + 32
    adapter, _endpoint = _adapter(tmp_path, capacity=total - 1)

    with pytest.raises(RequestEnvelopeExceeded) as raised:
        adapter.preview_request(
            "conjecturer",
            "ignored pack",
            _Output,
            pre_rendered_request=rendered,
        )

    assert raised.value.prompt_upper_bound == len(rendered.encode("utf-8"))


def test_direct_call_cannot_skip_envelope_enforcement(tmp_path):
    calls = []

    def forbidden(_prompt):
        calls.append(True)
        return '{"value":"unexpected"}'

    adapter, endpoint = _adapter(tmp_path, capacity=33, response=forbidden)
    with pytest.raises(RequestEnvelopeExceeded) as raised:
        adapter.call("conjecturer", "direct call", _Output)

    assert calls == []
    assert endpoint.last_transport_attempts == 0
    assert getattr(raised.value, "spend", None) is None


def test_repair_envelope_overflow_preserves_prior_provider_spend(tmp_path):
    pack = "repair envelope boundary"
    initial_prompt = _unqualified_prompt(tmp_path, pack)
    capacity = len(initial_prompt.encode("utf-8")) + 32
    # MockEndpoint reports chars/4 usage. This unterminated multibyte string
    # stays below the 32-token completion allowance while making the repair
    # request's UTF-8 envelope larger than the fitting initial request.
    invalid = '"' + ("🧪" * 118)
    valid_but_forbidden = '{"value":"must not dispatch"}'
    pending = iter((invalid, valid_but_forbidden))
    prompts = []

    def respond(prompt):
        prompts.append(prompt)
        return next(pending)

    meter = TokenMeter(100_000)
    adapter, endpoint = _adapter(
        tmp_path,
        capacity=capacity,
        response=respond,
        retry_max=1,
        meter=meter,
    )
    preview_prompt, preview_contract, preview_lease, _maximum = (
        adapter.preview_request("conjecturer", pack, _Output)
    )
    assert preview_prompt == initial_prompt

    with pytest.raises(RequestEnvelopeExceeded) as raised:
        adapter.call("conjecturer", pack, _Output)

    error = raised.value
    spend = error.spend
    assert prompts == [initial_prompt]
    assert endpoint.last_transport_attempts == 1
    assert spend is not None
    assert spend.attempts == 1
    assert len(spend.attempt_trace) == 1
    attempt = spend.attempt_trace[0]
    assert attempt.attempt == 0
    assert attempt.prompt_ref == spend.prompt_ref
    assert attempt.raw_ref == spend.raw_ref
    assert adapter.blobs.get(spend.prompt_ref).decode("utf-8") == initial_prompt
    assert adapter.blobs.get(spend.raw_ref).decode("utf-8") == invalid
    assert spend.role == "conjecturer"
    assert spend.model == "offline-envelope-model"
    assert spend.endpoint == "mock://envelope-route"
    assert attempt.contract_id == preview_contract.contract_id
    assert attempt.endpoint_id == "envelope-route"
    assert attempt.route_sha256 == route_fingerprint(preview_lease.route)
    assert spend.tokens > 0
    assert attempt.tokens == spend.tokens
    assert spend.work_order_id is None
    assert spend.dispatch_authorization_ref is None
    assert meter.snapshot()["calls"] == 1
    assert meter.snapshot()["completion_tokens"] <= 32
    assert meter.snapshot()["reserved"] == 0
    assert adapter._compact_recovery_roles == set()


def test_runtime_endpoint_cannot_widen_frozen_capacity(tmp_path):
    adapter, endpoint = _adapter(tmp_path, capacity=1000)
    endpoint.context_window_tokens = 2000

    with pytest.raises(RuntimeError, match="ROUTE_LEASE_MISMATCH"):
        adapter.preview_request("conjecturer", "pack", _Output)

    endpoint.context_window_tokens = 1000
    endpoint.max_tokens = 64
    with pytest.raises(RuntimeError, match="field=max_tokens"):
        adapter.preview_request("conjecturer", "pack", _Output)
