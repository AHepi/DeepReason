"""LLM endpoints (spec §9): frontier APIs | ollama | llama.cpp |
OpenAI-compatible — mix freely per role. MockEndpoint serves tests and
replay experiments without network.
"""

import json
import time
import urllib.error
import urllib.request

_RETRYABLE_HTTP = {429, 500, 502, 503, 504}
_BACKOFFS = (2, 4, 8)


class EndpointError(RuntimeError):
    """A completion failed after transport retries (or non-retryably)."""


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
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
            last = e
        if delay is None:
            break
        time.sleep(delay)
    raise EndpointError(f"transport failed after retries: {last}") from last


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
                return json.load(response)

        data = request_with_retries(_once)
        choice = data["choices"][0]
        self.last_usage = data.get("usage") or None
        self.last_finish_reason = choice.get("finish_reason")
        self.last_mean_surprisal = mean_surprisal(choice.get("logprobs"))
        return choice["message"]["content"]
