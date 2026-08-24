"""Minimal OpenAI-compatible chat client (Ollama local proxy or ollama.com).
Returns (content, finish_reason): finish_reason "length" with empty content
is the signature of a reasoning model exhausting max_tokens on its trace
before emitting output (defect #1)."""
from __future__ import annotations
import os, time
import httpx


class ChatError(RuntimeError):
    pass


def chat(messages, model, base_url=None, temperature=0.0, seed=17,
         max_tokens=4000, timeout=600.0, retries=2):
    base = (base_url or os.environ.get("TREADLE_BASE_URL")
            or "http://localhost:11434/v1").rstrip("/")
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("OLLAMA_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    payload = {"model": model, "messages": messages, "temperature": temperature,
               "max_tokens": max_tokens, "stream": False}
    if seed is not None:
        payload["seed"] = seed
    last = None
    for a in range(retries + 1):
        try:
            r = httpx.post(f"{base}/chat/completions", json=payload,
                           headers=headers, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return (choice["message"].get("content") or "",
                    (choice.get("finish_reason") or "unknown")
                    + f"|prompt_tokens={usage.get('prompt_tokens', '?')}")
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
            last = e
            if a < retries:
                time.sleep(2 * (a + 1))
    raise ChatError(f"chat failed after {retries+1} attempts: {last}")
