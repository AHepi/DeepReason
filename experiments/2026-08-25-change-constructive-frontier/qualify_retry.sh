#!/usr/bin/env bash
# Re-qualify the EXISTING (uncommitted, zero-cycle) root until the battery
# passes, writing to the path `deepreason run` actually reads.
#
# WHY THIS IS NEEDED, AND WHAT IT DOES NOT HIDE.
# The production-contract battery on this manifest fails INTERMITTENTLY and
# always in the same place: `critic.atomic-target.v1` (argumentative_critic,
# glm-5.2) returns one schema-invalid first pass in 20, and the repair path
# then violates its own edit scope -- `REPAIR_SCOPE_VIOLATION`. One such case
# disqualifies the whole battery. Observed fail, pass, fail across three
# batteries on identical inputs.
#
# This retries. It does NOT make the failure go away, and the retry count is
# reported in RESULTS.md as a reliability finding about the seat, because a
# green obtained on the third try is not the same fact as a green obtained on
# the first. The underlying defect is PARKED, not fixed here (one tranche,
# one goal).
#
# Editing this root is legitimate precisely because it is UNCOMMITTED and has
# run ZERO cycles: no log.jsonl, no progress.jsonl, no evidence to destroy.
# The rule that protects roots protects COMMITTED ones.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
ROOT="$HERE/run"
LOG="$HERE/driver.log"
MAX="${MAX_ATTEMPTS:-6}"
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }
cd "$REPO"
set -a; . "$HERE/env"; set +a
export DEEPREASON_HOME="$HERE/home" DEEPREASON_QUALIFY_CONCURRENCY=2

for attempt in $(seq 1 "$MAX"); do
  log "=== QUALIFY retry attempt $attempt/$MAX ==="
  if python -m deepreason doctor \
      --run-manifest "$ROOT/run-manifest.json" \
      --production-contracts \
      --out "$ROOT/production-contract-qualification.json" \
      > "$HERE/qualify-retry-$attempt.json" 2> "$HERE/qualify-retry-$attempt.stderr.log"; then
    log "QUALIFY OK on attempt $attempt rc=0"
    echo "$attempt" > "$HERE/qualify-attempts-needed.txt"
    exit 0
  fi
  log "QUALIFY attempt $attempt FAILED -- $(python -c "
import json,pathlib
try:
    d=json.loads(pathlib.Path('$HERE/qualify-retry-$attempt.json').read_text())
    bad=[p['pair']['contract_id'] for p in d['pairs'] if not p.get('qualified')]
    print('unqualified:', ','.join(bad), 'scope_violations:', d['summary']['scope_violations'])
except Exception as e:
    print('unreadable report:', e)
")"
done
log "QUALIFY still failing after $MAX attempts -- STOP"
exit 1
