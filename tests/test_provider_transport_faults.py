"""Provider transport faults: visible, retried on a typed policy, survivable.

Regression (P-A1 run 4565139800f5ca02, P-S1 run 9e48a36b1dec91ee): ten of
glm-5.3's 25 calls returned zero tokens after ~1215 s each — four byte-identical
resends against a ~300 s zero-byte wall — and the resulting faults reached no
surface an operator or a monitor reads. P-S1 ran 15 of 24 cycles against a dead
provider with 54 typed transport failures named in none of its 13 summaries.

The wall stub below is the offline stand-in for that endpoint: it accepts the
connection, reads the whole request, waits, then closes having written no body.
urllib surfaces that as http.client.RemoteDisconnected, which is exactly the
diagnostic string all 39 P-A1 faults carry.
"""

import json
import socket
import threading
import time

import pytest

COMPLETION = {
    "choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 7, "completion_tokens": 3},
}


class WallServer:
    """Accept, read the request, wait ``wall_s``, close with no body written.

    ``bodies`` records the verbatim request body of every attempt, which is what
    makes "the retry is byte-identical" a measurement rather than a reading.
    ``serve_after`` lets a stub answer normally once the policy has changed the
    request, so a test can show the retry SUCCEEDING rather than merely differing.

    The wall is held with ``Event.wait`` and never ``time.sleep``: the retry
    backoff is patched out by monkeypatching ``time.sleep`` on the module
    object, which is the same object this thread would call.
    """

    def __init__(self, wall_s=0.3, serve_after=None, sse_body=None):
        self.wall_s = wall_s
        self.serve_after = serve_after
        self.sse_body = sse_body
        self.bodies: list[bytes] = []
        self._stop = threading.Event()
        self._socket = socket.socket()
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen(8)
        self.port = self._socket.getsockname()[1]
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                connection, _ = self._socket.accept()
            except OSError:
                return
            threading.Thread(
                target=self._handle, args=(connection,), daemon=True
            ).start()

    def _handle(self, connection) -> None:
        try:
            buffered = b""
            while b"\r\n\r\n" not in buffered:
                chunk = connection.recv(65536)
                if not chunk:
                    return
                buffered += chunk
            head, _, rest = buffered.partition(b"\r\n\r\n")
            length = 0
            for line in head.split(b"\r\n"):
                if line.lower().startswith(b"content-length:"):
                    length = int(line.split(b":")[1])
            while len(rest) < length:
                chunk = connection.recv(65536)
                if not chunk:
                    break
                rest += chunk
            self.bodies.append(rest)
            asked = json.loads(rest or b"{}")
            if self.serve_after is not None and self.serve_after(
                len(self.bodies), asked
            ):
                connection.sendall(
                    _sse_response(self.sse_body)
                    if asked.get("stream")
                    else _json_response()
                )
                return
            self._stop.wait(self.wall_s)
        finally:
            try:
                connection.close()
            except OSError:
                pass

    def close(self) -> None:
        self._stop.set()
        try:
            self._socket.close()
        except OSError:
            pass


def _json_response() -> bytes:
    payload = json.dumps(COMPLETION).encode()
    return (
        b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
        + str(len(payload)).encode()
        + b"\r\nConnection: close\r\n\r\n"
        + payload
    )


def _sse_response(body: bytes | None) -> bytes:
    """The framing measured off ollama.com (probe/raw/H1.sse): content deltas,
    `finish_reason` alone on a chunk with an empty delta, `usage` on a chunk
    with no choices, terminated by `data: [DONE]`."""

    if body is None:
        body = (
            b'data: {"choices":[{"delta":{"role":"assistant"}}]}\n\n'
            b'data: {"choices":[{"delta":{"content":"h"}}]}\n\n'
            b'data: {"choices":[{"delta":{"content":"i"}}]}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b'data: {"choices":[],"usage":{"prompt_tokens":7,'
            b'"completion_tokens":3}}\n\n'
            b"data: [DONE]\n\n"
        )
    return (
        b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nContent-Length: "
        + str(len(body)).encode()
        + b"\r\nConnection: close\r\n\r\n"
        + body
    )


@pytest.fixture
def no_backoff_sleep(monkeypatch):
    """The 2/4/8 s ladder is pinned by its own constant test; sleeping it here
    would buy nothing but 14 s per case."""
    from deepreason.llm import endpoints

    monkeypatch.setattr(endpoints.time, "sleep", lambda seconds: None)


def test_the_backoff_ladder_is_still_the_one_the_record_was_written_under():
    """The arithmetic in DIAGNOSIS.md E1 subtracts exactly 2+4+8 s from each
    fault's `ms` before dividing by four; if the ladder moves, that derivation
    stops reproducing and the recorded ~300.3 s wall stops being re-derivable."""
    from deepreason.llm import endpoints

    assert endpoints._BACKOFFS == (2, 4, 8)


def test_a_zero_byte_wall_is_not_answered_with_an_identical_resend(
    no_backoff_sleep,
):
    """P-A1's ten dead calls each sent the SAME bytes four times into the same
    wall. A wall is not a transient fault: whatever the policy does — shrink the
    cap, stand the leg down — the second attempt must differ from the first."""
    from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint

    server = WallServer()
    try:
        endpoint = OpenAICompatEndpoint(
            server.base_url, "m", timeout_s=30, max_tokens=49152
        )
        with pytest.raises(EndpointError):
            endpoint.complete("PACK")
    finally:
        server.close()

    assert len(server.bodies) >= 2, "expected at least one retry"
    assert server.bodies[1] != server.bodies[0], (
        "the retry resent byte-identical bytes into the same wall: "
        f"{len(server.bodies)} attempts, "
        f"{len(set(server.bodies))} distinct request bodies"
    )


def test_a_streamed_retry_succeeds_where_the_first_attempt_died(no_backoff_sleep):
    """The retry that gets through is the SAME request on a framing that
    survives — measured 2026-09-03: cap 32768 non-streaming died at 300.51 s,
    the same cap streamed finished at 369.64 s.

    Not a smaller request. `invariants.py` requires every recorded
    attempt.max_tokens to be the route's or one a PRIOR logged controller policy
    authorized, and llm/ may not write to the log, so a cap this layer chose
    could never be authorized and the run would fail replay validation.
    """
    from deepreason.llm.endpoints import OpenAICompatEndpoint

    server = WallServer(serve_after=lambda attempt, body: bool(body.get("stream")))
    try:
        endpoint = OpenAICompatEndpoint(
            server.base_url, "m", timeout_s=30, max_tokens=49152
        )
        assert endpoint.complete("PACK") == "hi"
    finally:
        server.close()

    first, last = json.loads(server.bodies[0]), json.loads(server.bodies[-1])
    assert "stream" not in first, "the FIRST attempt must send today's bytes"
    assert last["stream"] is True
    assert last["stream_options"] == {"include_usage": True}, (
        "a streamed call that does not ask for usage reports none, and an "
        "unreported spend defeats the hard token ceiling"
    )
    assert last["max_tokens"] == first["max_tokens"] == 49152
    assert endpoint.last_streamed_attempts == 1


def test_a_streamed_retry_records_what_a_plain_success_would_have_recorded(
    no_backoff_sleep,
):
    """Transport, never presentation: the same model output must produce the
    same record, or a fix for the wall becomes a change to the evidence."""
    from deepreason.llm.endpoints import OpenAICompatEndpoint

    plain = WallServer(serve_after=lambda attempt, body: True)
    walled = WallServer(serve_after=lambda attempt, body: bool(body.get("stream")))
    try:
        direct = OpenAICompatEndpoint(plain.base_url, "m", timeout_s=30)
        content = direct.complete("PACK")
        streamed = OpenAICompatEndpoint(walled.base_url, "m", timeout_s=30)
        assert streamed.complete("PACK") == content
    finally:
        plain.close()
        walled.close()

    assert streamed.last_usage == direct.last_usage
    assert streamed.last_finish_reason == direct.last_finish_reason
    assert streamed.last_reasoning_trace == direct.last_reasoning_trace


def test_a_stream_that_stops_early_is_a_failure_not_a_short_answer(
    no_backoff_sleep,
):
    """A stream can return 200, emit tokens, then die (the provider documents
    it). Reading that as a completion is a silent data-quality failure."""
    from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint

    truncated = b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n'
    server = WallServer(
        serve_after=lambda attempt, body: bool(body.get("stream")),
        sse_body=truncated,
    )
    try:
        endpoint = OpenAICompatEndpoint(server.base_url, "m", timeout_s=30)
        with pytest.raises(EndpointError):
            endpoint.complete("PACK")
    finally:
        server.close()


def test_an_error_object_mid_stream_is_a_failure(no_backoff_sleep):
    from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint

    poisoned = (
        b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n'
        b'data: {"error":{"message":"upstream died"}}\n\n'
        b"data: [DONE]\n\n"
    )
    server = WallServer(
        serve_after=lambda attempt, body: bool(body.get("stream")),
        sse_body=poisoned,
    )
    try:
        endpoint = OpenAICompatEndpoint(server.base_url, "m", timeout_s=30)
        with pytest.raises(EndpointError):
            endpoint.complete("PACK")
    finally:
        server.close()


def test_a_call_that_asked_for_logprobs_is_never_streamed(no_backoff_sleep):
    """No chunk of a streamed response carries logprobs — measured against a
    real SSE body, not assumed — so such a call must stay non-streaming even
    though that means standing down at the wall."""
    from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint

    server = WallServer(serve_after=lambda attempt, body: bool(body.get("stream")))
    try:
        endpoint = OpenAICompatEndpoint(
            server.base_url, "m", timeout_s=30, request_logprobs=True
        )
        with pytest.raises(EndpointError, match="no body"):
            endpoint.complete("PACK")
    finally:
        server.close()

    assert endpoint.last_streamed_attempts == 0
    assert all("stream" not in json.loads(b) for b in server.bodies)


def test_an_unknown_policy_id_falls_back_and_discloses_rather_than_refusing():
    """All configurations are allowed (operator law, 2026-08-12): a policy
    selector meets an unknown id with the shipped default and a disclosure."""
    from deepreason.llm.transport_policy import DEFAULT_POLICY_ID, resolve

    _, used, fell_back_from = resolve("no-such-policy")
    assert used == DEFAULT_POLICY_ID
    assert fell_back_from == "no-such-policy"
    assert resolve(DEFAULT_POLICY_ID)[2] is None


def test_the_two_real_diagnostic_strings_classify_as_different_kinds():
    """P-A1's hang-up costs 300 s an attempt; P-S1's refusal costs
    milliseconds. Retrying them the same way is what made one of them
    expensive."""
    from deepreason.llm.transport_policy import classify

    assert classify(
        "RemoteDisconnected:Remote end closed connection without response"
    ) == "zero_byte_close"
    assert classify(
        "URLError:<urlopen error [Errno 111] Connection refused>"
    ) == "connect_failure"


def test_the_total_wall_time_of_a_dead_seat_is_bounded(no_backoff_sleep):
    """Four unbounded attempts made one call cost 1215 s of a 4.94 h run. The
    policy must bound what a single dead call can spend, in attempts AND in
    wall time, the way TIMEOUT_FACTORS already bounds the read-timeout branch
    at 3x (SUB-llm Traps, "Retrying an identical wait ... fails identically")."""
    from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint

    wall_s = 0.3
    server = WallServer(wall_s=wall_s)
    try:
        endpoint = OpenAICompatEndpoint(
            server.base_url, "m", timeout_s=30, max_tokens=49152
        )
        started = time.monotonic()
        with pytest.raises(EndpointError):
            endpoint.complete("PACK")
        elapsed = time.monotonic() - started
    finally:
        server.close()

    assert len(server.bodies) <= 3, (
        f"a zero-byte wall got {len(server.bodies)} identical attempts; "
        "the read-timeout branch already stops at 2"
    )
    assert elapsed < 3 * wall_s, (
        f"spent {elapsed:.2f}s against a {wall_s}s wall "
        f"({elapsed / wall_s:.1f}x); the read-timeout branch bounds its own "
        "total at 3x by construction"
    )


def test_the_endpoint_reports_zero_byte_faults_separately_from_other_faults(
    no_backoff_sleep,
):
    """`transport_diagnostics` records the string; nothing records the SHAPE.
    A zero-byte close, a mid-body drop and an HTTP 500 are three different
    conditions and the surfacing layer needs to tell them apart per seat."""
    from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint

    server = WallServer()
    try:
        endpoint = OpenAICompatEndpoint(server.base_url, "m", timeout_s=30)
        with pytest.raises(EndpointError):
            endpoint.complete("PACK")
    finally:
        server.close()

    assert endpoint.last_zero_byte_returns >= 1
    assert endpoint.last_fault_kind == "zero_byte_close"


# --- the two surfaces an operator and a monitor actually read -------------- #
#
# The record kept the receipts the whole time: P-S1's REPLAY_VALIDATION.json
# even carries `provider_transport_attempts: 442` against `attempts: 280`.
# Nothing names that number and nothing prints it, so 54 typed failures reached
# 0 of 13 summary documents and P-A1's purpose-built monitor raised 0 alerts on
# 40 faults. Publishing the fault where a monitor already looks is the fix.


def test_a_progress_row_carries_per_seat_provider_health():
    """A watcher tails progress.jsonl. P-A1's and P-S1's rows carry one key set
    of 24 and not one of them matches transport|provider|health|fault, so the
    outage was structurally unwatchable."""
    from deepreason.runtime.progress import ProgressEvent

    assert "provider_health" in ProgressEvent.model_fields


def test_a_progress_row_that_measured_nothing_says_so_rather_than_claiming_zero():
    """`a default is not an absence` (SUB-application Traps, the token_spend
    incident: 20 of 59 roots carry a false zero because a skipped keyword
    asserted a spend of nought). A row emitted where no seat health was
    computed must be absent, not an empty health map."""
    from deepreason.runtime.progress import ProgressEvent

    field = ProgressEvent.model_fields["provider_health"]
    assert field.default is None, (
        "provider_health must default to a typed absence (None), not to a "
        f"legal value ({field.default!r}) that reads as 'all seats healthy'"
    )


def test_a_progress_row_that_did_measure_names_the_seat_and_its_faults():
    """Per seat: attempts, faults, zero-byte returns, last fault kind."""
    from deepreason.runtime.progress import ProgressEvent

    event = ProgressEvent(
        seq=0,
        run_id="r",
        state="running",
        workload="text",
        phase="convergence",
        activity="cycle evaluated",
        provider_health={
            "conjecturer#1": {
                "attempts": 17,
                "faults": 6,
                "zero_byte_returns": 6,
                "last_fault_kind": "zero_byte_close",
            }
        },
    )
    row = json.loads(event.model_dump_json())
    assert row["provider_health"]["conjecturer#1"]["faults"] == 6
    assert row["provider_health"]["conjecturer#1"]["last_fault_kind"] == (
        "zero_byte_close"
    )


def test_results_reports_provider_health_and_types_its_absence():
    """`deepreason results` is the ONE retrieval surface (SUB-application).
    A fact it does not carry is one nobody will find by grepping the root."""
    from deepreason.application.results import ABSENCE_REASONS, results_summary

    assert any("PROVIDER" in reason for reason in ABSENCE_REASONS), (
        "no absence code can say 'this root recorded no provider attempts'"
    )
    summary = results_summary(_a_root_without_provider_attempts())
    assert "provider_health" in summary
    assert summary["provider_health"].get("absent") is True


def test_results_renders_a_provider_health_heading():
    from deepreason.application.results import render_results, results_summary

    rendered = render_results(results_summary(_a_root_without_provider_attempts()))
    # Whole line, not substring: `"## Provider health" in rendered` also passes
    # for "## Provider healthXX", which a mutation run proved.
    assert "## Provider health" in rendered.splitlines()


def _a_root_without_provider_attempts():
    """Smallest committed root: enough to prove the key is present and typed
    absent, without inventing a fixture the live shape would not match."""
    import subprocess
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    listed = subprocess.run(
        ["git", "ls-files", "experiments"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    roots = sorted(
        {repo / Path(entry).parent for entry in listed if entry.endswith("/log.jsonl")},
        key=lambda root: (root / "log.jsonl").stat().st_size,
    )
    if not roots:
        pytest.skip("no committed run root")
    return roots[0]


def test_the_derivation_counts_a_real_committed_fault_rather_than_reporting_healthy():
    """The derivation is the whole surfacing obligation, so it is pinned
    against COMMITTED evidence rather than a fixture.

    Selected by property, not by path: the one committed root whose
    `workflow-provider-attempt-v1` objects contain a `transport_failure` (the
    census at `docs/map/INV-frozen-surfaces.md` counts exactly one). A rename
    that retires a root must not fail this test; a derivation that stops
    counting faults must.
    """
    from deepreason.harness import Harness
    from deepreason.runtime.provider_health import seat_health

    root = _a_root_with_a_recorded_transport_failure()
    health = seat_health(Harness(root, read_only=True))
    faulted = {
        instance: row for instance, row in health.items() if row["faults"]
    }
    assert faulted, f"no seat in {root.name} reports the fault its record carries"
    row = next(iter(faulted.values()))
    assert row["zero_byte_returns"] >= 1
    assert row["last_fault_kind"] == "zero_byte_close"
    assert row["attempts"] > row["calls"], (
        "a retried call must cost more transport attempts than calls, which is "
        "the number P-S1's REPLAY_VALIDATION.json carried unnamed (442 vs 280)"
    )
    assert row["fault_ms"] > 0


def _a_root_with_a_recorded_transport_failure():
    import subprocess
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    listed = subprocess.run(
        ["git", "ls-files", "experiments"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    for entry in listed:
        if "workflow-provider-attempt-v1" not in entry or not entry.endswith(".json"):
            continue
        if "transport_failure" not in (repo / entry).read_text():
            continue
        root = repo / Path(entry).parents[2]
        if (root / "log.jsonl").exists():
            return root
    pytest.skip("no committed root records a transport_failure")


def test_a_dead_seat_streak_emits_a_typed_notice_once_and_does_not_stop_the_run(
    tmp_path,
):
    """GOAL clause 6: N consecutive zero-byte attempts on one seat must
    disclose. Disclose, never die — the run is not stopped and no seat is stood
    down (operator disposition 2026-09-03, road A; standing a seat down is
    PARKED.md P1).

    Driven over a COPY of a committed root, never the root itself: a committed
    root is evidence, and a writable open would repair — that is, destroy — it.
    """
    import shutil

    from deepreason.config import Config
    from deepreason.harness import Harness
    from deepreason.scheduler.scheduler import Scheduler
    from deepreason.signals import DEAD_SEAT_STREAK_SIGNAL

    source = _a_root_with_a_recorded_transport_failure()
    root = tmp_path / "copy"
    shutil.copytree(source, root)

    config = Config()
    config.TRANSPORT_POLICY.dead_seat_streak = 1

    class _Bound:
        # The two methods under test, over a harness and a config and nothing
        # else — constructing a whole Scheduler would test the constructor.
        _provider_health = Scheduler._provider_health
        _measure_recorded = Scheduler._measure_recorded

    bound = _Bound()
    bound.harness = Harness(root)
    bound.config = config

    def emitted():
        return [
            [str(v) for v in (event.inputs or ())]
            for event in bound.harness.log.read()
            if (event.inputs or ()) and str(event.inputs[0]) == DEAD_SEAT_STREAK_SIGNAL
        ]

    assert emitted() == []
    health = bound._provider_health()
    assert health, "the copied root records provider attempts"
    notices = emitted()
    assert len(notices) == 1, notices
    assert notices[0][3] == "zero_byte_close"

    # Idempotent BY SEARCHING THE RECORD, so a resumed run neither re-discloses
    # nor falls silent.
    bound._provider_health()
    assert emitted() == notices


def test_a_healthy_run_emits_no_dead_seat_notice(tmp_path):
    import shutil

    from deepreason.config import Config
    from deepreason.harness import Harness
    from deepreason.scheduler.scheduler import Scheduler
    from deepreason.signals import DEAD_SEAT_STREAK_SIGNAL

    source = _a_root_with_a_recorded_transport_failure()
    root = tmp_path / "copy"
    shutil.copytree(source, root)

    config = Config()
    config.TRANSPORT_POLICY.dead_seat_streak = 99

    class _Bound:
        _provider_health = Scheduler._provider_health
        _measure_recorded = Scheduler._measure_recorded

    bound = _Bound()
    bound.harness = Harness(root)
    bound.config = config
    bound._provider_health()
    assert not [
        event
        for event in bound.harness.log.read()
        if (event.inputs or ()) and str(event.inputs[0]) == DEAD_SEAT_STREAK_SIGNAL
    ]
