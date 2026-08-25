#!/usr/bin/env bash
# P-R1 ladder: setup -> preflights -> qualify -> reason -> audit.
#
# The design is frozen in PREREG.md; this script executes it and judges
# NOTHING. Every verdict in this tranche comes from a typed artifact
# (run-status.json, verify_root, findings.json, results.txt), never from
# this driver's own opinion.
#
# Launch detached from this directory (CLAUDE.md "Live runs",
# dr-drive-harness §3):   setsid nohup ./pr1_run.sh & disown
# Offline rehearsal, no provider call:   DRY_RUN=1 ./pr1_run.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

# A dry run binds a real manifest, so it must not bind it at the path the
# live launch will claim: an existing $ROOT is exactly what the
# RUN_ALREADY_STARTED guard below refuses, and a rehearsal that blocks the
# launch it was rehearsing is a footgun.
if [ "${DRY_RUN:-0}" = "1" ]; then
  ROOT="$HERE/.dry-run-root"
  rm -rf "$ROOT"
else
  ROOT="$HERE/run"
fi
LOG="$HERE/driver.log"

# PREREG.md §3. The CYCLE budget is meant to bind first: a token-bound stop
# truncates mid-cycle, a cycle-bound stop does not.
CYCLES="${CYCLES:-12}"
TOKENS="${TOKENS:-3000000}"

# Fresh DEEPREASON_HOME: isolates this tranche's admission store and
# qualification cache from any other tranche's state.
export DEEPREASON_HOME="$HERE/home"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

cd "$REPO"

if [ "${DRY_RUN:-0}" != "1" ]; then
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
fi

# Run identity is deterministic. A leftover root refuses relaunch with
# RUN_ALREADY_STARTED; retire it with `git mv run <state>-run-<id>` and
# COMMIT THE RENAME FIRST -- never edit or overwrite a committed root.
if [ -e "$ROOT" ]; then
  log "FATAL: $ROOT already exists -- retire it first (git mv), never overwrite -- rc=1"
  exit 1
fi

log "=== SETUP: build_manifest_pr1.py -> $ROOT ==="
if ! python "$HERE/build_manifest_pr1.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "SETUP FAILED -- rc=1"
  exit 1
fi
log "SETUP OK rc=0"

# The three subject predicates must discriminate on subject rather than
# form, and the dossier-leakage census must be re-measured rather than
# trusted from PREREG.md: the criteria and the record are both committed
# here, so a drift in either shows up as a changed report.
log "=== PREFLIGHT: criteria discrimination + dossier leakage census ==="
if ! python "$HERE/preflight_criteria.py" 2>&1 | tee -a "$LOG"; then
  log "PREFLIGHT FAILED (the battery does not discriminate on subject) -- rc=1"
  exit 1
fi
log "PREFLIGHT OK rc=0"

# Every seat's model must EXIST before ~14 minutes of qualification spend
# discovers otherwise. Compile no longer refuses an unreachable model
# (operator law 2026-08-12), so this is the cheapest place the four ids can
# be falsified. The catalogue endpoint answers unauthenticated.
log "=== PREFLIGHT: the four seat models exist in the live catalogue ==="
if ! python "$HERE/preflight_models.py" 2>&1 | tee -a "$LOG"; then
  log "MODEL PREFLIGHT FAILED (a seat names a model the provider does not list) -- rc=1"
  exit 1
fi
log "MODEL PREFLIGHT OK rc=0"

if [ "${DRY_RUN:-0}" = "1" ]; then
  rm -rf "$ROOT"
  log "DRY RUN: stopping before qualify -- no provider call made, rehearsal root removed, rc=0"
  exit 0
fi

# Ollama Cloud concurrency is per ACCOUNT and plan-gated
# (docs/OLLAMA_CLOUD_OPERATIONS.md §1): own the limit client-side.
# This manifest's subject digest is new -- four models, a judge ensemble and
# a bound dossier -- so the full battery runs here. That is the priced cost
# of the configuration, not a fault.
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

log "=== REASON: run --budget cycles=$CYCLES --token-budget $TOKENS ==="
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

log "=== AUDIT: verify_root + findings + results + the milestone census ==="
python -c "
import json
from deepreason.invariants import verify_root
print(json.dumps(verify_root('$ROOT'), indent=1, sort_keys=True, default=str))
" > "$HERE/verify_root.json" 2>&1 || true
python -m deepreason --root "$ROOT" findings --json > "$HERE/findings.json" 2>&1 || true
# `results` takes its target POSITIONALLY; addressing it with --root falls
# back to DEEPREASON_HOME and records a path error instead of the summary.
python -m deepreason results "$ROOT" > "$HERE/results.txt" 2>&1 || true

# The milestone census decides M1/M2/M3 from the typed record alone. Its
# exit code is NOT the tranche's verdict -- PREREG.md §6 is -- but a
# non-zero exit means a REQUIRED milestone is unmet and RESULTS.md must say
# so as a recorded negative result.
MILESTONE_RC=0
python "$HERE/milestone_census.py" "$ROOT" 2>&1 | tee -a "$LOG" || MILESTONE_RC=$?
if [ "$MILESTONE_RC" = "0" ]; then
  log "MILESTONES: M1 and M2 met, M3 met or untriggered -- SUCCESS by PREREG.md §6"
else
  log "MILESTONES: a REQUIRED milestone is unmet (rc=$MILESTONE_RC) -- typed failure, judge per PREREG.md §6"
fi

log "=== DONE: see $HERE/{reason.log,verify_root.json,findings.json,results.txt,milestones.json} ==="
