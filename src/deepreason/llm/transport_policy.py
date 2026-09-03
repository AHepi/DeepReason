"""Transport retry policy — a versioned registry, selected by id from Config.

Imports nothing from `deepreason`: a policy is a pure function of what the
transport observed, so a consumer can never reach around the interface to a
subsystem, and this module can never grow a dependency the `DR-SUB-llm`
boundary check forbids.

The policy exists because a zero-byte close is not a transient fault. Measured
2026-09-03 against ollama.com: four non-streaming calls closed at 300.510 /
300.268 / 300.210 / 300.289 s having received zero bytes, across two model
families — a 0.3-second range is a timer on the path, and every resend of the
same request meets it again. The same call with `stream: true` completed at
369.6 s and at 756.5 s.

What a policy may NOT do, and why the obvious implementation is wrong: it may
not shrink `max_tokens` for the retry. `invariants.py` requires every recorded
`attempt.max_tokens` to be the route's or one a PRIOR logged controller policy
authorized, and `llm/` may not write to the log — so a cap chosen here could
never be authorized and would make the run replay-invalid. A cap change arms the
NEXT call, through the controller, exactly as compact recovery does.
"""

# Closed kind vocabulary. Keyed by the exception-name prefix the endpoint puts
# in front of every diagnostic string, so the in-process classifier and a reader
# working from a committed record cannot drift.
_KINDS = {
    "RemoteDisconnected": "zero_byte_close",
    "IncompleteRead": "mid_body_drop",
    "BadStatusLine": "mid_body_drop",
    "TimeoutError": "read_timeout",
    "URLError": "connect_failure",
    "ConnectionResetError": "connect_failure",
    "ConnectionRefusedError": "connect_failure",
    "HTTPError": "http_status",
    "_TransientBody": "malformed_body",
}

KINDS = frozenset({*_KINDS.values(), "other"})

# A wall close costs the full wall per attempt, so the bound is the same 2 the
# read-timeout branch already uses (TIMEOUT_FACTORS): one observation, one
# remedy, then stand down.
ZERO_BYTE_WALL_MAX_ATTEMPTS = 2

DEFAULT_POLICY_ID = "stream-the-retry-v1"


def classify(diagnostic: str) -> str:
    """The kind of transport fault a diagnostic string describes.

    P-A1 (run 4565139800f5ca02) recorded `RemoteDisconnected:...` and P-S1 (run
    9e48a36b1dec91ee) recorded `URLError:<urlopen error [Errno 111] Connection
    refused>`. They are different conditions with different costs — 300 s and
    milliseconds — and the policy below turns on telling them apart.
    """

    return _KINDS.get(str(diagnostic).split(":", 1)[0], "other")


class Decision:
    """What to do after one failed attempt. `action` is closed."""

    __slots__ = ("action", "reason")

    def __init__(self, action: str, reason: str) -> None:
        self.action = action
        self.reason = reason

    def __repr__(self) -> str:  # pragma: no cover - diagnostic aid only
        return f"Decision({self.action!r}, {self.reason!r})"


def _stream_the_retry_v1(kind, attempt_index, streaming_available):
    if kind != "zero_byte_close":
        return Decision("retry", "not a wall close")
    if attempt_index + 1 >= ZERO_BYTE_WALL_MAX_ATTEMPTS:
        return Decision("stand_down", "zero-byte wall, attempts exhausted")
    if streaming_available:
        return Decision("retry_streaming", "zero-byte wall, retry as a stream")
    return Decision("stand_down", "zero-byte wall, streaming unavailable")


def _identical_v0(kind, attempt_index, streaming_available):
    """The behaviour that shipped before this policy existed, kept selectable
    so a run can reproduce a historical shape without editing code."""

    return Decision("retry", "identical resend")


POLICIES = {
    DEFAULT_POLICY_ID: _stream_the_retry_v1,
    "identical-v0": _identical_v0,
}


def resolve(policy_id):
    """The policy for an id, and the id actually used.

    An unknown id falls back to the shipped default and DISCLOSES what it fell
    back from; it never refuses. Compile-time denial of a parseable
    configuration is abolished (operator law, 2026-08-12).
    """

    wanted = str(policy_id or DEFAULT_POLICY_ID)
    if wanted in POLICIES:
        return POLICIES[wanted], wanted, None
    return POLICIES[DEFAULT_POLICY_ID], DEFAULT_POLICY_ID, wanted


def decide(policy_id, kind, attempt_index, streaming_available):
    policy, _, _ = resolve(policy_id)
    return policy(kind, attempt_index, bool(streaming_available))
