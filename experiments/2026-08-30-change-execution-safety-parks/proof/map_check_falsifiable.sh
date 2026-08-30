#!/bin/sh
# The `check:` on DR-SUB-verification's self-report Trap has three clauses, and
# a check has TWO ways to be wrong: it can fail to go red when the property it
# guards is gone, and it can go red when nothing regressed. Both are measured
# here. F1 and F2 must exit non-zero; F3 and F4 must exit ZERO.
#
# F3 and F4 exist because the first version of this check had both false-red
# modes, demonstrated by a batch-2 skeptic: clause 2 counted a NAME PREFIX
# pinned at 7, so any future `test_the_contained_*` reddened the map, and
# clause 3 banned the bare substring `network_denial`, which is also inside the
# OS-layer helpers `network_denial_available` / `network_denial_prefix` -- so an
# effect-based assertion on the helper, the very style this Trap demands,
# reddened the map too. Clause 2 now names the seven functions exactly and
# clause 3 matches the FIELD ACCESS `["network_denial"]` rather than the token.
#
# The mutations are applied to tests/test_sandbox_guard.py and reverted by a
# trap on every exit path, including interrupt; the last line compares the file
# against the copy taken before the first mutation, so a reader can see it
# restored whatever the tree's commit state.
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
echo "--- F3: a benign eighth test_the_contained_* is added; the check must STAY GREEN ---"
cat >> "$TARGET" <<'EOF'


def test_the_contained_backend_reports_a_stable_toolchain_id():
    backend = ContainedSimulationBackend(
        toolchain_id="python@x",
        maximum_wall_ms=20_000,
        maximum_memory_bytes=512 * 1024 * 1024,
    )
    assert backend.toolchain_id == "python@x"
EOF
sh -c "$CHECK" >/dev/null 2>&1; echo "exit=$? (ZERO required: nothing regressed)"
echo -n "  name-prefix census would have said: "
grep -c 'def test_the_contained\|def test_the_network_namespace\|def test_the_code_testing_worker_environment' "$TARGET"
cp "$BACKUP" "$TARGET"

echo
echo "--- F4: an effect-based assert on network_denial_available; the check must STAY GREEN ---"
cat >> "$TARGET" <<'EOF'


def test_a_future_effect_based_test_on_the_prefix_helper():
    from deepreason.sandbox_os import network_denial_available

    assert network_denial_available() is CONTAINMENT_AVAILABLE
EOF
sh -c "$CHECK" >/dev/null 2>&1; echo "exit=$? (ZERO required: nothing regressed)"
echo -n "  the bare-substring ban would have matched: "
grep -rcE "assert .*(ephemeral scratch workdir|network_denial)" "$TARGET"
cp "$BACKUP" "$TARGET"

echo
echo "--- restored ---"
sh -c "$CHECK" >/dev/null 2>&1; echo "exit=$?"
cmp -s "$BACKUP" "$TARGET" && echo "restoration: byte-identical to the pre-run file" \
    || echo "restoration: DIFFERS -- the tree is dirty"
