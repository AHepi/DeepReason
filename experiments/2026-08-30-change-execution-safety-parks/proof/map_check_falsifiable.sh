#!/bin/sh
# The new `check:` on DR-SUB-verification's self-report Trap has three clauses.
# `docs_verify --audit` refuses a check that cannot fail, so each clause is
# shown failing here. The mutations are applied to tests/test_sandbox_guard.py
# and reverted by a trap on every exit path, including interrupt; the last line
# compares the file against the copy taken before the first mutation, so a
# reader can see it restored whatever the tree's commit state.
#
# Clause 1 (the pytest run) is not re-proved here: `proof/mutation_proof.out`
# already shows all seven of those tests going RED under source mutations, and
# this check runs exactly those tests.
REPO=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$REPO"
TARGET=tests/test_sandbox_guard.py
BACKUP=$(mktemp)
cp "$TARGET" "$BACKUP"
trap 'cp "$BACKUP" "$TARGET"; rm -f "$BACKUP"' EXIT INT TERM

CHECK=$(python - <<'PY'
import pathlib
for line in pathlib.Path("docs/map/SUB-verification.md").read_text().splitlines():
    if line.startswith('`check: python -m pytest tests/test_sandbox_guard.py -q -k "denies_network'):
        print(line[len("`check: "):-1]); break
PY
)
echo "THE CHECK, verbatim from docs/map/SUB-verification.md:"
echo "  $CHECK"
echo
echo "--- unmutated: expect exit 0 ---"
sh -c "$CHECK" >/dev/null 2>&1; echo "exit=$?"

echo
echo "--- F1: one differential renamed away; the -eq 7 census must fail ---"
python - <<'PY'
import pathlib
p = pathlib.Path("tests/test_sandbox_guard.py")
t = p.read_text()
p.write_text(t.replace("def test_the_contained_child_really_receives_every_declared_rlimit",
                       "def retired_receives_every_declared_rlimit", 1))
PY
sh -c "$CHECK" >/dev/null 2>&1; echo "exit=$? (non-zero required)"
cp "$BACKUP" "$TARGET"

echo
echo "--- F2: a self-reported filesystem string asserted again; clause 3 must fail ---"
python - <<'PY'
import pathlib
p = pathlib.Path("tests/test_sandbox_guard.py")
t = p.read_text()
t = t.replace('    prefix = ContainedSimulationBackend.containment_prefix()\n'
              '    if not prefix:\n',
              '    assert ContainedSimulationBackend(toolchain_id="t", maximum_wall_ms=1,'
              ' maximum_memory_bytes=1).resource_limits()["filesystem"]'
              ' == "ephemeral scratch workdir"\n'
              '    prefix = ContainedSimulationBackend.containment_prefix()\n'
              '    if not prefix:\n', 1)
p.write_text(t)
PY
sh -c "$CHECK" >/dev/null 2>&1; echo "exit=$? (non-zero required)"
cp "$BACKUP" "$TARGET"

echo
echo "--- restored ---"
sh -c "$CHECK" >/dev/null 2>&1; echo "exit=$?"
cmp -s "$BACKUP" "$TARGET" && echo "restoration: byte-identical to the pre-run file" \
    || echo "restoration: DIFFERS -- the tree is dirty"
