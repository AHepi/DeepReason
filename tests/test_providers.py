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
