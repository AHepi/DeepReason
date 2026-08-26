"""Regression (W7 run-anatomy synthesis, 2026-08-26, row 9): the allocation
controller recorded 47 tuning decisions across the committed population and
NONE of them became the ``max_tokens`` of any later call.  The conjecturer's
cap was driven 32768 -> 800 across sixteen cycles of
``experiments/2026-08-25-change-constructive-frontier/run`` while every single
dispatch went out at 32768.

The cause is a composition of two correct fixes, not a bug in either.  ERRATA
E43 relaxed the route firewall's completion check from an identity to a ceiling
so a lawful narrowing stopped killing the run (run 40e713b30a147dfc, cycle 2).
The epoch-3 fix then made ``Adapter._completion_cap`` return the route ceiling
whenever the route declares qualified capacity, because the preview and the
call each recomputed the cap and a controller settling a seat between them
parted the two sides of the reservation guard (run bb0455384ea09b5b attempt 3).
Together they left ``Controller._apply_cap`` writing ``endpoint.max_tokens``
and nothing downstream reading it.

The recompute defect is closed by DIFFERENT machinery that these tests do not
touch: under a dispatch authorization the call CONSUMES
``reservation_record.completion_bound_tokens`` instead of recomputing.  So the
completion cap may once again be the seat's SETTLED value, bounded by the route
ceiling qualification certified.

These tests pin the connection itself.  They fail on the exact reversion --
booking the ceiling instead of the settled cap -- and they are written against
the booked envelope rather than against completion counts, because
``experiments/2026-08-26-run-anatomy-program/W5-signals-controller/RESULTS.md``
("One thing the record does NOT let us conclude") shows completions cannot
distinguish an enforced cap from an ignored one when no call ever wanted more.
"""

from deepreason.controller import Controller
from deepreason.llm.adapter import LLMAdapter

from tests.test_route_lease_maxtokens_tuning import (
    LEASED_CAP,
    QUALIFIED_WINDOW,
    RECORDED_TUNE,
    _log_conjecturer_calls,
    _seat,
)


def _booked(adapter, endpoint, lease) -> int:
    """The completion envelope one dispatch would book for this seat.

    Read through the adapter's own single definition -- ``preview_request``
    returns exactly this value as its fourth element and the workflow books
    that number -- so the assertion is about what the wire would carry, not
    about a private helper's arithmetic.
    """
    return type(adapter)._completion_cap(endpoint, lease)


def test_a_settled_cap_is_what_a_qualified_dispatch_books(tmp_path):
    """W5's finding, inverted: the decision reaches the envelope.

    The recorded narrowing to 20480 on the reach-rich run's own qualified
    route. Before the fix this booked 32768 -- the route ceiling -- and the
    controller's decision reached nothing.
    """
    harness, adapter, lease, endpoint = _seat(
        tmp_path, max_tokens=LEASED_CAP, context_window_tokens=QUALIFIED_WINDOW
    )
    controller = Controller(harness, adapter)
    _log_conjecturer_calls(harness, n=6, truncated=False)

    assert controller.step() == {"cap:conjecturer": RECORDED_TUNE}
    assert endpoint.max_tokens == RECORDED_TUNE
    assert _booked(adapter, endpoint, lease) == RECORDED_TUNE


def test_a_settled_cap_above_the_qualified_ceiling_still_books_the_ceiling(tmp_path):
    """Qualification's ceiling still binds absolutely.

    Wiring the settled cap must not let any endpoint book more completion than
    the leased route certified -- the escape E43's ceiling branch exists to
    refuse. The booking clamps rather than raising, because the firewall is
    what refuses an inadmissible endpoint; the envelope's job is to stay
    inside it.
    """
    _harness, adapter, lease, endpoint = _seat(
        tmp_path, max_tokens=LEASED_CAP, context_window_tokens=QUALIFIED_WINDOW
    )
    endpoint.max_tokens = LEASED_CAP + 10_000

    assert _booked(adapter, endpoint, lease) == LEASED_CAP


def test_an_unqualified_route_books_the_settled_cap_exactly_as_before(tmp_path):
    """The legacy branch is untouched.

    A route declaring no ``context_window_tokens`` always booked the endpoint's
    own cap and keeps doing so; this fix is about the qualified branch alone.
    """
    _harness, adapter, lease, endpoint = _seat(
        tmp_path, max_tokens=LEASED_CAP, context_window_tokens=None
    )
    endpoint.max_tokens = 4096

    assert _booked(adapter, endpoint, lease) == 4096


def test_every_step_of_a_narrowing_series_reaches_the_envelope(tmp_path):
    """The sixteen-cycle series W5 tabled, in miniature.

    W5's table is sixteen rows of "tuned to X, dispatched 32768". One decision
    reaching the wire could be an accident of a single value; a series that
    tracks every applied knob is the property. Each step re-reads the envelope
    after the controller settles, so a fix that happened to work once and then
    latched onto a stale value fails here.
    """
    harness, adapter, lease, endpoint = _seat(
        tmp_path, max_tokens=LEASED_CAP, context_window_tokens=QUALIFIED_WINDOW
    )
    controller = Controller(harness, adapter)

    booked = []
    for _ in range(6):
        _log_conjecturer_calls(harness, n=6, truncated=False)
        applied = controller.step()
        if not applied:
            continue
        booked.append((applied["cap:conjecturer"], _booked(adapter, endpoint, lease)))

    assert booked, "the controller never settled the seat"
    assert all(tuned == sent for tuned, sent in booked), booked
    assert len({tuned for tuned, _ in booked}) > 1, booked


def test_the_completion_envelope_has_exactly_one_definition(tmp_path):
    """The property the epoch-3 fix bought, kept.

    ``preview_request`` returns the envelope the workflow books, and the call
    reads it back off the reservation. Both sides must therefore agree with
    ``_completion_cap`` for the SAME endpoint and lease -- a second expression
    anywhere is what let a mid-cycle settling part them by exactly the amount
    of the narrowing (run bb0455384ea09b5b attempt 3).
    """
    import inspect

    source = inspect.getsource(LLMAdapter._completion_cap)
    preview = inspect.getsource(LLMAdapter.preview_request)
    call = inspect.getsource(LLMAdapter.call)

    assert "self._completion_cap(endpoint, lease)" in preview
    assert "reservation_record.completion_bound_tokens" in call
    # The reversion this file exists to catch: booking the ceiling
    # unconditionally on the qualified branch, ignoring the settled cap.
    assert "getattr(endpoint" in source, source
