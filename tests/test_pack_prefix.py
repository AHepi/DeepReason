"""Stable-prefix pack ordering (docs/TOKEN_ECONOMY.md angle 4): slow-changing
sections render before volatile ones so provider prefix caches bill the
repeated head at the cached rate. Ordering is presentation only — every
section still renders; nothing epistemic moves."""

from os.path import commonprefix

from deepreason.config import Config
from deepreason.llm.packs import render_conj_pack, render_crit_pack
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
)


def _problem(harness) -> Problem:
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_commitment(Commitment(id="k-long", eval="predicate:len(content) > 10"))
    problem = Problem(
        id="pi-tides",
        description="explain the tides",
        criteria=["k-moon", "k-long"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    )
    harness.register_problem(problem)
    return problem


def _sibling(harness, text: str, extra: str | None = None):
    commitments = ["k-moon", "k-long"] + ([extra] if extra else [])
    return harness.create_artifact(
        text,
        interface=Interface(commitments=commitments),
        provenance=Provenance(role="conjecturer"),
    )


def test_crit_pack_shares_prefix_across_sibling_targets(harness):
    _problem(harness)
    a = _sibling(harness, "the moon pulls the sea strongly")
    b = _sibling(harness, "moon resonance in enclosed basins")
    pack_a = render_crit_pack(a.id, harness.state, harness.commitments, harness.blobs, 2500)
    pack_b = render_crit_pack(b.id, harness.state, harness.commitments, harness.blobs, 2500)
    shared = commonprefix([pack_a, pack_b])
    # The shared criteria lines are inside the cacheable common prefix...
    assert "k-moon" in shared and "k-long" in shared
    # ...because commitments render before the (volatile) target section.
    assert pack_a.index("k-moon") < pack_a.index(f"TARGET {a.id}")


def test_crit_pack_prefix_diverges_only_at_per_target_extras(harness):
    _problem(harness)
    harness.register_commitment(Commitment(id="fc-x", eval="predicate:'x' in content"))
    harness.register_commitment(Commitment(id="fc-y", eval="predicate:'y' in content"))
    a = _sibling(harness, "the moon pulls the sea", extra="fc-x")
    b = _sibling(harness, "the moon pulls the sea twice", extra="fc-y")
    pack_a = render_crit_pack(a.id, harness.state, harness.commitments, harness.blobs, 2500)
    pack_b = render_crit_pack(b.id, harness.state, harness.commitments, harness.blobs, 2500)
    shared = commonprefix([pack_a, pack_b])
    assert "k-long" in shared            # shared criteria still in the prefix
    assert "fc-x" not in shared          # divergence starts at per-target extras
    assert "fc-x" in pack_a and "fc-y" in pack_b  # nothing dropped


def test_conj_pack_stance_precedes_neighbourhood(harness):
    problem = _problem(harness)
    school = {"id": "school-0", "stance_text": "prefer mechanisms", "weight": 0.8}
    config = Config(VS_K=2)

    def render() -> str:
        return render_conj_pack(
            problem, harness.state, harness.commitments, harness.blobs,
            vs_k=config.VS_K, token_budget=2500, school=school,
        )

    _sibling(harness, "the moon pulls the sea")
    before = render()
    _sibling(harness, "moon resonance in basins")  # neighbourhood grows
    after = render()
    assert before.index("SCHOOL STANCE") < before.index("NEIGHBOURHOOD")
    # Stance (stable) is inside the common prefix even as the neighbourhood churns.
    shared = commonprefix([before, after])
    assert "prefer mechanisms" in shared
    for section in ("CRITERIA", "SCHOOL STANCE", "NEIGHBOURHOOD", "DIRECTIVE"):
        assert section in before and section in after
