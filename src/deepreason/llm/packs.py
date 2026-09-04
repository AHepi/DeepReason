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

from collections.abc import Mapping
import hashlib
import json
from typing import Any

from deepreason.ontology.commitment import Commitment
from deepreason.ontology.problem import Problem
from deepreason.ontology.state import EpistemicState, Status
from deepreason.oracle import EXEC_PROGRAMS
from deepreason.llm.layout import (
    RenderLayoutPolicyV1,
    resolve_layout_policy,
)
from deepreason.packs import PackIR, PackSection, allocate_pack
from deepreason.packs.allocate import approximate_tokens
from deepreason.programs import content_text
from deepreason.llm.profiles import ModelProfile, ProfileSpec, clip_pack
from deepreason.llm.reference_menu import (
    REFERENCE_FIELD_DECLARATIONS,
    MenuRender,
)
from deepreason.llm.seat_sections import SectionRequestV1
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


# What a carried-forward entry says about its own truncation, and where the
# rest of it is. A silent cut is indistinguishable, from the model's side,
# from content that never existed -- the same argument the citable-evidence
# legend's disclosure rests on.
_CARRY_FORWARD_CLIPPED = " …[clipped; request this alias for the whole text]"
_CARRY_FORWARD_ROUTE = (
    "each entry is its CLAIM, distilled; request an alias through "
    "context_request to read that artifact whole"
)


def _claim_of(text: str) -> str | None:
    """The artifact's own claim, if it carries one.

    Distillation here is STRUCTURAL, not a model call: this tree's reasoning
    envelopes name their claim, so the "one-line claim summary, no prose" form
    is already present in the record and only has to be selected. An artifact
    with no parseable claim -- prose, a school policy, a relation -- returns
    None and falls back to the prefix head, so nothing loses its entry.
    """

    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    claim = parsed.get("claim")
    if isinstance(claim, str) and claim.strip():
        return claim.strip()
    return None


def _distilled(
    state: EpistemicState,
    artifact_id: str,
    blobs,
    layout: "RenderLayoutPolicyV1",
) -> str:
    """One carried-forward entry, under the layout policy."""

    text = content_text(state.artifacts[artifact_id], blobs)
    if not layout.distil_carry_forward:
        return text[: layout.distilled_head_chars].replace("\n", " ")
    body = (_claim_of(text) or text).replace("\n", " ").strip()
    if len(body) <= layout.distilled_head_chars:
        return body
    clipped = body[: layout.distilled_head_chars].rstrip()
    return clipped + (_CARRY_FORWARD_CLIPPED if layout.retrieval_note else "")


def _question_section(text: str) -> PackSection:
    """The seat's question, restated as the final block.

    MANDATORY and EXACT for the reason `target` and `open-criticisms` are: a
    droppable restatement would let budget pressure silently restore the
    arrangement this section exists to abolish, and a compressible one would
    lose its middle while still looking present. It carries NO new content --
    the same bytes as the pack's own priority-1 section -- so the cost is one
    duplication and the benefit is that nothing load-bearing follows it.
    """

    return _pack_section(
        "question",
        text,
        _QUESTION_PRIORITY,
        droppable=False,
        compressible=False,
    )


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
# After the withheld notice, and after everything else. The question restated
# last is what makes "nothing load-bearing after the question" true of a pack
# whose material necessarily follows its problem statement; allocation orders
# by `(priority, id)`, so a priority above every other section is the whole
# mechanism.
_QUESTION_PRIORITY = 100


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


_CONJECTURER_SEAT = "conjecturer"
_CRITIC_SEAT = "argumentative_critic"


def _walk_seat_layout(seat_id: str, layout_id, request, receipts=None):
    """Build one seat's sections by walking its registered layout.

    THE ONE LEGAL WAY a brief section is constructed. Every section resolves
    through `resolve_section_plugin`, so adding a section to a brief is a
    registration plus a layout entry and never a source edit -- which is the
    half of the modularity law a behaviour test alone would miss, and what
    `tests/test_seat_section_architecture.py` goes red on.

    Allocation facts come from the LAYOUT ENTRY unless the plugin overrides
    them, which is what lets two seats share one plugin at different
    priorities.
    """

    from deepreason.llm.seat_plugins import ensure_seeded
    from deepreason.llm.seat_sections import (
        SeatSectionError,
        SectionReceiptV1,
        resolve_seat_pack_layout,
        resolve_section_plugin,
    )

    ensure_seeded()
    pack_layout = resolve_seat_pack_layout(seat_id, layout_id)
    sections: list[PackSection] = []
    if receipts is None:
        receipts = []
    for entry in pack_layout.entries:
        plugin = resolve_section_plugin(entry.plugin_id, entry.plugin_version)
        params = plugin.parameters_model(**dict(entry.params))
        # A plugin whose declared input this seat does not carry DECLINES.
        # This is what makes a shell portable between seats (R20): the
        # conjecturer's brief bound in the critic's place renders the sections
        # a critic request can feed and records the rest as absent, rather
        # than raising on the first one that wanted a problem.
        missing = [
            name
            for name in getattr(plugin, "requires", ())
            if (request.problem is None)
            if name == "problem"
        ] + [
            name
            for name in getattr(plugin, "requires", ())
            if name != "problem" and not request.supplied.get(name)
        ]
        render = None if missing else plugin.render(request, params)
        digest = hashlib.sha256(
            json.dumps(
                params.model_dump(mode="json"), sort_keys=True
            ).encode("utf-8")
        ).hexdigest()
        if render is None:
            # An absent receipt names the SECTION that is missing, not the
            # plugin that declined: a reader asking "was there evidence in
            # this pack" is asking about the section.
            receipts.append(
                SectionReceiptV1(
                    section_id=getattr(plugin, "section_id", "") or entry.plugin_id,
                    plugin_id=plugin.plugin_id,
                    plugin_version=plugin.plugin_version,
                    parameters_digest=f"sha256:{digest}",
                    source_bytes=0,
                    rendered_bytes=0,
                    disposition="absent",
                )
            )
            continue
        source_bytes = len(render.text.encode("utf-8"))
        if (
            entry.max_render_bytes is not None
            and source_bytes > entry.max_render_bytes
        ):
            # NO SILENT CAPS: an overrun names its plugin and stops, because a
            # clip here would be a second budget applied under the first one's
            # accounting.
            raise SeatSectionError(
                "SEAT_SECTION_RENDER_OVERRUN",
                f"{plugin.plugin_id!r} rendered {source_bytes} bytes over its "
                f"declared ceiling of {entry.max_render_bytes}",
            )
        sections.append(
            _pack_section(
                render.section_id,
                render.text,
                entry.priority if render.priority is None else render.priority,
                droppable=(
                    entry.droppable if render.droppable is None
                    else render.droppable
                ),
                compressible=(
                    entry.compressible if render.compressible is None
                    else render.compressible
                ),
                min_tokens=(
                    entry.min_tokens if render.min_tokens is None
                    else render.min_tokens
                ),
                provenance_refs=render.provenance_refs,
            )
        )
        receipts.append(
            SectionReceiptV1(
                section_id=render.section_id,
                plugin_id=plugin.plugin_id,
                plugin_version=plugin.plugin_version,
                parameters_digest=f"sha256:{digest}",
                source_bytes=source_bytes,
                rendered_bytes=source_bytes,
                disposition="rendered",
            )
        )
    return sections, receipts


def _reconcile_receipts(receipts, result) -> None:
    """Rewrite each receipt's disposition from what the ALLOCATOR did.

    The walk can only say a section rendered; whether it survived the budget
    is decided afterwards. Without this the record would report `rendered` for
    a section the seat never saw, which is the silent cap this whole layer
    exists to abolish -- one telling the record a comfortable story instead of
    the pack.
    """

    if not receipts:
        return
    by_id = {section.id: section for section in result.sections}
    for index, receipt in enumerate(receipts):
        allocated = by_id.get(receipt.section_id)
        if allocated is None:
            continue
        if allocated.dropped:
            disposition, rendered = "dropped", 0
        elif allocated.tokens < allocated.source_tokens:
            disposition, rendered = "compressed", len(allocated.text.encode("utf-8"))
        else:
            disposition, rendered = "rendered", len(allocated.text.encode("utf-8"))
        receipts[index] = receipt.model_copy(
            update={"disposition": disposition, "rendered_bytes": rendered}
        )


def _allocate_sections(
    role: str, token_budget: int, sections: list[PackSection], receipts=None
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
            _reconcile_receipts(receipts, result)
            return AllocatedPack(result.text)
        seen.update(cut)
        disclosed = cut
    result, _ = _allocate(tuple(sorted(seen)))
    _reconcile_receipts(receipts, result)
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
    open_criticism_context: str | None = None,
    allow_no_candidate_outcome: bool = False,
    reference_menus: tuple[MenuRender, ...] = (),
    layout: RenderLayoutPolicyV1 | None = None,
    seat_pack_layout: str | None = None,
    section_receipts: list | None = None,
    supplied: Mapping[str, Any] | None = None,
) -> str:
    """school = {"id", "stance_text", "weight"} — lineage inheritance (§11.1):
    the neighbourhood prefers the school's own accepted descendants; the
    stance directive fades as lineage grows. complement is the §11.4
    stagnation directive. specs are Level-2 diversity specifications:
    candidate k must realize spec k (llm/specs.py). neighbourhood_n caps
    the exemplar section (0 = blind generation — the basin study's
    conditioning-vs-repertoire manipulation); presentation only.

    layout is the render layout policy (DR-INV-render-layout); resolved per
    call rather than bound at import, so selecting an arrangement through the
    environment takes effect without a restart.

    seat_pack_layout names the COMPOSITION -- which sections this brief is
    assembled from, in what order, under what budget. Resolved the same way
    and for the same reason: argument, then DEEPREASON_SEAT_PACK_LAYOUT, then
    the seat's default. Never a Config field and never a manifest field, which
    would move every qualification subject digest in the tree.

    supplied is the assembled output of the seat's registered SOURCE bundle
    (`llm/seat_sources.py`), and it OVERRIDES the individual context keyword
    arguments where both are given. The keyword arguments remain because two
    dozen call sites -- the golden fixtures among them -- pass them one by
    one; a caller that has run the sources passes the mapping instead and
    names no section at all, which is what keeps `rules/` out of the
    business of deciding what a seat is shown."""
    layout = layout or resolve_layout_policy()
    # The neighbourhood set is computed ONCE here rather than inside a plugin:
    # it depends on the school's lineage ordering and on `neighbourhood_n`,
    # and two plugins read it (`dr.neighbourhood` and `dr.neighbourhood.live`
    # split it by `layout.live_verbatim_n`). Computing it twice would let the
    # two disagree.
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

    supplied_values: dict[str, Any] = {
        "accepted": tuple(accepted),
        "suppressed_exemplars": tuple(suppressed_exemplars),
        "school": school,
        "complement": complement,
        "specs": specs,
        "vs_k": vs_k,
        "allow_no_candidate_outcome": allow_no_candidate_outcome,
        "generation_context": generation_context,
        "scratch_context": scratch_context,
        "frozen_evidence_context": frozen_evidence_context,
        "citable_evidence_context": citable_evidence_context,
        "capability_result_context": capability_result_context,
        "frame_slice_context": frame_slice_context,
        "frame_crisis_context": frame_crisis_context,
        "open_criticism_context": open_criticism_context,
    }
    if supplied:
        supplied_values.update(supplied)
    # The menus are the one assembled value that is NOT a section plugin's to
    # format: the walk renders them itself, because a plugin may render
    # evidence however it likes but may not also suppress the legal-handle
    # menu. So it leaves the supplied mapping rather than travelling through
    # it (`DR-INV-reference-menu`, FROZEN clause (b)).
    reference_menus = reference_menus or supplied_values.pop("reference_menus", ()) or ()
    supplied_values.pop("reference_menus", None)
    sections, _ = _walk_seat_layout(
        _CONJECTURER_SEAT,
        seat_pack_layout,
        SectionRequestV1(
            problem=problem,
            state=state,
            commitments=commitments,
            blobs=blobs,
            layout=layout,
            supplied=supplied_values,
        ),
        receipts=section_receipts,
    )
    # Priority 4 puts a menu beside the section that carries its field's
    # content -- `citable-evidence-blocks` and the scratch context both sit
    # at 4 -- so the legal set is adjacent to what it is legal FOR, rather
    # than in a block of its own at the end of the pack.
    #
    # Rendered by the WALK, never by a plugin: a plugin may render evidence
    # however it likes, but it may not also suppress the menu, because a menu
    # changes what the model is SHOWN and may never change what the harness
    # ACCEPTS (`DR-INV-reference-menu`, FROZEN clause (b)).
    sections += _menu_sections(reference_menus, 4)
    if layout.question_last:
        sections.append(
            _question_section(
                "QUESTION (restated last, so nothing load-bearing follows "
                f"it)\nPROBLEM {problem.id}\n{problem.description}"
            )
        )
    return _allocate_sections(
        "conjecturer", token_budget, sections, receipts=section_receipts
    )


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
    layout: RenderLayoutPolicyV1 | None = None,
    seat_pack_layout: str | None = None,
    section_receipts: list | None = None,
) -> str:
    """The critic's brief, composed from the same registry the conjecturer's
    is composed from.

    A seat is a shell: what makes this one a critic is the LAYOUT it walks and
    the FORM it is asked to fill, both registered configuration. Three of its
    thirteen sections are literally the conjecturer's own plugins at different
    priorities."""

    layout = layout or resolve_layout_policy()
    sections, _ = _walk_seat_layout(
        _CRITIC_SEAT,
        seat_pack_layout,
        SectionRequestV1(
            problem=None,
            state=state,
            commitments=commitments,
            blobs=blobs,
            layout=layout,
            supplied={
                "target_id": target_id,
                "token_budget": token_budget,
                "premise_invitation": premise_invitation,
                "citable_evidence_context": citable_evidence_context,
                "frame_slice_context": frame_slice_context,
                "frame_crisis_context": frame_crisis_context,
            },
        ),
        receipts=section_receipts,
    )
    sections += _menu_sections(reference_menus, 4)
    if layout.question_last:
        # The critic's question restates the problem AND names its target: a
        # restatement that dropped the target would let a late-attention seat
        # answer about the problem rather than about the artifact.
        restated = [
            "QUESTION (restated last, so nothing load-bearing follows it)",
            *_problem_context(
                state,
                [target_id],
                description_limit=900 if token_budget <= 1200 else 1500,
            ),
            f"DIRECTIVE: mount the strongest NEW specific case against TARGET "
            f"{target_id}, or attack=false if you find no genuine fault.",
        ]
        sections.append(_question_section("\n".join(restated).strip()))
    return _allocate_sections(
        "argumentative-critic", token_budget, sections, receipts=section_receipts
    )
