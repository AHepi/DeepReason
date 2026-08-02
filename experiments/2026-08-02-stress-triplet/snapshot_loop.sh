#!/usr/bin/env bash
# Rollback insurance: commit+push this experiment dir every 5 minutes while
# any of the three ladders is alive. Path-scoped; never sweeps source work.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRANCH="${SNAPSHOT_BRANCH:-claude/amendment-epochs-om0ztb}"
REL="experiments/2026-08-02-stress-triplet"
cd "$REPO" || exit 1
while pgrep -f "ladder_common.sh" >/dev/null 2>&1; do
  sleep 300
  git add -A "$REL" >/dev/null 2>&1
  git diff --cached --quiet || {
    git commit -q -m "stress-triplet snapshot $(date -u +%FT%TZ)"
    git push -q origin "$BRANCH" || true
  }
done
git add -A "$REL" >/dev/null 2>&1
git diff --cached --quiet || {
  git commit -q -m "stress-triplet final snapshot $(date -u +%FT%TZ)"
  git push -q origin "$BRANCH" || true
}
