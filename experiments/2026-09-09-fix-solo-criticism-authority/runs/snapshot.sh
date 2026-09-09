#!/bin/bash
# Commit-and-push loop for a long live run: the container can roll back and
# take every gitignored artifact with it (CLAUDE.md, Environment).
set -u
cd /home/user/DeepReason
D=experiments/2026-09-09-fix-solo-criticism-authority
B=claude/solo-model-criticism-authority-amn7qa
while true; do
  sleep 300
  git add -A "$D" 2>/dev/null
  if ! git diff --cached --quiet; then
    git commit -q -m "snapshot: live solo road $(date -u +%FT%TZ)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019XMzpVrS28NeV3WABFELZe" \
      && for i in 2 4 8 16; do git push -q origin "$B" && break || sleep $i; done
  fi
done
