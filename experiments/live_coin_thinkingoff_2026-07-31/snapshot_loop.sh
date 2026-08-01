#!/usr/bin/env bash
# Rollback insurance for this ladder: commit and push whatever the run has
# written under this experiment every five minutes, then exit once the
# driver script is gone. Commits are path-scoped so concurrent source-tree
# work in the same checkout is never swept into a snapshot.
set -u
DRIVER="${1:-coin_run.sh}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRANCH="${SNAPSHOT_BRANCH:-claude/amendment-epochs-om0ztb}"
LIVE_REL="experiments/live_coin_thinkingoff_2026-07-31"

cd "$REPO" || exit 1
while true; do
  sleep 300
  git add -A "$LIVE_REL" >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$LIVE_REL" 2>/dev/null; then
    git commit -q -m "${SNAPSHOT_LABEL:-Coin canonicity} snapshot ($(date -u +%FT%TZ))" -- "$LIVE_REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  pgrep -f "$DRIVER" >/dev/null 2>&1 || break
done
echo "snapshot loop finished: $DRIVER no longer running"
