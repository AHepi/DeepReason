"""Provider plugs — the model-change seam.

The harness speaks ONE neutral dialect of knobs; each provider entry here
maps them onto that provider's wire format. Changing models or providers
later is a config edit (role table: endpoint/model/provider/reasoning),
never a call-site change. Unknown providers degrade to no-op mappings, so
a new endpoint works immediately and gains its quirks by adding one entry.

Neutral reasoning knob (docs/TOKEN_ECONOMY.md angle 1 — the dominant cost
lever, epistemically free by D2):
    None            -> provider default (knob omitted from the body)
    "none"          -> disable reasoning entirely
    "low|medium|high|max" -> effort level (provider maps to its own scale)
    int             -> reasoning budget in tokens

DEFERRED (research-gated, per docs/TOKEN_ECONOMY.md): a deployable
harness-side caching layer (beyond provider prefix caches) — the seam for
it is this module plus the adapter; do not build until its effectiveness
is researched.
"""


def _deepseek_reasoning(value) -> dict:
    # DeepSeek V4 thinking control: {"thinking": {"type": "disabled"}} to
    # switch off; enabled with budget_tokens or an effort hint otherwise.
    if value is None:
        return {}
    if value == "none":
        return {"thinking": {"type": "disabled"}}
    if isinstance(value, int):
        return {"thinking": {"type": "enabled", "budget_tokens": value}}
    # Preserve the ordinal cost lever: low stays cheap, max is the top tier.
    # (An earlier table collapsed low/medium up to "high", silently sending
    # maximum-cost reasoning for the cheapest configured settings.)
    effort = {"low": "low", "medium": "medium", "high": "high", "max": "xhigh"}.get(
        str(value), str(value)
    )
    return {"thinking": {"type": "enabled", "effort": effort}}


def _openai_reasoning(value) -> dict:
    if value is None:
        return {}
    if isinstance(value, int):  # OpenAI takes effort levels, not budgets
        value = "low" if value <= 2000 else "high"
    effort = {"none": "minimal", "max": "high"}.get(str(value), str(value))
    return {"reasoning_effort": effort}


def _ollama_reasoning(value) -> dict:
    # Ollama's OpenAI-compatible surface takes reasoning_effort with the SAME
    # vocabulary as the neutral knob (none/low/medium/high/max), so pass it
    # straight through. This is what makes `reasoning: none` actually disable
    # thinking on Ollama (the dominant cost lever) instead of being silently
    # dropped by the generic no-op. An int budget collapses to a coarse effort.
    if value is None:
        return {}
    if isinstance(value, int):
        value = "low" if value <= 2000 else "high"
    return {"reasoning_effort": str(value)}


def _no_reasoning_knob(value) -> dict:
    return {}


REASONING_ADAPTERS = {
    "deepseek": _deepseek_reasoning,
    "openai": _openai_reasoning,
    "ollama": _ollama_reasoning,
    "generic": _no_reasoning_knob,
}


def infer_provider(base_url: str) -> str:
    url = (base_url or "").lower()
    if "deepseek" in url:
        return "deepseek"
    if "openai" in url:
        return "openai"
    # ollama.com (cloud) — its reasoning_effort takes the neutral vocabulary
    # natively. Local ollama at localhost:11434 has no "ollama" in the host, so
    # it stays generic unless the role sets provider: ollama explicitly.
    if "ollama" in url:
        return "ollama"
    return "generic"


def reasoning_body(provider: str, value) -> dict:
    """Extra request-body fields realizing the neutral reasoning knob."""
    return REASONING_ADAPTERS.get(provider, _no_reasoning_knob)(value)
