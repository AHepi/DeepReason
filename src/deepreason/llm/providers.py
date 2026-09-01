"""Provider plugs — the PROVIDER seam, and deliberately not the model seam.

The harness speaks ONE neutral dialect of knobs; each provider entry here
maps them onto that provider's WIRE FORMAT — which field name, which nesting,
which scale. Unknown providers degrade to no-op mappings, so a new endpoint
works immediately.

**What this module must never know is what a particular MODEL does with a
value.** It once did, and that is the defect this file was rewritten to end:
it carried `REASONING_OFF = "none"` as "the neutral vocabulary's off token"
and `llm/split.py` sent it on every emission leg of every model. On glm-5.3
`reasoning_effort: "none"` does not stop the thinking — it stops the
SEPARATION, so the trace lands in `message.content` ahead of the answer. The
constant was a per-MODEL claim wearing a per-VOCABULARY constant's clothes,
and it killed three runs. Per-model facts now live in a document a human
wrote; see `DR-CON-model-profiles` and `deepreason.model_profiles`.

This module's own docstring used to describe itself as "the model-change
seam" where a model "gains its quirks by adding one entry" — i.e. by a source
edit. That is exactly what the 2026-08-26 modularity law forbids and what the
operator retired on 2026-09-01: "Take this particular task out of the hands of
the machine because we don't really know what future LLMs settings will be?"

Neutral reasoning knob (docs/TOKEN_ECONOMY.md angle 1 — the dominant cost
lever, epistemically free by D2). What each value MEANS on a given model is
that model's document to say, not this table's:
    None            -> knob omitted from the body entirely
    "none"          -> the provider's own most-off token, whatever it does
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
    # straight through rather than dropping it into the generic no-op.
    # Passing it through is ALL this function claims: whether a given value
    # disables thinking on a given model is measured per model and declared in
    # that model's document -- on glm-5.2 `none` returns an empty reasoning
    # payload, on glm-5.3 the same value moves the trace into the content.
    # An int budget collapses to a coarse effort.
    if value is None:
        return {}
    if isinstance(value, int):
        value = "low" if value <= 2000 else "high"
    return {"reasoning_effort": str(value)}


def _no_reasoning_knob(value) -> dict:
    return {}


def reasoning_knob_available(provider: str) -> bool:
    """Whether this provider realizes the neutral reasoning knob at all.

    Availability is decidable here rather than by probing the endpoint: a
    provider whose adapter is the no-op cannot carry ANY reasoning field, so
    there is no value it could be asked to send. This is a transport fact and
    stays here; whether a value it CAN carry has the effect someone wants is a
    model fact and lives in that model's document.
    """

    return REASONING_ADAPTERS.get(provider, _no_reasoning_knob) is not _no_reasoning_knob


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
