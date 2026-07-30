#!/usr/bin/env bash
# Workflow-enforcement guard: a branch that changes production code or
# tests must also carry tranche artifacts (the paper trail the
# .claude/skills workflows mandate). Run before push; exits non-zero
# with an explanation when the trail is missing.
set -u
BASE="${1:-origin/main}"
git fetch origin main -q 2>/dev/null || true
RANGE="$(git merge-base "$BASE" HEAD 2>/dev/null || echo "$BASE")..HEAD"
CHANGED=$(git diff --name-only $RANGE 2>/dev/null)
echo "$CHANGED" | grep -qE '^(src/|tests/)' || exit 0   # no code change: pass
if echo "$CHANGED" | grep -qE '(GOAL|REQUEST|SPEC|CHECKLIST|DIAGNOSIS|REPRO|FIX|VALIDATION|VERIFY|DELIVERY)\.md$'; then
  exit 0
fi
cat >&2 <<'MSG'
TRANCHE_ARTIFACTS_MISSING: this branch changes src/ or tests/ but carries
none of the workflow paper trail (GOAL/DIAGNOSIS/REPRO/FIX/VERIFY.md for
defects, REQUEST/SPEC/CHECKLIST/VALIDATION/DELIVERY.md for changes).
Route the work through deepreason-orchestrator or dr-change-orchestrator
(.claude/skills/) and commit the tranche directory before pushing.
MSG
exit 2
