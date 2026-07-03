"""LLM endpoints (spec §9): frontier APIs | ollama | llama.cpp |
OpenAI-compatible — mix freely per role. MockEndpoint serves tests and
replay experiments without network.
"""

import json
import urllib.request


class MockEndpoint:
    """Returns scripted responses in order (raises when exhausted), or — when
    given a callable — computes each response from the prompt."""

    def __init__(self, responses, name: str = "mock", model: str = "mock") -> None:
        if callable(responses):
            self._fn = responses
            self._responses: list[str] | None = None
        else:
            self._fn = None
            self._responses = list(responses)
        self.name = name
        self.model = model

    def complete(self, prompt: str) -> str:
        if self._fn is not None:
            return self._fn(prompt)
        if not self._responses:
            raise RuntimeError("MockEndpoint exhausted")
        return self._responses.pop(0)


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
    ) -> None:
        self.name = base_url
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.timeout_s = timeout_s

    def complete(self, prompt: str) -> str:
        body: dict = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        if self.temperature is not None:
            body["temperature"] = self.temperature
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
        return data["choices"][0]["message"]["content"]
