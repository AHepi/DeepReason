"""Typed append-only process events for the advisory scratchpad."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from deepreason.ontology.frozen import FrozenList
from deepreason.scratch.models import HashRef, OpaqueRef, ScratchActor, ScratchRecord


class ScratchAction(str, Enum):
    BLOCK_CREATED = "block_created"
    BLOCK_REVISED = "block_revised"
    LINK_CREATED = "link_created"
    LINK_USED = "link_used"
    LINK_RETIRED = "link_retired"
    CLUSTER_CREATED = "cluster_created"
    CLUSTER_MEMBER_ADDED = "cluster_member_added"
    CLUSTER_MEMBER_REMOVED = "cluster_member_removed"
    CLUSTER_GUIDE_WRITTEN = "cluster_guide_written"
    SIMILARITY_RECORDED = "similarity_recorded"
    ATTENTION_PACK_RENDERED = "attention_pack_rendered"
    COVERAGE_CYCLE_STARTED = "coverage_cycle_started"
    COVERAGE_BLOCK_RENDERED = "coverage_block_rendered"
    COVERAGE_CYCLE_COMPLETED = "coverage_cycle_completed"


_INTERPRETIVE_ACTIONS = {
    ScratchAction.BLOCK_CREATED,
    ScratchAction.BLOCK_REVISED,
    ScratchAction.LINK_CREATED,
    ScratchAction.LINK_RETIRED,
    ScratchAction.CLUSTER_CREATED,
    ScratchAction.CLUSTER_MEMBER_ADDED,
    ScratchAction.CLUSTER_MEMBER_REMOVED,
    ScratchAction.CLUSTER_GUIDE_WRITTEN,
}


class ScratchEventPayloadV1(ScratchRecord):
    """Process-only scratch mutation details.

    Inputs and outputs mirror the enclosing canonical Event.  Keeping the
    typed action here prevents arbitrary caller-authored rule strings while
    leaving LLM accounting solely on ``Event.llm``.
    """

    schema_: Literal["scratch.event.payload.v1"] = Field(
        "scratch.event.payload.v1", alias="schema"
    )
    action: ScratchAction
    actor: ScratchActor
    inputs: list[HashRef] = Field(default_factory=FrozenList, max_length=2_048)
    outputs: list[HashRef] = Field(default_factory=FrozenList, max_length=2_048)
    reason_ref: OpaqueRef | None = None
    retrieval_receipt_ref: HashRef | None = None
    context_ref: OpaqueRef | None = None

    @field_validator("inputs", "outputs", mode="after")
    @classmethod
    def _freeze_sequences(cls, value):
        return FrozenList(value)

    @model_validator(mode="after")
    def _action_contract(self):
        if self.actor == ScratchActor.HARNESS and self.action in _INTERPRETIVE_ACTIONS:
            raise ValueError(
                f"the harness cannot author interpretive scratch action {self.action.value}"
            )
        if self.action == ScratchAction.LINK_RETIRED and self.reason_ref is None:
            raise ValueError("link retirement requires an immutable reason_ref")
        if self.action == ScratchAction.LINK_USED and self.context_ref is None:
            raise ValueError("link use requires an immutable context_ref")
        required_input_counts = {
            ScratchAction.BLOCK_CREATED: 0,
            ScratchAction.BLOCK_REVISED: 1,
            ScratchAction.LINK_CREATED: 0,
            ScratchAction.LINK_USED: 1,
            ScratchAction.LINK_RETIRED: 1,
            ScratchAction.CLUSTER_CREATED: 0,
            ScratchAction.CLUSTER_MEMBER_ADDED: 2,
            ScratchAction.CLUSTER_MEMBER_REMOVED: 2,
            ScratchAction.CLUSTER_GUIDE_WRITTEN: 1,
            ScratchAction.SIMILARITY_RECORDED: 0,
            ScratchAction.ATTENTION_PACK_RENDERED: 0,
            ScratchAction.COVERAGE_CYCLE_STARTED: 0,
            ScratchAction.COVERAGE_BLOCK_RENDERED: 2,
            ScratchAction.COVERAGE_CYCLE_COMPLETED: 1,
        }
        expected_inputs = required_input_counts[self.action]
        if len(self.inputs) != expected_inputs:
            raise ValueError(
                f"{self.action.value} requires {expected_inputs} input reference(s)"
            )
        if self.action == ScratchAction.ATTENTION_PACK_RENDERED:
            if len(self.outputs) != 1 or self.retrieval_receipt_ref != self.outputs[0]:
                raise ValueError(
                    "attention rendering must output and reference exactly one receipt"
                )
        return self
