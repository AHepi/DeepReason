#!/usr/bin/env bash
# Rollback insurance for long live runs: commit and push whatever the
# self-study run has written under experiments/ every five minutes, then
# exit once the run's driver script is gone.
#
# Commits are path-scoped to experiments/ so concurrent source-tree work in
# the same checkout is never swept into a snapshot.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRANCH="claude/handover-package-committed-kw8imd"
LIVE_REL="experiments/live_research_2026-07-29"

cd "$REPO" || exit 1
while true; do
  sleep 300
  git add -A "$LIVE_REL" >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$LIVE_REL" 2>/dev/null; then
    git commit -q -m "Selfstudy snapshot ($(date -u +%FT%TZ))" -- "$LIVE_REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  pgrep -f "[s]elfstudy_run.sh" >/dev/null 2>&1 || break
done
echo "snapshot loop finished: selfstudy_run.sh no longer running"
