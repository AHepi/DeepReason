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


class _TemplateParams(BaseModel):
    """A template kind takes no parameters of its own: its knobs ARE its
    text, which is the point of having it."""

    model_config = ConfigDict(extra="forbid", frozen=True)


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
# The manifest's `_source_config_data` dump carries every `Config` field into
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

    Order: explicit argument, then `DEEPREASON_SEAT_PACK_LAYOUT`, then the
    seat's SHELL, then the seat's bare default.
    """

    import os

    requested = layout_id
    if requested is None:
        raw = os.environ.get(SEAT_PACK_LAYOUT_ENV) or ""
        if raw.strip():
            requested = _environment_assignments(raw).get(seat_id)
    if requested is None:
        # The SHELL is consulted before the seat's bare default, because the
        # shell is what a seat kind IS: binding the conjecturer's shell in the
        # critic's place must change what the critic renders, or the pairing
        # would be a registry nobody reads.
        try:
            requested = resolve_seat_shell(seat_id).layout_id
        except SeatSectionError:
            requested = None
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


# ---------------------------------------------------------------------------
# Operator-authored plugins, loaded from the operator's own directory.
#
# TRUST BOUNDARY, stated because it is one and not a courtesy. A `.py` plugin
# here EXECUTES inside the harness. It is trusted for exactly the reason a
# treadle task is (CLAUDE.md, "Who may author a task"): the operator put the
# file there themselves. **Nothing model-authored is ever a plugin.** No run,
# no model reply, no fetched document and no tool result may write into this
# directory or name a plugin PATH; a plugin id that does not resolve in the
# registry is a typed refusal at resolution, never a load-by-path. That is
# what `resolve_section_plugin` already enforces, and this loader is the only
# other door.
# ---------------------------------------------------------------------------

# The template module imports this one for its typed refusal, so its name is
# taken lazily rather than at import.
SEAT_PLUGINS_DIRNAME = "seat_plugins"
TEMPLATE_SUFFIX = ".tmpl"
# A layout is DATA, not code, so it declares itself in JSON rather than in a
# module: nothing in a composition needs to run. The id comes from the file's
# own `layout_id` rather than from its name, because a layout id is already a
# field of the thing being declared and two sources for one identity is one
# too many.
LAYOUT_SUFFIX = ".layout.json"


def seat_plugins_root(*, home=None, environ=None):
    """The one directory the harness looks in, resolved the way
    `model_profiles/registry.py::profiles_root` resolves its own."""

    from deepreason.provider_profile import provider_state_dir

    return provider_state_dir(home=home, environ=environ) / SEAT_PLUGINS_DIRNAME


def load_operator_plugins(*, home=None, environ=None):
    """Register every plugin the operator has put in their own directory.

    Returns `(loaded, notices)`. NOTHING HERE RAISES on a bad file: a
    directory holding one unloadable plugin yields a typed notice naming the
    file and the error, and the run continues with the plugins that did load.
    That is the all-configurations law's "disclose, never die" shape applied
    here -- a broken formatting experiment three directories away must not
    take a run down, and a SILENT skip would be worse than either, because the
    operator would see a brief missing a section with no reason given.

    A harness with no plugin directory gets exactly the seeded set, and says
    so by returning an empty list rather than guessing.
    """

    loaded: list[str] = []
    notices: list[dict[str, str]] = []
    root = seat_plugins_root(home=home, environ=environ)
    try:
        candidates = (
            sorted(root.glob("*.py"))
            + sorted(root.glob(f"*{TEMPLATE_SUFFIX}"))
            + sorted(root.glob(f"*{LAYOUT_SUFFIX}"))
        )
    except OSError as error:
        return loaded, [
            {
                "code": "SEAT_PLUGIN_ROOT_UNREADABLE",
                "path": str(root),
                "detail": str(error),
            }
        ]
    if not root.is_dir():
        return loaded, notices

    for path in candidates:
        try:
            if path.name.endswith(LAYOUT_SUFFIX):
                loaded.append(register_seat_pack_layout_file(path).layout_id)
                continue
            if path.suffix == TEMPLATE_SUFFIX:
                plugin = _template_plugin(path)
            else:
                plugin = _python_plugin(path)
            register_section_plugin(plugin)
        except SeatSectionError as error:
            # A coded refusal keeps its own code in the notice: the operator
            # reading the record needs to know WHICH refusal this was, and
            # flattening every one of them to SEAT_PLUGIN_UNLOADABLE would
            # throw that away at the only point it is read.
            notices.append(
                {"code": error.code, "path": str(path), "detail": str(error)}
            )
            continue
        except Exception as error:  # noqa: BLE001 - disclosed, never raised
            notices.append(
                {
                    "code": "SEAT_PLUGIN_UNLOADABLE",
                    "path": str(path),
                    "detail": f"{type(error).__name__}: {error}",
                }
            )
            continue
        loaded.append(plugin.plugin_id)
    return loaded, notices


def register_seat_pack_layout_file(path) -> SeatPackLayoutV1:
    """Read one `.layout.json` and register the layout it declares.

    REFUSED, NEVER FALLEN BACK FROM. Every failure -- unreadable file,
    malformed JSON, a shape the model rejects -- raises one coded error naming
    the file, and nothing is registered. The third possibility is the one an
    operator would actually be hurt by: a brief silently composed from the
    seat's default while the file they wrote sits unread.

    `default_for_seat` is accepted alongside the layout's own fields because
    binding is a property of the DECLARATION, not of the composition; the
    model forbids extras, so it is taken out before validation.
    """

    import json

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise SeatSectionError(
            "SEAT_PACK_LAYOUT_FILE_UNPARSEABLE",
            f"{path.name} is not readable JSON: {type(error).__name__}: {error}",
        ) from error
    if not isinstance(raw, dict):
        raise SeatSectionError(
            "SEAT_PACK_LAYOUT_FILE_UNPARSEABLE",
            f"{path.name} declares {type(raw).__name__}, not one layout object",
        )
    data = dict(raw)
    default_for_seat = data.pop("default_for_seat", None)
    try:
        layout = SeatPackLayoutV1(**data)
    except SeatSectionError:
        raise
    except Exception as error:  # noqa: BLE001 - re-typed with the file's name
        raise SeatSectionError(
            "SEAT_PACK_LAYOUT_FILE_UNPARSEABLE",
            f"{path.name} is not one well-formed layout: "
            f"{type(error).__name__}: {error}",
        ) from error
    return register_seat_pack_layout(layout, default_for_seat=default_for_seat)


def _python_plugin(path):
    """Import one operator plugin file and take the plugin it declares.

    Loaded by PATH here and only here, from the operator's own directory.
    Every other route to a plugin goes through `resolve_section_plugin`, which
    refuses an unknown id rather than looking on disk.
    """

    import importlib.util

    spec = importlib.util.spec_from_file_location(
        f"deepreason_operator_plugin_{path.stem}", path
    )
    if spec is None or spec.loader is None:
        raise SeatSectionError(
            "SEAT_PLUGIN_UNLOADABLE", f"{path.name} is not importable"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plugin = getattr(module, "PLUGIN", None)
    if plugin is None:
        raise SeatSectionError(
            "SEAT_PLUGIN_UNLOADABLE",
            f"{path.name} declares no PLUGIN; an operator plugin file names "
            "the instance it provides as a module-level PLUGIN",
        )
    return plugin


def _template_plugin(path):
    """A `.tmpl` file becomes an ordinary plugin whose render expands it.

    Its plugin id and section id come from the FILENAME
    (`<plugin-id>@<section-id>.tmpl`, or `<section-id>.tmpl` for both), so an
    operator naming a template names what it replaces -- no metadata block, no
    second syntax to learn.
    """

    from deepreason.llm.seat_templates import render_template

    stem = path.stem
    plugin_id, _, section_id = stem.partition("@")
    section_id = section_id or plugin_id
    source = path.read_text(encoding="utf-8")

    class _Template:
        parameters_model = _TemplateParams
        declared_handle_kinds: tuple[str, ...] = ()

        def __init__(self):
            self.plugin_id = plugin_id
            self.plugin_version = "1.0.0"
            self.section_id = section_id

        def render(self, request, params):
            context = {
                "supplied": dict(request.supplied),
                **{
                    key: value
                    for key, value in request.supplied.items()
                    if isinstance(value, (str, int, float, bool, list, tuple, dict))
                },
            }
            text = render_template(source, context)
            if not text.strip():
                return None
            return SectionRenderV1(section_id=self.section_id, text=text)

    return _Template()


# ---------------------------------------------------------------------------
# The seat shell — the pairing that IS a seat kind.
#
# "A seat is a shell: its input and its output define it" (CLAUDE.md,
# 2026-09-03). What makes a seat a conjecturer or a critic is the BRIEF it is
# shown and the FORM it is asked to fill, so a seat kind is a registered
# pairing of a layout, a form and a wording -- never a code path with the
# seat's name on it. Binding the conjecturer's pairing where the critic's is
# bound is therefore a registry lookup, which is what
# `tests/test_seat_shell_swap.py` demonstrates.
#
# R22 and R23 -- "conjecturers will need to be split in two", "criticism will
# need two different types" -- are why this exists. Each is a THIRD registered
# pairing when the operator says what the two kinds are; neither is built here.
#
# NO SCORE, RANK, WEIGHT, CONFIDENCE, PRIORITY OR AUTHORITY FIELD. The shell
# is the generation side; shape may never buy standing on the evidence side
# (the formalism-optional law, and the criticism-source socket's own
# standard). `tests/test_seat_section_architecture.py` goes red if one appears.
# ---------------------------------------------------------------------------

SEAT_SHELL_ENV = "DEEPREASON_SEAT_SHELL"


class SeatShellV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    shell_id: str = Field(min_length=1, max_length=96)
    shell_version: str = Field(default="1.0.0", min_length=1)
    seat_id: str = Field(min_length=1, max_length=64)
    layout_id: str = Field(min_length=1, max_length=96)
    form_id: str = Field(min_length=1, max_length=96)
    role_prompt_template_id: str = Field(min_length=1, max_length=96)


_SHELL_REGISTRY: dict[str, SeatShellV1] = {}
_DEFAULT_SHELL_FOR_SEAT: dict[str, str] = {}


def register_seat_shell(
    shell: SeatShellV1, *, default_for_seat: str | None = None
) -> SeatShellV1:
    existing = _SHELL_REGISTRY.get(shell.shell_id)
    if existing is not None and existing != shell:
        raise SeatSectionError(
            "SEAT_SHELL_CONFLICT",
            f"shell id {shell.shell_id!r} is already registered with "
            "different values",
        )
    _SHELL_REGISTRY[shell.shell_id] = shell
    if default_for_seat is not None:
        _DEFAULT_SHELL_FOR_SEAT[default_for_seat] = shell.shell_id
    return shell


def seat_shell_ids() -> tuple[str, ...]:
    return tuple(sorted(_SHELL_REGISTRY))


def resolve_seat_shell(seat_id: str, shell_id: str | None = None) -> SeatShellV1:
    """Explicit argument, then `DEEPREASON_SEAT_SHELL`, then the seat's
    default. Never `Config`, never the manifest -- decision (1) of SPEC §13.

    Selecting a shell emits no refusal: the ungated-seats law says any model
    may sit in any seat and no flag may gate a seat-configuration path. An
    UNREGISTERED id is refused at the point of use, which is the
    all-configurations law's own shape -- impossibility surfaces where it
    bites, not at compile.
    """

    import os

    from deepreason.llm.seat_plugins import ensure_seeded

    ensure_seeded()
    requested = shell_id
    if requested is None:
        raw = os.environ.get(SEAT_SHELL_ENV) or ""
        if raw.strip():
            requested = _environment_assignments(raw).get(seat_id)
    if requested is None:
        requested = _DEFAULT_SHELL_FOR_SEAT.get(seat_id)
    if requested is None:
        raise SeatSectionError(
            "SEAT_SHELL_NO_DEFAULT",
            f"no default shell for seat {seat_id!r}; registered: "
            + ", ".join(seat_shell_ids()),
        )
    shell = _SHELL_REGISTRY.get(requested)
    if shell is None:
        raise SeatSectionError(
            "SEAT_SHELL_UNKNOWN",
            f"no seat shell {requested!r}; registered: "
            + ", ".join(seat_shell_ids()),
        )
    return shell
