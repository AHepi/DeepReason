#!/usr/bin/env bash
# Rollback insurance for this tranche's long live run (CLAUDE.md
# "Environment": the cloud container can roll back silently, killing
# background processes and deleting gitignored files). Commits and pushes
# whatever the run has written under this tranche directory every five
# minutes, then exits once the driver process is gone.
#
# Takes the driver's PID as $1, NOT a name to pattern-match. dr-drive-harness
# §5b: pgrep -f / pkill -f can match the watcher's own command line, and a
# loop that mistakes itself for its subject never exits. `kill -0 <pid>` asks
# the kernel about one specific process and cannot be fooled by a substring.
set -u
DRIVER_PID="${1:?usage: snapshot_loop.sh <driver-pid>}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRANCH="${SNAPSHOT_BRANCH:-claude/epoch3-second-lineage-907gie}"
TRANCHE_REL="experiments/2026-08-22-change-epoch3-second-lineage"

cd "$REPO" || exit 1
while true; do
  sleep 300
  git add -A "$TRANCHE_REL" >/dev/null 2>&1 || true
  # The gitignored env file (experiments/*/env, .gitignore:48) is never
  # staged by this add, but guard explicitly anyway -- a credential leak here
  # is not a risk worth trusting to a glob pattern alone.
  git reset -q -- "$TRANCHE_REL/env" >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$TRANCHE_REL" 2>/dev/null; then
    git commit -q -m "Epoch-3 live-run snapshot ($(date -u +%FT%TZ))" -- "$TRANCHE_REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  kill -0 "$DRIVER_PID" 2>/dev/null || break
done
echo "snapshot loop finished: driver pid $DRIVER_PID is gone"
