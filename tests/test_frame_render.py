"""Frame render semantics and the departure protocol (v2 calculus, Rung 6).

The claims these tests exist to make falsifiable, in the order the tranche's
REQUEST.md numbers them:

- R1  the pack for a problem in scope carries the frame's articulation digest
      AND the subject's standing attackers -- "the frame ships its own crisis";
- R2/R3 the slice carries the departure directive, and a DECLARED departure
      removes the hidden-premise criticism's target deterministically, while
      the declaration stays an ordinary attackable artifact;
- R4  (L-4) nothing scores a departure -- asserted as an ABSENCE, both
      behaviourally and structurally;
- R5  scope predicates cannot read a departure declaration;
- R7  all three exit grades are reachable and the render distinguishes them;
- G2  (Prop 12.5, render layer) rendering the slice moves no label;
- G4  (C1) the slice is byte-identical across renders;
- G5  (N1) no pack emits an empty provenance-shaped slot;
- G6  (N2) an attacker present at cycle k still renders at the TERMINAL cycle.
"""

import json

import pytest

from deepreason.calculus import operations
from deepreason.calculus.render import (
    EXIT_GRADE_MEANINGS,
    EXIT_GRADES,
    FRAME_SLICE_ATTACKERS_N,
    render_frame_crisis_context,
    articulation_digest,
    declared_departures,
    exit_grade,
    frame_exits,
    frame_slices,
    held_frame_obligations,
    render_frame_slice_context,
)
from deepreason.harness import Harness
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
)
from deepreason.ontology.artifact import RefRole
from tests.conftest import attack

SCOPE = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}
SUBJECT_COMMITMENT = Commitment(id="k:tides-are-lunar-only", eval="prose")
SUBJECT_TEXT = (
    "b: the lunar theory of tides -- the tide is the moon's differential "
    "pull, and the sun contributes nothing that matters at the scale of a "
    "harbour timetable."
)


def _art(harness, text, *, interface=None, role="import"):
    return harness.create_artifact(
        text,
        interface=interface if interface is not None else Interface(refs=[]),
        provenance=Provenance(role=role),
    )


def _problem(harness, pid, description):
    return harness.register_problem(
        Problem(
            id=pid, description=description, criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def _framed(harness):
    """A consulted frame over a subject that carries one commitment.

    The subject carries a commitment because a departure names commitment
    IDS: a subject with an empty interface would make the departure protocol
    untestable while every assertion about it still passed.
    """
    harness.register_commitment(SUBJECT_COMMITMENT)
    subject = _art(
        harness, SUBJECT_TEXT,
        interface=Interface(commitments=[SUBJECT_COMMITMENT.id], refs=[]),
    )
    case = _art(harness, "reach record: three lineages cite this subject")
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "should the lunar theory frame this scope"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=subject.id, scope=SCOPE,
        reach_case_refs=(case.id,),
        departure_protocol="name the broken commitment ids in a declaration",
    )
    return subject, case, promotion, assertion


# --- R1: the slice, and what it carries --------------------------------------

def test_a_consulted_frame_renders_its_digest_and_its_standing_attackers(harness):
    """R1. Both halves, in one pack: the articulation the frame asserts, and
    the open indictments against it. A slice with only the first would be a
    frame presented as settled, which is the state §9.5 exists to refuse."""
    subject, _, _, assertion = _framed(harness)
    critic, _ = attack(
        harness, subject.id, "mispredicts-the-neap-tide-by-forty-minutes"
    )
    problem = _problem(harness, "p-tides", "predict the spring tides here")

    digest = render_frame_slice_context(harness, "p-tides")
    crisis = render_frame_crisis_context(harness, "p-tides")
    assert digest is not None and crisis is not None
    assert subject.id in digest and subject.id in crisis
    assert "the moon's differential" in digest        # the articulation
    assert SUBJECT_COMMITMENT.id in digest            # the departure surface
    assert critic.id in crisis                        # the crisis, in frame
    assert "STANDING ATTACKERS" in crisis
    assert problem.id == "p-tides"


def test_a_problem_outside_the_scope_carries_no_frame_slice(harness):
    """R1's other half. sigma decides, and a scope that admits everything
    would make every assertion above pass for the wrong reason."""
    _framed(harness)
    _problem(harness, "p-orbits", "predict the orbit of a comet")
    assert render_frame_slice_context(harness, "p-orbits") is None
    assert frame_slices(harness, "p-orbits") == ()


def test_the_standing_attacker_cap_states_itself(harness):
    """G7, in the render. A count shown without its total is a silent cap,
    and a reader cannot then tell a quiet frame from a truncated one."""
    subject, _, _, _ = _framed(harness)
    for index in range(FRAME_SLICE_ATTACKERS_N + 2):
        attack(harness, subject.id, f"independent-fault-{index}")
    _problem(harness, "p-tides", "predict the spring tides here")

    text = render_frame_crisis_context(harness, "p-tides")
    assert f"{FRAME_SLICE_ATTACKERS_N} of {FRAME_SLICE_ATTACKERS_N + 2} shown" in text
    slice_ = frame_slices(harness, "p-tides")[0]
    assert len(slice_.attackers) == FRAME_SLICE_ATTACKERS_N
    assert slice_.attackers_total == FRAME_SLICE_ATTACKERS_N + 2


# --- R2, R3: the departure protocol ------------------------------------------

def test_the_slice_carries_the_departure_directive_and_the_protocol(harness):
    """R2. The directive is standing text in every pack in scope, and the
    assertion's own protocol string travels with it."""
    _framed(harness)
    _problem(harness, "p-tides", "predict the spring tides here")
    text = render_frame_crisis_context(harness, "p-tides")
    assert "DEPARTURES ARE PERMITTED" in text
    assert "no penalty anywhere" in text
    assert "UNDECLARED conflict" in text
    assert "name the broken commitment ids in a declaration" in text


def test_declaring_a_departure_removes_the_held_obligation(harness):
    """R3, and it is the DETERMINISTIC gate rather than an instruction.

    Q1's finding is that a standing rule in context decays regardless of
    where it sits, so what the hidden-premise criticism aims at cannot be
    whatever the model says it assumed. It is the record's own subtraction:
    the subject's commitment ids minus the ids the candidate declared.
    """
    subject, _, _, _ = _framed(harness)
    problem = _problem(harness, "p-tides", "predict the spring tides here")
    silent = _art(harness, "c1: a tidal model that quietly assumes the sun away")
    departing = _art(harness, "c2: a solar-lunar composite")

    assert held_frame_obligations(harness, subject.id, silent.id) == (
        SUBJECT_COMMITMENT.id,
    )
    operations.file_departure_declaration(
        harness, problem=problem, subject_ref=subject.id,
        departing_ref=departing.id, broken_ids=[SUBJECT_COMMITMENT.id],
        rationale="the solar term is not negligible at the equinox",
    )
    assert held_frame_obligations(harness, subject.id, departing.id) == ()
    assert held_frame_obligations(harness, subject.id, silent.id) == (
        SUBJECT_COMMITMENT.id,
    )
    assert departing.id in render_frame_crisis_context(harness, "p-tides")


def test_a_departure_declaration_is_itself_attackable(harness):
    """R3's second half. Nothing protects the declaration: it takes an attack
    and is refuted exactly as any artifact would be. A declaration that could
    not be attacked would let a candidate exempt itself by asserting it."""
    subject, _, _, _ = _framed(harness)
    problem = _problem(harness, "p-tides", "predict the spring tides here")
    departing = _art(harness, "c: a solar-lunar composite")
    declaration = operations.file_departure_declaration(
        harness, problem=problem, subject_ref=subject.id,
        departing_ref=departing.id, broken_ids=[SUBJECT_COMMITMENT.id],
        rationale="the solar term is not negligible at the equinox",
    )
    assert harness.state.status[declaration.id] == Status.ACCEPTED
    attack(harness, declaration.id, "the-named-commitment-is-not-the-one-broken")
    assert harness.state.status[declaration.id] == Status.REFUTED


# --- G4 / C1: determinism -----------------------------------------------------

def test_the_slice_is_byte_identical_across_renders(tmp_path):
    """G4. Two renders of one problem over one state, and two independently
    replayed harnesses over one root, agree byte for byte.

    What this pins is PURITY: a renderer that consumed an iterator, cached
    mutable state between calls, or read anything outside the replayed record
    fails it. What it does NOT pin is the attacker ORDER -- `state.att` is a
    list in log order, so an unsorted render would be deterministic too. That
    claim needs its own test, and has one below."""
    root = tmp_path / "run"
    harness = Harness(root)
    subject, _, _, _ = _framed(harness)
    for index in range(3):
        attack(harness, subject.id, f"independent-fault-{index}")
    _problem(harness, "p-tides", "predict the spring tides here")

    replayed = Harness(root, read_only=True)
    for render in (render_frame_slice_context, render_frame_crisis_context):
        first = render(harness, "p-tides")
        assert first == render(harness, "p-tides")
        assert render(replayed, "p-tides") == first


# --- G5 / N1: omit, do not redact --------------------------------------------

# Labels that name WHO or WHAT produced a content. Judge blinding's placebo
# result is that a present-but-empty one of these draws more attention than a
# populated one, so the slice carries none of them in either state.
PROVENANCE_SHAPED = (
    "author", "provenance", "origin", "produced by", "produced-by",
    "seat:", "model:", "endpoint:", "school:", "role:", "redacted",
)


def test_the_frame_slice_emits_no_provenance_shaped_slot(harness):
    """G5 (N1). Not "no EMPTY provenance slot" -- no provenance slot at all,
    in the fully-populated case and in the everything-absent case alike. A
    slot that is only omitted when empty is a slot, and its absence is then
    itself the signal."""
    subject, _, _, _ = _framed(harness)
    _problem(harness, "p-tides", "predict the spring tides here")

    bare = render_frame_slice_context(harness, "p-tides")
    bare_crisis = render_frame_crisis_context(harness, "p-tides")
    assert bare is not None and bare_crisis is not None
    attack(harness, subject.id, "mispredicts-the-neap-tide")
    departing = _art(harness, "c: a solar-lunar composite")
    operations.file_departure_declaration(
        harness, problem=harness.state.problems["p-tides"],
        subject_ref=subject.id, departing_ref=departing.id,
        broken_ids=[SUBJECT_COMMITMENT.id], rationale="the solar term matters",
    )
    full = render_frame_slice_context(harness, "p-tides")
    full_crisis = render_frame_crisis_context(harness, "p-tides")

    for text in (bare, bare_crisis, full, full_crisis):
        lowered = text.lower()
        for label in PROVENANCE_SHAPED:
            assert label not in lowered, (label, text)
    # And the empty parts are ABSENT rather than blanked.
    assert "STANDING ATTACKERS" not in bare_crisis   # no attackers yet
    assert "ALREADY DECLARED" not in bare_crisis     # nothing declared yet
    for text in (full, full_crisis):
        assert "(none)" not in text


def test_an_absent_frame_renders_nothing_rather_than_a_no_frame_notice(harness):
    """G5's sharpest case. A "no frame is consulted here" line would be the
    empty slot itself: every unframed pack would carry a header inviting the
    model to wonder what was withheld."""
    _problem(harness, "p-plain", "an ordinary problem with no frame at all")
    assert render_frame_slice_context(harness, "p-plain") is None
    assert render_frame_crisis_context(harness, "p-plain") is None


def test_attackers_render_in_id_order_whatever_order_the_state_holds(harness):
    """The ordering claim, against a SHUFFLED `att`, because the obvious test
    is vacuous.

    `Harness._adjudicate` already does `self.state.att = sorted(att)`, so a
    test that registers three attacks and checks the render is sorted passes
    with the sort in `subject_attackers` deleted -- it measures the harness,
    not this module. That first version was written and thrown away; this one
    hands the renderer a state whose `att` is in the opposite order and
    fails if the module leans on someone else's sortedness.

    Why the property is worth a test at all: under the cap, arrival order
    would let an early criticism hold a slot against every later one, and
    arrival order is origin information that appraisal may not read (Ax 4.1).
    """
    subject, _, _, _ = _framed(harness)
    _problem(harness, "p-tides", "predict the spring tides here")
    made = [attack(harness, subject.id, f"fault-{i}")[0].id for i in range(3)]

    harness.state.att = list(reversed(harness.state.att))
    assert [a for a, _ in harness.state.att if _ == subject.id] != sorted(made)

    slice_ = frame_slices(harness, "p-tides")[0]
    assert [attacker for attacker, _, _ in slice_.attackers] == sorted(made)


# --- the slice as a PACK section ---------------------------------------------

def _pack_state(harness):
    """A framed problem plus a target, ready for either renderer."""
    subject, _, _, _ = _framed(harness)
    attack(harness, subject.id, "mispredicts-the-neap-tide-by-forty-minutes")
    problem = _problem(harness, "p-tides", "predict the spring tides here")
    return subject, problem


def test_the_frame_slice_survives_a_budget_that_drops_everything_optional(harness):
    """The mechanism, not the position (N3).

    A budget small enough to drop every optional section must still carry the
    frame slice, because a dropped section leaves NO header and no
    placeholder: a droppable slice would restore the settled-frame
    presentation §9.5 exists to abolish, and nothing downstream could tell
    that it had. Both renderers, because a frame that shipped its crisis to
    the conjecturer and not the critic would leave the critic unable to tell
    a declared departure from a silent one.
    """
    from deepreason.llm.packs import render_conj_pack, render_crit_pack

    subject, _ = _pack_state(harness)
    slice_text = render_frame_slice_context(harness, "p-tides")
    assert slice_text is not None

    crisis_text = render_frame_crisis_context(harness, "p-tides")
    assert crisis_text is not None

    conj = render_conj_pack(
        harness.state.problems["p-tides"], harness.state, harness.commitments,
        harness.blobs, vs_k=2, token_budget=1,
        frame_slice_context=slice_text, frame_crisis_context=crisis_text,
    )
    crit = render_crit_pack(
        subject.id, harness.state, harness.commitments, harness.blobs,
        token_budget=1,
        frame_slice_context=slice_text, frame_crisis_context=crisis_text,
    )
    for pack in (conj, crit):
        assert "frame-crisis" in pack and "frame-slice" in pack
        # The WHOLE crisis, not a compressed view of it: every attacker line
        # survives a budget of one token. This is the assertion the one-section
        # version failed.
        assert crisis_text in pack
        assert "STANDING ATTACKERS" in pack


def test_an_unframed_problem_adds_no_frame_section_to_either_pack(harness):
    """G5, at the pack layer. `None` in means no section out — not an empty
    one, and not a header announcing that no frame applies."""
    from deepreason.llm.packs import render_conj_pack, render_crit_pack

    target = _art(harness, "an ordinary candidate")
    problem = _problem(harness, "p-plain", "an ordinary problem, no frame")
    conj = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500,
        frame_slice_context=render_frame_slice_context(harness, "p-plain"),
        frame_crisis_context=render_frame_crisis_context(harness, "p-plain"),
    )
    crit = render_crit_pack(
        target.id, harness.state, harness.commitments, harness.blobs,
        token_budget=2500,
        frame_slice_context=render_frame_slice_context(harness, "p-plain"),
        frame_crisis_context=render_frame_crisis_context(harness, "p-plain"),
    )
    for pack in (conj, crit):
        assert "frame-slice" not in pack
        assert "frame-crisis" not in pack
        assert "FRAME (" not in pack


def test_the_frame_slice_allocation_is_accounted(harness):
    """G7. The slice is in the allocation record with its own size, so "does
    it fit the budget" is a question the accounting answers rather than one
    a reader estimates from the rendered bytes."""
    from deepreason.packs import PackIR, PackSection, allocate_pack
    from deepreason.packs.allocate import approximate_tokens

    _pack_state(harness)
    slice_text = render_frame_slice_context(harness, "p-tides")
    section = PackSection(
        id="frame-slice", text_ref=f"inline:{slice_text}", priority=4,
        min_tokens=96, max_tokens=approximate_tokens(slice_text),
        droppable=False, compressible=True, cache_group="frame-slice",
    )
    result = allocate_pack(
        PackIR(profile="p", template_role="conjecturer", target_tokens=2500,
               sections=(section,))
    )
    booked = result.accounting()["sections"]["frame-slice"]
    assert booked["dropped"] is False
    assert booked["tokens"] == booked["source_tokens"]
    assert result.allocated_tokens <= result.target_tokens


def test_the_exact_crisis_section_is_bounded_by_construction(harness):
    """The price of EXACT, paid where it can be seen.

    A non-droppable, non-compressible section is retained in full even when it
    exceeds the target (`DR-CON-packs-and-token-economy`'s mandatory-section
    rule), so a crisis block that could grow without limit would be an
    unbounded mandatory cost on every pack in the frame's scope. It cannot:
    the attacker cap, the attacker head bound and the declaration cap bound it
    together, and both caps state themselves in-band where they bite.
    """
    from deepreason.calculus.render import (
        ARTICULATION_DIGEST_CHARS,
        FRAME_SLICE_DEPARTURES_N,
    )
    from deepreason.packs.allocate import approximate_tokens

    subject, _, _, _ = _framed(harness)
    problem = _problem(harness, "p-tides", "predict the spring tides here")
    for index in range(FRAME_SLICE_ATTACKERS_N * 4):
        attack(harness, subject.id, f"independent-fault-{index}")
    for index in range(FRAME_SLICE_DEPARTURES_N * 3):
        departing = _art(harness, f"c{index}: a rival that breaks with the frame")
        operations.file_departure_declaration(
            harness, problem=problem, subject_ref=subject.id,
            departing_ref=departing.id, broken_ids=[SUBJECT_COMMITMENT.id],
            rationale=f"reason {index}",
        )

    crisis = render_frame_crisis_context(harness, "p-tides")
    slice_ = frame_slices(harness, "p-tides")[0]
    assert len(slice_.attackers) == FRAME_SLICE_ATTACKERS_N
    assert len(slice_.declared_departures) == FRAME_SLICE_DEPARTURES_N
    # Both caps disclose themselves rather than implying the shown set is all.
    assert f"{FRAME_SLICE_ATTACKERS_N} of {slice_.attackers_total} shown" in crisis
    assert (
        f"{FRAME_SLICE_DEPARTURES_N} of {slice_.declared_departures_total} shown"
        in crisis
    )
    # The bound itself: comfortably inside the smallest shipped pack budget
    # (`PROFILES[COMPACT].pack_tokens_max` is 1200).
    assert approximate_tokens(crisis) < 600
    assert approximate_tokens(render_frame_slice_context(harness, "p-tides")) < (
        ARTICULATION_DIGEST_CHARS // 2
    )


# --- R6 / G7: P4's render half, and no silent caps ---------------------------

def _notice_body(pack: str) -> str:
    """Just the `context-withheld` section's own text.

    The notice sits at priority 1, so it renders near the TOP of the pack and
    everything after it -- including the real section headers -- follows it. A
    bare `pack.split("CONTEXT WITHHELD")[1]` therefore reads the whole rest of
    the pack as if it were the notice, which is how the first version of these
    two tests failed against correct code.
    """
    if "## context-withheld" not in pack:
        return ""
    after = pack.split("## context-withheld", 1)[1]
    return after.split("\n\n## ", 1)[0]


def test_a_dropped_citable_legend_is_disclosed_in_the_pack(harness):
    """R6 (P4's render half) and G7.

    P4 measured 0 of 36 sub-problem prompts carrying citable evidence blocks
    and fixed the GATING -- the legend's universe is now unconditional. This
    is the allocation half of the same question, and the point is that the
    same outcome is still reachable silently: a dropped section leaves no
    header and no placeholder, so a pack whose legend the budget cut is
    byte-indistinguishable from a run with no admitted evidence in it. After
    this, the deterministic section allocation SAYS what it settled.
    """
    from deepreason.llm.packs import DISCLOSED_ON_DROP, render_conj_pack

    problem = _problem(harness, "p-cite", "a problem with admitted evidence")
    legend = "CITABLE EVIDENCE BLOCKS\n" + "\n".join(
        f"[{i:016x}] an admitted passage about the tides" for i in range(12)
    )

    generous = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500, citable_evidence_context=legend,
    )
    assert "## citable-evidence-blocks" in generous
    assert "CONTEXT WITHHELD" not in generous

    starved = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=1, citable_evidence_context=legend,
    )
    # The notice renders at priority 1, near the TOP of the pack, so a bare
    # substring search finds the name inside the notice itself. Sections are
    # identified by their header; the notice by its own section body.
    assert "## citable-evidence-blocks" not in starved
    assert "CONTEXT WITHHELD" in starved
    assert "citable-evidence-blocks" in _notice_body(starved)
    assert "citable-evidence-blocks" in DISCLOSED_ON_DROP


def test_nothing_dropped_means_no_withheld_notice_at_all(harness):
    """G5 again, at the allocation layer. A standing "withheld: none" line
    would be the empty slot the blinding note measured as worse than a
    populated one, and it would appear in every pack in the run."""
    from deepreason.llm.packs import render_conj_pack

    problem = _problem(harness, "p-plain", "an ordinary problem")
    pack = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500,
    )
    assert "CONTEXT WITHHELD" not in pack
    assert "## context-withheld" not in pack


def test_the_disclosure_loop_reaches_a_fixed_point(harness):
    """The termination argument, exercised rather than asserted.

    Adding the mandatory notice shrinks `remaining`, which can cut MORE
    sections, which grows the notice. The dropped set is NOT monotone in
    `remaining` -- `allocate_pack` is greedy and `continue`s past a section
    that will not fit, so a smaller budget can afford a later small section it
    could not afford before. Convergence is therefore a measured property, not
    a proved one, and this sweep is the measurement: 115 budgets from 1 to
    799 plus the default, each returning a pack that agrees with itself.

    The invariant, stated as the two assertions below: no section is both
    rendered and reported withheld, and no disclosed-on-drop section supplied
    to the pack is absent without being named.
    """
    from deepreason.llm.packs import DISCLOSED_ON_DROP, render_conj_pack

    problem = _problem(harness, "p-many", "a problem carrying every optional part")
    for budget in list(range(1, 800, 7)) + [2500]:
        pack = render_conj_pack(
            problem, harness.state, harness.commitments, harness.blobs,
            vs_k=2, token_budget=budget,
            citable_evidence_context="CITABLE EVIDENCE BLOCKS\n" + "x" * 4000,
            frozen_evidence_context="FROZEN EVIDENCE\n" + "y" * 4000,
        )
        present = {s for s in DISCLOSED_ON_DROP if f"## {s}" in pack}
        body = _notice_body(pack)
        named = {s for s in DISCLOSED_ON_DROP if s in body}
        # No section is both rendered and reported withheld.
        assert not (present & named), (budget, present, named)
        # And every disclosed-on-drop section supplied to this pack is either
        # present or named -- never quietly absent.
        for section in ("citable-evidence-blocks", "frozen-evidence-context"):
            assert section in present or section in named, (budget, section)


# --- the slice reaches a REAL pack through the rules --------------------------

def test_both_rules_put_the_frame_in_the_pack_they_dispatch(harness, monkeypatch):
    """S7. The renderers take the slice; these are the two callers that
    actually supply it. A slice nothing passes is a section nothing renders,
    which is the shape `docs/ERRATA.md` E28 records -- a mechanism nobody
    triggers.

    Asserted against the CALL SITES rather than a dispatched prompt, because
    dispatch needs an adapter, a lease and a manifest, and none of those is
    what this claim is about.
    """
    import ast
    import pathlib

    for module, callee in (
        ("src/deepreason/rules/conj.py", "render_conj_pack"),
        ("src/deepreason/rules/crit.py", "render_crit_pack"),
    ):
        tree = ast.parse(pathlib.Path(module).read_text())
        calls = [
            call for call in ast.walk(tree)
            if isinstance(call, ast.Call)
            and getattr(call.func, "id", "") == callee
        ]
        assert calls, module
        for call in calls:
            passed = {kw.arg for kw in call.keywords}
            assert "frame_slice_context" in passed, (module, sorted(passed))
            assert "frame_crisis_context" in passed, (module, sorted(passed))


def test_the_frame_reaches_a_conjecture_pack_end_to_end(harness):
    """The same claim, exercised: a problem in scope, rendered through the
    real `render_conj_pack` with the real slice, carries the wounds."""
    from deepreason.llm.packs import render_conj_pack

    subject, _ = _pack_state(harness)
    pack = render_conj_pack(
        harness.state.problems["p-tides"], harness.state, harness.commitments,
        harness.blobs, vs_k=2, token_budget=2500,
        frame_slice_context=render_frame_slice_context(harness, "p-tides"),
        frame_crisis_context=render_frame_crisis_context(harness, "p-tides"),
    )
    assert "## frame-crisis" in pack and "## frame-slice" in pack
    assert "STANDING ATTACKERS" in pack
    assert "DEPARTURES ARE PERMITTED" in pack
    assert pack.index("## frame-crisis") < pack.index("## frame-slice")


# --- N2 / G6: the pack renderer is the memory policy -------------------------

def test_a_standing_attacker_at_cycle_k_still_renders_at_the_terminal_cycle(tmp_path):
    """G6 (N2). Persistence asserted AT THE TERMINAL step, never at injection.

    The convergence note's finding is that the record forgetting nothing does
    not make the pack remember: content that must keep ACTING has to keep
    RENDERING inside the horizon. So this drives eight cycles of accumulating
    state, injects the wound at cycle 2, and asks the question only at cycle
    8 -- the cycle where a renderer that had quietly stopped carrying it would
    look identical to one that never carried it at all.
    """
    from deepreason.llm.packs import render_conj_pack

    harness = Harness(tmp_path / "run")
    subject, _, _, _ = _framed(harness)
    problem = _problem(harness, "p-tides", "predict the spring tides here")

    wound = None
    packs_by_cycle = {}
    for cycle in range(1, 9):
        if cycle == 2:
            wound, _ = attack(harness, subject.id, "mispredicts-the-neap-tide")
        # Every later cycle adds ACCEPTED state, so the neighbourhood grows
        # and the pack competes for budget exactly as a real run's does. A
        # terminal render over a static graph would prove nothing: the whole
        # failure mode is a section that survives an empty pack and loses to
        # a full one.
        _art(harness, f"candidate produced at cycle {cycle} " + "detail " * 40)
        packs_by_cycle[cycle] = render_conj_pack(
            problem, harness.state, harness.commitments, harness.blobs,
            # 200, not a comfortable number: measured as the budget where a
            # DROPPABLE crisis section would be cut outright. A test run at
            # 300 passes with the section made droppable, and would therefore
            # have proved nothing about what keeps the wound in the pack.
            vs_k=2, token_budget=200,
            frame_slice_context=render_frame_slice_context(harness, "p-tides"),
            frame_crisis_context=render_frame_crisis_context(harness, "p-tides"),
        )

    assert wound is not None
    assert wound.id not in packs_by_cycle[1]
    for cycle in range(2, 9):
        assert wound.id in packs_by_cycle[cycle], cycle
    # The claim, made where it counts -- at the terminal cycle, in the PACK,
    # under a budget that has already dropped optional sections.
    assert wound.id in packs_by_cycle[8]
    assert "STANDING ATTACKERS" in packs_by_cycle[8]
    assert "## neighbourhood" not in packs_by_cycle[8]


def test_a_defeated_attacker_stops_occupying_a_crisis_slot(harness):
    """The cap makes "standing" load-bearing rather than decorative.

    A REFUTED attacker is an attack that was made and defeated -- not an open
    indictment. Rendering it would merely mislead if the list were unbounded;
    under the cap it would displace a LIVE attacker, so the crisis would
    understate itself in exactly the case where it matters most.
    """
    subject, _, _, _ = _framed(harness)
    _problem(harness, "p-tides", "predict the spring tides here")
    doomed, _ = attack(harness, subject.id, "an-objection-that-will-not-survive")
    assert doomed.id in render_frame_crisis_context(harness, "p-tides")

    attack(harness, doomed.id, "the-objection-misreads-the-tide-table")
    assert harness.state.status[doomed.id] == Status.REFUTED
    crisis = render_frame_crisis_context(harness, "p-tides")
    assert doomed.id not in crisis
    # And with no surviving attacker the block is ABSENT, not empty (N1).
    assert "STANDING ATTACKERS" not in crisis
    assert frame_slices(harness, "p-tides")[0].attackers_total == 0


def test_the_cap_can_displace_an_individual_attacker_and_says_so(harness):
    """The limit of G6, stated rather than left for a reader to discover.

    What persists is the CRISIS, not any particular attacker: under the cap,
    an early wound can be displaced by later ones whose ids sort lower. That
    is not a silent loss -- the count discloses it ("5 of 9 shown, by id") --
    but "a standing attacker present at cycle k still renders at cycle n" is
    true unconditionally only while the total is within the cap, and this
    test is what stops that being read as an unconditional guarantee.
    """
    subject, _, _, _ = _framed(harness)
    _problem(harness, "p-tides", "predict the spring tides here")
    made = [
        attack(harness, subject.id, f"fault-{i}")[0].id
        for i in range(FRAME_SLICE_ATTACKERS_N + 4)
    ]
    crisis = render_frame_crisis_context(harness, "p-tides")

    # `shown` is in registration order here, so compare as a SET against the
    # id-ordered prefix -- the claim is WHICH attackers survive the cap, not
    # the order this list comprehension happened to visit them in.
    shown = {a for a in made if a in crisis}
    assert len(shown) == FRAME_SLICE_ATTACKERS_N
    assert shown == set(sorted(made)[:FRAME_SLICE_ATTACKERS_N])
    # Displaced, but not silently: the total is in the pack.
    assert f"{FRAME_SLICE_ATTACKERS_N} of {len(made)} shown" in crisis
    assert set(made) - set(shown)


# --- R7 / G1: the third exit grade, and the anti-FrameDecisive check ---------

def _unresolved_attack_on(harness, target_id: str):
    """Attack `target_id` with a critic that is itself locked in an
    unresolved cycle, so the attacker is neither accepted nor defeated.

    A CYCLE is required, not a chain. An attacker attacked by an unattacked
    critic is simply refuted, and a chain of three REINSTATES the first
    attacker under grounded semantics -- the first version of this fixture
    built exactly that and produced `refuted` where it wanted `suspended`.

    Warrants attach only at artifact registration (there is no
    `register_warrant`), so the cycle is closed by letting the first critic
    name a target that does not exist yet, which `Harness` admits.
    """
    from deepreason.ontology import Artifact, Warrant, WarrantType

    nu_a = _art(harness, "nu: the overreach case is sound")
    nu_b = _art(harness, "nu: the rebuttal is sound")
    against_rebuttal = Warrant(
        id="w-overreach-vs-rebuttal", target="CRITIC-REBUTTAL",
        type=WarrantType.ARGUMENTATIVE, validity_node=nu_a.id,
    )
    against_target = Warrant(
        id="w-overreach-vs-frame", target=target_id,
        type=WarrantType.ARGUMENTATIVE, validity_node=nu_a.id,
    )
    harness.register_artifact(
        Artifact(
            id="CRITIC-OVERREACH",
            content_ref="inline:critic: this frame overreaches its scope",
            warrants=[against_rebuttal.id, against_target.id],
            provenance=Provenance(role="critic"),
        ),
        warrants=[against_rebuttal, against_target],
    )
    against_overreach = Warrant(
        id="w-rebuttal-vs-overreach", target="CRITIC-OVERREACH",
        type=WarrantType.ARGUMENTATIVE, validity_node=nu_b.id,
    )
    harness.register_artifact(
        Artifact(
            id="CRITIC-REBUTTAL",
            content_ref="inline:critic: the overreach case misreads the scope",
            warrants=[against_overreach.id],
            provenance=Provenance(role="critic"),
        ),
        warrants=[against_overreach],
    )


def _assertion_labelled(harness, target_status):
    """A consulted-shaped frame assertion driven to one of the three exit
    labels, by its OWN registration rather than by patching a status.

    Each grade needs a different graph, which is the point: if one setup
    could produce all three, the grades would be a relabelling of one
    condition rather than three reachable states.
    """
    subject, case, promotion, assertion = _framed(harness)
    if target_status is Status.REFUTED:
        # fall: the assertion itself is defeated by a warranted attack.
        attack(harness, assertion.id, "this-frame-was-never-earned")
    elif target_status is Status.SUSPENDED_UNSUPPORTED:
        # revocation: the reach case it DEPENDS on is refuted, so pass two
        # takes its support away. Orphaned, not false.
        attack(harness, case.id, "the-reach-records-were-contaminated")
    else:
        # contestation: the attacker is locked in an unresolved cycle, so it
        # is neither accepted nor defeated and the assertion is attacked by
        # something nobody has beaten. A CYCLE is required, not a chain: a
        # chain of three reinstates the first critic (grounded semantics), and
        # the first version of this fixture built one and produced `refuted`.
        _unresolved_attack_on(harness, assertion.id)
    assert harness.state.status[assertion.id] == target_status, (
        target_status, harness.state.status[assertion.id]
    )
    return assertion


@pytest.mark.parametrize(
    "label,grade",
    [
        (Status.REFUTED, "fall"),
        (Status.SUSPENDED_UNSUPPORTED, "revocation"),
        (Status.SUSPENDED, "contestation"),
    ],
)
def test_all_three_exit_grades_are_reachable_by_their_own_registration(
    tmp_path, label, grade
):
    """G1. Each grade reached by a DIFFERENT graph, and the render names it.

    This is the anti-`FrameDecisive` check. The Computable Calculus claims a
    consulted frame exits standing in exactly two ways; the Formalization
    (§8.2) shows that is true only under an extra axiom it never states --
    `FrameDecisive(L): ℓ_L(f) ≠ S`. If that axiom held, the third
    parametrisation here would be unreachable.
    """
    from deepreason.calculus.standing import standing_view

    harness = Harness(tmp_path / f"run-{grade}")
    assertion = _assertion_labelled(harness, label)

    assert exit_grade(label) == grade
    view = standing_view(harness)
    reported = [e for e in view["exits"] if e["assertion"] == assertion.id]
    assert len(reported) == 1, view["exits"]
    assert reported[0]["grade"] == grade
    assert reported[0]["label"] == label.value
    # It has left standing, whichever way: no grant, and no frame renders.
    assert view["grants"] == []


def test_the_three_grades_are_distinct_and_contestation_rounds_to_neither(tmp_path):
    """G1's second half, and the one the rider actually exists for.

    Three labels, three grades, no collapsing. A design that adopted
    `FrameDecisive` would map `S` onto `R` or `SU` and this would fail; so
    would a render that reported "not consulted" for all three, which is the
    lazier way to lose the distinction.
    """
    from deepreason.calculus.standing import standing_view

    seen = {}
    for label, grade in (
        (Status.REFUTED, "fall"),
        (Status.SUSPENDED_UNSUPPORTED, "revocation"),
        (Status.SUSPENDED, "contestation"),
    ):
        harness = Harness(tmp_path / f"root-{grade}")
        assertion = _assertion_labelled(harness, label)
        entry = next(
            e for e in standing_view(harness)["exits"]
            if e["assertion"] == assertion.id
        )
        seen[grade] = (entry["label"], entry["means"])

    assert len(seen) == 3
    assert len({v[0] for v in seen.values()}) == 3          # three labels
    assert len({v[1] for v in seen.values()}) == 3          # three meanings
    assert seen["contestation"][0] == Status.SUSPENDED.value
    assert seen["contestation"][1] != seen["fall"][1]
    assert seen["contestation"][1] != seen["revocation"][1]
    assert len(EXIT_GRADES) == 3 and len(set(EXIT_GRADES.values())) == 3
    assert exit_grade(Status.ACCEPTED) is None               # still standing


def test_no_module_rounds_a_suspended_frame_onto_a_neighbour(tmp_path):
    """G1, structurally. `FrameDecisive` is not adopted, asserted as an
    ABSENCE rather than trusted to stay unadopted: `EXIT_GRADES` is the one
    mapping from label to grade, it is injective, and `SUSPENDED` maps to
    neither of its neighbours' grades."""
    assert EXIT_GRADES[Status.SUSPENDED] not in (
        EXIT_GRADES[Status.REFUTED],
        EXIT_GRADES[Status.SUSPENDED_UNSUPPORTED],
    )
    assert set(EXIT_GRADES) == {
        Status.REFUTED, Status.SUSPENDED_UNSUPPORTED, Status.SUSPENDED
    }
    assert Status.ACCEPTED not in EXIT_GRADES


def test_the_cli_prints_all_three_grades_with_their_meanings(tmp_path):
    """R7 at the reader's surface. The grade names are not self-evident --
    "revocation" reads like a weaker "fall" unless it says otherwise -- so
    the text output prints each grade WITH what it means, and never collapses
    the three into "no longer framing"."""
    from deepreason.calculus.standing import standing_view
    from deepreason.cli.main import render_exit_grades

    for label, grade in (
        (Status.REFUTED, "fall"),
        (Status.SUSPENDED_UNSUPPORTED, "revocation"),
        (Status.SUSPENDED, "contestation"),
    ):
        harness = Harness(tmp_path / f"root-{grade}")
        _assertion_labelled(harness, label)
        out = "\n".join(render_exit_grades(standing_view(harness)))
        assert "LEFT STANDING" in out, grade
        assert grade in out, grade
        assert EXIT_GRADE_MEANINGS[grade] in out, grade
        assert label.value in out, grade
        for other in ("fall", "revocation", "contestation"):
            if other != grade:
                assert EXIT_GRADE_MEANINGS[other] not in out, (grade, other)

    # No exits, no heading -- not an empty one (N1, at the reader's surface).
    quiet = Harness(tmp_path / "quiet")
    _framed(quiet)
    assert render_exit_grades(standing_view(quiet)) == []


def test_the_standing_json_view_carries_the_exits(tmp_path):
    """The same three grades through `deepreason standing --json`, which is
    also what the MCP `run_standing` tool renders -- so the expansion path
    for a frame slice reaches both surfaces without either gaining a tool."""
    from deepreason.calculus.standing import standing_view

    harness = Harness(tmp_path / "run")
    assertion = _assertion_labelled(harness, Status.SUSPENDED)
    view = standing_view(harness)
    assert view["view"] == "standing.v1"
    entry = next(e for e in view["exits"] if e["assertion"] == assertion.id)
    assert set(entry) == {
        "assertion", "subject", "promotion_problem", "label", "grade", "means"
    }
    assert entry["grade"] == "contestation"
