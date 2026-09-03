"""Phase 0 transport-wall probe. Design frozen in PREREG.md; do not edit.

Wire shape is the harness's own (llm/endpoints.py:420-427 + build_body): urllib,
POST https://ollama.com/v1/chat/completions, Content-Type + Authorization and
nothing else, one user message, no system message, no top_p, no temperature, no
reasoning_effort. Client timeout is 1800 s on every arm so a death at ~300 s is
provably not ours.

Writes one JSON file per call under raw/ BEFORE the next call starts, so a
container rollback loses at most one measurement. Never prints or records the
key.
"""

import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

URL = "https://ollama.com/v1/chat/completions"
RAW = Path(__file__).resolve().parent / "raw"
GLM = "glm-5.3"
DEEPSEEK = "deepseek-v4-pro:0813"

PROMPT = (
    "Write a complete, self-contained technical monograph on the history and "
    "mechanics of error-correcting codes, from Hamming through Reed-Solomon to "
    "modern LDPC and polar codes. Include worked numerical examples, full "
    "derivations, and a chapter on decoding complexity. Do not summarise; "
    "write the full text."
)

ARMS = [
    ("A1", GLM, 16384, False), ("A2", GLM, 24576, False),
    ("A3", GLM, 32768, False), ("A4", GLM, 49152, False),
    ("B1", GLM, 16384, True), ("B2", GLM, 24576, True),
    ("B3", GLM, 32768, True), ("B4", GLM, 49152, True),
    ("C1", DEEPSEEK, 49152, False), ("C2", DEEPSEEK, 49152, True),
    ("D1", GLM, 49152, False), ("D2", GLM, 49152, True),
    ("E1", DEEPSEEK, 49152, False), ("E2", DEEPSEEK, 49152, True),
    ("F1", GLM, 2048, False), ("F2", GLM, 2048, True),
    ("G1", GLM, 49152, False), ("G2", GLM, 49152, True),
    # PREREG Amendment 1: does the endpoint honour stream_options.include_usage?
    ("H1", GLM, 2048, "usage"),
]

_write_lock = threading.Lock()


def proxy_relay_failures() -> object:
    """The ONLY thing that separates a container-proxy abort from an
    Ollama-edge close: the container's own README says a tunnel abort reaches
    the client as a bare reset, indistinguishable from the remote's."""
    proxy = os.environ.get("HTTPS_PROXY", "")
    if not proxy:
        return "no HTTPS_PROXY"
    try:
        out = subprocess.run(
            ["curl", "-sS", f"{proxy}/__agentproxy/status"],
            capture_output=True, text=True, timeout=30,
        ).stdout
        return json.loads(out).get("recentRelayFailures", "absent")
    except Exception as error:  # a probe of the probe must never kill the probe
        return f"unreadable: {type(error).__name__}: {error}"


def run_arm(arm: str, model: str, max_tokens: int, stream: bool) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": max_tokens,
    }
    if stream:
        body["stream"] = True
        if stream == "usage":
            body["stream_options"] = {"include_usage": True}
    request = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + os.environ["OLLAMA_API_KEY"],
        },
    )
    row = {
        "arm": arm, "model": model, "max_tokens": max_tokens, "stream": stream,
        "t_submit": None, "t_headers": None, "t_first_body_byte": None,
        "t_last_byte": None, "elapsed_s": None, "http_status": None,
        "response_headers": None, "bytes_received": 0, "chunks": 0,
        "completion_tokens": None, "finish_reason": None,
        "exception_type": None, "exception_str": None,
        "proxy_recent_relay_failures_after": None,
    }
    started = time.monotonic()
    row["t_submit"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with urllib.request.urlopen(request, timeout=1800) as response:
            row["t_headers"] = round(time.monotonic() - started, 3)
            row["http_status"] = response.status
            row["response_headers"] = {
                k: v for k, v in response.headers.items()
                if k.lower() != "authorization"
            }
            received = bytearray()
            first_body = None
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                if first_body is None:
                    first_body = round(time.monotonic() - started, 3)
                received += chunk
                row["chunks"] += 1
            row["t_first_body_byte"] = first_body
            row["bytes_received"] = len(received)
            row["t_last_byte"] = round(time.monotonic() - started, 3)
            row.update(_parse(bytes(received), bool(stream)))
            if arm.startswith("H"):
                # Amendment 1 also needs GROUND TRUTH for the reassembly
                # design: the exact SSE framing, so a reader can be shown to
                # rebuild the non-streaming dict shape byte-for-byte rather
                # than by assumption. Same call, extra recording.
                (RAW / f"{arm}.sse").write_bytes(bytes(received))
    except Exception as error:
        row["exception_type"] = type(error).__name__
        row["exception_str"] = str(error)[:500]
        row["proxy_recent_relay_failures_after"] = proxy_relay_failures()
    row["elapsed_s"] = round(time.monotonic() - started, 3)
    with _write_lock:
        (RAW / f"{arm}.json").write_text(json.dumps(row, indent=2, sort_keys=True))
    print(
        f"{arm} {model} cap={max_tokens} stream={stream} "
        f"elapsed={row['elapsed_s']}s status={row['http_status']} "
        f"tokens={row['completion_tokens']} "
        f"exc={row['exception_type']}",
        flush=True,
    )
    return row


def _parse(payload: bytes, stream: bool) -> dict:
    """Pull completion_tokens / finish_reason out of either framing.

    OLLAMA_CLOUD_OPERATIONS.md §2: a stream can return 200, emit partial
    tokens, then fail with an `error` object mid-body. Record that rather than
    reading a 200 as success.
    """
    out: dict = {}
    try:
        if not stream:
            data = json.loads(payload)
            out["finish_reason"] = data["choices"][0].get("finish_reason")
            out["completion_tokens"] = (data.get("usage") or {}).get(
                "completion_tokens"
            )
            if "error" in data:
                out["stream_error"] = str(data["error"])[:300]
            return out
        terminal = False
        for line in payload.split(b"\n"):
            line = line.strip()
            if not line:
                continue
            if line == b"data: [DONE]":
                terminal = True
                continue
            if line.startswith(b"data: "):
                line = line[6:]
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if "error" in event:
                out["stream_error"] = str(event["error"])[:300]
            usage = event.get("usage") or {}
            if usage.get("completion_tokens") is not None:
                out["completion_tokens"] = usage["completion_tokens"]
            for choice in event.get("choices") or ():
                if choice.get("finish_reason"):
                    out["finish_reason"] = choice["finish_reason"]
        out["stream_terminated"] = terminal
    except Exception as error:
        out["parse_error"] = f"{type(error).__name__}: {error}"
    return out


def main() -> int:
    if not os.environ.get("OLLAMA_API_KEY"):
        print("OLLAMA_API_KEY not set; refusing to run", file=sys.stderr)
        return 2
    RAW.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    arms = [a for a in ARMS if not only or a[0] in only]
    # Ollama Pro per-account concurrency is 3 (OLLAMA_CLOUD_OPERATIONS.md §1);
    # exceeding it contaminates latency with queue wait, which §4.5 says is not
    # separable from generation latency without first-token timestamps.
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda a: run_arm(*a), arms))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
