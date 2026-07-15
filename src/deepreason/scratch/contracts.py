"""Compact model-facing contracts for advisory scratch authoring.

These values are transport objects, not canonical scratch instances.  Models
cannot author IDs, provenance, snapshots, routing, or workflow state here.
Harness-owned compilers resolve call-local handles/indices before canonical
objects are constructed by the scratch service.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.llm.wire import AliasTable, WireContract
from deepreason.ontology.frozen import FrozenList, FrozenRecord
from deepreason.scratch.models import HashRef, ScratchBlockBodyV1, ScratchLinkBodyV1


MAX_LOCAL_INDEX = 4_095
MAX_LOCAL_HANDLE_LENGTH = 64
MAX_GUIDE_OPEN_THREADS = 64
MAX_GUIDE_ENTRY_POINTS = 64
MAX_SHORT_TEXT = 16_384
MAX_LONG_TEXT = 262_144

_CANONICAL_HASH = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$")
_LOCAL_HANDLE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,63}$")


SCRATCH_CONTRACT_INSTRUCTIONS = """Scratch material is non-authoritative.
It may contradict itself.
Do not turn uncertainty into a confident fact.
Do not invent a reason merely to fill an optional field.
Relationships are provisional.
A guide is a temporary navigation aid."""


class ScratchWireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


def _nonblank(value: str | None) -> str | None:
    if value is not None and not value.strip():
        raise ValueError("text must contain a non-whitespace character")
    return value


def _local_handle(value: str) -> str:
    if _CANONICAL_HASH.fullmatch(value):
        raise ValueError("canonical IDs are forbidden; use a provided local handle")
    if _LOCAL_HANDLE.fullmatch(value) is None:
        raise ValueError(
            "local handle must begin with a letter and contain at most 64 "
            "letters, digits, '.', '_', ':', or '-'"
        )
    return value


WireText = Annotated[str, Field(min_length=1, max_length=MAX_LONG_TEXT)]
WireShortText = Annotated[str, Field(min_length=1, max_length=MAX_SHORT_TEXT)]
LocalHandle = Annotated[str, Field(min_length=1, max_length=MAX_LOCAL_HANDLE_LENGTH)]
LocalIndex = Annotated[int, Field(ge=0, le=MAX_LOCAL_INDEX)]


class ScratchBlockWireV1(ScratchWireModel):
    """One loose thought; only ``content`` is required."""

    content: WireText
    why_keep_this: WireText | None = None
    unfinished: WireText | None = None
    possible_next_move: WireText | None = None

    @field_validator("content", "why_keep_this", "unfinished", "possible_next_move")
    @classmethod
    def _nonblank_text(cls, value):
        return _nonblank(value)


class ScratchLinkWireV1(ScratchWireModel):
    """A provisional relation using only call-local endpoint references.

    Indices are zero-based positions in the rendered block list.  A caller
    may instead provide opaque handles.  Exactly one representation is legal
    for each endpoint.
    """

    from_index: LocalIndex | None = None
    from_handle: LocalHandle | None = None
    to_index: LocalIndex | None = None
    to_handle: LocalHandle | None = None
    relation_hint: WireShortText
    because: WireText | None = None
    holds_when: WireText | None = None
    weakens_when: WireText | None = None
    direction: Literal["directed", "symmetric"] | None = None

    @field_validator("from_handle", "to_handle", mode="before")
    @classmethod
    def _handles_are_local(cls, value):
        return None if value is None else _local_handle(value)

    @field_validator("relation_hint", "because", "holds_when", "weakens_when")
    @classmethod
    def _nonblank_text(cls, value):
        return _nonblank(value)

    @model_validator(mode="after")
    def _one_reference_per_endpoint(self):
        if (self.from_index is None) == (self.from_handle is None):
            raise ValueError("provide exactly one of from_index or from_handle")
        if (self.to_index is None) == (self.to_handle is None):
            raise ValueError("provide exactly one of to_index or to_handle")
        return self


class ClusterGuideWireV1(ScratchWireModel):
    """Temporary navigation prose; no cluster/snapshot IDs are model-authored."""

    working_focus: WireText
    open_threads: list[WireShortText] | None = Field(
        default=None, max_length=MAX_GUIDE_OPEN_THREADS
    )
    entry_points: list[LocalHandle] | None = Field(
        default=None, max_length=MAX_GUIDE_ENTRY_POINTS
    )
    local_summary: WireText | None = None

    @field_validator("working_focus", "local_summary")
    @classmethod
    def _nonblank_text(cls, value):
        return _nonblank(value)

    @field_validator("open_threads")
    @classmethod
    def _threads_are_nonblank(cls, value):
        if value is not None:
            for item in value:
                _nonblank(item)
        return value

    @field_validator("entry_points", mode="before")
    @classmethod
    def _entry_handles_are_local_and_unique(cls, value):
        if value is None:
            return value
        for item in value:
            _local_handle(item)
        if len(value) != len(set(value)):
            raise ValueError("entry-point handles must not contain duplicates")
        return value


class ClusterGuideDraftV1(FrozenRecord):
    """Harness-side guide content after local handles are resolved."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    working_focus: str
    open_threads: list[str] | None = None
    entry_points: list[HashRef] | None = None
    local_summary: str | None = None

    @field_validator("open_threads", "entry_points", mode="after")
    @classmethod
    def _freeze_sequences(cls, value):
        return None if value is None else FrozenList(value)


class ScratchWireReferenceError(ValueError):
    def __init__(self, message: str, pointer: str) -> None:
        self.code = "SCRATCH_WIRE_REFERENCE_INVALID"
        self.pointer = pointer
        super().__init__(f"{self.code} at {pointer}: {message}")


class ScratchBlockWireContract(WireContract[ScratchBlockBodyV1]):
    def __init__(self) -> None:
        super().__init__(
            "scratch.block.compact.v1",
            ScratchBlockWireV1,
            ScratchBlockBodyV1,
            variant="compact",
        )

    def compile(self, wire: ScratchBlockWireV1) -> ScratchBlockBodyV1:
        return ScratchBlockBodyV1.model_validate(wire.model_dump(exclude_none=True))


class _ReferenceCompiler:
    def __init__(
        self,
        *,
        indexed_block_ids: Sequence[str] = (),
        handles: Mapping[str, str] | AliasTable | None = None,
    ) -> None:
        self.indexed_block_ids = tuple(indexed_block_ids)
        if isinstance(handles, AliasTable):
            self.handles = handles
        else:
            self.handles = AliasTable(dict(handles or {}))

    def _resolve(
        self,
        *,
        index: int | None,
        handle: str | None,
        pointer: str,
    ) -> str:
        if index is not None:
            try:
                return self.indexed_block_ids[index]
            except IndexError as error:
                raise ScratchWireReferenceError(
                    f"index {index} is outside the rendered block list", pointer
                ) from error
        assert handle is not None  # enforced by the wire model
        try:
            return self.handles.resolve(handle)
        except ValueError as error:
            raise ScratchWireReferenceError(str(error), pointer) from error


class ScratchLinkWireContract(_ReferenceCompiler, WireContract[ScratchLinkBodyV1]):
    def __init__(
        self,
        *,
        indexed_block_ids: Sequence[str] = (),
        handles: Mapping[str, str] | AliasTable | None = None,
    ) -> None:
        _ReferenceCompiler.__init__(
            self, indexed_block_ids=indexed_block_ids, handles=handles
        )
        WireContract.__init__(
            self,
            "scratch.link.compact.v1",
            ScratchLinkWireV1,
            ScratchLinkBodyV1,
            aliases=self.handles,
            variant="compact",
        )

    def compile(self, wire: ScratchLinkWireV1) -> ScratchLinkBodyV1:
        from_id = self._resolve(
            index=wire.from_index,
            handle=wire.from_handle,
            pointer="/from_index" if wire.from_index is not None else "/from_handle",
        )
        to_id = self._resolve(
            index=wire.to_index,
            handle=wire.to_handle,
            pointer="/to_index" if wire.to_index is not None else "/to_handle",
        )
        return ScratchLinkBodyV1(
            from_=from_id,
            to=to_id,
            relation_hint=wire.relation_hint,
            because=wire.because,
            holds_when=wire.holds_when,
            weakens_when=wire.weakens_when,
            direction=wire.direction,
        )


class ClusterGuideWireContract(_ReferenceCompiler, WireContract[ClusterGuideDraftV1]):
    def __init__(self, *, handles: Mapping[str, str] | AliasTable) -> None:
        _ReferenceCompiler.__init__(self, handles=handles)
        WireContract.__init__(
            self,
            "scratch.cluster-guide.compact.v1",
            ClusterGuideWireV1,
            ClusterGuideDraftV1,
            aliases=self.handles,
            variant="compact",
        )

    def compile(self, wire: ClusterGuideWireV1) -> ClusterGuideDraftV1:
        entries = (
            [
                self._resolve(index=None, handle=handle, pointer=f"/entry_points/{index}")
                for index, handle in enumerate(wire.entry_points)
            ]
            if wire.entry_points is not None
            else None
        )
        return ClusterGuideDraftV1(
            working_focus=wire.working_focus,
            open_threads=wire.open_threads,
            entry_points=entries,
            local_summary=wire.local_summary,
        )


# Explicit compact aliases make intent clear at call sites without creating a
# second protocol or model-profile fork.
CompactScratchBlockV1 = ScratchBlockWireV1
CompactScratchLinkV1 = ScratchLinkWireV1
CompactClusterGuideV1 = ClusterGuideWireV1


__all__ = [
    "ClusterGuideDraftV1",
    "ClusterGuideWireContract",
    "ClusterGuideWireV1",
    "CompactClusterGuideV1",
    "CompactScratchBlockV1",
    "CompactScratchLinkV1",
    "LocalHandle",
    "LocalIndex",
    "MAX_GUIDE_ENTRY_POINTS",
    "MAX_GUIDE_OPEN_THREADS",
    "MAX_LOCAL_HANDLE_LENGTH",
    "MAX_LOCAL_INDEX",
    "SCRATCH_CONTRACT_INSTRUCTIONS",
    "ScratchBlockWireContract",
    "ScratchBlockWireV1",
    "ScratchLinkWireContract",
    "ScratchLinkWireV1",
    "ScratchWireReferenceError",
]
