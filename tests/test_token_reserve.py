"""Reserve-settle TokenMeter (llm/budget.py): the hard ceiling holds under
concurrency, settling shrinks reservations to provider-reported usage, and
an unboundable dispatch against a finite ceiling fails closed."""

import random
from concurrent.futures import ThreadPoolExecutor

import pytest

from deepreason.llm.budget import (
    TokenBudgetExceeded,
    TokenMeter,
    conservative_prompt_bound,
)


def test_concurrent_reservations_never_exceed_ceiling():
    """ThreadPoolExecutor stress: many dispatchers race reserve/settle; at
    every observable instant total + reserved stays within the ceiling, and
    the final logged total never exceeds it."""

    ceiling = 50_000
    meter = TokenMeter(budget=ceiling)
    settled = []
    rejected = []

    def worker(seed: int) -> None:
        rng = random.Random(seed)
        for _ in range(40):
            prompt = "x" * rng.randint(30, 2_400)  # bound 10..800
            max_tokens = rng.randint(1, 400)
            try:
                reservation = meter.reserve(
                    prompt_text=prompt, max_tokens=max_tokens
                )
            except TokenBudgetExceeded:
                rejected.append(1)
                continue
            # Invariant while the reservation is outstanding.
            snap = meter.snapshot()
            assert snap["total"] + snap["reserved"] <= ceiling
            assert snap["total"] <= ceiling
            usage = {
                "prompt_tokens": rng.randint(
                    1, conservative_prompt_bound(prompt)
                ),
                "completion_tokens": rng.randint(0, max_tokens),
            }
            reservation.settle(usage)
            settled.append(usage["prompt_tokens"] + usage["completion_tokens"])
            assert meter.snapshot()["total"] <= ceiling

    with ThreadPoolExecutor(max_workers=16) as pool:
        for future in [pool.submit(worker, seed) for seed in range(16)]:
            future.result()

    assert rejected, "the stress test must actually hit the ceiling"
    assert settled, "some dispatches must have been admitted"
    snap = meter.snapshot()
    assert snap["total"] == sum(settled)  # every settle recorded exactly once
    assert snap["total"] <= ceiling  # the logged total never exceeds it
    assert snap["reserved"] == 0  # every reservation settled or rejected
    assert snap["calls"] == len(settled)


def test_settle_shrinks_reservation_to_reported_usage():
    meter = TokenMeter(budget=1_000)
    reservation = meter.reserve(prompt_text="y" * 900, max_tokens=200)  # 500
    assert meter.reserved == 500
    # A second full-size reservation cannot fit while the first is open.
    with pytest.raises(TokenBudgetExceeded):
        meter.reserve(prompt_text="y" * 900, max_tokens=300)
    reservation.settle({"prompt_tokens": 40, "completion_tokens": 10})
    assert meter.reserved == 0
    assert meter.total == 50  # provider-reported usage, not the bound
    assert meter.calls == 1
    # Settling freed the headroom the bound had held.
    second = meter.reserve(prompt_text="y" * 900, max_tokens=300)  # 600
    assert second.amount == 600
    second.release()  # unknown usage: reserve returned, nothing recorded
    assert meter.reserved == 0 and meter.total == 50 and meter.calls == 1
    with pytest.raises(RuntimeError):
        second.release()  # one-shot


def test_fail_closed_on_unknown_bound():
    meter = TokenMeter(budget=10_000)
    with pytest.raises(TokenBudgetExceeded):  # no completion bound
        meter.reserve(prompt_text="hello", max_tokens=None)
    with pytest.raises(TokenBudgetExceeded):  # no prompt bound
        meter.reserve(max_tokens=64)
    assert meter.reserved == 0 and meter.total == 0
    # Without a ceiling there is nothing to defend: dispatch is not blocked.
    unmetered = TokenMeter(budget=None)
    reservation = unmetered.reserve(prompt_text="hello", max_tokens=None)
    reservation.settle({"prompt_tokens": 3, "completion_tokens": 2})
    assert unmetered.total == 5


def test_check_add_compatibility_layer_semantics_unchanged():
    """Old code paths (scripts, minireason parity) keep the historical
    check/add behavior: check gates on recorded total only, add records
    unconditionally."""

    meter = TokenMeter(budget=100)
    meter.check()  # under the ceiling: passes
    meter.add({"prompt_tokens": 70, "completion_tokens": 40})  # overshoot ok
    assert meter.total == 110
    with pytest.raises(TokenBudgetExceeded):
        meter.check()
