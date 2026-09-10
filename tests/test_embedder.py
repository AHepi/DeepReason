"""Embedder upgrade (llm/embedder.py) — the design adjudicated in
runs/embedder_design, with the corrections its criticism record extracted:
no cross-environment determinism claim (fingerprint + sentinel detect drift
instead), visible fallback when the optional backend is missing, and
threshold calibration against LABELED planted duplicates rather than a
blind distribution map. fastembed is a core dependency since the
2026-08-16 auto-install tranche; the neural tests skip only when its ONNX
weights cannot be fetched."""

import importlib.util
import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.embedder import (
    DEFAULT_NEURAL_MODEL,
    EmbedderUnavailable,
    HashingEmbedder,
    NeuralEmbedder,
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


def test_fastembed_is_a_core_dependency():
    """Regression (tranche 2026-08-16-change-embedder-auto-install):
    fastembed left the [embed] extra for the core dependency list, so a
    plain `pip install -e .` arms the neural default that
    config.EMBEDDER_MODEL has named all along. While it was optional, every
    container preflight produced a run that measured with hashing-128
    behind an `embedder-fallback` measure nobody read — grounded-extension
    run log.jsonl seq 2 (the fallback) and seq 8 (the hashing stamp).

    This test NEVER skips. A skip here would restore exactly the silence
    the tranche removed.
    """
    assert importlib.util.find_spec("fastembed") is not None, (
        "fastembed is not importable: either the core dependency was moved "
        "back into an extra, or this environment was not installed from "
        "pyproject.toml"
    )


def test_build_embedder_returns_neural_under_plain_install():
    """Regression (tranche 2026-08-16-change-embedder-auto-install): the
    configured neural model must actually BUILD, not merely be named.

    The weight fetch is the one half that a genuinely offline machine
    cannot perform, so it is the one half that may skip — and only after
    proving fastembed itself is present, which is the packaging claim.
    """
    try:
        engine = build_embedder(DEFAULT_NEURAL_MODEL)
    except EmbedderUnavailable as error:
        # Anchored to the module spec, not to the exception's wording: the
        # message is operator-facing prose and may be reworded, but "is
        # fastembed installed" is the actual question separating a
        # packaging regression from an offline machine.
        assert importlib.util.find_spec("fastembed") is not None, (
            "fastembed is missing, which is a packaging regression and "
            f"never a reason to skip: {error}"
        )
        pytest.skip(
            "2026-08-16-change-embedder-auto-install: fastembed is "
            "installed but its ONNX weights cannot be fetched in this "
            f"environment ({error}); genuinely offline CI only. The "
            "packaging half is asserted by "
            "test_fastembed_is_a_core_dependency, which never skips."
        )
    assert isinstance(engine, NeuralEmbedder)
    assert engine.model == DEFAULT_NEURAL_MODEL


def test_hashing_escape_survives_the_armed_neural_default():
    """Implements R3/R15 of tranche 2026-08-16-change-embedder-auto-install:
    arming the neural backend by install does not close the deliberate
    hashing road. EMBEDDER_MODEL=None stays the zero-dependency escape that
    controlled experiments and replay configurations depend on, and taking
    it is NOT a degradation — no `embedder-fallback` measure is recorded,
    because nothing failed.
    """
    engine = build_embedder(None)
    assert isinstance(engine, HashingEmbedder)
    assert engine.model == "hashing-128"
    assert engine.fingerprint()["model"] == "hashing-128"


def test_build_embedder_raises_unavailable_without_fastembed(monkeypatch):
    """The refusal is typed AND actionable. Since 2026-08-16 fastembed is a
    core dependency, so reaching this branch means the environment was not
    installed from pyproject.toml — the message must point at the install,
    not at the (now empty) [embed] extra."""
    import sys

    monkeypatch.setitem(sys.modules, "fastembed", None)  # forces ImportError
    with pytest.raises(EmbedderUnavailable, match="fastembed") as raised:
        build_embedder("BAAI/bge-small-en-v1.5")
    assert "pip install" in str(raised.value)
    assert "[embed]" not in str(raised.value)


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

    # Default config now names the neural model (E0.1), so a missing backend
    # degrades VISIBLY there too, citing the default model id.
    harness2 = Harness(tmp_path / "run2")
    assert make_embedder(harness2, Config()) is None
    falls2 = [e for e in harness2.log.read()
              if e.inputs and e.inputs[0] == "embedder-fallback"]
    assert len(falls2) == 1
    assert falls2[0].inputs[1] == "nomic-ai/nomic-embed-text-v1.5"

    # Explicit None: hashing is chosen deliberately — no fallback, no measure.
    harness3 = Harness(tmp_path / "run3")
    assert make_embedder(harness3, Config(EMBEDDER_MODEL=None)) is None
    assert not [e for e in harness3.log.read()
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


# ---- the setup-phase warm-up (tranche 2026-08-16-change-embedder-auto-install) ----


def _warmup(argv, monkeypatch=None):
    """Run `deepreason embedder-warmup ...` through the real parser."""
    from deepreason.cli.main import build_parser, main

    build_parser().parse_args(argv)  # the parser must admit the command
    return main(argv)


def test_embedder_warmup_reports_the_backend_a_run_will_use(tmp_path, capsys):
    """Implements R4 of tranche 2026-08-16-change-embedder-auto-install: the
    ~523 MB weight fetch happens in the setup phase behind a visible progress
    line, never silently inside cycle 1 of the first run to touch an
    embedder. The command's stdout is the typed fingerprint — the same
    identity the scheduler stamps on the log — so a ladder can record which
    geometry its runs are about to use before any of them start.
    """
    profile = tmp_path / "hashing.yaml"
    profile.write_text("EMBEDDER_MODEL: null\n")
    code = _warmup(["--config", str(profile), "embedder-warmup"])
    captured = capsys.readouterr()
    assert code == 0
    fingerprint = json.loads(captured.out)
    assert fingerprint["model"] == "hashing-128"
    # An unset model is a chosen configuration, not a failure: it reports
    # the hashing backend and succeeds (the all-configurations law).
    assert "hashing embedder" in captured.err


def test_embedder_warmup_surfaces_a_typed_failure_not_a_traceback(
    monkeypatch, capsys
):
    """An unbuildable backend is a runtime failure at the point of use — a
    named, non-zero exit an operator can read, never a stack trace and never
    a compile-time refusal of the configuration itself.
    """
    import sys as _sys

    monkeypatch.setitem(_sys.modules, "fastembed", None)  # forces ImportError
    code = _warmup(["embedder-warmup", "--model", "BAAI/bge-small-en-v1.5"])
    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == ""
    assert "EMBEDDER_WARMUP_UNAVAILABLE" in captured.err
    assert "Traceback" not in captured.err


def test_embedder_warmup_names_the_real_cache_directory(monkeypatch):
    """The printed disk location must be where fastembed will actually put
    the weights, so an operator budgeting disk is not planning against a
    plausible-looking guess. Derived exactly as fastembed derives it:
    FASTEMBED_CACHE_PATH, else `fastembed_cache` under the system temp dir.
    """
    import tempfile
    from pathlib import Path

    from deepreason.cli.main import embedder_cache_dir

    monkeypatch.delenv("FASTEMBED_CACHE_PATH", raising=False)
    assert embedder_cache_dir() == str(Path(tempfile.gettempdir()) / "fastembed_cache")
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", "/somewhere/else")
    assert embedder_cache_dir() == "/somewhere/else"


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


# ---- neural backend (core dependency since 2026-08-16; weights fetched) ----

# No module-level importorskip: a Skipped raised here would skip the WHOLE
# module, including test_fastembed_is_a_core_dependency, whose entire value
# is that it cannot skip. The `neural` fixture below already degrades to a
# skip for the only condition that legitimately warrants one — fastembed
# present but its weights unfetchable — since build_embedder raises
# EmbedderUnavailable in both cases.


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


def _measures(harness, signal):
    return [
        event
        for event in harness.log.read()
        if event.rule == Rule.MEASURE and event.inputs and event.inputs[0] == signal
    ]


def test_a_run_that_configured_no_embedder_says_so_on_its_own_log(tmp_path):
    """Regression (the five brief-variation arms,
    experiments/2026-09-04-experiment-brief-variation-step1/roots/
    {A0,A1,A1P,A2,A3}-run-fe00609058e10605590206d51ab2b7a0): each stamped
    ["embedder", "hashing-128", "1", "4226e035204776db"], carried zero
    `embedder-fallback` events and zero compile notices, and so could not say
    why it measured on the lexical scale after that session's own
    `deepreason embedder-warmup` had returned the neural fingerprint.

    "Nobody asked for the neural backend" is a legitimate answer and an
    inadmissible silence: a measurement scale that changes between runs with
    nothing in the record to attribute it to makes every distance reading in
    the corpus unattributable.
    """
    harness = Harness(tmp_path / "run")

    assert make_embedder(harness, Config(EMBEDDER_MODEL=None)) is None

    said = _measures(harness, "embedder-unconfigured")
    assert len(said) == 1, "the run must say WHY its geometry is hashing, once"
    assert said[0].inputs[1] == Config.model_fields["EMBEDDER_MODEL"].default, (
        "the record names the model the shipped default would have used, "
        "which is the fact an operator who warmed that model needs"
    )
    assert said[0].inputs[2], "a cause with no text is the silence again"
    assert "engine_config" in said[0].inputs[2], (
        "the cause must send a reader to the field that DECIDES the embedder. "
        "`scratch_policy.embedder_model` does not: two soak roots differing "
        "only in the engine config carried it as null while one measured "
        "neural and the other hashing "
        "(experiments/2026-09-09-neural-embedder-fallback/VERIFY.md)"
    )

    # R3/R15 of tranche 2026-08-16-change-embedder-auto-install: the deliberate
    # hashing escape is not a degradation. Saying why must not reclassify it.
    assert not _measures(harness, "embedder-fallback")


def test_the_two_hashing_causes_never_both_fire(monkeypatch, tmp_path):
    """A backend that was asked for and could not be built is a different fact
    from one nobody asked for, and a reader that saw both would not know which
    happened."""
    import sys

    monkeypatch.setitem(sys.modules, "fastembed", None)
    harness = Harness(tmp_path / "run")

    assert make_embedder(harness, Config(EMBEDDER_MODEL="BAAI/bge-small-en-v1.5")) is None

    assert len(_measures(harness, "embedder-fallback")) == 1
    assert not _measures(harness, "embedder-unconfigured")


def test_a_run_on_the_neural_backend_records_neither_cause(tmp_path):
    """The stamp alone is the answer when the run got what it asked for."""

    class Fixed:
        model = "fixture-neural"

        def embed(self, texts):
            return [[0.0, 1.0] for _ in texts]

        def fingerprint(self):
            return {"model": self.model, "version": "fixture", "sentinel": "0" * 16}

    from deepreason.llm import embedder as embedder_module

    harness = Harness(tmp_path / "run")
    built = Fixed()
    original = embedder_module.build_embedder
    embedder_module.build_embedder = lambda _model: built
    try:
        assert make_embedder(harness, Config(EMBEDDER_MODEL="fixture-neural")) is built
    finally:
        embedder_module.build_embedder = original

    assert not _measures(harness, "embedder-unconfigured")
    assert not _measures(harness, "embedder-fallback")


def test_the_managed_path_configuration_records_its_dropped_embedder(tmp_path):
    """Regression: a managed run whose configuration names no embedder model
    still records WHICH scale it measured on and why.

    Since 2026-09-10 an operator who STATES a model gets it — the managed path
    carries `EMBEDDER_MODEL` when `model_fields_set` says the operator asked
    (`tests/test_managed_path_host_owned_values.py`). This test now covers the
    condition that remains: an operator who states nothing keeps the host's
    hashing default, and the run must still say so rather than leaving a
    reader to infer the scale from a distance number.
    """
    from datetime import datetime, timezone

    from deepreason.preparation import build_preparation_manifest
    from deepreason.provider_profile import ProviderProfileV1
    from deepreason.run_manifest import config_from_run_manifest

    profile = ProviderProfileV1.create(
        provider="openai",
        endpoint="https://api.example.com/v1",
        model_id="model-a",
        model_revision="rev-a",
        family="family-a",
        context_window_tokens=262144,
        maximum_completion_tokens=4096,
        credential_env="DEEPREASON_TEST_KEY",
    )
    manifest = build_preparation_manifest(
        profile,
        question="Why is the sky blue?",
        compiled_at=datetime(2026, 7, 23, tzinfo=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        # States nothing about the embedder: `model_fields_set` is empty, so
        # the host default stands. A `Config(EMBEDDER_MODEL=...)` here would
        # now be CARRIED, which is a different test.
        config=Config.model_validate({}),
    )
    compiled = config_from_run_manifest(manifest)
    assert compiled.EMBEDDER_MODEL is None, (
        "fixture precondition: an unstated embedder keeps the host default"
    )

    harness = Harness(tmp_path / "run")
    assert make_embedder(harness, compiled) is None

    said = _measures(harness, "embedder-unconfigured")
    assert len(said) == 1
    assert said[0].inputs[1] == DEFAULT_NEURAL_MODEL


def test_results_says_why_a_run_measured_on_the_lexical_scale(tmp_path):
    """The half that reaches the operator. A typed record read by nobody is
    the 2026-08-16 trap's own lesson repeating: `deepreason results` is where
    an operator already looks, so the cause has to arrive there."""
    from deepreason.application.results import embedder_line, embedder_summary

    harness = Harness(tmp_path / "run")
    make_embedder(harness, Config(EMBEDDER_MODEL=None))
    harness.record_measure(inputs=["embedder", "hashing-128", "1", "0" * 16])

    summary = embedder_summary(harness)
    assert summary["backend"] == "hashing"
    assert summary["fallback"] is False, "nothing fell back; nothing was asked"
    assert summary["unconfigured"] is True
    assert summary["configured_model"] == DEFAULT_NEURAL_MODEL
    assert summary["fallback_reason"]

    line = embedder_line(summary)
    assert "hashing" in line
    assert summary["fallback_reason"] in line, (
        "the line must carry the recorded cause, not a fresh sentence that "
        "could drift from it"
    )
