#!/usr/bin/env bash
# Live verification for the controller-steering fix: setup -> qualify ->
# reason -> audit, against a fresh root under this tranche directory.
#
# The manifest inputs (build_manifest.py, run-config.yaml) are byte-copies of
# the grounded-extension tranche's, so the run compiles the SAME configuration
# that recorded zero steering artifacts -- every role pinned at
# max_tokens=16384. The only difference is the code under test.
#
# Launch detached from this directory: setsid nohup ./verify_run.sh & disown
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
ROOT="$HERE/run"
LOG="$HERE/driver.log"

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

# Ollama Cloud concurrency is per ACCOUNT and plan-gated
# (docs/OLLAMA_CLOUD_OPERATIONS.md §1): own the limit client-side rather
# than letting the server queue an unbounded batch.
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

log "=== REASON: deepreason run --budget cycles=6 --token-budget 150000 ==="
if python -m deepreason --root "$ROOT" run \
    --run-manifest "$ROOT/run-manifest.json" \
    --problem "$ROOT/problem.json" \
    --budget cycles=6 \
    --token-budget 150000 \
    > "$HERE/reason.log" 2> "$HERE/reason.stderr.log"; then
  log "REASON rc=0"
else
  rc=$?
  log "REASON rc=$rc -- see $HERE/reason.log and $HERE/reason.stderr.log (a non-zero rc here can still be a typed stop; audit before treating as failure)"
fi

log "=== AUDIT: verify_root + findings + the steering evidence ==="
python -c "
from deepreason.invariants import verify_root
import json
print(json.dumps(verify_root('$ROOT')['violations'], indent=1))
" > "$HERE/verify_root.json" 2>&1 || true
python -m deepreason --root "$ROOT" findings --json > "$HERE/findings.json" 2>&1 || true
python "$HERE/steering_evidence.py" "$ROOT" > "$HERE/steering_evidence.txt" 2>&1 || true

log "=== DONE: see $HERE/{reason.log,verify_root.json,steering_evidence.txt} ==="
