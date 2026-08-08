#!/usr/bin/env bash
# Rollback insurance for this rung's live run: commit and push whatever
# has been written under this experiment dir every five minutes, then
# exit once the driver script is gone. Pass the driver script name to
# watch as $1 (default s6_run.sh). Mirrors
# experiments/live_research_2026-07-29/snapshot_loop.sh.
set -u
DRIVER="${1:-s6_run.sh}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRANCH="${SNAPSHOT_BRANCH:-claude/s6-live-two-seat-ab}"
LIVE_REL="experiments/2026-08-08-live-two-seat-ab-s6"

cd "$REPO" || exit 1
while true; do
  sleep 300
  # Exclude live run roots: a run mid-append must never be committed
  # (Failure #4 -- an earlier version of this loop's blanket `git add -A`
  # caught an in-progress run root twice while `continue` was still
  # writing it). Everything else under the experiment dir (scripts, env,
  # logs, RESULTS.md, PARKED.md, audit JSON) is safe to snapshot anytime.
  git add -A -- "$LIVE_REL" ":!$LIVE_REL/home-s6/runs" >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$LIVE_REL" 2>/dev/null; then
    git commit -q -m "S6 snapshot ($(date -u +%FT%TZ))" -- "$LIVE_REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  pgrep -f "$DRIVER" >/dev/null 2>&1 || break
done
echo "snapshot loop finished: $DRIVER no longer running"
