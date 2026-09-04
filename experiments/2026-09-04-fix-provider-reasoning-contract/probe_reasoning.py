"""Guarded live probe: does Ollama Cloud accept the body the harness builds
when a seat carries a reasoning value?

Decides part 2 of DIAGNOSIS.md's falsifiable prediction, which no offline
artifact can decide. Every case sends a body built by the harness's OWN
`OpenAICompatEndpoint.build_body`, except the two clearly-labelled CONTROL
cases, which send hand-built bodies to reproduce the 2026-09-04 refusal and
to establish the baseline.

Guards, from GOAL.md and CLAUDE.md's live-run rules:
  * at most 3 concurrent calls (Ollama Cloud Pro plan limit,
    docs/OLLAMA_CLOUD_OPERATIONS.md s1);
  * the key is read at call time from the environment or a gitignored env
    file, is never printed, and is scrubbed from every recorded transcript;
  * small caps and a one-token question -- this probe measures the request
    CONTRACT, not model behaviour.

Usage:
    OLLAMA_API_KEY=... python experiments/.../probe_reasoning.py
    python experiments/.../probe_reasoning.py --env-file <path to gitignored env>
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from deepreason.llm.endpoints import OpenAICompatEndpoint

BASE_URL = "https://ollama.com/v1"
PROVIDER = "ollama"
MAX_CONCURRENCY = 3
HERE = pathlib.Path(__file__).parent

# Every distinct model in the committed provider-profile catalog: the census
# is `git ls-files | grep provider.yaml$`, all of them provider=ollama at
# BASE_URL. The two trailing ids carry a committed model-profile document
# (docs/model-profiles/) without a committed provider profile.
CATALOG_MODELS = ("qwen3.5:397b", "glm-5.2", "kimi-k2.6", "deepseek-v4-pro")
PROFILE_ONLY_MODELS = ("glm-5.3", "gpt-oss:120b")

# The neutral vocabulary of llm/providers.py, plus None (knob omitted).
REASONING_VALUES = (None, "none", "low", "medium", "high", "max", 512)

PROMPT = 'Reply with exactly this JSON and nothing else: {"ok":true}'


def read_key(env_file: pathlib.Path | None) -> str:
    import os

    key = os.environ.get("OLLAMA_API_KEY", "").strip()
    if key:
        return key
    if env_file and env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip().startswith("OLLAMA_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit(
        "no credential: set OLLAMA_API_KEY or pass --env-file pointing at a "
        "gitignored env file containing OLLAMA_API_KEY=..."
    )


def scrub(text: str, key: str) -> str:
    out = text.replace(key, "<KEY>") if key else text
    return re.sub(r"(sk-|ollama-)[A-Za-z0-9_\-]{8,}", r"\1<REDACTED>", out)


def harness_body(model: str, reasoning) -> dict:
    """The body the harness itself would send for this seat."""
    endpoint = OpenAICompatEndpoint(
        base_url=BASE_URL,
        model=model,
        api_key=None,
        max_tokens=2000,
        json_mode=True,
        reasoning=reasoning,
        provider=PROVIDER,
    )
    return endpoint.build_body(PROMPT)


def post(body: dict, key: str, timeout: int = 120) -> dict:
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"http": response.status, "payload": json.loads(response.read().decode())}
    except urllib.error.HTTPError as error:
        return {"http": error.code, "payload_text": error.read().decode()[:1200]}
    except Exception as error:  # transport, not contract
        return {"http": None, "transport_error": f"{type(error).__name__}: {error}"}


def run_case(case: dict, key: str) -> dict:
    result = post(case["body"], key)
    row = dict(case)
    row.pop("body_secret", None)
    if "payload" in result:
        choice = (result["payload"].get("choices") or [{}])[0]
        message = choice.get("message") or {}
        row.update(
            http=result["http"],
            accepted=True,
            content=(message.get("content") or "")[:120],
            reasoning_chars=len(message.get("reasoning") or message.get("reasoning_content") or ""),
            usage=result["payload"].get("usage"),
            finish_reason=choice.get("finish_reason"),
        )
    elif "payload_text" in result:
        row.update(http=result["http"], accepted=False, error=scrub(result["payload_text"], key))
    else:
        row.update(http=None, accepted=None, error=result["transport_error"])
    return row


def build_cases() -> list[dict]:
    cases: list[dict] = []
    for model in CATALOG_MODELS + PROFILE_ONLY_MODELS:
        origin = "catalog" if model in CATALOG_MODELS else "model-profile-only"
        for value in REASONING_VALUES:
            body = harness_body(model, value)
            cases.append(
                {
                    "kind": "harness",
                    "origin": origin,
                    "model": model,
                    "reasoning_value": value,
                    "wire_keys": sorted(k for k in body if k not in ("model", "messages")),
                    "body": body,
                }
            )
    # CONTROLS, hand-built, one model. These are NOT what the harness sends.
    control_model = CATALOG_MODELS[0]
    base = harness_body(control_model, None)
    for label, extra in (
        ("bare-reasoning-string (the 2026-09-04 probe's shape)", {"reasoning": "none"}),
        ("reasoning-object", {"reasoning": {"effort": "none"}}),
        ("think-false", {"think": False}),
    ):
        cases.append(
            {
                "kind": "control",
                "origin": "control",
                "model": control_model,
                "reasoning_value": label,
                "wire_keys": sorted(extra),
                "body": dict(base, **extra),
            }
        )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=pathlib.Path, default=HERE / "env")
    parser.add_argument("--out", type=pathlib.Path, default=HERE / "PROBE.json")
    args = parser.parse_args()

    key = read_key(args.env_file)
    cases = build_cases()
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as pool:
        rows = list(pool.map(lambda case: run_case(case, key), cases))

    width = max(len(str(r["reasoning_value"])) for r in rows)
    for row in rows:
        verdict = {True: "ACCEPTED", False: "REFUSED", None: "TRANSPORT"}[row["accepted"]]
        detail = (
            f"content={row['content']!r} reas={row['reasoning_chars']}"
            if row["accepted"]
            else str(row.get("error", ""))[:160].replace("\n", " ")
        )
        print(
            f"{row['model']:20s} {str(row['reasoning_value']):{width}s} "
            f"{'+'.join(row['wire_keys']):45s} http={str(row['http']):4s} {verdict:9s} {detail}"
        )

    args.out.write_text(json.dumps({"base_url": BASE_URL, "rows": rows}, indent=1, default=str))
    print(f"\nwrote {args.out}")

    catalog = [r for r in rows if r["origin"] == "catalog" and r["reasoning_value"] is not None]
    every_catalog_value_accepted = all(r["accepted"] for r in catalog)
    print(
        "\nGOAL CRITERION 2 (a live seat call with a reasoning value set succeeds "
        f"on every committed catalog profile): {'MET' if every_catalog_value_accepted else 'NOT MET'}"
    )
    return 0 if every_catalog_value_accepted else 1


if __name__ == "__main__":
    sys.exit(main())
