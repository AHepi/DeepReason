"""B0 — the no-harness arm. One call, same question, same model, same settings.

The 2026-09-03 law makes this the thing every harness arm is measured against:
*"the condition of success it something materially better than what's produced
without it."* `RESULTS_M1_QUALITY.md` §6 residue 5 records that no such arm
existed for this question, so nothing in the history tranche could speak to
whether either of its arms beat a single model call. This closes that.

WHAT IS HELD IDENTICAL to the harness arms, and why each one matters:

  * the model and endpoint (`qwen3.5:397b` on ollama.com/v1) -- a different
    model would make the comparison about models;
  * `reasoning: {"effort": "none"}` -- the arms' own provider profile sets it,
    and `judge.py` records that WITHOUT it this model spends its whole
    completion cap on hidden reasoning and emits an empty content field;
  * `max_tokens` 8192 -- the arms' `--maximum-completion-tokens`, so B0 is not
    handicapped or advantaged on room to write;
  * `temperature` 1.0 -- `judge.py`'s own value on this endpoint.

WHAT IS NOT HELD IDENTICAL, stated rather than hidden: the harness renders a
brief with criteria, neighbours, open criticisms and an output contract. B0
gets the question and nothing else. That IS the treatment. Adding any of it
back would make B0 a harness arm with fewer sections.

n = 12 INDEPENDENT CALLS, not one. A single call has no scatter, and the whole
experiment turns on whether an arm's gap exceeds noise; a baseline with no
measurable variance would make every comparison against it unfalsifiable.
Twelve keeps B0's spend inside the same order as one harness arm's.

Resumable: each answer is appended to `b0/answers.jsonl` as it lands, and a
re-run tops up to `--n` rather than starting over. The judging batches in this
tree were killed part-way twice by the container; a script that banks progress
to disk costs nothing and survives it.

Usage:
    python baseline_b0.py            # top up to 12
    python baseline_b0.py --n 12
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "b0"
ENDPOINT = "https://ollama.com/v1/chat/completions"
MODEL = "qwen3.5:397b"
MAX_TOKENS = 8192
TEMPERATURE = 1.0


def _key() -> str:
    for line in (HERE / "env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OLLAMA_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OLLAMA_API_KEY in the tranche env file")


def _call(key: str, question: str, attempts: int = 5):
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": question}],
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "reasoning": {"effort": "none"},
        }
    ).encode()
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                ENDPOINT,
                data=body,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(request, timeout=300) as response:
                payload = json.loads(response.read())
        except Exception as error:  # noqa: BLE001 - transport; retry
            print(f"    transport {type(error).__name__}, retrying", flush=True)
            time.sleep(2**attempt)
            continue
        message = (payload.get("choices") or [{}])[0].get("message", {})
        text = message.get("content") or ""
        if not text.strip():
            # The empty-content failure this model has on this endpoint when
            # reasoning is left on. Recorded, never silently retried away.
            print("    EMPTY content returned; retrying", flush=True)
            time.sleep(2**attempt)
            continue
        usage = payload.get("usage") or {}
        return {
            "text": text,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }
    return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=12)
    args = parser.parse_args(argv[1:])

    question = (HERE / "QUESTION.txt").read_text(encoding="utf-8").strip()
    OUT.mkdir(exist_ok=True)
    path = OUT / "answers.jsonl"
    have = [
        json.loads(line)
        for line in (path.read_text().splitlines() if path.exists() else [])
        if line.strip()
    ]
    print(f"B0: {len(have)} on disk, target {args.n}")
    key = _key()
    for index in range(len(have), args.n):
        got = _call(key, question)
        if got is None:
            print(f"  call {index + 1}: FAILED after retries; stopping", flush=True)
            return 1
        got["index"] = index
        got["chars"] = len(got["text"])
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(got) + "\n")
        print(
            f"  call {index + 1}/{args.n}: {got['chars']} chars, "
            f"{got['total_tokens']} tokens",
            flush=True,
        )
        time.sleep(1.0)
    print(f"B0 complete -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
