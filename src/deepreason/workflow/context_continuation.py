"""Immutable authority binding for RunManifest-v6 context continuations.

The model response is only a request.  This module records the deterministic
policy evaluation that turns that request into either a fresh conjecture work
preparation or a typed, unissued denial.  It deliberately carries no provider
authorization: a granted continuation must still reserve and issue its own
transaction.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.frozen import FrozenRecord


_WORK_ID = r"^sha256:[0-9a-f]{64}$"
_BLOB_REF = r"^[0-9a-f]{64}$"
_DIGEST = r"^[0-9a-f]{64}$"


class ContextContinuationEligibility(str, Enum):
    ELIGIBLE = "eligible"
    CHANNEL_NOT_PERMITTED = "channel_not_permitted"
    CAPABILITY_NOT_GRANTED = "capability_not_granted"
    REQUEST_LIMIT_REACHED = "request_limit_reached"


class ConjectureContextContinuationV1(FrozenRecord):
    """Code-authored binding from one admitted request to its child work."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_: Literal["conjecture.context-continuation.v1"] = Field(
        "conjecture.context-continuation.v1", alias="schema"
    )
    decision_ref: str = Field(pattern=_WORK_ID)
    manifest_digest: str = Field(pattern=_DIGEST)
    problem_id: str = Field(min_length=1, max_length=512)
    school_id: str | None = Field(
        default=None, pattern=r"^school-(0|[1-9][0-9]*)$"
    )
    parent_work_id: str = Field(pattern=_WORK_ID)
    parent_attempt_index: int = Field(ge=0, le=64)
    parent_provider_attempt_ref: str = Field(pattern=_WORK_ID)
    parent_exposure_receipt_ref: str = Field(pattern=_WORK_ID)
    parent_semantic_admission_ref: str = Field(pattern=_WORK_ID)
    parent_semantic_output_ref: str = Field(pattern=_BLOB_REF)
    parent_provider_event_seq: int = Field(ge=0)
    request_hash: str = Field(pattern=_WORK_ID)
    request_ref: str = Field(pattern=_BLOB_REF)
    expansion_index: int = Field(ge=1, le=9)
    maximum_expansions: int = Field(ge=0, le=8)
    maximum_extra_blocks: int = Field(ge=0, le=1_000)
    policy_mode: Literal[
        "disabled", "harness_only", "harness_plus_model_request"
    ]
    permitted_retrieval_channels: tuple[str, ...] = ()
    desired_retrieval_channels: tuple[str, ...] = ()
    prior_selection_receipt_ref: str | None = Field(
        default=None, pattern=_WORK_ID
    )
    prior_context_plan_sha256: str | None = Field(default=None, pattern=_DIGEST)
    eligibility: ContextContinuationEligibility

    @field_validator(
        "permitted_retrieval_channels",
        "desired_retrieval_channels",
        mode="after",
    )
    @classmethod
    def _channels_are_unique(cls, value: tuple[str, ...]):
        if len(value) != len(set(value)):
            raise ValueError("context continuation channels must be unique")
        return tuple(value)

    @staticmethod
    def evaluate(
        *,
        policy_mode: str,
        permitted_retrieval_channels: tuple[str, ...],
        desired_retrieval_channels: tuple[str, ...],
        expansion_index: int,
        maximum_expansions: int,
    ) -> ContextContinuationEligibility:
        if set(desired_retrieval_channels) - set(permitted_retrieval_channels):
            return ContextContinuationEligibility.CHANNEL_NOT_PERMITTED
        if policy_mode != "harness_plus_model_request":
            return ContextContinuationEligibility.CAPABILITY_NOT_GRANTED
        if expansion_index > maximum_expansions:
            return ContextContinuationEligibility.REQUEST_LIMIT_REACHED
        return ContextContinuationEligibility.ELIGIBLE

    @staticmethod
    def _identity_payload(values: dict) -> dict:
        return {
            key: value
            for key, value in values.items()
            if key not in {"schema", "schema_", "decision_ref"}
            and value is not None
        }

    @classmethod
    def create(cls, **values) -> "ConjectureContextContinuationV1":
        desired = tuple(values.get("desired_retrieval_channels", ()))
        permitted = tuple(values.get("permitted_retrieval_channels", ()))
        eligibility = cls.evaluate(
            policy_mode=str(values["policy_mode"]),
            permitted_retrieval_channels=permitted,
            desired_retrieval_channels=desired,
            expansion_index=int(values["expansion_index"]),
            maximum_expansions=int(values["maximum_expansions"]),
        )
        normalized = {
            **values,
            "permitted_retrieval_channels": permitted,
            "desired_retrieval_channels": desired,
            "eligibility": eligibility,
        }
        decision_ref = "sha256:" + sha256_hex(
            b"conjecture.context-continuation.v1\x00"
            + canonical_json(cls._identity_payload(normalized))
        )
        return cls(decision_ref=decision_ref, **normalized)

    @model_validator(mode="after")
    def _policy_decision_and_identity_match(self):
        if (self.prior_selection_receipt_ref is None) != (
            self.prior_context_plan_sha256 is None
        ):
            raise ValueError("prior context selection and plan digest must appear together")
        expected_eligibility = self.evaluate(
            policy_mode=self.policy_mode,
            permitted_retrieval_channels=self.permitted_retrieval_channels,
            desired_retrieval_channels=self.desired_retrieval_channels,
            expansion_index=self.expansion_index,
            maximum_expansions=self.maximum_expansions,
        )
        if self.eligibility != expected_eligibility:
            raise ValueError("context continuation eligibility differs from frozen policy")
        values = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        expected_ref = "sha256:" + sha256_hex(
            b"conjecture.context-continuation.v1\x00"
            + canonical_json(self._identity_payload(values))
        )
        if self.decision_ref != expected_ref:
            raise ValueError("context continuation decision_ref is not canonical")
        return self


def context_plan_sha256(plan) -> str | None:
    """Return the stable digest of a pure planned context, when one exists."""

    if plan is None:
        return None
    return sha256_hex(
        canonical_json(
            plan.model_dump(mode="json", by_alias=True, exclude_none=True)
        )
    )


__all__ = [
    "ConjectureContextContinuationV1",
    "ContextContinuationEligibility",
    "context_plan_sha256",
]
