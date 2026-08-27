#!/usr/bin/env bash
# P-C2 ARM H3, re-entered on an EXISTING, SOUND root after a CONTAINER RESTART.
#
# WHY THIS SCRIPT EXISTS. `pc2_run.sh` refuses to touch a root that already
# exists -- correctly: run identity is deterministic and overwriting a root is
# how evidence gets destroyed. But the container restarted at 2026-08-27
# ~00:17Z (`uptime` reported 3 minutes) and killed both arms mid-flight. ARM
# H3 had already built a good root and was 45 minutes into QUALIFY; the root
# carries its bound manifest with the registered seat settings
# (reasoning unset, max_tokens 100000, timeout_s 900), an empty log, and no
# cycles. Nothing to preserve, nothing to redo except the phases that did not
# finish. This is P-C1's `pc1_reason.sh` situation exactly, and this file is
# that script's shape.
#
# WHAT IT DOES NOT DO: build anything, or judge anything.
#
# Launch detached:  setsid nohup ./pc2_reenter.sh & disown
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
FRONTIER="$REPO/experiments/2026-08-25-change-constructive-frontier"
ROOT="${PC2_ROOT:-$HERE/run_h3}"
LOG="${PC2_LOG:-$HERE/driver.log}"
CYCLES="${CYCLES:-24}"
TOKENS="${TOKENS:-3000000}"
export PC2_CONFIG="${PC2_CONFIG:-run-config-h3.yaml}"
ARM="H3"; ARMLC="h3"
export DEEPREASON_HOME="${PC2_HOME:-$HERE/home}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }
cd "$REPO"

# ABSOLUTE PATH with a leading dot. `source env` without one searches PATH
# first and finds the coreutils BINARY /usr/bin/env, which sets no variables
# and fails silently -- one P-C1 qualification attempt reported ENDPOINT_ERROR
# on all 80 cases against an empty key that way.
set -a
# shellcheck disable=SC1090
. "$HERE/env"
set +a
if [ -z "${OLLAMA_API_KEY:-}" ]; then
  log "FATAL: OLLAMA_API_KEY is empty after sourcing env -- rc=1"; exit 1
fi

if [ ! -f "$ROOT/run-manifest.json" ]; then
  log "FATAL: $ROOT has no bound manifest -- use pc2_run.sh for a fresh launch -- rc=1"
  exit 1
fi

# A killed process leaves its operator locks behind. They are the harness's
# own concurrency guard, not evidence, and a restart is exactly the case they
# cannot distinguish from a live peer -- so they are cleared HERE, visibly,
# rather than by a flag that would also clear them against a real peer.
for lock in "$ROOT"/.run-operator.lock "$ROOT"/.make-operator.lock; do
  [ -e "$lock" ] && { rm -f "$lock"; log "cleared stale lock $(basename "$lock") (container restart)"; }
done

log "=== ARM $ARM RE-ENTRY (container restart 2026-08-27 ~00:17Z) on $ROOT ==="

# The preflight still binds on re-entry: it reads the BOUND manifest, so it
# proves the root that is about to run carries the registered arm -- thinking
# ON, the discharge channel live, and no unaccounted manifest drift.
log "=== PREFLIGHT: question frozen, registered delta, CHANNEL LIVE, THINKING ON ==="
if ! python "$HERE/preflight_pc2.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "P-C2 PREFLIGHT FAILED -- rc=1"; exit 1
fi
log "P-C2 PREFLIGHT OK rc=0"

log "=== QUALIFY: production-contract doctor (concurrency=2) ==="
export DEEPREASON_QUALIFY_CONCURRENCY=2
if python -m deepreason doctor \
    --run-manifest "$ROOT/run-manifest.json" \
    --production-contracts \
    --out "$ROOT/production-contract-qualification.json" \
    > "$HERE/qualify-$ARMLC.json" 2> "$HERE/qualify-$ARMLC.stderr.log"; then
  log "QUALIFY OK rc=0"
else
  rc=$?
  log "QUALIFY FAILED rc=$rc -- see $HERE/qualify-$ARMLC.{json,stderr.log}"
  exit "$rc"
fi

log "=== REASON: run --budget cycles=$CYCLES --token-budget $TOKENS ==="
if python -m deepreason --root "$ROOT" run \
    --run-manifest "$ROOT/run-manifest.json" \
    --problem "$ROOT/problem.json" \
    --budget "cycles=$CYCLES" \
    --token-budget "$TOKENS" \
    > "$HERE/reason-$ARMLC.log" 2> "$HERE/reason-$ARMLC.stderr.log"; then
  log "REASON rc=0"
else
  rc=$?
  log "REASON rc=$rc -- see $HERE/reason-$ARMLC.{log,stderr.log} (a non-zero rc here can still be a typed stop; audit before treating it as failure)"
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
" > "$HERE/verify_root-$ARMLC.json" 2>&1 || true
python -m deepreason --root "$ROOT" findings --json > "$HERE/findings-$ARMLC.json" 2>&1 || true
python -m deepreason results "$ROOT" > "$HERE/results-$ARMLC.txt" 2>&1 || true

log "=== SCORE: the exact checker over every artifact in the record ==="
python "$FRONTIER/score_run.py" "$ROOT" > "$HERE/arm_${ARMLC}_scores.json" 2>&1 || true
python -c "
import json,pathlib
d=json.loads(pathlib.Path('$HERE/arm_${ARMLC}_scores.json').read_text())
print('ARM $ARM best valid score:', d.get('best_score'))
print('ARM $ARM candidates:', d.get('n_candidates'), ' refuted:', d.get('n_refuted'))
" 2>&1 | tee -a "$LOG" || true

log "=== T_H3: provider-counted tokens, from W6's committed flow scan ==="
python - "$ROOT" > "$HERE/arm_${ARMLC}_tokens.json" 2>&1 <<'PYTOK' || true
import json, os, sys
sys.path.insert(0, "experiments/2026-08-26-run-anatomy-program/W6-token-flow")
import flow
root = os.path.relpath(sys.argv[1], os.getcwd())
rows = flow.scan_root(root).get("rows") or []
print(json.dumps({"root": root, "llm_calls": len(rows),
                  "T_H": sum(r["total_tokens"] for r in rows)}, indent=1, sort_keys=True))
PYTOK
cat "$HERE/arm_${ARMLC}_tokens.json" | tee -a "$LOG" || true

log "=== DONE (ARM $ARM re-entry) ==="
