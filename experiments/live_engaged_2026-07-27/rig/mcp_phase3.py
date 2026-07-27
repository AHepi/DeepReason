"""Phase 3: live bridge trio + scratch open/related against a fresh
bridge-enabled run. Argument: run_id of the fresh run."""

import json
import os
import subprocess
import sys
import time

LIVE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(LIVE, "venv", "bin", "deepreason-mcp")
HOME = os.path.join(LIVE, "r6-large")
RUN_ID = sys.argv[1]

env = dict(os.environ)
env["DEEPREASON_HOME"] = HOME
proc = subprocess.Popen([SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, text=True, env=env, bufsize=1)
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
        results.append((label, False, text[:170]))
        return None
    try:
        payload = json.loads(text)
    except ValueError:
        payload = text
    results.append((label, True, "ok"))
    return payload


rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "phase3", "version": "0"}})
proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
proc.stdin.flush()
tools = {t["name"]: t for t in rpc("tools/list")["result"]["tools"]}

# Scratch: map should now expose openable unclustered refs.
scratch = call("scratch_map", {"run_id": RUN_ID})
refs = []
if isinstance(scratch, dict):
    refs = list(scratch.get("unclustered_block_ids") or [])
    for cluster in scratch.get("clusters") or []:
        refs.extend(cluster.get("member_ids") or [])
results.append(("scratch_map exposes refs", bool(refs), f"{len(refs)} refs"))
if refs:
    open_props = tools["scratch_open"]["inputSchema"]["properties"]
    ref_key = "block" if "block" in open_props else next(k for k in open_props if k != "run_id")
    opened = call("scratch_open", {"run_id": RUN_ID, ref_key: refs[0]})
    rel_props = tools["scratch_related"]["inputSchema"]["properties"]
    rel_key = "block" if "block" in rel_props else next(k for k in rel_props if k != "run_id")
    call("scratch_related", {"run_id": RUN_ID, rel_key: refs[0]})

# Bridge trio.
sb_schema = tools["start_bridge"]["inputSchema"]
sb_args = {"run_id": RUN_ID}
for key in sb_schema.get("required", []):
    if key in sb_args:
        continue
    spec = sb_schema["properties"].get(key, {})
    if "enum" in spec:
        sb_args[key] = spec["enum"][0]
    elif spec.get("type") == "string":
        sb_args[key] = (
            "What is the minimum durable evidence a harness must bind to a "
            "published result to make post-crash divergence detectable?"
        )
print("start_bridge args:", sorted(sb_args), file=sys.stderr)
started = call("start_bridge", sb_args, label="start_bridge", timeout=900)
if isinstance(started, dict):
    print("started:", json.dumps(started)[:300], file=sys.stderr)
    status_required = tools["bridge_status"]["inputSchema"].get("required", ["run_id"])
    args = {}
    for key in status_required:
        args[key] = started.get(key) or started.get("bridge_id") or RUN_ID
    terminal = None
    last = None
    for _ in range(120):
        reply = rpc("tools/call", {"name": "bridge_status", "arguments": args})
        text = "".join(i.get("text", "") for i in reply.get("result", {}).get("content", ()))
        if reply.get("result", {}).get("isError"):
            results.append(("bridge_status(poll)", False, text[:170]))
            break
        last = json.loads(text)
        state = last.get("state") or last.get("lifecycle")
        if state in {"completed", "failed", "cancelled", "resolved"}:
            terminal = state
            break
        time.sleep(10)
    results.append(("bridge_status(terminal)", terminal == "completed",
                    f"state={terminal} detail={json.dumps(last)[:120] if last else ''}"))
    bridge_result = call("bridge_result", args, label="bridge_result")
    if isinstance(bridge_result, dict):
        print("bridge_result head:", json.dumps(bridge_result)[:800], file=sys.stderr)
        resolution = bridge_result.get("resolution") or bridge_result.get("state")
        results.append(("bridge_result has resolution", resolution is not None,
                        f"resolution={resolution}"))
    claims = call("bridge_claims", args, label="bridge_claims")
    if isinstance(claims, dict):
        print("claims head:", json.dumps(claims)[:800], file=sys.stderr)

proc.stdin.close()
proc.wait(timeout=60)
print("\n=== PHASE 3 RESULTS ===")
fails = 0
for label, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {label}  | {detail}")
    fails += 0 if ok else 1
print(f"=== {len(results) - fails}/{len(results)} passed ===")
sys.exit(1 if fails else 0)
