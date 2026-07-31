"""A model-authored program may ask a bounded broker, and nothing more.

The brokered worker adds exactly one name to the program's namespace so a
simulation can measure a real model. These tests pin the two halves of that
claim: the added verb works, and the containment that makes running generated
code safe at all is untouched.

No network. The broker is stood up locally over its real Unix socket with a
stub responder, so the transport, the framing and every refusal path are
exercised for real while the gate stays offline.
"""

from __future__ import annotations

import json
import socket
import tempfile
import threading
from pathlib import Path

import pytest

from deepreason.verification.brokered import (
    BROKERED_WORKER_SHA256_V2,
    BROKERED_WORKER_SOURCE_V2,
)
from deepreason.verification.contained import (
    CONTAINED_WORKER_SHA256,
    CONTAINED_WORKER_SOURCE_V1,
)
from deepreason.verification.llm_broker import BrokerLimits, LLMBroker


def _worker_namespace():
    namespace: dict = {}
    exec(compile(BROKERED_WORKER_SOURCE_V2, "<brokered-worker>", "exec"), namespace)
    return namespace


class _StubBroker:
    """The real socket and framing, a canned reply instead of a provider."""

    def __init__(self, path: Path, reply):
        self.path, self.reply, self.seen = path, reply, []
        self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server.bind(str(path))
        self._server.listen(4)
        self._server.settimeout(0.5)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        while not self._stop.is_set():
            try:
                connection, _ = self._server.accept()
            except (TimeoutError, socket.timeout):
                continue
            except OSError:
                break
            with connection:
                raw = b""
                while not raw.endswith(b"\n"):
                    chunk = connection.recv(65536)
                    if not chunk:
                        break
                    raw += chunk
                if not raw.strip():
                    continue
                request = json.loads(raw)
                self.seen.append(request)
                payload = self.reply(request) if callable(self.reply) else self.reply
                connection.sendall(json.dumps(payload).encode() + b"\n")

    def close(self):
        self._stop.set()
        self._thread.join(timeout=5)
        self._server.close()


def test_the_brokered_worker_adds_one_verb_and_removes_no_containment():
    """The whole safety argument is that generated code cannot import, cannot
    open a file and cannot build a socket. Adding a way to reach a model must
    not become a way around any of that.
    """

    namespace = _worker_namespace()
    load = namespace["load_function"]

    # V1 must be untouched: it is the recorded runtime identity of every run
    # already in the record, and a brokered run is a DIFFERENT worker.
    assert BROKERED_WORKER_SHA256_V2 != CONTAINED_WORKER_SHA256
    assert "import socket" not in CONTAINED_WORKER_SOURCE_V1
    assert "import socket" in BROKERED_WORKER_SOURCE_V2

    refused = {
        "import": "def simulate(inputs, rng):\n    import socket\n    return {}\n",
        "from-import": "def simulate(inputs, rng):\n    from os import listdir\n    return {}\n",
        "private attribute": "def simulate(inputs, rng):\n    return {'v': llm.__globals__}\n",
    }
    for label, source in refused.items():
        function, error = load(source, "simulate", "simulation", {"llm": lambda **_: {}})
        assert function is None, f"{label} was not refused at parse"
        assert "may not" in error, (label, error)

    # These load but the names simply do not exist at runtime.
    for label, source, missing in (
        ("open", "def simulate(inputs, rng):\n    return {'v': open('/etc/passwd')}\n", "open"),
        ("__import__", "def simulate(inputs, rng):\n    return {'v': __import__('os')}\n", "__import__"),
        ("eval", "def simulate(inputs, rng):\n    return {'v': eval('1')}\n", "eval"),
    ):
        function, error = load(source, "simulate", "simulation", {"llm": lambda **_: {}})
        assert function is not None, (label, error)
        with pytest.raises(NameError, match=missing):
            function({}, None)


def test_a_program_can_ask_the_broker_and_is_bounded_by_it():
    """The verb works, and the budget is enforced on the worker side too, so a
    program that ignores a refusal and loops still cannot spend without bound.
    """

    namespace = _worker_namespace()
    load, make_llm = namespace["load_function"], namespace["make_llm"]

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "llm.sock"
        stub = _StubBroker(path, lambda request: {"ok": {"text": "Apple"}})
        try:
            program = (
                "def simulate(inputs, rng):\n"
                "    out = []\n"
                "    for i in range(5):\n"
                "        r = llm('Name a fruit.', temperature=1.0, seed=i)\n"
                "        out.append(r.get('text') or r.get('error'))\n"
                "    return {'answers': out}\n"
            )
            function, error = load(
                program, "simulate", "simulation",
                {"llm": make_llm(str(path), "glm-5.2", [3])},
            )
            assert error is None, error
            answers = function({}, None)["answers"]
        finally:
            stub.close()

    # Three calls served, then the worker-side budget refuses the rest without
    # ever reaching the broker.
    assert answers[:3] == ["Apple", "Apple", "Apple"], answers
    assert all("exhausted its authorized provider calls" in a for a in answers[3:]), answers
    assert len(stub.seen) == 3, stub.seen
    # The knobs the program chose are forwarded, not silently dropped.
    assert stub.seen[0]["temperature"] == 1.0
    assert stub.seen[0]["model"] == "glm-5.2"


def test_the_broker_pins_the_model_and_caps_the_calls():
    """The broker is the authority, not the program: the credential, the
    destination and the ceiling all live on this side of the socket.
    """

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "llm.sock"
        broker = LLMBroker(
            socket_path=path,
            endpoint="https://ollama.com/v1/chat/completions",
            api_key="never-used-in-this-test",
            limits=BrokerLimits(
                allowed_hosts=frozenset({"ollama.com"}),
                maximum_calls=2,
                allowed_models=frozenset({"glm-5.2"}),
            ),
        )
        broker.start()
        try:
            def ask(payload):
                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client.settimeout(30)
                client.connect(str(path))
                client.sendall(json.dumps(payload).encode() + b"\n")
                raw = b""
                while not raw.endswith(b"\n"):
                    chunk = client.recv(65536)
                    if not chunk:
                        break
                    raw += chunk
                client.close()
                return json.loads(raw)

            # Refused before any provider call, so no credential is spent.
            assert "outside the authorized set" in ask(
                {"prompt": "hi", "model": "gpt-oss:120b"}
            )["error"]
            assert "non-empty string" in ask({"prompt": "  ", "model": "glm-5.2"})["error"]
            assert broker.ledger.calls == 0, "a refused request must not count as a call"

            # The socket is owner-only: the one verb is not a public service.
            assert (path.stat().st_mode & 0o777) == 0o600
        finally:
            broker.stop()
        assert not path.exists(), "the broker must not leave its socket behind"

        ledger = broker.ledger.snapshot()
        assert ledger["schema"] == "llm-broker-ledger.v1"
        assert len(ledger["refusals"]) == 2
        # Prompts are recorded by digest, not text: the record should show what
        # was asked without copying the content of every call into it.
        assert all("prompt_sha256_prefix" in entry for entry in ledger["prompts"])
