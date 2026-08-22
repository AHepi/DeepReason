"""Frame assertions: Def 9.2, Law 9.4, Thm 12.3, and S-10's absence.

Implements R1, R2, R3, R10, R11 (v2 calculus program, Rung 4). A frame
assertion is an ORDINARY artifact -- no new event rule, no kind field, no
status of its own -- whose CONTENT is the frame claim. Every property below is
therefore a property of the ordinary graph, which is the whole point: the two
axes are separated by EDGE ROLE, not by a new node type.

`bounded` validity is content and not a third value (C3): instrument standing
is a consulted assertion whose validity happens to read `bounded`, and the
tolerance is authored and attackable like anything else.
"""

import pytest

from deepreason.calculus import operations
from deepreason.calculus.claims import (
    FRAME_ASSERTION_V1,
    ClaimDecodeError,
    FrameAssertionV1,
    decode,
    encode,
)
from deepreason.calculus.compiler import compile_interface
from deepreason.calculus.programs import FRAME_ASSERTION_COMMITMENT, frame_assertion_wf
from deepreason.calculus.separation import FRAME_NOT_SEPARATED
from deepreason.calculus.standing import consultability_of, standing_of
from deepreason.ontology import Interface, Provenance, Ref, Status
from deepreason.ontology.event import Rule
from deepreason.ontology.artifact import RefRole
from deepreason.programs import content_text
from tests.conftest import attack


SCOPE = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}


def _body(subject, cases=(), **kwargs):
    return FrameAssertionV1(
        subject_ref=subject,
        scope=SCOPE,
        departure_protocol="declare the departure in the pack and cite this id",
        reach_case_refs=list(cases),
        **kwargs,
    )


def _art(harness, text, refs=()):
    return harness.create_artifact(
        text,
        interface=Interface(refs=list(refs)),
        provenance=Provenance(role="critic"),
    )


def _framed(harness, *, description="why do tides follow the moon"):
    """A subject, its reach case, a promotion problem, and a filed assertion.

    The reach case MENTIONS nothing of the subject, which is what keeps the two
    in disjoint adjudication components (Def 7.2) rather than merely unlinked.
    """
    subject = _art(harness, "b: the lunar theory of tides")
    case = _art(harness, "reach record: this subject reached three lineages")
    problem = operations.ensure_promotion_problem(harness, subject.id, description)
    assertion = operations.file_frame_assertion(
        harness, problem=problem, subject_ref=subject.id,
        scope=SCOPE, reach_case_refs=(case.id,),
        departure_protocol="declare the departure in the pack and cite this id",
    )
    return subject, case, problem, assertion


# --- R1: an ordinary artifact carrying Def 9.2's content ---------------------

def test_a_frame_assertion_is_an_ordinary_artifact(harness):
    """R1. Registered by `create_artifact` like anything else: it appears in
    `state.artifacts`, receives an ordinary `Status`, and its registration
    commits the ordinary REGISTER rule."""
    _subject, _case, _problem, assertion = _framed(harness)
    assert assertion.id in harness.state.artifacts
    assert harness.state.status[assertion.id] == Status.ACCEPTED
    assert decode(content_text(assertion, harness.blobs)).schema_ == FRAME_ASSERTION_V1


def test_no_new_event_rule_and_no_kind_field(harness):
    """R1. Two absences, asserted rather than assumed. The body declares no
    `kind`, and registering an assertion emits only rules the harness already
    had -- a frame layer that needed its own event rule would be a second graph
    whose interaction with att, dep, replay and status is unproven."""
    assert "kind" not in FrameAssertionV1.model_fields
    _framed(harness)
    emitted = {e.rule for e in harness.log.read()}
    assert emitted <= {Rule.REGISTER, Rule.SPAWN}, sorted(r.value for r in emitted)


def test_bounded_validity_is_content_not_a_third_value(harness):
    """R1/C3. `bounded` is a CONTENT field with its domain and tolerance, not a
    third standing value: the derived view grants the same one relation either
    way, and the reader tells them apart by reading the content."""
    subject, case, problem, _ = _framed(harness)
    bounded = operations.file_frame_assertion(
        harness, problem=problem, subject_ref=subject.id, scope=SCOPE,
        reach_case_refs=(case.id,), departure_protocol="cite this id",
        validity="bounded", validity_domain="tidal amplitudes under 4 m",
        validity_tolerance="within 3 per cent",
    )
    grants = standing_of(harness, subject.id)
    assert {g.validity for g in grants} == {"universal", "bounded"}
    assert len({type(g) for g in grants}) == 1
    assert bounded.id in {g.assertion_id for g in grants}


def test_bounded_requires_its_domain_and_tolerance_and_universal_forbids_them():
    """R1/C3. The shape is enforced on the body, so a `bounded` assertion
    cannot silently become an unqualified one by omitting its tolerance."""
    with pytest.raises(ValueError):
        _body("b", validity="bounded")
    with pytest.raises(ValueError):
        _body("b", validity="universal", validity_domain="d",
              validity_tolerance="t")


def test_a_case_that_is_the_subject_is_refused():
    """R1/R2. A reach case that IS the subject would be a dependence on the
    subject under another name, which is exactly what Law 9.4 forbids."""
    with pytest.raises(ValueError):
        _body("b", cases=("b",))


# --- R2: the mention law ------------------------------------------------------

def test_the_compiler_makes_the_subject_a_mention_and_the_case_a_dependence():
    """R2, Law 9.4. The compiler is the only authority on ref roles: MENTION on
    the subject is what stops pass two dragging the assertion down when the
    subject is refuted; DEPENDENCE on the case is what makes refuting the case
    cut the assertion's support."""
    interface = compile_interface(_body("b", cases=("case-1",)))
    roles = {r.target: r.role.value for r in interface.refs}
    assert roles == {"b": "mention", "case-1": "dependence"}
    assert interface.commitments == [FRAME_ASSERTION_COMMITMENT.id]


def test_a_wound_reference_is_a_mention_never_a_dependence():
    """R2, Def 9.2: "mention -> the wounds of any incumbent it succeeds". A
    dependence would suspend the successor the moment the incumbent's wound was
    reinstated away."""
    interface = compile_interface(
        FrameAssertionV1(subject_ref="b", scope=SCOPE, departure_protocol="p",
                         succeeded_wound_refs=["w-1"])
    )
    assert {r.target: r.role.value for r in interface.refs} == {
        "b": "mention", "w-1": "mention"
    }


def test_an_assertion_that_depends_on_its_subject_fails_well_formedness(harness):
    """R2, Law 9.4, as a well-formedness commitment. The generic
    controller-compiled comparison would also reject this, but the diagnostic
    would say "interface not controller compiled" -- naming the LAW is what
    lets a reader tell a violated separation from a mis-registered artifact."""
    body = _body("b-1", cases=("case-1",))
    bad = _art(
        harness, encode(body),
        refs=[Ref(target="b-1", role=RefRole.DEPENDENCE),
              Ref(target="case-1", role=RefRole.DEPENDENCE)],
    )
    verdict, trace = frame_assertion_wf(encode(body), None, bad)
    assert verdict == "fail"
    assert trace["reason"] == "frame-assertion-depends-on-subject"


def test_a_controller_compiled_assertion_passes_well_formedness(harness):
    """R2. The positive half: without it the test above would pass on a
    program that failed everything."""
    body = _body("b-1", cases=("case-1",))
    good = _art(harness, encode(body), refs=compile_interface(body).refs)
    verdict, trace = frame_assertion_wf(encode(body), None, good)
    assert verdict == "pass", trace
    assert trace["schema"] == FRAME_ASSERTION_V1


def test_the_closed_name_set_did_not_grow():
    """R1. This rung supplies a PRODUCER for a name the closed set already
    declared. A set that grew would mean an ontology addition rode in on a
    rung that was only meant to build one."""
    from deepreason.calculus import CLAIM_SCHEMAS

    assert len(CLAIM_SCHEMAS) == 9
    assert FRAME_ASSERTION_V1 in CLAIM_SCHEMAS
    with pytest.raises(ClaimDecodeError) as caught:
        decode('{"schema": "poietic.succession.v1"}')
    assert caught.value.code == "claim-schema-not-implemented"


# --- R3: consult through Rung 3b's separation --------------------------------

def test_a_separated_assertion_addressed_to_a_promotion_problem_is_consulted(harness):
    """R3, Def 9.2. All four conditions met: recognised, addressed to a
    promotion problem, unrefuted, and separated from its subject."""
    subject, _case, _problem, assertion = _framed(harness)
    verdict = consultability_of(harness, assertion.id)
    assert verdict.consultable is True and verdict.code is None
    assert {g.assertion_id for g in standing_of(harness, subject.id)} == {assertion.id}


def test_an_unseparated_assertion_is_unconsultable_with_rung3bs_own_code(harness):
    """R3. Rung 3b's machinery is INVOKED, not re-implemented: the code this
    returns is `separation.FRAME_NOT_SEPARATED` itself, and `separation.py` is
    not edited by this rung. A reach case that DEPENDS on the subject puts the
    assertion and its subject in one adjudication component."""
    subject = _art(harness, "b: the lunar theory of tides")
    tainted = _art(harness, "reach record resting on the subject",
                   refs=[Ref(target=subject.id, role=RefRole.DEPENDENCE)])
    problem = operations.ensure_promotion_problem(harness, subject.id, "tides")
    assertion = operations.file_frame_assertion(
        harness, problem=problem, subject_ref=subject.id, scope=SCOPE,
        reach_case_refs=(tainted.id,), departure_protocol="cite this id",
    )
    verdict = consultability_of(harness, assertion.id)
    assert verdict.consultable is False
    assert verdict.code == FRAME_NOT_SEPARATED
    assert standing_of(harness, subject.id) == ()


def test_an_unconsultable_assertion_moves_no_edge_no_warrant_no_label(harness):
    """R3/R64. A failed engineering invariant is a reason to stop trusting a
    frame, never a reason to invent a defeat for it. Everything a manufactured
    refutation would have to move is compared WHOLE."""
    subject = _art(harness, "b: the lunar theory of tides")
    tainted = _art(harness, "reach record resting on the subject",
                   refs=[Ref(target=subject.id, role=RefRole.DEPENDENCE)])
    problem = operations.ensure_promotion_problem(harness, subject.id, "tides")
    assertion = operations.file_frame_assertion(
        harness, problem=problem, subject_ref=subject.id, scope=SCOPE,
        reach_case_refs=(tainted.id,), departure_protocol="cite this id",
    )
    before = (
        sorted(tuple(p) for p in harness.state.att),
        sorted(tuple(p) for p in harness.state.dep),
        dict(harness.state.status),
        sorted(harness.warrants),
        len((harness.root / "log.jsonl").read_text().splitlines()),
    )
    assert consultability_of(harness, assertion.id).consultable is False
    after = (
        sorted(tuple(p) for p in harness.state.att),
        sorted(tuple(p) for p in harness.state.dep),
        dict(harness.state.status),
        sorted(harness.warrants),
        len((harness.root / "log.jsonl").read_text().splitlines()),
    )
    assert before == after


def test_an_assertion_outside_a_promotion_problem_is_never_consulted(harness):
    """R3, Def 9.2 and Remark 9.5's closure. "A frame assertion born anywhere
    else is an ordinary artifact the renderer ignores" -- so an assertion that
    is separated, unrefuted and perfectly well formed still grants no standing
    when the problem it addresses is an ordinary one."""
    from deepreason.ontology import Problem, ProblemProvenance, SpawnTrigger

    subject = _art(harness, "b: the lunar theory of tides")
    case = _art(harness, "reach record")
    ordinary = harness.register_problem(Problem(
        id="pi-ordinary", description="why do tides follow the moon",
        provenance=ProblemProvenance(trigger=SpawnTrigger.SEED, **{"from": []}),
    ))
    assertion = operations.file_frame_assertion(
        harness, problem=ordinary, subject_ref=subject.id, scope=SCOPE,
        reach_case_refs=(case.id,), departure_protocol="cite this id",
    )
    verdict = consultability_of(harness, assertion.id)
    assert verdict.consultable is False
    assert verdict.code == "frame-not-addressed-to-promotion"
    assert standing_of(harness, subject.id) == ()


def test_ensure_promotion_problem_is_idempotent(harness):
    """R3/S8. Deterministic and idempotent in the `ensure_problem_subject`
    shape: the id is a pure function of the subject, so a crash between the
    registration and the assertion is repaired by running it again."""
    subject = _art(harness, "b: the lunar theory of tides")
    first = operations.ensure_promotion_problem(harness, subject.id, "tides")
    count = len(harness.state.problems)
    second = operations.ensure_promotion_problem(harness, subject.id, "tides")
    assert first.id == second.id
    assert len(harness.state.problems) == count


# --- R10 / R11: Thm 12.3's exits, and the revocation rule that does not exist -

def test_a_frame_assertion_inherits_every_exit(harness):
    """R10, Thm 12.3. Three exits on one assertion, each a constructible
    registration rather than a special frame-layer path -- which is what "no
    absorbing status" means for the standing axis."""
    _subject, case, _problem, assertion = _framed(harness)
    assert harness.state.status[assertion.id] == Status.ACCEPTED

    critic, validity_node = attack(harness, assertion.id, "direct-attack")
    assert harness.state.status[assertion.id] == Status.REFUTED

    # Lemma 6.1: reinstate by attacking the attacker's validity node.
    attack(harness, validity_node.id, "the-attack-is-not-relevant")
    assert harness.state.status[assertion.id] == Status.ACCEPTED

    # Losing its case suspends it unsupported -- orphaned, not false.
    attack(harness, case.id, "the-reach-record-is-not-held-out")
    assert harness.state.status[assertion.id] == Status.SUSPENDED_UNSUPPORTED
    assert critic.id in harness.state.artifacts


def test_revocation_has_no_rule_of_its_own(harness):
    """R11, S-10. Asserted in both admissible forms, because either alone is
    satisfiable by the wrong thing: a structural scan alone is satisfied by
    naming the code something else, and a behavioural exhibit alone does not
    show the absence.

    Structural: no revocation symbol or branch anywhere in the package.
    Behavioural: revocation nonetheless HAPPENS, by attacking the reach case
    and nothing more -- which is the point. "Orphaned != false does exactly the
    right work: revocation says unearned, not wrong."
    """
    import ast
    import pathlib

    package = pathlib.Path("src/deepreason/calculus")
    named = []
    for path in sorted(package.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            name = getattr(node, "name", None) or getattr(node, "id", None) \
                or getattr(node, "attr", None) or getattr(node, "arg", None)
            if isinstance(name, str) and (
                "revoke" in name.lower() or "revocation" in name.lower()
            ):
                named.append(f"{path.name}:{name}")
    # Names, not prose: the docstrings here EXPLAIN the absence, and a scan
    # that counted the explanation would force the absence to go unexplained.
    assert named == [], named

    subject, case, _problem, _assertion = _framed(harness)
    assert standing_of(harness, subject.id) != ()
    attack(harness, case.id, "contaminated")
    assert standing_of(harness, subject.id) == ()
    assert harness.state.status[subject.id] == Status.ACCEPTED
