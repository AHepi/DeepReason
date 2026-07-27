"""Canonical aggregate limits.

Unlimited aggregate work is an unbounded sequence of bounded operations; it
never relaxes a model-output, verifier, simulation, retrieval, or sandbox
limit.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Limit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["bounded", "unlimited"]
    value: int | None = Field(default=None)

    @model_validator(mode="after")
    def _coherent(self):
        if self.mode == "bounded" and (self.value is None or self.value <= 0):
            raise ValueError("bounded limit requires a positive value")
        if self.mode == "unlimited" and self.value is not None:
            raise ValueError("unlimited limit must have value=null")
        return self

    @classmethod
    def bounded(cls, value: int) -> "Limit":
        return cls(mode="bounded", value=value)

    @classmethod
    def unlimited(cls) -> "Limit":
        return cls(mode="unlimited", value=None)


def parse_limit(
    value: int | str | None | Limit,
    *,
    optional: bool = True,
) -> tuple[Limit, str | None]:
    """Parse a boundary value and return an optional deprecation diagnostic."""
    if isinstance(value, Limit):
        return value, None
    if value is None:
        if optional:
            return Limit.unlimited(), None
        raise ValueError("limit is required")
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized == "unlimited":
            return Limit.unlimited(), None
        try:
            value = int(normalized)
        except ValueError as error:
            raise ValueError("limit must be a positive integer or 'unlimited'") from error
    numeric = int(value)
    if numeric < 0:
        raise ValueError("limit cannot be negative")
    if numeric == 0:
        return Limit.unlimited(), "legacy zero limit means unlimited; use 'unlimited'"
    return Limit.bounded(numeric), None


class LimitExceeded(RuntimeError):
    pass


class AggregateMeter:
    """Always-on spend accounting for either bounded or unlimited policy."""

    def __init__(self, limit: Limit, *, name: str = "aggregate") -> None:
        self.limit = limit
        self.name = name
        self.spent = 0

    @property
    def remaining(self) -> int | None:
        if self.limit.mode == "unlimited":
            return None
        return max(0, int(self.limit.value) - self.spent)

    def check(self, amount: int = 1) -> None:
        if amount < 0:
            raise ValueError("meter amount cannot be negative")
        if self.limit.mode == "bounded" and self.spent + amount > int(self.limit.value):
            raise LimitExceeded(
                f"{self.name} limit exhausted: {self.spent}/{self.limit.value}"
            )

    def add(self, amount: int = 1) -> None:
        self.check(amount)
        self.spent += amount

    def snapshot(self) -> dict:
        return {
            "name": self.name,
            "mode": self.limit.mode,
            "limit": self.limit.value,
            "spent": self.spent,
            "remaining": self.remaining,
        }
