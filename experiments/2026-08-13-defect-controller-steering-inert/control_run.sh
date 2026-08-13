#!/usr/bin/env bash
# CONTROL for the three cycle-0 seat failures: the identical ladder, the
# identical compiled config, run against PRE-FIX code (origin/main, checked
# out at ../../prefix-wt) via PYTHONPATH.
#
# The manifest is compiled by the working tree's build_manifest.py, which is
# fine and checkable: manifest compilation is untouched by this tranche, and
# the script asserts the resulting sha is the same 8e22d0431fd2b98d... the
# grounded root and all three epochs produced. Only the RUN uses pre-fix code.
#
# Reads: if this ALSO fails at cycle 0 with V6_ROUTE_SEAT_INSUFFICIENT_
# CAPABILITY, the cause is environmental and this tranche is exonerated. If it
# SUCCEEDS, the fix is implicated and the tranche returns to dr-diagnose.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PREFIX_SRC="$REPO/prefix-wt/src"
ROOT="$HERE/control-run"
LOG="$HERE/control-driver.log"

export DEEPREASON_HOME="$HERE/control-home"
export PYTHONPATH="$PREFIX_SRC${PYTHONPATH:+:$PYTHONPATH}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

cd "$REPO"

if [ ! -d "$PREFIX_SRC" ]; then
  log "FATAL: pre-fix worktree missing at $PREFIX_SRC -- rc=1"; exit 1
fi
if PYTHONPATH="$PREFIX_SRC" python -c "
import deepreason.controller as c, sys
sys.exit(0 if not hasattr(c,'cap_envelope') else 1)"; then
  log "CONTROL CONFIRMED: loaded controller has no cap_envelope (pre-fix)"
else
  log "FATAL: PYTHONPATH did not select pre-fix code -- rc=1"; exit 1
fi

set -a
# shellcheck disable=SC1090
source "$HERE/env"
set +a

if [ -e "$ROOT" ]; then
  log "FATAL: $ROOT exists -- retire it first -- rc=1"; exit 1
fi

log "=== SETUP: build_manifest.py -> $ROOT ==="
python "$HERE/build_manifest.py" "$ROOT" 2>&1 | tee -a "$LOG"
SHA=$(python -c "
import json;print(json.load(open('$ROOT/run-manifest.sha256'.replace('.sha256','.json')) ) and open('$ROOT/run-manifest.sha256').read().strip())" 2>/dev/null || cat "$ROOT/run-manifest.sha256")
log "manifest sha: $SHA"
case "$SHA" in
  8e22d0431fd2b98d*) log "SAME CONFIG as the grounded root and all three epochs" ;;
  *) log "FATAL: manifest sha differs -- the control is not comparable -- rc=1"; exit 1 ;;
esac

log "=== QUALIFY: production-contract doctor (concurrency=2) ==="
export DEEPREASON_QUALIFY_CONCURRENCY=2
python -m deepreason doctor \
    --run-manifest "$ROOT/run-manifest.json" \
    --production-contracts \
    --out "$ROOT/production-contract-qualification.json" \
    > "$HERE/control-qualify.json" 2> "$HERE/control-qualify.stderr.log" \
  && log "QUALIFY OK rc=0" || { log "QUALIFY FAILED rc=$? "; exit 1; }

log "=== REASON (PRE-FIX CODE): --budget cycles=12 --token-budget 500000 ==="
if python -m deepreason --root "$ROOT" run \
    --run-manifest "$ROOT/run-manifest.json" \
    --problem "$ROOT/problem.json" \
    --budget cycles=12 \
    --token-budget 500000 \
    > "$HERE/control-reason.log" 2> "$HERE/control-reason.stderr.log"; then
  log "REASON rc=0"
else
  log "REASON rc=$? -- audit the typed stop before calling it a failure"
fi

log "=== AUDIT ==="
python -c "
import json;from deepreason.invariants import verify_root
print(json.dumps(verify_root('$ROOT')['violations']))" > "$HERE/control-verify_root.json" 2>&1 || true
python "$HERE/steering_evidence.py" "$ROOT" > "$HERE/control-steering_evidence.txt" 2>&1 || true
log "=== DONE ==="
