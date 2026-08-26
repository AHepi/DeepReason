#!/usr/bin/env bash
# P-C2 ARM S2: blind repeated sampling at ARM H2's MEASURED budget.
#
# PREREG.md §5. This runs P-C1's `arm_s.py` UNCHANGED -- no wrapper, no copy,
# no re-tuned constant. That script already takes `--token-budget` and
# `--out`, so this file supplies exactly those two things and nothing else.
# Anything else it supplied would be a second difference between the arms.
#
# THE BUDGET IS MEASURED, NEVER REGISTERED. It comes from ARM H2's own log
# via W6's flow scan (`arm_h2_tokens.json`, written by `pc2_run.sh`), because
# a cap match would let an arm that under-spends look cheap. If the file is
# missing, this refuses rather than guessing: an unmatched arm is worse than
# no arm, and PREREG §5's rule (T_S >= 0.95 * T_H) cannot be evaluated
# against a number nobody measured.
#
# FRESH SAMPLES, not P-C1's cached best (PREREG §5): a rematch against a
# stored number is a rematch against one draw of the baseline's luck.
#
# Launch detached:  setsid nohup ./pc2_arm_s2.sh & disown
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
FRONTIER="$REPO/experiments/2026-08-25-change-constructive-frontier"
LOG="${PC2_LOG:-$HERE/driver.log}"
OUT="${ARM_S2_OUT:-$HERE/arm_s2}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

set -a
# shellcheck disable=SC1090
. "$HERE/env"
set +a
if [ -z "${OLLAMA_API_KEY:-}" ]; then
  log "FATAL: OLLAMA_API_KEY is empty after sourcing env -- rc=1"
  exit 1
fi

TOKENS_FILE="$HERE/arm_h2_tokens.json"
if [ -n "${T_H:-}" ]; then
  BUDGET="$T_H"
  log "ARM S2 budget from the T_H environment override: $BUDGET"
elif [ -f "$TOKENS_FILE" ]; then
  BUDGET="$(python -c "
import json,pathlib
print(json.loads(pathlib.Path('$TOKENS_FILE').read_text())['T_H'])
")"
  log "ARM S2 budget from ARM H2's measured spend: $BUDGET"
else
  log "FATAL: $TOKENS_FILE is missing and T_H is unset -- run pc2_run.sh first -- rc=1"
  exit 1
fi

if [ "$BUDGET" -le 0 ]; then
  log "FATAL: measured T_H is $BUDGET -- refusing to sample against a zero budget -- rc=1"
  exit 1
fi

log "=== ARM S2: python arm_s.py --token-budget $BUDGET --out $OUT ==="
cd "$FRONTIER"
if python arm_s.py --token-budget "$BUDGET" --out "$OUT" > "$HERE/arm_s2.out" 2>&1; then
  log "ARM S2 rc=0"
else
  rc=$?
  log "ARM S2 rc=$rc -- see $HERE/arm_s2.out"
fi
tail -20 "$HERE/arm_s2.out" | tee -a "$LOG" || true

log "=== ADMISSIBILITY: PREREG §5.4, T_S / T_H >= 0.95 ==="
python - "$OUT" "$BUDGET" 2>&1 | tee -a "$LOG" <<'PYADM' || true
import json, pathlib, sys
out, budget = pathlib.Path(sys.argv[1]), int(sys.argv[2])
summary = json.loads((out / "summary.json").read_text()) if (out / "summary.json").exists() else {}
spent = int(summary.get("tokens_spent") or 0)
ratio = spent / budget if budget else 0.0
print(json.dumps({
    "T_H": budget,
    "T_S": spent,
    "ratio": round(ratio, 4),
    "admissible": ratio >= 0.95,
    "rule": "PREREG §5.4 -- below 0.95 the comparison is UNMATCHED and no margin is claimed",
}, indent=1, sort_keys=True))
PYADM

log "=== DONE: ARM S2 ==="
