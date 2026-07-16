"""Typed process evidence for bounded v4 conjecture outcomes.

These events are authority observations only.  They never carry a formal
``StateDiff`` and never turn a context request or abstention into an artifact.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.frozen import FrozenRecord


class ConjectureTurnAction(str, Enum):
    CONTEXT_GRANTED = "context_granted"
    CONTEXT_DENIED = "context_denied"
    CONTEXT_EXHAUSTED = "context_exhausted"
    ABSTAINED = "abstained"


class ConjectureTurnEventPayloadV1(FrozenRecord):
    """Harness-authored result of evaluating one model proposal."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True
    )

    schema_: Literal["conjecture.turn.event.v1"] = Field(
        "conjecture.turn.event.v1", alias="schema"
    )
    decision_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    action: ConjectureTurnAction
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    problem_id: str = Field(min_length=1, max_length=512)
    school_id: str | None = Field(
        default=None, pattern=r"^school-(0|[1-9][0-9]*)$"
    )
    source_call_seq: int = Field(ge=0)
    expansion_index: int = Field(default=0, ge=0, le=8)
    maximum_expansions: int = Field(default=0, ge=0, le=8)
    request_hash: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    request_ref: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    abstention_hash: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    abstention_ref: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    prior_selection_receipt_ref: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    reason_code: Literal[
        "granted",
        "capability_not_granted",
        "request_limit_reached",
        "no_additional_context",
        "no_context_capacity",
        "channel_not_permitted",
        "abstained",
    ]

    @staticmethod
    def _identity_payload(values: dict) -> dict:
        return {
            key: value
            for key, value in values.items()
            if key not in {"schema", "schema_", "decision_id"}
            and value is not None
        }

    @classmethod
    def create(cls, **values) -> ConjectureTurnEventPayloadV1:
        payload = cls._identity_payload(values)
        decision_id = "sha256:" + sha256_hex(
            b"conjecture.turn.event.v1\x00" + canonical_json(payload)
        )
        return cls(decision_id=decision_id, **values)

    @model_validator(mode="after")
    def _action_shape_and_identity(self):
        request_action = self.action in {
            ConjectureTurnAction.CONTEXT_GRANTED,
            ConjectureTurnAction.CONTEXT_DENIED,
            ConjectureTurnAction.CONTEXT_EXHAUSTED,
        }
        if request_action != bool(self.request_hash and self.request_ref):
            raise ValueError("context decisions require one immutable request")
        if (self.request_hash is None) != (self.request_ref is None):
            raise ValueError("request hash and blob reference must appear together")
        abstained = self.action == ConjectureTurnAction.ABSTAINED
        if abstained != bool(self.abstention_hash and self.abstention_ref):
            raise ValueError("abstention events require one immutable abstention")
        if (self.abstention_hash is None) != (self.abstention_ref is None):
            raise ValueError("abstention hash and blob reference must appear together")
        if self.expansion_index > self.maximum_expansions:
            raise ValueError("expansion index exceeds the frozen maximum")
        expected_reasons = {
            ConjectureTurnAction.CONTEXT_GRANTED: {"granted"},
            ConjectureTurnAction.CONTEXT_DENIED: {
                "capability_not_granted",
                "no_additional_context",
                "no_context_capacity",
                "channel_not_permitted",
            },
            ConjectureTurnAction.CONTEXT_EXHAUSTED: {"request_limit_reached"},
            ConjectureTurnAction.ABSTAINED: {"abstained"},
        }
        if self.reason_code not in expected_reasons[self.action]:
            raise ValueError("reason code does not match the conjecture turn action")
        values = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        expected = "sha256:" + sha256_hex(
            b"conjecture.turn.event.v1\x00"
            + canonical_json(self._identity_payload(values))
        )
        if self.decision_id != expected:
            raise ValueError("decision_id does not match the canonical event payload")
        return self


__all__ = [
    "ConjectureTurnAction",
    "ConjectureTurnEventPayloadV1",
]
