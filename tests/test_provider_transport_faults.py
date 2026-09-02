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

    def __init__(self, wall_s=0.3, serve_after=None):
        self.wall_s = wall_s
        self.serve_after = serve_after
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
            if self.serve_after is not None and self.serve_after(
                len(self.bodies), json.loads(rest or b"{}")
            ):
                payload = json.dumps(COMPLETION).encode()
                connection.sendall(
                    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                    b"Content-Length: " + str(len(payload)).encode()
                    + b"\r\nConnection: close\r\n\r\n" + payload
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


def test_a_shrinking_policy_lets_the_retry_succeed_where_the_first_attempt_died(
    no_backoff_sleep,
):
    """The point of not resending identically: a smaller request can get under
    a wall the first one could not. Stub answers only a request whose cap has
    come down."""
    from deepreason.llm.endpoints import OpenAICompatEndpoint

    server = WallServer(
        serve_after=lambda attempt, body: body.get("max_tokens", 0) < 49152
    )
    try:
        endpoint = OpenAICompatEndpoint(
            server.base_url, "m", timeout_s=30, max_tokens=49152
        )
        assert endpoint.complete("PACK") == "hi"
    finally:
        server.close()

    assert [json.loads(b)["max_tokens"] for b in server.bodies][0] == 49152
    assert json.loads(server.bodies[-1])["max_tokens"] < 49152


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
    assert "## Provider health" in rendered


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
