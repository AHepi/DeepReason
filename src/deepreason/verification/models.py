"""Shared immutable result records for verifier backends."""

from __future__ import annotations

from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class VerificationRequest(BaseModel):
    """Generic transport envelope; backend-specific payloads remain explicit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    backend: str = Field(min_length=1)
    toolchain_id: str = Field(min_length=1)
    payload: dict[str, Any]


class VerificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    backend: str = Field(min_length=1)
    fingerprint: dict[str, Any]
    verdict: Literal["pass", "fail", "overrun"]
    diagnostics_ref: str | None = None
    output_ref: str | None = None
    trace: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class VerifierBackend(Protocol):
    name: str

    def fingerprint(self) -> dict[str, Any]: ...

    def verify(self, request: Any, blobs: Any = None) -> VerificationResult: ...
