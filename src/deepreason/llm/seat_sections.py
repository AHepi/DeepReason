"""The seat section plugin interface — one brief, assembled from parts.

A seat is a shell: what makes it a conjecturer or a critic is the BRIEF it is
shown and the FORM it is asked to fill, both registered, versioned
configuration rather than a code path carrying the seat's name (CLAUDE.md,
"A seat is a shell: its input and its output define it", 2026-09-03). This
module holds the input side of that: the protocol a brief section is rendered
through, the read-only request it is handed, the free-text render it returns,
and the typed receipt of what actually ran.

Nothing here knows about seats. `SectionRequestV1`, `SectionRenderV1` and
`SectionReceiptV1` carry no seat name and no seat field, and that absence is
load-bearing rather than incidental: the law's own scope boundary says the
shell governs how content is GENERATED and may never reach what counts as
EVIDENCE, so a receipt that named its seat would hand the evidence side a
generation-side fact to read.

Three layers, and they are not interchangeable (the signal-contract pattern
the modularity law generalizes, as `DR-INV-render-layout` states it):

**FROZEN** is the change protocol. A plugin's output is PRESENTATION, never
evidence: no plugin may change what is admitted, ranked, immune or refuted.
The parse half of every form does not vary. Nothing truncates silently. Only
the operator authors a plugin.

**VERSIONED** is the registry and the shipped layouts: a new arrangement is a
registration, never a consumer edit.

**FREE** is each plugin's parameters and each layout entry's bounds, refused
typed at construction when out of range rather than silently clamped.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

SECTION_SCHEMA_VERSION = "seat-section.v1"

# What a rendered section can have become by the time the allocator is done.
# `absent` is the plugin declining to render at all (a `None` return); it is
# distinct from `dropped`, which is the allocator cutting content that existed.
DISPOSITIONS = ("rendered", "compressed", "dropped", "absent")


class SeatSectionError(ValueError):
    """A typed refusal from the section layer.

    Carries a code because the callers that must distinguish causes -- a
    layout construction refusing an out-of-envelope value, a resolution
    refusing an unregistered id -- are the ones the architecture tests assert
    on, and asserting on a message string is what a gutted guard survives.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class SectionRequestV1(BaseModel):
    """Everything a section plugin may read, and nothing it may write.

    FROZEN, and the freeze is the interface rather than a convenience: a
    plugin that could mutate the request could reach the run's state through
    the brief, which is the one direction the seat-is-a-shell law forbids.
    `render` may not call the harness or write the log either -- the same
    prohibition `DR-CON-conjecture-source` already places on `conj`.

    `supplied` carries the contexts the CALLER computed, keyed by the argument
    names the renderers already use, because nine of the conjecturer's twenty
    sections and four of the critic's thirteen are computed in `rules/` rather
    than in the renderer: they need a dossier receipt, a fence sequence or a
    work order, none of which a renderer holds
    (`DR-SEAM-packs-and-token-economy-x-rules`). Their plugins FORMAT a value
    the caller supplies; moving that computation behind this interface is a
    later step, not this one.
    """

    model_config = ConfigDict(
        extra="forbid", frozen=True, arbitrary_types_allowed=True
    )

    problem: Any | None = None
    state: Any = None
    commitments: Mapping[str, Any] = Field(default_factory=dict)
    blobs: Any = None
    layout: Any = None
    supplied: Mapping[str, Any] = Field(default_factory=dict)


class SectionRenderV1(BaseModel):
    """One section's free text, plus the allocation facts it may override.

    `text` is FREE TEXT (`R7`). The harness does not parse it, does not
    interpret it, and asserts nothing about its content -- the plugin formats
    it. What the harness does assert is that it is NOT EMPTY: an empty render
    is an error, while `None` from `render` is a legal absence. That
    distinction is the one the allocator's drop signal depends on. A dropped
    section leaves no header, so "rendered empty" and "never had content"
    would otherwise be byte-indistinguishable in the pack, which is the silent
    cap `DR-CON-packs-and-token-economy`'s NO SILENT CAPS rule abolishes.

    `priority`, `droppable`, `compressible` and `min_tokens` default to the
    layout entry's values and are overridden only when a plugin has a reason
    the layout cannot express.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    priority: int | None = Field(default=None, ge=1)
    droppable: bool | None = None
    compressible: bool | None = None
    min_tokens: int | None = Field(default=None, ge=0)
    provenance_refs: tuple[str, ...] = ()
    declared_handle_kinds: tuple[str, ...] = ()


class SectionReceiptV1(BaseModel):
    """What actually ran, typed, so the record can answer "which bytes did
    this run show, from which plugin, at which version, under which
    parameters".

    "Not typed" (`R7`) constrains a plugin's OUTPUT, not its RECEIPT. A
    plugin that emitted nothing typed at all would make the run unauditable,
    which contradicts this repo's own epistemology: the record is the only
    admissible evidence.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str = Field(min_length=1)
    plugin_id: str = Field(min_length=1)
    plugin_version: str = Field(min_length=1)
    parameters_digest: str = Field(min_length=1)
    source_bytes: int = Field(ge=0)
    rendered_bytes: int = Field(ge=0)
    disposition: str = Field(min_length=1)

    def __init__(self, **data: Any) -> None:
        # Checked BEFORE pydantic rather than in a validator: pydantic wraps
        # anything a validator raises into a ValidationError, and the point of
        # a typed refusal is that a caller can read its code. A `Literal`
        # field would refuse the value too, but with the same wrapping.
        disposition = data.get("disposition")
        if disposition is not None and disposition not in DISPOSITIONS:
            raise SeatSectionError(
                "SEAT_SECTION_DISPOSITION_UNKNOWN",
                f"{disposition!r} is not one of {DISPOSITIONS}",
            )
        super().__init__(**data)


@runtime_checkable
class SeatSectionPluginV1(Protocol):
    """One generic interface, every section, every seat (`R5`).

    `plugin_id` is stable for the life of the plugin; `plugin_version` moves
    when the DEFAULT RENDER changes, so a receipt naming a version answers
    "which bytes" from the record alone.

    `render` returns `None` when the section has nothing this cycle -- exactly
    the `if <context>:` guards the renderers use today.
    """

    plugin_id: str
    plugin_version: str
    parameters_model: type[BaseModel]

    def render(
        self, request: SectionRequestV1, params: BaseModel
    ) -> SectionRenderV1 | None: ...


# ---------------------------------------------------------------------------
# The registry — the VERSIONED layer.
#
# Modelled on `llm/layout.py::register_layout_policy`, which
# `DR-INV-render-layout` proves needs no consumer edit to gain an arrangement.
# Keyed by `(plugin_id, plugin_version)` so a version bump is additive rather
# than a replacement: a layout entry may pin a version, and a run's receipt
# always records the version that actually resolved.
# ---------------------------------------------------------------------------

SECTION_PLUGIN_REGISTRY: dict[tuple[str, str], SeatSectionPluginV1] = {}


def _version_key(version: str) -> tuple:
    """Sort versions numerically where they look numeric, lexically otherwise.

    A plain string sort puts "1.10.0" before "1.9.0", which would silently
    resolve an unpinned entry to the wrong plugin.
    """

    parts = []
    for piece in version.split("."):
        parts.append((0, int(piece), "") if piece.isdigit() else (1, 0, piece))
    return tuple(parts)


def register_section_plugin(plugin: SeatSectionPluginV1) -> SeatSectionPluginV1:
    """Add a section plugin. Re-registering one `(id, version)` with a
    DIFFERENT object is refused: a version names one render for the life of
    the process, or two receipts citing it would not mean the same thing.

    Registering the same object twice is idempotent, because a module
    imported twice must not be an error.
    """

    if not isinstance(plugin, SeatSectionPluginV1):
        raise SeatSectionError(
            "SEAT_SECTION_PLUGIN_MALFORMED",
            "a section plugin must carry plugin_id, plugin_version, "
            "parameters_model and render",
        )
    key = (plugin.plugin_id, plugin.plugin_version)
    existing = SECTION_PLUGIN_REGISTRY.get(key)
    if existing is not None and existing is not plugin:
        raise SeatSectionError(
            "SEAT_SECTION_PLUGIN_CONFLICT",
            f"plugin {plugin.plugin_id!r} version "
            f"{plugin.plugin_version!r} is already registered",
        )
    SECTION_PLUGIN_REGISTRY[key] = plugin
    return plugin


def section_plugin_ids() -> tuple[str, ...]:
    return tuple(sorted({plugin_id for plugin_id, _ in SECTION_PLUGIN_REGISTRY}))


def resolve_section_plugin(
    plugin_id: str, version: str | None = None
) -> SeatSectionPluginV1:
    """Pinned resolves exactly; unpinned resolves to the highest version.

    An unregistered id is a TYPED REFUSAL and never a load-by-path. That is a
    security boundary and not a courtesy: a plugin's code runs inside the
    harness, so the only thing that may introduce one is the operator putting
    a file in their own plugin directory. A configuration, a model reply, a
    fetched document or a tool result naming a plugin id it does not have gets
    this refusal, never a filesystem lookup (`S3.2`).
    """

    if version is not None:
        plugin = SECTION_PLUGIN_REGISTRY.get((plugin_id, version))
        if plugin is None:
            raise SeatSectionError(
                "SEAT_SECTION_PLUGIN_UNKNOWN",
                f"no section plugin {plugin_id!r} at version {version!r}; "
                "registered: " + ", ".join(section_plugin_ids()),
            )
        return plugin

    versions = [v for pid, v in SECTION_PLUGIN_REGISTRY if pid == plugin_id]
    if not versions:
        raise SeatSectionError(
            "SEAT_SECTION_PLUGIN_UNKNOWN",
            f"no section plugin {plugin_id!r}; registered: "
            + ", ".join(section_plugin_ids()),
        )
    return SECTION_PLUGIN_REGISTRY[
        (plugin_id, max(versions, key=_version_key))
    ]


# ---------------------------------------------------------------------------
# The layout — which plugins a seat's brief is assembled from, in what order,
# under what budget. The FREE layer: parameter values inside declared
# envelopes, refused typed at construction rather than silently clamped.
#
# Selection is by ID, from an argument or the environment, and NEVER from
# `Config` or the manifest. That is not a preference, it is measured:
# `run_manifest.py::_source_config_data` dumps every `Config` field into
# `engine_config_json` and `qualification.py` folds that into every
# qualification subject digest, so a layout knob on `Config` would move the
# digest of every qualification bundle in the tree -- four committed manifests
# tested, identical verdict
# (`experiments/2026-09-03-change-conjecturer-pluggable-interface/`
# FEASIBILITY.md §6.2). The transport tranche measured the other half of it:
# a `Config` field holding a pydantic model cannot round-trip through the
# manifest's carriage notice at all.
# ---------------------------------------------------------------------------

SEAT_PACK_LAYOUT_ENV = "DEEPREASON_SEAT_PACK_LAYOUT"

# The allocator orders by `(priority, id)` and reserves 99 for the withheld
# notice and 100 for the restated question, so an entry may not claim either.
MAXIMUM_ENTRY_PRIORITY = 98
MAXIMUM_MIN_TOKENS = 4096
MAXIMUM_RENDER_BYTES = 1_048_576


class SeatPackLayoutEntryV1(BaseModel):
    """One plugin's place in one seat's brief.

    `priority`, `droppable`, `compressible` and `min_tokens` are ALLOCATION
    facts and live here rather than in the plugin, which is what lets two
    seats share one plugin at different priorities: the conjecturer carries
    `citable-evidence-blocks` at 4 and the critic at 6, and neither bends the
    plugin to do it.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    plugin_id: str = Field(min_length=1)
    plugin_version: str | None = None
    priority: int = Field(ge=1, le=MAXIMUM_ENTRY_PRIORITY)
    droppable: bool = False
    compressible: bool = False
    min_tokens: int = Field(default=0, ge=0, le=MAXIMUM_MIN_TOKENS)
    max_render_bytes: int | None = Field(
        default=None, ge=1, le=MAXIMUM_RENDER_BYTES
    )
    params: Mapping[str, Any] = Field(default_factory=dict)

    def __init__(self, **data: Any) -> None:
        # Refused, never clamped, and refused BEFORE pydantic so the caller
        # reads a code rather than a wrapped ValidationError. A silently
        # clamped value is a configuration that did not do what it says, which
        # is the failure the FREE layer's envelope exists to prevent.
        for field, ceiling in (
            ("priority", MAXIMUM_ENTRY_PRIORITY),
            ("min_tokens", MAXIMUM_MIN_TOKENS),
            ("max_render_bytes", MAXIMUM_RENDER_BYTES),
        ):
            value = data.get(field)
            if isinstance(value, int) and not isinstance(value, bool):
                if value > ceiling or (field != "min_tokens" and value < 1):
                    raise SeatSectionError(
                        "SEAT_PACK_LAYOUT_OUT_OF_ENVELOPE",
                        f"{field}={value} is outside its declared envelope "
                        f"(1..{ceiling}); values are refused, never clamped",
                    )
                if field == "min_tokens" and value < 0:
                    raise SeatSectionError(
                        "SEAT_PACK_LAYOUT_OUT_OF_ENVELOPE",
                        f"min_tokens={value} is negative",
                    )
        super().__init__(**data)


class SeatPackLayoutV1(BaseModel):
    """One seat's brief, as an ordered list of plugin entries.

    The direct sibling of `RenderLayoutPolicyV1`, which governs ARRANGEMENT
    (where a rendered prompt puts what it carries). This governs COMPOSITION
    (which parts it carries at all). A run reads both.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    layout_id: str = Field(min_length=1, max_length=96)
    layout_version: str = Field(default="1.0.0", min_length=1)
    entries: tuple[SeatPackLayoutEntryV1, ...] = ()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        seen: set[str] = set()
        for entry in self.entries:
            if entry.plugin_id in seen:
                raise SeatSectionError(
                    "SEAT_PACK_LAYOUT_DUPLICATE_PLUGIN",
                    f"{entry.plugin_id!r} appears twice in "
                    f"{self.layout_id!r}; a section id renders once per pack",
                )
            seen.add(entry.plugin_id)

    @property
    def plugin_ids(self) -> tuple[str, ...]:
        return tuple(entry.plugin_id for entry in self.entries)

    def entry_for(self, plugin_id: str) -> SeatPackLayoutEntryV1 | None:
        for entry in self.entries:
            if entry.plugin_id == plugin_id:
                return entry
        return None


_LAYOUT_REGISTRY: dict[str, SeatPackLayoutV1] = {}
_DEFAULT_LAYOUT_FOR_SEAT: dict[str, str] = {}


# A plugin is EVIDENCE-FAMILY if it renders admitted evidence -- by naming
# itself so, or by declaring the handle kinds that make evidence citable.
EVIDENCE_FAMILY_PREFIX = "dr.evidence."


def _refuse_undisclosed_evidence(layout: SeatPackLayoutV1) -> None:
    """An evidence-family section must be one whose ABSENCE is disclosed.

    A dropped section leaves no header, so a pack whose evidence the budget cut
    looks exactly like a run with no admitted evidence in it -- and a seat that
    cannot tell those apart stops citing. `DISCLOSED_ON_DROP` is what forces
    the `context-withheld` notice instead, and a layout that put an evidence
    plugin outside that set would re-open the silent path by configuration.
    Refused here rather than at render, so the operator learns at load.
    """

    from deepreason.llm.packs import DISCLOSED_ON_DROP

    for entry in layout.entries:
        try:
            plugin = resolve_section_plugin(entry.plugin_id, entry.plugin_version)
        except SeatSectionError:
            # Resolution failures are that function's to report, with its own
            # code; this check does not want to mask one.
            continue
        evidence = entry.plugin_id.startswith(EVIDENCE_FAMILY_PREFIX) or bool(
            getattr(plugin, "declared_handle_kinds", ())
        )
        section_id = getattr(plugin, "section_id", "")
        if evidence and section_id not in DISCLOSED_ON_DROP:
            raise SeatSectionError(
                "SEAT_PACK_LAYOUT_EVIDENCE_NOT_DISCLOSED",
                f"{entry.plugin_id!r} renders evidence as section "
                f"{section_id!r}, which is not in DISCLOSED_ON_DROP; a "
                "budget cut would remove it with no signal",
            )


def register_seat_pack_layout(
    layout: SeatPackLayoutV1, *, default_for_seat: str | None = None
) -> SeatPackLayoutV1:
    """Add a layout. Re-registering one id with different values is refused,
    for the reason `register_layout_policy` refuses it: an id names ONE
    composition, or two runs citing it do not mean the same thing."""

    _refuse_undisclosed_evidence(layout)
    existing = _LAYOUT_REGISTRY.get(layout.layout_id)
    if existing is not None and existing != layout:
        raise SeatSectionError(
            "SEAT_PACK_LAYOUT_CONFLICT",
            f"layout id {layout.layout_id!r} is already registered with "
            "different values",
        )
    _LAYOUT_REGISTRY[layout.layout_id] = layout
    if default_for_seat is not None:
        _DEFAULT_LAYOUT_FOR_SEAT[default_for_seat] = layout.layout_id
    return layout


def seat_pack_layout_ids() -> tuple[str, ...]:
    return tuple(sorted(_LAYOUT_REGISTRY))


def _environment_assignments(raw: str) -> dict[str, str]:
    """Parse `conjecturer=<id>,critic=<id>`.

    One process renders every seat, so a single-valued variable could not say
    which seat it meant. A malformed term is a TYPED REFUSAL naming it, never
    a silent fallback to the default -- a configuration that quietly did
    nothing is the shape the all-configurations law calls a gate the operator
    cannot turn on.
    """

    assignments: dict[str, str] = {}
    for term in raw.split(","):
        term = term.strip()
        if not term:
            continue
        seat, separator, layout_id = term.partition("=")
        if not separator or not seat.strip() or not layout_id.strip():
            raise SeatSectionError(
                "SEAT_PACK_LAYOUT_ASSIGNMENT_MALFORMED",
                f"{term!r} is not `<seat>=<layout_id>` in "
                f"{SEAT_PACK_LAYOUT_ENV}",
            )
        assignments[seat.strip()] = layout_id.strip()
    return assignments


def resolve_seat_pack_layout(
    seat_id: str, layout_id: str | None = None
) -> SeatPackLayoutV1:
    """Explicit argument, then the environment, then the seat's default.

    Resolved PER CALL rather than bound at import, so selecting a composition
    through the environment takes effect without a restart -- the property
    `DR-INV-render-layout` already relies on for arrangement.
    """

    import os

    requested = layout_id
    if requested is None:
        raw = os.environ.get(SEAT_PACK_LAYOUT_ENV) or ""
        if raw.strip():
            requested = _environment_assignments(raw).get(seat_id)
    if requested is None:
        requested = _DEFAULT_LAYOUT_FOR_SEAT.get(seat_id)
    if requested is None:
        raise SeatSectionError(
            "SEAT_PACK_LAYOUT_NO_DEFAULT",
            f"no default seat pack layout for seat {seat_id!r}; registered: "
            + ", ".join(seat_pack_layout_ids()),
        )
    layout = _LAYOUT_REGISTRY.get(requested)
    if layout is None:
        raise SeatSectionError(
            "SEAT_PACK_LAYOUT_UNKNOWN",
            f"no seat pack layout {requested!r}; registered: "
            + ", ".join(seat_pack_layout_ids()),
        )
    return layout
