#!/usr/bin/env bash
# P-C2b ARM H ladder: setup -> preflights -> qualify -> reason -> audit -> score.
#
# The design is frozen in PREREG.md; this script executes it and judges
# NOTHING. Every verdict in this tranche comes from a typed artifact
# (run-status.json, verify_root, findings.json, results.txt) or from the
# committed checker's output, never from this driver's own opinion.
#
# This is P-C1's `pc1_run.sh` with the builder and the preflight set changed
# and NOTHING ELSE, deliberately: a re-tuned ladder would put a second
# difference into a two-arm comparison that is meant to carry one.
#
# Launch detached from this directory:  setsid nohup ./pc2_run.sh & disown
# Offline rehearsal, no provider call:  DRY_RUN=1 ./pc2_run.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

ARM="H"; ARMLC="h"

if [ "${DRY_RUN:-0}" = "1" ]; then
  ROOT="$HERE/.dry-run-root"
  rm -rf "$ROOT"
else
  ROOT="${PC2B_ROOT:-$HERE/run}"
fi
LOG="${PC2B_LOG:-$HERE/driver.log}"

# P-C1's tranche directory. Every REUSED instrument is invoked from there and
# never copied here: a copy is a second thing to keep true, and "same checker"
# is the one property this rematch cannot afford to lose.
FRONTIER="$REPO/experiments/2026-08-25-change-constructive-frontier"

# PREREG.md §4: P-C1's own depth and cap, unchanged. The CYCLE budget is
# meant to bind first -- a token-bound stop truncates mid-cycle, a
# cycle-bound stop does not.
CYCLES="${CYCLES:-24}"
# PREREG §5: 200000 per arm, measured as total logged tokens.
TOKENS="${TOKENS:-200000}"

# Fresh DEEPREASON_HOME: isolates this tranche's admission store and
# qualification cache from P-C1's. PC2B_HOME lets the pre-authorized repeat
# (PREREG §8) use a different one, which it must -- run identity is
# deterministic, so the same question and config in the same home would
# refuse with RUN_ALREADY_STARTED.
export DEEPREASON_HOME="${PC2B_HOME:-$HERE/home}"

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

# Run identity is deterministic. A leftover root refuses relaunch with
# RUN_ALREADY_STARTED; retire it with `git mv run <state>-run-<id>` and
# COMMIT THE RENAME FIRST -- never edit or overwrite a committed root.
if [ -e "$ROOT" ]; then
  log "FATAL: $ROOT already exists -- retire it first (git mv), never overwrite -- rc=1"
  exit 1
fi

log "=== ARM $ARM (config run-config.yaml, reasoning ON, symmetric with arm_s_split.py) ==="
log "=== SETUP: build_manifest_pc2b.py -> $ROOT ==="
if ! python "$HERE/build_manifest_pc2b.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "SETUP FAILED -- rc=1"
  exit 1
fi
log "SETUP OK rc=0"

# THE TWO PREFLIGHTS THAT DECIDE WHETHER THIS RUN MEANS ANYTHING.
#
# P-C1's own: a malformed `predicate:` is a REFUTATION, not an error --
# `programs.evaluate` catches every exception and returns `fail`. A typo in
# criteria.py would refute every artifact silently, and the finished record
# would read exactly like "the model could not construct anything". P-C1
# lost a whole run to the JSON-envelope version of that.
log "=== PREFLIGHT: criteria discrimination + malformed-predicate guard ==="
if ! python "$FRONTIER/preflight_criteria.py" 2>&1 | tee -a "$LOG"; then
  log "PREFLIGHT FAILED (the battery is malformed or does not discriminate) -- rc=1"
  exit 1
fi
log "PREFLIGHT OK rc=0"

# P-C2's own: the rebuilt organ must actually be ON at RUNTIME. PREREG §3
# FINDING F-A -- the discharge policy is popped from the manifest's config
# echo, so a run reads the CODE DEFAULT. A P-C2 with the channel off would
# be a second P-C1 wearing P-C2's name and nothing typed would say so.
log "=== PREFLIGHT: question frozen, one-field delta, CHANNEL LIVE, manifest delta accounted ==="
if ! python "$HERE/preflight_pc2b.py" "$ROOT" 2>&1 | tee -a "$LOG"; then
  log "P-C2 PREFLIGHT FAILED -- rc=1"
  exit 1
fi
log "P-C2 PREFLIGHT OK rc=0"

log "=== PREFLIGHT: the checker's own mutation table ==="
if ! python "$FRONTIER/mutation_proof.py" 2>&1 | tee -a "$LOG"; then
  log "CHECKER MUTATION PROOF FAILED -- rc=1"
  exit 1
fi
log "CHECKER OK rc=0"

# REUSED, and deliberately NOT invoked in place. `preflight_models.py` writes
# `preflight_models.json` beside its own __file__, so running it from P-C1's
# directory OVERWRITES P-C1's COMMITTED EVIDENCE with this run's catalogue --
# which it did on the first P-C2 launch (catalogue_size 19 -> 20), restored
# with `git checkout`. A committed root's contents are never edited, and that
# rule covers a committed tranche's preflight output too. Copying the source
# to a shim in THIS directory keeps the reuse (the bytes are read at run time,
# so the two can never drift) while landing the output where it belongs.
log "=== PREFLIGHT: the seat model exists in the live catalogue ==="
if ! python "$HERE/run_model_preflight.py" 2>&1 | tee -a "$LOG"; then
  log "MODEL PREFLIGHT FAILED (a seat names a model the provider does not list) -- rc=1"
  exit 1
fi
log "MODEL PREFLIGHT OK rc=0"

if [ "${DRY_RUN:-0}" = "1" ]; then
  rm -rf "$ROOT"
  log "DRY RUN: stopping before qualify -- no provider call made, rehearsal root removed, rc=0"
  exit 0
fi

# Ollama Cloud concurrency is per ACCOUNT and plan-gated: own the limit
# client-side.
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
  log "QUALIFY FAILED rc=$rc -- see $HERE/qualify.json and $HERE/qualify.stderr.log"
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
# `results` takes its target POSITIONALLY; addressing it with --root falls
# back to DEEPREASON_HOME and records a path error instead of the summary.
python -m deepreason results "$ROOT" > "$HERE/results-$ARMLC.txt" 2>&1 || true

# Score every candidate the run produced with the OFFLINE EXACT checker.
# The in-run battery is float64 and is an admission gate; this is the
# authority for every number RESULTS.md quotes.
log "=== SCORE: the exact checker over every artifact in the record ==="
python "$FRONTIER/score_run.py" "$ROOT" > "$HERE/arm_${ARMLC}_scores.json" 2>&1 || true
python -c "
import json,pathlib
d=json.loads(pathlib.Path('$HERE/arm_h2_scores.json').read_text())
print('ARM H2 best valid score:', d.get('best_score'))
print('ARM H2 candidates:', d.get('n_candidates'), ' refuted:', d.get('n_refuted'))
" 2>&1 | tee -a "$LOG" || true

# T_H for PREREG §5's matched-budget rule, from W6's committed instrument.
# NOT from `deepreason results`: P-C1's counter printed 0 after 292 provider
# calls and that tranche parked it as P2.
log "=== T_H: provider-counted tokens, from W6's flow scan ==="
python - "$ROOT" > "$HERE/arm_${ARMLC}_tokens.json" 2>&1 <<'PYTOK' || true
import json, os, sys
sys.path.insert(0, "experiments/2026-08-26-run-anatomy-program/W6-token-flow")
import flow
root = os.path.relpath(sys.argv[1], os.getcwd())
rows = flow.scan_root(root).get("rows") or []
print(json.dumps({
    "root": root,
    "llm_calls": len(rows),
    "T_H": sum(r["total_tokens"] for r in rows),
}, indent=1, sort_keys=True))
PYTOK
cat "$HERE/arm_${ARMLC}_tokens.json" | tee -a "$LOG" || true

log "=== DONE (ARM $ARM): ARM S is a SEPARATE step -- see pc2b_arm_s.sh ==="
