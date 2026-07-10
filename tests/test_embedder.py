"""Embedder upgrade (llm/embedder.py) — the design adjudicated in
runs/embedder_design, with the corrections its criticism record extracted:
no cross-environment determinism claim (fingerprint + sentinel detect drift
instead), visible fallback when the optional backend is missing, and
threshold calibration against LABELED planted duplicates rather than a
blind distribution map. Neural tests skip when fastembed is absent."""

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.embedder import (
    EmbedderUnavailable,
    HashingEmbedder,
    build_embedder,
    distance,
)
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Provenance, Rule
from deepreason.ops import make_embedder
from deepreason.views.basin import DEFAULT_PLANTED, threshold_calibration


def test_hashing_fingerprint_is_stable_and_complete():
    a, b = HashingEmbedder(), HashingEmbedder()
    fa, fb = a.fingerprint(), b.fingerprint()
    assert fa == fb  # pure function of content: identical across instances
    assert fa["model"] == "hashing-128"
    assert set(fa) == {"model", "version", "sentinel"}
    assert len(fa["sentinel"]) == 16


def test_build_embedder_default_is_hashing():
    assert isinstance(build_embedder(None), HashingEmbedder)
    assert isinstance(build_embedder(""), HashingEmbedder)


def test_build_embedder_raises_unavailable_without_fastembed(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "fastembed", None)  # forces ImportError
    with pytest.raises(EmbedderUnavailable, match="deepreason\\[embed\\]"):
        build_embedder("BAAI/bge-small-en-v1.5")


def test_make_embedder_fallback_lands_on_the_log(monkeypatch, tmp_path):
    """A configured-but-missing backend degrades to hashing VISIBLY: the
    run's geometry is worse and the post-hoc reader must be able to see
    why — never a silent swap (the adjudicated correction to 'refuse to
    start vs silent stub' contradictions in the refuted rivals)."""
    import sys

    monkeypatch.setitem(sys.modules, "fastembed", None)
    harness = Harness(tmp_path / "run")
    embedder = make_embedder(harness, Config(EMBEDDER_MODEL="BAAI/bge-small-en-v1.5"))
    assert embedder is None  # scheduler falls back to its hashing default
    falls = [e for e in harness.log.read()
             if e.rule == Rule.MEASURE and e.inputs
             and e.inputs[0] == "embedder-fallback"]
    assert len(falls) == 1
    assert falls[0].inputs[1] == "BAAI/bge-small-en-v1.5"
    assert "fastembed" in falls[0].inputs[2]

    # Unset knob: no fallback, no measure — hashing is the intended default.
    harness2 = Harness(tmp_path / "run2")
    assert make_embedder(harness2, Config()) is None
    assert not [e for e in harness2.log.read()
                if e.inputs and e.inputs[0] == "embedder-fallback"]


def test_embed_cache_is_keyed_by_model(tmp_path):
    """Two embedders with distinct model ids must not share cache entries
    (pre-fix the key was the CLASS name, which would alias two
    NeuralEmbedders loading different models)."""

    class Fixed:
        def __init__(self, model, value):
            self.model = model
            self._value = value

        def embed(self, text):
            return [self._value, 0.0]

    harness = Harness(tmp_path / "run")
    art = harness.create_artifact("some content", provenance=Provenance(role="seed"))
    v1 = harness.embed_artifact(Fixed("model-a", 1.0), art.id)
    v2 = harness.embed_artifact(Fixed("model-b", 2.0), art.id)
    assert v1 == [1.0, 0.0] and v2 == [2.0, 0.0]


def _seeded_harness(tmp_path) -> Harness:
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-any", eval="predicate:len(content) > 0"))
    for pid, texts in {
        # Siblings are RELATED but substantively distinct claims — the
        # population a run actually produces (rival algorithms, rival
        # mechanisms), not rewordings of one stem.
        "pi-sort": [
            "Use quicksort: pick a pivot, partition the items around it, and "
            "recurse into both halves until single elements remain.",
            "Merge sort divides the sequence in two, sorts each half "
            "recursively, then interleaves the results in order.",
            "Build a max-heap over the array, then repeatedly extract the "
            "root and shrink the heap to produce a sorted suffix.",
        ],
        "pi-tides": [
            "The moon's gravity pulls hardest on the near-side ocean, so "
            "water bulges toward it while inertia raises a second bulge on "
            "the far side.",
            "Tidal friction transfers angular momentum from earth's spin to "
            "the moon's orbit, lengthening the day and pushing the moon "
            "slowly outward.",
            "Spring tides happen when sun and moon align at new or full "
            "moon and their tidal forces add; at quadrature they partially "
            "cancel into neap tides.",
        ],
    }.items():
        harness.register_problem(Problem(
            id=pid, description=pid, criteria=["k-any"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        ))
        for text in texts:
            harness.create_artifact(
                text, provenance=Provenance(role="conjecturer"), problem_id=pid)
    return harness


def test_threshold_calibration_structure_and_determinism(tmp_path):
    harness = _seeded_harness(tmp_path)
    embedder = HashingEmbedder()
    one = threshold_calibration(harness, embedder)
    two = threshold_calibration(harness, embedder)
    assert one == two  # deterministic function of (log, embedder)
    assert one["embedder"]["model"] == "hashing-128"
    for key in ("planted_duplicate", "within_problem", "cross_problem",
                "separable", "recommended", "note"):
        assert key in one
    assert one["planted_duplicate"]["n"] == len(DEFAULT_PLANTED)
    assert json.dumps(one)  # JSON-serializable for the CLI
    # The documented finding this whole upgrade exists to fix: hashing cannot
    # separate planted duplicates from genuine siblings.
    assert one["separable"]["near_dup_gate"] is False


def test_scheduler_accepts_custom_embedder_and_stamps_it(tmp_path):
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.scheduler.scheduler import Scheduler

    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-x", eval="predicate:'x' in content"))
    harness.register_problem(Problem(
        id="pi-x", description="x", criteria=["k-x"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    conj = json.dumps({"candidates": [{"content": "x idea", "typicality": 0.9}]})
    adapter = LLMAdapter({"conjecturer": MockEndpoint([conj])}, harness.blobs)

    class Duck:
        model = "duck-7"
        version = "v7"

        def embed(self, text):
            return [1.0, 0.0]

    Scheduler(harness, adapter, Config(VS_K=1, N_SCHOOLS=0, FUZZ_N=0),
              embedder=Duck()).step()
    stamp = next(e for e in harness.log.read()
                 if e.rule == Rule.MEASURE and e.inputs and e.inputs[0] == "embedder")
    # Duck-typed embedders without fingerprint() still stamp their identity.
    assert list(stamp.inputs[1:]) == ["duck-7", "v7", "-"]


# ---- neural backend (optional dependency; guarded like the browser oracle) ----

fastembed = pytest.importorskip("fastembed")


@pytest.fixture(scope="module")
def neural():
    try:
        return build_embedder("BAAI/bge-small-en-v1.5")
    except EmbedderUnavailable as e:  # installed but model not fetchable here
        pytest.skip(str(e))


def test_neural_embed_normalized_and_deterministic_in_process(neural):
    a = neural.embed("the moon causes the tides")
    b = neural.embed("the moon causes the tides")
    assert a == b  # within one process: same text, same vector
    assert abs(sum(x * x for x in a) - 1.0) < 1e-6


def test_neural_fingerprint_names_the_environment(neural):
    fp = neural.fingerprint()
    assert fp["model"] == "BAAI/bge-small-en-v1.5"
    assert "fastembed-" in fp["version"] and "onnxruntime-" in fp["version"]
    assert len(fp["sentinel"]) == 16
    assert fp == neural.fingerprint()  # stable within the environment


def test_neural_orders_the_fine_distinctions(neural):
    """The acceptance criterion from the adjudicated record: every planted
    duplicate (same content, reworded/renamed) must read CLOSER than a
    genuinely-different pair — the ordering hashing measurably inverts."""
    different = distance(
        neural.embed(DEFAULT_PLANTED[1][0]),  # lex-min toposort
        neural.embed("def solve(a, b):\n    return sorted(a, reverse=True)\n"),
    )
    for left, right in DEFAULT_PLANTED:
        assert distance(neural.embed(left), neural.embed(right)) < different


def test_neural_calibration_separates_the_gate(neural, tmp_path):
    result = threshold_calibration(_seeded_harness(tmp_path), neural)
    assert result["separable"]["near_dup_gate"] is True
    eps = result["recommended"]["NEAR_DUP_EPS"]
    assert eps is not None
    # The recommended gate catches every planted duplicate...
    for left, right in DEFAULT_PLANTED:
        assert distance(neural.embed(left), neural.embed(right)) < eps
    # ...and admits typical same-problem siblings.
    assert result["within_problem"]["median"] > eps
