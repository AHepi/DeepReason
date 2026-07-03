"""Token budgeting (spec §14: global budgets, generalized to the provider).

A TokenMeter is shared across all endpoints of a provider and enforces a
HARD ceiling: once total tokens (prompt + completion) reach the budget, the
next call raises TokenBudgetExceeded before spending anything. The
scheduler catches it and stops the run gracefully — budget exhaustion is a
logged stop, never a crash. Enforcement lives in the adapter (the one
place every call passes through); endpoints only report usage.
"""


class TokenBudgetExceeded(RuntimeError):
    pass


class TokenMeter:
    def __init__(self, budget: int | None = None) -> None:
        self.budget = budget
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def check(self) -> None:
        if self.budget is not None and self.total >= self.budget:
            raise TokenBudgetExceeded(
                f"token budget exhausted: {self.total}/{self.budget}"
            )

    def add(self, usage: dict) -> None:
        self.prompt_tokens += int(usage.get("prompt_tokens", 0))
        self.completion_tokens += int(usage.get("completion_tokens", 0))
        self.calls += 1

    def snapshot(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total": self.total,
            "budget": self.budget,
            "calls": self.calls,
        }
