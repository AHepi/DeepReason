#!/usr/bin/env bash
# P-A2 ladder: stage profiles -> setup -> preflight -> qualify -> reason
#              -> BRIDGE -> audit -> census.
#
# P-A1's ladder with TWO steps added and nothing removed. The design is
# frozen in PREREG.md; this script executes it and judges NOTHING. Every
# verdict in this tranche comes from a typed artifact (run-status.json,
# run-stop.json, verify_root, findings.json, results.json, the bridge JSONs)
# or from a committed checker's output, never from this driver's opinion.
#
# THE TWO ADDED STEPS, both P-A2 requirements:
#   1. STAGE MODEL PROFILES into $DEEPREASON_HOME/model-profiles BEFORE the
#      compile. Nothing ships (docs/model-profiles/README.md: "Home directory
#      only, nothing ships"), so without this the run stamps a registry of
#      ZERO profiles -- the designed state of an unstaged home, and a STOP for
#      this tranche.
#   2. The OUTCOME-BASED audit: monitor_pa2.py (typed attempt outcomes) and
#      rescore.py (the ARTIFACT Pareto frontier, which is not what the
#      `frontier` CLI prints).
#
# Launch detached from this directory:  setsid nohup ./pa2_run.sh & disown
# Offline rehearsal, no provider call:  DRY_RUN=1 ./pa2_run.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

if [ "${DRY_RUN:-0}" = "1" ]; then
  ROOT="$HERE/.dry-run-root"
  rm -rf "$ROOT"
else
  ROOT="${PA2_ROOT:-$HERE/run}"
fi
LOG="${PA2_LOG:-$HERE/driver.log}"

# PREREG §3. The CYCLE budget is meant to bind first: a token-bound stop
# truncates mid-cycle, a cycle-bound stop does not. P-A1's own depth and
# budget, unchanged, because this run is a comparison.
CYCLES="${CYCLES:-24}"
TOKENS="${TOKENS:-3000000}"

# Fresh DEEPREASON_HOME: isolates this tranche's admission store and
# qualification cache. Run identity is deterministic, so the same question
# and config in the same home would refuse with RUN_ALREADY_STARTED.
export DEEPREASON_HOME="${PA2_HOME:-$HERE/home}"

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

log "=== P-A2: P-A1's shape, four fields corrected, seed question 933313a5... ==="

# --- C5: THE MODEL PROFILES ------------------------------------------------
# Copied, not symlinked: the registry digests the document bytes it reads, and
# a link into the working tree would make the run's stamp depend on a file the
# tranche can still edit afterwards.
log "=== SETUP: stage model profiles into \$DEEPREASON_HOME/model-profiles ==="
mkdir -p "$DEEPREASON_HOME/model-profiles"
cp -r "$REPO"/docs/model-profiles/*/ "$DEEPREASON_HOME/model-profiles/"
python - <<'PY' 2>&1 | tee -a "$LOG"
from deepreason.model_profiles import profiles_root, registry_fingerprint
fingerprint = registry_fingerprint()
print(f"model-profile registry: {fingerprint['count']} profiles at {profiles_root()}")
print(f"  ids      : {[row['model_id'] for row in fingerprint['profiles']]}")
print(f"  unreadable: {fingerprint['problem_count']} {fingerprint['problems']}")
# A zero stamp is a STOP for this tranche, and it is the DESIGNED state of an
# unstaged home -- so it must fail loudly here rather than read as "the models
# were never described".
raise SystemExit(0 if fingerprint["count"] == 5 else 1)
PY
log "PROFILES OK rc=0"

# The embedder is a CONFIGURED INSTRUMENT for this run, not an optimisation:
# NEAR_DUP_EPS and RESEED_DIST_MIN are absolute distances calibrated to
# fingerprint d6e3599ce0377000, and run-config.yaml sets
# EMBEDDER_FAILURE_POLICY: error so a missing backend fails BEFORE the first
# model call rather than silently swapping the geometry.
log "=== SETUP: embedder warm-up (idempotent) ==="
if ! python -m deepreason embedder-warmup 2>&1 | tee -a "$LOG"; then
  log "EMBEDDER WARM-UP FAILED -- rc=1"
  exit 1
fi

log "=== SETUP: build_manifest_pa2.py -> $ROOT ==="
if ! python "$HERE/build_manifest_pa2.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "SETUP FAILED -- rc=1"
  exit 1
fi
log "SETUP OK rc=0"

# THE PREFLIGHT THAT DECIDES WHETHER THIS RUN MEANS ANYTHING (PREREG §7).
# Every expensive failure mode of this configuration is SILENT: an empty
# behavioural-contract grant list, a switch the config echo dropped and
# nothing restored, a channel that says ON and cannot reach its capability.
# All three produce a run that spends its whole budget and reads, afterwards,
# exactly like "the models had nothing to say".
log "=== PREFLIGHT: 60 typed gates over the compiled manifest and its runtime Config ==="
PREFLIGHT_ARGS=("$ROOT")
[ "${DRY_RUN:-0}" = "1" ] || PREFLIGHT_ARGS+=(--catalogue)
if ! python "$HERE/preflight_pa2.py" "${PREFLIGHT_ARGS[@]}" 2>&1 | tee -a "$LOG"; then
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
# client-side. The seat routes moved (reasoning and max_tokens both feed the
# provider profile), so a FULL battery is expected here rather than a cache
# hit off P-A1's home -- and this is a fresh home in any case.
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

# --- THE COMPOSITION STEP AT TERMINAL --------------------------------------
# A non-zero rc here is recorded and does NOT abort the audit -- a refusal is
# a typed result this tranche wants to read, not a reason to stop reading.
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
# Recorded for completeness AND as the contrast P4 depends on: this CLI
# prints the PROBLEM registry, not the artifact frontier.
python -m deepreason --root "$ROOT" frontier > "$HERE/frontier.txt" 2>&1 || true
python -m deepreason --root "$ROOT" report > "$HERE/report.txt" 2>&1 || true

# --- P2/P5: the typed OUTCOME census (P-A1's monitor could not see this) ----
log "=== AUDIT: transport/outcome census (monitor_pa2.py) ==="
python "$HERE/monitor_pa2.py" "$ROOT" > "$HERE/monitor_final.txt" 2>&1 || true
python "$HERE/monitor_pa2.py" "$ROOT" --json > "$HERE/monitor_final.json" 2>&1 || true
cat "$HERE/monitor_final.txt" | tee -a "$LOG" || true

# --- P4: the ARTIFACT Pareto frontier, both formulas ------------------------
# rescore.py, NOT the `frontier` CLI above. READ-ONLY: it opens the harness
# with read_only=True, because a writable open REPAIRS a root, which destroys
# the evidence a reader opened it to look at.
log "=== AUDIT: artifact Pareto frontier before/after (rescore.py) ==="
python "$REPO/experiments/2026-09-02-defect-coverage-pending-commitments/rescore.py" \
  "$ROOT" > "$HERE/rescore_pa2.txt" 2>&1 || true
cat "$HERE/rescore_pa2.txt" | tee -a "$LOG" || true

# --- the module-coverage census, from the typed record only -----------------
log "=== CENSUS: module coverage + the measured known-open defects ==="
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
