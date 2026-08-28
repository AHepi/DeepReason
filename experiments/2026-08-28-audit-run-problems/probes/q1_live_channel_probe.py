#!/usr/bin/env python3
"""Q1 LIVE probe -- registered in PREREG_LITE.md, frozen before this ran.

Replays the ONE critic dispatch in six epochs that was shown both the premise
invitation and the citable-block legend (epoch 6 seq 180), verbatim from that
root's own prompt blob, and asks whether the seat fills `premise_evidence`.

Arm A  the prompt bytes exactly as the run sent them.
Arm B  the same bytes plus one appended exemplar of a filled entry.

Every request and response is written verbatim under probes/live/.
Stops and reports partial if the registered 100 000-token cap would be crossed.
"""
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

BLOB = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(__file__).resolve().parent / "live"
N = 8
TOKEN_CAP = 100_000
MODEL = "kimi-k3"
BASE = "https://ollama.com/v1"

EXEMPLAR = """

EXAMPLE of a filled premise_evidence entry, for form only — do not reuse its
content, and cite only a block id that appears in the CITABLE EVIDENCE BLOCKS
list above:

  "premise": "<the presupposition the problem makes>",
  "premise_evidence": [
    {"block": "028950f9751ab59a",
     "quote": "mutations no guard catches were reported as caught"}
  ]
"""


def call(prompt: str, key: str) -> tuple[dict, str]:
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "reasoning_effort": "low",
    }
    request = urllib.request.Request(
        BASE + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=900) as response:
        payload = json.loads(response.read().decode())
    text = payload["choices"][0]["message"]["content"]
    return payload, text


def hit(text: str) -> tuple[bool, object]:
    """A HIT is any case object carrying a non-empty premise_evidence list."""
    try:
        parsed = json.loads(text)
    except Exception:
        return False, "UNPARSEABLE"
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "premise_evidence" in node:
                found.append(node.get("premise_evidence"))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(parsed)
    return any(isinstance(f, list) and f for f in found), found


def main() -> int:
    key = os.environ.get("OLLAMA_API_KEY")
    if not key:
        print("no credential in OLLAMA_API_KEY", file=sys.stderr)
        return 2
    base_prompt = BLOB.read_text(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    arms = {"A_control": base_prompt, "B_exemplar": base_prompt + EXEMPLAR}
    spent = 0
    rows = []
    for arm, prompt in arms.items():
        for i in range(N):
            if spent >= TOKEN_CAP:
                print(f"STOPPING: registered cap {TOKEN_CAP} reached at {spent}")
                break
            try:
                payload, text = call(prompt, key)
            except urllib.error.HTTPError as error:
                detail = error.read().decode()[:400]
                rows.append({"arm": arm, "rep": i, "error": f"HTTP {error.code}", "detail": detail})
                print(f"{arm} rep {i}: HTTP {error.code} {detail[:120]}")
                time.sleep(2)
                continue
            except Exception as error:  # noqa: BLE001 - recorded, never silent
                rows.append({"arm": arm, "rep": i, "error": repr(error)})
                print(f"{arm} rep {i}: {error!r}")
                continue
            usage = payload.get("usage") or {}
            tokens = int(usage.get("total_tokens") or 0)
            spent += tokens
            is_hit, evidence = hit(text)
            (OUT / f"{arm}-{i:02d}-response.json").write_text(
                json.dumps(payload, indent=1), encoding="utf-8"
            )
            rows.append({
                "arm": arm, "rep": i, "tokens": tokens, "hit": is_hit,
                "premise_evidence_values": evidence,
                "response_chars": len(text),
            })
            print(f"{arm} rep {i}: tokens={tokens:6d} hit={is_hit} evidence={str(evidence)[:110]}")
    (OUT / "prompt-arm-A.txt").write_text(arms["A_control"], encoding="utf-8")
    (OUT / "prompt-arm-B.txt").write_text(arms["B_exemplar"], encoding="utf-8")
    summary = {
        "model": MODEL,
        "n_per_arm": N,
        "token_cap": TOKEN_CAP,
        "tokens_spent": spent,
        "calls_made": len([r for r in rows if "tokens" in r]),
        "errors": len([r for r in rows if "error" in r]),
        "hits": {
            arm: sum(1 for r in rows if r.get("arm") == arm and r.get("hit"))
            for arm in arms
        },
        "attempts": {
            arm: len([r for r in rows if r.get("arm") == arm and "tokens" in r])
            for arm in arms
        },
        "rows": rows,
    }
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print()
    print(json.dumps({k: summary[k] for k in
                      ("tokens_spent", "calls_made", "errors", "hits", "attempts")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
