#!/bin/sh
# The RED-then-GREEN obligations for this tranche, as commands rather than
# claims. Two mutations, each restating a real prior state of the tree.
#
#   M1  the attribute boundary reverted to the historical underscore-only rule
#       -- the defect this tranche found. tests/test_sandbox_guard.py must go
#       red, because a fix nothing can falsify is not a fix.
#
#   M2  the simulation runner default reverted to `declarative` -- the state
#       that made model-authored code execution unreachable for four live
#       epochs. tests/test_simulation_runner_default.py must go red, including
#       the end-to-end admission through the real controller.
#
# Both mutations are reverted on exit, including on interrupt.
set -e

GUARD=src/deepreason/sandbox_guard.py
POLICY=src/deepreason/v6_policy.py
GUARD_BACKUP=$(mktemp)
POLICY_BACKUP=$(mktemp)
cp "$GUARD" "$GUARD_BACKUP"
cp "$POLICY" "$POLICY_BACKUP"
trap 'cp "$GUARD_BACKUP" "$GUARD"; cp "$POLICY_BACKUP" "$POLICY"; rm -f "$GUARD_BACKUP" "$POLICY_BACKUP"' EXIT INT TERM

echo "########################################################################"
echo "# M1: the attribute boundary reverted to the historical underscore rule"
echo "########################################################################"
python - <<'PY'
import pathlib, re
p = pathlib.Path("src/deepreason/sandbox_guard.py")
t = p.read_text()
t = re.sub(r'FORBIDDEN_ATTRIBUTE_PREFIXES: tuple\[str, \.\.\.\] = \([^)]*\)',
           'FORBIDDEN_ATTRIBUTE_PREFIXES: tuple[str, ...] = ("_",)', t, count=1)
t = t.replace('frozenset({"mro"})', 'frozenset()')
p.write_text(t)
PY
echo "--- RED expected ---"
python -m pytest tests/test_sandbox_guard.py -q 2>&1 | tail -12 || true
cp "$GUARD_BACKUP" "$GUARD"
echo "--- GREEN restored ---"
python -m pytest tests/test_sandbox_guard.py -q 2>&1 | tail -3

echo
echo "########################################################################"
echo "# M2: the simulation runner default reverted to 'declarative'"
echo "########################################################################"
python - <<'PY'
import pathlib
p = pathlib.Path("src/deepreason/v6_policy.py")
t = p.read_text()
assert 'DEFAULT_SIMULATION_RUNNER = "contained"' in t
p.write_text(t.replace('DEFAULT_SIMULATION_RUNNER = "contained"',
                       'DEFAULT_SIMULATION_RUNNER = "declarative"', 1))
PY
echo "--- RED expected ---"
python -m pytest tests/test_simulation_runner_default.py -q 2>&1 | tail -12 || true
cp "$POLICY_BACKUP" "$POLICY"
echo "--- GREEN restored ---"
python -m pytest tests/test_simulation_runner_default.py -q 2>&1 | tail -3
