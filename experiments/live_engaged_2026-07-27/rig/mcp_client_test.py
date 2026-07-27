"""Exercise the deepreason-mcp stdio surface as a real client.

Read-only + fail-closed probes against an existing qualified home, plus one
live start/cancel lifecycle with a minimal budget. Prints a compact verdict
per tool. Never prints credentials.
"""

import json
import os
import subprocess
import sys
import time

LIVE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.join(LIVE, "r4-large")
SERVER = os.path.join(LIVE, "venv", "bin", "deepreason-mcp")
RUN_ID = sys.argv[1]

env = dict(os.environ)
env["DEEPREASON_HOME"] = HOME

proc = subprocess.Popen(
    [SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    stderr=subprocess.PIPE, text=True, env=env, bufsize=1,
)
_next = iter(range(1, 10_000))
results = []


def rpc(method, params=None, *, expect_error=False, label=None):
    ident = next(_next)
    message = {"jsonrpc": "2.0", "id": ident, "method": method}
    if params is not None:
        message["params"] = params
    proc.stdin.write(json.dumps(message) + "\n")
    proc.stdin.flush()
    deadline = time.time() + 240
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("server closed stdout")
        reply = json.loads(line)
        if reply.get("id") == ident:
            return reply
    raise TimeoutError(method)


def call(tool, arguments, *, label=None, want_error_code=None):
    label = label or tool
    reply = rpc("tools/call", {"name": tool, "arguments": arguments})
    if "error" in reply:
        verdict = f"PROTOCOL_ERROR {json.dumps(reply['error'])[:120]}"
        results.append((label, want_error_code is not None, verdict))
        return None
    result = reply["result"]
    is_error = bool(result.get("isError"))
    text = "".join(
        item.get("text", "") for item in result.get("content", ())
    )
    if want_error_code is not None:
        ok = is_error and want_error_code in text
        results.append((label, ok, text[:140]))
        return text
    payload = None
    if not is_error:
        try:
            payload = json.loads(text)
        except ValueError:
            payload = text
    results.append((label, not is_error, text[:140] if is_error else "ok"))
    return payload


init = rpc("initialize", {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "live-mcp-test", "version": "0"},
})
results.append(("initialize", "result" in init, json.dumps(init.get("result", init))[:100]))
rpc("notifications/initialized") if False else proc.stdin.write(
    json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
)
proc.stdin.flush()

tools_reply = rpc("tools/list")
tools = {t["name"]: t for t in tools_reply["result"]["tools"]}
results.append(("tools/list", len(tools) >= 15, f"{len(tools)} tools: {sorted(tools)[:6]}..."))

caps = call("get_capabilities", {})
topics = []
help_schema = tools.get("get_help_topic", {}).get("inputSchema", {})
topic_enum = help_schema.get("properties", {}).get("topic", {}).get("enum", [])
if topic_enum:
    call("get_help_topic", {"topic": topic_enum[0]}, label=f"get_help_topic({topic_enum[0]})")
req_schema = tools.get("get_request_requirements", {}).get("inputSchema", {})
req_enum = req_schema.get("properties", {}).get("request", {}).get("enum", [])
if req_enum:
    call("get_request_requirements", {"request": req_enum[0]},
         label=f"get_request_requirements({req_enum[0]})")

ready = call("get_readiness", {})
if isinstance(ready, dict):
    results.append(("readiness.ready", ready.get("ready") is True,
                    f"state={ready.get('qualification_state')}"))

status = call("run_status", {"run_id": RUN_ID})
if isinstance(status, dict):
    results.append(("run_status.state", status.get("state") == "completed",
                    f"state={status.get('state')}"))
first = time.time()
result_payload = call("run_result", {"run_id": RUN_ID}, label="run_result(recovery)")
first_elapsed = time.time() - first
if isinstance(result_payload, dict):
    verification = result_payload.get("verification") or {}
    results.append(("run_result.reverified_valid", verification.get("valid") is True,
                    f"valid={verification.get('valid')} in {first_elapsed:.1f}s"))
second = time.time()
call("run_result", {"run_id": RUN_ID}, label="run_result(steady)")
results.append(("run_result.steady_fast", (time.time() - second) < max(10, first_elapsed),
                f"{time.time() - second:.1f}s vs first {first_elapsed:.1f}s"))

call("scratch_map", {"run_id": RUN_ID})
call("scratch_search", {"run_id": RUN_ID, "query": "durable evidence binding"})

# Fail-closed probes.
call("run_status", {"run_id": "../../../etc/passwd"},
     label="run_status(path-shaped id)", want_error_code="MCP_INPUT_INVALID")
call("run_status", {"run_id": "run-" + "0" * 32},
     label="run_status(unknown id)", want_error_code="RUN")
call("run_result", {"run_id": RUN_ID, "extra": True},
     label="run_result(extra key)", want_error_code="MCP_INPUT_INVALID")
call("start_run", {"question": "q", "budget": {"cycles": 99, "token_budget": 10**9}},
     label="start_run(over ceiling)", want_error_code="")
reply = rpc("tools/call", {"name": "no_such_tool", "arguments": {}})
bad = reply.get("error") or (reply.get("result", {}).get("isError") and reply["result"])
results.append(("unknown tool rejected", bool(bad), json.dumps(bad)[:100]))

# Live lifecycle: start with minimal budget, observe, cancel.
started = call("start_run", {
    "question": "What single durable record proves a run was cancelled rather than crashed?",
    "budget": {"cycles": 1, "token_budget": 5000},
}, label="start_run(minimal)")
if isinstance(started, dict) and started.get("run_id"):
    new_id = started["run_id"]
    time.sleep(3)
    live_status = call("run_status", {"run_id": new_id}, label="run_status(live)")
    cancelled = call("cancel_run", {"run_id": new_id}, label="cancel_run")
    time.sleep(5)
    after = call("run_status", {"run_id": new_id}, label="run_status(after cancel)")
    if isinstance(after, dict):
        results.append(("cancel took effect",
                        after.get("state") in {"cancelled", "cancelling", "failed", "completed"},
                        f"state={after.get('state')}"))

proc.stdin.close()
proc.wait(timeout=30)

print("\n=== MCP TOOL TEST RESULTS ===")
failures = 0
for label, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {label}  | {detail}")
    failures += 0 if ok else 1
print(f"=== {len(results) - failures}/{len(results)} passed ===")
sys.exit(1 if failures else 0)
