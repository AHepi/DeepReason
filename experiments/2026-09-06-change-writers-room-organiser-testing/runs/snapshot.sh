#!/bin/bash
# Snapshot loop: commit and push the arms' roots and logs every 5 minutes
# while an arm runs, so a container rollback cannot take the record with it
# (CLAUDE.md, Environment). Never touches env (gitignored; checked first).
#   setsid nohup runs/snapshot.sh > runs/snapshot.log 2>&1 & disown
set -u
cd /home/user/DeepReason
D=experiments/2026-09-06-change-writers-room-organiser-testing
git check-ignore -q $D/env || { echo "REFUSED: $D/env is not ignored"; exit 9; }
while true; do
  sleep 300
  git add $D/runs 2>/dev/null
  if ! git diff --cached --quiet; then
    git commit -q -m "organiser arms: snapshot $(date -u +%FT%TZ)" && \
    for i in 1 2 3 4; do git push -q && break; sleep $((2**i)); done
  fi
  [ -f $D/runs/STOP_SNAPSHOT ] && exit 0
done
