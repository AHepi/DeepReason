#!/usr/bin/env bash
# Rollback insurance for this tranche's long live run (CLAUDE.md
# "Environment": the cloud container can roll back silently). Commits and
# pushes whatever the run has written under this tranche directory every
# five minutes, then exits once the driver script is gone. Pass the driver
# script name to watch as $1 (default grounded_run.sh).
set -u
DRIVER="${1:-grounded_run.sh}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRANCH="${SNAPSHOT_BRANCH:-claude/controller-steering-parity-k49vte}"
TRANCHE_REL="experiments/2026-08-13-defect-controller-steering-inert"

cd "$REPO" || exit 1
while true; do
  sleep 300
  git add -A "$TRANCHE_REL" >/dev/null 2>&1 || true
  # The gitignored env file (experiments/*/env, .gitignore:48) is never
  # staged by this add, but guard explicitly anyway -- a credential leak
  # here is not a risk worth trusting to a glob pattern alone.
  git reset -q -- "$TRANCHE_REL/env" >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$TRANCHE_REL" 2>/dev/null; then
    git commit -q -m "Grounded-extension-expansion snapshot ($(date -u +%FT%TZ))" -- "$TRANCHE_REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  pgrep -f "$DRIVER" >/dev/null 2>&1 || break
done
echo "snapshot loop finished: $DRIVER no longer running"
