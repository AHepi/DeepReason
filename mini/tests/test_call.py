"""M0 — call: meter==log under schema storms and budget death (the parent's
chaos-test family, ported to the mini's single call path)."""

import json

import pytest
from pydantic import BaseModel

from minireason.call import (BudgetExceeded, EndpointError, MockEndpoint,
                             SchemaError, TokenMeter, call, usage_tokens)
from minireason.log import BlobStore


class Out(BaseModel):
    answer: str


VALID = json.dumps({"answer": "ok"})


def test_success_carries_spend_and_meter_matches(tmp_path):
    meter = TokenMeter(budget=10_000)
    out, spend = call(MockEndpoint([VALID]), "q", Out, meter, BlobStore(tmp_path))
    assert out.answer == "ok"
    assert spend.tokens == meter.total > 0
    assert spend.attempts == 1


def test_repair_loop_feeds_error_back(tmp_path):
    seen = []

    def endpoint_fn(prompt):
        seen.append(prompt)
        return "not json at all" if len(seen) == 1 else VALID

    meter = TokenMeter()
    out, spend = call(MockEndpoint(endpoint_fn), "q", Out, meter, BlobStore(tmp_path))
    assert out.answer == "ok"
    assert spend.attempts == 2
    assert "previous output was invalid" in seen[1]
    assert spend.tokens == meter.total  # both attempts on one spend record


def test_schema_storm_exhausts_with_spend(tmp_path):
    meter = TokenMeter()
    with pytest.raises(SchemaError) as err:
        call(MockEndpoint(lambda p: "{}"), "q", Out, meter, BlobStore(tmp_path),
             retry_max=2)
    assert err.value.spend is not None
    assert err.value.spend.tokens == meter.total > 0
    assert err.value.spend.attempts == 3


def test_budget_death_mid_retry_carries_spend(tmp_path):
    # First attempt spends past the tiny budget; the pre-spend check on the
    # retry must hand back the already-spent tokens (the 833-token leak).
    meter = TokenMeter(budget=10)
    with pytest.raises(BudgetExceeded) as err:
        call(MockEndpoint(lambda p: "invalid " * 20), "q", Out, meter,
             BlobStore(tmp_path))
    assert err.value.spend is not None
    assert err.value.spend.tokens == meter.total > 10


def test_budget_death_before_any_spend_has_no_spend(tmp_path):
    meter = TokenMeter(budget=10)
    meter.add({"prompt_tokens": 10, "completion_tokens": 5})
    with pytest.raises(BudgetExceeded) as err:
        call(MockEndpoint([VALID]), "q", Out, meter, BlobStore(tmp_path))
    assert err.value.spend is None  # nothing new spent, nothing to log


def test_endpoint_error_after_partial_spend(tmp_path):
    responses = iter(["bad json"])

    def endpoint_fn(prompt):
        try:
            return next(responses)
        except StopIteration:
            raise EndpointError("provider fell over") from None

    meter = TokenMeter()
    with pytest.raises(EndpointError) as err:
        call(MockEndpoint(endpoint_fn), "q", Out, meter, BlobStore(tmp_path))
    assert err.value.spend is not None
    assert err.value.spend.tokens == meter.total > 0


def test_partial_usage_block_never_counts_as_zero():
    # total_tokens-only shape (seen live) must not zero the hard budget.
    assert usage_tokens({"total_tokens": 42}, "x" * 400, "y" * 400) == {
        "prompt_tokens": 42, "completion_tokens": 0}
    # Fully absent usage falls back to chars/4.
    est = usage_tokens(None, "x" * 400, "y" * 40)
    assert est == {"prompt_tokens": 100, "completion_tokens": 10}
    # Normal shape passes through.
    assert usage_tokens({"prompt_tokens": 7, "completion_tokens": 3}, "", "") == {
        "prompt_tokens": 7, "completion_tokens": 3}


def test_truncation_gets_compression_hint(tmp_path):
    seen = []
    endpoint = MockEndpoint(lambda p: (seen.append(p) or '{"answer'))
    endpoint_complete = endpoint.complete

    def complete(prompt):
        raw = endpoint_complete(prompt)
        endpoint.last_finish_reason = "length"
        return raw

    endpoint.complete = complete
    with pytest.raises(SchemaError):
        call(endpoint, "q", Out, TokenMeter(), BlobStore(tmp_path), retry_max=1)
    assert "CUT OFF mid-JSON" in seen[1]
    assert "MORE COMPACTLY" in seen[1]
