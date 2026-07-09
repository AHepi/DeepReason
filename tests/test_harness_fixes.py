"""Regression tests for three evidence-backed fixes (from live 200k runs):

1. remove-arbitrariness spawns carry the ROOT problem's description + criteria,
   so the ra-loop stays anchored instead of drifting off-problem.
2. generator_metrics exposes an embedder-agnostic school-separation ratio, so
   a RESEED_DIST_MIN that is below the embedder's distance scale is visible.
3. why() on a refuted status surfaces the sanctioned reinstatement move
   (criticize the critic), the load-bearing operator mechanic that was unwritten.
"""

from deepreason.capture import detection
from deepreason.config import Config
from deepreason.llm.embedder import HashingEmbedder
from deepreason.llm.packs import render_conj_pack
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
)
from deepreason.rules.spawn import scan_spawns
from deepreason.views.why import why
from tests.conftest import art, attack


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
