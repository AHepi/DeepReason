#!/usr/bin/env bash
# Mutation proof for pilot rung T3. Authored by the MONITOR and deliberately
# OUTSIDE the T3 task cone (experiments/2026-08-23-treadle-pilot/T3/*), so the
# driver's model cannot rewrite its own judge.
#
# The behaviour under proof, from src/deepreason/informal/trial.py's own
# comment: in pairwise_discriminate, a NAMED winner whose decisive_point is
# the empty string must block on referential-integrity, "the empty string is
# a substring of everything, so it would otherwise pass vacuously".
#
# Exit 0 iff the candidate test is GREEN on the real tree and RED under the
# mutation that deletes the empty-string guard. A test that passes both ways
# does not test this behaviour, and this script fails it.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2

TARGET=src/deepreason/informal/trial.py
TESTS=(experiments/2026-08-23-treadle-pilot/T3/test_*.py)
GUARD='if not ruling1.decisive_point or ruling1.decisive_point not in f"{a_text}\n{b_text}":'
MUTANT='if ruling1.decisive_point not in f"{a_text}\n{b_text}":'

if [ ! -e "${TESTS[0]}" ]; then
    echo "MUTATION_PROOF: FAIL — no candidate test file in the T3 cone"; exit 1
fi

BACKUP=$(mktemp) || exit 2
cp "$TARGET" "$BACKUP"
restore() { cp "$BACKUP" "$TARGET"; rm -f "$BACKUP"; }
trap restore EXIT INT TERM

echo "--- 1/2: candidate must be GREEN on the unmutated tree"
if ! python -m pytest "${TESTS[@]}" -q; then
    echo "MUTATION_PROOF: FAIL — candidate is not green on the real tree"; exit 1
fi

echo "--- 2/2: candidate must be RED once the empty-string guard is deleted"
python3 - "$TARGET" "$GUARD" "$MUTANT" <<'PY'
import sys
path, guard, mutant = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(path, encoding="utf-8").read()
if s.count(guard) != 1:
    print(f"MUTATION_PROOF: FAIL - guard line found {s.count(guard)} times, expected 1")
    sys.exit(3)
open(path, "w", encoding="utf-8").write(s.replace(guard, mutant))
PY
rc=$?
[ $rc -eq 3 ] && exit 1
[ $rc -ne 0 ] && { echo "MUTATION_PROOF: FAIL - could not apply mutation"; exit 2; }

if python -m pytest "${TESTS[@]}" -q; then
    echo "MUTATION_PROOF: FAIL — candidate still passes with the guard deleted;"
    echo "it does not pin the behaviour it claims to pin."
    exit 1
fi

echo "MUTATION_PROOF: PASS — green on the real tree, red under the mutation."
exit 0
