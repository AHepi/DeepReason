"""The one request field mini's transport does not forward: `reasoning`.

PREREG_D8.md §0 records the finding (PARKED P10): `HttpEndpoint.complete`
builds its body from model, messages, temperature, max_tokens and
response_format, and the managed shallow entry never passes the profile's
`reasoning` setting through. Without `reasoning: none` this model spends the
completion cap on hidden reasoning and returns empty content. This subclass
adds exactly that field and changes nothing else; it is experiment scope,
not production code, and ARM M is disclosed as having run through it.
"""

from __future__ import annotations

import json
import urllib.request

from minireason.call import HttpEndpoint

REASONING = {"effort": "none"}


class ReasoningOffEndpoint(HttpEndpoint):
    def complete(self, prompt: str) -> str:
        original = urllib.request.Request

        def request_with_reasoning(url, data=None, headers=None, **kw):
            body = json.loads(data.decode()) if data else {}
            body["reasoning"] = REASONING
            return original(url, data=json.dumps(body).encode(), headers=headers or {}, **kw)

        urllib.request.Request = request_with_reasoning  # type: ignore[assignment]
        try:
            return super().complete(prompt)
        finally:
            urllib.request.Request = original  # type: ignore[assignment]


def endpoint_from_profile(profile, key: str) -> ReasoningOffEndpoint:
    """Mirror `deepreason.shallow._endpoint` field for field, plus the one."""
    return ReasoningOffEndpoint(
        profile.endpoint,
        profile.model_id,
        api_key=key,
        max_tokens=profile.maximum_completion_tokens,
    )
