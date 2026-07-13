"""M0 — call: meter==log under schema storms and budget death (the parent's
chaos-test family, ported to the mini's single call path)."""

import json

import pytest
from pydantic import BaseModel

from minireason.call import (BudgetExceeded, EndpointError, MockEndpoint,
                             SchemaError, TokenMeter, call, usage_tokens)
from minireason.log import BlobStore
from minireason.loop import Session


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
    assert "INVALID JSON" in seen[1]
    assert spend.tokens == meter.total  # both attempts on one spend record
    assert [attempt.valid for attempt in spend.attempt_trace] == [False, True]
    assert sum(attempt.tokens for attempt in spend.attempt_trace) == spend.tokens
    assert BlobStore(tmp_path).get(spend.attempt_trace[0].raw_ref) == b"not json at all"
    assert BlobStore(tmp_path).get(spend.attempt_trace[0].diagnostic_ref)


def test_third_attempt_repairs_only_the_invalid_subtree(tmp_path):
    seen = []

    def endpoint_fn(prompt):
        seen.append(prompt)
        if len(seen) < 3:
            return json.dumps({"answer": 7})
        return json.dumps("ok")

    out, spend = call(
        MockEndpoint(endpoint_fn),
        "q",
        Out,
        TokenMeter(),
        BlobStore(tmp_path),
        retry_max=99,
    )

    assert out.answer == "ok"
    assert spend.attempts == 3
    assert len(seen) == 3  # RETRY_MAX cannot open a fourth transport attempt.
    assert "Repair only the JSON value at /answer" in seen[2]
    assert [item.repair_scope for item in spend.attempt_trace] == [
        "/answer",
        "/answer",
        "/answer",
    ]
    assert [item.valid for item in spend.attempt_trace] == [False, False, True]


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
    assert len(err.value.spend.attempt_trace) == 2
    assert err.value.spend.attempt_trace[-1].usage_unknown
    assert err.value.spend.attempt_trace[-1].diagnostic_ref


def test_endpoint_error_before_usage_still_carries_replay_trace(tmp_path):
    def endpoint_fn(_prompt):
        raise EndpointError("bounded timeout")

    blobs = BlobStore(tmp_path)
    with pytest.raises(EndpointError) as err:
        call(MockEndpoint(endpoint_fn), "q", Out, TokenMeter(), blobs)

    spend = err.value.spend
    assert spend is not None and spend.tokens == 0 and spend.attempts == 1
    attempt = spend.attempt_trace[0]
    assert attempt.usage_unknown and not attempt.raw_ref
    assert blobs.get(attempt.prompt_ref)
    assert b"bounded timeout" in blobs.get(attempt.diagnostic_ref)


def test_partial_usage_block_never_counts_as_zero():
    # total_tokens-only shape (seen live) must not zero the hard budget.
    assert usage_tokens({"total_tokens": 42}, "x" * 400, "y" * 400) == {
        "prompt_tokens": 21, "completion_tokens": 21}
    # Fully absent usage falls back to chars/4.
    est = usage_tokens(None, "x" * 400, "y" * 40)
    assert est == {"prompt_tokens": 100, "completion_tokens": 10}
    # Normal shape passes through.
    assert usage_tokens({"prompt_tokens": 7, "completion_tokens": 3}, "", "") == {
        "prompt_tokens": 7, "completion_tokens": 3}
    # One reported side is preserved; its peer is estimated, never zeroed.
    assert usage_tokens({"prompt_tokens": 7}, "x" * 40, "y" * 20) == {
        "prompt_tokens": 7, "completion_tokens": 5}
    assert usage_tokens({"completion_tokens": 3}, "x" * 40, "y" * 20) == {
        "prompt_tokens": 10, "completion_tokens": 3}


@pytest.mark.parametrize(
    ("partial_usage", "reported_side", "reported_value"),
    [
        ({"prompt_tokens": 7}, "prompt_tokens", 7),
        ({"completion_tokens": 3}, "completion_tokens", 3),
    ],
)
def test_one_sided_usage_matches_meter_and_shared_log(
    tmp_path, partial_usage, reported_side, reported_value
):
    class OneSidedUsageEndpoint(MockEndpoint):
        def complete(self, prompt):
            raw = super().complete(prompt)
            self.last_usage = dict(partial_usage)
            return raw

    session = Session(tmp_path / reported_side)
    meter = TokenMeter()
    _, spend = call(
        OneSidedUsageEndpoint([VALID]),
        "q",
        Out,
        meter,
        session.blobs,
    )
    session.measure(["usage-accounting-test"], spend)

    assert getattr(meter, reported_side) == reported_value
    missing_side = (
        meter.completion_tokens
        if reported_side == "prompt_tokens"
        else meter.prompt_tokens
    )
    assert missing_side > 0
    assert spend.tokens == meter.total == session.state.logged_tokens()


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
