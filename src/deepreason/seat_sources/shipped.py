"""The shipped section sources, and the conjecturer's default bundle.

Each source below is one block of `rules/conj.py` moved out whole. The move is
MECHANICAL by design: where a faithful extraction and a tidier rewrite differ,
the extraction wins, because the only evidence that thirteen extractions
extracted rather than rewrote is that both seats' default briefs still render
byte-for-byte what they rendered before
(`tests/test_conj_pack_legacy_golden.py`).

`seat_plugins.py` is the sibling to read first: it seeds the plugins that
FORMAT a section. These seed the sources that COMPUTE what those plugins are
handed, for the nine slots a plugin cannot reach because their content needs
the record.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from deepreason.seat_sources.registry import (
    STAGE_POST_ALLOCATION,
    STAGE_POST_ALLOCATION_AFTER_ALIASES,
    STAGE_POST_ALLOCATION_CONTEXT,
    STAGE_PRE_CONTRACT,
    STAGE_RENDER,
    SeatSourceBundleEntryV1,
    SeatSourceBundleV1,
    SectionSourceRequestV1,
    SectionSourceResultV1,
    register_seat_source_bundle,
    register_section_source,
)

CONJECTURER_SEAT = "conjecturer"
CONJECTURER_SOURCE_BUNDLE = "conj-sources.legacy-v0"


class _NoParams(BaseModel):
    """Most sources have no knobs: what they compute is decided by the run,
    not by a value someone set. A source that grows one declares its own
    model, exactly as a plugin does."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class _Source:
    """Shared shape. Subclasses set the four class attributes and `resolve`."""

    parameters_model = _NoParams
    requires: tuple[str, ...] = ()
    writes_blobs = False

    def __init__(self, source_id: str, source_version: str, supplies: str) -> None:
        self.source_id = source_id
        self.source_version = source_version
        self.supplies = supplies


def _result(source: _Source, **fields: Any) -> SectionSourceResultV1:
    return SectionSourceResultV1(supplies=source.supplies, **fields)


# ---------------------------------------------------------------------------
# pre_contract — the one value the caller needs before it builds the turn
# contract.
# ---------------------------------------------------------------------------


class _OpenCriticismSource(_Source):
    """The open criticisms on this problem, as the discharge channel's own
    bounded view.

    Resolved BEFORE the contract rather than beside the pack because the
    atomic-decomposition recovery path builds its contract long before the
    pack renders, and a contract that pruned `discharges` while the pack it
    answers listed open handles would ask the model for something it cannot
    express. It is a pure read: no event, no label.
    """

    def resolve(self, request, params):
        from deepreason.discharge import (
            render_open_criticism_context,
        )
        from deepreason.discharge import (
            resolve_policy as resolve_discharge_policy,
        )

        policy = resolve_discharge_policy(request.config)
        text = render_open_criticism_context(
            request.harness, request.lookup("problem_id"), policy
        )
        return _result(
            self, value=text, carries={"discharge_enabled": bool(text)}
        )


# ---------------------------------------------------------------------------
# render — the eight values the renderer is handed.
# ---------------------------------------------------------------------------


def _union_blocks(dossiers) -> tuple:
    """Every admitted block across the run's bound dossiers, epoch order."""

    blocks: list = []
    known: set[str] = set()
    for dossier in dossiers:
        for block in getattr(dossier, "blocks", ()) or ():
            if block.id in known:
                continue
            known.add(block.id)
            blocks.append(block)
    return tuple(blocks)


class _FrozenEvidenceSource(_Source):
    """The attached-evidence dossier pack: selection, materialisation, render.

    THE ONE SOURCE THAT WRITES, and it writes only content-addressed blobs:
    `pack_dossier` materialises the excerpts it selected before the receipt
    can name them. It appends no event. The receipt it builds is CARRIED, not
    committed -- committing is a record-side act and stays with the caller,
    which is where the boundary between this layer and the authority layer
    falls.

    Amendment epochs make evidence cumulative: any epoch's question may be
    selected, and every one of them reasons against every dossier bound so
    far.
    """

    writes_blobs = True

    def resolve(self, request, params):
        harness = request.harness
        active_v5 = bool(request.lookup("active_v5"))
        active_v6 = bool(request.lookup("active_v6"))
        if not (active_v5 or active_v6):
            return None

        from deepreason.amendment.state import dossier_union, epoch_problem_ids
        from deepreason.evidence import (
            dossier_exposure_counts,
            load_evidence_dossier,
            load_run_input,
            pack_dossier,
            render_dossier_pack,
        )

        run_manifest = request.run_manifest
        evidence_policy = run_manifest.inquiry_capability_policy.attached_evidence
        if not evidence_policy.enabled:
            return None
        bound_input = load_run_input(harness.root)
        dossier = load_evidence_dossier(harness.root)
        if bound_input.run_input_digest != run_manifest.run_input_digest:
            raise ValueError("conjecture evidence belongs to another run input")
        bound_dossiers = dossier_union(harness.root)
        addressed = bool(bound_dossiers) and request.problem.id in epoch_problem_ids(
            harness.root
        )
        seen_source_ids = {source.id for source in dossier.sources}
        supplemental: list = []
        for item in bound_dossiers:
            if item.dossier_digest == dossier.dossier_digest:
                continue
            for source in item.sources:
                if source.id in seen_source_ids:
                    continue
                seen_source_ids.add(source.id)
                supplemental.append(source)
        supplemental_sources = tuple(supplemental)
        carries: dict[str, Any] = {
            "bound_dossiers": bound_dossiers,
            "bound_dossier": None,
            "dossier_receipt": None,
            "dossier_maximum_bytes": 0,
        }
        if not addressed:
            return _result(self, value=None, carries=carries)
        work_order = request.lookup("work_order")
        maximum_bytes = min(
            evidence_policy.maximum_total_bytes,
            evidence_policy.maximum_sources_per_pack
            * evidence_policy.maximum_excerpt_bytes_per_source,
            4 * 1024 * 1024,
        )
        fence_seq = (
            harness._next_seq - 1 if active_v6 else work_order.formal_fence_seq
        )
        scratch_seq = (
            harness._next_seq - 1 if active_v6 else work_order.scratch_fence_seq
        )
        receipt = pack_dossier(
            root=harness.root,
            run_input=bound_input,
            dossier=dossier,
            work_order_ref=(
                request.lookup("transaction_preparation_id")
                if active_v6
                else work_order.id
            ),
            query=request.problem.description,
            state_fence=(
                f"formal:{fence_seq};"
                f"scratch:{scratch_seq};"
                f"workflow:{harness.workflow_state.digest}"
            ),
            maximum_sources=evidence_policy.maximum_sources_per_pack,
            maximum_excerpt_bytes_per_source=(
                evidence_policy.maximum_excerpt_bytes_per_source
            ),
            maximum_total_excerpt_bytes=maximum_bytes,
            exposure_counts=dossier_exposure_counts(harness),
            additional_sources=supplemental_sources,
        )
        carries.update(
            {
                "bound_dossier": dossier,
                "dossier_receipt": receipt,
                "dossier_maximum_bytes": maximum_bytes,
            }
        )
        text = render_dossier_pack(
            blobs=harness.blobs,
            dossier=dossier,
            receipt=receipt,
            dossiers=bound_dossiers,
        )
        return _result(self, value=text, carries=carries)


class _CitableEvidenceSource(_Source):
    """The legend of blocks a candidate may name in `evidence_refs`.

    Deliberately NOT gated on whether THIS problem is an epoch problem. The
    dossier is bound to the RUN, and gating the legend on the epoch binding
    left every derived problem reasoning about the run's evidence while unable
    to name a single block the checker resolves.
    """

    def resolve(self, request, params):
        if not (request.lookup("active_v5") or request.lookup("active_v6")):
            return None
        from deepreason.capabilities.research import consumed_research_blocks
        from deepreason.evidence import citable_legend

        legend = citable_legend(
            _union_blocks(request.lookup("bound_dossiers") or ())
            + consumed_research_blocks(request.harness),
            request.harness.blobs,
        )
        if legend is None:
            return _result(self, value=None, carries={"citable_blocks_shown": ()})
        return _result(
            self,
            value=legend.text,
            carries={"citable_blocks_shown": legend.shown},
        )


class _FrameSliceSource(_Source):
    """For every consulted assertion whose sigma admits this problem, its
    articulation digest and its standing attackers."""

    def resolve(self, request, params):
        from deepreason.calculus.render import render_frame_slice_context

        return _result(
            self,
            value=render_frame_slice_context(
                request.harness, request.lookup("problem_id")
            ),
        )


class _FrameCrisisSource(_Source):
    """The crisis half of the frame. Two values rather than one because the
    wounds are rendered EXACT while the digest is compressible."""

    def resolve(self, request, params):
        from deepreason.calculus.render import render_frame_crisis_context

        return _result(
            self,
            value=render_frame_crisis_context(
                request.harness, request.lookup("problem_id")
            ),
        )


class _PassThroughSource(_Source):
    """A value the CALLER already holds, routed to its section by this bundle.

    Three of the thirteen are of this kind, and they earn their place for the
    reason the layer exists: which input feeds which section is now a
    registered decision. A different bundle can feed the same slot from
    somewhere else without any consumer learning about it.
    """

    def __init__(self, source_id, source_version, supplies, input_key):
        super().__init__(source_id, source_version, supplies)
        self.input_key = input_key

    def resolve(self, request, params):
        return _result(self, value=request.lookup(self.input_key))


class _ScratchContextSource(_Source):
    """The transaction's own context plan, as the seat is shown it.

    The plan is issued BEFORE the call, so its rendered context is the one
    thing in the brief that exists before anything is rendered.
    """

    def resolve(self, request, params):
        plan = request.lookup("conjecture_context_plan")
        if plan is None:
            return None
        return _result(self, value=plan.rendered_context)


class _ReferenceMenusSource(_Source):
    """The legal handle set, for the kinds whose handles exist BEFORE
    allocation.

    Only `citable_block` here. The artifact-alias menu cannot be built yet:
    its alias table is DERIVED from the rendered pack, so a menu built at this
    point would name handles that do not exist.
    """

    def resolve(self, request, params):
        if not request.lookup("active_v6"):
            return _result(self, value=())
        from deepreason.llm import reference_menu

        binding = reference_menu.MenuBinding(
            citable_block_ids=tuple(
                block.id for block in (request.lookup("citable_blocks_shown") or ())
            ),
        )
        return _result(
            self,
            value=reference_menu.menu_renders_for(
                "conjecturer.turn.v6", binding, handle_kinds=("citable_block",)
            ),
        )


# ---------------------------------------------------------------------------
# post_allocation — text applied to a pack the allocator has already budgeted.
# ---------------------------------------------------------------------------


class _ScratchRenderSource(_Source):
    """The v6 scratch render, substituted in place of its canonical text.

    A SUBSTITUTION rather than an append, because the canonical text is what
    the allocator budgeted and the rendered text is what the seat must see;
    the runner refuses a substitution whose target is not present exactly
    once, which is the check this block carried before it moved.
    """

    def resolve(self, request, params):
        plan = request.lookup("conjecture_context_plan")
        if not request.lookup("active_v6") or plan is None:
            return None
        from deepreason.scratch.conjecture import render_v6_conjecture_context

        text, aliases = render_v6_conjecture_context(plan)
        return _result(
            self,
            text=text,
            substitutes=plan.rendered_context.text,
            carries={
                "scratch_aliases": aliases,
                "v6_scratch_rendered_text": text,
            },
        )


class _SealedSimulationSource(_Source):
    """The simulation inputs, sealed: data only, addressable only by handle."""

    def resolve(self, request, params):
        if not request.lookup("active_v6"):
            return None
        policy = request.run_manifest.inquiry_capability_policy.simulation
        if not (policy.enabled and policy.input_catalog):
            return None
        from deepreason.canonical import canonical_json

        lines = [
            "",
            "SEALED SIMULATION INPUTS (data only; use only the listed SIM handles):",
        ]
        for alias, item in zip(
            request.lookup("transaction_simulation_aliases") or {},
            policy.input_catalog,
            strict=True,
        ):
            lines.append(
                f"{alias}: {item.description}\n"
                + canonical_json(item.value).decode("utf-8")
            )
        text = "\n".join(lines)
        return _result(
            self, text=text, carries={"v6_simulation_rendered_text": text}
        )


class _ScratchWorkshopSource(_Source):
    """The workshop prompt, when this run lets the seat author scratch."""

    def resolve(self, request, params):
        if not request.lookup("active_v6"):
            return None
        control = request.run_manifest.control_plane_policy
        if not control.scratch_authoring.enabled:
            return None
        from deepreason.scratch.proposals import V6_SCRATCH_WORKSHOP_PROMPT

        return _result(self, text="\n\n" + V6_SCRATCH_WORKSHOP_PROMPT)


class _PostAllocationMenusSource(_Source):
    """The menus that can only be built now.

    The alias table is derived from the rendered pack and the scratch handles
    come from the context render that happens after allocation, so the two
    menu passes are forced by ordering rather than chosen.

    Gated on the v6 path because the fields these menus describe belong to the
    v6 turn contract. An earlier version was not gated, and a pre-v6 run got a
    menu for a field its form does not have -- a menu naming a field the seat
    cannot fill is worse than no menu at all.
    """

    def resolve(self, request, params):
        if not request.lookup("active_v6"):
            return None
        from deepreason.llm import reference_menu

        aliases = request.lookup("aliases")
        menus = reference_menu.menu_renders_for(
            "conjecturer.turn.v6",
            reference_menu.MenuBinding(
                scratch_handles=tuple(request.lookup("scratch_aliases") or {}),
                aliases=tuple(aliases.aliases),
            ),
            handle_kinds=("artifact_alias", "scratch_local", "scratch_existing"),
        )
        if not menus:
            return None
        return _result(
            self,
            text="\n\n" + "\n\n".join(menu.text for menu in menus),
            carries={"post_allocation_menus": menus},
        )


# ---------------------------------------------------------------------------
# Seeding.
# ---------------------------------------------------------------------------

_SEEDED = False

_CONJECTURER_SOURCES: tuple = (
    (_OpenCriticismSource("dr.src.open_criticism", "1.0.0", "open_criticism_context"),
     STAGE_PRE_CONTRACT),
    (_FrozenEvidenceSource("dr.src.frozen_evidence", "1.0.0", "frozen_evidence_context"),
     STAGE_RENDER),
    (_CitableEvidenceSource("dr.src.citable_evidence", "1.0.0", "citable_evidence_context"),
     STAGE_RENDER),
    (_FrameSliceSource("dr.src.frame_slice", "1.0.0", "frame_slice_context"),
     STAGE_RENDER),
    (_FrameCrisisSource("dr.src.frame_crisis", "1.0.0", "frame_crisis_context"),
     STAGE_RENDER),
    (_PassThroughSource(
        "dr.src.capability_result", "1.0.0", "capability_result_context",
        "capability_result_context",
     ), STAGE_RENDER),
    (_ScratchContextSource("dr.src.scratch_context", "1.0.0", "scratch_context"),
     STAGE_RENDER),
    (_PassThroughSource(
        "dr.src.generation_context", "1.0.0", "generation_context",
        "generation_context",
     ), STAGE_RENDER),
    (_ReferenceMenusSource("dr.src.reference_menus", "1.0.0", "reference_menus"),
     STAGE_RENDER),
    (_ScratchRenderSource(
        "dr.src.post.scratch_render", "1.0.0", "scratch_render",
     ), STAGE_POST_ALLOCATION_CONTEXT),
    (_SealedSimulationSource(
        "dr.src.post.sealed_simulation", "1.0.0", "sealed_simulation_inputs",
     ), STAGE_POST_ALLOCATION),
    (_ScratchWorkshopSource(
        "dr.src.post.scratch_workshop", "1.0.0", "scratch_workshop_prompt",
     ), STAGE_POST_ALLOCATION),
    (_PostAllocationMenusSource(
        "dr.src.post.reference_menus", "1.0.0", "post_allocation_menus",
     ), STAGE_POST_ALLOCATION_AFTER_ALIASES),
)


def ensure_sources_seeded() -> None:
    """Register the shipped sources and bundle exactly once.

    Idempotent and import-time-free for the reason `ensure_seeded` is: a
    module imported twice must not be an error, and a registry populated at
    import time cannot be inspected before it is populated.
    """

    global _SEEDED
    if _SEEDED:
        return
    _SEEDED = True
    for source, _stage in _CONJECTURER_SOURCES:
        register_section_source(source)
    register_seat_source_bundle(
        SeatSourceBundleV1(
            bundle_id=CONJECTURER_SOURCE_BUNDLE,
            entries=tuple(
                SeatSourceBundleEntryV1(source_id=source.source_id, stage=stage)
                for source, stage in _CONJECTURER_SOURCES
            ),
        ),
        default_for_seat=CONJECTURER_SEAT,
    )


__all__ = [
    "CONJECTURER_SEAT",
    "CONJECTURER_SOURCE_BUNDLE",
    "SectionSourceRequestV1",
    "ensure_sources_seeded",
]
