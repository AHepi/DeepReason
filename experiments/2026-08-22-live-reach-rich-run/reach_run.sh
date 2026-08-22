#!/usr/bin/env bash
# Reach-rich tranche: setup -> qualify -> reason -> audit -> reach census,
# against a fresh root under this tranche directory.
#
# Design is frozen in PREREG.md; this script executes it and judges nothing.
# Launch detached from this directory (CLAUDE.md "Live runs", dr-drive-harness
# §3):   setsid nohup ./reach_run.sh & disown
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
ROOT="$HERE/run"
LOG="$HERE/driver.log"

# Fresh DEEPREASON_HOME: isolates this tranche's admission store and
# qualification cache from any other tranche's state.
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

# Run identity is deterministic (CLAUDE.md "Live runs"): the same question
# and config mint the same root, and a leftover root refuses relaunch with
# RUN_ALREADY_STARTED. Retire it with `git mv run-<id> failed-epochN-run-<id>`
# and COMMIT THE RENAME FIRST -- never edit or overwrite a committed root.
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

# The criteria under test must actually reach the seeded problem, and must
# discriminate on subject rather than form. Both are offline facts; check
# them here so a mis-frozen workload fails before any token is spent.
log "=== PREFLIGHT: seeded criteria + discrimination ==="
if ! python "$HERE/preflight_seed.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "PREFLIGHT FAILED (a criterion does not discriminate) -- rc=1"
  exit 1
fi
log "PREFLIGHT OK rc=0"

# Ollama Cloud concurrency is per ACCOUNT and plan-gated
# (docs/OLLAMA_CLOUD_OPERATIONS.md §1): own the limit client-side.
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

CYCLES="${CYCLES:-24}"
TOKEN_BUDGET="${TOKEN_BUDGET:-400000}"

log "=== REASON: deepreason run --budget cycles=$CYCLES --token-budget $TOKEN_BUDGET ==="
if python -m deepreason --root "$ROOT" run \
    --run-manifest "$ROOT/run-manifest.json" \
    --problem "$ROOT/problem.json" \
    --budget "cycles=$CYCLES" \
    --token-budget "$TOKEN_BUDGET" \
    > "$HERE/reason.log" 2> "$HERE/reason.stderr.log"; then
  log "REASON rc=0"
else
  rc=$?
  log "REASON rc=$rc -- see $HERE/reason.log and $HERE/reason.stderr.log (a non-zero rc here can still be a typed stop; audit before treating it as failure)"
fi

log "=== AUDIT: verify_root + findings + the reach census ==="
python -c "
import json
from deepreason.invariants import verify_root
print(json.dumps(verify_root('$ROOT'), indent=1, sort_keys=True, default=str))
" > "$HERE/verify_root.json" 2>&1 || true
python -m deepreason --root "$ROOT" findings --json > "$HERE/findings.json" 2>&1 || true
python -m deepreason --root "$ROOT" results > "$HERE/results.txt" 2>&1 || true

# The census exits 0 only when the record itself carries reach_set events.
# That exit code IS the tranche's success criterion; nothing downstream may
# soften it.
if python "$HERE/census_new_root.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "REACH CENSUS: reach_set events > 0 -- SUCCESS by PREREG.md §4"
else
  log "REACH CENSUS: zero reach_set events -- judge per PREREG.md §4 (UNSUPPORTED vs PRECONDITION-BLOCKED)"
fi

log "=== DONE: see $HERE/{reason.log,verify_root.json,reach-census.json,findings.json} ==="
