#!/usr/bin/env bash
# Rollback insurance: commit+push this experiment dir every 5 minutes
# while the testphase driver is alive, then exit. Path-scoped so nothing
# else in the checkout is swept in; env is gitignored and never lands.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRANCH="${SNAPSHOT_BRANCH:-claude/handover-defect-audit-33pv3d}"
LIVE_REL="experiments/2026-08-05-testphase-live-validation"
cd "$REPO" || exit 1
while true; do
  sleep 300
  git add -A "$LIVE_REL"
  if ! git diff --cached --quiet; then
    git commit -q -m "testphase snapshot $(date -u +%FT%TZ)" && \
      git push -q origin "$BRANCH" || true
  fi
  pgrep -f testphase_run.sh >/dev/null || exit 0
done
