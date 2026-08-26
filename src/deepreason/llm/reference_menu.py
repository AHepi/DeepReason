"""Reference menus: one authority for every legal handle set.

A reference-bearing field is one whose value must NAME something that
already exists -- an evidence block id, a scratch handle, an artifact
alias. Across 54 committed roots, 737 of the 1 178 field-attributed
diagnostics in the record (62.6%) are a handle the model made up
(`experiments/2026-08-26-run-anatomy-program/W1-form-census/RESULTS.md`
section 2). Told in prose that omission was legal, seats invented a handle
anyway in 255 of 257 announced cases; where an escape lives in the
VOCABULARY instead -- `claim_class`'s `unknown` -- models take it. So the
legal set is rendered as a menu at the point of choice, and the omission
form is entry [0] of it rather than a sentence beside it.

Three layers, per the operator design law of 2026-08-26 and the pattern
`DR-INV-signal-contract` establishes (`docs/map/INV-reference-menu.md`):

FROZEN     one resolver per field, consumed through this interface by both
           the prompt menu and the repair diagnostic; a menu is
           PRESENTATION and never validity; no silent truncation.
VERSIONED  `REFERENCE_FIELD_DECLARATIONS` and `MenuRenderPolicy`.
FREE       the policy's parameter values inside their envelopes.

The FROZEN layer's middle clause is the one to guard hardest: it is the
harness's oldest invariant -- measures never adjudicate -- wearing this
module's clothes. A menu changes what the model is SHOWN. Nothing here may
change what the validators ACCEPT.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Any, Protocol, runtime_checkable

from deepreason.packs.allocate import approximate_tokens

__all__ = [
    "DEFAULT_MENU_POLICY",
    "INDEX_REPLY_GUIDANCE",
    "LegalHandleSet",
    "LegalHandleSource",
    "MenuBinding",
    "MenuEntry",
    "MenuRender",
    "MenuRenderPolicy",
    "OMISSION",
    "REFERENCE_FIELD_DECLARATIONS",
    "ReferenceFieldDeclaration",
    "declaration_for",
    "declarations_for_contract",
    "handle_source",
    "legal_handles_for",
    "menu_entries",
    "menu_renders_for",
    "register_handle_source",
    "register_reference_field",
    "render_reference_menu",
    "resolve_index_reply",
    "unregister_handle_source",
    "unregister_reference_field",
]


# --------------------------------------------------------------------------
# FREE -- parameter values inside declared envelopes.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MenuRenderPolicy:
    """How a menu is laid out. Presentation only, by construction: nothing
    here is read by any validator.

    `maximum_entries` is not a new number. 32 is what the repair
    diagnostic already truncated its legal-handle list to
    (`_MAX_DIAGNOSTIC_LEGAL_HANDLES`) and what `citable_legend` already
    caps its block list at, so the menu inherits a bound the tree chose
    rather than introducing a third one.
    """

    inline_threshold: int = 12
    maximum_entries: int = 32

    def __post_init__(self) -> None:
        if self.inline_threshold < 1 or self.maximum_entries < 1:
            raise ValueError("menu policy bounds must be positive")
        if self.inline_threshold > self.maximum_entries:
            raise ValueError("inline_threshold may not exceed maximum_entries")


DEFAULT_MENU_POLICY = MenuRenderPolicy()


# --------------------------------------------------------------------------
# The interface: a source of legal handles, keyed by handle kind.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MenuBinding:
    """The call-local facts a menu is built from.

    Every field defaults empty so a caller holding none of a kind produces
    no menu rather than an error -- the all-configurations law applied to
    presentation: a topology that cannot supply a handle set renders
    nothing, it does not die.
    """

    citable_block_ids: tuple[str, ...] = ()
    scratch_handles: tuple[str, ...] = ()
    new_block_keys: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    render_receipt: Any | None = None


@runtime_checkable
class LegalHandleSource(Protocol):
    """What may this kind of field contain, given one call's binding.

    `grammar` is the field's own value grammar, and it is part of the
    interface rather than an implementation detail: `resolve_index_reply`
    is safe only because no index token matches any registered grammar,
    and that property is checkable exactly because each source states it.
    """

    grammar: str

    def handles(self, binding: MenuBinding) -> tuple[str, ...]: ...


class CitableBlockHandles:
    """Block ids the run's evidence checker will actually resolve.

    Sourced from `CitableLegend.shown` rather than from the blocks a run
    holds: rendering drops a block whose bytes cannot be recovered, and a
    menu built from the input list would offer handles the checker rejects.
    """

    grammar = r"^[0-9a-f]{12,64}$"

    def handles(self, binding: MenuBinding) -> tuple[str, ...]:
        return tuple(dict.fromkeys(binding.citable_block_ids))


class ScratchLocalHandles:
    """The visible SCR catalog plus this proposal's own NEW keys.

    New keys come first: a link into a block the same turn is authoring is
    the commonest legal reference, and it is the one a model is least
    likely to believe it may use.
    """

    grammar = r"^(?:SCR|NEW)_[0-9]{3,}$"

    def handles(self, binding: MenuBinding) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys((*binding.new_block_keys, *_scratch_catalog(binding)))
        )


class ScratchExistingHandles:
    """Only the visible SCR catalog.

    A revision targets a block that already exists, so a NEW key is not a
    legal target here. Keeping this a separate KIND rather than a flag on
    the declaration is what lets the difference be stated once, in the
    registry, instead of re-derived at each consumer.
    """

    grammar = r"^SCR_[0-9]{3,}$"

    def handles(self, binding: MenuBinding) -> tuple[str, ...]:
        return tuple(dict.fromkeys(_scratch_catalog(binding)))


class ArtifactAliasHandles:
    """The call-local alias table, which never leaves the process.

    The table is derived from the RENDERED pack, so a menu of this kind
    cannot exist before allocation -- see `DR-SEAM-llm-x-rules` on
    re-wrapping post-allocation appends in `AllocatedPack`.
    """

    grammar = r"^(?:A[0-9]+|SRC_[0-9]{3,})$"

    def handles(self, binding: MenuBinding) -> tuple[str, ...]:
        return tuple(dict.fromkeys(binding.aliases))


def _scratch_catalog(binding: MenuBinding) -> tuple[str, ...]:
    """Scratch handles in handle-INDEX order, never key order.

    Where the call carries a render receipt, that receipt's own
    `ordered_refs` accessor is the authority -- CLAUDE.md's ledgered
    invariant, verbatim: handle maps reload key-sorted (B1, B10, B2, ...),
    so comparison goes by handle index and never through `.values()`.
    Where there is no receipt the same discipline is applied directly by
    sorting on the handle's numeric index.
    """

    receipt = binding.render_receipt
    if receipt is not None:
        try:
            ordered = receipt.ordered_refs("block")
        except Exception:  # noqa: BLE001 - presentation never fails a pack
            ordered = ()
        if ordered:
            mapping = receipt.alias_map("block")
            by_target = {target: handle for handle, target in mapping.items()}
            handles = tuple(
                by_target[target] for target in ordered if target in by_target
            )
            if handles:
                return handles
    return tuple(sorted(binding.scratch_handles, key=_handle_sort_key))


def _handle_sort_key(handle: str) -> tuple[str, int, str]:
    """Sort SCR_002 before SCR_010, and both before SCR_0100.

    A lexicographic sort puts SCR_010 before SCR_002 the moment the corpus
    grows past nine, which is the exact shape of the ledgered
    `ordered_refs` trap.
    """

    match = re.match(r"^([A-Za-z_]+)([0-9]+)$", handle)
    if match is None:
        return (handle, 0, handle)
    return (match.group(1), int(match.group(2)), handle)


_HANDLE_SOURCES: dict[str, LegalHandleSource] = {
    "citable_block": CitableBlockHandles(),
    "scratch_local": ScratchLocalHandles(),
    "scratch_existing": ScratchExistingHandles(),
    "artifact_alias": ArtifactAliasHandles(),
}


def register_handle_source(kind: str, source: LegalHandleSource) -> None:
    """Add a kind of legal-handle source. The extension point for a new
    subsystem: a consumer is never taught about one."""

    if not kind or not isinstance(getattr(source, "grammar", None), str):
        raise ValueError(f"handle source declaration incomplete: {kind!r}")
    _HANDLE_SOURCES[kind] = source


def unregister_handle_source(kind: str) -> None:
    _HANDLE_SOURCES.pop(kind, None)


def handle_source(kind: str) -> LegalHandleSource:
    try:
        return _HANDLE_SOURCES[kind]
    except KeyError as exc:
        raise ValueError(f"unregistered handle kind {kind!r}") from exc


# --------------------------------------------------------------------------
# VERSIONED -- the registry of reference-bearing fields.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ReferenceFieldDeclaration:
    """One reference-bearing field's contract.

    Both omission spellings live here because a first ask has no patch to
    remove from and a repair does: one escape road, two sentences, one
    owner. Split between two authors is how the road gets spelled two ways.
    """

    contract: str
    pointer: str
    handle_kind: str
    omission_legal: bool
    omission_first_ask: str
    omission_repair: str

    def __post_init__(self) -> None:
        if not self.contract or not self.pointer.startswith("/"):
            raise ValueError(f"reference field declaration incomplete: {self!r}")
        if self.handle_kind not in _HANDLE_SOURCES:
            raise ValueError(f"unregistered handle kind {self.handle_kind!r}")
        if self.omission_legal and not (
            self.omission_first_ask.strip() and self.omission_repair.strip()
        ):
            raise ValueError(
                f"{self.field_id}: omission is legal but unspelled; an escape "
                f"road stated only as prose advice is the one the record "
                f"measured seats declining to take"
            )

    @property
    def field_id(self) -> str:
        return f"{self.contract}:{self.pointer}"

    @property
    def field_name(self) -> str:
        return self.pointer.rstrip("/*").rsplit("/", 1)[-1]

    @property
    def section_id(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.pointer.lower()).strip("-")
        return f"reference-menu-{slug}"


def _declare(*declarations: ReferenceFieldDeclaration) -> dict:
    return {declaration.field_id: declaration for declaration in declarations}


_V6 = "conjecturer.turn.v6"
_BATCH_CRITIC = "batch-critic.v2"

# The five census-attested failing fields (W1 section 2: 244, 230, 129, 70
# and 64 diagnostics, 737 of the 1 178 the record can pin on a field) plus
# the siblings that share their namespace and cost nothing to cover.
#
# `omission_legal` MIRRORS the validators, it does not decide for them: it
# is true exactly where `repair.py` already records
# `omission_or_unknown_legal`, which is array fields and the proposal root.
# A scalar link endpoint stays false because dropping it alone leaves a
# malformed link -- the legal repair there removes the whole link.
REFERENCE_FIELD_DECLARATIONS: dict[str, ReferenceFieldDeclaration] = _declare(
    ReferenceFieldDeclaration(
        contract=_V6,
        pointer="/candidates/*/evidence_refs/*/block",
        handle_kind="citable_block",
        omission_legal=True,
        omission_first_ask=(
            'OMIT -- leave "evidence_refs" out of this candidate entirely. '
            "This is a legal, complete answer; prefer it to a guess."
        ),
        omission_repair=(
            "OMIT -- write a remove operation at this candidate's "
            '"evidence_refs", or a replace that drops the offending entry. '
            "Never invent a handle to fill an optional reference."
        ),
    ),
    ReferenceFieldDeclaration(
        contract=_V6,
        pointer="/candidates/*/optional_refs/*",
        handle_kind="artifact_alias",
        omission_legal=True,
        omission_first_ask=(
            'OMIT -- leave "optional_refs" empty for this candidate. '
            "A candidate that names no neighbour is a complete candidate."
        ),
        omission_repair=(
            'OMIT -- write a remove operation at this candidate\'s '
            '"optional_refs", or a replace that drops the offending entry.'
        ),
    ),
    ReferenceFieldDeclaration(
        contract=_V6,
        pointer="/candidates/*/neighbours/*",
        handle_kind="artifact_alias",
        omission_legal=True,
        omission_first_ask=(
            'OMIT -- leave "neighbours" empty for this candidate. '
            "A candidate that names no neighbour is a complete candidate."
        ),
        omission_repair=(
            'OMIT -- write a remove operation at this candidate\'s '
            '"neighbours", or a replace that drops the offending entry.'
        ),
    ),
    ReferenceFieldDeclaration(
        contract=_V6,
        pointer="/scratch_proposal/unresolved_questions/*/related_refs",
        handle_kind="scratch_local",
        omission_legal=True,
        omission_first_ask=(
            'OMIT -- leave "related_refs" empty for this question. '
            "A question that relates to nothing yet is a legal question."
        ),
        omission_repair=(
            'OMIT -- write a remove operation at this question\'s '
            '"related_refs", or a replace that drops the offending entry.'
        ),
    ),
    ReferenceFieldDeclaration(
        contract=_V6,
        pointer="/scratch_proposal/cluster_suggestions/*/member_refs",
        handle_kind="scratch_local",
        omission_legal=True,
        omission_first_ask=(
            'OMIT -- leave "member_refs" empty, or propose no cluster at all.'
        ),
        omission_repair=(
            'OMIT -- write a remove operation at this suggestion\'s '
            '"member_refs", or a replace that drops the offending entry.'
        ),
    ),
    ReferenceFieldDeclaration(
        contract=_V6,
        pointer="/scratch_proposal/links/*/to_ref",
        handle_kind="scratch_local",
        omission_legal=False,
        omission_first_ask="",
        omission_repair="",
    ),
    ReferenceFieldDeclaration(
        contract=_V6,
        pointer="/scratch_proposal/links/*/from_ref",
        handle_kind="scratch_local",
        omission_legal=False,
        omission_first_ask="",
        omission_repair="",
    ),
    ReferenceFieldDeclaration(
        contract=_V6,
        pointer="/scratch_proposal/revisions/*/target_alias",
        handle_kind="scratch_existing",
        omission_legal=False,
        omission_first_ask="",
        omission_repair="",
    ),
    ReferenceFieldDeclaration(
        contract=_BATCH_CRITIC,
        pointer="/cases/*/premise_evidence/*/block",
        handle_kind="citable_block",
        omission_legal=True,
        omission_first_ask=(
            'OMIT -- leave "premise_evidence" out of this case entirely. '
            "Declining costs you nothing and never weakens your case."
        ),
        omission_repair=(
            'OMIT -- write a remove operation at this case\'s '
            '"premise_evidence", or a replace that drops the offending entry.'
        ),
    ),
    ReferenceFieldDeclaration(
        contract=_BATCH_CRITIC,
        pointer="/cases/*/target_alias",
        handle_kind="artifact_alias",
        omission_legal=False,
        omission_first_ask="",
        omission_repair="",
    ),
)


def register_reference_field(declaration: ReferenceFieldDeclaration) -> None:
    """Give a field a menu. The whole extension point: no renderer edit."""

    REFERENCE_FIELD_DECLARATIONS[declaration.field_id] = declaration


def unregister_reference_field(field_id: str) -> None:
    REFERENCE_FIELD_DECLARATIONS.pop(field_id, None)


def declaration_for(field_id: str) -> ReferenceFieldDeclaration | None:
    return REFERENCE_FIELD_DECLARATIONS.get(field_id)


def declarations_for_contract(contract: str) -> tuple[ReferenceFieldDeclaration, ...]:
    return tuple(
        declaration
        for declaration in REFERENCE_FIELD_DECLARATIONS.values()
        if declaration.contract == contract
    )


# --------------------------------------------------------------------------
# FROZEN -- the one authority, and the one renderer over it.
# --------------------------------------------------------------------------


class _Omission:
    """The sentinel an index-0 reply resolves to: absence, chosen."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "OMISSION"


OMISSION = _Omission()

INDEX_REPLY_GUIDANCE = (
    "You may answer with the handle itself or with its [index]."
)

_INDEX_REPLY = re.compile(r"^\s*(?:#|\[)?\s*([0-9]{1,3})\s*\]?\s*$")


@dataclass(frozen=True)
class MenuEntry:
    index: int
    text: str
    is_omission: bool = False


@dataclass(frozen=True)
class LegalHandleSet:
    """What one field may contain on one call. THE authority.

    Both the prompt menu and the repair diagnostic are renderings of this
    one value, which is what makes "the diagnostic's list is identical to
    the menu shown" a property of the code rather than of two authors'
    diligence.
    """

    field_id: str
    handles: tuple[str, ...]
    total: int
    truncated: bool
    omission_legal: bool

    @property
    def shown(self) -> int:
        return len(self.handles)

    def handle_at(self, index: int) -> str | None:
        if index < 1 or index > len(self.handles):
            return None
        return self.handles[index - 1]

    def index_of(self, handle: str) -> int | None:
        try:
            return self.handles.index(handle) + 1
        except ValueError:
            return None


def legal_handles_for(
    field_id: str,
    binding: MenuBinding,
    *,
    policy: MenuRenderPolicy = DEFAULT_MENU_POLICY,
) -> LegalHandleSet | None:
    """The ONE resolver. Every legal set in the harness comes from here.

    Returns None for an undeclared field, which is how a consumer asks
    "does this field have a menu?" without knowing the registry's shape.
    """

    declaration = REFERENCE_FIELD_DECLARATIONS.get(field_id)
    if declaration is None:
        return None
    handles = tuple(handle_source(declaration.handle_kind).handles(binding))
    shown = handles[: policy.maximum_entries]
    return LegalHandleSet(
        field_id=field_id,
        handles=shown,
        total=len(handles),
        truncated=len(shown) < len(handles),
        omission_legal=declaration.omission_legal,
    )


def menu_entries(
    field_id: str,
    binding: MenuBinding,
    *,
    policy: MenuRenderPolicy = DEFAULT_MENU_POLICY,
) -> tuple[MenuEntry, ...]:
    """The menu's items, omission first where it is legal.

    Index 0 is the escape and indices count from 1 for handles, so a
    handle's index is stable whether or not the field permits omission --
    a seat cannot be taught one numbering on one field and another on the
    next.
    """

    legal = legal_handles_for(field_id, binding, policy=policy)
    if legal is None:
        return ()
    declaration = REFERENCE_FIELD_DECLARATIONS[field_id]
    entries: list[MenuEntry] = []
    if legal.omission_legal:
        entries.append(
            MenuEntry(index=0, text=declaration.omission_first_ask, is_omission=True)
        )
    entries.extend(
        MenuEntry(index=position, text=handle)
        for position, handle in enumerate(legal.handles, start=1)
    )
    return tuple(entries)


@dataclass(frozen=True)
class MenuRender:
    """One rendered menu, with its cost stated in the token economy's own
    unit and its truncation stated INSIDE its text.

    Truncation is disclosed in `text` rather than beside it so that no
    consumer can carry the menu without the fact that it is partial -- the
    no-silent-caps rule of `DR-CON-packs-and-token-economy` applied to a
    new section family.
    """

    field_id: str
    section_id: str
    text: str
    tokens: int
    total: int
    shown: int
    truncated: bool
    inline: bool


def render_reference_menu(
    field_id: str,
    binding: MenuBinding,
    *,
    policy: MenuRenderPolicy = DEFAULT_MENU_POLICY,
) -> MenuRender | None:
    """Render one field's menu, or None when the field has no handles.

    Nothing in here may name a field: a new reference-bearing field gets a
    menu by registering a declaration, never by an edit to this function.
    """

    legal = legal_handles_for(field_id, binding, policy=policy)
    if legal is None or not legal.handles:
        return None
    declaration = REFERENCE_FIELD_DECLARATIONS[field_id]
    entries = menu_entries(field_id, binding, policy=policy)
    inline = legal.shown <= policy.inline_threshold
    lines = [
        f"REFERENCE MENU -- {declaration.pointer}",
        "Choose a value for this field from this list ONLY. Any value not "
        "listed is rejected; do not write a handle that is not here.",
    ]
    if not inline:
        lines.append(f"  idx  handle ({legal.shown} legal values)")
    for entry in entries:
        lines.append(f"  [{entry.index}] {entry.text}")
    if legal.truncated:
        lines.append(
            f"  (+{legal.total - legal.shown} further legal handles not shown "
            f"-- this menu was truncated to fit the pack budget; the full "
            f"legal set is larger than what is listed here.)"
        )
    lines.append(INDEX_REPLY_GUIDANCE)
    text = "\n".join(lines)
    return MenuRender(
        field_id=field_id,
        section_id=declaration.section_id,
        text=text,
        tokens=approximate_tokens(text),
        total=legal.total,
        shown=legal.shown,
        truncated=legal.truncated,
        inline=inline,
    )


def menu_renders_for(
    contract: str,
    binding: MenuBinding,
    *,
    policy: MenuRenderPolicy = DEFAULT_MENU_POLICY,
    handle_kinds: tuple[str, ...] | None = None,
) -> tuple[MenuRender, ...]:
    """Every declared menu for one contract, in registry order.

    `handle_kinds` narrows the selection for callers that must render in
    two passes -- an artifact-alias menu cannot exist until after pack
    allocation, because the alias table is derived from the rendered pack.
    """

    renders = []
    for declaration in declarations_for_contract(contract):
        if handle_kinds is not None and declaration.handle_kind not in handle_kinds:
            continue
        render = render_reference_menu(declaration.field_id, binding, policy=policy)
        if render is not None:
            renders.append(render)
    return tuple(renders)


def resolve_index_reply(
    field_id: str,
    value: Any,
    binding: MenuBinding,
    *,
    policy: MenuRenderPolicy = DEFAULT_MENU_POLICY,
) -> Any:
    """Turn a seat's `[2]` into the handle the menu showed at index 2.

    Returns the value UNCHANGED unless it is an index token for a field
    that has a menu, so this can never capture a value that would have
    been valid: no registered field's own grammar admits a bare integer,
    and `tests/test_reference_menu.py` pins that over the whole registry.
    Index 0 resolves to `OMISSION` where the field permits it -- the escape
    road taken structurally rather than advised.
    """

    if not isinstance(value, str):
        return value
    match = _INDEX_REPLY.fullmatch(value)
    if match is None:
        return value
    legal = legal_handles_for(field_id, binding, policy=policy)
    if legal is None or not legal.handles:
        return value
    index = int(match.group(1))
    if index == 0:
        return OMISSION if legal.omission_legal else value
    resolved = legal.handle_at(index)
    return value if resolved is None else resolved
