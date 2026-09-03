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
