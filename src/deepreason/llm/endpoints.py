"""LLM endpoints (spec §9): frontier APIs | ollama | llama.cpp |
OpenAI-compatible — mix freely per role. MockEndpoint serves tests and
replay experiments without network.
"""

import base64
import http.client
import json
import time
import urllib.error
import urllib.request

from deepreason.llm.repair import OutputMechanism

_RETRYABLE_HTTP = {429, 500, 502, 503, 504}
_BACKOFFS = (2, 4, 8)
# Bounded read-timeout policy. One authoritative default wait per attempt
# (endpoints inherit it; the role table overrides via timeout_s), and a
# fixed escalation: attempt 1 waits 1x, the retry after a read timeout
# waits 2x, and a second read timeout is terminal — max total wait 3x the
# base (900s at the 300s default), never an unbounded ladder. A read
# timeout proves only that no complete response arrived before the
# deadline; since non-streaming completions can legitimately need longer
# than the base wait, one wider retry is justified — more is not.
DEFAULT_TIMEOUT_S = 300
TIMEOUT_FACTORS = (1, 2)

# JSON-value grammar accepted by llama.cpp-compatible constrained decoders.
# Semantic field constraints remain in the WireContract validator.
JSON_GBNF = r'''root ::= ws value ws
value ::= object | array | string | number | "true" | "false" | "null"
object ::= "{" ws (pair (ws "," ws pair)*)? ws "}"
pair ::= string ws ":" ws value
array ::= "[" ws (value (ws "," ws value)*)? ws "]"
string ::= "\"" chars "\""
chars ::= ([^"\\] | "\\" (["\\/bfnrt] | "u" hex hex hex hex))*
number ::= "-"? ("0" | [1-9] [0-9]*) ("." [0-9]+)? ([eE] [+-]? [0-9]+)?
hex ::= [0-9a-fA-F]
ws ::= [ \t\n\r]*'''


class EndpointError(RuntimeError):
    """A completion failed after transport retries (or non-retryably)."""


class _TransientBody(OSError):
    """A 200 response with a malformed/empty body — retryable like any
    transport fault (subclasses OSError so request_with_retries takes it)."""


def request_with_retries(fn):
    """Run fn(); retry transient network failures with 2s/4s/8s backoff.
    Non-retryable HTTP errors (auth, bad request) raise immediately."""
    last: Exception | None = None
    for delay in (*_BACKOFFS, None):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            if e.code not in _RETRYABLE_HTTP:
                raise EndpointError(f"HTTP {e.code}: {e.reason}") from e
            last = e
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError,
                http.client.HTTPException) as e:
            # HTTPException covers IncompleteRead — a mid-stream drop the
            # OSError net misses (observed live: killed two runs at cycle 1).
            last = e
        if delay is None:
            break
        time.sleep(delay)
    raise EndpointError(f"transport failed after retries: {last}") from last


def list_models(base_url: str, api_key: str | None) -> list[str]:
    """GET /models on an OpenAI-compatible endpoint; returns the id list."""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(base_url.rstrip("/") + "/models", headers=headers)

    def _once() -> dict:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    data = request_with_retries(_once)
    return [m["id"] for m in data.get("data", []) if isinstance(m, dict) and m.get("id")]


def _pick_primary(available: list[str]) -> str:
    for want in (("v4", "pro"), ("v4",), ("pro",), ("chat",)):
        hits = [m for m in available if all(w in m.lower() for w in want)]
        if hits:
            return sorted(hits)[0]
    if not available:
        raise EndpointError("provider returned no models to resolve 'auto'")
    return sorted(available)[0]


def _pick_alt(available: list[str], primary: str) -> str:
    others = [m for m in available if m != primary]
    for want in ("reason", "r1"):
        hits = [m for m in others if want in m.lower()]
        if hits:
            return sorted(hits)[0]
    return sorted(others)[0] if others else primary


_MODEL_CACHE: dict[tuple[str, str | None], list[str]] = {}


def resolve_model(model: str, base_url: str, api_key: str | None) -> str:
    """Resolve the ``auto``/``auto-alt`` model sentinels against the
    provider's live /models list (cached per endpoint). Concrete ids pass
    through unchanged. This is what makes the shipped ``model: auto`` role
    table usable from ``deepreason run`` and MCP, not just live_run."""
    if model not in ("auto", "auto-alt"):
        return model
    key = (base_url, api_key)
    available = _MODEL_CACHE.get(key)
    if available is None:
        available = list_models(base_url, api_key)
        _MODEL_CACHE[key] = available
    primary = _pick_primary(available)
    return _pick_alt(available, primary) if model == "auto-alt" else primary


def mean_surprisal(logprobs_block: dict | None) -> float | None:
    """-mean(logprob) over the completion's sampled tokens (OpenAI-shaped
    ``logprobs.content``). A surprisal proxy for token-level uncertainty —
    true entropy would need the full per-position distribution."""
    if not logprobs_block:
        return None
    content = logprobs_block.get("content") or []
    values = [t["logprob"] for t in content if isinstance(t.get("logprob"), (int, float))]
    if not values:
        return None
    return -sum(values) / len(values)


class MockEndpoint:
    """Returns scripted responses in order (raises when exhausted), or — when
    given a callable — computes each response from the prompt. Reports an
    estimated usage (chars/4) so token accounting is testable."""

    def __init__(self, responses, name: str = "mock", model: str = "mock") -> None:
        if callable(responses):
            self._fn = responses
            self._responses: list[str] | None = None
        else:
            self._fn = None
            self._responses = list(responses)
        self.name = name
        self.model = model
        self.last_usage: dict | None = None
        self.last_images: list[bytes] = []
        self.last_kwargs: dict = {}
        self.last_transport_attempts = 0
        self.last_transport_diagnostics: list[str] = []

    def complete(self, prompt: str, images: list[bytes] | None = None, **kwargs) -> str:
        self.last_usage = None
        self.last_transport_attempts = 1
        self.last_transport_diagnostics = []
        self.last_images = list(images) if images else []  # test-inspectable
        self.last_kwargs = dict(kwargs)
        if self._fn is not None:
            response = self._fn(prompt)
        elif self._responses:
            response = self._responses.pop(0)
        else:
            raise RuntimeError("MockEndpoint exhausted")
        self.last_usage = {
            "prompt_tokens": max(1, len(prompt) // 4),
            "completion_tokens": max(1, len(response) // 4),
        }
        return response


class OpenAICompatEndpoint:
    """Chat-completions endpoint (OpenAI-compatible: OpenAI, ollama,
    llama.cpp server, most gateways)."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        temperature: float | None = None,
        timeout_s: int = DEFAULT_TIMEOUT_S,
        max_tokens: int | None = None,
        json_mode: bool = False,
        request_logprobs: bool = False,
        reasoning: str | int | None = None,
        provider: str | None = None,
        output_mechanism: str | OutputMechanism = OutputMechanism.JSON_TEXT,
    ) -> None:
        from deepreason.llm.providers import infer_provider

        self.name = base_url
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        # response_format json_object: stops models prefacing the JSON with
        # analysis prose (observed live: judge rulings truncating at the cap).
        self.json_mode = json_mode
        self.request_logprobs = request_logprobs
        # Neutral reasoning knob, realized per provider (llm/providers.py) —
        # the dominant cost lever (docs/TOKEN_ECONOMY.md angle 1).
        self.reasoning = reasoning
        self.provider = provider or infer_provider(base_url)
        self.output_mechanism = OutputMechanism(output_mechanism).value
        self.last_usage: dict | None = None
        self.last_finish_reason: str | None = None
        self.last_mean_surprisal: float | None = None
        self.last_transport_attempts = 0
        self.last_transport_diagnostics: list[str] = []

    def build_body(
        self,
        prompt: str,
        images: list[bytes] | None = None,
        *,
        response_schema: dict | None = None,
        output_mechanism: str | OutputMechanism | None = None,
        stop: list[str] | None = None,
    ) -> dict:
        from deepreason.llm.providers import reasoning_body

        # Vision (multimodal): with images, content becomes OpenAI content
        # parts — text first, then one image_url part per PNG as a base64
        # data URL. Without images the body is byte-identical to before.
        if images:
            content: object = [
                {"type": "text", "text": prompt},
                *(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,"
                            + base64.b64encode(png).decode()
                        },
                    }
                    for png in images
                ),
            ]
        else:
            content = prompt
        body: dict = {"model": self.model, "messages": [{"role": "user", "content": content}]}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if self.max_tokens is not None:
            body["max_tokens"] = self.max_tokens
        mechanism = OutputMechanism(output_mechanism) if output_mechanism else None
        if mechanism == OutputMechanism.NATIVE_JSON_SCHEMA:
            if not response_schema:
                raise EndpointError("native_json_schema requires response_schema")
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "deepreason_output",
                    "strict": True,
                    "schema": response_schema,
                },
            }
        elif mechanism == OutputMechanism.GRAMMAR:
            # Grammar is a fixed lease property. Unsupported providers reject
            # the request; this method never falls back to a different mode.
            body["grammar"] = JSON_GBNF
        elif self.json_mode and mechanism is None:
            body["response_format"] = {"type": "json_object"}
        if stop:
            body["stop"] = list(stop)
        if self.request_logprobs:
            body["logprobs"] = True
        body.update(reasoning_body(self.provider, self.reasoning))
        return body

    def complete(
        self,
        prompt: str,
        images: list[bytes] | None = None,
        *,
        response_schema: dict | None = None,
        output_mechanism: str | OutputMechanism | None = None,
        stop: list[str] | None = None,
    ) -> str:
        self.last_usage = None
        self.last_finish_reason = None
        self.last_mean_surprisal = None
        self.last_transport_attempts = 0
        self.last_transport_diagnostics = []
        body = self.build_body(
            prompt,
            images,
            response_schema=response_schema,
            output_mechanism=output_mechanism,
            stop=stop,
        )
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.name.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode(),
            headers=headers,
        )

        # Bounded read-timeout escalation (TIMEOUT_FACTORS): retrying an
        # identical wait after a read timeout fails identically (observed
        # live: two variator calls dropped after 4 x 120s waits while ~110s
        # generations were succeeding at the same endpoint), so the retry
        # waits 2x — and a second read timeout is terminal, keeping the
        # total wait bounded at 3x. Read timeouts are counted separately
        # from other transport faults, which keep the plain retry/backoff.
        # The counter lives in the closure so request_with_retries keeps
        # its signature and its other callers are untouched.
        read_timeouts = 0

        def _note_transport(error: Exception) -> None:
            code = getattr(error, "code", None)
            label = type(error).__name__ + (f":HTTP-{code}" if code else "")
            detail = str(error).replace("\n", " ")[:200]
            self.last_transport_diagnostics.append(
                f"{label}:{detail}" if detail else label
            )

        def _timed_out(e: Exception) -> bool:
            return isinstance(e, TimeoutError) or (
                isinstance(e, urllib.error.URLError)
                and isinstance(e.reason, TimeoutError)
            )

        def _once() -> dict:
            nonlocal read_timeouts
            self.last_transport_attempts += 1
            timeout = self.timeout_s * TIMEOUT_FACTORS[read_timeouts]
            try:
                # The stall can hit at connect/first byte (urlopen) or
                # mid-body (json.load reading the socket): both count.
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    try:
                        data = json.load(response)
                    except ValueError as e:
                        # 200 with a non-JSON body (gateway/proxy hiccup):
                        # transient in practice — let the retry loop take it.
                        raise _TransientBody(f"non-JSON response body: {e}") from e
            except Exception as e:
                _note_transport(e)
                if _timed_out(e):
                    read_timeouts += 1
                    if read_timeouts >= len(TIMEOUT_FACTORS):
                        waits = ", ".join(
                            f"{self.timeout_s * f}s" for f in TIMEOUT_FACTORS
                        )
                        # EndpointError is not retryable: terminal by design.
                        raise EndpointError(
                            f"no complete response within escalated read "
                            f"timeouts ({waits}): {e}"
                        ) from e
                raise
            # Malformed 200 shapes (empty body, missing choices, null content)
            # are usually transient server faults: surface them as retryable;
            # the post-retry guards below still catch the persistent case.
            try:
                if data["choices"][0]["message"]["content"] is None:
                    error = _TransientBody(
                        f"null content (finish_reason="
                        f"{data['choices'][0].get('finish_reason')!r})"
                    )
                    _note_transport(error)
                    raise error
            except (KeyError, IndexError, TypeError) as e:
                detail = data.get("error") if isinstance(data, dict) else data
                error = _TransientBody(f"malformed completion response: {detail!r}")
                _note_transport(error)
                raise error from e
            return data

        data = request_with_retries(_once)
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            detail = data.get("error") if isinstance(data, dict) else data
            raise EndpointError(f"malformed completion response: {detail!r}") from e
        if content is None:
            # Legal per the API (content filter; reasoning-only replies) —
            # surface as an endpoint failure so the caller's drop/retry
            # handling applies instead of crashing on None.
            raise EndpointError(
                f"null content (finish_reason={choice.get('finish_reason')!r})"
            )
        self.last_usage = data.get("usage") or None
        self.last_finish_reason = choice.get("finish_reason")
        self.last_mean_surprisal = mean_surprisal(choice.get("logprobs"))
        return content
