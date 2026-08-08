#!/usr/bin/env bash
# Rollback insurance for the whole overnight omnibus tranche: commit
# and push everything under this experiment dir every five minutes,
# excluding any in-flight DEEPREASON_HOME run roots (a run mid-append
# must never be committed -- S6's Failure #4, mirrored here). Exits
# once NONE of the given driver name patterns (argv) are still
# running. Pass one pattern per block driver currently in flight, e.g.:
#   ./snapshot_loop.sh block_a_run.sh block_c_run.sh
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRANCH="${SNAPSHOT_BRANCH:-claude/overnight-omnibus-executor-5dw66r}"
LIVE_REL="experiments/2026-08-09-overnight-omnibus"
PATTERNS=("$@")
if [ "${#PATTERNS[@]}" -eq 0 ]; then
  PATTERNS=(block_a_run.sh block_b_run.sh block_c_run.sh block_d_run.sh)
fi

cd "$REPO" || exit 1
while true; do
  sleep 300
  git add -A -- "$LIVE_REL" \
    ":!$LIVE_REL/*/home-*/runs/**" \
    ":!$LIVE_REL/*/*/home-*/runs/**" \
    >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$LIVE_REL" 2>/dev/null; then
    git commit -q -m "Omnibus snapshot ($(date -u +%FT%TZ))" -- "$LIVE_REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  any_running=0
  for pat in "${PATTERNS[@]}"; do
    pgrep -f "$pat" >/dev/null 2>&1 && any_running=1
  done
  [ "$any_running" -eq 1 ] || break
done
echo "snapshot loop finished: none of [${PATTERNS[*]}] still running"
