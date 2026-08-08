#!/usr/bin/env bash
# Rollback insurance for this tranche's live run: commit and push whatever
# has been written under this experiment dir every five minutes, then
# exit once the driver script is gone. Pass the driver script name to
# watch as $1 (default phase1_run.sh). Mirrors
# experiments/2026-08-08-live-two-seat-ab-s6/snapshot_loop.sh.
set -u
DRIVER="${1:-phase1_run.sh}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRANCH="${SNAPSHOT_BRANCH:-claude/corpus-enrichment-patrol-pilot-f4khnk}"
LIVE_REL="experiments/2026-08-08-corpus-enrichment-patrol-pilot"

cd "$REPO" || exit 1
while true; do
  sleep 300
  # Exclude live run roots: a run mid-append must never be committed
  # (S6's Failure #4 -- an earlier version of this loop's blanket
  # `git add -A` caught an in-progress run root twice while `continue`
  # was still writing it). Everything else under the experiment dir
  # (scripts, env, logs, RESULTS.md, PARKED.md, audit JSON) is safe to
  # snapshot anytime. Completed roots are committed explicitly by the
  # driver's own per-root commit step, not swept in here.
  git add -A -- "$LIVE_REL" ":!$LIVE_REL/home/runs" >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$LIVE_REL" 2>/dev/null; then
    git commit -q -m "Corpus-enrichment pilot snapshot ($(date -u +%FT%TZ))" -- "$LIVE_REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  pgrep -f "$DRIVER" >/dev/null 2>&1 || break
done
echo "snapshot loop finished: $DRIVER no longer running"
