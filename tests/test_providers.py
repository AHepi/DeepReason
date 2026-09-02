"""Provider plugs: the neutral reasoning knob maps to each provider's wire
format; unknown providers no-op; the config role table drives everything."""

from deepreason.llm.adapter import _endpoint_from_spec
from deepreason.llm.endpoints import OpenAICompatEndpoint
from deepreason.llm.providers import infer_provider, reasoning_body


def test_infer_provider():
    assert infer_provider("https://api.deepseek.com") == "deepseek"
    assert infer_provider("https://api.openai.com/v1") == "openai"
    assert infer_provider("https://ollama.com/v1") == "ollama"  # cloud
    assert infer_provider("http://localhost:11434/v1") == "generic"  # local host, no "ollama"


def test_ollama_reasoning_passthrough():
    # Ollama's reasoning_effort takes the neutral vocabulary natively, so
    # `none` actually disables thinking (unlike the openai mapping -> minimal).
    assert reasoning_body("ollama", None) == {}
    assert reasoning_body("ollama", "none") == {"reasoning_effort": "none"}
    assert reasoning_body("ollama", "medium") == {"reasoning_effort": "medium"}
    assert reasoning_body("ollama", "max") == {"reasoning_effort": "max"}
    assert reasoning_body("ollama", 1500) == {"reasoning_effort": "low"}
    assert reasoning_body("ollama", 5000) == {"reasoning_effort": "high"}


def test_ollama_endpoint_maps_reasoning_none_to_disabled_effort():
    ep = OpenAICompatEndpoint(
        "https://ollama.com/v1", "gpt-oss:120b", json_mode=True, reasoning="none",
    )
    assert ep.provider == "ollama"
    assert ep.build_body("PROMPT")["reasoning_effort"] == "none"


def test_deepseek_reasoning_mapping():
    assert reasoning_body("deepseek", None) == {}
    assert reasoning_body("deepseek", "none") == {"thinking": {"type": "disabled"}}
    assert reasoning_body("deepseek", 2000) == {
        "thinking": {"type": "enabled", "budget_tokens": 2000}
    }
    assert reasoning_body("deepseek", "max") == {
        "thinking": {"type": "enabled", "effort": "xhigh"}
    }


def test_openai_reasoning_mapping_and_unknown_provider():
    assert reasoning_body("openai", "none") == {"reasoning_effort": "minimal"}
    assert reasoning_body("openai", 1500) == {"reasoning_effort": "low"}
    assert reasoning_body("something-else", "none") == {}  # safe no-op


def test_endpoint_body_carries_reasoning():
    ep = OpenAICompatEndpoint(
        "https://api.deepseek.com", "deepseek-v4-pro",
        json_mode=True, reasoning="none",
    )
    body = ep.build_body("PROMPT")
    assert body["thinking"] == {"type": "disabled"}
    assert body["response_format"] == {"type": "json_object"}
    # Provider default: knob omitted entirely.
    ep2 = OpenAICompatEndpoint("https://api.deepseek.com", "deepseek-v4-pro")
    assert "thinking" not in ep2.build_body("PROMPT")


def test_role_table_is_the_model_change_plug():
    spec = {
        "endpoint": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
        "temperature": 0.7,
        "reasoning": "none",
        "max_tokens": 1400,
        "json_mode": True,
        "logprobs": True,
    }
    ep = _endpoint_from_spec(spec)
    assert ep.model == "deepseek-v4-flash"
    assert ep.provider == "deepseek"
    assert ep.reasoning == "none"
    assert ep.max_tokens == 1400
    assert ep.json_mode is True and ep.request_logprobs is True


def test_endpoint_family_defaults_to_lease_inference():
    """A config without an explicit family key must produce an endpoint whose
    family matches what route_from_endpoint infers, so the route firewall
    cannot fail closed on the first call (bronze flat run finding F2)."""
    from deepreason.llm.firewall import route_from_endpoint

    spec = {
        "endpoint": "https://ollama.com/v1",
        "model": "deepseek-v4-pro",
        "provider": "ollama",
        "temperature": 0.0,
        "json_mode": True,
    }
    ep = _endpoint_from_spec(spec)
    assert ep.family == "deepseek"
    route = route_from_endpoint(ep)
    assert route.family == ep.family
    # explicit override still wins
    ep2 = _endpoint_from_spec({**spec, "family": "custom"})
    assert ep2.family == "custom"


def test_knob_availability_is_a_provider_fact_and_stays_here():
    """What the WIRE can carry is decided by the adapter table, not by probing.

    This is the half of the old `thinking_off` rule that is genuinely about
    providers. The other half -- what a value MEANS on a given model -- moved
    to that model's own document on 2026-09-01; see the test below.
    """

    from deepreason.llm.providers import reasoning_knob_available

    assert reasoning_knob_available("ollama")
    assert reasoning_knob_available("openai")
    assert reasoning_knob_available("deepseek")
    assert not reasoning_knob_available("generic")
    assert not reasoning_knob_available("some-unlisted-provider")

    # The neutral off token reaches the wire as each provider's own most-off
    # spelling. What the MODEL then does with it is not this table's claim.
    assert reasoning_body("ollama", "none") == {"reasoning_effort": "none"}
    assert reasoning_body("openai", "none") == {"reasoning_effort": "minimal"}
    assert reasoning_body("generic", "none") == {}


def test_what_off_means_is_a_model_fact_and_lives_in_the_model_document():
    """Regression (coin canonicity run-c5f901f3): the live profile carried
    reasoning=None, which sends no reasoning field, and glm-5.2 thought by
    default — the first conjecture turn returned completion_tokens exactly
    equal to the 24576 cap and produced no candidate. Unset is not off.

    That claim is unchanged and is asserted below. What changed on 2026-09-01
    is WHERE it is decided. `providers.reasoning_disabled` used to answer it
    from a constant, for every model at once, and it was wrong about glm-5.3:
    `none` there does not stop the thinking, it stops the SEPARATION (0/8
    clean content against 8/8 at `low`). Two models, two answers, one
    question — so the question belongs to each model's own document.
    """

    from deepreason import model_profiles
    from deepreason.llm.split import (
        NOTICE_NOT_A_REASONING_SEAT,
        plan_split,
    )

    def _document(model_id, disabling):
        return model_profiles.parse_document(
            "```" + model_profiles.FENCE_INFO + f"""
schema: deepreason-model-profile.v1
model_id: {model_id}
measured_on: 2026-08-31
reasoning:
  documented_values: [none, low, high, max]
  extraction_value: low
  thinking_disablable: {"true" if disabling else "false"}
  disabling_values: {disabling}
  trace_destination: {{low: side_channel}}
```
"""
        )

    # glm-5.2: `none` really does disable thinking (P-S1, 5/5 clean content
    # with no reasoning field). The seat is out of scope for the split.
    glm_52 = _document("glm-5.2", "[none]")
    off = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="none", profile=glm_52,
    )
    assert not off.armed and off.notice == NOTICE_NOT_A_REASONING_SEAT

    # Unset is STILL not off, on either model: no reasoning field is sent and
    # a reasoning model thinks by default.
    unset = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning=None, profile=glm_52,
    )
    assert unset.armed

    # glm-5.3: the SAME configured value, a different measured answer. Nothing
    # a per-provider table could have known.
    glm_53 = _document("glm-5.3", "[]")
    still_thinking = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="none", profile=glm_53,
    )
    assert still_thinking.armed

    # An int budget is a budget, never a disable — on any model.
    for budget in (0, 2000):
        assert plan_split(
            mode="auto", ceiling=4096, extraction_tokens=512,
            provider="ollama", reasoning=budget, profile=glm_52,
        ).armed
