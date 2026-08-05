"""Reproduction for S1 (GOAL.md, DIAGNOSIS.md).

DIAGNOSIS predicted: the fixture BODY is sound and merely unreachable, so
calling the dead function directly must produce a live listener that answers
the provider protocol. If that holds, the fix is to wire it up, not rewrite it.

Imports the smoke module without running main(), so nothing is built or
installed. No provider call, no network beyond loopback.

Run:  python experiments/2026-08-05-fix-loopback-fixture-daemon/repro.py
"""

import ast
import importlib.util
import json
import pathlib
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
SMOKE = ROOT / "scripts" / "wheel_operational_smoke.py"

# --- 1. the defect, read structurally from the file itself -------------------
tree = ast.parse(SMOKE.read_text())
calls = sum(
    1 for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and getattr(n.func, "id", getattr(n.func, "attr", None)) == "_provider_server"
)
refs = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "_provider_server")
states = sum(
    1 for n in ast.walk(tree)
    if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "ProviderState"
)
print("THE DEFECT, structurally:")
print("  _provider_server call sites : %d" % calls)
print("  _provider_server name refs  : %d" % refs)
print("  ProviderState() constructions: %d" % states)
print("  -> the fixture is defined and unreachable")
print()

# --- 2. the prediction: call it directly and see if it serves ---------------
spec = importlib.util.spec_from_file_location("_smoke_under_test", SMOKE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

state = module.ProviderState()
server, thread = module._provider_server(state)
port = server.server_address[1]
print("THE PREDICTION: call the dead function directly")
print("  server bound on port : %d" % port)
print("  serve_forever thread : alive=%s daemon=%s" % (thread.is_alive(), thread.daemon))

# A realistic request: the fixture requires the loopback credential and an
# advertised output schema, exactly as the product's adapter sends them.
schema = {
    "type": "object",
    "properties": {"candidates": {"type": "array"}},
    "required": ["candidates"],
    "additionalProperties": False,
}
payload = json.dumps({
    "model": "deepreason-loopback-v6",
    "max_tokens": 64,
    "response_format": {"type": "json_schema", "json_schema": {"name": "t", "schema": schema}},
    "messages": [{"role": "user", "content": "Qualification case 1: respond."}],
}).encode()
request = urllib.request.Request(
    "http://127.0.0.1:%d/v1/chat/completions" % port,
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + module.TEST_CREDENTIAL,
    },
)
try:
    with urllib.request.urlopen(request, timeout=10) as response:
        status = response.status
        body = json.loads(response.read().decode())
    served = True
except urllib.error.URLError as error:
    status, body, served = None, {"error": str(error)}, False

print("  POST /v1/chat/completions -> status=%s" % status)
if served:
    choice = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    print("     completion present : %s (%d chars)" % (bool(choice), len(choice or "")))
    print("     recorded by fixture: total_calls=%d qualification_calls=%d"
          % (state.total_calls, state.qualification_calls))
print()
print("VERDICT: fixture body %s" % ("SOUND -- only the wiring is missing"
                                    if served else "ALSO BROKEN -- see error above"))
server.shutdown()
server.server_close()
