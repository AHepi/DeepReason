"""Wire-independent v6 model drafts for advisory scratch authoring."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json

SCRATCH_AUTHORING_PURPOSE = "imaginative_workshop"
SCRATCH_EPISTEMIC_BOUNDARY = "advisory_non_grounding"
V6_SCRATCH_WORKSHOP_PROMPT = (
    "IMAGINATIVE SCRATCH WORKSHOP (optional): speculative mechanisms, "
    "counterfactuals, contradictions, rough fragments, and unresolved questions "
    "are explicitly welcome. Explore boldly. Scratch remains advisory: storage "
    "alone never makes it a fact, evidence, a formal claim, or support for one."
)
V6_SCRATCH_WORKSHOP_SCHEMA_DESCRIPTION = (
    "Optional imaginative workshop: speculative mechanisms, counterfactuals, "
    "contradictions, rough fragments, and unresolved questions are welcome. "
    "Scratch remains advisory; storage alone never makes it fact, evidence, "
    "a formal claim, or formal support."
)


class ScratchProposalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ScratchBlockDraftBodyV1(ScratchProposalModel):
    content: str = Field(min_length=1, max_length=262_144)
    why_keep_this: str | None = Field(default=None, min_length=1, max_length=262_144)
    unfinished: str | None = Field(default=None, min_length=1, max_length=262_144)
    possible_next_move: str | None = Field(default=None, min_length=1, max_length=262_144)


class ScratchNewBlockDraftV1(ScratchProposalModel):
    local_key: str = Field(pattern=r"^NEW_[0-9]{3,}$")
    body: ScratchBlockDraftBodyV1


class ScratchRevisionDraftV1(ScratchProposalModel):
    target_alias: str = Field(pattern=r"^SCR_[0-9]{3,}$")
    body: ScratchBlockDraftBodyV1


class ScratchProposalLinkV1(ScratchProposalModel):
    from_ref: str = Field(pattern=r"^(?:SCR|NEW)_[0-9]{3,}$")
    to_ref: str = Field(pattern=r"^(?:SCR|NEW)_[0-9]{3,}$")
    relation_hint: str = Field(min_length=1, max_length=16_384)
    because: str | None = Field(default=None, min_length=1, max_length=262_144)
    holds_when: str | None = Field(default=None, min_length=1, max_length=262_144)
    weakens_when: str | None = Field(default=None, min_length=1, max_length=262_144)
    direction: Literal["directed", "symmetric"] | None = None

    @model_validator(mode="after")
    def _not_a_self_link(self):
        if self.from_ref == self.to_ref:
            raise ValueError("scratch proposal links must connect distinct blocks")
        return self


class ScratchQuestionDraftV1(ScratchProposalModel):
    question: str = Field(min_length=1, max_length=262_144)
    related_refs: tuple[str, ...] = Field(default=(), max_length=64)

    @field_validator("related_refs")
    @classmethod
    def _local_refs(cls, value):
        if any(re.fullmatch(r"^(?:SCR|NEW)_[0-9]{3,}$", item) is None for item in value):
            raise ValueError("unresolved questions may use only visible/local scratch refs")
        if len(value) != len(set(value)):
            raise ValueError("related scratch references must be unique")
        return tuple(value)


class ScratchClusterSuggestionV1(ScratchProposalModel):
    seed_focus: str = Field(min_length=1, max_length=262_144)
    member_refs: tuple[str, ...] = Field(min_length=1, max_length=64)

    @field_validator("member_refs")
    @classmethod
    def _members_are_local(cls, value):
        if any(re.fullmatch(r"^(?:SCR|NEW)_[0-9]{3,}$", item) is None for item in value):
            raise ValueError("cluster suggestions may use only visible/local scratch refs")
        if len(value) != len(set(value)):
            raise ValueError("cluster suggestion members must be unique")
        return tuple(value)


class ScratchProposalV1(ScratchProposalModel):
    """Model-authored drafts only; no IDs, provenance, snapshots, or status."""

    new_blocks: tuple[ScratchNewBlockDraftV1, ...] = Field(default=(), max_length=32)
    revisions: tuple[ScratchRevisionDraftV1, ...] = Field(default=(), max_length=32)
    links: tuple[ScratchProposalLinkV1, ...] = Field(default=(), max_length=64)
    unresolved_questions: tuple[ScratchQuestionDraftV1, ...] = Field(
        default=(), max_length=32
    )
    cluster_suggestions: tuple[ScratchClusterSuggestionV1, ...] = Field(
        default=(), max_length=32
    )

    @model_validator(mode="after")
    def _local_namespace_is_closed(self):
        local_keys = tuple(item.local_key for item in self.new_blocks)
        if len(local_keys) != len(set(local_keys)):
            raise ValueError("new scratch local keys must be unique")
        allowed_new = set(local_keys)
        referenced_new = {
            ref
            for link in self.links
            for ref in (link.from_ref, link.to_ref)
            if ref.startswith("NEW_")
        }
        referenced_new.update(
            ref
            for question in self.unresolved_questions
            for ref in question.related_refs
            if ref.startswith("NEW_")
        )
        referenced_new.update(
            ref
            for cluster in self.cluster_suggestions
            for ref in cluster.member_refs
            if ref.startswith("NEW_")
        )
        if not referenced_new <= allowed_new:
            raise ValueError("scratch proposal references an unknown new-block key")
        return self

    @property
    def encoded_bytes(self) -> int:
        return len(canonical_json(self.model_dump(mode="json")))


__all__ = [
    "SCRATCH_AUTHORING_PURPOSE",
    "SCRATCH_EPISTEMIC_BOUNDARY",
    "V6_SCRATCH_WORKSHOP_PROMPT",
    "V6_SCRATCH_WORKSHOP_SCHEMA_DESCRIPTION",
    "ScratchBlockDraftBodyV1",
    "ScratchClusterSuggestionV1",
    "ScratchNewBlockDraftV1",
    "ScratchProposalLinkV1",
    "ScratchProposalV1",
    "ScratchQuestionDraftV1",
    "ScratchRevisionDraftV1",
]
