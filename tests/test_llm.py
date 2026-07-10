"""LLM adapter (spec §9): schema validation, bounded repair retries, logged
prompt/raw blobs."""

import json

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
