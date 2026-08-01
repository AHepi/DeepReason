"""Native one-shot baselines: the same question, thinking on, one reply each.

Records the full sanitizable outcome per model (content, visible
reasoning if the provider returns it, usage, wall time) so the
comparison against DeepReason runs is grounded in durable artifacts.
"""

import json
import os
import sys
import time
import urllib.request

LIVE = os.path.dirname(os.path.abspath(__file__))
QUESTION = (
    "When two independently generated conclusions inside a deterministic "
    "reasoning system appear to agree, by what criteria should the system "
    "decide they are the same claim rather than distinct claims that "
    "merely overlap, and what does it risk by merging too eagerly or too "
    "reluctantly?"
)
MODELS = {
    "glm": "glm-5.2",
    "kimi": "kimi-k2.6",
    "deepseek": "deepseek-v4-pro",
}


def call(model_id: str) -> dict:
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": QUESTION}],
        # Thinking stays ON (provider default for these models); the large
        # completion budget keeps hidden reasoning from starving content
        # (kimi-k2.6 returned empty content at 8192 in the last campaign).
        "max_tokens": 16384,
    }
    request = urllib.request.Request(
        "https://ollama.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + os.environ["OLLAMA_API_KEY"],
            "Content-Type": "application/json",
        },
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=1800) as response:
        body = json.load(response)
    elapsed = time.monotonic() - started
    message = body["choices"][0]["message"]
    return {
        "model": model_id,
        "question": QUESTION,
        "seconds": round(elapsed, 1),
        "finish_reason": body["choices"][0].get("finish_reason"),
        "usage": body.get("usage"),
        "reasoning": message.get("reasoning") or message.get("reasoning_content"),
        "content": message.get("content"),
    }


def main() -> int:
    for slug, model_id in MODELS.items():
        target = os.path.join(LIVE, f"{slug}-native.json")
        print(f"[{slug}] {model_id} …", flush=True)
        try:
            outcome = call(model_id)
        except Exception as error:  # noqa: BLE001 - recorded, run continues
            outcome = {"model": model_id, "question": QUESTION, "error": str(error)}
        with open(target, "w", encoding="utf-8") as stream:
            json.dump(outcome, stream, indent=2, sort_keys=True)
        content = outcome.get("content") or ""
        print(
            f"[{slug}] done: {outcome.get('seconds', '?')}s, "
            f"{len(content)} content chars, "
            f"finish={outcome.get('finish_reason')}, "
            f"error={outcome.get('error', 'none')[:120]}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
