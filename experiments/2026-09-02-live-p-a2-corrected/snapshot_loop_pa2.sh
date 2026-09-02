#!/usr/bin/env bash
# Rollback insurance for the P-A2 live run: commit and push whatever the run
# has written under this tranche every five minutes, then exit once the
# driver is gone.
#
# The container can roll back silently, killing background processes and
# deleting gitignored files, so work between pushes is work at risk.
#
# WATCHES BY PID FILE, NOT BY PATTERN. `pgrep -f <driver>` matches any command
# line containing that string -- including this loop's own, and including the
# operating session's shell. CLAUDE.md's process-hygiene rule ("kill by PID,
# never by pattern") is about the same hazard, and a watcher that mistakes
# itself for its subject never exits.
#
# Commits are path-scoped to this tranche so concurrent work in the same
# checkout is never swept into a snapshot. The env file is gitignored and
# cannot be committed by this loop.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
REL="experiments/2026-09-02-live-p-a2-corrected"
BRANCH="${SNAPSHOT_BRANCH:-claude/executor-live-run-p-a2-84hyco}"
PIDFILE="${PA2_PIDFILE:-$HERE/driver.pid}"

cd "$REPO" || exit 1
while true; do
  sleep 300
  git add -A "$REL" >/dev/null 2>&1 || true
  if ! git diff --cached --quiet -- "$REL" 2>/dev/null; then
    git commit -q -m "P-A2 live-run snapshot ($(date -u +%FT%TZ))" -- "$REL" >/dev/null 2>&1 || true
    for attempt in 1 2 3 4; do
      git push -u origin "$BRANCH" >/dev/null 2>&1 && break
      sleep $((2 ** attempt))
    done
  fi
  # The driver is gone when its recorded PID no longer names a live process.
  [ -f "$PIDFILE" ] || continue
  kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null || break
done
