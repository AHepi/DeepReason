#!/usr/bin/env bash
# P-C1 ARM H, the ladder's remaining phases, re-entered on an EXISTING root.
#
# WHY THIS SCRIPT EXISTS.  `pc1_run.sh` refuses to touch a root that already
# exists -- correctly: run identity is deterministic and overwriting a root
# is how evidence gets destroyed.  But the first launch built a perfectly
# good root and then died in QUALIFY on a stochastic seat-contract failure
# (driver.log 18:52:07, `REPAIR_SCOPE_VIOLATION` on critic.atomic-target.v1,
# 19 of 20 cases valid).  Re-qualification passed 80/80 with zero scope
# violations on the SAME manifest, so the root is sound and only the
# remaining phases need running.
#
# This runs exactly the commands pc1_run.sh runs, on the same root, with the
# same budgets, appending to the same driver.log.  It builds nothing and
# judges nothing.
#
# Launch detached:  setsid nohup ./pc1_reason.sh & disown
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
ROOT="${PC1_ROOT:-$HERE/run}"
LOG="${PC1_LOG:-$HERE/driver.log}"
CYCLES="${CYCLES:-24}"
TOKENS="${TOKENS:-3000000}"
export DEEPREASON_HOME="${PC1_HOME:-$HERE/home}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }
cd "$REPO"

# ABSOLUTE PATH, and this is not a style preference.  `source env` without a
# leading ./ searches PATH first and finds /usr/bin/env -- the coreutils
# BINARY -- which sets no variables and fails silently.  That mistake made
# one qualification attempt report ENDPOINT_ERROR on all 80 cases against an
# empty key; the attempt is retained as
# qualify-attempt2-VOID-agent-error.json.
set -a
# shellcheck disable=SC1090
. "$HERE/env"
set +a
if [ -z "${OLLAMA_API_KEY:-}" ]; then
  log "FATAL: OLLAMA_API_KEY is empty after sourcing env -- rc=1"
  exit 1
fi

if [ ! -f "$ROOT/run-manifest.json" ]; then
  log "FATAL: $ROOT has no bound manifest -- use pc1_run.sh for a fresh launch -- rc=1"
  exit 1
fi

log "=== REASON (re-entry): run --budget cycles=$CYCLES --token-budget $TOKENS ==="
if python -m deepreason --root "$ROOT" run \
    --run-manifest "$ROOT/run-manifest.json" \
    --problem "$ROOT/problem.json" \
    --budget "cycles=$CYCLES" \
    --token-budget "$TOKENS" \
    > "$HERE/reason.log" 2> "$HERE/reason.stderr.log"; then
  log "REASON rc=0"
else
  rc=$?
  log "REASON rc=$rc -- see $HERE/reason.{log,stderr.log} (a non-zero rc here can still be a typed stop; audit before treating it as failure)"
fi

STOP_REASON="$(python -c "
import json, pathlib
p = pathlib.Path('$ROOT/run-stop.json')
print(json.loads(p.read_text())['reason'] if p.exists() else 'NO_STOP_RECORD')
" 2>/dev/null || echo NO_STOP_RECORD)"
log "REASON stop_reason=$STOP_REASON"

log "=== AUDIT: verify_root + findings + results ==="
python -c "
import json
from deepreason.invariants import verify_root
print(json.dumps(verify_root('$ROOT'), indent=1, sort_keys=True, default=str))
" > "$HERE/verify_root.json" 2>&1 || true
python -m deepreason --root "$ROOT" findings --json > "$HERE/findings.json" 2>&1 || true
python -m deepreason results "$ROOT" > "$HERE/results.txt" 2>&1 || true

log "=== SCORE: the exact checker over every artifact in the record ==="
python "$HERE/score_run.py" "$ROOT" > "$HERE/arm_h_scores.json" 2>&1 || true
python -c "
import json,pathlib
d=json.loads(pathlib.Path('$HERE/arm_h_scores.json').read_text())
print('ARM H best valid score:', d.get('best_score'))
print('ARM H candidates:', d.get('n_candidates'), ' refuted:', d.get('n_refuted'))
print('ARM H tokens spent:', d.get('tokens_spent'))
" 2>&1 | tee -a "$LOG" || true

log "=== DONE (re-entry) ==="
