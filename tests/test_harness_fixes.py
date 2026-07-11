"""Regression tests for three evidence-backed fixes (from live 200k runs):

1. remove-arbitrariness spawns carry the ROOT problem's description + criteria,
   so the ra-loop stays anchored instead of drifting off-problem.
2. generator_metrics exposes an embedder-agnostic school-separation ratio, so
   a RESEED_DIST_MIN that is below the embedder's distance scale is visible.
3. why() on a refuted status surfaces the sanctioned reinstatement move
   (criticize the critic), the load-bearing operator mechanic that was unwritten.
"""

from deepreason import programs
from deepreason.capture import detection, schools
from deepreason.config import Config
from deepreason.llm.embedder import HashingEmbedder
from deepreason.llm.packs import render_conj_pack
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
    Status,
)
from deepreason.ontology.artifact import RefRole
from deepreason.rules.crit import crit_program
from deepreason.rules.spawn import scan_spawns
from deepreason.unification.isolation import lineage_ref_commitment
from deepreason.views.why import why
from tests.conftest import art, attack


def _conj(harness, text, **kw):
    return harness.create_artifact(text, provenance=Provenance(role="conjecturer", **kw))


# ---- Fix 1: remove-arbitrariness stays anchored to the root problem ---------

def test_remove_arbitrariness_carries_root_description_and_criteria(harness):
    harness.register_commitment(Commitment(id="c-fmt", eval="predicate:True"))
    harness.register_problem(
        Problem(
            id="pi-root",
            description="explain the SPECIFIC_ROOT_TOPIC in concrete terms",
            criteria=["c-fmt"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    a = harness.create_artifact(
        "a candidate answer",
        interface=Interface(commitments=["c-fmt"]),
        provenance=Provenance(role="conjecturer"),
        problem_id="pi-root",
    )
    assert harness.state.status[a.id] == Status.ACCEPTED
    harness.record_measure(hv={a.id: 0.1})  # easy-to-vary => below the 0.5 floor

    scan_spawns(harness, Config())

    ra = harness.state.problems[f"ra:{a.id[:12]}"]
    assert ra.provenance.trigger.value == "remove-arbitrariness"
    # Anchored: the root problem's topic rides into the ra-pack...
    assert "SPECIFIC_ROOT_TOPIC" in ra.description
    # ...and the format/content contract (criteria) is inherited.
    assert "c-fmt" in ra.criteria
    # Idempotent rescan.
    n = len(harness.state.problems)
    scan_spawns(harness, Config())
    assert len(harness.state.problems) == n


def test_ra_conjecture_pack_is_anchored_not_drifting(harness):
    """The drift problem, end-to-end: the remove-arbitrariness re-attempt used
    to be conditioned on a contextless "remove arbitrariness of <id>" pack, so
    the generator had nothing holding it to the topic and long runs wandered
    off-problem. This checks the fix at the point that actually matters — the
    rendered conjecture pack the generator sees — and contrasts it with the
    pre-fix contextless pack to guard against regressing the description."""
    harness.register_commitment(Commitment(id="c-fmt", eval="predicate:True"))
    harness.register_problem(
        Problem(
            id="pi-root",
            description="explain the SPECIFIC_ROOT_TOPIC in concrete terms",
            criteria=["c-fmt"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    a = harness.create_artifact(
        "a candidate answer",
        interface=Interface(commitments=["c-fmt"]),
        provenance=Provenance(role="conjecturer"),
        problem_id="pi-root",
    )
    harness.record_measure(hv={a.id: 0.1})
    scan_spawns(harness, Config())
    ra = harness.state.problems[f"ra:{a.id[:12]}"]

    budget = Config().PACK_TOKEN_BUDGET
    anchored = render_conj_pack(
        ra, harness.state, harness.commitments, harness.blobs, vs_k=3, token_budget=budget
    )
    # The generator is now conditioned on the ORIGINAL problem => it cannot
    # drift off-topic the way the contextless loop did.
    assert "SPECIFIC_ROOT_TOPIC" in anchored

    # Regression guard: the pre-fix contextless ra description carries no topic.
    bare = Problem(
        id="ra-bare",
        description=f"remove arbitrariness of accepted {a.id[:12]} (hv=0.10)",
        criteria=[],
        provenance=ProblemProvenance.model_validate(
            {"trigger": "remove-arbitrariness", "from": [a.id]}
        ),
    )
    bare_pack = render_conj_pack(
        bare, harness.state, harness.commitments, harness.blobs, vs_k=3, token_budget=budget
    )
    assert "SPECIFIC_ROOT_TOPIC" not in bare_pack


def test_remove_arbitrariness_skips_artifacts_addressing_no_problem(harness):
    # An accepted artifact with a low HV but addressing no problem has no root
    # to anchor to, so it spawns nothing (you can only sharpen it FOR a problem).
    a = art(harness, "orphan artifact")
    harness.record_measure(hv={a.id: 0.1})
    scan_spawns(harness, Config())
    assert f"ra:{a.id[:12]}" not in harness.state.problems


# ---- Fix 2: embedder-agnostic school-separation ratio is exposed ------------

def test_generator_metrics_exposes_scale_normalized_school_ratio(harness):
    for school, texts in {
        "A": ["gear pressure torque linkage", "lever fulcrum load moment"],
        "B": ["anomaly refutation boundary case", "counterexample falsifier exception"],
    }.items():
        for t in texts:
            harness.create_artifact(t, provenance=Provenance(role="conjecturer", school=school))

    m = detection.generator_metrics(harness, HashingEmbedder(), window=20)
    assert m["inter_school_min_dist"] is not None
    assert m["mean_pairwise_dist"] is not None
    # The ratio is the absolute separation normalized by the within-stream
    # spread — embedder-agnostic, so RESEED_DIST_MIN's calibration is visible.
    assert m["inter_school_dist_ratio"] is not None
    assert abs(
        m["inter_school_dist_ratio"] - m["inter_school_min_dist"] / m["mean_pairwise_dist"]
    ) < 1e-9


def test_school_ratio_is_none_without_two_schools(harness):
    harness.create_artifact("only one school", provenance=Provenance(role="conjecturer", school="A"))
    m = detection.generator_metrics(harness, HashingEmbedder(), window=20)
    assert m["inter_school_dist_ratio"] is None  # no inter-school pair


# ---- Fix 3: why() surfaces the criticize-the-critic reinstatement move ------

def test_why_refuted_surfaces_criticize_the_critic(harness):
    target = art(harness, "a bold claim")
    attack(harness, target.id, "flawed")
    assert harness.state.status[target.id] == Status.REFUTED

    out = why(target.id, harness.state)
    assert "Criticize the CRITIC" in out
    assert "REINSTATED" in out


def test_why_accepted_has_no_hint(harness):
    a = art(harness, "an unattacked claim")
    assert harness.state.status[a.id] == Status.ACCEPTED
    out = why(a.id, harness.state)
    assert "Criticize the CRITIC" not in out


# ---- Fix #2: structural lineage-ref catches abstraction escape at the program level

def test_lineage_ref_passes_with_dependence_into_lineage(harness):
    ep = art(harness, "an endpoint in the lineage")
    lineage = lineage_ref_commitment([ep.id])
    harness.register_commitment(lineage)
    good = harness.create_artifact(
        "a genuine bridge",
        interface=Interface(commitments=[lineage.id], refs=[Ref(target=ep.id, role=RefRole.DEPENDENCE)]),
        provenance=Provenance(role="conjecturer"),
    )
    verdict, _ = programs.evaluate(lineage, harness.state.artifacts[good.id], harness.blobs)
    assert verdict == "pass"


def test_lineage_ref_refutes_import_from_nowhere(harness):
    ep = art(harness, "an endpoint in the lineage")
    lineage = lineage_ref_commitment([ep.id])
    harness.register_commitment(lineage)
    orphan = harness.create_artifact(
        "imported from nowhere (no dependence ref)",
        interface=Interface(commitments=[lineage.id]),
        provenance=Provenance(role="conjecturer"),
    )
    assert harness.state.status[orphan.id] == Status.ACCEPTED
    crit_program(harness, orphan.id)  # program criticism, not a rubric judge
    assert harness.state.status[orphan.id] == Status.REFUTED


def test_connection_problem_pins_lineage_ref_commitment(harness):
    harness.register_commitment(Commitment(id="c-fmt", eval="predicate:True"))
    harness.register_problem(
        Problem(
            id="pi",
            description="root",
            criteria=["c-fmt"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    a = harness.create_artifact(
        "an isolated accepted artifact",
        interface=Interface(commitments=["c-fmt"]),
        provenance=Provenance(role="conjecturer"),
        problem_id="pi",
    )
    assert harness.state.status[a.id] == Status.ACCEPTED  # no dependence edges => isolated
    scan_spawns(harness, Config(FLOOR=1))
    conn = harness.state.problems.get(f"conn:{a.id[:12]}")
    assert conn is not None
    assert any(c.startswith("lineage-ref@") for c in conn.criteria)
    assert any(c.startswith("hv-floor@") for c in conn.criteria)


# ---- Calibration: the embedder-agnostic ratio firing path for school_convergence

def _two_schools(harness):
    for school, texts in {
        "school-0": ["gear pressure torque linkage", "lever fulcrum load moment"],
        "school-1": ["anomaly refutation boundary case", "counterexample falsifier exception"],
    }.items():
        for t in texts:
            _conj(harness, t, school=school)


def test_school_convergence_ratio_path(harness):
    _two_schools(harness)
    ratio = detection.generator_metrics(harness, HashingEmbedder(), 20)["inter_school_dist_ratio"]
    assert ratio is not None and ratio > 0.02
    emb = HashingEmbedder()
    # Absolute path pinned off (0.01 << hot hashing distances) to isolate the ratio path.
    off = Config(RESEED_DIST_MIN=0.01)  # RESEED_RATIO_MAX defaults to None
    assert detection.raw_flags(harness, emb, off)["school_convergence"] is False
    fires = Config(RESEED_DIST_MIN=0.01, RESEED_RATIO_MAX=ratio + 0.01)
    assert detection.raw_flags(harness, emb, fires)["school_convergence"] is True
    quiet = Config(RESEED_DIST_MIN=0.01, RESEED_RATIO_MAX=ratio - 0.01)
    assert detection.raw_flags(harness, emb, quiet)["school_convergence"] is False


# ---- Fix #3: forced cross-school crossover on a convergence reseed

def test_reseed_records_crossover_and_exemplars_pulls_foreign(harness):
    schools.init_schools(harness, Config(N_SCHOOLS=2))
    b = _conj(harness, "a foreign lineage idea", school="school-1")
    assert harness.state.status[b.id] == Status.ACCEPTED
    roster = schools.roster(harness)
    schools.reseed(harness, "school-0", roster["school-0"], reason="t", crossover_from="school-1")
    assert schools.roster(harness)["school-0"]["crossover_from"] == "school-1"
    assert b.id in schools.crossover_exemplars(harness, "school-0")


def test_crossover_exemplars_empty_without_pending_crossover(harness):
    schools.init_schools(harness, Config(N_SCHOOLS=2))
    _conj(harness, "a foreign lineage idea", school="school-1")
    assert schools.crossover_exemplars(harness, "school-0") == []


def test_conj_pack_renders_forced_crossover_section(harness):
    b = _conj(harness, "foreign idea X to reconcile", school="school-1")
    harness.register_problem(
        Problem(
            id="pi",
            description="root",
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    pack = render_conj_pack(
        harness.state.problems["pi"], harness.state, harness.commitments, harness.blobs,
        vs_k=3, token_budget=Config().PACK_TOKEN_BUDGET,
        school={"id": "school-0", "stance_text": "x", "weight": 0.5, "crossover": [b.id]},
    )
    assert "CROSSOVER" in pack
    assert b.id in pack


# ---- evidence_lambda: truly-exogenous grounding, distinct from spec lambda ----

def test_evidence_lambda_none_without_empirical_claims(harness):
    # A design/explanatory run (no observation_valued commitments) => grounding
    # is NOT applicable => None, not 0.0 (so the opt-in brake never fires on it).
    harness.register_commitment(Commitment(id="c-fmt", eval="predicate:True"))
    harness.create_artifact(
        "a pure design idea",
        interface=Interface(commitments=["c-fmt"]),
        provenance=Provenance(role="conjecturer"),
    )
    assert detection.evidence_lambda(harness) is None


def test_evidence_lambda_zero_when_empirical_claim_uncovered(harness):
    harness.register_commitment(
        Commitment(id="k-obs", eval="predicate:True", observation_valued=True)
    )
    harness.create_artifact(
        "an ungrounded empirical claim",
        interface=Interface(commitments=["k-obs"]),
        provenance=Provenance(role="conjecturer"),
    )
    assert detection.evidence_lambda(harness) == 0.0


def test_evidence_lambda_one_when_covered_by_evidence(harness):
    harness.register_commitment(
        Commitment(id="k-obs", eval="predicate:True", observation_valued=True)
    )
    a = harness.create_artifact(
        "an empirical claim",
        interface=Interface(commitments=["k-obs"]),
        provenance=Provenance(role="conjecturer"),
    )
    scan_spawns(harness, Config())  # spawns research:k-obs:<aid>
    rid = f"research:k-obs:{a.id[:12]}"
    assert rid in harness.state.problems
    harness.create_artifact(  # accepted import evidence covering it
        "NOAA measurements 2026",
        provenance=Provenance(role="import"),
        problem_id=rid,
    )
    assert detection.evidence_lambda(harness) == 1.0


def test_grounding_brake_uses_evidence_lambda_only_when_opted_in(harness):
    harness.register_commitment(
        Commitment(id="k-obs", eval="predicate:True", observation_valued=True)
    )
    harness.create_artifact(
        "an ungrounded empirical claim",
        interface=Interface(commitments=["k-obs"]),
        provenance=Provenance(role="conjecturer"),
    )
    emb = HashingEmbedder()
    # Default: spec lambda (no rubric verdicts in window => 1.0) => no brake.
    off = Config(LAMBDA_FLOOR=0.3)
    assert detection.raw_flags(harness, emb, off)["grounding_decay"] is False
    # Opt-in: evidence_lambda = 0.0 (uncovered) < floor => brake fires.
    on = Config(LAMBDA_FLOOR=0.3, GROUNDING_USE_EVIDENCE_LAMBDA=True)
    assert detection.raw_flags(harness, emb, on)["grounding_decay"] is True


def test_grounding_brake_not_spurious_on_design_problem(harness):
    # Opt-in ON but no empirical claims => evidence_lambda None => fall back to
    # spec lambda => no spurious brake on a pure design problem.
    harness.create_artifact("pure design idea", provenance=Provenance(role="conjecturer"))
    on = Config(LAMBDA_FLOOR=0.3, GROUNDING_USE_EVIDENCE_LAMBDA=True)
    assert detection.raw_flags(harness, HashingEmbedder(), on)["grounding_decay"] is False


def test_eval_report_surfaces_uncovered_research(harness):
    from deepreason.report import eval_report

    harness.register_commitment(
        Commitment(id="k-obs", eval="predicate:True", observation_valued=True)
    )
    harness.create_artifact(
        "an empirical claim",
        interface=Interface(commitments=["k-obs"]),
        provenance=Provenance(role="conjecturer"),
    )
    scan_spawns(harness, Config())
    rep = eval_report(harness, Config())
    assert rep["research"]["problems"] >= 1
    assert rep["research"]["uncovered"] >= 1
    assert rep["research"]["note"]
    assert rep["capture"]["evidence_lambda"] == 0.0


# ---- Paper-cut: appellate_rule gives an ACTIONABLE error, not a bare KeyError

def test_registered_specs_enumerates_standards(harness):
    from deepreason.informal.standards import register_standard, registered_specs

    register_standard(harness, "std-b", rubric="r2")
    register_standard(harness, "std-a", rubric="r1")
    assert registered_specs(harness) == ["std-a", "std-b"]


def test_appellate_rule_unresolved_spec_is_actionable(harness):
    import pytest

    from deepreason.informal.appellate import rule
    from deepreason.informal.standards import register_standard

    register_standard(harness, "std-usability", rubric="r")
    with pytest.raises(ValueError) as exc:
        rule(harness, "c-1", "some holding", "std-explain")  # wrong/invented spec id
    msg = str(exc.value)
    assert "std-explain" in msg  # names what was wrong
    assert "std-usability" in msg  # lists what is valid
    assert "severity label" in msg  # the documented misuse hint


def test_appellate_rule_succeeds_with_registered_standard(harness):
    from deepreason.informal.appellate import rule
    from deepreason.informal.standards import register_standard

    register_standard(harness, "std-usability", rubric="r")
    precedent = rule(harness, "c-1", "naming a mechanism counts", "std-usability")
    assert precedent.provenance.role.value == "user"
    assert harness.state.status[precedent.id] == Status.ACCEPTED


def test_appellate_rule_actionable_through_mcp_surface(harness, monkeypatch):
    import pytest

    from deepreason.informal.standards import register_standard
    from deepreason.mcp_server import call_tool

    monkeypatch.setenv("DEEPREASON_ENABLE_LEGACY_MCP", "1")

    register_standard(harness, "std-usability", rubric="r")
    with pytest.raises(ValueError, match="std-usability"):
        call_tool(
            "appellate_rule",
            {"root": str(harness.root), "case_id": "c", "holding": "h", "standard": "nope"},
        )
