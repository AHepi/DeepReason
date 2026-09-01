#!/usr/bin/env bash
# P-A1 live monitor. Prints the typed state AND -- the part that matters --
# the TRANSPORT-FAILURE signature.
#
# Why the second half exists. Fifteen of P-S1's twenty-four cycles ran
# against a dead provider and NO summary said so: the run kept advancing
# cycles, the state stayed healthy, and only the per-attempt record knew.
# A monitor that watches `state` and `cycle` alone would have reported that
# run as fine for its whole second half. So this one reports, per role, how
# many provider attempts SUCCEEDED and how many failed, and shouts when the
# most recent window contains failures and no successes.
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$(cd "$HERE/../.." && pwd)"
R="${PA1_ROOT:-$HERE/run}"
python - "$R" <<'PY'
import collections, json, pathlib, sys
root = pathlib.Path(sys.argv[1])

progress = root / "progress.jsonl"
if progress.exists():
    rows = [json.loads(l) for l in progress.open() if l.strip()]
    last = rows[-1]
    print(f"state={last.get('state')} phase={last.get('phase')} "
          f"cycle={last.get('cycle')} accepted={last.get('accepted')} "
          f"refuted={last.get('refuted')} stop={last.get('stop_reason')} "
          f"tokens={last.get('tokens')}")
else:
    print("reasoning not started yet (no progress.jsonl)")

log = root / "log.jsonl"
if not log.exists():
    print("no log.jsonl yet")
    raise SystemExit(0)

ok = collections.Counter()
bad = collections.Counter()
recent = collections.deque(maxlen=40)
rules = collections.Counter()
sig = collections.Counter()
hv = reach = scratchsum = 0
for line in log.open():
    e = json.loads(line)
    rules[e.get("rule")] += 1
    ins = e.get("inputs") or []
    if ins:
        sig[str(ins[0])] += 1
    sd = e.get("state_diff") or {}
    hv += 1 if sd.get("hv_set") else 0
    reach += 1 if sd.get("reach_set") else 0
    scratchsum += 1 if e.get("scratch") else 0
    llm = e.get("llm")
    if not llm:
        continue
    role = llm.get("role") or "?"
    traces = llm.get("attempt_trace") or []
    failed = [t for t in traces if t.get("error") or t.get("failure") or t.get("status") == "error"]
    if failed and not llm.get("output_ref") and not llm.get("output"):
        bad[role] += 1
        recent.append((role, "FAIL"))
    else:
        ok[role] += 1
        recent.append((role, "ok"))

print(f"  rules: {dict(rules)}")
print(f"  hv_set events={hv}  reach_set events={reach}  scratch events={scratchsum}")
print(f"  provider calls OK   : {dict(ok) or 'NONE'}")
print(f"  provider calls FAILED: {dict(bad) or 'none'}")
deferred = {k: v for k, v in sig.items() if k == "v6-model-phase-deferred.v1"}
print(f"  deferred model phases: {deferred or 'none'}")
window = list(recent)
if window and all(s == "FAIL" for _, s in window):
    print("  *** ALERT: every provider call in the last "
          f"{len(window)} attempts FAILED -- this is the P-S1 dead-provider "
          "signature; the run will keep advancing cycles and say nothing ***")
elif window and sum(1 for _, s in window if s == "FAIL") > len(window) // 2:
    print(f"  *** WARNING: {sum(1 for _, s in window if s == 'FAIL')} of the last "
          f"{len(window)} provider attempts failed ***")
PY
echo "--- driver log, last rc/FATAL/stop lines ---"
grep -E "rc=|FATAL|stop_reason=|ALERT" "$HERE/driver.log" 2>/dev/null | tail -6
