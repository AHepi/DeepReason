"""The seeded section plugins — today's briefs, extracted, not rewritten.

Every plugin here reproduces one block of `render_conj_pack` or
`render_crit_pack` BYTE FOR BYTE at default parameters. That is the whole
point of this module and the reason it reads as a transcription rather than a
design: the acceptance test the tranche turns on is that the default render
does not move (SPEC S10.4), so a plugin that improved its section's wording
would fail the tranche rather than pass it.

Where the two seats render the SAME section, one plugin serves both and the
difference lives in the layout entry — the conjecturer carries
`citable-evidence-blocks` at priority 4 and the critic at 6, and neither bends
the plugin to do it. Where the text differs, the seats get separate ids.

Imported lazily by `llm/packs.py`: this module imports that one for the
helpers the extracted blocks call, so a module-level import there would close
the cycle. The same idiom `_simulation_contract_note` already uses.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from deepreason.llm.seat_sections import (
    SectionRenderV1,
    SectionRequestV1,
    register_section_plugin,
)

CONJECTURER_SEAT = "conjecturer"
CRITIC_SEAT = "argumentative_critic"


class NoParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _Plugin:
    """Base for a seeded plugin: an id, a version, and no knobs unless the
    subclass declares some.

    `plugin_version` moves when the DEFAULT RENDER changes, which for these is
    never without an operator-approved change to what a brief says.
    """

    plugin_id = ""
    plugin_version = "1.0.0"
    # The pack section id this plugin renders. Declared STATICALLY, not only
    # returned from `render`, so a layout's composition can be read -- and
    # checked -- without running a render.
    section_id = ""
    parameters_model: type[BaseModel] = NoParams

    def render(
        self, request: SectionRequestV1, params: BaseModel
    ) -> SectionRenderV1 | None:  # pragma: no cover - subclasses override
        raise NotImplementedError(self.plugin_id)


def _supplied(request: SectionRequestV1, key: str, default: Any = None) -> Any:
    return request.supplied.get(key, default)


def _verbatim(plugin_id: str, section_id: str, supplied_key: str):
    """A plugin whose whole job is to pass a caller-computed context through.

    Nine of the conjecturer's twenty sections and four of the critic's
    thirteen are computed in `rules/` rather than in the renderer, because
    they need a dossier receipt, a fence sequence or a work order that a
    renderer does not hold (`DR-SEAM-packs-and-token-economy-x-rules`). Their
    plugins FORMAT a value the caller supplies; A6 keeps the computation where
    it is for this tranche.
    """

    class _Verbatim(_Plugin):
        def render(self, request, params):
            text = _supplied(request, supplied_key)
            if not text:
                return None
            return SectionRenderV1(section_id=self.section_id, text=text)

    _Verbatim.plugin_id = plugin_id
    _Verbatim.section_id = section_id
    _Verbatim.__name__ = f"_Verbatim_{section_id.replace('-', '_')}"
    return _Verbatim


# ---------------------------------------------------------------------------
# The conjecturer's twenty sections, in `render_conj_pack`'s own order.
# ---------------------------------------------------------------------------


class _ProblemStatement(_Plugin):
    plugin_id = "dr.problem"
    section_id = "problem"

    def render(self, request, params):
        problem = request.problem
        return SectionRenderV1(
            section_id=self.section_id,
            text=f"PROBLEM {problem.id}\n{problem.description}",
            provenance_refs=(problem.id,),
        )


class _Criteria(_Plugin):
    plugin_id = "dr.criteria"
    section_id = "criteria"

    def render(self, request, params):
        problem = request.problem
        lines = ["CRITERIA (commitments every candidate will carry and face):"]
        for cid in problem.criteria:
            kappa = request.commitments.get(cid)
            lines.append(f"- {cid}: {kappa.eval if kappa else '(schema pending)'}")
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(lines),
            provenance_refs=tuple(problem.criteria),
        )


class _MandatoryInterface(_Plugin):
    plugin_id = "dr.mandatory-interface"
    section_id = "mandatory-interface"

    def render(self, request, params):
        from deepreason.llm.packs import _lineage_foundation

        foundation = _lineage_foundation(
            request.problem, request.state, request.commitments, request.blobs
        )
        if not foundation:
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(foundation).strip(),
            provenance_refs=tuple(request.problem.criteria),
        )


class ActivePropertiesParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_chars: int = Field(default=200, ge=16, le=4096)
    """How much of each validated standard's docstring claim is shown. 200 is
    today's value; it is a knob because "increased or shrunk at will" (R6) is
    what the operator asked the plugin layer for."""


class _ActiveProperties(_Plugin):
    plugin_id = "dr.active-properties"
    section_id = "active-properties"
    parameters_model = ActivePropertiesParams

    def render(self, request, params):
        from deepreason.llm.packs import _active_property_claims

        claims = _active_property_claims(
            request.state, request.blobs, request.problem.criteria
        )
        if not claims:
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text="ACTIVE PROPERTIES (conjectured standards the run has "
            "validated — candidates violating them are refuted by "
            "execution):\n"
            + "\n".join(f"- {c[: params.claim_chars]}" for c in claims),
        )


class _SchoolStance(_Plugin):
    plugin_id = "dr.school-stance"
    section_id = "school-stance"

    def render(self, request, params):
        school = _supplied(request, "school")
        if school is None or school.get("weight", 0) <= 0:
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text=f"SCHOOL STANCE (weight {school['weight']:.2f}): "
            f"{school['stance_text']}",
        )


class _GenerationContext(_Plugin):
    plugin_id = "dr.generation-context"
    section_id = "experimental-generation-context"

    def render(self, request, params):
        context = _supplied(request, "generation_context")
        if not context:
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text="GENERATION CONTEXT (attention only; truth, admission, and "
            "verifier standards are unchanged):\n" + context,
        )


class _ScratchAdvisory(_Plugin):
    plugin_id = "dr.scratch-advisory"
    section_id = "scratch-advisory-context"

    def render(self, request, params):
        scratch = _supplied(request, "scratch_context")
        if scratch is None:
            return None
        from deepreason.scratch.render import RenderedScratchPackV1

        scratch = RenderedScratchPackV1.model_validate(scratch)
        return SectionRenderV1(
            section_id=self.section_id, text=scratch.text
        )


class _CapabilityResult(_Plugin):
    plugin_id = "dr.capability-result"
    section_id = "capability-result-context"

    def render(self, request, params):
        context = _supplied(request, "capability_result_context")
        if not context:
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text="RECORDED SIMULATION OBSERVATION (fresh work):\n"
            "This is the output of the named program under the named inputs and "
            "execution conditions. It is not a universal fact and does not "
            "automatically establish the requesting hypothesis.\n" + context,
        )


class CitableEvidenceParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    requires_invitation: bool = False
    """The critic renders the legend only alongside the premise invitation it
    serves: a legend visible while the invitation was dropped would list ids
    nothing asked it to cite. The conjecturer has no invitation, so its entry
    leaves this false."""


class _CitableEvidence(_Plugin):
    plugin_id = "dr.evidence.citable"
    section_id = "citable-evidence-blocks"
    parameters_model = CitableEvidenceParams

    def render(self, request, params):
        context = _supplied(request, "citable_evidence_context")
        if not context:
            return None
        if params.requires_invitation and not _supplied(
            request, "premise_invitation"
        ):
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text=context,
            declared_handle_kinds=("citable_block",),
        )


class _Neighbourhood(_Plugin):
    plugin_id = "dr.neighbourhood"
    section_id = "neighbourhood"

    def render(self, request, params):
        from deepreason.llm.packs import _CARRY_FORWARD_ROUTE, _distilled

        layout = request.layout
        accepted = list(_supplied(request, "accepted", ()))
        live = list(accepted[-layout.live_verbatim_n:]) if layout.live_verbatim_n else []
        distilled_ids = [aid for aid in accepted if aid not in set(live)]
        if not distilled_ids:
            return None
        header = (
            "NEIGHBOURHOOD (accepted artifacts; carry dependence refs where natural)"
        )
        if layout.retrieval_note and layout.distil_carry_forward:
            header += f" — {_CARRY_FORWARD_ROUTE}"
        lines = [header + ":"]
        for aid in distilled_ids:
            lines.append(
                f"- {aid}: {_distilled(request.state, aid, request.blobs, layout)}"
            )
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(lines),
            provenance_refs=tuple(distilled_ids),
        )


class _LiveNeighbourhood(_Plugin):
    plugin_id = "dr.neighbourhood.live"
    section_id = "live-neighbourhood"

    def render(self, request, params):
        from deepreason.programs import content_text

        layout = request.layout
        accepted = list(_supplied(request, "accepted", ()))
        live = list(accepted[-layout.live_verbatim_n:]) if layout.live_verbatim_n else []
        if not live:
            return None
        lines = [
            "LIVE NEIGHBOURHOOD (accepted and still standing — shown whole "
            "because these are the ones to build on or beat):"
        ]
        for aid in live:
            lines.append(
                f"- {aid}: {content_text(request.state.artifacts[aid], request.blobs)}"
            )
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(lines),
            provenance_refs=tuple(live),
        )


class HistoryParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    include_refuted: bool = False
    """OFF by default, and the default is the point. Rendering refuted
    artifacts back to the seat whose job is to leave them is an EPISTEMIC
    change, not a layout one; today's `layout.superseded_summary_n` is 0 and
    this reproduces that. The capability exists so the question can be settled
    by a calibration run rather than by argument."""

    refuted_n: int = Field(default=0, ge=0, le=8)
    """How many refuted artifacts render, when `include_refuted` is on. Left
    at 0 so the shipped default reads its value from the layout policy
    exactly as the renderer does today."""


class _History(_Plugin):
    """History as EVIDENCE rather than as narration (R3).

    The operator's own framing — "History should be in evidence. That's a good
    move." — and their own list, which names history separately from evidence,
    so this is a separate plugin from the evidence pair and both may sit in one
    layout at once.
    """

    plugin_id = "dr.history.v1"
    section_id = "superseded-conjectures"
    parameters_model = HistoryParams

    def render(self, request, params):
        from deepreason.llm.packs import _CARRY_FORWARD_ROUTE, _distilled
        from deepreason.ontology.state import Status

        layout = request.layout
        # The layout policy still decides by default: `superseded_summary_n`
        # is the shipped knob and this reproduces it. `include_refuted` is the
        # plugin-level override the operator asked for, and it only ever
        # WIDENS what the policy allows.
        count = layout.superseded_summary_n
        if params.include_refuted:
            count = max(count, params.refuted_n)
        if not count:
            return None
        suppressed = set(_supplied(request, "suppressed_exemplars", ()))
        superseded = [
            aid
            for aid, status in request.state.status.items()
            if status == Status.REFUTED and aid not in suppressed
        ][-count:]
        if not superseded:
            return None
        header = (
            "SUPERSEDED (refuted — do not re-propose these; they are here "
            "so you can tell a new idea from a repeat)"
        )
        if layout.retrieval_note and layout.distil_carry_forward:
            header += f" — {_CARRY_FORWARD_ROUTE}"
        lines = [header + ":"]
        for aid in superseded:
            lines.append(
                f"- {aid}: {_distilled(request.state, aid, request.blobs, layout)}"
            )
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(lines),
            provenance_refs=tuple(superseded),
        )


class _Crossover(_Plugin):
    plugin_id = "dr.crossover"
    section_id = "crossover"

    def render(self, request, params):
        from deepreason.llm.packs import _distilled

        school = _supplied(request, "school")
        crossover = (school or {}).get("crossover") if school else None
        if not crossover:
            return None
        suppressed = set(_supplied(request, "suppressed_exemplars", ()))
        lines = [
            "CROSSOVER (a divergent lineage from the most distant school — "
            "your school just reseeded on convergence; reconcile or bridge "
            "these, do NOT echo your own lineage):",
        ]
        for aid in crossover:
            if aid in request.state.artifacts and aid not in suppressed:
                lines.append(
                    f"- {aid}: "
                    f"{_distilled(request.state, aid, request.blobs, request.layout)}"
                )
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(lines),
            provenance_refs=tuple(crossover),
        )


class _ComplementDirective(_Plugin):
    plugin_id = "dr.complement-directive"
    section_id = "complement-directive"

    def render(self, request, params):
        if not _supplied(request, "complement"):
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text="COMPLEMENT DIRECTIVE: produce the attempt these summaries make "
            "least likely — avoid the modal continuation of the neighbourhood.",
        )


class _DiversitySpecifications(_Plugin):
    plugin_id = "dr.diversity-specifications"
    section_id = "diversity-specifications"

    def render(self, request, params):
        specs = _supplied(request, "specs")
        if not specs:
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text="DIVERSITY SPECIFICATIONS (binding — candidate k MUST realize spec k):\n"
            + "\n".join(f"  spec {i + 1}: {s}" for i, s in enumerate(specs)),
        )


class _ConjecturerOutputContract(_Plugin):
    plugin_id = "dr.output-contract.conjecturer"
    section_id = "output-contract"

    def render(self, request, params):
        vs_k = _supplied(request, "vs_k")
        allow_no_candidate = _supplied(request, "allow_no_candidate_outcome")
        directive = (
            f"DIRECTIVE: return up to {vs_k} diverse candidates with typicality "
            "estimates. You may instead or additionally request bounded context, "
            "or abstain when no responsible proposal is available. Return at "
            "least one meaningful outcome; never invent a candidate to fill a "
            "quota. Include atypical candidates when proposing candidates."
            if allow_no_candidate
            else f"DIRECTIVE: return exactly {vs_k} diverse candidates with "
            "typicality estimates. Include atypical candidates, not just the "
            "modal answer."
        )
        if _supplied(request, "open_criticism_context"):
            directive += (
                " EVERY candidate must carry a `discharges` entry for EVERY handle "
                "listed under OPEN CRITICISMS above. A submission missing any of "
                "them is returned to you once with the open list, and then accepted "
                "with the gap recorded."
            )
        return SectionRenderV1(section_id=self.section_id, text=directive)


class _EpisodeSlot(_Plugin):
    """REGISTERED AND UNIMPLEMENTED, on purpose.

    The operator has NOT decided what episodes are — their own words, the same
    day they asked for this interface: "But I'm still unsure what to do with
    episodes." So the registry admits the id and nothing else: it is in no
    shipped layout, it renders nothing if invoked, and this docstring is the
    whole of what the tranche says about episodes (`R13`).
    """

    plugin_id = "dr.episodes.slot"
    section_id = "episodes"

    def render(self, request, params):
        return None


# The nine caller-computed contexts that need no formatting beyond passing
# through (A6, and `DR-SEAM-packs-and-token-economy-x-rules`'s table).
_OpenCriticisms = _verbatim(
    "dr.open-criticisms", "open-criticisms", "open_criticism_context"
)
_FrozenEvidence = _verbatim(
    "dr.evidence.frozen", "frozen-evidence-context", "frozen_evidence_context"
)
_FrameCrisis = _verbatim("dr.frame.crisis", "frame-crisis", "frame_crisis_context")
_FrameSlice = _verbatim("dr.frame.slice", "frame-slice", "frame_slice_context")


# ---------------------------------------------------------------------------
# The critic's thirteen sections, in `render_crit_pack`'s own order.
#
# Three of them are NOT here, because they are the conjecturer's already:
# `dr.frame.crisis`, `dr.frame.slice` and `dr.evidence.citable` render the
# same section for both seats. The critic's copy differs only in its layout
# entry (priorities 4/4/6 against 4/4/4, a 32-token floor against 64) and in
# `dr.evidence.citable`'s `requires_invitation` parameter -- differences the
# layout expresses, so neither plugin forks.
# ---------------------------------------------------------------------------


class _ProblemContext(_Plugin):
    plugin_id = "dr.problem-context"
    section_id = "problem-context"

    def render(self, request, params):
        from deepreason.llm.packs import _problem_context

        target_id = _supplied(request, "target_id")
        token_budget = _supplied(request, "token_budget", 0)
        limit = 900 if token_budget <= 1200 else 1500
        lines = _problem_context(
            request.state, [target_id], description_limit=limit
        )
        if not lines:
            return None
        return SectionRenderV1(
            section_id=self.section_id, text="\n".join(lines).strip()
        )


class _TargetCommitments(_Plugin):
    plugin_id = "dr.target-commitments"
    section_id = "target-commitments"

    def render(self, request, params):
        from deepreason.llm.packs import _execution_spec_lines

        target = request.state.artifacts[_supplied(request, "target_id")]
        lines = ["TARGET COMMITMENTS (the target's declared attack surface):"]
        for cid in target.interface.commitments:
            kappa = request.commitments.get(cid)
            lines.append(f"- {cid}: {kappa.eval if kappa else '(unregistered)'}")
            if kappa is not None:
                lines += _execution_spec_lines(kappa)
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(lines),
            provenance_refs=tuple(target.interface.commitments),
        )


class _MachineEvaluationBoundary(_Plugin):
    plugin_id = "dr.machine-evaluation-boundary"
    section_id = "machine-evaluation-boundary"

    def render(self, request, params):
        from deepreason.llm.packs import _MACHINE_EVAL_NOTE

        return SectionRenderV1(
            section_id=self.section_id, text=_MACHINE_EVAL_NOTE
        )


class StandingAttacksParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    attackers_n: int = Field(default=5, ge=1, le=64)
    """How many standing attacks the critic is shown. 5 is `ATTACKERS_N`,
    today's value."""


class _StandingAttacks(_Plugin):
    plugin_id = "dr.standing-attacks"
    section_id = "standing-attacks"
    parameters_model = StandingAttacksParams

    def render(self, request, params):
        from deepreason.llm.packs import _head

        target_id = _supplied(request, "target_id")
        attackers = [
            x for x, t in sorted(request.state.att) if t == target_id
        ][: params.attackers_n]
        if not attackers:
            return None
        lines = ["STANDING ATTACKS (do not repeat these):"]
        for x in attackers:
            status = request.state.status.get(x)
            lines.append(
                f"- {x} [{status.value if status else '?'}]: "
                f"{_head(request.state, x, request.blobs)}"
            )
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(lines),
            provenance_refs=tuple(attackers),
        )


class _TargetSupportChain(_Plugin):
    plugin_id = "dr.target.support-chain"
    section_id = "target-support-chain"

    def render(self, request, params):
        target = request.state.artifacts[_supplied(request, "target_id")]
        support = target.interface.refs
        if not support:
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(
                ["TARGET SUPPORT CHAIN (what the target declares it rests on):"]
                + [f"- {ref.target} [{ref.role.value}]" for ref in support]
            ),
            provenance_refs=tuple(ref.target for ref in support),
        )


class _TargetSupportContent(_Plugin):
    plugin_id = "dr.target.support-content"
    section_id = "target-support-content"

    def render(self, request, params):
        from deepreason.llm.packs import _head

        target = request.state.artifacts[_supplied(request, "target_id")]
        support = target.interface.refs
        if not support:
            return None
        known = [ref for ref in support if ref.target in request.state.artifacts]
        if not known:
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(
                ["SUPPORT CONTENT:"]
                + [
                    f"- {ref.target}: "
                    f"{_head(request.state, ref.target, request.blobs)}"
                    for ref in known
                ]
            ),
            provenance_refs=tuple(ref.target for ref in known),
        )


class _Target(_Plugin):
    plugin_id = "dr.target"
    section_id = "target"

    def render(self, request, params):
        from deepreason.programs import content_text

        target_id = _supplied(request, "target_id")
        target = request.state.artifacts[target_id]
        return SectionRenderV1(
            section_id=self.section_id,
            text=f"TARGET {target_id}\n{content_text(target, request.blobs)}",
            provenance_refs=(target_id,),
        )


class _CounterexampleRecourse(_Plugin):
    plugin_id = "dr.counterexample-recourse"
    section_id = "counterexample-recourse"

    def render(self, request, params):
        from deepreason.llm.packs import (
            _COUNTEREXAMPLE_NOTE,
            _carries_execution_oracle,
        )

        target = request.state.artifacts[_supplied(request, "target_id")]
        if not _carries_execution_oracle(target, request.commitments):
            return None
        return SectionRenderV1(
            section_id=self.section_id, text=_COUNTEREXAMPLE_NOTE
        )


class _PremiseInvitation(_Plugin):
    plugin_id = "dr.premise-invitation"
    section_id = "premise-invitation"

    def render(self, request, params):
        from deepreason.llm.packs import premise_invitation_note

        invitation = _supplied(request, "premise_invitation")
        if invitation is None:
            return None
        return SectionRenderV1(
            section_id=self.section_id,
            text=premise_invitation_note(
                invitation,
                citable=bool(_supplied(request, "citable_evidence_context")),
            ),
        )


class _CriticOutputContract(_Plugin):
    plugin_id = "dr.output-contract.critic"
    section_id = "output-contract"

    def render(self, request, params):
        return SectionRenderV1(
            section_id=self.section_id,
            text="DIRECTIVE: mount the strongest NEW specific case against the target, "
            "or attack=false if you find no genuine fault.",
        )


CRITIC_PLUGINS: tuple[type[_Plugin], ...] = (
    _ProblemContext,
    _TargetCommitments,
    _MachineEvaluationBoundary,
    _StandingAttacks,
    _TargetSupportChain,
    _TargetSupportContent,
    _Target,
    _CounterexampleRecourse,
    _PremiseInvitation,
    _CriticOutputContract,
)
"""Ten NEW plugins; the critic's other three sections are the conjecturer's
own `dr.frame.crisis`, `dr.frame.slice` and `dr.evidence.citable`, which is
why this tuple is ten rather than thirteen."""


CONJECTURER_PLUGINS: tuple[type[_Plugin], ...] = (
    _ProblemStatement,
    _Criteria,
    _OpenCriticisms,
    _MandatoryInterface,
    _ActiveProperties,
    _SchoolStance,
    _GenerationContext,
    _ScratchAdvisory,
    _FrozenEvidence,
    _CitableEvidence,
    _CapabilityResult,
    _FrameCrisis,
    _FrameSlice,
    _Neighbourhood,
    _LiveNeighbourhood,
    _History,
    _Crossover,
    _ComplementDirective,
    _DiversitySpecifications,
    _ConjecturerOutputContract,
)

_SEEDED = False


def ensure_seeded() -> None:
    """Register every seeded plugin exactly once.

    Called by the renderers rather than run at import, because importing this
    module from `llm/packs.py` at module level would close an import cycle.
    """

    global _SEEDED
    if _SEEDED:
        return
    for plugin_class in CONJECTURER_PLUGINS + CRITIC_PLUGINS + (_EpisodeSlot,):
        register_section_plugin(plugin_class())
    _seed_layouts()
    _SEEDED = True


def _seed_layouts() -> None:
    from deepreason.llm.seat_layouts import register_shipped_layouts

    register_shipped_layouts()
