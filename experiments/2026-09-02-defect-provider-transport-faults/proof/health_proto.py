"""Prototype of the per-seat provider-health derivation, run against the two
real records before it becomes production code."""
import json, sys, collections

KINDS = {
    "RemoteDisconnected": "zero_byte_close",
    "IncompleteRead": "mid_body_drop",
    "TimeoutError": "read_timeout",
    "URLError": "connect_failure",
    "ConnectionResetError": "connect_failure",
    "HTTPError": "http_status",
    "_TransientBody": "malformed_body",
}

def classify(diagnostic: str) -> str:
    return KINDS.get(diagnostic.split(":", 1)[0], "other")

def derive(path):
    seats = {}
    for line in open(path):
        e = json.loads(line)
        llm = e.get("llm")
        if not llm:
            continue
        for a in llm.get("attempt_trace") or []:
            key = "%s#%s" % (llm["role"], a.get("seat", 0))
            s = seats.setdefault(key, dict(
                endpoint_id=a.get("endpoint_id", ""), model=llm.get("model", ""),
                calls=0, attempts=0, faults=0, zero_byte_returns=0,
                last_fault_kind=None, consecutive_zero_byte=0, max_streak=0,
                fault_ms=0, ok_ms=0))
            s["calls"] += 1
            s["attempts"] += int(a.get("transport_attempts") or 1)
            diags = a.get("transport_diagnostics") or []
            if diags:
                s["faults"] += 1
                s["fault_ms"] += int(a.get("ms") or 0)
                kinds = [classify(d) for d in diags]
                s["last_fault_kind"] = kinds[-1]
                if not a.get("tokens"):
                    s["zero_byte_returns"] += 1
                    s["consecutive_zero_byte"] += 1
                    s["max_streak"] = max(s["max_streak"], s["consecutive_zero_byte"])
                else:
                    s["consecutive_zero_byte"] = 0
            else:
                s["consecutive_zero_byte"] = 0
                s["ok_ms"] += int(a.get("ms") or 0)
    return seats

for path in sys.argv[1:]:
    print("==", path.split("/")[-2])
    for k, v in sorted(derive(path).items()):
        print("  %-28s calls=%-4d attempts=%-4d faults=%-3d zero_byte=%-3d streak=%-3d last=%-16s fault_time=%.1fmin"
              % (k, v["calls"], v["attempts"], v["faults"], v["zero_byte_returns"],
                 v["max_streak"], v["last_fault_kind"], v["fault_ms"]/60000))
