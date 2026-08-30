#!/usr/bin/env bash
# Remove road (a) -- the parked P2 change -- in one act, if the operator
# answers "b" or "c".
#
# Road (a) does NOT live in one droppable commit. `fe6b29ed2` built it, and
# the delivery commit that followed added a pytest node id and a symbol grep
# to two `docs/map/SUB-scheduler.md` check lines so the table's own promise
# ("every Test cell is a node id this check runs by name") stayed true. Both
# of those symbols exist only inside road (a), so reverting `fe6b29ed2` alone
# leaves two RED map checks. This script removes both halves together.
#
# It reverses THIS LANE's contribution to the road's files since the park
# base -- not the files' whole history -- so it fails loudly instead of
# clobbering if the tree it runs on has moved those hunks.
#
#   bash experiments/2026-08-30-defect-formalism-rank-penalty/drop_road_a.sh
#
# Exit 0  DROPPED       -- staged, verified; commit it.
# Exit 1  REFUSED       -- preconditions unmet; nothing was changed.
# Exit 2  DROP_UNSOUND  -- the removal applied but a check did not go green.
set -uo pipefail

BASE=736b50839                       # the commit before road (a) landed
LANE="${1:-claude/b2-lane-C}"        # this lane's tip; not a merged trunk

PATHS=(
  src/deepreason/capture/pareto.py
  src/deepreason/scheduler/scheduler.py
  tests/test_formalism_optional_rank.py
  docs/map/CON-conjecture-kinds.md
  docs/map/SUB-periphery.md
  docs/map/SUB-scheduler.md
  experiments/2026-08-27-audit-formalism-optional/repro_coverage_rank.py
  experiments/2026-08-30-defect-formalism-rank-penalty/measure_footprint.py
)

cd "$(git rev-parse --show-toplevel)" || exit 1

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "REFUSED: working tree or index is dirty. Commit or stash first."
  exit 1
fi
for ref in "$BASE" "$LANE"; do
  git rev-parse --verify --quiet "$ref^{commit}" >/dev/null || {
    echo "REFUSED: $ref does not resolve in this repository."; exit 1; }
done

if ! git diff "$BASE" "$LANE" -- "${PATHS[@]}" | git apply -R --index; then
  echo "REFUSED: the reverse patch did not apply. Road (a)'s hunks have moved"
  echo "on this tree; drop it by hand and re-run this script's checks below."
  exit 1
fi

fail=0
grep -q "^def pareto_scores(" src/deepreason/scheduler/scheduler.py && {
  echo "DROP_UNSOUND: pareto_scores is still defined."; fail=1; }
[ -e tests/test_formalism_optional_rank.py ] && {
  echo "DROP_UNSOUND: tests/test_formalism_optional_rank.py still exists."; fail=1; }

# The two check lines that go red if only fe6b29ed2 is reverted.
while IFS= read -r line; do
  cmd=${line#\`check: }; cmd=${cmd%\`}
  if bash -c "$cmd" >/dev/null 2>&1; then
    echo "green: ${cmd:0:72}..."
  else
    echo "DROP_UNSOUND: red after the drop: ${cmd:0:72}..."; fail=1
  fi
done < <(grep -E '^`check: (python -m pytest tests/test_scheduler.py::test_focus_family|for c in LIVENESS_QUEUE)' docs/map/SUB-scheduler.md)

[ "$fail" -ne 0 ] && exit 2

echo "DROPPED: road (a) is removed and staged; the two SUB-scheduler.md checks"
echo "that depend on it are green. Commit with:"
echo "  git commit -m 'drop road (a): the operator answered b or c'"
exit 0
