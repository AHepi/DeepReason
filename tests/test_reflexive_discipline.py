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
from deepreason.measures.reach import reach_sweep
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
    """A successor of a debt problem stays reflexive; a problem descending
    from independent work does not; mixed parentage is independent."""
    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-a", eval="predicate:len(content) > 0"))
    _problem(h, "pi-root", ["k-a"])
    _problem(h, "debt:abc", ["k-a"], trigger="explanation-debt", from_=["pi-root"])
    on_debt = h.create_artifact("x", provenance=Provenance(role="conjecturer"),
                                problem_id="debt:abc")
    _problem(h, "succ:ofdebt", ["k-a"], trigger="successor",
             from_=[on_debt.id, "debt:abc"])
    on_root = h.create_artifact("y", provenance=Provenance(role="conjecturer"),
                                problem_id="pi-root")
    _problem(h, "succ:ofroot", ["k-a"], trigger="successor",
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
