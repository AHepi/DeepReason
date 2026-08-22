#!/usr/bin/env bash
# Epoch-3 ladder: setup -> preflights -> qualify -> PHASE 1 (reason) ->
# amend (second lineage) -> PHASE 2 (continue) -> audit -> reach census.
#
# Design is frozen in PREREG_EPOCH3.md; this script executes it and judges
# nothing. The two-phase shape is not a preference: an amendment epoch is the
# only surface that puts a second problem lineage in a root without a src/
# change (SPEC.md M1/M6), every amendment `continue` accepts must carry
# --attach (M4), and `continue` accepts only a terminal whose stop reason is
# "converged" or "budget_exhausted" (M3). So phase 1 must reach a resumable
# terminal before the amendment can buy anything.
#
# Launch detached from this directory (CLAUDE.md "Live runs",
# dr-drive-harness §3):   setsid nohup ./epoch3_run.sh & disown
# Offline rehearsal, no provider call:   DRY_RUN=1 ./epoch3_run.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
REACH_RICH="$REPO/experiments/2026-08-22-live-reach-rich-run"
# A dry run binds a real manifest, so it must not bind it at the path the
# live launch will claim: an existing $ROOT is exactly what the
# RUN_ALREADY_STARTED guard below refuses, and a rehearsal that blocks the
# launch it was rehearsing is a footgun. The rehearsal root is removed on
# the way out.
if [ "${DRY_RUN:-0}" = "1" ]; then
  ROOT="$HERE/.dry-run-root"
  rm -rf "$ROOT"
else
  ROOT="$HERE/run"
fi
LOG="$HERE/driver.log"
SUPPLEMENT="$HERE/supplement-nocturnal-collapse.md"

# PREREG_EPOCH3.md: the reach-rich tranche's frozen 24 cycles / 400 000
# tokens, SPLIT across the two phases rather than added to.
PHASE1_CYCLES="${PHASE1_CYCLES:-12}"
PHASE1_TOKENS="${PHASE1_TOKENS:-200000}"
PHASE2_CYCLES="${PHASE2_CYCLES:-12}"
PHASE2_TOKENS="${PHASE2_TOKENS:-200000}"

SIBLING_QUESTION="Why does the night-time warmth gap between a large city and its surrounding countryside collapse on a windy or overcast night, and what single mechanism best explains why some cities lose that gap at lower wind speeds than others?"

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
# RUN_ALREADY_STARTED; retire it with `git mv run <state>-epochN-run-<id>`
# and COMMIT THE RENAME FIRST -- never edit or overwrite a committed root.
if [ -e "$ROOT" ]; then
  log "FATAL: $ROOT already exists -- retire it first (git mv), never overwrite -- rc=1"
  exit 1
fi

log "=== SETUP: build_manifest_epoch3.py -> $ROOT ==="
if ! python "$HERE/build_manifest_epoch3.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "SETUP FAILED -- rc=1"
  exit 1
fi
log "SETUP OK rc=0"

# The three subject criteria must actually reach the seeded problem and must
# discriminate on subject rather than form. Run the reach-rich tranche's OWN
# checker rather than a second copy of it; it writes its report into its own
# directory, so the guard below proves the regenerated file is byte-identical
# and no committed artifact of that tranche moved.
log "=== PREFLIGHT: seeded criteria + discrimination ==="
if ! python "$REACH_RICH/preflight_seed.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "PREFLIGHT FAILED (a criterion does not discriminate) -- rc=1"
  exit 1
fi
cp "$REACH_RICH/preflight_seed.json" "$HERE/epoch3-preflight_seed.json"
if [ -n "$(git status --porcelain -- "$REACH_RICH")" ]; then
  log "FATAL: the preflight moved a committed artifact of the reach-rich tranche -- rc=1"
  git status --porcelain -- "$REACH_RICH" | tee -a "$LOG"
  exit 1
fi
log "PREFLIGHT OK rc=0"

# The amendment's attached source must NOT satisfy the seed problem's subject
# predicates by itself, or a lineage-2 artifact could clear them by quoting
# the attachment and the reach hit would be unattributable.
log "=== SUPPLEMENT PREFLIGHT: the attachment must not pass the seed battery ==="
if ! python "$HERE/preflight_supplement.py" "$SUPPLEMENT" 2>&1 | tee -a "$LOG"; then
  log "SUPPLEMENT PREFLIGHT FAILED (the attachment passes all three) -- rc=1"
  exit 1
fi
log "SUPPLEMENT PREFLIGHT OK rc=0"

if [ "${DRY_RUN:-0}" = "1" ]; then
  rm -rf "$ROOT"
  log "DRY RUN: stopping before qualify -- no provider call made, rehearsal root removed, rc=0"
  exit 0
fi

# Ollama Cloud concurrency is per ACCOUNT and plan-gated
# (docs/OLLAMA_CLOUD_OPERATIONS.md §1): own the limit client-side.
# This manifest's subject digest differs from the reach-rich one by the
# attached-evidence policy alone (SPEC.md M8), so the full ~14-minute
# battery runs once here. That is the priced cost of the second lineage.
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

log "=== PHASE 1: run --budget cycles=$PHASE1_CYCLES --token-budget $PHASE1_TOKENS ==="
if python -m deepreason --root "$ROOT" run \
    --run-manifest "$ROOT/run-manifest.json" \
    --problem "$ROOT/problem.json" \
    --budget "cycles=$PHASE1_CYCLES" \
    --token-budget "$PHASE1_TOKENS" \
    > "$HERE/phase1-reason.log" 2> "$HERE/phase1-reason.stderr.log"; then
  log "PHASE 1 rc=0"
else
  rc=$?
  log "PHASE 1 rc=$rc -- see $HERE/phase1-reason.{log,stderr.log} (a non-zero rc here can still be a typed stop; audit before treating it as failure)"
fi

python -m deepreason results "$ROOT" > "$HERE/phase1-results.txt" 2>&1 || true

# `continue` accepts only RESUMABLE_STOP_REASONS = {converged,
# budget_exhausted} (workflow/lifecycle.py:28). Anything else means phase 2
# cannot run, and the honest thing is to say so and audit what phase 1 did
# rather than issue an amendment that can never be continued.
STOP_REASON="$(python -c "
import json, pathlib
p = pathlib.Path('$ROOT/run-stop.json')
print(json.loads(p.read_text())['reason'] if p.exists() else 'NO_STOP_RECORD')
" 2>/dev/null || echo NO_STOP_RECORD)"
log "PHASE 1 stop_reason=$STOP_REASON"

AMENDED=0
if [ "$STOP_REASON" = "converged" ] || [ "$STOP_REASON" = "budget_exhausted" ]; then
  log "=== AMEND: second seed lineage (attach supplement + reshape question) ==="
  if python -m deepreason --root "$ROOT" amend \
      --attach "$SUPPLEMENT" \
      --reshape-question "$SIBLING_QUESTION" \
      > "$HERE/amend.json" 2> "$HERE/amend.stderr.log"; then
    log "AMEND rc=0 -- see $HERE/amend.json"
    AMENDED=1
  else
    rc=$?
    log "AMEND FAILED rc=$rc -- see $HERE/amend.stderr.log"
  fi
else
  log "AMEND SKIPPED: stop_reason '$STOP_REASON' does not authorize continuation (workflow/lifecycle.py:28) -- phase 2 cannot run"
fi

if [ "$AMENDED" = "1" ]; then
  log "=== PHASE 2: continue --budget cycles=$PHASE2_CYCLES --token-budget $PHASE2_TOKENS ==="
  if python -m deepreason --root "$ROOT" continue \
      --budget "cycles=$PHASE2_CYCLES" \
      --token-budget "$PHASE2_TOKENS" \
      > "$HERE/phase2-continue.log" 2> "$HERE/phase2-continue.stderr.log"; then
    log "PHASE 2 rc=0"
  else
    rc=$?
    log "PHASE 2 rc=$rc -- see $HERE/phase2-continue.{log,stderr.log} (a non-zero rc here can still be a typed stop)"
  fi
fi

log "=== AUDIT: verify_root + findings + results + the reach census ==="
python -c "
import json
from deepreason.invariants import verify_root
print(json.dumps(verify_root('$ROOT'), indent=1, sort_keys=True, default=str))
" > "$HERE/verify_root.json" 2>&1 || true
python -m deepreason --root "$ROOT" findings --json > "$HERE/findings.json" 2>&1 || true
# P8-reach: `results` takes its target POSITIONALLY. Addressing it with
# --root falls back to DEEPREASON_HOME and records a path error instead of
# the run summary.
python -m deepreason results "$ROOT" > "$HERE/results.txt" 2>&1 || true

# The census exits 0 only when the record itself carries reach_set events.
# That exit code IS the tranche's success criterion; nothing downstream may
# soften it. The committed shim writes into ITS OWN tranche directory, so
# move the result here and restore that tranche's committed file -- this
# ladder may read another tranche's tooling, never rewrite its record.
CENSUS_RC=0
python "$REACH_RICH/census_new_root.py" "$ROOT" 2>&1 | tee -a "$LOG" || CENSUS_RC=$?
if [ -f "$REACH_RICH/reach-census.json" ]; then
  cp "$REACH_RICH/reach-census.json" "$HERE/epoch3-reach-census.json"
  git checkout -- "$REACH_RICH/reach-census.json" 2>/dev/null || true
fi
if [ -n "$(git status --porcelain -- "$REACH_RICH")" ]; then
  log "WARNING: the reach-rich tranche is not clean after the census -- inspect before committing"
  git status --porcelain -- "$REACH_RICH" | tee -a "$LOG"
fi
if [ "$CENSUS_RC" = "0" ]; then
  log "REACH CENSUS: reach_set events > 0 -- SUCCESS by PREREG_EPOCH3.md §5"
else
  log "REACH CENSUS: zero reach_set events -- judge per PREREG_EPOCH3.md §5"
fi

log "=== DONE: see $HERE/{phase1-reason.log,phase2-continue.log,verify_root.json,epoch3-reach-census.json,findings.json,results.txt} ==="
