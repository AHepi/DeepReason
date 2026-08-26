#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
sed "s|\$HERE/run|\$HERE/run_h3|" /dev/null >/dev/null 2>&1
python - "$HERE/run_h3" <<'PY'
import json, pathlib, sys, collections
root = pathlib.Path(sys.argv[1])
p = root / "progress.jsonl"
if not p.exists():
    print("no progress.jsonl yet"); raise SystemExit(0)
last = [json.loads(l) for l in p.open() if l.strip()][-1]
print(f"state={last['state']} phase={last['phase']} activity={last['activity']!r} "
      f"cycle={last['cycle']} accepted={last['accepted']} refuted={last['refuted']} "
      f"stop={last['stop_reason']}")
log = root / "log.jsonl"
if log.exists():
    m = collections.Counter(); pt = ct = calls = 0
    for line in log.open():
        e = json.loads(line)
        ins = e.get("inputs") or []
        if ins and str(ins[0]).startswith("discharge"):
            h = str(ins[0]); m[h.split(":",1)[0] if h.startswith("discharge:") else h] += 1
    print("  discharge measures:", dict(m) or "NONE YET")
w = root / "objects" / "warrant"
if w.is_dir():
    f = collections.Counter()
    for path in w.glob("*.json"):
        d = json.loads(path.read_text())["data"]
        if d.get("verdict") == "fail": f[d.get("commitment")] += 1
    print("  demonstrative fail warrants:", dict(f) or "NONE YET")
PY
echo "-- THINKING ON? completion share of tokens (ARM H2 was 27.5%) --"
python - "$HERE/run_h3" <<'PY'
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "..", "2026-08-26-run-anatomy-program", "W6-token-flow"))
try:
    import flow
    rel = os.path.relpath(sys.argv[1], os.getcwd())
    rows = flow.scan_root(rel).get("rows") or []
    known = [r for r in rows if r.get("prompt_tokens") is not None]
    if known:
        tp = sum(r["prompt_tokens"] for r in known); tc = sum(r["completion_tokens"] for r in known)
        print(f"  {len(rows)} calls  prompt {tp}  completion {tc}  "
              f"completion share {tc/(tp+tc):.1%}  T_H3 so far {tp+tc}")
    else:
        print("  no calls with an exact split yet")
except Exception as e:
    print("  ", type(e).__name__, e)
PY
grep -E "rc=|FATAL|stop_reason=" "$HERE/driver.log" | tail -3
