"""A bounded LLM call broker for model-authored simulations.

Model-authored Python inside the contained worker cannot import, cannot open a
file, and cannot construct a socket: the worker's AST guard rejects imports and
private-attribute traversal, and its builtins allowlist omits ``open``,
``__import__``, ``eval`` and ``exec``. That is the load-bearing containment;
the unshared network namespace is defence in depth behind it.

So a program that needs to measure a real model cannot reach one on its own,
and should not be given the means to. Instead the worker injects ONE callable,
and this broker is what stands behind it:

* the credential never enters the sandbox — it lives only here;
* the destination is pinned, so the one verb cannot become a general socket;
* calls are capped, so a loop in generated code cannot bill the operator
  without bound;
* every call is logged, so the record shows exactly what the program asked.

The transport is a Unix domain socket. That is deliberate: a Unix socket is a
filesystem object, not a network one, so it crosses an unshared NETWORK
namespace untouched and the worker keeps ``--net`` with no exception carved
into it.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_MAX_FRAME_BYTES = 1 * 1024 * 1024
_READ_TIMEOUT_SECONDS = 180


class BrokerRefusal(Exception):
    """The broker declined a request; the reason is returned to the program."""


@dataclass
class BrokerLimits:
    """Every bound the broker enforces, in one place so it can be audited."""

    #: Exact hosts the broker will contact. A request for anything else is
    #: refused: the injected callable must not become a general socket.
    allowed_hosts: frozenset[str]
    #: Hard ceiling on provider calls for the whole run. Generated code loops.
    maximum_calls: int
    #: Ceiling on completion tokens per call, so one request cannot spend the
    #: budget the ceiling above is meant to bound.
    maximum_completion_tokens: int = 512
    #: Models the broker will address, so a program cannot silently switch to
    #: a more expensive one.
    allowed_models: frozenset[str] = frozenset()


@dataclass
class BrokerLedger:
    """What the broker did, for the record."""

    calls: int = 0
    refusals: list[str] = field(default_factory=list)
    prompts: list[dict[str, Any]] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": "llm-broker-ledger.v1",
            "calls": self.calls,
            "refusals": list(self.refusals),
            "prompts": list(self.prompts),
        }


class LLMBroker:
    """Serve bounded provider calls over a Unix socket, holding the credential.

    Started before the sandbox runs and stopped after; the socket path is the
    only thing the worker learns.
    """

    def __init__(
        self,
        *,
        socket_path: Path,
        endpoint: str,
        api_key: str,
        limits: BrokerLimits,
    ) -> None:
        self.socket_path = Path(socket_path)
        self.endpoint = endpoint
        self._api_key = api_key
        self.limits = limits
        self.ledger = BrokerLedger()
        self._server: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    # -- lifecycle -------------------------------------------------------

    def start(self) -> None:
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(self.socket_path))
        # Only the owner may speak to the broker.
        os.chmod(self.socket_path, 0o600)
        server.listen(8)
        server.settimeout(0.5)
        self._server = server
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        if self._server is not None:
            self._server.close()
        if self.socket_path.exists():
            self.socket_path.unlink()

    def __enter__(self) -> LLMBroker:
        self.start()
        return self

    def __exit__(self, *exception: object) -> None:
        self.stop()

    # -- serving ---------------------------------------------------------

    def _serve(self) -> None:
        assert self._server is not None
        while not self._stop.is_set():
            try:
                connection, _ = self._server.accept()
            except (TimeoutError, socket.timeout):
                continue
            except OSError:
                break
            with connection:
                try:
                    self._handle(connection)
                except Exception:  # noqa: BLE001 - a broker fault must not kill the run
                    continue

    def _handle(self, connection: socket.socket) -> None:
        connection.settimeout(_READ_TIMEOUT_SECONDS)
        chunks: list[bytes] = []
        total = 0
        while b"\n" not in b"".join(chunks[-2:] or [b""]):
            chunk = connection.recv(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > _MAX_FRAME_BYTES:
                self._reply(connection, {"error": "request_too_large"})
                return
            chunks.append(chunk)
        raw = b"".join(chunks).strip()
        if not raw:
            return
        try:
            request = json.loads(raw)
        except json.JSONDecodeError:
            self._reply(connection, {"error": "request_not_json"})
            return
        try:
            self._reply(connection, {"ok": self._call(request)})
        except BrokerRefusal as refusal:
            with self._lock:
                self.ledger.refusals.append(str(refusal))
            self._reply(connection, {"error": str(refusal)})

    @staticmethod
    def _reply(connection: socket.socket, payload: dict) -> None:
        connection.sendall(json.dumps(payload).encode("utf-8") + b"\n")

    # -- the one verb ----------------------------------------------------

    def _call(self, request: dict) -> dict:
        prompt = request.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise BrokerRefusal("prompt must be a non-empty string")
        model = request.get("model")
        if self.limits.allowed_models and model not in self.limits.allowed_models:
            raise BrokerRefusal(
                f"model {model!r} is outside the authorized set "
                f"{sorted(self.limits.allowed_models)}"
            )
        host = urllib.request.urlparse(self.endpoint).hostname or ""
        if host not in self.limits.allowed_hosts:
            # Defensive: the endpoint is broker-side, so this can only trip if
            # the broker itself was constructed wrongly.
            raise BrokerRefusal(f"endpoint host {host!r} is not authorized")

        with self._lock:
            if self.ledger.calls >= self.limits.maximum_calls:
                raise BrokerRefusal(
                    f"call ceiling reached ({self.limits.maximum_calls}); "
                    "no further provider calls are authorized for this run"
                )
            self.ledger.calls += 1
            index = self.ledger.calls

        payload = {
            "model": model,
            "messages": (
                [{"role": "system", "content": request["system"]}]
                if isinstance(request.get("system"), str) and request["system"].strip()
                else []
            )
            + [{"role": "user", "content": prompt}],
            "max_tokens": min(
                int(request.get("max_tokens", 256) or 256),
                self.limits.maximum_completion_tokens,
            ),
            "reasoning_effort": "none",
        }
        for knob in ("temperature", "top_p", "seed"):
            if knob in request and isinstance(request[knob], (int, float)):
                payload[knob] = request[knob]

        started = time.monotonic()
        text, error = self._send(payload)
        with self._lock:
            self.ledger.prompts.append(
                {
                    "index": index,
                    "model": model,
                    "prompt_sha256_prefix": _digest_prefix(prompt),
                    "knobs": {k: payload[k] for k in ("temperature", "top_p", "seed")
                              if k in payload},
                    "elapsed_ms": int((time.monotonic() - started) * 1000),
                    "error": error,
                }
            )
        if error is not None:
            raise BrokerRefusal(f"provider call failed: {error}")
        return {"text": text, "call_index": index,
                "calls_remaining": self.limits.maximum_calls - index}

    def _send(self, payload: dict) -> tuple[str, str | None]:
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            return "", f"{type(error).__name__}"
        try:
            return (body["choices"][0]["message"].get("content") or "").strip(), None
        except (KeyError, IndexError, TypeError):
            return "", "malformed_provider_response"


def _digest_prefix(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


__all__ = ["BrokerLedger", "BrokerLimits", "BrokerRefusal", "LLMBroker"]
