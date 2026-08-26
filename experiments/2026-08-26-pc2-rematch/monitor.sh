#!/usr/bin/env bash
# One monitor tick: the typed state of the newest root, plus the driver's own
# rc= lines. Judges nothing -- it prints what the record says.
HERE="$(cd "$(dirname "$0")" && pwd)"
R="$HERE/run"
python - "$R" <<'PY'
import json, pathlib, sys, collections
root = pathlib.Path(sys.argv[1])
p = root / "progress.jsonl"
if not p.exists():
    print("no progress.jsonl yet"); raise SystemExit(0)
lines = [json.loads(l) for l in p.open() if l.strip()]
last = lines[-1]
print(f"state={last['state']} phase={last['phase']} activity={last['activity']!r} "
      f"cycle={last['cycle']} tokens={last['token_spend']}/{last['token_limit']} "
      f"accepted={last['accepted']} refuted={last['refuted']} "
      f"frontier={last['frontier_size']} stop={last['stop_reason']}")
# The two facts that say the organ under test is ALIVE.
log = root / "log.jsonl"
if log.exists():
    m = collections.Counter()
    for line in log.open():
        e = json.loads(line)
        ins = e.get("inputs") or []
        if ins and str(ins[0]).startswith("discharge"):
            h = str(ins[0])
            m[h.split(":", 1)[0] if h.startswith("discharge:") else h] += 1
    print("  discharge measures:", dict(m) or "NONE YET")
w = root / "objects" / "warrant"
if w.is_dir():
    f = collections.Counter()
    for path in w.glob("*.json"):
        d = json.loads(path.read_text())["data"]
        if d.get("verdict") == "fail":
            f[d.get("commitment")] += 1
    print("  demonstrative fail warrants:", dict(f) or "NONE YET")
PY
echo "-- driver rc= lines --"
grep -E "rc=|FATAL|stop_reason=" "$HERE/driver.log" | tail -5
