import pytest

from deepreason.runtime.budget import AggregateMeter, Limit, LimitExceeded, parse_limit


def test_boundary_limit_grammar_and_legacy_zero_diagnostic():
    assert parse_limit(7)[0] == Limit.bounded(7)
    assert parse_limit("unlimited")[0] == Limit.unlimited()
    assert parse_limit(None)[0] == Limit.unlimited()
    zero, diagnostic = parse_limit(0)
    assert zero == Limit.unlimited()
    assert "legacy zero" in diagnostic
    with pytest.raises(ValueError):
        parse_limit(-1)


def test_unlimited_meter_records_spend_without_stopping():
    meter = AggregateMeter(Limit.unlimited(), name="cycles")
    meter.add(10**6)
    assert meter.spent == 10**6
    assert meter.remaining is None


def test_bounded_meter_checks_before_overspend():
    meter = AggregateMeter(Limit.bounded(2), name="proof attempts")
    meter.add(2)
    with pytest.raises(LimitExceeded):
        meter.add()
    assert meter.spent == 2
