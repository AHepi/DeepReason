"""Evaluate the two completion-cap expressions AS THEY WERE over identical inputs.

Historical: this reproduces the defect's arithmetic, not the current tree. Both
expressions existed in llm/adapter.py before 2026-08-23 -- preview_request's
`maximum` and call's `transport_limits["max_tokens"]`. The fix left only the
first (now `LLMAdapter._completion_cap`) and made `call` consume the booked
number instead of evaluating the second, so `dispatched_cap` below no longer
corresponds to anything in the source. Kept because it is the cheapest
statement of what "two computations" cost.

No provider, no adapter construction, no I/O.
"""


class Route:
    def __init__(self, max_tokens, context_window_tokens):
        self.max_tokens = max_tokens
        self.context_window_tokens = context_window_tokens


class Lease:
    def __init__(self, route):
        self.route = route


class Endpoint:
    def __init__(self, max_tokens):
        self.max_tokens = max_tokens


def booked_cap(lease, endpoint):
    """adapter.preview_request: the cap the workflow reserves against."""
    maximum = (
        lease.route.max_tokens
        if lease.route.context_window_tokens is not None
        else getattr(endpoint, "max_tokens", lease.route.max_tokens)
    )
    return int(maximum or 0)


def dispatched_cap(lease, endpoint):
    """adapter.call: the cap the guard recomputes at the wire boundary."""
    return int(getattr(endpoint, "max_tokens", lease.route.max_tokens) or 0)


CASES = (
    ("controller settled the seat below its ceiling", Route(32768, 131072), Endpoint(20480)),
    ("role spec omits max_tokens (endpoint default None)", Route(32768, 131072), Endpoint(None)),
    ("no qualified capacity declared (legacy route)", Route(32768, None), Endpoint(20480)),
    ("caps coincide", Route(32768, 131072), Endpoint(32768)),
)


def main():
    print(f"{'configuration':<52}{'booked':>8}{'dispatch':>10}{'delta':>8}")
    diverging = 0
    for name, route, endpoint in CASES:
        lease = Lease(route)
        booked, dispatched = booked_cap(lease, endpoint), dispatched_cap(lease, endpoint)
        diverging += booked != dispatched
        print(f"{name:<52}{booked:>8}{dispatched:>10}{booked - dispatched:>8}")
    print(f"\n{diverging} of {len(CASES)} configurations diverge")
    return diverging


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
