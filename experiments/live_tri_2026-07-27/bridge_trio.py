"""Live bridge trio against one completed engaged run.

Usage: bridge_trio.py <deepreason_home> <run_id> <problem_id>

Drives the installed deepreason-mcp stdio server: start_bridge with the
run's own problem id (free text is rejected by design), polls
bridge_status to a terminal state, then reads bridge_result and
bridge_claims.  Exit 0 only if the bridge completes with a resolution.
"""

import json
import os
import subprocess
import sys
import time

HOME, RUN_ID, PROBLEM_ID = sys.argv[1], sys.argv[2], sys.argv[3]

env = dict(os.environ)
env["DEEPREASON_HOME"] = HOME
proc = subprocess.Popen(
    ["deepreason-mcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env,
    bufsize=1,
)
_next = iter(range(1, 10_000))
results = []


def rpc(method, params=None, timeout=900):
    ident = next(_next)
    msg = {"jsonrpc": "2.0", "id": ident, "method": method}
    if params is not None:
        msg["params"] = params
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("server closed stdout")
        reply = json.loads(line)
        if reply.get("id") == ident:
            return reply
    raise TimeoutError(method)


def call(tool, arguments, *, label=None, timeout=900):
    label = label or tool
    reply = rpc("tools/call", {"name": tool, "arguments": arguments}, timeout=timeout)
    result = reply.get("result", {})
    text = "".join(i.get("text", "") for i in result.get("content", ()))
    if reply.get("error") or result.get("isError"):
        results.append((label, False, text[:300]))
        return None
    try:
        payload = json.loads(text)
    except ValueError:
        payload = text
    results.append((label, True, "ok"))
    return payload


rpc(
    "initialize",
    {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "bridge-trio", "version": "0"},
    },
)
proc.stdin.write(
    json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
)
proc.stdin.flush()
tools = {t["name"]: t for t in rpc("tools/list")["result"]["tools"]}

sb_schema = tools["start_bridge"]["inputSchema"]
sb_args = {"run_id": RUN_ID}
for key in sb_schema.get("required", []):
    if key in sb_args:
        continue
    spec = sb_schema["properties"].get(key, {})
    if "enum" in spec:
        sb_args[key] = spec["enum"][0]
    elif spec.get("type") == "string":
        sb_args[key] = PROBLEM_ID
print("start_bridge args:", json.dumps(sb_args), file=sys.stderr)
started = call("start_bridge", sb_args, label="start_bridge", timeout=900)

terminal = None
last = None
if isinstance(started, dict):
    print("started:", json.dumps(started)[:300], file=sys.stderr)
    status_required = tools["bridge_status"]["inputSchema"].get("required", ["run_id"])
    args = {}
    for key in status_required:
        args[key] = started.get(key) or started.get("bridge_id") or RUN_ID
    for _ in range(360):
        reply = rpc("tools/call", {"name": "bridge_status", "arguments": args})
        text = "".join(
            i.get("text", "") for i in reply.get("result", {}).get("content", ())
        )
        if reply.get("result", {}).get("isError"):
            results.append(("bridge_status(poll)", False, text[:300]))
            break
        last = json.loads(text)
        state = last.get("state") or last.get("lifecycle")
        if state in {"completed", "failed", "cancelled", "resolved"}:
            terminal = state
            break
        time.sleep(10)
    results.append(
        (
            "bridge_status(terminal)",
            terminal == "completed",
            f"state={terminal} detail={json.dumps(last)[:200] if last else ''}",
        )
    )
    bridge_result = call("bridge_result", args, label="bridge_result")
    if isinstance(bridge_result, dict):
        print("bridge_result:", json.dumps(bridge_result)[:1200], file=sys.stderr)
        resolution = bridge_result.get("resolution") or bridge_result.get("state")
        results.append(
            (
                "bridge_result has resolution",
                resolution is not None,
                f"resolution={resolution}",
            )
        )
    claims = call("bridge_claims", args, label="bridge_claims")
    if isinstance(claims, dict):
        print("claims head:", json.dumps(claims)[:800], file=sys.stderr)

proc.stdin.close()
proc.wait(timeout=60)
print("\n=== BRIDGE TRIO RESULTS ===")
fails = 0
for label, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {label}  | {detail}")
    fails += 0 if ok else 1
print(f"=== {len(results) - fails}/{len(results)} passed ===")
sys.exit(1 if fails else 0)
