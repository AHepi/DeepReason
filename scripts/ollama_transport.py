#!/usr/bin/env python3
"""Transport for review_harness: the operator's Ollama Cloud endpoint.

review_harness ships no network code and no credential handling on purpose;
a transport is any callable (system, user, params) -> reply_text. This one
reads its key from the process environment ONLY (OLLAMA_API_KEY), never from
an argument and never from a file in the repository — the ledger's verifier
refuses any row carrying credential material, so a mistake here fails loudly
rather than silently committing a key.

Not an acceptance command, and cannot become one: it calls an external model,
whose reply is evidence about the model, not a verdict about the artifact
(FR-16 — the params it records are provenance, not a replay guarantee).
"""
import os

BASE_URL = os.environ.get("TREADLE_BASE_URL", "https://ollama.com/v1")


def OllamaTransport(system, user, params):
    import httpx

    key = os.environ.get("OLLAMA_API_KEY")
    if not key:
        raise RuntimeError(
            "OLLAMA_API_KEY is not set. Export it; never pass it as an argument "
            "and never write it into the repository."
        )
    body = {
        "model": params["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": params.get("temperature", 0.0),
        "max_tokens": params.get("max_tokens", 4000),
    }
    if "seed" in params:
        body["seed"] = params["seed"]
    r = httpx.post(
        f"{BASE_URL.rstrip('/')}/chat/completions",
        json=body,
        headers={"Authorization": f"Bearer {key}"},
        timeout=300.0,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
