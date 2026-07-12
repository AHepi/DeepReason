"""Shared immutable request and result records for verifier backends."""

from __future__ import annotations

import re
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.ontology.frozen import FrozenDict, FrozenList

_DIGEST_PATTERN = r"^[0-9a-f]{64}$"
_EXACT_LEAN_ID = r"^lean4@[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$"


class VerificationRequest(BaseModel):
    """One finite verifier operation.

    ``payload`` supports generic backends. Lean uses the explicit pinned
    fields so source, imports, recursion, and heartbeat bounds cannot hide in
    an untyped object.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    backend: str = Field(min_length=1)
    toolchain_id: str = Field(min_length=1)
    payload: dict[str, Any] | None = None
    source_ref: str | None = Field(default=None, pattern=_DIGEST_PATTERN)
    imports_lock_ref: str | None = Field(default=None, pattern=_DIGEST_PATTERN)
    max_heartbeats: int = Field(default=200_000, gt=0)
    max_rec_depth: int = Field(default=1_000, gt=0)
    allow_sorry: bool = False
    allowed_axioms: list[str] = Field(default_factory=list)
    target_theorems: list[str] = Field(default_factory=list)

    @field_validator("toolchain_id")
    @classmethod
    def _resolved_toolchain(cls, value: str) -> str:
        if (
            value in {"auto", "latest"}
            or value.endswith(".x")
            or any(marker in value for marker in "*^~<>= ")
        ):
            raise ValueError("toolchain_id must be an exact resolved coordinate")
        return value

    @field_validator("allowed_axioms", "target_theorems")
    @classmethod
    def _unique_nonempty_names(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("names must be non-empty")
        if any(re.search(r"[\s#;]", item) for item in value):
            raise ValueError("names must be single Lean identifiers")
        if len(value) != len(set(value)):
            raise ValueError("names must be unique")
        return FrozenList(value)

    @model_validator(mode="after")
    def _backend_shape(self):
        if self.backend == "lean4":
            if not re.fullmatch(_EXACT_LEAN_ID, self.toolchain_id):
                raise ValueError("toolchain_id must pin an exact Lean 4 version")
            if self.source_ref is None:
                raise ValueError("Lean verification requires source_ref")
        elif self.payload is None and self.source_ref is None:
            raise ValueError("generic verification requires payload or source_ref")
        return self


class VerificationResult(BaseModel):
    """Immutable verifier receipt; only ``fail`` can back fail criticism."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    backend: str = Field(min_length=1)
    fingerprint: dict[str, Any]
    verdict: Literal["pass", "fail", "overrun"]
    diagnostics_ref: str | None = Field(default=None, pattern=_DIGEST_PATTERN)
    output_ref: str | None = Field(default=None, pattern=_DIGEST_PATTERN)
    trace: dict[str, Any] = Field(default_factory=dict)
    axioms_ref: str | None = Field(default=None, pattern=_DIGEST_PATTERN)
    theorems: list[str] = Field(default_factory=list)
    source_sha256: str | None = Field(default=None, pattern=_DIGEST_PATTERN)
    toolchain_sha256: str | None = Field(default=None, pattern=_DIGEST_PATTERN)

    @field_validator("fingerprint", "trace", mode="after")
    @classmethod
    def _freeze_mappings(cls, value: dict[str, Any]):
        return FrozenDict(value)

    @field_validator("theorems", mode="after")
    @classmethod
    def _freeze_theorems(cls, value: list[str]):
        return FrozenList(value)

    @property
    def fail_warrant_eligible(self) -> bool:
        return self.verdict == "fail"


@runtime_checkable
class VerifierBackend(Protocol):
    def fingerprint(self) -> dict[str, Any]: ...

    def verify(self, request: Any, blobs: Any = None) -> VerificationResult: ...
