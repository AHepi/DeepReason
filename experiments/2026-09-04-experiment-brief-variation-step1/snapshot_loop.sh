#!/usr/bin/env bash
# Rollback insurance. The container can roll back to a stale checkout at any
# time and takes every gitignored and uncommitted file with it, so a live arm's
# root is only safe once it is pushed. Commits and pushes this tranche's
# directory every five minutes, then exits when the watched driver is gone.
#
# Path-scoped to this tranche so concurrent work in the same checkout is never
# swept into a snapshot. The credential file is gitignored (`experiments/**/env`)
# and cannot be picked up by `git add -A` here.
set -u
DRIVER="${1:-arm.sh}"
REPO="/home/user/DeepReason"
REL="experiments/2026-09-04-experiment-brief-variation-step1"
BRANCH="${SNAPSHOT_BRANCH:-claude/brief-variation-harness-experiment-fhv8qu}"

cd "$REPO" || exit 1
while true; do
  sleep 300
  git add -A "$REL" >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$REL" 2>/dev/null; then
    git -c user.email=aaron_thyne@outlook.com -c user.name="Claude" \
      commit -q -m "step-1 snapshot ($(date -u +%FT%TZ))" -- "$REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  pgrep -f "$DRIVER" >/dev/null 2>&1 || break
done
echo "snapshot loop finished: $DRIVER no longer running"
