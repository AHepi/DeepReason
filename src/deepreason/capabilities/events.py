"""Typed append-only capability event envelope."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.frozen import FrozenList, FrozenRecord

_ID = r"^sha256:[0-9a-f]{64}$"


class CapabilityEventPayloadV1(FrozenRecord):
    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True
    )

    schema_: Literal["capability.event.v1"] = Field(
        "capability.event.v1", alias="schema"
    )
    lifecycle: CapabilityLifecycle
    request_ref: str = Field(pattern=_ID)
    transition_ref: str = Field(pattern=_ID)
    inputs: list[str] = Field(default_factory=FrozenList, min_length=2, max_length=2)
    outputs: list[str] = Field(default_factory=FrozenList, min_length=1, max_length=3)

    @field_validator("inputs", "outputs", mode="after")
    @classmethod
    def _frozen_sequences(cls, value):
        return FrozenList(value)

    @model_validator(mode="after")
    def _canonical_references(self):
        if any(not item for item in self.inputs):
            raise ValueError("capability event inputs must be nonempty")
        if self.inputs[1] != self.request_ref:
            raise ValueError("capability event input one must name its proposal")
        if any(not item.startswith("sha256:") for item in self.outputs):
            raise ValueError("capability outputs must be canonical record IDs")
        if len(self.outputs) != len(set(self.outputs)):
            raise ValueError("capability outputs must not repeat")
        if self.outputs[-1] != self.transition_ref:
            raise ValueError("capability transition must be the final event output")
        return self


__all__ = ["CapabilityEventPayloadV1"]
