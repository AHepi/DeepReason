"""LLM endpoints (spec §9): frontier APIs | ollama | llama.cpp |
OpenAI-compatible — mix freely per role. MockEndpoint serves tests and
replay experiments without network.
"""

import json
import urllib.request


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
    ) -> None:
        self.name = base_url
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self.last_usage: dict | None = None
        self.last_finish_reason: str | None = None

    def complete(self, prompt: str) -> str:
        body: dict = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if self.max_tokens is not None:
            body["max_tokens"] = self.max_tokens
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.name.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode(),
            headers=headers,
        )
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            data = json.load(response)
        self.last_usage = data.get("usage") or None
        self.last_finish_reason = data["choices"][0].get("finish_reason")
        return data["choices"][0]["message"]["content"]
