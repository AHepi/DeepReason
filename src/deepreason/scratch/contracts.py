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

from deepreason.llm.wire import AliasTable, WireContract, exclusive_fields_schema
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
It is advisory, not a harness verdict.
It may contradict itself.
It may be wrong, stale, contradictory, incomplete, duplicated, or abandoned.
It does not ground a formal claim or supply evidence for one.
Ignore any block that is irrelevant to the current problem.
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


def _require_one_reference_per_endpoint(link) -> None:
    """Report every violated endpoint in one message, not just the first.

    Both endpoints can be wrong in one response (observed live: a model
    emitting every reference field null).  The repair loop grants one
    field patch per turn under a two-repair budget, so a diagnostic that
    names only the first violated endpoint leaves the model unable to
    plan the second patch and the case exhausts.  Naming every violation
    once makes the two-patch chain convergent.
    """

    problems = []
    if (link.from_index is None) == (link.from_handle is None):
        problems.append(
            "set exactly one of from_index or from_handle and leave the "
            "other null"
        )
    if (link.to_index is None) == (link.to_handle is None):
        problems.append(
            "set exactly one of to_index or to_handle and leave the "
            "other null"
        )
    if problems:
        raise ValueError(
            "link endpoint references are invalid: " + "; ".join(problems)
        )


class ScratchBlockMinimalWireV1(ScratchWireModel):
    """Smallest separately qualified scratch block: one advisory thought."""

    content: WireText

    @field_validator("content")
    @classmethod
    def _content_is_nonblank(cls, value):
        return _nonblank(value)


class ScratchLinkWireV1(ScratchWireModel):
    """A provisional relation using only call-local endpoint references.

    Indices are zero-based positions in the rendered block list.  A caller
    may instead provide opaque handles.  Exactly one representation is legal
    for each endpoint, and the schema enforces that: send from_index OR
    from_handle, and to_index OR to_handle, omitting the unused field.
    """

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        # One rule, one mechanism: the same encoder every other contract
        # uses. Two groups because the endpoints are independent.
        json_schema_extra=exclusive_fields_schema(
            ("from_index", "from_handle"), ("to_index", "to_handle")
        ),
    )

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
        _require_one_reference_per_endpoint(self)
        return self


class ScratchLinkMinimalWireV1(ScratchWireModel):
    """Smallest separately qualified provisional relation.

    Same per-endpoint reference rule as the compact form, enforced by the
    schema: from_index OR from_handle, to_index OR to_handle.
    """

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        # One rule, one mechanism: the same encoder every other contract
        # uses. Two groups because the endpoints are independent.
        json_schema_extra=exclusive_fields_schema(
            ("from_index", "from_handle"), ("to_index", "to_handle")
        ),
    )

    from_index: LocalIndex | None = None
    from_handle: LocalHandle | None = None
    to_index: LocalIndex | None = None
    to_handle: LocalHandle | None = None
    relation_hint: WireShortText

    @field_validator("from_handle", "to_handle", mode="before")
    @classmethod
    def _handles_are_local(cls, value):
        return None if value is None else _local_handle(value)

    @field_validator("relation_hint")
    @classmethod
    def _relation_is_nonblank(cls, value):
        return _nonblank(value)

    @model_validator(mode="after")
    def _one_reference_per_endpoint(self):
        _require_one_reference_per_endpoint(self)
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


class ClusterGuideMinimalWireV1(ScratchWireModel):
    """Smallest separately qualified navigation guide."""

    working_focus: WireText

    @field_validator("working_focus")
    @classmethod
    def _focus_is_nonblank(cls, value):
        return _nonblank(value)

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
    def __init__(
        self,
        message: str,
        pointer: str,
        *,
        rejected_handle: str | None = None,
        observed_kind: str | None = None,
        required_kinds: Sequence[str] = (),
        legal_handles: Sequence[str] = (),
        omission_allowed: bool | None = None,
    ) -> None:
        self.code = "SCRATCH_WIRE_REFERENCE_INVALID"
        self.pointer = pointer
        self.rejected_handle = rejected_handle
        self.observed_kind = observed_kind
        self.required_kinds = tuple(required_kinds)
        self.legal_handles = tuple(legal_handles[:32])
        self.omission_allowed = omission_allowed
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


class ScratchBlockMinimalWireContract(WireContract[ScratchBlockBodyV1]):
    def __init__(self) -> None:
        super().__init__(
            "scratch.block.minimal.v1",
            ScratchBlockMinimalWireV1,
            ScratchBlockBodyV1,
            variant="minimal",
        )

    def compile(self, wire: ScratchBlockMinimalWireV1) -> ScratchBlockBodyV1:
        return ScratchBlockBodyV1(content=wire.content)


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

    _HANDLE_FIELDS: tuple[str, ...] = ()

    def _bind_legal_handles(self, schema: dict) -> dict:
        """Name the legal call-local handles IN the schema, not only in prose.

        The contract already knows which handles exist — it is constructed
        with the alias table and rejects anything outside it — but the
        rendered schema said only ``{"type": "string"}``. A model reading the
        schema as its source of structural truth has no way to know which
        strings are legal, and invents one. Measured on gpt-oss:20b with
        thinking off: ``scratch.link.compact.v1`` reached 20/20 eventual
        validity and still failed the release gate on 2 alias failures, and
        ``scratch.cluster-guide.compact.v1`` failed with 4.

        The v6 conjecturer already does this for its alias arrays
        (``_bind_alias_array``); this applies the same rule to the scratch
        contracts' handle fields, scalar and array alike.

        With no handles bound there is nothing legal to name, so the field is
        left alone rather than given an empty ``enum`` that nothing could
        satisfy; the endpoint exclusion then admits only the index form.
        """

        legal = sorted(self.handles.aliases)
        if not legal:
            return schema
        properties = schema.get("properties", {})
        for name in self._HANDLE_FIELDS:
            field = properties.get(name)
            if not isinstance(field, dict):
                continue
            if field.get("type") == "array" or "items" in field:
                field["items"] = {"enum": list(legal), "type": "string"}
                continue
            branches = [
                option
                for option in field.get("anyOf", ())
                if isinstance(option, dict) and option.get("type") == "array"
            ]
            if branches:
                for option in branches:
                    option["items"] = {"enum": list(legal), "type": "string"}
                continue
            field.pop("anyOf", None)
            field.pop("maxLength", None)
            field.pop("minLength", None)
            field.update({"enum": list(legal), "type": "string"})
        return schema

    def model_json_schema(self) -> dict:
        return self._bind_legal_handles(super().model_json_schema())

    def _resolve(
        self,
        *,
        index: int | None,
        handle: str | None,
        pointer: str,
    ) -> str:
        # Entry-point handles live in an optional array a repair may simply
        # drop; link endpoints are required within their entry.
        omission_allowed = pointer.startswith("/entry_points/")
        legal = tuple(self.handles.aliases)
        if index is not None:
            try:
                return self.indexed_block_ids[index]
            except IndexError as error:
                raise ScratchWireReferenceError(
                    f"index {index} is outside the rendered block list",
                    pointer,
                    observed_kind="rendered_list_index",
                    required_kinds=("rendered_list_index", "local_handle"),
                    legal_handles=legal,
                    omission_allowed=omission_allowed,
                ) from error
        assert handle is not None  # enforced by the wire model
        try:
            return self.handles.resolve(handle)
        except ValueError as error:
            raise ScratchWireReferenceError(
                str(error),
                pointer,
                rejected_handle=handle,
                observed_kind="unknown",
                required_kinds=("local_handle",),
                legal_handles=legal,
                omission_allowed=omission_allowed,
            ) from error


class ScratchLinkWireContract(_ReferenceCompiler, WireContract[ScratchLinkBodyV1]):
    _HANDLE_FIELDS = ("from_handle", "to_handle")

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


class ScratchLinkMinimalWireContract(
    _ReferenceCompiler, WireContract[ScratchLinkBodyV1]
):
    _HANDLE_FIELDS = ("from_handle", "to_handle")

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
            "scratch.link.minimal.v1",
            ScratchLinkMinimalWireV1,
            ScratchLinkBodyV1,
            aliases=self.handles,
            variant="minimal",
        )

    def compile(self, wire: ScratchLinkMinimalWireV1) -> ScratchLinkBodyV1:
        return ScratchLinkBodyV1(
            from_=self._resolve(
                index=wire.from_index,
                handle=wire.from_handle,
                pointer=(
                    "/from_index" if wire.from_index is not None else "/from_handle"
                ),
            ),
            to=self._resolve(
                index=wire.to_index,
                handle=wire.to_handle,
                pointer="/to_index" if wire.to_index is not None else "/to_handle",
            ),
            relation_hint=wire.relation_hint,
        )


class ClusterGuideWireContract(_ReferenceCompiler, WireContract[ClusterGuideDraftV1]):
    _HANDLE_FIELDS = ("entry_points",)

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


class ClusterGuideMinimalWireContract(
    _ReferenceCompiler, WireContract[ClusterGuideDraftV1]
):
    _HANDLE_FIELDS = ("entry_points",)

    def __init__(self, *, handles: Mapping[str, str] | AliasTable) -> None:
        _ReferenceCompiler.__init__(self, handles=handles)
        WireContract.__init__(
            self,
            "scratch.cluster-guide.minimal.v1",
            ClusterGuideMinimalWireV1,
            ClusterGuideDraftV1,
            aliases=self.handles,
            variant="minimal",
        )

    def compile(self, wire: ClusterGuideMinimalWireV1) -> ClusterGuideDraftV1:
        return ClusterGuideDraftV1(working_focus=wire.working_focus)


# Explicit compact aliases make intent clear at call sites without creating a
# second protocol or model-profile fork.
CompactScratchBlockV1 = ScratchBlockWireV1
CompactScratchLinkV1 = ScratchLinkWireV1
CompactClusterGuideV1 = ClusterGuideWireV1


__all__ = [
    "ClusterGuideDraftV1",
    "ClusterGuideWireContract",
    "ClusterGuideMinimalWireContract",
    "ClusterGuideMinimalWireV1",
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
    "ScratchBlockMinimalWireContract",
    "ScratchBlockMinimalWireV1",
    "ScratchBlockWireV1",
    "ScratchLinkWireContract",
    "ScratchLinkMinimalWireContract",
    "ScratchLinkMinimalWireV1",
    "ScratchLinkWireV1",
    "ScratchWireReferenceError",
]
