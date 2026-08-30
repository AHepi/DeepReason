#!/bin/sh
# Evidence for PARKED.md S5, road C — priced, not implemented.
#
# CLAIM UNDER TEST: `tests/test_schema_carries_every_prose_rule.py:170`'s bare
# `import jsonschema` runs twelve lines above the module's own
# `pytest.importorskip("jsonschema", ...)` at :182, so that guard has never
# been able to do its job; deleting line 170 alone makes the suite run on a
# container with no `jsonschema` at all.
#
# `jsonschema` is HIDDEN rather than uninstalled -- four sibling lanes share
# this box. The hiding must be FAITHFUL, and the first attempt was not: a stub
# package that raises a bare `ImportError` is a BROKEN module, not an absent
# one, and pytest 9's `importorskip` re-raises it. Absence is a
# `ModuleNotFoundError` from the import system, so this uses a `sys.meta_path`
# finder that raises exactly that. Recorded because the distinction is the
# whole point of the road being tested.
#
# The line deletion is applied to the repository file and reverted by a trap on
# every exit path; the last lines compare the file against the copy taken
# before the mutation and re-run the test unmutated.
REPO=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$REPO"
TARGET=tests/test_schema_carries_every_prose_rule.py
NODE="$TARGET::test_alias_bearing_fields_name_their_legal_values_in_the_schema"
BACKUP=$(mktemp)
HIDE=$(mktemp -d)
cp "$TARGET" "$BACKUP"
cat > "$HIDE/sitecustomize.py" <<'PY'
import sys


class _Absent:
    def __init__(self, name):
        self.name = name

    def find_spec(self, fullname, path=None, target=None):
        if fullname == self.name or fullname.startswith(self.name + "."):
            raise ModuleNotFoundError(f"No module named {self.name!r}", name=fullname)
        return None


sys.meta_path.insert(0, _Absent("jsonschema"))
PY
trap 'cp "$BACKUP" "$TARGET"; rm -rf "$BACKUP" "$HIDE"' EXIT INT TERM

echo "the two lines, as committed:"
sed -n '170p;182p' "$TARGET"

echo
echo "the blocker is faithful: absence, not breakage"
PYTHONPATH="$HIDE" python -c "
try:
    import jsonschema
except BaseException as error:
    print('   import jsonschema ->', type(error).__name__ + ':', error)
"

echo
echo "--- A: jsonschema present (this container): passes either way ---"
python -m pytest "$NODE" -q 2>&1 | tail -2

echo
echo "--- B: jsonschema absent, file UNCHANGED: the guard cannot help ---"
PYTHONPATH="$HIDE" python -m pytest "$NODE" -q -rs 2>&1 | tail -4

echo
echo "--- C: jsonschema absent, line 170 deleted: the guard works, test SKIPS ---"
python - <<'PY'
import pathlib
p = pathlib.Path("tests/test_schema_carries_every_prose_rule.py")
lines = p.read_text().splitlines(keepends=True)
assert lines[169].strip() == "import jsonschema", lines[169]
del lines[169]
p.write_text("".join(lines))
PY
PYTHONPATH="$HIDE" python -m pytest "$NODE" -q -rs 2>&1 | tail -4
cp "$BACKUP" "$TARGET"

echo
echo "--- restored ---"
cmp -s "$BACKUP" "$TARGET" && echo "restoration: byte-identical to the pre-run file" \
    || echo "restoration: DIFFERS -- the tree is dirty"
python -m pytest "$NODE" -q 2>&1 | tail -2

echo
echo "NOTE, and it limits road C: this closes the jsonschema half only."
echo "\`-n 4\` still needs pytest-xdist, which no import can guard."
