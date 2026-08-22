"""Reflexive-machinery discipline (Def 3.7 as amended + approved corrections):
reach is cross-problem survival, never textual reference; full hits register
addressing; thin batteries yield provisional hits; debt problems pose the
genuine explanatory question; relation candidates fail on form without a
named kind and a refutation condition; reflexive descendants stay inside the
shared budget; HV equivalence is decided by verdict vectors, embedding only
as pre-filter/fallback."""

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
    Status,
)
from deepreason.measures.reach import _substantive, reach_sweep
from deepreason.rules.spawn import scan_spawns
from deepreason.scheduler.scheduler import reflexive_problems


def _problem(h, pid, criteria, trigger="seed", from_=()):
    return h.register_problem(Problem(
        id=pid, description=f"problem {pid}", criteria=list(criteria),
        provenance=ProblemProvenance.model_validate(
            {"trigger": trigger, "from": list(from_)}),
    ))


def test_textual_reference_alone_creates_no_reach(tmp_path):
    """An artifact MENTIONING another problem's artifacts/ids is not reach;
    a rubric-only foreign battery cannot ground reach either."""
    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-home", eval="predicate:'tide' in content"))
    h.register_commitment(Commitment(id="k-rubric", eval="rubric:std-x"))
    _problem(h, "home", ["k-home"])
    _problem(h, "foreign", ["k-rubric"])  # rubric-only: unguarded here
    other = h.create_artifact("something else entirely",
                              provenance=Provenance(role="conjecturer"),
                              problem_id="foreign")
    a = h.create_artifact(
        f"the tide text mentions artifact {other.id} and problem foreign at length",
        provenance=Provenance(role="conjecturer"), problem_id="home")
    hits = reach_sweep(h)
    assert hits == []
    assert h.state.reach.get(a.id, 0.0) == 0.0
    assert (a.id, "foreign") not in h.state.addr


def test_structural_programs_never_ground_reach(tmp_path):
    from deepreason.unification.isolation import lineage_ref_commitment

    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-home", eval="predicate:len(content) > 0"))
    _problem(h, "home", ["k-home"])
    anchor = h.create_artifact("anchor", provenance=Provenance(role="seed"),
                               problem_id="home")
    lineage = lineage_ref_commitment([anchor.id])
    h.register_commitment(lineage)
    _problem(h, "conn-like", [lineage.id])  # structural-only battery
    from deepreason.ontology import Ref

    a = h.create_artifact(
        "connected thing", provenance=Provenance(role="conjecturer"),
        interface=Interface(refs=[Ref(target=anchor.id, role="dependence")]),
        problem_id="home")
    assert reach_sweep(h) == []          # lineage_ref passes but grounds nothing
    assert (a.id, "conn-like") not in h.state.addr


def test_genuine_cross_problem_survival_registers_addressing(tmp_path):
    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    h.register_commitment(Commitment(id="k-sea", eval="predicate:'sea' in content"))
    _problem(h, "home", ["k-moon"])
    _problem(h, "foreign", ["k-sea"])
    a = h.create_artifact("the moon pulls the sea",
                          provenance=Provenance(role="conjecturer"),
                          problem_id="home")
    hits = reach_sweep(h)
    assert hits == [(a.id, "foreign")]
    assert (a.id, "foreign") in h.state.addr       # the normative amendment
    assert h.state.reach[a.id] == 1.0
    # and it replays: a cold open carries the addressing
    h2 = Harness(tmp_path / "run")
    assert (a.id, "foreign") in h2.state.addr


def test_thin_coverage_yields_provisional_not_reach(tmp_path):
    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    h.register_commitment(Commitment(id="k-sea", eval="predicate:'sea' in content"))
    h.register_commitment(Commitment(id="k-rubric", eval="rubric:std-x"))
    _problem(h, "home", ["k-moon"])
    # foreign: 1 substantive evaluable of 3 total criteria -> coverage 1/3
    _problem(h, "foreign", ["k-sea", "k-rubric", "k-missing"])
    a = h.create_artifact("the moon pulls the sea",
                          provenance=Provenance(role="conjecturer"),
                          problem_id="home")
    hits = reach_sweep(h, coverage_min=0.5)
    assert hits == []
    assert (a.id, "foreign") not in h.state.addr
    prov = [e for e in h.log.read()
            if e.rule == Rule.MEASURE and e.inputs
            and e.inputs[0] == "reach-provisional"]
    assert len(prov) == 1 and prov[0].inputs[1] == a.id


def test_debt_problem_asks_the_genuine_question(tmp_path):
    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    h.register_commitment(Commitment(id="k-sea", eval="predicate:'sea' in content"))
    _problem(h, "home", ["k-moon"])
    _problem(h, "foreign", ["k-sea"])
    a = h.create_artifact("the moon pulls the sea",
                          provenance=Provenance(role="conjecturer"),
                          problem_id="home")
    reach_sweep(h)
    scan_spawns(h, Config(N_SCHOOLS=0))
    debt = h.state.problems[f"debt:{a.id[:12]}"]
    text = debt.description.lower()
    assert "single explanation" in text and "never commentary" in text
    # the union attack surface travels with the question
    assert set(debt.criteria) == {"k-moon", "k-sea"}


def test_summary_only_relation_fails_on_form(tmp_path):
    from deepreason import programs
    from deepreason.unification.isolation import relation_form_commitment

    h = Harness(tmp_path / "run")
    gate = relation_form_commitment()
    h.register_commitment(gate)
    summary = h.create_artifact(
        "Artifact A says the moon pulls the sea; artifact B says palaces "
        "fell. Both are interesting.",
        interface=Interface(commitments=[gate.id]),
        provenance=Provenance(role="synthesizer"))
    v, _ = programs.evaluate(gate, summary, h.blobs)
    assert v == "fail"                    # a summary is not a relation
    substantive = h.create_artifact(
        "B reduces to A: the palace collapse is a special case of tidal "
        "forcing. REFUTED IF any palace fell during a neap tide.",
        interface=Interface(commitments=[gate.id]),
        provenance=Provenance(role="synthesizer"))
    v, _ = programs.evaluate(gate, substantive, h.blobs)
    assert v == "pass"


def test_reflexive_budget_follows_lineage(tmp_path):
    """A DESCENDANT of a debt problem stays reflexive; one descending from
    independent work does not; mixed parentage is independent.

    Re-founded on `discrimination` (operator ruling 2026-08-15: "There was a website development pipeline
    that I decommissioned a while ago. That needs to stay decommissioned."). The descendants used to
    carry SUCCESSOR, whose last producer was a remnant of that pipeline. The
    property under test is that the reflexive budget follows LINEAGE rather
    than the trigger, so it needs a descending trigger that is NOT itself
    reflexive -- which is exactly what SUCCESSOR was, and what discrimination
    is now. Re-founding, not weakening: the same asymmetry is asserted.
    """
    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-a", eval="predicate:len(content) > 0"))
    _problem(h, "pi-root", ["k-a"])
    _problem(h, "debt:abc", ["k-a"], trigger="explanation-debt", from_=["pi-root"])
    on_debt = h.create_artifact("x", provenance=Provenance(role="conjecturer"),
                                problem_id="debt:abc")
    _problem(h, "succ:ofdebt", ["k-a"], trigger="discrimination",
             from_=[on_debt.id, "debt:abc"])
    on_root = h.create_artifact("y", provenance=Provenance(role="conjecturer"),
                                problem_id="pi-root")
    _problem(h, "succ:ofroot", ["k-a"], trigger="discrimination",
             from_=[on_root.id, "pi-root"])
    reflexive = reflexive_problems(h.state)
    assert "debt:abc" in reflexive
    assert "succ:ofdebt" in reflexive     # lineage keeps drawing the budget
    assert "succ:ofroot" not in reflexive
    assert "pi-root" not in reflexive


def test_hv_equivalence_decided_by_verdict_vectors(tmp_path):
    """Vectors that differ are authoritative regardless of embedding
    proximity; vectors that agree decide only with discriminating margin."""
    from deepreason.measures.hv import _equivalence_battery, _equivalent

    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    h.register_commitment(Commitment(id="k-sea", eval="predicate:'sea' in content"))
    a = h.create_artifact("the moon pulls the sea",
                          interface=Interface(commitments=["k-moon"]),
                          provenance=Provenance(role="conjecturer"))

    class GluedEmbedder:  # calls everything identical: must NOT decide
        model = "glued"

        def embed(self, text):
            return [1.0, 0.0]

    battery = _equivalence_battery(h, a)
    assert battery == ["k-moon", "k-sea"]
    # differs on k-sea -> inequivalent, even though the embedder is glued
    assert not _equivalent(
        "the moon pulls the sea", "the moon pulls the tide",
        embedder=GluedEmbedder(), harness=h, equiv_battery=battery,
        pass_battery=["k-moon"],
    )
    # agrees on k-sea too, and k-sea is margin beyond the pass battery ->
    # equivalent, authoritatively (no embedding involved)
    assert _equivalent(
        "the moon pulls the sea", "the moon drags the sea",
        embedder=None, harness=h, equiv_battery=battery,
        pass_battery=["k-moon"],
    )


def test_reflexive_candidates_dont_flood_survivors(tmp_path):
    """Integration guard at the scheduler level: with the reflexive budget
    at zero, debt/conn/integ problems are never selected."""
    import json

    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.scheduler.scheduler import Scheduler

    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-a", eval="predicate:'idea' in content"))
    _problem(h, "pi-root", ["k-a"])
    _problem(h, "debt:x", ["k-a"], trigger="explanation-debt", from_=["pi-root"])
    conj = json.dumps({"candidates": [{"content": "an idea", "typicality": 0.9}]})
    adapter = LLMAdapter({"conjecturer": MockEndpoint([conj] * 8)}, h.blobs)
    sched = Scheduler(h, adapter, Config(VS_K=1, N_SCHOOLS=0, FUZZ_N=0,
                                         INTEGRATION_BUDGET_SHARE=0.0))
    for _ in range(4):
        sched.step()
    assert "debt:x" not in sched._problem_worked
    addressed_debt = [aid for aid, pid in h.state.addr if pid == "debt:x"
                      and h.state.artifacts[aid].provenance.role.value == "conjecturer"]
    assert addressed_debt == []


def test_paraphrase_only_reflexive_artifact_is_the_failure_condition(tmp_path):
    """The refined acceptance criterion: an accepted reflexive artifact that
    merely paraphrases existing artifacts WITHOUT a new criticisable
    commitment is the failure; the relation-form gate makes it mechanical
    for relation candidates."""
    from deepreason import programs
    from deepreason.unification.isolation import relation_form_commitment

    h = Harness(tmp_path / "run")
    gate = relation_form_commitment()
    h.register_commitment(gate)
    paraphrase = h.create_artifact(
        "In other words, the first artifact's claim restated: the moon "
        "pulls the sea, which the second artifact also discusses.",
        interface=Interface(commitments=[gate.id]),
        provenance=Provenance(role="synthesizer"))
    v, _ = programs.evaluate(gate, paraphrase, h.blobs)
    assert v == "fail"
    # and with crit_program the failure lands as an ordinary refutation
    from deepreason.rules.crit import crit_program

    crit_program(h, paraphrase.id)
    assert h.state.status[paraphrase.id] == Status.REFUTED


def _wf_commitment():
    """The commitment `seed_reasoning_workload` mints, byte for byte
    (workloads/text.py) -- a different budget would gate different content."""
    from deepreason.ontology.commitment import Budget

    return Commitment(
        id="reasoning-envelope-wf",
        eval="program:reasoning-envelope-wf",
        budget=Budget(steps=10_000, time_ms=2_000, extra={"max_chars": 64_000}),
    )


def test_declared_structural_programs_are_never_substantive():
    """Regression (tranche experiments/2026-08-22-reach-structural-programs-fix,
    reproduction R1): reach's structural set was a hand-kept second copy of the
    class `programs.PROGRAMS` declares, and it had drifted five names behind it
    (component_wf, generator_wf, integration_wf, manifest_wf,
    reasoning-envelope-wf), so each of those could ground reach and confer
    prose immunity while declaring itself structural.

    Asserted over the DECLARATION, never over a fixed list of names: a program
    registered `class_="structural"` tomorrow is covered the day it is declared,
    and this test cannot go red merely because the registry grew.
    """
    from deepreason.measures.reach import _STRUCTURAL_PROGRAMS, _substantive
    from deepreason.programs import PROGRAMS, programs_by_class

    declared = set(programs_by_class()["structural"])
    assert declared, "the structural class is never empty"
    assert declared == set(_STRUCTURAL_PROGRAMS)
    # The boundary still admits what it always admitted: a predicate over
    # content, and any non-structural program.
    assert _substantive(Commitment(id="k-p", eval="predicate:'x' in content"))
    for name, spec in PROGRAMS.items():
        kappa = Commitment(id=f"k-{name}", eval=f"program:{name}")
        assert _substantive(kappa) is (spec.class_ != "structural")


def test_a_well_formedness_gate_cannot_veto_a_reach_hit(tmp_path):
    """Regression (tranche experiments/2026-08-22-reach-structural-programs-fix,
    reproduction R2; rehearsal evidence
    experiments/2026-08-22-live-reach-rich-run/rehearsal.json S8a/S8b/S8c):
    the shape every text run has.

    A conn:/integ: candidate is prose carrying only the three auto-spawn
    structural commitments, so a seed problem's subject predicates are novel to
    it. While `reasoning-envelope-wf` counted as substantive it entered the
    foreign problem's QUALIFYING set, where every criterion must pass -- and it
    fails on prose by construction. A well-formedness check therefore vetoed a
    hit the subject criteria had already settled, which is why no text run
    could record a reach event.

    The control in the same fixture is what makes this a fix rather than a
    loosening: an on-form but OFF-SUBJECT candidate, against the identical
    batteries, must still record nothing.
    """
    from deepreason.config import Config
    from deepreason.measures.hv import hv_floor_commitment
    from deepreason.unification.isolation import (
        lineage_ref_commitment,
        relation_form_commitment,
    )
    from deepreason.workloads.models import compile_interface

    on_subject = (
        "Relation kind: shared mechanism. Both accounts turn on the same "
        "nocturnal release of stored daytime solar gain: urban surfaces "
        "combine high thermal mass with low albedo. REFUTED IF a city whose "
        "surfaces have low thermal mass shows the same night-time gap."
    )
    off_subject = (
        "Relation kind: dependence. The second account depends on the first. "
        "REFUTED IF the dependence does not hold."
    )

    def _sweep(content):
        h = Harness(tmp_path / f"run-{len(content)}")
        wf = _wf_commitment()
        seed = Commitment(id="k-mass",
                          eval="predicate:'thermal mass' in content.lower()")
        other = Commitment(id="k-night",
                           eval="predicate:'nocturnal' in content.lower()")
        home_battery = [relation_form_commitment(), hv_floor_commitment(Config()),
                        lineage_ref_commitment(["a" * 64])]
        for kappa in [*home_battery, wf, seed, other]:
            h.register_commitment(kappa)
        home = _problem(h, "home", [c.id for c in home_battery])
        foreign = _problem(h, "foreign", [wf.id, seed.id, other.id])
        a = h.create_artifact(content, provenance=Provenance(role="conjecturer"),
                              problem_id=home.id,
                              interface=compile_interface(h, home, content))
        # Unattacked, so the grounded extension already labels it ACCEPTED.
        # Asserting rather than forcing keeps the fixture to a state a real
        # run can reach.
        assert h.state.status[a.id] == Status.ACCEPTED
        qualifying = [c for c in foreign.criteria
                      if _substantive(h.commitments[c])]
        return h, a, qualifying, reach_sweep(h)

    h, a, qualifying, hits = _sweep(on_subject)
    assert "reasoning-envelope-wf" not in qualifying
    assert sorted(qualifying) == ["k-mass", "k-night"]
    assert hits == [(a.id, "foreign")]
    assert (a.id, "foreign") in h.state.addr
    assert h.state.reach[a.id] == 1.0

    h2, a2, qualifying2, hits2 = _sweep(off_subject)
    assert sorted(qualifying2) == ["k-mass", "k-night"]
    assert hits2 == []
    assert (a2.id, "foreign") not in h2.state.addr
    assert h2.state.reach.get(a2.id, 0.0) == 0.0
