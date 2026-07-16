"""Typed append-only events for workflow authority decisions.

The payload carries immutable references only.  The full work order,
proposal/guard receipts, and transition decision live in the canonical object
store; replay resolves those records instead of duplicating them here.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from deepreason.frozen import FrozenList, FrozenRecord


_WORKFLOW_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


class ControlEventPayloadV1(FrozenRecord):
    """References for one code-authored workflow transition.

    ``inputs`` and ``outputs`` deliberately mirror the enclosing
    :class:`deepreason.ontology.event.Event`.  Keeping the decision reference
    last gives readers one canonical location without requiring Event schema
    validation to open the object store.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )

    schema_: Literal["control.event.v1"] = Field(
        "control.event.v1", alias="schema"
    )
    decision_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    inputs: list[str] = Field(default_factory=FrozenList, max_length=2)
    outputs: list[str] = Field(default_factory=FrozenList, min_length=1, max_length=4)

    @field_validator("inputs", "outputs", mode="after")
    @classmethod
    def _freeze_sequences(cls, value):
        return FrozenList(value)

    @model_validator(mode="after")
    def _authority_references(self):
        if len(self.inputs) != 2:
            raise ValueError(
                "control inputs must name exactly one work order and trigger"
            )
        if _WORKFLOW_ID.fullmatch(self.inputs[0]) is None:
            raise ValueError(
                "control input zero must name a canonical work order "
                "or lifecycle workflow record"
            )
        if not self.inputs[1] or len(self.inputs[1]) > 512:
            raise ValueError("control trigger reference must be nonempty and bounded")
        if any(_WORKFLOW_ID.fullmatch(item) is None for item in self.outputs):
            raise ValueError("control outputs must be canonical workflow IDs")
        if len(self.outputs) != len(set(self.outputs)):
            raise ValueError("control outputs must not contain duplicate object IDs")
        if self.outputs[-1] != self.decision_ref:
            raise ValueError("control decision_ref must be the final event output")
        return self


class ControlEventPayloadV2(FrozenRecord):
    """Reference-only event envelope for workflow.controller.v2 decisions."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )

    schema_: Literal["control.event.v2"] = Field(
        "control.event.v2", alias="schema"
    )
    decision_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    inputs: list[str] = Field(default_factory=FrozenList, max_length=2)
    outputs: list[str] = Field(default_factory=FrozenList, min_length=1, max_length=4)

    @field_validator("inputs", "outputs", mode="after")
    @classmethod
    def _freeze_sequences(cls, value):
        return FrozenList(value)

    @model_validator(mode="after")
    def _authority_references(self):
        if len(self.inputs) != 2:
            raise ValueError("control inputs must name one work order and trigger")
        if _WORKFLOW_ID.fullmatch(self.inputs[0]) is None:
            raise ValueError("control input zero must be one canonical workflow ID")
        if not self.inputs[1] or len(self.inputs[1]) > 512:
            raise ValueError("control trigger reference must be nonempty and bounded")
        if any(_WORKFLOW_ID.fullmatch(item) is None for item in self.outputs):
            raise ValueError("control outputs must be canonical workflow IDs")
        if len(self.outputs) != len(set(self.outputs)):
            raise ValueError("control outputs must not contain duplicate IDs")
        if self.outputs[-1] != self.decision_ref:
            raise ValueError("control decision_ref must be the final event output")
        return self


__all__ = ["ControlEventPayloadV1", "ControlEventPayloadV2"]
