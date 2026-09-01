#!/usr/bin/env bash
# P-A1 ladder: setup -> preflights -> qualify -> reason -> BRIDGE -> audit.
#
# The design is frozen in PREREG.md; this script executes it and judges
# NOTHING. Every verdict in this tranche comes from a typed artifact
# (run-status.json, run-stop.json, verify_root, findings.json, results.txt,
# the bridge's own JSON) or from a committed checker's output, never from
# this driver's opinion.
#
# Launch detached from this directory:  setsid nohup ./pa1_run.sh & disown
# Offline rehearsal, no provider call:  DRY_RUN=1 ./pa1_run.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

if [ "${DRY_RUN:-0}" = "1" ]; then
  ROOT="$HERE/.dry-run-root"
  rm -rf "$ROOT"
else
  ROOT="${PA1_ROOT:-$HERE/run}"
fi
LOG="${PA1_LOG:-$HERE/driver.log}"

# PREREG §5. The CYCLE budget is meant to bind first: a token-bound stop
# truncates mid-cycle, a cycle-bound stop does not.
CYCLES="${CYCLES:-24}"
TOKENS="${TOKENS:-3000000}"

# Fresh DEEPREASON_HOME: isolates this tranche's admission store and
# qualification cache. Run identity is deterministic, so the same question
# and config in the same home would refuse with RUN_ALREADY_STARTED.
export DEEPREASON_HOME="${PA1_HOME:-$HERE/home}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

cd "$REPO"

if [ "${DRY_RUN:-0}" != "1" ]; then
  if [ ! -f "$HERE/env" ]; then
    log "FATAL: $HERE/env (OLLAMA_API_KEY) is missing -- rc=1"
    exit 1
  fi
  # ABSOLUTE PATH, and this is not a style preference. `source env` without a
  # leading ./ searches PATH first and finds /usr/bin/env -- the coreutils
  # BINARY -- which sets no variables and fails silently. That mistake made
  # one P-C1 qualification attempt report ENDPOINT_ERROR on all 80 cases
  # against an empty key.
  set -a
  # shellcheck disable=SC1090
  . "$HERE/env"
  set +a
  if [ -z "${OLLAMA_API_KEY:-}" ]; then
    log "FATAL: OLLAMA_API_KEY is empty after sourcing env -- rc=1"
    exit 1
  fi
fi

# A leftover root refuses relaunch with RUN_ALREADY_STARTED; retire it with
# `git mv run <state>-run-<id>` and COMMIT THE RENAME FIRST -- never edit or
# overwrite a committed root.
if [ -e "$ROOT" ]; then
  log "FATAL: $ROOT already exists -- retire it first (git mv), never overwrite -- rc=1"
  exit 1
fi

log "=== P-A1: all modules on, four models, seed question 933313a5... ==="

# The embedder is a CONFIGURED INSTRUMENT for this run, not an optimisation:
# NEAR_DUP_EPS and RESEED_DIST_MIN are absolute distances calibrated to
# fingerprint d6e3599ce0377000, and run-config.yaml sets
# EMBEDDER_FAILURE_POLICY: error so a missing backend fails BEFORE the first
# model call rather than silently swapping the geometry. Warming here pays
# the ~523 MB fetch where it is visible instead of inside cycle 1.
log "=== SETUP: embedder warm-up (idempotent) ==="
if ! python -m deepreason embedder-warmup 2>&1 | tee -a "$LOG"; then
  log "EMBEDDER WARM-UP FAILED -- rc=1"
  exit 1
fi

log "=== SETUP: build_manifest_pa1.py -> $ROOT ==="
if ! python "$HERE/build_manifest_pa1.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "SETUP FAILED -- rc=1"
  exit 1
fi
log "SETUP OK rc=0"

# THE PREFLIGHT THAT DECIDES WHETHER THIS RUN MEANS ANYTHING (PREREG §8).
# Every expensive failure mode of this configuration is SILENT: an empty
# behavioural-contract grant list, a switch the config echo dropped and
# nothing restored, a channel that says ON and cannot reach its capability.
# All three produce a run that spends its whole budget and reads, afterwards,
# exactly like "the models had nothing to say".
log "=== PREFLIGHT: 49 typed gates over the compiled manifest and its runtime Config ==="
PREFLIGHT_ARGS=("$ROOT")
[ "${DRY_RUN:-0}" = "1" ] || PREFLIGHT_ARGS+=(--catalogue)
if ! python "$HERE/preflight_pa1.py" "${PREFLIGHT_ARGS[@]}" 2>&1 | tee -a "$LOG"; then
  log "PREFLIGHT FAILED -- rc=1"
  exit 1
fi
log "PREFLIGHT OK rc=0"

if [ "${DRY_RUN:-0}" = "1" ]; then
  rm -rf "$ROOT"
  log "DRY RUN: stopping before qualify -- no provider call made, rc=0"
  exit 0
fi

# Ollama Cloud concurrency is per ACCOUNT and plan-gated: own the limit
# client-side. This is a NEW subject (four models, engaged criticism policy),
# so the full battery is expected and was priced by the operator on
# 2026-09-01. Do not trim the config to dodge it.
log "=== QUALIFY: production-contract doctor (concurrency=2), full battery expected ==="
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

# --- R3: THE COMPOSITION STEP AT TERMINAL ---------------------------------
# P-S1 ended with bridge_events: 0 for two reasons. One was the policy mode,
# fixed in run-config.yaml. THIS is the other: its ladder never called the
# composition step, so the grounded bridge had nothing to do even where it
# was allowed to. A non-zero rc here is recorded and does NOT abort the
# audit -- a refusal is a typed result this tranche wants to read, not a
# reason to stop reading.
PROBLEM_ID="$(python -c "
import json, pathlib
print(json.loads(pathlib.Path('$ROOT/problem.json').read_text())['problem']['id'])
")"
log "=== BRIDGE: build the grounded final output for $PROBLEM_ID ==="
if python -m deepreason --root "$ROOT" bridge build "$PROBLEM_ID" \
    --target answer --json > "$HERE/bridge-build.json" 2> "$HERE/bridge-build.stderr.log"; then
  log "BRIDGE BUILD rc=0"
else
  log "BRIDGE BUILD rc=$? -- see $HERE/bridge-build.{json,stderr.log}"
fi
for view in status result inspect claims validate; do
  python -m deepreason --root "$ROOT" bridge "$view" --json \
    > "$HERE/bridge-$view.json" 2>&1 || true
done

log "=== AUDIT: verify_root + findings + results + capture + frontier ==="
python -c "
import json
from deepreason.invariants import verify_root
print(json.dumps(verify_root('$ROOT'), indent=1, sort_keys=True, default=str))
" > "$HERE/verify_root.json" 2>&1 || true
python -m deepreason --root "$ROOT" findings --json > "$HERE/findings.json" 2>&1 || true
# `results` takes its target POSITIONALLY; addressing it with --root falls
# back to DEEPREASON_HOME and records a path error instead of the summary.
python -m deepreason results "$ROOT" > "$HERE/results.txt" 2>&1 || true
python -m deepreason results "$ROOT" --json > "$HERE/results.json" 2>&1 || true
python -m deepreason --root "$ROOT" capture > "$HERE/capture.txt" 2>&1 || true
python -m deepreason --root "$ROOT" frontier > "$HERE/frontier.txt" 2>&1 || true
python -m deepreason --root "$ROOT" report > "$HERE/report.txt" 2>&1 || true

# --- the module-coverage census, from the typed record only ---------------
log "=== CENSUS: module coverage + the three measured known-open defects ==="
python "$HERE/module_census.py" "$ROOT" > "$HERE/module_census.json" 2> "$HERE/module_census.stderr.log" || true
python -c "
import json, pathlib
d = json.loads(pathlib.Path('$HERE/module_census.json').read_text())
for row in d.get('modules', []):
    print(f\"  {row['module']:34s} {row['verdict']:12s} {row['evidence']}\")
print('  --- measured known-open defects ---')
for k, v in (d.get('measured') or {}).items():
    print(f'  {k}: {v}')
" 2>&1 | tee -a "$LOG" || true

log "=== DONE: judge only typed outcomes -- state, stop_reason, verify_root, the record ==="
