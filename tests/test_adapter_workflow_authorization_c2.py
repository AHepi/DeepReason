"""Active workflow callbacks fail closed at the provider boundary."""

import json

import pytest

from deepreason.harness import Harness
from deepreason.llm.adapter import (
    LLMAdapter,
    WorkflowAuthorizationError,
)
from deepreason.llm.budget import TokenMeter
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.endpoints import MockEndpoint


GOOD = json.dumps(
    {"candidates": [{"content": "bounded", "typicality": 0.5}]}
)
WORK_ID = "sha256:" + "a" * 64


def test_required_dispatch_releases_reservation_without_calling_provider(tmp_path):
    calls = []
    endpoint = MockEndpoint(
        lambda prompt: calls.append(prompt) or GOOD,
        max_tokens=64,
    )
    meter = TokenMeter(budget=10_000)
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        Harness(tmp_path).blobs,
        meter=meter,
    )

    with pytest.raises(WorkflowAuthorizationError, match="not durably authorized"):
        adapter.call(
            "conjecturer",
            "PACK",
            ConjecturerOutput,
            workflow_dispatch_observer=lambda _reserved: None,
            workflow_dispatch_required=True,
        )

    assert calls == []
    assert meter.total == 0
    assert meter.snapshot()["reserved"] == 0


def test_required_repair_failure_stops_before_next_provider_attempt(tmp_path):
    calls = []
    responses = iter(("{invalid-json", GOOD))
    endpoint = MockEndpoint(
        lambda prompt: calls.append(prompt) or next(responses),
        max_tokens=64,
    )
    meter = TokenMeter(budget=10_000)
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        Harness(tmp_path).blobs,
        meter=meter,
        retry_max=1,
    )

    with pytest.raises(WorkflowAuthorizationError) as raised:
        adapter.call(
            "conjecturer",
            "PACK",
            ConjecturerOutput,
            workflow_dispatch_observer=lambda _reserved: WORK_ID,
            workflow_repair_observer=lambda _attempt: (_ for _ in ()).throw(
                RuntimeError("injected repair persistence failure")
            ),
            workflow_dispatch_required=True,
        )

    assert len(calls) == 1
    assert raised.value.spend is not None
    assert raised.value.spend.work_order_id == WORK_ID
    assert len(raised.value.spend.attempt_trace) == 1
    assert meter.total == raised.value.spend.tokens
    assert meter.snapshot()["reserved"] == 0
