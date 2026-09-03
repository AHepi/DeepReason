"""The one guarded live check: the SHIPPED client through the real wall.

The probe measured the wall with its own script. This drives
`OpenAICompatEndpoint.complete` — the code that actually ships — at a cap the
probe proved cannot finish inside the wall, with the policy at its shipped
default. Expected: the first attempt is non-streaming and dies at ~300 s, the
policy retries as a stream, and the call returns content.

One call. Judged on typed outcomes only.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402
from deepreason.llm.transport_policy import TransportSettings  # noqa: E402

PROMPT = (
    "Write a complete, self-contained technical monograph on the history and "
    "mechanics of error-correcting codes, from Hamming through Reed-Solomon to "
    "modern LDPC and polar codes. Include worked numerical examples, full "
    "derivations, and a chapter on decoding complexity. Do not summarise; "
    "write the full text."
)


def main() -> int:
    if not os.environ.get("OLLAMA_API_KEY"):
        print("OLLAMA_API_KEY not set; refusing to run", file=sys.stderr)
        return 2
    endpoint = OpenAICompatEndpoint(
        "https://ollama.com/v1",
        "glm-5.3",
        api_key=os.environ["OLLAMA_API_KEY"],
        timeout_s=1800,
        max_tokens=49152,
        provider="ollama",
    )
    endpoint.transport_policy = TransportSettings()
    row = {"cap": 49152, "policy": endpoint.transport_policy.policy_id,
           "streaming_mode": endpoint.transport_policy.streaming}
    started = time.monotonic()
    try:
        content = endpoint.complete(PROMPT)
        row["outcome"] = "completed"
        row["content_chars"] = len(content)
    except EndpointError as error:
        row["outcome"] = "EndpointError"
        row["error"] = str(error)[:300]
        row["condition"] = getattr(error, "condition", None)
    row["elapsed_s"] = round(time.monotonic() - started, 3)
    row["transport_attempts"] = endpoint.last_transport_attempts
    row["transport_diagnostics"] = list(endpoint.last_transport_diagnostics)
    row["streamed_attempts"] = endpoint.last_streamed_attempts
    row["zero_byte_returns"] = endpoint.last_zero_byte_returns
    row["fault_kind"] = endpoint.last_fault_kind
    row["usage"] = endpoint.last_usage
    row["finish_reason"] = endpoint.last_finish_reason
    row["reasoning_chars"] = len(endpoint.last_reasoning_trace or "")
    out = os.path.join(os.path.dirname(__file__), "raw", "LIVE.json")
    with open(out, "w") as stream:
        json.dump(row, stream, indent=2, sort_keys=True)
    print(json.dumps(row, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
