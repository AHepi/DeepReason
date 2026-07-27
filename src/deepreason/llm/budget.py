"""Token budgeting (spec §14: global budgets, generalized to the provider).

A TokenMeter is shared across all endpoints of a provider and enforces a
HARD ceiling with a locked reserve-settle protocol:

- ``reserve()`` runs BEFORE dispatch.  It books a conservative upper bound
  for the call — a prompt bound (``ceil(chars / 3)`` when no tokenizer is
  available; deliberately conservative, since typical BPE English text runs
  ~4 chars/token) plus the transport's ``max_tokens`` completion cap — and
  rejects the dispatch when ``total + outstanding reserves + bound`` would
  exceed the ceiling.  Where a finite ceiling is set and either bound is
  unknown, the reservation FAILS CLOSED: an unboundable call is never
  dispatched against a hard budget.
- ``Reservation.settle()`` runs after the response and replaces the
  reserved bound with the provider-reported usage (the reservation shrinks
  to reality).  ``Reservation.release()`` returns the reserve untouched
  when the call died with unknown usage (transport failure), matching the
  pre-reserve accounting where such calls recorded nothing.

All transitions happen under one lock, so concurrent dispatchers can never
jointly overshoot: the logged total never exceeds the ceiling as long as
providers honor their own ``max_tokens`` caps.  Enforcement lives in the
adapter (the one place every call passes through); endpoints only report
usage.

``check()``/``add()`` are preserved as a thin compatibility layer for old
code paths (scripts, minireason) with their historical semantics: check is
a total-versus-ceiling gate that can overshoot by one in-flight call, and
add records usage unconditionally.  New code should use ``reserve()``.
"""

import threading


class TokenBudgetExceeded(RuntimeError):
    pass


def conservative_prompt_bound(text: str) -> int:
    """Upper bound on prompt tokens without a tokenizer: ``ceil(chars / 3)``.

    Documented heuristic: OpenAI-style BPE averages ~4 chars/token on
    English prose; dividing by 3 over-counts, which is the safe direction
    for a reservation against a hard ceiling.
    """

    return -(-len(text) // 3) if text else 0


class Reservation:
    """One call's booked upper bound; settle or release exactly once."""

    __slots__ = ("_meter", "amount", "_open")

    def __init__(self, meter: "TokenMeter", amount: int) -> None:
        self._meter = meter
        self.amount = amount
        self._open = True

    def settle(self, usage: dict) -> None:
        """Replace the reserved bound with provider-reported usage."""

        self._close()
        self._meter._settle(self.amount, usage)

    def release(self) -> None:
        """Return the reserve without recording spend (usage unknown —
        e.g. transport failure before any usage report)."""

        self._close()
        self._meter._settle(self.amount, None)

    @property
    def is_open(self) -> bool:
        """Whether this live reservation still authorizes one settlement."""

        return self._open

    def _close(self) -> None:
        if not self._open:
            raise RuntimeError("reservation already settled or released")
        self._open = False


class TokenMeter:
    def __init__(self, budget: int | None = None) -> None:
        self.budget = budget
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls = 0
        self.reserved = 0  # outstanding reserve, in tokens
        self._lock = threading.Lock()

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def check(self) -> None:
        """Compatibility gate (historical semantics, unchanged): raise once
        the recorded total has reached the ceiling.  Unlike ``reserve`` this
        does not account for the upcoming call's bound."""

        if self.budget is not None and self.total >= self.budget:
            raise TokenBudgetExceeded(
                f"token budget exhausted: {self.total}/{self.budget}"
            )

    def add(self, usage: dict) -> None:
        """Compatibility path: record usage unconditionally (no reserve)."""

        with self._lock:
            self._record(usage)

    def reserve(
        self,
        *,
        prompt_text: str | None = None,
        prompt_tokens: int | None = None,
        max_tokens: int | None = None,
    ) -> Reservation:
        """Book a conservative upper bound for one dispatch, or refuse it.

        The prompt bound is ``prompt_tokens`` when a caller has a real
        tokenizer count, else ``conservative_prompt_bound(prompt_text)``
        (chars/3).  The completion bound is the transport ``max_tokens``
        cap.  Against a finite ceiling, a missing bound on either side
        fails closed with :class:`TokenBudgetExceeded`.
        """

        with self._lock:
            bound_prompt = prompt_tokens
            if bound_prompt is None and prompt_text is not None:
                bound_prompt = conservative_prompt_bound(prompt_text)
            if self.budget is None:
                # No ceiling to defend: book whatever bound is known so the
                # snapshot stays informative, and never block.
                amount = (bound_prompt or 0) + (max_tokens or 0)
                self.reserved += amount
                return Reservation(self, amount)
            if bound_prompt is None:
                raise TokenBudgetExceeded(
                    "token budget reservation failed closed: no prompt bound "
                    f"(ceiling {self.budget})"
                )
            if max_tokens is None:
                raise TokenBudgetExceeded(
                    "token budget reservation failed closed: no completion "
                    f"bound (max_tokens unknown; ceiling {self.budget})"
                )
            amount = int(bound_prompt) + int(max_tokens)
            if self.total + self.reserved + amount > self.budget:
                raise TokenBudgetExceeded(
                    f"token budget cannot cover dispatch: {self.total} spent "
                    f"+ {self.reserved} reserved + {amount} bound > "
                    f"{self.budget}"
                )
            self.reserved += amount
            return Reservation(self, amount)

    def _settle(self, amount: int, usage: dict | None) -> None:
        with self._lock:
            self.reserved -= amount
            if usage is not None:
                self._record(usage)

    def _record(self, usage: dict) -> None:
        self.prompt_tokens += int(usage.get("prompt_tokens", 0))
        self.completion_tokens += int(usage.get("completion_tokens", 0))
        self.calls += 1

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total": self.total,
                "budget": self.budget,
                "calls": self.calls,
                "reserved": self.reserved,
            }
