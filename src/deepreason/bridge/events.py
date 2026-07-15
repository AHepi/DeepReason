"""Closed process-event vocabulary for grounded bridge operations."""

from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from deepreason.ontology.frozen import FrozenList, FrozenRecord
from deepreason.scratch.models import HashRef, OpaqueRef, ScratchActor


class BridgeAction(str, Enum):
    LEDGER_CREATED = "ledger_created"
    LEDGER_VALIDATED = "ledger_validated"
    LEDGER_AMENDMENT_REQUESTED = "ledger_amendment_requested"
    LEDGER_AMENDMENT_ATTEMPTED = "ledger_amendment_attempted"
    LEDGER_AMENDED = "ledger_amended"
    OUTPUT_COMPOSED = "output_composed"
    OUTPUT_VALIDATED = "output_validated"
    GROUNDED_REVIEW_ATTEMPTED = "grounded_review_attempted"
    GROUNDED_REVIEWED = "grounded_reviewed"
    REPAIR_ATTEMPTED = "repair_attempted"
    COMPLETED = "completed"
    FAILED = "failed"


class BridgeEventPayloadV1(FrozenRecord):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    schema_: Literal["bridge.event.payload.v1"] = Field(
        "bridge.event.payload.v1", alias="schema"
    )
    action: BridgeAction
    actor: ScratchActor
    inputs: list[HashRef] = Field(default_factory=FrozenList, max_length=2_048)
    outputs: list[HashRef] = Field(default_factory=FrozenList, max_length=2_048)
    finding_ref: HashRef | None = None
    error_code: OpaqueRef | None = None

    @field_validator("inputs", "outputs", mode="after")
    @classmethod
    def _freeze_sequences(cls, value):
        return FrozenList(value)
