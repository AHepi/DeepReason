"""LLM endpoints (spec §9): frontier APIs | ollama | llama.cpp |
OpenAI-compatible — mix freely per role. MockEndpoint serves tests and
replay experiments without network.
"""

import http.client
import json
import time
import urllib.error
import urllib.request

_RETRYABLE_HTTP = {429, 500, 502, 503, 504}
_BACKOFFS = (2, 4, 8)


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
                http.client.HTTPException, ValueError) as e:
            # A dropped/short chunked body raises http.client.IncompleteRead
            # (an HTTPException, NOT an OSError) or a base-16 ValueError from
            # the chunk-size parse — both are transient 200-stream faults, not
            # logic errors. Retrying re-issues the request; the LOGGED response
            # is whatever finally succeeds, so byte-replay is unaffected. This
            # gap crashed a 286k-token full-harness run mid-stream; mini's
            # call.py already caught these (experiments/results/
            # small_model_burden_report.json transport finding).
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

    def complete(self, prompt: str) -> str:
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
        timeout_s: int = 120,
        max_tokens: int | None = None,
        json_mode: bool = False,
        request_logprobs: bool = False,
        reasoning: str | int | None = None,
        provider: str | None = None,
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
        self.last_usage: dict | None = None
        self.last_finish_reason: str | None = None
        self.last_mean_surprisal: float | None = None

    def build_body(self, prompt: str) -> dict:
        from deepreason.llm.providers import reasoning_body

        body: dict = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if self.max_tokens is not None:
            body["max_tokens"] = self.max_tokens
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        if self.request_logprobs:
            body["logprobs"] = True
        body.update(reasoning_body(self.provider, self.reasoning))
        return body

    def complete(self, prompt: str) -> str:
        body = self.build_body(prompt)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.name.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode(),
            headers=headers,
        )

        def _once() -> dict:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                try:
                    data = json.load(response)
                except ValueError as e:
                    # 200 with a non-JSON body (gateway/proxy hiccup):
                    # transient in practice — let the retry loop take it.
                    raise _TransientBody(f"non-JSON response body: {e}") from e
            # Malformed 200 shapes (empty body, missing choices, null content)
            # are usually transient server faults: surface them as retryable;
            # the post-retry guards below still catch the persistent case.
            try:
                if data["choices"][0]["message"]["content"] is None:
                    raise _TransientBody(
                        f"null content (finish_reason="
                        f"{data['choices'][0].get('finish_reason')!r})"
                    )
            except (KeyError, IndexError, TypeError) as e:
                detail = data.get("error") if isinstance(data, dict) else data
                raise _TransientBody(f"malformed completion response: {detail!r}") from e
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
