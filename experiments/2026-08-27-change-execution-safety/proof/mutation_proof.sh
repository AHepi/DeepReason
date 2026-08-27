#!/bin/sh
# The RED-then-GREEN obligation for the boundary fix, as a command rather than
# a claim: revert deepreason/sandbox_guard.py to the historical underscore-only
# rule, watch tests/test_sandbox_guard.py go red, restore, watch it go green.
#
# The mutation is the DEFECT, restated exactly: before 2026-08-27 every guard
# in this repository rejected leading-underscore attributes and nothing else.
set -e
GUARD=src/deepreason/sandbox_guard.py
BACKUP=$(mktemp)
cp "$GUARD" "$BACKUP"
trap 'cp "$BACKUP" "$GUARD"; rm -f "$BACKUP"' EXIT

python - <<'PY'
import pathlib, re
p = pathlib.Path("src/deepreason/sandbox_guard.py")
t = p.read_text()
t = re.sub(r'FORBIDDEN_ATTRIBUTE_PREFIXES: tuple\[str, \.\.\.\] = \([^)]*\)',
           'FORBIDDEN_ATTRIBUTE_PREFIXES: tuple[str, ...] = ("_",)', t, count=1)
t = t.replace('frozenset({"mro"})', 'frozenset()')
p.write_text(t)
PY

echo "=== RED: the historical underscore-only rule ==="
python -m pytest tests/test_sandbox_guard.py -q 2>&1 | tail -12 || true
cp "$BACKUP" "$GUARD"
echo
echo "=== GREEN: the boundary restored ==="
python -m pytest tests/test_sandbox_guard.py -q 2>&1 | tail -3
