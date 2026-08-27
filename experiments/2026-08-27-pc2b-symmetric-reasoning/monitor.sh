#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$(cd "$HERE/../.." && pwd)"
R="experiments/2026-08-27-pc2b-symmetric-reasoning/run"
python - "$R" <<'PY'
import json, pathlib, sys, collections, os
root = pathlib.Path(sys.argv[1])
p = root / "progress.jsonl"
if p.exists():
    last = [json.loads(l) for l in p.open() if l.strip()][-1]
    print(f"state={last['state']} phase={last['phase']} cycle={last['cycle']} "
          f"accepted={last['accepted']} refuted={last['refuted']} stop={last['stop_reason']}")
else:
    print("reasoning not started yet")
log = root / "log.jsonl"
if log.exists():
    m = collections.Counter(); legs = collections.Counter()
    for line in log.open():
        e = json.loads(line)
        ins = e.get("inputs") or []
        if ins and str(ins[0]).startswith("discharge"):
            h = str(ins[0]); m[h.split(":",1)[0] if h.startswith("discharge:") else h] += 1
        if e.get("llm"):
            for t in (e["llm"].get("attempt_trace") or []):
                # Post-fix (main 0a23ae081) the two legs are a typed structure
                # ON one attempt -- `split_legs` -- not two attempt_trace
                # entries carrying `split_leg`. Reading the old shape would
                # report "no legs" on a run that is splitting correctly.
                for leg in (t.get("split_legs") or []):
                    legs[leg.get("leg") or "(unnamed)"] += 1
                if not (t.get("split_legs") or []):
                    legs["unsplit-attempt"] += 1
    print("  discharge measures:", dict(m) or "NONE YET")
    print("  split legs        :", dict(legs) or "NONE YET")
w = root / "objects" / "warrant"
if w.is_dir():
    f = collections.Counter()
    for path in w.glob("*.json"):
        d = json.loads(path.read_text())["data"]
        if d.get("verdict") == "fail": f[d.get("commitment")] += 1
    print("  demonstrative fail warrants:", dict(f) or "NONE YET")
sys.path.insert(0, "experiments/2026-08-26-run-anatomy-program/W6-token-flow")
try:
    import flow
    rows = flow.scan_root(sys.argv[1]).get("rows") or []
    t = sum(r["total_tokens"] for r in rows)
    print(f"  T_H so far: {t} / 200000  ({len(rows)} calls)")
except Exception as e:
    print("  tokens:", type(e).__name__, e)
PY
grep -E "rc=|FATAL|stop_reason=" "$HERE/driver.log" | tail -3
