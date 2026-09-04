"""Section SOURCES — where a brief section's CONTENT comes from.

A seat is a shell (CLAUDE.md, 2026-09-03). `seat_sections.py` holds the input
half of that shell: the plugin protocol that FORMATS one section, the layout
that composes a brief, and the registries both resolve from. This module holds
the half that plugin protocol deliberately cannot reach.

A plugin may not call the harness. Nine of the conjecturer's twenty sections
need the record to exist at all -- a dossier receipt, a fence sequence, a work
order, an open-criticism view -- so before this module they were computed in
`rules/conj.py` and handed to the renderer as strings
(`DR-SEAM-packs-and-token-economy-x-rules`, and the prior tranche's `SPEC.md`
assumption A6). That left the generation side reaching into the admission code
for exactly the sections that carry evidence, which is the seam the
seat-is-a-shell law's stated purpose -- "slowly separate the authority layer"
-- is aimed at.

A SOURCE closes it. A source reads the state and the record, computes one
value, writes no event, and hands the value to the plugin that formats it. It
is registered and versioned like a plugin, and a seat's SOURCE BUNDLE is
selected by id the same way its layout is.

**What a source may do, stated as the contract the architecture test
enforces.**

READ: the log, the state, the blobs, the run root, the manifest, the config,
and whatever call-local state the caller hands over. Reading the record is not
a contact with any frozen surface, and forbidding it would not make this layer
purer -- it would make it empty, and leave the computation where it was.

NEVER APPEND: after any source runs, the run's next event sequence, the bytes
of `log.jsonl`, and the state digest are unchanged. That is the whole
prohibition and `tests/test_seat_section_sources.py` measures all three across
every registered source, with a planted write to show the measurement bites.

ONE DECLARED WRITE: content-addressed blob materialisation, and only by a
source declaring `writes_blobs = True`. `pack_dossier` must materialise the
excerpts it selected before its receipt can name them, so the frozen-evidence
value cannot exist without it. A blob put is keyed by the hash of its own
bytes, is idempotent, appends no event, assigns no epistemic status and moves
no digest -- it is materialisation, not record. It is declared rather than
tolerated so that an undeclared one is a test failure.

**Stages, and why there are five.** A stage boundary exists only where the
CALLER must do something this interface may not: build the turn contract
(which needs to know whether criticism is open), allocate the pack, abandon a
pre-issued scratch context when its render fails, and bind the pack's alias
table. That last one is the load-bearing exclusion: an alias table decides
what a citation RESOLVES TO, which is the evidence side, and a registered,
swappable alias binder would let a brief configuration change what the harness
accepts.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

SOURCE_SCHEMA_VERSION = "seat-section-source.v1"

# What a source can have become. `absent` is the source declining -- a `None`
# return, or a declared input this seat's call does not carry. There is no
# `dropped`: dropping is the allocator's verb and happens to SECTIONS, after a
# plugin has formatted whatever a source produced.
SOURCE_DISPOSITIONS = ("resolved", "absent")

# The five stages, in the order a caller runs them. Ordering is part of the
# vocabulary rather than a convention, because a bundle entry names one and the
# runner must refuse a name it cannot place.
STAGE_PRE_CONTRACT = "pre_contract"
STAGE_RENDER = "render"
STAGE_POST_ALLOCATION_CONTEXT = "post_allocation_context"
STAGE_POST_ALLOCATION = "post_allocation"
STAGE_POST_ALLOCATION_AFTER_ALIASES = "post_allocation_after_aliases"

STAGES = (
    STAGE_PRE_CONTRACT,
    STAGE_RENDER,
    STAGE_POST_ALLOCATION_CONTEXT,
    STAGE_POST_ALLOCATION,
    STAGE_POST_ALLOCATION_AFTER_ALIASES,
)

# The stages whose sources produce PACK TEXT rather than a supplied value.
POST_ALLOCATION_STAGES = (
    STAGE_POST_ALLOCATION_CONTEXT,
    STAGE_POST_ALLOCATION,
    STAGE_POST_ALLOCATION_AFTER_ALIASES,
)


class SeatSourceError(ValueError):
    """A typed refusal from the source layer.

    Carries a code for the reason `SeatSectionError` does: the tests that must
    distinguish an out-of-vocabulary stage from an unregistered id assert on
    the code, and asserting on a message string is what a gutted guard
    survives.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class SectionSourceRequestV1(BaseModel):
    """Everything a source may read, and nothing it may write.

    `harness` is the live harness and `run_manifest`, `config` and `problem`
    are the run's own objects, because a source's whole reason to exist is
    that a plugin cannot see them. The prohibition on appending is a CONTRACT,
    not a wrapper: a read-only proxy over the harness would have to enumerate
    every read four subsystems make, and the first one it missed would be a
    run that died rather than a test that failed.

    `inputs` carries the call-local state the caller hands over -- which
    contract version is active, the transaction's work order, the scratch
    context plan. `supplied` and `carries` are what earlier sources in this
    bundle already produced, so a later source can build on one without the
    caller relaying it.
    """

    model_config = ConfigDict(
        extra="forbid", frozen=True, arbitrary_types_allowed=True
    )

    harness: Any = None
    run_manifest: Any = None
    config: Any = None
    problem: Any = None
    inputs: Mapping[str, Any] = Field(default_factory=dict)
    supplied: Mapping[str, Any] = Field(default_factory=dict)
    carries: Mapping[str, Any] = Field(default_factory=dict)

    def lookup(self, name: str, default: Any = None) -> Any:
        """One name space over the three mappings, searched most-local first.

        A source declares `requires` against this, so a value can move between
        "the caller handed it over" and "an earlier source produced it"
        without every source that reads it changing.
        """

        for mapping in (self.carries, self.supplied, self.inputs):
            if name in mapping:
                return mapping[name]
        return default


class SectionSourceResultV1(BaseModel):
    """What one source produced.

    A RENDER-stage source sets `value`: the thing a plugin will format, under
    the key `supplies`. A POST-ALLOCATION source sets `text`, which the runner
    appends to the pack -- and additionally `substitutes` when the text
    REPLACES existing pack bytes instead of following them.

    `carries` is the by-product channel, and it is what keeps the record-side
    act in `rules/`: the frozen-evidence source carries the dossier receipt it
    built, and the caller -- not this layer -- commits it.
    """

    model_config = ConfigDict(
        extra="forbid", frozen=True, arbitrary_types_allowed=True
    )

    supplies: str = Field(min_length=1)
    value: Any = None
    text: str | None = None
    substitutes: str | None = None
    carries: Mapping[str, Any] = Field(default_factory=dict)


class SectionSourceReceiptV1(BaseModel):
    """What actually ran, typed.

    Returned to the caller and NEVER written to the log. Writing it would
    create a new record object kind, which is frozen surface 2 and an explicit
    stop for an operator grant; the previous build parked exactly that and
    this one does not reopen it.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    supplies: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    parameters_digest: str = Field(min_length=1)
    value_bytes: int = Field(ge=0)
    disposition: str = Field(min_length=1)

    def __init__(self, **data: Any) -> None:
        # Checked before pydantic, so a caller reads a code rather than a
        # wrapped ValidationError -- `SectionReceiptV1` states the reasoning.
        disposition = data.get("disposition")
        if disposition is not None and disposition not in SOURCE_DISPOSITIONS:
            raise SeatSourceError(
                "SEAT_SOURCE_DISPOSITION_UNKNOWN",
                f"{disposition!r} is not one of {SOURCE_DISPOSITIONS}",
            )
        super().__init__(**data)


class SourceAssemblyV1(BaseModel):
    """One stage's output: the values, the by-products, and what ran."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, arbitrary_types_allowed=True
    )

    supplied: Mapping[str, Any] = Field(default_factory=dict)
    carries: Mapping[str, Any] = Field(default_factory=dict)
    receipts: tuple[SectionSourceReceiptV1, ...] = ()

    def value(self, name: str, default: Any = None) -> Any:
        if name in self.supplied:
            return self.supplied[name]
        return self.carries.get(name, default)


@runtime_checkable
class SeatSectionSourceV1(Protocol):
    """One generic interface, every caller-computed section, every seat.

    `source_id` is stable for the life of the source; `source_version` moves
    when the value it computes changes, so a receipt naming a version answers
    "which bytes" from the record alone -- the same rule the plugin registry
    keeps.
    """

    source_id: str
    source_version: str
    supplies: str
    parameters_model: type[BaseModel]

    def resolve(
        self, request: SectionSourceRequestV1, params: BaseModel
    ) -> SectionSourceResultV1 | None: ...


# ---------------------------------------------------------------------------
# The registry — the VERSIONED layer, keyed exactly as the plugin registry is.
# ---------------------------------------------------------------------------

SECTION_SOURCE_REGISTRY: dict[tuple[str, str], SeatSectionSourceV1] = {}


def _version_key(version: str) -> tuple:
    """Numeric where it looks numeric, lexical otherwise, so "1.10.0" sorts
    above "1.9.0" -- a plain string sort would resolve an unpinned entry to
    the wrong source."""

    parts = []
    for piece in version.split("."):
        parts.append((0, int(piece), "") if piece.isdigit() else (1, 0, piece))
    return tuple(parts)


def register_section_source(source: SeatSectionSourceV1) -> SeatSectionSourceV1:
    """Add a source. Re-registering one `(id, version)` with a DIFFERENT
    object is refused: a version names one computation for the life of the
    process, or two receipts citing it would not mean the same thing.

    Registering the same object twice is idempotent, because a module imported
    twice must not be an error.
    """

    if not isinstance(source, SeatSectionSourceV1):
        raise SeatSourceError(
            "SEAT_SOURCE_MALFORMED",
            "a section source must carry source_id, source_version, supplies, "
            "parameters_model and resolve",
        )
    key = (source.source_id, source.source_version)
    existing = SECTION_SOURCE_REGISTRY.get(key)
    if existing is not None and existing is not source:
        raise SeatSourceError(
            "SEAT_SOURCE_CONFLICT",
            f"source {source.source_id!r} version {source.source_version!r} "
            "is already registered",
        )
    SECTION_SOURCE_REGISTRY[key] = source
    return source


def section_source_ids() -> tuple[str, ...]:
    return tuple(sorted({source_id for source_id, _ in SECTION_SOURCE_REGISTRY}))


def resolve_section_source(
    source_id: str, version: str | None = None
) -> SeatSectionSourceV1:
    """Pinned resolves exactly; unpinned resolves to the highest version.

    An unregistered id is a TYPED REFUSAL and never a load-by-path, for the
    reason `resolve_section_plugin` gives: a source's code runs inside the
    harness with the harness in its hand, so the only thing that may introduce
    one is the operator.
    """

    if version is not None:
        source = SECTION_SOURCE_REGISTRY.get((source_id, version))
        if source is None:
            raise SeatSourceError(
                "SEAT_SOURCE_UNKNOWN",
                f"no section source {source_id!r} at version {version!r}; "
                "registered: " + ", ".join(section_source_ids()),
            )
        return source

    versions = [v for sid, v in SECTION_SOURCE_REGISTRY if sid == source_id]
    if not versions:
        raise SeatSourceError(
            "SEAT_SOURCE_UNKNOWN",
            f"no section source {source_id!r}; registered: "
            + ", ".join(section_source_ids()),
        )
    return SECTION_SOURCE_REGISTRY[(source_id, max(versions, key=_version_key))]


# ---------------------------------------------------------------------------
# The bundle — which sources a seat's brief is fed from, in what order, at
# which stage. Selected by ID from an argument or the environment, and NEVER
# from `Config` or the manifest: the manifest dumps every `Config` field into
# `engine_config_json` and qualification folds that into every subject digest,
# so a knob here would move the digest of every qualification bundle in the
# tree (`DR-INV-seat-section-plugins`, which measured it).
# ---------------------------------------------------------------------------

SEAT_SOURCE_BUNDLE_ENV = "DEEPREASON_SEAT_SOURCE_BUNDLE"


class SeatSourceBundleEntryV1(BaseModel):
    """One source's place in one seat's assembly."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    source_version: str | None = None
    stage: str = Field(min_length=1)
    params: Mapping[str, Any] = Field(default_factory=dict)

    def __init__(self, **data: Any) -> None:
        stage = data.get("stage")
        if stage is not None and stage not in STAGES:
            raise SeatSourceError(
                "SEAT_SOURCE_STAGE_UNKNOWN",
                f"{stage!r} is not one of {STAGES}",
            )
        super().__init__(**data)


class SeatSourceBundleV1(BaseModel):
    """One seat's assembly, as an ordered list of source entries.

    Order inside a stage is meaningful and is the declaration of it: the
    pre-allocation menu source reads the citable blocks the evidence source
    carried, and the post-allocation menu source reads the scratch aliases the
    context source carried.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    bundle_id: str = Field(min_length=1, max_length=96)
    bundle_version: str = Field(default="1.0.0", min_length=1)
    entries: tuple[SeatSourceBundleEntryV1, ...] = ()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        seen: set[str] = set()
        for entry in self.entries:
            if entry.source_id in seen:
                raise SeatSourceError(
                    "SEAT_SOURCE_BUNDLE_DUPLICATE",
                    f"{entry.source_id!r} appears twice in "
                    f"{self.bundle_id!r}; a source resolves once per call",
                )
            seen.add(entry.source_id)

    def entries_for_stage(self, stage: str) -> tuple[SeatSourceBundleEntryV1, ...]:
        if stage not in STAGES:
            raise SeatSourceError(
                "SEAT_SOURCE_STAGE_UNKNOWN", f"{stage!r} is not one of {STAGES}"
            )
        return tuple(entry for entry in self.entries if entry.stage == stage)


_BUNDLE_REGISTRY: dict[str, SeatSourceBundleV1] = {}
_DEFAULT_BUNDLE_FOR_SEAT: dict[str, str] = {}


def register_seat_source_bundle(
    bundle: SeatSourceBundleV1, *, default_for_seat: str | None = None
) -> SeatSourceBundleV1:
    """Add a bundle. Re-registering one id with different values is refused:
    an id names ONE assembly, or two runs citing it do not mean the same
    thing."""

    existing = _BUNDLE_REGISTRY.get(bundle.bundle_id)
    if existing is not None and existing != bundle:
        raise SeatSourceError(
            "SEAT_SOURCE_BUNDLE_CONFLICT",
            f"bundle id {bundle.bundle_id!r} is already registered with "
            "different values",
        )
    _BUNDLE_REGISTRY[bundle.bundle_id] = bundle
    if default_for_seat is not None:
        _DEFAULT_BUNDLE_FOR_SEAT[default_for_seat] = bundle.bundle_id
    return bundle


def seat_source_bundle_ids() -> tuple[str, ...]:
    return tuple(sorted(_BUNDLE_REGISTRY))


def _environment_assignments(raw: str) -> dict[str, str]:
    """Parse `conjecturer=<id>,critic=<id>`.

    One process feeds every seat, so a single-valued variable could not say
    which seat it meant. A malformed term is a typed refusal naming it, never
    a silent fallback -- a configuration that quietly did nothing is the shape
    the all-configurations law calls a gate the operator cannot turn on.
    """

    assignments: dict[str, str] = {}
    for term in raw.split(","):
        term = term.strip()
        if not term:
            continue
        seat, separator, bundle_id = term.partition("=")
        if not separator or not seat.strip() or not bundle_id.strip():
            raise SeatSourceError(
                "SEAT_SOURCE_BUNDLE_ASSIGNMENT_MALFORMED",
                f"{term!r} is not `<seat>=<bundle_id>` in "
                f"{SEAT_SOURCE_BUNDLE_ENV}",
            )
        assignments[seat.strip()] = bundle_id.strip()
    return assignments


def resolve_seat_source_bundle(
    seat_id: str, bundle_id: str | None = None
) -> SeatSourceBundleV1:
    """Explicit argument, then the environment, then the seat's default.

    Resolved PER CALL rather than bound at import, so selecting an assembly
    through the environment takes effect without a restart -- the property the
    layout and arrangement registries already rely on.
    """

    from deepreason.seat_sources.shipped import ensure_sources_seeded

    ensure_sources_seeded()
    requested = bundle_id
    if requested is None:
        raw = os.environ.get(SEAT_SOURCE_BUNDLE_ENV) or ""
        if raw.strip():
            requested = _environment_assignments(raw).get(seat_id)
    if requested is None:
        requested = _DEFAULT_BUNDLE_FOR_SEAT.get(seat_id)
    if requested is None:
        raise SeatSourceError(
            "SEAT_SOURCE_BUNDLE_NO_DEFAULT",
            f"no default source bundle for seat {seat_id!r}; registered: "
            + ", ".join(seat_source_bundle_ids()),
        )
    bundle = _BUNDLE_REGISTRY.get(requested)
    if bundle is None:
        raise SeatSourceError(
            "SEAT_SOURCE_BUNDLE_UNKNOWN",
            f"no seat source bundle {requested!r}; registered: "
            + ", ".join(seat_source_bundle_ids()),
        )
    return bundle


# ---------------------------------------------------------------------------
# The runner.
# ---------------------------------------------------------------------------


def _parameters_digest(params: BaseModel) -> str:
    payload = json.dumps(params.model_dump(mode="json"), sort_keys=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _value_bytes(result: SectionSourceResultV1) -> int:
    for candidate in (result.text, result.value):
        if isinstance(candidate, str):
            return len(candidate.encode("utf-8"))
    return 0


def _run_stage(seat_id, stage, request, bundle_id, prior):
    """Walk one stage's entries in order, threading what each produced.

    THE ONE LEGAL WAY a caller-computed section value is produced. A source
    that declines -- by returning `None`, or by declaring an input this call
    does not carry -- is recorded `absent` and leaves its key OUT of the
    supplied mapping, which is what makes the renderer's own default apply and
    the default render stay byte-identical.
    """

    bundle = resolve_seat_source_bundle(seat_id, bundle_id)
    supplied: dict[str, Any] = dict(prior.supplied) if prior is not None else {}
    carries: dict[str, Any] = dict(prior.carries) if prior is not None else {}
    receipts: list[SectionSourceReceiptV1] = []
    applied: list[SectionSourceResultV1] = []
    for entry in bundle.entries_for_stage(stage):
        source = resolve_section_source(entry.source_id, entry.source_version)
        params = source.parameters_model(**dict(entry.params))
        view = request.model_copy(
            update={"supplied": dict(supplied), "carries": dict(carries)}
        )
        missing = [
            name
            for name in getattr(source, "requires", ())
            if view.lookup(name) in (None, (), "", {})
        ]
        result = None if missing else source.resolve(view, params)
        if result is None:
            receipts.append(
                SectionSourceReceiptV1(
                    source_id=source.source_id,
                    source_version=source.source_version,
                    supplies=source.supplies,
                    stage=stage,
                    parameters_digest=_parameters_digest(params),
                    value_bytes=0,
                    disposition="absent",
                )
            )
            continue
        if stage in POST_ALLOCATION_STAGES:
            if not result.text:
                raise SeatSourceError(
                    "SEAT_SOURCE_POST_ALLOCATION_EMPTY",
                    f"{source.source_id!r} returned a result with no text at "
                    f"stage {stage!r}; decline with None instead",
                )
            applied.append(result)
        else:
            supplied[result.supplies] = result.value
        # A source may resolve to NOTHING and still carry a by-product -- the
        # frozen-evidence source carries the run's bound dossiers even on a run
        # with no attached evidence, because the citable legend after it is
        # computed over that (empty) union either way. Its disposition is still
        # `absent`, because the SECTION is what a reader of this receipt is
        # asking about.
        carries.update(result.carries)
        receipts.append(
            SectionSourceReceiptV1(
                source_id=source.source_id,
                source_version=source.source_version,
                supplies=source.supplies,
                stage=stage,
                parameters_digest=_parameters_digest(params),
                value_bytes=_value_bytes(result),
                disposition=(
                    "absent"
                    if result.text is None and result.value is None
                    else "resolved"
                ),
            )
        )
    assembly = SourceAssemblyV1(
        supplied=supplied,
        carries=carries,
        receipts=tuple(prior.receipts if prior is not None else ()) + tuple(receipts),
    )
    return assembly, applied


def assemble_sources(
    seat_id: str,
    *,
    stage: str = STAGE_RENDER,
    request: SectionSourceRequestV1,
    bundle_id: str | None = None,
    prior: SourceAssemblyV1 | None = None,
) -> SourceAssemblyV1:
    """Run one non-post-allocation stage and return what it produced."""

    if stage in POST_ALLOCATION_STAGES:
        raise SeatSourceError(
            "SEAT_SOURCE_STAGE_MISMATCH",
            f"{stage!r} produces pack text; run it through "
            "apply_post_allocation",
        )
    assembly, _ = _run_stage(seat_id, stage, request, bundle_id, prior)
    return assembly


def apply_post_allocation(
    seat_id: str,
    *,
    stage: str,
    pack: str,
    request: SectionSourceRequestV1,
    bundle_id: str | None = None,
    prior: SourceAssemblyV1 | None = None,
):
    """Run one post-allocation stage over an already-budgeted pack.

    Returns `(pack, assembly)`. Every application RE-WRAPS in `AllocatedPack`,
    and that is not tidiness: `str` operations return a plain `str`, and a
    plain `str` tells the adapter this pack was never budgeted section by
    section, so it re-applies the profile's aggregate prefix clip -- a blind
    cut through whatever sits at the boundary, on top of a budget already
    spent. Every insertion here is separately byte-accounted and bounded by
    the request envelope, so the marker must survive
    (`DR-SEAM-packs-and-token-economy-x-rules`, Traps).

    A source that SUBSTITUTES states the exact text it replaces and replaces
    it once. Replacing text that is not there, or is there more than once, is
    a typed refusal rather than a silent no-op: the pack the seat sees would
    otherwise differ from the one the transaction accounted for.
    """

    from deepreason.llm.packs import AllocatedPack

    if stage not in POST_ALLOCATION_STAGES:
        raise SeatSourceError(
            "SEAT_SOURCE_STAGE_MISMATCH",
            f"{stage!r} produces a supplied value; run it through "
            "assemble_sources",
        )
    assembly, applied = _run_stage(seat_id, stage, request, bundle_id, prior)
    for result in applied:
        if result.substitutes is None:
            pack = AllocatedPack(pack + result.text)
            continue
        if pack.count(result.substitutes) != 1:
            raise SeatSourceError(
                "SEAT_SOURCE_SUBSTITUTION_NOT_UNIQUE",
                f"{result.supplies!r} substitutes text that appears "
                f"{pack.count(result.substitutes)} times in the pack; it must "
                "appear exactly once",
            )
        pack = AllocatedPack(pack.replace(result.substitutes, result.text, 1))
    return pack, assembly


__all__ = [
    "POST_ALLOCATION_STAGES",
    "SEAT_SOURCE_BUNDLE_ENV",
    "SECTION_SOURCE_REGISTRY",
    "SOURCE_DISPOSITIONS",
    "SOURCE_SCHEMA_VERSION",
    "STAGES",
    "STAGE_POST_ALLOCATION",
    "STAGE_POST_ALLOCATION_AFTER_ALIASES",
    "STAGE_POST_ALLOCATION_CONTEXT",
    "STAGE_PRE_CONTRACT",
    "STAGE_RENDER",
    "SeatSectionSourceV1",
    "SeatSourceBundleEntryV1",
    "SeatSourceBundleV1",
    "SeatSourceError",
    "SectionSourceReceiptV1",
    "SectionSourceRequestV1",
    "SectionSourceResultV1",
    "SourceAssemblyV1",
    "apply_post_allocation",
    "assemble_sources",
    "register_seat_source_bundle",
    "register_section_source",
    "resolve_seat_source_bundle",
    "resolve_section_source",
    "seat_source_bundle_ids",
    "section_source_ids",
]
