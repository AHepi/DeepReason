#!/usr/bin/env python3
"""PREREG §8 step 2: ONE call confirming reachability, the model id, and that
reasoning_effort "none" really returns an empty reasoning payload (the record
says unset is NOT off).  Writes preflight.json; changes nothing."""
import json
import os
import pathlib

import requests

HERE = pathlib.Path(__file__).resolve().parent
BODY = {
    "model": "glm-5.2",
    "messages": [
        {"role": "system", "content": "Answer with one short sentence."},
        {"role": "user", "content": "Name one property of a falsifiable conjecture."},
    ],
    "temperature": 0.9,
    "top_p": 0.95,
    "max_tokens": 200,
    "reasoning_effort": "none",
}
key = os.environ["OLLAMA_API_KEY"]
r = requests.post("https://ollama.com/v1/chat/completions", json=BODY,
                  headers={"Authorization": f"Bearer {key}"}, timeout=300)
payload = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"_body": r.text[:5000]}
msg = ((payload.get("choices") or [{}])[0].get("message") or {})
out = {
    "http_status": r.status_code,
    "model_echoed": payload.get("model"),
    "content": msg.get("content"),
    "reasoning_field_present": any(k for k in msg if "reason" in k.lower()),
    "reasoning_payload": {k: v for k, v in msg.items() if "reason" in k.lower()},
    "usage": payload.get("usage"),
    "raw": payload,
}
(HERE / "preflight.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({k: v for k, v in out.items() if k != "raw"}, indent=2, ensure_ascii=False))
