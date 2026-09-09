# Parked — noticed in this tranche, not this tranche's goal

## P1. Two docs_verify rows postdate the recorded baseline

WHAT: `docs/AUDIT_BASELINES.md` records 5 or 6 docs_verify failures on this
container (2026-08-30/31). Two serial runs on 2026-09-09 report 7, and the two
extra rows are newer than the baseline entry: `INV-frozen-surfaces.md:909`
(reads `origin/claude/deepreason-p-s1-commitments-wowcib`, a branch this clone
has not fetched) and `INV-frozen-surfaces.md:1274` (points at
`experiments/2026-09-06-change-writers-room-organiser-testing/runs/home-r/runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092`,
which `tools/record_claims.py` rejects: "no run-status.json (not a run root)").
Both are pre-existing on `origin/main`.

```
Route: dr-audit-orchestrator, dimension docs-drift (read-only).
One goal: decide, for each of the two docs_verify rows below, whether it is a
rotted check, a check that needs a committed artifact it does not have, or a
container-conditional row that belongs in the baseline list -- and update
docs/AUDIT_BASELINES.md's expected-failure table so a future delta is a finding
again.
Evidence: docs/AUDIT_BASELINES.md lines 40-70 (the baseline entry and its
expected-failure table, recording 5 or 6 on this container as of 2026-08-30/31);
experiments/2026-09-09-defect-organiser-seat-fixture-mismatch/VERIFY.md (two
serial runs at 7, with all seven rows classified and each reproduced at
origin/main with the tranche's change stashed).
The two rows: INV-frozen-surfaces.md:909 -- `python experiments/
2026-09-01-defect-judge-canary-compile-gap/price_compile_gap.py --expect fixed`
dies on `git show origin/claude/deepreason-p-s1-commitments-wowcib:...` exit
128; INV-frozen-surfaces.md:1274 -- `python tools/record_claims.py --claims
experiments/2026-09-06-change-writers-room-organiser-testing/claims.json --root
.../runs/home-r/runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092 --json` prints "no
run-status.json (not a run root)" and emits nothing for the JSON reader.
End state: AUDIT_BASELINES.md's table carries a row for each, with its class and
its disposition, or a fix prompt for whichever is a real rot. Read-only
otherwise: no check is edited in that tranche.
```

## P2. `record_claims.py` gives no typed failure when its root is missing

WHAT: the `INV-frozen-surfaces.md:1274` check pipes `tools/record_claims.py`
into a `json.load`. When the root is absent the tool prints a human sentence to
stderr and nothing to stdout, so the reader dies on
`JSONDecodeError: Expecting value: line 1 column 1` — a message that says
nothing about the actual cause. The check reports rot where the real fact is a
missing artifact.

```
Route: deepreason-orchestrator, starting at dr-set-goal.
One goal: `python tools/record_claims.py --claims <any> --root <a path that is
not a run root> --json` emits a typed refusal on stdout that a JSON reader can
parse and a map check can assert on, instead of an empty stdout and a prose
line on stderr.
Evidence: experiments/2026-09-09-defect-organiser-seat-fixture-mismatch/
VERIFY.md, the docs_verify section (the 1274 row and its reproduction at
origin/main); docs/map/INV-frozen-surfaces.md:1274 (the check that consumes it).
End state: the tool emits a typed object for the missing-root case, a
regression test pins it, and the map check reads the typed field.
Boundary: the tool and its test only -- do NOT relocate or re-point the map
check, and do NOT commit a run root to make the check pass.
```

## P3. No census of which tests read data under `experiments/`

WHAT: this defect exists because `tests/test_organiser_seat.py` is fixtured on
a data file inside `experiments/`, and the window that rewrote that file froze
`tests/` on the ground that `src/` was byte-untouched. Nothing in the repo says
which other test files have the same shape, so nothing tells the next window
which experiment directories are test inputs.

```
Route: dr-audit-orchestrator, dimension broken (read-only).
One goal: produce the list of test files under tests/ that read a path under
experiments/, and for each say what it reads and whether it copies a fact about
those bytes (a digest, a count, a rendered number) into the test file rather
than reading the published one.
Evidence: experiments/2026-09-09-defect-organiser-seat-fixture-mismatch/
DIAGNOSIS.md (the shape of the defect, and why a frozen-tests scope rule missed
it); the fixed file tests/test_organiser_seat.py as the worked example of the
repair.
End state: AUDIT_REPORT.md carries the list and a fix prompt per copied fact.
Findings only -- the audit family fixes nothing.
```
