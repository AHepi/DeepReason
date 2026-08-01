"""The brokered worker: the contained worker plus exactly one injected name.

`contained.py` is deliberately not edited. Its worker source and digest are the
recorded runtime identity of every existing run, and a brokered run should be a
DIFFERENT worker with a different digest rather than a quiet mutation of the
one already in the record. So V2 is derived here, from V1, by two explicit
substitutions that fail loudly if the source they target ever moves.

What is NOT relaxed, because it is the actual containment:

* the AST guard still refuses any `import` or private-attribute traversal in
  model-authored source;
* the builtins allowlist still omits `open`, `__import__`, `eval` and `exec`;
* the worker still executes inside an unshared NETWORK namespace.

Measured, not assumed — see `tests/test_brokered_simulation.py`: model code
attempting `import socket` is refused at parse, and `open` and `__import__` are
undefined names at runtime.

What IS added is one callable, `llm`, in the program's namespace. Its only
power is to ask a bounded broker for a completion. The broker holds the
credential, pins the destination host and model, and caps the call count
(`deepreason.verification.llm_broker`). The transport is a Unix domain socket,
which is a filesystem object rather than a network one, so it crosses the
unshared network namespace untouched and no exception is carved into `--net`.

The program therefore gains exactly one verb and no general socket.
"""

from __future__ import annotations

from deepreason.canonical import sha256_hex
from deepreason.verification.contained import CONTAINED_WORKER_SOURCE_V1

_BROKER_BRIDGE = '''

def _broker_call(socket_path, request, budget):
    """One framed request to the broker. Refusals come back as data, not raises."""
    if budget[0] <= 0:
        return {"error": "the program exhausted its authorized provider calls"}
    budget[0] -= 1
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(180)
    chunks = []
    try:
        connection.connect(socket_path)
        connection.sendall(json.dumps(request).encode("utf-8") + b"\\n")
        while not b"".join(chunks).endswith(b"\\n"):
            chunk = connection.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
    except Exception as error:
        return {"error": "broker unreachable: " + type(error).__name__}
    finally:
        connection.close()
    try:
        reply = json.loads(b"".join(chunks).decode("utf-8"))
    except Exception:
        return {"error": "broker reply was not JSON"}
    if "ok" in reply:
        return reply["ok"]
    return {"error": reply.get("error", "broker refused")}


def make_llm(socket_path, model, budget):
    def llm(prompt, system=None, temperature=None, top_p=None, seed=None,
            max_tokens=None):
        """Ask the brokered model once.

        Returns {"text": ...} on success or {"error": ...} on refusal. Every
        bound is enforced broker-side, so a program that ignores an error and
        loops is simply refused rather than trusted to stop.
        """
        request = {"prompt": prompt, "model": model}
        if system is not None:
            request["system"] = system
        for name, value in (("temperature", temperature), ("top_p", top_p),
                            ("seed", seed), ("max_tokens", max_tokens)):
            if value is not None:
                request[name] = value
        return _broker_call(socket_path, request, budget)

    return llm

'''

_IMPORT_ANCHOR = "import ast\nimport builtins"
_LOAD_ANCHOR = (
    '        simulation, error = load_function(\n'
    '            job["source"], job["entry"], "simulation", {"math": math}\n'
    '        )'
)
_LOAD_REPLACEMENT = (
    '        extras = {"math": math}\n'
    '        if job.get("llm_socket"):\n'
    '            extras["llm"] = make_llm(\n'
    '                job["llm_socket"],\n'
    '                job.get("llm_model"),\n'
    '                [int(job.get("llm_call_budget", 0))],\n'
    '            )\n'
    '        simulation, error = load_function(\n'
    '            job["source"], job["entry"], "simulation", extras\n'
    '        )'
)


def _derive_v2(source: str) -> str:
    """Build the brokered worker, refusing to guess if V1 has moved."""

    if source.count(_IMPORT_ANCHOR) != 1:
        raise RuntimeError("brokered worker: V1 import anchor is not unique")
    if source.count(_LOAD_ANCHOR) != 1:
        raise RuntimeError("brokered worker: V1 simulation-load anchor is not unique")
    if source.count("def run(job):") != 1:
        raise RuntimeError("brokered worker: V1 run() anchor is not unique")
    derived = source.replace(
        _IMPORT_ANCHOR, _IMPORT_ANCHOR + "\nimport socket", 1
    )
    derived = derived.replace(_LOAD_ANCHOR, _LOAD_REPLACEMENT, 1)
    return derived.replace("def run(job):", _BROKER_BRIDGE + "\ndef run(job):", 1)


BROKERED_WORKER_SOURCE_V2 = _derive_v2(CONTAINED_WORKER_SOURCE_V1)
BROKERED_WORKER_SHA256_V2 = sha256_hex(BROKERED_WORKER_SOURCE_V2.encode("utf-8"))

__all__ = ["BROKERED_WORKER_SHA256_V2", "BROKERED_WORKER_SOURCE_V2"]
