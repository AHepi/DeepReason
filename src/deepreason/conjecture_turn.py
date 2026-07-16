"""Open-semantic v4 conjecture outcomes under a bounded authority shell."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.capabilities.models import SimulationProposalDraftV1
from deepreason.llm.contracts import ConjectureCandidate
from deepreason.run_manifest import ConjectureContextPolicyV1, ScratchPolicy
from deepreason.scratch.models import RetrievalChannel
from deepreason.workloads.text import ReasoningCandidateProposal


class _TurnRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ContextRequestV1(_TurnRecord):
    """Canonical semantic retrieval proposal; never executable authority."""

    query: str | None = Field(default=None, min_length=1, max_length=8_192)
    requested_refs: tuple[str, ...] = Field(default=(), max_length=64)
    desired_retrieval_channels: tuple[RetrievalChannel, ...] = Field(
        default=(), max_length=len(RetrievalChannel)
    )
    purpose: str | None = Field(default=None, min_length=1, max_length=4_096)

    @model_validator(mode="after")
    def _has_semantic_selector(self):
        if not (
            self.query
            or self.requested_refs
            or self.desired_retrieval_channels
        ):
            raise ValueError(
                "context request requires a query, visible reference, or channel"
            )
        return self

    @field_validator("requested_refs", "desired_retrieval_channels", mode="after")
    @classmethod
    def _ordered_unique(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("context request values must not contain duplicates")
        if (
            value
            and isinstance(value[0], RetrievalChannel)
            and RetrievalChannel.DIRECT_OPEN in value
        ):
            raise ValueError("direct_open is not a model-requestable retrieval channel")
        return tuple(value)

    @property
    def request_hash(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        return "sha256:" + sha256_hex(
            b"conjecture.context.request.v1\x00" + canonical_json(payload)
        )


class ConjectureAbstentionV1(_TurnRecord):
    """A responsible no-proposal signal using the existing search vocabulary."""

    search_signal: Literal[
        "need_context",
        "stuck",
        "capability_mismatch",
    ] = "stuck"
    note: str | None = Field(default=None, min_length=1, max_length=8_192)

    @property
    def abstention_hash(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        return "sha256:" + sha256_hex(
            b"conjecture.abstention.v1\x00" + canonical_json(payload)
        )


class ConjecturerTurnV4(_TurnRecord):
    """General conjecturer result: proposal, context request, or abstention."""

    candidates: tuple[ConjectureCandidate, ...] = Field(default=(), max_length=256)
    context_request: ContextRequestV1 | None = None
    abstention: ConjectureAbstentionV1 | None = None

    @model_validator(mode="after")
    def _meaningful_outcome(self):
        if not (self.candidates or self.context_request or self.abstention):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and self.candidates:
            raise ValueError("abstention cannot accompany candidate proposals")
        return self


class ReasoningConjecturerTurnV4(_TurnRecord):
    """Reasoning-workload v4 result with the same process escape outcomes."""

    candidates: tuple[ReasoningCandidateProposal, ...] = Field(
        default=(), max_length=256
    )
    context_request: ContextRequestV1 | None = None
    abstention: ConjectureAbstentionV1 | None = None

    @model_validator(mode="after")
    def _meaningful_outcome(self):
        if not (self.candidates or self.context_request or self.abstention):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and self.candidates:
            raise ValueError("abstention cannot accompany candidate proposals")
        return self


class ConjecturerTurnV5(_TurnRecord):
    """Tranche-A turn: ordinary outcomes plus semantic simulation proposals."""

    candidates: tuple[ConjectureCandidate, ...] = Field(default=(), max_length=256)
    context_request: ContextRequestV1 | None = None
    abstention: ConjectureAbstentionV1 | None = None
    simulation_proposals: tuple[SimulationProposalDraftV1, ...] = Field(
        default=(), max_length=32
    )

    @model_validator(mode="after")
    def _meaningful_outcome(self):
        if not (
            self.candidates
            or self.context_request
            or self.abstention
            or self.simulation_proposals
        ):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and (
            self.candidates or self.simulation_proposals
        ):
            raise ValueError("abstention cannot accompany semantic proposals")
        return self


class ReasoningConjecturerTurnV5(_TurnRecord):
    candidates: tuple[ReasoningCandidateProposal, ...] = Field(
        default=(), max_length=256
    )
    context_request: ContextRequestV1 | None = None
    abstention: ConjectureAbstentionV1 | None = None
    simulation_proposals: tuple[SimulationProposalDraftV1, ...] = Field(
        default=(), max_length=32
    )

    @model_validator(mode="after")
    def _meaningful_outcome(self):
        if not (
            self.candidates
            or self.context_request
            or self.abstention
            or self.simulation_proposals
        ):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and (
            self.candidates or self.simulation_proposals
        ):
            raise ValueError("abstention cannot accompany semantic proposals")
        return self


class ConjectureTurnAuthorityV1(_TurnRecord):
    """Manifest-derived capability passed to Conj; contains no route choice."""

    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    scratch_policy: ScratchPolicy
    context_policy: ConjectureContextPolicyV1


ConjectureNoProposalV1 = ConjectureAbstentionV1


__all__ = [
    "ConjectureAbstentionV1",
    "ConjectureTurnAuthorityV1",
    "ConjectureNoProposalV1",
    "ConjecturerTurnV4",
    "ConjecturerTurnV5",
    "ContextRequestV1",
    "ReasoningConjecturerTurnV4",
    "ReasoningConjecturerTurnV5",
]
