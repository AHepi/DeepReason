from deepreason.runtime.progress import ProgressSink
from deepreason.ui.status import read_run_status


def test_progress_is_monotonic_append_only_and_latest_is_atomic(tmp_path):
    sink = ProgressSink(tmp_path, run_id="r" * 64, workload="text")
    first = sink.emit(state="starting", phase="manifest", activity="bound")
    second = sink.emit(state="running", phase="conjecture", activity="start")
    assert (first.seq, second.seq) == (0, 1)
    assert [event.seq for event in sink.read_since(0)] == [1]
    assert '"seq":1' in (tmp_path / "run-status.json").read_text()


def test_unlimited_progress_is_indeterminate(tmp_path):
    sink = ProgressSink(tmp_path, run_id="r", workload="formal")
    event = sink.emit(
        state="running",
        phase="proof",
        activity="kernel check",
        token_spend=100,
        token_limit=None,
        determinate=False,
    )
    assert event.total_units is None and not event.determinate


def test_status_poll_tolerates_append_before_latest_snapshot_replace(tmp_path):
    sink = ProgressSink(tmp_path, run_id="r", workload="text")
    first = sink.emit(state="starting", phase="manifest", activity="bound")
    sink.emit(state="running", phase="reasoning", activity="cycle complete")
    # This is the only legitimate transient ordering: progress append first,
    # atomic latest-file replacement second.
    (tmp_path / "run-status.json").write_text(first.model_dump_json())
    status = read_run_status(tmp_path, since_seq=0)
    assert status["seq"] == 1
    assert [event["seq"] for event in status["events"]] == [1]
