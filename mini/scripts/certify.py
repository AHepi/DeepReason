#!/usr/bin/env python
"""Seat certification for the mini instrument (MINI_PLAN §6 risk 2):
run the trimmed planted-flaw battery against every configured seat.
A seat above the 0.25 error ceiling must not judge anything.

Usage: DEEPSEEK_API_KEY=... [POOLSIDE_API_KEY=...] python mini/scripts/certify.py
"""

import json
import os
import sys
from pathlib import Path

MINI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINI))

from minireason.call import HttpEndpoint, TokenMeter  # noqa: E402
from minireason.judge import certify_seat  # noqa: E402
from minireason.log import BlobStore  # noqa: E402


def main() -> int:
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if not deepseek_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1
    seats = {
        "pro/off": HttpEndpoint("https://api.deepseek.com", "deepseek-v4-pro",
                                api_key=deepseek_key, temperature=0.0, max_tokens=600),
        "flash/default": HttpEndpoint("https://api.deepseek.com", "deepseek-v4-flash",
                                      api_key=deepseek_key, temperature=0.0,
                                      max_tokens=600),
    }
    poolside_key = os.environ.get("POOLSIDE_API_KEY")
    if poolside_key:
        seats["laguna-m.1/default"] = HttpEndpoint(
            "https://inference.poolside.ai/v1", "poolside/laguna-m.1",
            api_key=poolside_key, temperature=0.0, max_tokens=600)

    meter = TokenMeter(budget=60_000)
    blobs = BlobStore(Path("runs/mini_certify_blobs"))
    report = {"experiment": "mini seat certification (trimmed planted-flaw battery)",
              "seats": {}}
    for name, endpoint in seats.items():
        result = certify_seat(endpoint, meter, blobs)
        report["seats"][name] = result
        print(f"{name}: {result}", flush=True)
    report["tokens"] = meter.snapshot()
    out = MINI.parent / "experiments" / "results" / "mini_seat_certification.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if all(s["passes"] for s in report["seats"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
