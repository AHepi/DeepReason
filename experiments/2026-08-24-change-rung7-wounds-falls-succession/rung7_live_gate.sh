#!/usr/bin/env bash
# Rung 7 live gate (L-6): setup -> qualify -> reason -> STAGE A FALL -> audit.
#
# The tranche instruction's own words: "a fall staged on a live root, judged on
# typed outcomes only (the mark appears with its grade, the cascade fires,
# verify_root clean)". This script executes that and judges nothing else --
# `stage_fall.py` prints typed outcomes and returns an exit code; no line here
# reads the model's prose.
#
# THE LAUNCH CONFIG IS THE SOAK'S OWN `epoch3` CASE, field for field, and that
# is not a convenience. CLAUDE.md: no live launch without a green cycle soak on
# the launch config, and "if the launch config differs from the epoch3 case,
# extend the soak's case table in the same commit rather than skipping the
# gate". `scripts/cycle_soak.py`'s epoch3 case IS
# `experiments/2026-08-22-live-reach-rich-run/run-config.yaml` driven through
# that tranche's `build_manifest`, so this ladder uses exactly those two rather
# than a profile of its own.
#
# The first attempt here did NOT: it built a profile through `deepreason setup`,
# which is a different config from the one the soak covered, and glm-5.2
# qualified at the SHALLOW tier under it. That was the discipline catching a
# real mistake before it produced a root, and it is recorded rather than
# quietly corrected.
#
# Launch detached from this directory:  setsid nohup ./rung7_live_gate.sh & disown
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
REACH_RICH="$REPO/experiments/2026-08-22-live-reach-rich-run"
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

# Run identity is deterministic: the same question and config mint the same
# root, and a leftover root refuses relaunch with RUN_ALREADY_STARTED. Retire
# it with `git mv`, never overwrite.
if [ -e "$ROOT" ]; then
  log "FATAL: $ROOT already exists -- retire it first (git mv), never overwrite -- rc=1"
  exit 1
fi

log "=== SETUP: the soak's epoch3 manifest, built into $ROOT ==="
if ! python "$REACH_RICH/build_manifest.py" "$ROOT" > "$HERE/setup.log" 2>&1; then
  log "SETUP FAILED -- see $HERE/setup.log -- rc=1"
  exit 1
fi
log "SETUP OK rc=0"

log "=== QUALIFY: production-contract doctor (concurrency=2) ==="
export DEEPREASON_QUALIFY_CONCURRENCY=2
if python -m deepreason doctor \
    --run-manifest "$ROOT/run-manifest.json" \
    --production-contracts \
    --out "$ROOT/production-contract-qualification.json" \
    > "$HERE/qualify.log" 2> "$HERE/qualify.stderr.log"; then
  log "QUALIFY OK rc=0"
else
  rc=$?
  log "QUALIFY FAILED rc=$rc -- see $HERE/qualify.log and $HERE/qualify.stderr.log"
  exit "$rc"
fi

CYCLES="${CYCLES:-6}"
TOKEN_BUDGET="${TOKEN_BUDGET:-150000}"

# REASON *and* the staging, in one process. The fall is staged on the OPEN
# harness, inside the run, because writing to a terminalized root is a state no
# operator can reach -- and the harness says so: the first attempt staged on
# the stopped root and `verify_root` refused it with
# TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED. L-6 judges verify_root CLEAN, so an
# illegitimate staging cannot produce a passing gate. That refusal is kept as
# `refused-post-horizon-l6-outcomes.json` rather than tidied away.
log "=== REASON + STAGE THE FALL (in-run): cycles=$CYCLES token-budget=$TOKEN_BUDGET ==="
if python "$HERE/live_gate_driver.py" "$CYCLES" "$TOKEN_BUDGET" \
    > "$HERE/l6-driver.log" 2>&1; then
  log "L-6 PASS -- see $HERE/l6-typed-outcomes.json"
else
  rc=$?
  log "L-6 rc=$rc -- see $HERE/l6-typed-outcomes.json and $HERE/l6-driver.log"
fi

python -m deepreason results "$ROOT" > "$HERE/results.txt" 2>&1 || true
python -m deepreason --root "$ROOT" findings --json > "$HERE/findings.json" 2>&1 || true

log "=== DONE: $HERE/{l6-typed-outcomes.json,reason.log,results.txt,findings.json} ==="
