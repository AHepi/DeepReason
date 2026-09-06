"""ONE throwaway call through the ARM M endpoint override. Not an arm.

Shows, before ARM M launches, that the `reasoning: none` field is honoured on
this route and that content comes back non-empty under json mode with the
profile's completion cap. PREREG_D8.md §6 step 2. Output -> d8/PROBE.txt.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "mini"))

from deepreason.provider_profile import resolve_provider_profile  # noqa: E402
from reasoning_endpoint import endpoint_from_profile  # noqa: E402


def main() -> int:
    profile = resolve_provider_profile(None).profile
    key = os.environ[profile.credential_env]
    ep = endpoint_from_profile(profile, key)
    t0 = time.time()
    content = ep.complete('Return the JSON object {"ok": true} and nothing else.')
    out = {
        "schema": "d8-probe-result.v1",
        "model": profile.model_id,
        "reasoning_field_sent": True,
        "content": content,
        "content_chars": len(content),
        "usage": ep.last_usage,
        "finish_reason": ep.last_finish_reason,
        "transport_attempts": ep.last_transport_attempts,
        "seconds": round(time.time() - t0, 1),
    }
    text = json.dumps(out, indent=1)
    (HERE / "PROBE.txt").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if content.strip() else 1


if __name__ == "__main__":
    sys.exit(main())
