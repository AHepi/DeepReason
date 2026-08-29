"""LLM adapter (spec §9): schema validation, bounded repair retries, logged
prompt/raw blobs."""

import json
import time

import pytest

from deepreason.llm.adapter import LLMAdapter, SchemaRepairError
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.storage.blobs import BlobStore

GOOD = json.dumps({"candidates": [{"content": "the moon pulls the sea", "typicality": 0.7}]})


def _adapter(tmp_path, responses, retry_max=2):
    from deepreason.llm.endpoints import MockEndpoint

    blobs = BlobStore(tmp_path / "blobs")
    return LLMAdapter({"conjecturer": MockEndpoint(responses)}, blobs, retry_max=retry_max), blobs


def test_call_logs_prompt_and_raw(tmp_path):
    adapter, blobs = _adapter(tmp_path, [GOOD])
    output, call = adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert output.candidates[0].typicality == 0.7
    assert call.role == "conjecturer"
    assert "PACK" in blobs.get(call.prompt_ref).decode()
    assert blobs.get(call.raw_ref).decode() == GOOD


def test_schema_repair_retries_then_succeeds(tmp_path):
    adapter, _ = _adapter(tmp_path, ["definitely not json", GOOD])
    output, _ = adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert len(output.candidates) == 1


def test_fenced_json_is_extracted(tmp_path):
    adapter, _ = _adapter(tmp_path, [f"```json\n{GOOD}\n```"])
    output, _ = adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert output.candidates[0].content == "the moon pulls the sea"


def test_retries_exhausted_raises(tmp_path):
    adapter, _ = _adapter(tmp_path, ["bad"] * 3, retry_max=2)
    with pytest.raises(SchemaRepairError):
        adapter.call("conjecturer", "PACK", ConjecturerOutput)


def test_missing_role_raises(tmp_path):
    adapter, _ = _adapter(tmp_path, [GOOD])
    assert not adapter.has_role("judge")
    with pytest.raises(KeyError):
        adapter.call("judge", "PACK", ConjecturerOutput)


def test_retry_covers_mid_stream_disconnects():
    """http.client.IncompleteRead escapes the OSError net (killed two live
    runs at cycle 1) — the retry wrapper must treat it as transient."""
    import http.client

    from deepreason.llm.endpoints import request_with_retries

    calls = [0]

    def flaky():
        calls[0] += 1
        if calls[0] < 3:
            raise http.client.IncompleteRead(b"")
        return "ok"

    assert request_with_retries(flaky) == "ok"
    assert calls[0] == 3


PAYLOAD = json.dumps(
    {
        "choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    }
).encode()


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, *a):
        return PAYLOAD


def _patched_endpoint(monkeypatch, fake_urlopen, timeout_s=100):
    import urllib.request

    from deepreason.llm import endpoints
    from deepreason.llm.endpoints import OpenAICompatEndpoint

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(endpoints.time, "sleep", lambda s: None)
    return OpenAICompatEndpoint("https://example.invalid", "m", timeout_s=timeout_s)


def test_read_timeout_retry_waits_longer_then_succeeds(monkeypatch):
    """A read timeout proves only that no complete response arrived before
    the deadline; the single escalated retry waits 2x (two variator calls
    were dropped live after four identical 120s waits)."""
    seen_timeouts = []

    def fake_urlopen(request, timeout=None):
        seen_timeouts.append(timeout)
        if len(seen_timeouts) < 2:
            raise TimeoutError("The read operation timed out")
        return _Response()

    ep = _patched_endpoint(monkeypatch, fake_urlopen)
    assert ep.complete("PACK") == "hi"
    assert seen_timeouts == [100, 200]


def test_second_read_timeout_is_terminal_and_bounded(monkeypatch):
    """The escalation is bounded: after 1x + 2x waits a second read timeout
    raises EndpointError immediately — no third identical-or-wider wait."""
    from deepreason.llm.endpoints import EndpointError

    seen_timeouts = []

    def fake_urlopen(request, timeout=None):
        seen_timeouts.append(timeout)
        raise TimeoutError("The read operation timed out")

    ep = _patched_endpoint(monkeypatch, fake_urlopen)
    with pytest.raises(EndpointError, match="escalated read timeouts"):
        ep.complete("PACK")
    assert seen_timeouts == [100, 200]  # total wait bounded at 3x base


def test_non_timeout_faults_keep_plain_retry_policy(monkeypatch):
    """Read timeouts are distinguished from other transport faults: a
    connection drop retries at the base wait, not an escalated one."""
    seen_timeouts = []

    def fake_urlopen(request, timeout=None):
        seen_timeouts.append(timeout)
        if len(seen_timeouts) < 3:
            raise ConnectionResetError("peer reset")
        return _Response()

    ep = _patched_endpoint(monkeypatch, fake_urlopen)
    assert ep.complete("PACK") == "hi"
    assert seen_timeouts == [100, 100, 100]


def test_slow_local_server_succeeds_under_escalated_wait():
    """End-to-end against a real socket: the first request stalls past its
    deadline, the retry (with the 2x wait) gets a valid completion."""
    import http.server
    import threading

    from deepreason.llm.endpoints import OpenAICompatEndpoint

    hits = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            hits.append(1)
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if len(hits) == 1:
                time.sleep(2.5)  # outlast the first 1s deadline
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(PAYLOAD)

        def log_message(self, *a):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.handle_error = lambda *a: None  # first request's pipe breaks; fine
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        ep = OpenAICompatEndpoint(
            f"http://127.0.0.1:{server.server_address[1]}", "m", timeout_s=1
        )
        assert ep.complete("PACK") == "hi"
    finally:
        server.shutdown()
        thread.join(timeout=5)
    assert len(hits) == 2


def test_timeout_spec_plumbs_to_endpoint():
    """roles.<role>.timeout_s reaches the endpoint; unset keeps the default."""
    from deepreason.llm.adapter import _endpoint_from_spec

    tuned = _endpoint_from_spec(
        {"endpoint": "https://example.invalid", "model": "m", "timeout_s": 45}
    )
    assert tuned.timeout_s == 45
    default = _endpoint_from_spec({"endpoint": "https://example.invalid", "model": "m"})
    assert default.timeout_s == 300


# --- transport provenance on EndpointError (P7-A) -------------------------- #
#
# Regression (audit finding P7-A, tranche
# experiments/2026-08-29-defect-qualification-circuit-breaker/): the provider's
# HTTP status was flattened into a message string and never reached the record,
# so a credential refusal and a quota refusal wrote byte-identical qualification
# evidence while costing 0s and 5040s of mandated wait respectively.


def _ladder_against(status, monkeypatch):
    """Drive the REAL request_with_retries against a scripted HTTP status.

    Returns (call_list, sleep_list, run) — `run()` performs one urlopen
    through the shipped ladder, so the retry policy under test is the
    production one and not a restatement of it.
    """
    import urllib.error
    import urllib.request

    from deepreason.llm import endpoints as endpoints_module

    calls, sleeps = [], []

    def fake_urlopen(request, timeout=None):
        calls.append(request)
        raise urllib.error.HTTPError(
            "https://example.invalid/v1", status, "scripted", {}, None
        )

    monkeypatch.setattr(endpoints_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(endpoints_module.time, "sleep", sleeps.append)

    def run():
        return endpoints_module.request_with_retries(
            lambda: urllib.request.urlopen(
                urllib.request.Request("https://example.invalid/v1")
            )
        )

    return calls, sleeps, run


def test_endpoint_error_carries_a_non_retryable_provider_status(monkeypatch):
    """R1. A 401 is terminal on arrival: one call, no sleep, status kept."""
    from deepreason.llm.endpoints import EndpointError

    calls, sleeps, run = _ladder_against(401, monkeypatch)

    with pytest.raises(EndpointError) as caught:
        run()

    assert caught.value.http_status == 401
    assert caught.value.condition == "http_refusal"
    assert len(calls) == 1
    assert sleeps == []


def test_endpoint_error_carries_the_status_that_exhausted_the_ladder(monkeypatch):
    """R2. A 429 walks the whole 2s/4s/8s ladder and still names itself."""
    from deepreason.llm.endpoints import EndpointError

    calls, sleeps, run = _ladder_against(429, monkeypatch)

    with pytest.raises(EndpointError) as caught:
        run()

    assert caught.value.http_status == 429
    assert len(calls) == 4
    assert sleeps == [2, 4, 8]


def test_failure_code_distinguishes_a_credential_from_a_quota_refusal():
    """R3. The two conditions the defect collapsed now write different bytes."""
    from deepreason.cli.doctor import _failure_code
    from deepreason.llm.endpoints import EndpointError

    assert _failure_code(EndpointError("x", http_status=401)) == "ENDPOINT_HTTP_401"
    assert _failure_code(EndpointError("x", http_status=429)) == "ENDPOINT_HTTP_429"
    assert (
        _failure_code(EndpointError("x", condition="read_timeout"))
        == "ENDPOINT_READ_TIMEOUT"
    )
    assert _failure_code(EndpointError("x")) == "ENDPOINT_TRANSPORT"


def test_the_provider_status_is_never_exposed_as_a_numeric_code_attribute():
    """R4. Parked finding C5, pinned so this tranche cannot step on it.

    `_failure_code` reads `.code` FIRST, and a numeric one normalises to the
    string "429", which fails ProductionContractCaseResultV1.failure_code's
    own `^[A-Z][A-Z0-9_]*$` pattern and would take the whole battery down
    through qualification.py's exception flattening.
    """
    import re

    from deepreason.cli.doctor import _failure_code
    from deepreason.llm.endpoints import EndpointError

    error = EndpointError("x", http_status=429)
    assert not hasattr(error, "code")
    assert re.fullmatch(r"[A-Z][A-Z0-9_]*", _failure_code(error))
