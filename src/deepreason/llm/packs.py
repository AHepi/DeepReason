"""Pack renderer (spec §9) — deterministic, budgeted.

P1 renders: problem + compressed criteria + neighbourhood (born-connected,
§7 L1) + VS directive for Conj packs; commitments + target + standing
attackers for Crit packs. School render weights, precedent slices, and
summarizer re-voicing land with P2/P5. Negative case law is NEVER rendered
(§11.5); sealed holdout bytes are excluded until Reveal (§10.5).

Section ORDER is stable-prefix-first (docs/TOKEN_ECONOMY.md angle 4):
slow-changing sections (problem, criteria, school stance, shared
commitment schemas) render before volatile ones (neighbourhood, target
content, directives), so provider prefix caches bill the repeated head at
the cached rate. Ordering is presentation only — zero epistemic content.
"""

import json

from deepreason.ontology.commitment import Commitment
from deepreason.ontology.problem import Problem
from deepreason.ontology.state import EpistemicState, Status
from deepreason.oracle import EXEC_PROGRAMS
from deepreason.packs import PackIR, PackSection, allocate_pack
from deepreason.packs.allocate import approximate_tokens
from deepreason.programs import content_text
from deepreason.llm.profiles import ModelProfile, ProfileSpec, clip_pack
from deepreason.llm.reference_menu import (
    REFERENCE_FIELD_DECLARATIONS,
    MenuRender,
)
from deepreason.llm.wire import AliasTable

_CHARS_PER_TOKEN = 4
NEIGHBOURHOOD_N = 8
ATTACKERS_N = 5
FOUNDATION_CHARS = 8000  # total across all lineage endpoints in one pack

_EXECUTION_EVALS = {f"program:{p}" for p in EXEC_PROGRAMS}


class AllocatedPack(str):
    """Marker for a pack already budgeted section-by-section by PackIR."""

def _simulation_contract_note() -> str:
    """The critic-side statement of the simulation channel and its contract.

    Built from the same two wire constants the conjecturer's schema carries,
    so the rule the critic is told and the rule the harness enforces cannot
    drift into two wordings. Imported lazily: llm.wire imports this module's
    package siblings, and a module-level import would close the cycle.
    """

    from deepreason.llm.wire import (
        SIMULATION_MODEL_SOURCE_CONTRACT,
        SIMULATION_REQUESTED_OBSERVABLES_CONTRACT,
    )

    return (
        "SIMULATION IS AVAILABLE TO THE TARGETS YOU ARE JUDGING. A candidate "
        "whose claim turns on a discriminating experiment could have filed a "
        "typed simulation proposal and had it executed under containment; one "
        "that only describes an experiment in prose has not established it. "
        "Judge whether the claim NEEDED one, and say so in your case.\n"
        "The contract a filed program must satisfy, verbatim as the "
        "conjecturer is shown it:\n"
        f"- model_source: {SIMULATION_MODEL_SOURCE_CONTRACT}\n"
        f"- requested_observables: {SIMULATION_REQUESTED_OBSERVABLES_CONTRACT}\n"
        "You cannot file a simulation yourself on this contract; you can "
        "convict a candidate for not having filed one, or attack the program "
        "it did file."
    )


_COUNTEREXAMPLE_NOTE = (
    "EXECUTION-BACKED TARGETS: a target whose commitments include an "
    "execution oracle is judged by RUNNING it — if it currently passes, a "
    "purely argumentative case CANNOT refute it. To refute such a target, "
    "also return \"counterexample\": a JSON list of positional args for its "
    "entry point; the harness will run the target on it and check the "
    "declared property. An input the problem's gate rejects, or one the "
    "target handles correctly, grounds nothing."
)

_MACHINE_EVAL_NOTE = (
    "MACHINE-EVALUATED COMMITMENTS: schemas whose eval starts with "
    "'predicate:' or 'program:' are checked by the harness DETERMINISTICALLY "
    "— every target shown here currently PASSES them (failures were refuted "
    "mechanically before this call). Do NOT base a case on claiming such a "
    "commitment is violated (e.g. re-counting a length bound): that claim is "
    "machine-decided and your case would assert a falsehood. Argue about the "
    "SUBSTANCE of the content instead."
)


def premise_invitation_note(problem_id: str, *, citable: bool = False) -> str:
    """The premise channel's invitation (premises.py, v2 Rung 2).

    Attention only, and it says so: declining carries no penalty, so nothing
    ranks a critic on whether it accepts (C5). It asks for a presupposition
    that FORBIDS NOTHING because that is the only kind the harness can
    adjudicate on its own — it reads an artifact's attack surface, and a
    presupposition with nothing to forbid has none.
    """
    return (
        f"PREMISE INVITATION (optional): every candidate offered for problem "
        f"{problem_id} so far has been refuted. If the PROBLEM ITSELF "
        "presupposes something that FORBIDS NOTHING — a presupposition no "
        "observation and no execution could ever tell against, so that the "
        "question is malformed rather than merely hard — state that "
        "presupposition in \"premise\". Leave it null otherwise; declining "
        "costs you nothing, and this never replaces your case against the "
        "target."
    ) + (
        # Only when blocks are actually listed below: asking for a quote a
        # pack carries no source for would invite invention, which is the
        # opposite of what the byte-check is for (R62).
        (
            " If admitted evidence bears on that presupposition, cite it in "
            "\"premise_evidence\" as a block id from the CITABLE EVIDENCE "
            "BLOCKS list together with an EXACT quote from that block. The "
            "quote is byte-checked against the recorded bytes; an unquoted "
            "citation cannot be made here, and a citation of a block this "
            "call was not shown does not verify."
        )
        if citable
        else ""
    )


def _active_property_claims(state: EpistemicState, blobs, criteria: list[str]) -> list[str]:
    """Docstring claims of ACCEPTED proposed properties (code:python-prop
    artifacts with a MENTION ref into the problem's criteria). Shown to the
    conjecturer so candidates comply with the run's validated standards up
    front — presentation only (§9); the checkers still decide everything.
    (Reimplemented from rules/experiment.py against raw state: packs must not
    import rules.)"""
    from deepreason.ontology.artifact import RefRole

    criteria_set = set(criteria)
    claims: list[str] = []
    for aid, artifact in state.artifacts.items():
        if artifact.codec != "code:python-prop":
            continue
        if state.status.get(aid) != Status.ACCEPTED:
            continue
        if not any(
            r.role == RefRole.MENTION and r.target in criteria_set
            for r in artifact.interface.refs
        ):
            continue
        text = content_text(artifact, blobs)
        if text.startswith('"""'):
            end = text.find('"""', 3)
            if end > 0:
                claims.append(text[3:end].strip())
    return claims


def _lineage_foundation(
    problem: Problem,
    state: EpistemicState,
    commitments: dict[str, Commitment],
    blobs,
) -> list[str]:
    """FOUNDATION section: full content of the lineage-ref endpoints the
    problem's criteria freeze (staged pipelines: the surviving plan/design
    the next stage must build on). Presentation only (§9) — the AUTHORITY
    is the program:lineage_ref commitment itself, which mechanically
    refutes any candidate that fails to declare the dependence. The
    endpoint set is frozen into the commitment id, so this section is
    static for the life of the problem and all its successors — it belongs
    in the cacheable prefix."""
    endpoints: list[str] = []
    for cid in problem.criteria:
        kappa = commitments.get(cid)
        if kappa is None or kappa.eval != "program:lineage_ref":
            continue
        for eid in (kappa.budget.extra.get("endpoints") or "").split(","):
            if eid and eid in state.artifacts and eid not in endpoints:
                endpoints.append(eid)
    if not endpoints:
        return []
    per_endpoint = FOUNDATION_CHARS // len(endpoints)
    lines = ["", "FOUNDATION (adjudicated groundwork this problem builds on — "
                 "your candidate MUST implement it faithfully):"]
    for eid in endpoints:
        lines += [f"--- foundation artifact {eid} ---",
                  content_text(state.artifacts[eid], blobs)[:per_endpoint]]
    lines.append(
        "REQUIRED: every candidate's \"refs\" MUST include "
        + " or ".join(f'{{"target": "{eid}", "role": "dependence"}}' for eid in endpoints)
        + " for the foundation it builds on — candidates without this ref "
          "are refuted mechanically."
    )
    return lines


def _carries_execution_oracle(artifact, commitments: dict[str, Commitment]) -> bool:
    return any(
        (kappa := commitments.get(cid)) is not None and kappa.eval in _EXECUTION_EVALS
        for cid in artifact.interface.commitments
    )


def _execution_spec_lines(kappa: Commitment) -> list[str]:
    """Render an execution commitment's frozen spec so critics can aim: the
    entry point, one example input, and the counterexample admission gate. A
    critic that cannot see the gate proposes out-of-spec inputs (integer node
    ids, cyclic graphs) that ground nothing — the commitment is the declared
    attack surface, so its spec belongs in the pack. Presentation only."""
    if kappa.eval not in _EXECUTION_EVALS:
        return []
    try:
        spec = json.loads(kappa.budget.extra.get("spec", "{}"))
    except (ValueError, AttributeError):
        return []
    if not spec:
        return []
    example = None
    if spec.get("inputs"):
        example = spec["inputs"][0]
    elif spec.get("tests"):
        example = spec["tests"][0].get("in")
    lines = [f"    entry point: {spec.get('entry')}"]
    if example is not None:
        lines.append(f"    example input (positional args): {json.dumps(example)}")
    contract = spec.get("input_contract")
    if contract:
        lines.append(f"    INPUT CONTRACT (binding): {contract}")
    gate = spec.get("input_check")
    if gate:
        lines.append("    counterexample admission gate — def valid(inp) must return True:")
        lines += [f"      {line}" for line in gate.splitlines()]
    return lines


def _head(state: EpistemicState, artifact_id: str, blobs, limit: int = 160) -> str:
    text = content_text(state.artifacts[artifact_id], blobs)
    return text[:limit].replace("\n", " ")


def _clip(text: str, token_budget: int) -> str:
    return text[: token_budget * _CHARS_PER_TOKEN]


def _pack_section(
    identifier: str,
    text: str,
    priority: int,
    *,
    droppable: bool,
    compressible: bool,
    min_tokens: int = 0,
    provenance_refs: tuple[str, ...] = (),
) -> PackSection:
    source_tokens = approximate_tokens(text)
    return PackSection(
        id=identifier,
        text_ref=f"inline:{text}",
        priority=priority,
        min_tokens=min(source_tokens, min_tokens),
        max_tokens=source_tokens,
        droppable=droppable,
        compressible=compressible,
        cache_group=identifier,
        provenance_refs=provenance_refs,
    )


# Sections whose ABSENCE changes what the model may DO, rather than only what
# it sees. A dropped `neighbourhood` costs exemplars; a dropped
# `citable-evidence-blocks` costs the ability to cite at all, and the pack
# then looks exactly like a run with no admitted evidence in it. P4 measured
# that shape from the other side -- 0 of 36 sub-problem prompts carried
# citable blocks -- and fixed the GATING; this is the allocation half, where
# the same outcome can still be reached silently, because a dropped section
# leaves no header and no placeholder.
DISCLOSED_ON_DROP = frozenset(
    {
        "citable-evidence-blocks",
        "frozen-evidence-context",
        "premise-invitation",
        "standing-attacks",
    }
)

_WITHHELD_ID = "context-withheld"
# Above every declared priority in either renderer, so the notice always
# sorts last however many sections a future pack grows.
_WITHHELD_PRIORITY = 99


def _withheld_notice(dropped: tuple[str, ...]) -> str:
    return (
        "CONTEXT WITHHELD FOR BUDGET — these sections exist in this run and "
        "were cut from THIS pack to fit its token budget, not because they "
        "are empty: " + ", ".join(dropped) + ". Treat what you were shown as "
        "partial; do not conclude the withheld content does not exist."
    )


def _menu_sections(
    reference_menus: "tuple[MenuRender, ...]",
    priority: int,
) -> list[PackSection]:
    """One PackSection per rendered menu: EXACT and MANDATORY.

    Not compressible, because compression cuts the tail of a section and a
    menu's tail is its truncation notice -- compressing one would remove
    both some handles and the statement that handles were removed, which is
    precisely the silent cap this layer exists to abolish.

    Not droppable either, and that pairing is forced rather than chosen: a
    droppable section that is also exact is admitted on its `min_tokens`
    and then rendered at full source size, overshooting the budget with no
    accounting signal (`DR-CON-packs-and-token-economy`, the NEGATIVE rule
    and its exhibiting check). Exact is affordable here for the same reason
    it is affordable for `frame-crisis`: the content is bounded by
    construction, at `MenuRenderPolicy.maximum_entries`.
    """

    return [
        _pack_section(
            menu.section_id,
            menu.text,
            priority,
            droppable=False,
            compressible=False,
        )
        for menu in reference_menus
    ]


def _allocate_sections(
    role: str, token_budget: int, sections: list[PackSection]
) -> str:
    """Render one finite PackIR without ever clipping the aggregate prefix.

    NO SILENT CAPS. `allocate_pack` drops an unaffordable optional section
    leaving no header and no placeholder -- absence is the only signal, which
    is right for a neighbourhood and wrong for the sections in
    `DISCLOSED_ON_DROP`, where absence is indistinguishable from a run that
    never had the content. So the allocation runs to a FIXED POINT: allocate,
    and if any disclosed-on-drop section was cut, allocate again with a
    mandatory one-line notice naming what was cut.

    Termination is by the BOUND, and the first version of this comment claimed
    something stronger that is not true. Adding the notice only ever decreases
    `remaining`, but the dropped set is NOT monotone in `remaining`:
    `allocate_pack` admits droppable sections greedily in `(priority, id)`
    order and `continue`s past one that will not fit, so a smaller budget can
    drop an early large section and thereby afford a later small one that had
    not fit before. Convergence is therefore measured rather than proved --
    at most three passes across 115 budgets from 1 to 799
    (`experiments/2026-08-24-change-rung6-frame-render-departures/`), against a
    bound of `len(sections) + 1`.

    What IS guaranteed is the property that matters: the loop returns only
    when the notice names exactly the disclosed-on-drop sections that final
    allocation cut. On the bound-exhaustion path it names the union of every
    cut it saw, which can OVER-name -- and over-naming is the safe direction,
    because a section reported withheld while present costs a reader one
    confusing line, whereas a section cut and not reported is the silent cap
    this function exists to abolish.

    When nothing disclosed is dropped the notice is ABSENT, not empty: an
    always-present "withheld: none" line would be the empty slot that
    `docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md` measured as worse than a
    populated one.
    """
    base = list(sections)

    def _allocate(disclosed: tuple[str, ...]):
        current = list(base)
        if disclosed:
            current.append(
                _pack_section(
                    _WITHHELD_ID,
                    _withheld_notice(disclosed),
                    # LAST, and the reason is caching rather than emphasis.
                    # Allocation order is `(priority, id)`, so at priority 1
                    # "context-withheld" sorts ahead of "problem" and
                    # "problem-context" -- the notice would lead every pack
                    # carrying one and, being per-call volatile, would
                    # invalidate the whole cacheable prefix the section
                    # ordering exists to protect. A mandatory section is
                    # retained in full at any priority, so moving it costs
                    # nothing it was doing.
                    _WITHHELD_PRIORITY,
                    droppable=False,
                    compressible=False,
                )
            )
        result = allocate_pack(
            PackIR(
                profile=f"legacy.{role}.pack-ir.v1",
                template_role=role,
                target_tokens=token_budget,
                sections=tuple(current),
            )
        )
        cut = tuple(
            sorted(
                section.id
                for section in result.sections
                if section.dropped and section.id in DISCLOSED_ON_DROP
            )
        )
        return result, cut

    disclosed: tuple[str, ...] = ()
    seen: set[str] = set()
    for _ in range(len(base) + 1):
        result, cut = _allocate(disclosed)
        if cut == disclosed:
            return AllocatedPack(result.text)
        seen.update(cut)
        disclosed = cut
    result, _ = _allocate(tuple(sorted(seen)))
    return AllocatedPack(result.text)


def _document_excerpt(text: str, char_budget: int) -> str:
    """Budget a long target without making its tail look deleted.

    Prefix-only clipping caused compact critics to refute valid compiled
    designs for "ending abruptly" even though the omitted manifest and later
    components existed and had passed deterministic checks.  A labeled
    head/tail excerpt preserves document closure and makes the transport
    omission explicit; it does not manufacture or summarize target content.
    """
    if len(text) <= char_budget:
        return text
    marker = (
        "\n\n[HARNESS PACK EXCERPT: middle bytes omitted only for the model-facing "
        "budget. They remain in the logged target. This omission is not a "
        "fault; do not claim that unshown sections are missing.]\n\n"
    )
    available = max(2, char_budget - len(marker))
    head = (available * 3) // 4
    tail = available - head
    return text[:head].rstrip() + marker + text[-tail:].lstrip()


def apply_model_profile(
    pack: str,
    profile: str | ModelProfile | ProfileSpec,
    requested_tokens: int | None = None,
) -> str:
    """Apply only the profile's presentation budget to an existing pack."""
    return clip_pack(pack, profile, requested_tokens)


def alias_references(
    values: list[str],
    *,
    prefix: str = "A",
) -> tuple[AliasTable, str]:
    """Return an external alias table and deterministic model-facing list."""
    table = AliasTable.from_values(values, prefix=prefix)
    return table, "\n".join(f"{a}" for a in table.aliases)


def aliases_for_values(values, *, prefix: str = "A") -> AliasTable:
    """Build a deterministic table from nonempty unique call-local values."""
    unique = list(dict.fromkeys(str(value) for value in values if value))
    return AliasTable.from_values(unique, prefix=prefix)


def aliases_for_pack(
    pack: str,
    values,
    *,
    prefix: str = "A",
) -> AliasTable:
    """Alias only canonical values actually exposed by this rendered pack.

    Ordering follows first appearance, then input order. The mapping remains
    outside the model response and compiles back deterministically.
    """
    unique = list(dict.fromkeys(str(value) for value in values if value and str(value) in pack))
    positions = {value: pack.find(value) for value in unique}
    unique.sort(key=lambda value: positions[value])
    return AliasTable.from_values(unique, prefix=prefix)


def render_conj_pack(
    problem: Problem,
    state: EpistemicState,
    commitments: dict[str, Commitment],
    blobs,
    vs_k: int,
    token_budget: int,
    school: dict | None = None,
    complement: bool = False,
    specs: list[str] | None = None,
    neighbourhood_n: int = NEIGHBOURHOOD_N,
    generation_context: str | None = None,
    suppressed_exemplars: tuple[str, ...] = (),
    scratch_context=None,
    frozen_evidence_context: str | None = None,
    citable_evidence_context: str | None = None,
    capability_result_context: str | None = None,
    frame_slice_context: str | None = None,
    frame_crisis_context: str | None = None,
    allow_no_candidate_outcome: bool = False,
    reference_menus: tuple[MenuRender, ...] = (),
) -> str:
    """school = {"id", "stance_text", "weight"} — lineage inheritance (§11.1):
    the neighbourhood prefers the school's own accepted descendants; the
    stance directive fades as lineage grows. complement is the §11.4
    stagnation directive. specs are Level-2 diversity specifications:
    candidate k must realize spec k (llm/specs.py). neighbourhood_n caps
    the exemplar section (0 = blind generation — the basin study's
    conditioning-vs-repertoire manipulation); presentation only."""
    sections = [
        _pack_section(
            "problem",
            f"PROBLEM {problem.id}\n{problem.description}",
            1,
            droppable=False,
            compressible=False,
            provenance_refs=(problem.id,),
        )
    ]
    criteria = ["CRITERIA (commitments every candidate will carry and face):"]
    for cid in problem.criteria:
        kappa = commitments.get(cid)
        criteria.append(f"- {cid}: {kappa.eval if kappa else '(schema pending)'}")
    sections.append(
        _pack_section(
            "criteria",
            "\n".join(criteria),
            2,
            droppable=False,
            compressible=False,
            provenance_refs=tuple(problem.criteria),
        )
    )
    # FOUNDATION before the volatile sections: frozen into the lineage
    # commitment's id, hence static per problem (cache-prefix, angle 4).
    foundation = _lineage_foundation(problem, state, commitments, blobs)
    if foundation:
        sections.append(
            _pack_section(
                "mandatory-interface",
                "\n".join(foundation).strip(),
                3,
                droppable=False,
                compressible=False,
                provenance_refs=tuple(problem.criteria),
            )
        )
    claims = _active_property_claims(state, blobs, problem.criteria)
    if claims:
        sections.append(
            _pack_section(
                "active-properties",
                "ACTIVE PROPERTIES (conjectured standards the run has "
                "validated — candidates violating them are refuted by "
                "execution):\n" + "\n".join(f"- {c[:200]}" for c in claims),
                4,
                droppable=True,
                compressible=True,
                min_tokens=24,
            )
        )
    suppressed = set(suppressed_exemplars)
    accepted = [
        aid
        for aid, status in state.status.items()
        if status == Status.ACCEPTED and aid not in suppressed
    ]
    if school is not None:
        lineage = [
            aid for aid in accepted
            if state.artifacts[aid].provenance.school == school["id"]
        ]
        others = [aid for aid in accepted if aid not in set(lineage)]
        accepted = (lineage + others)[:neighbourhood_n]
    else:
        accepted = accepted[-neighbourhood_n:] if neighbourhood_n else []
    # Stance before neighbourhood: the stance text is stable per school while
    # the neighbourhood changes every cycle — cache-prefix ordering (angle 4).
    if school is not None and school.get("weight", 0) > 0:
        sections.append(
            _pack_section(
                "school-stance",
                f"SCHOOL STANCE (weight {school['weight']:.2f}): "
                f"{school['stance_text']}",
                5,
                droppable=False,
                compressible=True,
                min_tokens=24,
            )
        )
    if generation_context:
        sections.append(
            _pack_section(
                "experimental-generation-context",
                "GENERATION CONTEXT (attention only; truth, admission, and "
                "verifier standards are unchanged):\n" + generation_context,
                6,
                droppable=False,
                compressible=False,
            )
        )
    if scratch_context is not None:
        from deepreason.scratch.render import RenderedScratchPackV1

        scratch_context = RenderedScratchPackV1.model_validate(scratch_context)
        sections.append(
            _pack_section(
                "scratch-advisory-context",
                scratch_context.text,
                7,
                droppable=False,
                compressible=False,
            )
        )
    if frozen_evidence_context:
        sections.append(
            _pack_section(
                "frozen-evidence-context",
                frozen_evidence_context,
                4,
                droppable=True,
                compressible=True,
                min_tokens=64,
            )
        )
    if citable_evidence_context:
        sections.append(
            _pack_section(
                "citable-evidence-blocks",
                citable_evidence_context,
                4,
                droppable=True,
                compressible=True,
                min_tokens=64,
            )
        )
    if capability_result_context:
        sections.append(
            _pack_section(
                "capability-result-context",
                "RECORDED SIMULATION OBSERVATION (fresh work):\n"
                "This is the output of the named program under the named inputs and "
                "execution conditions. It is not a universal fact and does not "
                "automatically establish the requesting hypothesis.\n"
                + capability_result_context,
                3,
                droppable=False,
                compressible=False,
            )
        )
    if frame_crisis_context:
        # EXACT, and it sorts before "frame-slice" on id so the crisis leads.
        # A frame renders its own open indictments in every pack in its scope
        # (§9.5). Droppable would let budget pressure remove them silently --
        # a dropped section leaves no header. Compressible would do the same
        # thing more quietly still: the first version of this carried the
        # wounds and the digest in ONE compressible section, and at a tight
        # budget `_bounded_view` cut the STANDING ATTACKERS block out of a
        # pack that still showed a frame. Bounded by construction in
        # `calculus/render.py`, which is what makes exact affordable.
        sections.append(
            _pack_section(
                "frame-crisis",
                frame_crisis_context,
                4,
                droppable=False,
                compressible=False,
            )
        )
    if frame_slice_context:
        # The articulation digest, and this half IS "compressed; expandable by
        # view" in §9.5's own words -- the expansion is `deepreason standing
        # --json`. Non-droppable so a frame never renders as absent.
        sections.append(
            _pack_section(
                "frame-slice",
                frame_slice_context,
                4,
                droppable=False,
                compressible=True,
                min_tokens=96,
            )
        )
    if accepted:
        neighbourhood = [
            "NEIGHBOURHOOD (accepted artifacts; carry dependence refs where natural):"
        ]
        for aid in accepted:
            neighbourhood.append(f"- {aid}: {_head(state, aid, blobs)}")
        sections.append(
            _pack_section(
                "neighbourhood",
                "\n".join(neighbourhood),
                8,
                droppable=True,
                compressible=True,
                min_tokens=32,
                provenance_refs=tuple(accepted),
            )
        )
    crossover = (school or {}).get("crossover") if school else None
    if crossover:
        crossover_lines = [
            "CROSSOVER (a divergent lineage from the most distant school — "
            "your school just reseeded on convergence; reconcile or bridge "
            "these, do NOT echo your own lineage):",
        ]
        for aid in crossover:
            if aid in state.artifacts and aid not in suppressed:
                crossover_lines.append(f"- {aid}: {_head(state, aid, blobs)}")
        sections.append(
            _pack_section(
                "crossover",
                "\n".join(crossover_lines),
                9,
                droppable=True,
                compressible=True,
                min_tokens=24,
                provenance_refs=tuple(crossover),
            )
        )
    if complement:
        sections.append(
            _pack_section(
                "complement-directive",
                "COMPLEMENT DIRECTIVE: produce the attempt these summaries make "
                "least likely — avoid the modal continuation of the neighbourhood.",
                10,
                droppable=False,
                compressible=False,
            )
        )
    if specs:
        sections.append(
            _pack_section(
                "diversity-specifications",
                "DIVERSITY SPECIFICATIONS (binding — candidate k MUST realize spec k):\n"
                + "\n".join(f"  spec {i + 1}: {s}" for i, s in enumerate(specs)),
                11,
                droppable=False,
                compressible=False,
            )
        )
    sections.append(
        _pack_section(
            "output-contract",
            (
                f"DIRECTIVE: return up to {vs_k} diverse candidates with typicality "
                "estimates. You may instead or additionally request bounded context, "
                "or abstain when no responsible proposal is available. Return at "
                "least one meaningful outcome; never invent a candidate to fill a "
                "quota. Include atypical candidates when proposing candidates."
                if allow_no_candidate_outcome
                else f"DIRECTIVE: return exactly {vs_k} diverse candidates with "
                "typicality estimates. Include atypical candidates, not just the "
                "modal answer."
            ),
            12,
            droppable=False,
            compressible=False,
        )
    )
    # Priority 4 puts a menu beside the section that carries its field's
    # content -- `citable-evidence-blocks` and the scratch context both sit
    # at 4 -- so the legal set is adjacent to what it is legal FOR, rather
    # than in a block of its own at the end of the pack.
    sections += _menu_sections(reference_menus, 4)
    return _allocate_sections("conjecturer", token_budget, sections)


def render_batch_crit_pack(
    target_ids: list[str],
    state: EpistemicState,
    commitments: dict[str, Commitment],
    blobs,
    token_budget: int,
    simulation_proposals: tuple[tuple[str, str, str, str], ...] = (),
    simulation_enabled: bool = False,
    premise_invitation: str | None = None,
    citable_evidence_context: str | None = None,
    reference_menus: tuple[MenuRender, ...] = (),
) -> str:
    """One critic pass over several targets (§14 batching): the commitment
    schemas — usually shared, since batch-mates come from one problem —
    render once; each target carries its content and standing attacks.
    Only the call is shared; every warrant stays per-target."""
    lines = _problem_context(state, target_ids)
    lines += [
        f"TARGETS ({len(target_ids)}) — judge each independently.",
        "",
        "COMMITMENT SCHEMAS (attack surfaces; each target lists its own ids):",
    ]
    seen: set[str] = set()
    for tid in target_ids:
        for cid in state.artifacts[tid].interface.commitments:
            if cid in seen:
                continue
            seen.add(cid)
            kappa = commitments.get(cid)
            lines.append(f"- {cid}: {kappa.eval if kappa else '(unregistered)'}")
            if kappa is not None:
                lines += _execution_spec_lines(kappa)
    lines += ["", _MACHINE_EVAL_NOTE]
    content_chars = max(320, (token_budget * 2) // max(1, len(target_ids)))
    for tid in target_ids:
        target = state.artifacts[tid]
        lines += [
            "",
            f"TARGET {tid}",
            content_text(target, blobs)[:content_chars],
            f"commitments: {', '.join(target.interface.commitments) or '(none)'}",
        ]
        attackers = [x for x, t in sorted(state.att) if t == tid][:ATTACKERS_N]
        if attackers:
            lines.append("standing attacks (do not repeat these):")
            for x in attackers:
                status = state.status.get(x)
                lines.append(f"- {x} [{status.value if status else '?'}]: {_head(state, x, blobs)}")
    if any(_carries_execution_oracle(state.artifacts[tid], commitments) for tid in target_ids):
        lines += ["", _COUNTEREXAMPLE_NOTE]
    # Gated: a run that cannot propose a simulation must render the pack it
    # rendered before this section existed, byte for byte, so no committed
    # pack-derived baseline moves for runs the channel does not reach.
    if simulation_enabled:
        lines += ["", _simulation_contract_note()]
        if simulation_proposals:
            lines.append("")
            lines.append("SIMULATIONS ALREADY FILED ON THIS PROBLEM:")
            for request_id, mode, lifecycle, reason in simulation_proposals:
                lines.append(
                    f"- {request_id} [{mode}] -> {lifecycle}"
                    + (f" ({reason})" if reason else "")
                )
        else:
            lines += ["", "SIMULATIONS ALREADY FILED ON THIS PROBLEM: none."]
    # Gated exactly like the simulation section above: a pack with no
    # standing invitation renders byte for byte what it rendered before this
    # section existed.
    if premise_invitation is not None:
        lines += [
            "",
            premise_invitation_note(
                premise_invitation, citable=bool(citable_evidence_context)
            ),
        ]
        if citable_evidence_context:
            lines += ["", citable_evidence_context]
    # Menus sit immediately before the directive, so the legal set is the
    # last thing read before the instruction that uses it. This renderer
    # clips a joined string rather than allocating sections, so a menu here
    # is subject to the same `_clip` as everything else -- which is why the
    # truncation notice lives inside the menu text and not beside it.
    for menu in reference_menus:
        lines += ["", menu.text]
    lines += [
        "",
        "DIRECTIVE: return exactly one entry per target id above — the "
        "strongest NEW specific case (attack=true) or attack=false. Never "
        "attack an id that is not listed.",
    ]
    return _clip("\n".join(lines), token_budget)


def render_experiment_pack(
    base: Commitment,
    existing: list[str],
    token_budget: int,
    n_generators: int = 2,
    targets: list[str] | None = None,
) -> str:
    """Experiment-design pack (rules/experiment.py): the property oracle's
    full frozen spec — entry, example inputs, CHECKER source (what a violation
    means), input contract, and admission gate — plus the heads of already-
    accepted generators so new designs cover DIFFERENT ground, plus the CODE
    of standing execution-backed survivors. The survivors are what the
    experiment is FOR: a blind generator explores coverage; a generator
    designed against real code hunts the specific dimension its shortcuts
    ignore. Showing the code cannot bias adjudication — the frozen gate and
    checker decide every verdict (presentation only, §9)."""
    try:
        spec = json.loads(base.budget.extra.get("spec", "{}"))
    except (ValueError, AttributeError):
        spec = {}
    lines = [
        f"PROPERTY ORACLE {base.id}",
        f"entry point: {spec.get('entry')}",
        f"frozen example inputs (positional-args lists): "
        f"{json.dumps(spec.get('inputs', [])[:4])}",
    ]
    contract = spec.get("input_contract")
    if contract:
        lines.append(f"INPUT CONTRACT (binding): {contract}")
    checker = spec.get("checker")
    if checker:
        lines += ["", "correctness checker — a candidate output violating this "
                      "refutes the candidate:", checker]
    gate = spec.get("input_check")
    if gate:
        lines += ["", "admission gate — def valid(inp) must return True for every "
                      "generated input:", gate]
    if targets:
        lines += [
            "",
            "STANDING SURVIVORS (they pass every existing input; your "
            "experiments exist to probe THEM — read each implementation and "
            "design inputs that reach whatever the frozen examples and "
            "existing generators never vary: sizes, orderings, ties, "
            "degenerate shapes):",
        ]
        lines += targets
    if existing:
        lines += ["", "ALREADY-ACCEPTED GENERATORS (cover DIFFERENT ground — do "
                      "not duplicate these):"]
        for src in existing:
            head = " / ".join(src.splitlines()[:3])
            lines.append(f"- {head[:160]}")
    lines += [
        "",
        f"DIRECTIVE: return exactly {n_generators} substantively different "
        "generators (different structural families of inputs, not parameter "
        "tweaks of one idea).",
    ]
    return _clip("\n".join(lines), token_budget)


def render_property_pack(
    base: Commitment,
    problem_description: str,
    existing_claims: list[str],
    token_budget: int,
    n_properties: int = 2,
) -> str:
    """Property-design pack (rules/experiment.py): the PROBLEM STATEMENT (the
    sole source of legitimacy) plus the oracle's current spec. Deliberately
    shows NO candidate code — a property derived from code enshrines the
    code's bugs; a property derived from the problem statement tests them."""
    try:
        spec = json.loads(base.budget.extra.get("spec", "{}"))
    except (ValueError, AttributeError):
        spec = {}
    lines = [
        "PROBLEM STATEMENT (the sole source of legitimacy for any property):",
        problem_description,
        "",
        f"PROPERTY ORACLE {base.id}",
        f"entry point: {spec.get('entry')}",
        f"frozen example inputs (positional-args lists): "
        f"{json.dumps(spec.get('inputs', [])[:4])}",
    ]
    contract = spec.get("input_contract")
    if contract:
        lines.append(f"INPUT CONTRACT: {contract}")
    checker = spec.get("checker")
    if checker:
        lines += ["", "CURRENT checker — find requirements the problem states "
                      "that this does NOT enforce:", checker]
    if existing_claims:
        lines += ["", "ALREADY-ACTIVE PROPERTY CLAIMS (do not duplicate):"]
        lines += [f"- {c[:160]}" for c in existing_claims]
    lines += [
        "",
        f"DIRECTIVE: return at most {n_properties} properties, each targeting "
        "a DIFFERENT unenforced requirement. If the current checker already "
        "enforces everything the problem states, return one property that "
        "restates the weakest-enforced requirement more strictly ONLY if the "
        "problem statement actually demands it.",
    ]
    return _clip("\n".join(lines), token_budget)


def render_cx_retry_pack(
    rejected: list[dict],
    state: EpistemicState,
    commitments: dict[str, Commitment],
    blobs,
    token_budget: int,
) -> str:
    """Counterexample-retry pack (§3): each entry is {target, counterexample,
    reason} for an attack on an execution-backed target whose counterexample
    failed to ground. The rejection reason is the gate/oracle's own
    deterministic verdict — echoing it back is what turns a one-shot guesser
    into an experimenter. Renders the target's code and its frozen spec
    (entry, example input, gate) so the critic can aim."""
    lines = [
        f"COUNTEREXAMPLE RETRY ({len(rejected)} target(s)) — your previous "
        "attack(s) on execution-backed targets did not ground. For each "
        "target below: the harness's verdict on your proposed input, the "
        "target's code, and its oracle spec. Return one entry per target id "
        "with a NEW \"counterexample\" (a JSON list of positional args) that "
        "satisfies the admission gate AND makes the target's output violate "
        "the checker; attack=false if you cannot construct one.",
    ]
    for item in rejected:
        tid = item["target"]
        target = state.artifacts[tid]
        lines += [
            "",
            f"TARGET {tid}",
            content_text(target, blobs)[: max(320, token_budget // max(1, len(rejected)))],
            f"your previous counterexample: {json.dumps(item.get('counterexample'))}",
            f"harness verdict: {item.get('reason') or 'did not ground'}",
        ]
        for cid in target.interface.commitments:
            kappa = commitments.get(cid)
            if kappa is not None and kappa.eval in _EXECUTION_EVALS:
                lines.append(f"- {cid}: {kappa.eval}")
                lines += _execution_spec_lines(kappa)
    return _clip("\n".join(lines), token_budget)


def _problem_context(
    state: EpistemicState,
    target_ids: list[str],
    *,
    description_limit: int = 1500,
) -> list[str]:
    """The problem statements the targets address — the STANDARD criticism is
    measured against. A critic shown a plan but not its problem reliably
    manufactures out-of-scope faults (observed live: 'lacks accessibility
    provisions' and 'raises privacy concerns' against a problem that scoped a
    small local timer page — unbounded scope-expansion always wins against a
    finite document). Problem descriptions are the run's most stable text, so
    the section leads the pack (cache-prefix, angle 4)."""
    targets = set(target_ids)
    pids: list[str] = []
    for aid, pid in state.addr:
        if aid in targets and pid in state.problems and pid not in pids:
            pids.append(pid)
    lines: list[str] = []
    for pid in pids[:3]:
        lines += [
            f"PROBLEM CONTEXT ({pid}) — the standard the target answers to. "
            "A FAULT must show the target fails THIS problem as stated; "
            "omitting scope the problem never asked for is not a fault:",
            state.problems[pid].description[:description_limit],
            "",
        ]
    return lines


def render_crit_pack(
    target_id: str,
    state: EpistemicState,
    commitments: dict[str, Commitment],
    blobs,
    token_budget: int,
    premise_invitation: str | None = None,
    citable_evidence_context: str | None = None,
    frame_slice_context: str | None = None,
    frame_crisis_context: str | None = None,
    reference_menus: tuple[MenuRender, ...] = (),
) -> str:
    target = state.artifacts[target_id]
    # Commitments render BEFORE the target (angle 4): problem criteria lead
    # each interface list, so sibling targets share this section verbatim
    # and the cacheable prefix runs through it.
    context_limit = 900 if token_budget <= 1200 else 1500
    problem_context = _problem_context(
        state, [target_id], description_limit=context_limit
    )
    commitments_lines = [
        "TARGET COMMITMENTS (the target's declared attack surface):"
    ]
    for cid in target.interface.commitments:
        kappa = commitments.get(cid)
        commitments_lines.append(
            f"- {cid}: {kappa.eval if kappa else '(unregistered)'}"
        )
        if kappa is not None:
            commitments_lines += _execution_spec_lines(kappa)
    sections: list[PackSection] = []
    if problem_context:
        sections.append(
            _pack_section(
                "problem-context",
                "\n".join(problem_context).strip(),
                1,
                droppable=False,
                compressible=True,
                min_tokens=64,
            )
        )
    sections.extend(
        [
            _pack_section(
                "target-commitments",
                "\n".join(commitments_lines),
                2,
                droppable=False,
                compressible=False,
                provenance_refs=tuple(target.interface.commitments),
            ),
            _pack_section(
                "machine-evaluation-boundary",
                _MACHINE_EVAL_NOTE,
                3,
                droppable=False,
                compressible=False,
            ),
        ]
    )
    optional_suffix: list[str] = []
    attackers = [x for x, t in sorted(state.att) if t == target_id][:ATTACKERS_N]
    if attackers:
        optional_suffix.append("STANDING ATTACKS (do not repeat these):")
        for x in attackers:
            status = state.status.get(x)
            optional_suffix.append(
                f"- {x} [{status.value if status else '?'}]: "
                f"{_head(state, x, blobs)}"
            )
        sections.append(
            _pack_section(
                "standing-attacks",
                "\n".join(optional_suffix),
                5,
                droppable=True,
                compressible=True,
                min_tokens=24,
                provenance_refs=tuple(attackers),
            )
        )
    # The declared support chain is part of the argument, not context around
    # it: a case that a target is unsupported cannot be mounted or answered
    # without seeing what the target claims to rest on. Ids and roles are
    # exact, because a chain missing an entry reads as a chain that has none.
    # The referents' text is separately droppable — losing it costs the critic
    # detail, losing the declaration would misstate the argument.
    support = target.interface.refs
    if support:
        sections.append(
            _pack_section(
                "target-support-chain",
                "\n".join(
                    ["TARGET SUPPORT CHAIN (what the target declares it rests on):"]
                    + [f"- {ref.target} [{ref.role.value}]" for ref in support]
                ),
                4,  # sorts after "target" on id; the chain follows what it supports
                droppable=False,
                compressible=False,
                provenance_refs=tuple(ref.target for ref in support),
            )
        )
        known = [ref for ref in support if ref.target in state.artifacts]
        if known:
            sections.append(
                _pack_section(
                    "target-support-content",
                    "\n".join(
                        ["SUPPORT CONTENT:"]
                        + [
                            f"- {ref.target}: {_head(state, ref.target, blobs)}"
                            for ref in known
                        ]
                    ),
                    6,
                    droppable=True,
                    compressible=True,
                    min_tokens=24,
                    provenance_refs=tuple(ref.target for ref in known),
                )
            )
    if frame_crisis_context:
        # The critic needs this half for a reason the conjecturer does not: an
        # UNDECLARED conflict with the frame is criticisable as a silent
        # assumption, and a critic who cannot see what was declared cannot
        # tell the two apart. Exact, for the same reason as in the conjecture
        # pack.
        sections.append(
            _pack_section(
                "frame-crisis",
                frame_crisis_context,
                4,
                droppable=False,
                compressible=False,
            )
        )
    if frame_slice_context:
        sections.append(
            _pack_section(
                "frame-slice",
                frame_slice_context,
                4,
                droppable=False,
                compressible=True,
                min_tokens=96,
            )
        )
    counterexample_note = (
        _COUNTEREXAMPLE_NOTE
        if _carries_execution_oracle(target, commitments)
        else ""
    )
    directive = (
        "DIRECTIVE: mount the strongest NEW specific case against the target, "
        "or attack=false if you find no genuine fault."
    )
    # The target arrives whole. An excerpted argument cannot be refuted on the
    # bytes that were omitted, so budgeting it silently converted a transport
    # limit into an epistemic one. The section is mandatory and exact, so the
    # allocator retains it in full and an oversize prompt becomes a typed
    # envelope failure at dispatch rather than a quietly partial case.
    target_text = content_text(target, blobs)
    sections.append(
        _pack_section(
            "target",
            f"TARGET {target_id}\n{target_text}",
            4,
            droppable=False,
            compressible=False,
            provenance_refs=(target_id,),
        )
    )
    if counterexample_note:
        sections.append(
            _pack_section(
                "counterexample-recourse",
                counterexample_note,
                6,
                droppable=False,
                compressible=False,
            )
        )
    if premise_invitation is not None:
        # Droppable: an invitation the budget cannot afford is an invitation
        # not made this call, which costs nothing — the producer offers it
        # again next time the problem is worked. Compressible with it, per the
        # allocator's droppable/compressible pairing rule.
        sections.append(
            _pack_section(
                "premise-invitation",
                premise_invitation_note(
                    premise_invitation, citable=bool(citable_evidence_context)
                ),
                6,
                droppable=True,
                compressible=True,
                min_tokens=32,
            )
        )
        if citable_evidence_context:
            # Droppable with the invitation it serves, and never without it:
            # a legend the critic can see while the invitation was dropped
            # would list ids nothing asked it to cite.
            sections.append(
                _pack_section(
                    "citable-evidence-blocks",
                    citable_evidence_context,
                    6,
                    droppable=True,
                    compressible=True,
                    min_tokens=32,
                )
            )
    sections.append(
        _pack_section(
            "output-contract",
            directive,
            7,
            droppable=False,
            compressible=False,
        )
    )
    sections += _menu_sections(reference_menus, 4)
    return _allocate_sections("argumentative-critic", token_budget, sections)
