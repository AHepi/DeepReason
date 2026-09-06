"""ARM 0 — the same model, no harness. PREREG_D8.md §1.

K = 3 independent chat completions, user message = the frozen problem
description verbatim, max_tokens 8192, reasoning off, no response_format, no
system prompt, provider-default temperature. Each call's request (key
omitted), response, usage and finish_reason go to d8/arm0/call-<k>.json.
Transport failures retry with backoff (4 attempts); an empty or
length-truncated completion is recorded as such and kept.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "arm0"
ENDPOINT = "https://ollama.com/v1/chat/completions"
MODEL = "qwen3.5:397b"
K = 3
MAX_TOKENS = 8192


def question() -> str:
    root = HERE.parent / "runs" / "input-d8"
    run_input = json.loads((root / "run-input.json").read_text(encoding="utf-8"))
    return run_input["problem"]["description"]


def one_call(key: str, q: str, k: int) -> dict:
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": q}],
        "max_tokens": MAX_TOKENS,
        "reasoning": {"effort": "none"},
    }
    record: dict = {"schema": "d8-arm0-call.v1", "k": k, "request": body, "attempts": []}
    for attempt in range(4):
        t0 = time.time()
        try:
            req = urllib.request.Request(
                ENDPOINT,
                data=json.dumps(body).encode(),
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=900) as r:
                response = json.loads(r.read())
        except urllib.error.HTTPError as e:
            record["attempts"].append({"attempt": attempt + 1, "error": f"HTTP {e.code}", "seconds": round(time.time() - t0, 1)})
            time.sleep(2 ** (attempt + 1))
            continue
        except Exception as e:  # noqa: BLE001 - transport
            record["attempts"].append({"attempt": attempt + 1, "error": repr(e)[:200], "seconds": round(time.time() - t0, 1)})
            time.sleep(2 ** (attempt + 1))
            continue
        choice = (response.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content") or ""
        record.update(
            {
                "response": response,
                "content": content,
                "content_chars": len(content),
                "usage": response.get("usage"),
                "finish_reason": choice.get("finish_reason"),
                "seconds": round(time.time() - t0, 1),
                "completed": bool(choice.get("finish_reason")) and bool(content.strip()),
            }
        )
        record["attempts"].append({"attempt": attempt + 1, "ok": True, "seconds": record["seconds"]})
        return record
    record["completed"] = False
    record["content"] = ""
    return record


def main() -> int:
    key = os.environ["OLLAMA_API_KEY"]
    q = question()
    OUT.mkdir(exist_ok=True)
    summary = {"schema": "d8-arm0-result.v1", "model": MODEL, "k": K, "calls": []}
    for k in range(1, K + 1):
        path = OUT / f"call-{k}.json"
        if path.exists():
            rec = json.loads(path.read_text(encoding="utf-8"))
            print(f"call {k}: already recorded (completed={rec.get('completed')})", flush=True)
        else:
            print(f"call {k}: started {time.strftime('%FT%TZ', time.gmtime())}", flush=True)
            rec = one_call(key, q, k)
            path.write_text(json.dumps(rec, indent=1), encoding="utf-8")
            print(f"call {k}: completed={rec.get('completed')} chars={rec.get('content_chars')} usage={rec.get('usage')} finish={rec.get('finish_reason')} s={rec.get('seconds')}", flush=True)
        summary["calls"].append(
            {k2: rec.get(k2) for k2 in ("k", "completed", "content_chars", "usage", "finish_reason", "seconds")}
        )
    summary["completed_calls"] = sum(1 for c in summary["calls"] if c["completed"])
    summary["total_tokens"] = sum(int((c["usage"] or {}).get("total_tokens", 0)) for c in summary["calls"])
    (OUT / "ARM0_RESULT.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0 if summary["completed_calls"] == K else 1


if __name__ == "__main__":
    sys.exit(main())
