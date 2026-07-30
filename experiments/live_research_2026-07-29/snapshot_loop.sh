#!/usr/bin/env bash
# Rollback insurance for long live runs: commit and push whatever the
# watched run has written under experiments/ every five minutes, then
# exit once the run's driver script is gone. Pass the driver script name
# to watch as $1 (default selfstudy_run.sh).
#
# Commits are path-scoped to experiments/ so concurrent source-tree work in
# the same checkout is never swept into a snapshot.
#
# SNAPSHOT_BRANCH overrides the push target for ladders run from a
# different working branch; the default preserves the original caller.
set -u
DRIVER="${1:-selfstudy_run.sh}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRANCH="${SNAPSHOT_BRANCH:-claude/handover-package-committed-kw8imd}"
LIVE_REL="experiments/live_research_2026-07-29"

cd "$REPO" || exit 1
while true; do
  sleep 300
  git add -A "$LIVE_REL" >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$LIVE_REL" 2>/dev/null; then
    git commit -q -m "${SNAPSHOT_LABEL:-Selfstudy} snapshot ($(date -u +%FT%TZ))" -- "$LIVE_REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  pgrep -f "$DRIVER" >/dev/null 2>&1 || break
done
echo "snapshot loop finished: $DRIVER no longer running"
