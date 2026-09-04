"""Reproduction: what the harness actually puts on the wire for the committed
launch config's critic seat, and what every provider adapter emits.

Offline and deterministic. Decides part 1 of DIAGNOSIS.md's falsifiable
prediction. Part 2 (does the provider still accept it) is not decidable
here and belongs to probe_reasoning.py.
"""

import json
import pathlib
import sys

from deepreason.llm.endpoints import OpenAICompatEndpoint
from deepreason.llm.providers import REASONING_ADAPTERS, reasoning_body

MANIFEST = pathlib.Path(
    "experiments/2026-09-03-change-provenance-history-channel/runs/home-m3/"
    "runs/run-5565bd1ef7011e3d25fef3197bdf1cdb/run-manifest.json"
)
PROBED_FIELD = "reasoning"  # the field the 2026-09-04 probe sent and P2 names


def main() -> int:
    route = json.loads(MANIFEST.read_text())["roles"]["argumentative_critic"][0]
    endpoint = OpenAICompatEndpoint(
        base_url=route["base_url"],
        model=route["model_id"],
        api_key=None,
        temperature=route["temperature"],
        timeout_s=route["timeout_s"],
        max_tokens=route["max_tokens"],
        json_mode=route["output_mode"] == "json_object",
        reasoning=route["reasoning"],
        provider=route["provider"],
        output_mechanism=route["output_mechanism"],
    )
    body = endpoint.build_body("probe")
    shown = dict(body, messages="<elided>")

    print("committed route     :", route["provider"], route["base_url"], route["model_id"])
    print("configured value    :", repr(route["reasoning"]))
    print("body the harness sends:", json.dumps(shown, sort_keys=True))
    print()
    print("keys carrying the reasoning value, per provider, for the value 'none':")
    for provider in sorted(REASONING_ADAPTERS):
        print(f"  {provider:9s} {json.dumps(reasoning_body(provider, 'none'), sort_keys=True)}")
    print()

    sends_effort = "reasoning_effort" in body
    sends_probed_field = PROBED_FIELD in body
    any_adapter_sends_probed_field = any(
        PROBED_FIELD in reasoning_body(p, v)
        for p in REASONING_ADAPTERS
        for v in ("none", "low", "medium", "high", "max", 512, None)
    )

    print(f"harness sends 'reasoning_effort'          : {sends_effort}")
    print(f"harness sends bare '{PROBED_FIELD}' (P2's field) : {sends_probed_field}")
    print(f"ANY adapter, ANY value, sends '{PROBED_FIELD}'   : {any_adapter_sends_probed_field}")

    ok = sends_effort and not sends_probed_field and not any_adapter_sends_probed_field
    print()
    print("PART 1 OF THE PREDICTION:", "CONFIRMED" if ok else "REFUTED")
    print("PART 2 (does the provider still accept this body?): NOT DECIDABLE OFFLINE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
