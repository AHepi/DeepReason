#!/usr/bin/env bash
# ARM S2 watchdog: resume with the REMAINING budget if the sampler dies early.
#
# P-C1's ARM S ran in THREE segments for exactly this reason -- a worker
# restart killed the first at 56% of budget and an uncaught
# http.client.RemoteDisconnected killed the second at 72%. Each resumption
# carried the remaining budget, so the segments sum to ONE matched arm rather
# than three arms. That is the procedure this reproduces, unattended.
#
# It changes NOTHING about the sampling: `arm_s.py` is invoked unmodified,
# each sample is still blind and one-shot, and the budgets sum to T_H.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
FRONTIER="$HERE/../2026-08-25-change-constructive-frontier"
LOG="$HERE/driver.log"
T_H="$(python -c "import json;print(json.load(open('$HERE/arm_h2_tokens.json'))['T_H'])")"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

set -a; . "$HERE/env"; set +a

spent() {
  python - "$HERE" <<'PY'
import json, pathlib, sys
total = 0
for d in sorted(pathlib.Path(sys.argv[1]).glob("arm_s2*")):
    f = d / "results.jsonl"
    if f.is_dir() or not f.exists():
        continue
    rows = [json.loads(l) for l in f.open() if l.strip()]
    if rows:
        total += rows[-1]["cumulative_tokens"]
print(total)
PY
}

seg=2
while true; do
  # Wait for whatever segment is running to exit.
  while pgrep -f "arm_s\.py --token-budget" >/dev/null; do sleep 60; done
  s="$(spent)"
  remaining=$(( T_H - s ))
  log "ARM S2 watchdog: segment ended, spent=$s of $T_H, remaining=$remaining"
  if [ "$remaining" -le 0 ]; then
    log "ARM S2 watchdog: budget met -- done"; break
  fi
  # A tiny remainder cannot buy a sample; stop rather than spin.
  if [ "$remaining" -lt 5000 ]; then
    log "ARM S2 watchdog: remaining $remaining < one sample -- done"; break
  fi
  log "ARM S2 watchdog: resuming as segment $seg with budget $remaining"
  ( cd "$FRONTIER" && python arm_s.py --token-budget "$remaining" \
      --out "$HERE/arm_s2_part$seg" >> "$HERE/arm_s2.out" 2>&1 )
  seg=$(( seg + 1 ))
  [ "$seg" -gt 8 ] && { log "ARM S2 watchdog: 8 segments, stopping"; break; }
done
log "=== ARM S2 watchdog exit ==="
