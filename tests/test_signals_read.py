"""Part F (R15): a pure, read-only aggregation over already-existing,
already-live signals -- no new event/record type, no mid-run consumption
(Amendment 5's benching holds)."""

from deepreason.harness import Harness
from deepreason.ontology.event import LLMCall


def _fixture_root(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.record_measure(
        inputs=[
            "config-critique:config_mistuned",
            "recommendation:research_allowance_step_tighten",
            "cited:1,2",
        ]
    )
    harness.record_measure(
        inputs=[
            "v6-model-phase-deferred.v1",
            "hv-floor",
            "argumentative_critic",
            "target-ref",
            "obligation-ref",
            "budget-exhausted",
        ]
    )
    harness.record_measure(
        inputs=[
            "v6-model-phase-deferred.v1",
            "hv-floor",
            "argumentative_critic",
            "target-ref-2",
            "obligation-ref-2",
            "budget-exhausted",
        ]
    )
    harness.record_measure(
        inputs=[
            "v6-model-phase-deferred.v1",
            "rubric-trial",
            "judge",
            "target-ref-3",
            "obligation-ref-3",
            "budget-exhausted",
        ]
    )
    prompt_ref = harness.blobs.put(b"prompt")
    raw_ref = harness.blobs.put(b'{"ok":true}')
    call = LLMCall(
        role="conjecturer",
        model="gemma4:31b",
        endpoint="https://gemma.invalid/v1",
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        tokens=30,
        prompt_tokens=20,
        completion_tokens=10,
    )
    harness.record_llm_calls([call], "test-spend")
    return harness.root


def test_signal_snapshot_shape(tmp_path):
    from deepreason.signals_read import SignalSnapshotV1, read_signal_snapshot

    root = _fixture_root(tmp_path)
    snapshot = read_signal_snapshot(root)

    assert isinstance(snapshot, SignalSnapshotV1)

    assert snapshot.config_critique is not None
    assert snapshot.config_critique["signal"] == "config-critique:config_mistuned"

    assert snapshot.deferred_model_phase_counts == {"hv-floor": 2, "rubric-trial": 1}

    assert snapshot.token_spend["prompt_tokens"] == 20
    assert snapshot.token_spend["completion_tokens"] == 10
    assert snapshot.token_spend["total"] == 30
    assert snapshot.token_spend["calls"] == 1


def test_signal_snapshot_shape_with_no_signals_at_all(tmp_path):
    """No config critique, no deferrals, no LLM calls -- the empty case
    must not raise, and every field must have a legible empty value."""

    from deepreason.signals_read import read_signal_snapshot

    harness = Harness(tmp_path / "run")
    root = harness.root

    snapshot = read_signal_snapshot(root)

    assert snapshot.config_critique is None
    assert snapshot.deferred_model_phase_counts == {}
    assert snapshot.token_spend == {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total": 0,
        "calls": 0,
    }
