#!/usr/bin/env bash
# P-C2b ARM S: split-mirroring blind sampling at ARM H's MEASURED budget.
#
# PREREG.md §5. Runs `arm_s_split.py`, which imports the SHIPPED planner so
# its two legs cannot drift from the harness's. The budget is MEASURED, never
# registered: it comes from ARM H's own logged total via W6's flow scan.
#
# Launch detached:  setsid nohup ./pc2b_arm_s.sh & disown
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="${PC2B_LOG:-$HERE/driver.log}"
OUT="${ARM_S_OUT:-$HERE/arm_s}"
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

set -a; . "$HERE/env"; set +a
[ -z "${OLLAMA_API_KEY:-}" ] && { log "FATAL: OLLAMA_API_KEY empty -- rc=1"; exit 1; }

TOKENS_FILE="$HERE/arm_h_tokens.json"
if [ -n "${T_H:-}" ]; then
  BUDGET="$T_H"; log "ARM S budget from the T_H override: $BUDGET"
elif [ -f "$TOKENS_FILE" ]; then
  BUDGET="$(python -c "
import json,pathlib; print(json.loads(pathlib.Path('$TOKENS_FILE').read_text())['T_H'])")"
  log "ARM S budget from ARM H's measured logged total: $BUDGET"
else
  log "FATAL: $TOKENS_FILE missing and T_H unset -- run pc2b_run.sh first -- rc=1"; exit 1
fi
[ "$BUDGET" -le 0 ] && { log "FATAL: measured T_H is $BUDGET -- rc=1"; exit 1; }

log "=== ARM S: arm_s_split.py --token-budget $BUDGET --out $OUT ==="
if python "$HERE/arm_s_split.py" --token-budget "$BUDGET" --out "$OUT" \
     > "$HERE/arm_s.out" 2>&1; then log "ARM S rc=0"; else log "ARM S rc=$? -- see $HERE/arm_s.out"; fi
tail -25 "$HERE/arm_s.out" | tee -a "$LOG" || true

log "=== ADMISSIBILITY: PREREG §5, |T_S - T_H| within 5% ==="
python - "$OUT" "$BUDGET" 2>&1 | tee -a "$LOG" <<'PYADM' || true
import json, pathlib, sys
out, budget = pathlib.Path(sys.argv[1]), int(sys.argv[2])
s = json.loads((out / "summary.json").read_text()) if (out / "summary.json").exists() else {}
spent = int(s.get("tokens_spent") or 0)
ratio = spent / budget if budget else 0.0
print(json.dumps({
    "T_H": budget, "T_S": spent, "ratio": round(ratio, 4),
    "within_5pc": abs(ratio - 1.0) <= 0.05,
    "rule": "PREREG §5 -- outside 5% the comparison is NOT quoted",
}, indent=1, sort_keys=True))
PYADM
log "=== DONE: ARM S ==="
