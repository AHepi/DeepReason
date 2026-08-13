#!/usr/bin/env bash
# grounded-extension expansion, third launch attempt: setup -> qualify ->
# reason -> audit against a fresh root under this tranche directory.
#
# Launch detached from this directory: setsid nohup ./grounded_run.sh &
# disown -- see CLAUDE.md "Live runs" and dr-drive-harness §3.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
ROOT="$HERE/run"
LOG="$HERE/driver.log"

# Fresh DEEPREASON_HOME (CLAUDE.md "Live runs"): isolates the admission
# store admit_attachment_paths writes into (admission/) from any prior
# tranche's state. This ladder's own qualification step is NOT the
# subject-digest-cached `deepreason qualify` battery -- it is the
# manifest-bound production-contract doctor (PREREG.md "Launch mechanics"),
# which always executes fresh and writes its report into --root, never into
# DEEPREASON_HOME -- so this isolates the admission store, not a cache.
export DEEPREASON_HOME="$HERE/home"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

cd "$REPO"

if [ ! -f "$HERE/env" ]; then
  log "FATAL: $HERE/env (OLLAMA_API_KEY) is missing -- rc=1"
  exit 1
fi
set -a
# shellcheck disable=SC1090
source "$HERE/env"
set +a
if [ -z "${OLLAMA_API_KEY:-}" ]; then
  log "FATAL: OLLAMA_API_KEY is empty after sourcing env -- rc=1"
  exit 1
fi

if [ -e "$ROOT" ]; then
  log "FATAL: $ROOT already exists -- retire it first (git mv), never overwrite -- rc=1"
  exit 1
fi

log "=== SETUP: build_manifest.py -> $ROOT ==="
if ! python "$HERE/build_manifest.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "SETUP FAILED -- rc=1"
  exit 1
fi
log "SETUP OK rc=0"

log "=== QUALIFY: production-contract doctor (concurrency=2) ==="
export DEEPREASON_QUALIFY_CONCURRENCY=2
if python -m deepreason doctor \
    --run-manifest "$ROOT/run-manifest.json" \
    --production-contracts \
    --out "$ROOT/production-contract-qualification.json" \
    > "$HERE/qualify.json" 2> "$HERE/qualify.stderr.log"; then
  log "QUALIFY OK rc=0"
else
  rc=$?
  log "QUALIFY FAILED rc=$rc -- see $HERE/qualify.json and $HERE/qualify.stderr.log"
  exit "$rc"
fi

log "=== REASON: deepreason run --budget cycles=24 --token-budget 1000000 ==="
if python -m deepreason --root "$ROOT" run \
    --run-manifest "$ROOT/run-manifest.json" \
    --problem "$ROOT/problem.json" \
    --budget cycles=24 \
    --token-budget 1000000 \
    > "$HERE/reason.log" 2> "$HERE/reason.stderr.log"; then
  log "REASON rc=0"
else
  rc=$?
  log "REASON rc=$rc -- see $HERE/reason.log and $HERE/reason.stderr.log (a non-zero rc here can still be a typed stop; audit before treating as failure)"
fi

log "=== AUDIT: verify_root + findings ==="
python -c "
from deepreason.invariants import verify_root
result = verify_root('$ROOT')
print('violations:', result['violations'])
" 2>&1 | tee -a "$LOG" > "$HERE/verify_root.json" || true
python -m deepreason --root "$ROOT" findings --json > "$HERE/findings.json" 2>&1 || true

log "=== DONE: see $HERE/{reason.log,verify_root.json,findings.json,$ROOT/run-status.json} ==="
