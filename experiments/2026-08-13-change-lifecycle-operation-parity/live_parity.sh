#!/usr/bin/env bash
# Live proof of lifecycle-operation parity on the REAL grounded-extension
# root: finalize -> amend -> continue.
#
# Launch detached from this directory (CLAUDE.md "Live runs",
# dr-drive-harness §3):
#     setsid nohup ./live_parity.sh & disown
#
# Stages 1 and 2 make NO model call and need no credential. Stage 3 does,
# and is skipped with a typed message when the key is absent, so the
# credential-free half always completes and reports.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
TARGET="$REPO/experiments/2026-08-12-live-grounded-extension-expansion"
ROOT="$TARGET/run"
LOG="$HERE/live_parity.log"

# The six documents the run bound and never introduced. build_manifest.py
# staged their exact bytes; these are the same paths it read.
DOSSIER_PATHS=(
  "$REPO/docs/STATE_OF_THE_THEORY.md"
  "$REPO/docs/harness-spec-v1.3.md"
  "$REPO/docs/proposals/GROUNDED_OVERLAY_PREPLAN.md"
  "$REPO/experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md"
  "$REPO/docs/map/CON-warrants-and-attacks.md"
  "$REPO/docs/map/SUB-adjudication.md"
)

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

cd "$REPO"
export DEEPREASON_HOME="$TARGET/home"
# Ollama Cloud: own the concurrency rather than borrowing it, and treat a
# repeated 429 as quota exhaustion instead of retrying forever
# (docs/OLLAMA_CLOUD_OPERATIONS.md).
export DEEPREASON_QUALIFY_CONCURRENCY=2

if [ ! -d "$ROOT" ]; then
  log "FATAL: $ROOT does not exist -- rc=1"
  exit 1
fi

log "=== STAGE 1: finalize (appends only; no model call) ==="
if python -m deepreason --root "$ROOT" finalize --json \
     > "$HERE/finalize.json" 2> "$HERE/finalize.stderr.log"; then
  log "FINALIZE OK rc=0 -- see $HERE/finalize.json"
else
  rc=$?
  log "FINALIZE rc=$rc -- see $HERE/finalize.stderr.log"
  exit "$rc"
fi

log "=== STAGE 2: amend, admitting the six bound documents (no model call) ==="
ATTACH_ARGS=()
for path in "${DOSSIER_PATHS[@]}"; do
  if [ ! -f "$path" ]; then
    log "FATAL: dossier document missing: $path -- rc=1"
    exit 1
  fi
  ATTACH_ARGS+=(--attach "$path")
done
if python -m deepreason --root "$ROOT" amend "${ATTACH_ARGS[@]}" --json \
     > "$HERE/amend.json" 2> "$HERE/amend.stderr.log"; then
  log "AMEND OK rc=0 -- see $HERE/amend.json"
else
  rc=$?
  log "AMEND rc=$rc -- see $HERE/amend.stderr.log"
  exit "$rc"
fi

log "=== MEASURE: verify_root after the amendment epoch ==="
python -c "
from deepreason.invariants import verify_root
import json
result = verify_root('$ROOT')
print(json.dumps(result['violations'], indent=2, sort_keys=True))
" > "$HERE/verify_root_after_amend.json" 2>&1 || true
log "verify_root written -- see $HERE/verify_root_after_amend.json"

if [ ! -f "$TARGET/env" ]; then
  log "STAGE 3 SKIPPED: $TARGET/env (OLLAMA_API_KEY) is absent -- the"
  log "container dropped the gitignored credential. Stages 1-2 are complete"
  log "and are the credential-free half of the proof. Recreate the file and"
  log "re-run to continue. rc=0"
  exit 0
fi
set -a
# shellcheck disable=SC1090
source "$TARGET/env"
set +a
if [ -z "${OLLAMA_API_KEY:-}" ]; then
  log "STAGE 3 SKIPPED: OLLAMA_API_KEY is empty after sourcing env -- rc=0"
  exit 0
fi

log "=== STAGE 3: continue, +8 cycles, 500000 tokens ==="
if python -m deepreason --root "$ROOT" continue \
     --budget cycles=8 \
     --token-budget 500000 \
     > "$HERE/continue.log" 2> "$HERE/continue.stderr.log"; then
  log "CONTINUE rc=0"
else
  rc=$?
  log "CONTINUE rc=$rc -- a non-zero rc here can still be a typed stop; audit before treating as failure"
fi

log "=== AUDIT: verify_root + findings after the continuation ==="
python -c "
from deepreason.invariants import verify_root
import json
print(json.dumps(verify_root('$ROOT')['violations'], indent=2, sort_keys=True))
" > "$HERE/verify_root_after_continue.json" 2>&1 || true
python -m deepreason --root "$ROOT" findings --json \
  > "$HERE/findings_after_continue.json" 2>&1 || true
log "=== DONE ==="
