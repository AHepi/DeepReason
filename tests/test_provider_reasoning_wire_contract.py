"""The wire shape each provider carries the neutral reasoning value in.

Regression (live probe 2026-09-04, 45 calls, transcript at
`experiments/2026-09-04-fix-provider-reasoning-contract/PROBE.json`):
Ollama Cloud refuses a bare `reasoning` STRING --

    HTTP 400  json: cannot unmarshal string into Go struct field
              ChatCompletionRequest.reasoning of type openai.Reasoning

-- while accepting `reasoning_effort` on all six catalog models across
the whole neutral vocabulary (42/42 HTTP 200). The harness has never sent
the refused field; the alarm that prompted this tranche
(`experiments/2026-09-04-experiment-blind-critic/PARKED.md` P2) read the
configuration VALUE "none" as though it were the wire FIELD `reasoning`.

What that makes load-bearing, and what these tests pin: which FIELD each
provider carries the value in. A silent move of that field is the failure
the provider now refuses, and nothing else in the suite would catch it --
`tests/test_providers.py` pins what each adapter DOES emit, and no test
pinned what none of them may emit.
"""

import json
import pathlib

from deepreason.llm.endpoints import OpenAICompatEndpoint
from deepreason.llm.providers import REASONING_ADAPTERS, reasoning_body

# The neutral vocabulary of `llm/providers.py`, plus None (knob omitted)
# and an int budget. Every value the probe sent live.
NEUTRAL_VALUES = (None, "none", "low", "medium", "high", "max", 512, 5000)

# The field the provider refuses as a string. Named once, here, because
# every assertion below is about it.
REFUSED_AS_STRING = "reasoning"

# The committed launch config the alarm named. Absence-tolerant: the
# route is asserted from the checked-in manifest when it is present, and
# from this transcribed copy otherwise, so the property is pinned either
# way rather than silently skipped.
LAUNCH_MANIFEST = pathlib.Path(
    "experiments/2026-09-03-change-provenance-history-channel/runs/home-m3/"
    "runs/run-5565bd1ef7011e3d25fef3197bdf1cdb/run-manifest.json"
)
LAUNCH_CRITIC_ROUTE = {
    "base_url": "https://ollama.com/v1",
    "model_id": "qwen3.5:397b",
    "provider": "ollama",
    "reasoning": "none",
    "max_tokens": 8192,
    "output_mode": "json_object",
    "output_mechanism": "json_text",
    "temperature": None,
    "timeout_s": 120,
}


def _launch_critic_route() -> dict:
    if LAUNCH_MANIFEST.exists():
        roles = json.loads(LAUNCH_MANIFEST.read_text())["roles"]
        route = roles["argumentative_critic"][0]
        assert route["reasoning"] == "none", (
            "the committed launch config no longer binds the value this "
            f"regression was written about: {route['reasoning']!r}"
        )
        return route
    return LAUNCH_CRITIC_ROUTE


def _body_for(route: dict) -> dict:
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
    return endpoint.build_body("PROMPT")


def test_no_provider_adapter_emits_a_bare_reasoning_string():
    """The property the 2026-09-04 refusal makes load-bearing.

    An adapter may carry the value under any key it likes, and may nest an
    object under `reasoning` -- the probe accepted
    `{"reasoning": {"effort": "none"}}` as well. What no adapter may do is
    put a STRING directly under `reasoning`, which is the exact shape the
    provider rejects with a 400 before generating anything.
    """

    offenders = []
    for provider in sorted(REASONING_ADAPTERS):
        for value in NEUTRAL_VALUES:
            emitted = reasoning_body(provider, value)
            carried = emitted.get(REFUSED_AS_STRING)
            if isinstance(carried, str):
                offenders.append((provider, value, emitted))
    assert offenders == [], (
        "a provider adapter now sends a bare `reasoning` string, which "
        "Ollama Cloud refuses with HTTP 400 "
        "(json: cannot unmarshal string into Go struct field "
        f"ChatCompletionRequest.reasoning of type openai.Reasoning): {offenders}"
    )


def test_each_provider_carries_the_value_in_its_own_field():
    """The exact emitted dict per provider, for the whole vocabulary.

    Every shape asserted here returned HTTP 200 live on 2026-09-04 for the
    ollama rows; the deepseek and openai rows are the committed mapping,
    unchanged by this tranche and not probed (no committed provider
    profile names either endpoint).
    """

    assert reasoning_body("ollama", None) == {}
    assert reasoning_body("ollama", "none") == {"reasoning_effort": "none"}
    assert reasoning_body("ollama", "low") == {"reasoning_effort": "low"}
    assert reasoning_body("ollama", "max") == {"reasoning_effort": "max"}
    assert reasoning_body("ollama", 512) == {"reasoning_effort": "low"}
    assert reasoning_body("ollama", 5000) == {"reasoning_effort": "high"}

    assert reasoning_body("openai", None) == {}
    assert reasoning_body("openai", "none") == {"reasoning_effort": "minimal"}

    assert reasoning_body("deepseek", None) == {}
    assert reasoning_body("deepseek", "none") == {"thinking": {"type": "disabled"}}
    assert reasoning_body("deepseek", 512) == {
        "thinking": {"type": "enabled", "budget_tokens": 512}
    }

    # A provider with no adapter cannot carry any reasoning field at all.
    assert reasoning_body("generic", "none") == {}
    assert reasoning_body("a-provider-nobody-has-written-yet", "none") == {}


def test_the_committed_launch_config_builds_an_accepted_body():
    """End to end on the route the alarm named, through build_body itself.

    This is the assertion that inverts if the harness ever starts sending
    what P2 believed it was already sending.
    """

    body = _body_for(_launch_critic_route())

    assert body["reasoning_effort"] == "none"
    assert REFUSED_AS_STRING not in body, (
        f"the launch config's critic seat now puts {body.get(REFUSED_AS_STRING)!r} "
        f"under {REFUSED_AS_STRING!r}, the shape the provider refuses"
    )
    assert body["model"] == "qwen3.5:397b"
    assert body["response_format"] == {"type": "json_object"}
