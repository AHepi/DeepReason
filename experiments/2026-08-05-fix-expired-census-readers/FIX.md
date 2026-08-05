# Fix: state the property, not the census — four readers stop pinning a root count

Guarantee restored: **a reader of the committed record asserts what must
be true of every root forever (absence is valid, presence is
well-formed, some roots refuse, "raising" ≠ "no manifest"), never how
many roots there happen to be today.**

## The design rule this applies

Every one of the four instruments already had a correct claim in its
prose or docstring; each then asserted a census as a proxy for it. The
fix restates each assertion as the claim it was standing in for. Nothing
is deleted, and nothing becomes vacuous — the partition is
self-identifying, because a stamped root carries
`module-fingerprints.v1` in its own record and an unstamped one does
not, so the reader can split the roots without naming any of them.

## Change sites (exhaustive)

- `tests/test_module_fingerprints.py`, `_sweep_committed_roots` (the
  `assert recorded_module_fingerprints(harness) == (), root` line):
  stop asserting absence for every root. Return the partition —
  `(unstamped, stamped, refused)` — so the two claims can be asserted
  separately by the tests that own them.
- `tests/test_module_fingerprints.py`,
  `test_every_committed_root_reads_as_having_no_module_fingerprints`:
  rename to reflect the real claim and assert BOTH halves — every
  unstamped root reads as absence-not-error (floor, `> 20`), and every
  stamped root's payload is well-formed (`schema_`, non-empty
  `modules`, digest present). Reading the same roots the old assertion
  read; asserting what the docstring always said.
- `tests/test_module_fingerprints.py`,
  `test_the_census_of_committed_roots_is_unchanged`: **assertions
  unchanged** — they are already a partition identity, an existence
  claim and a floor, none of which expires. Only the helper's return
  shape changes, so the call site is updated.
- `docs/map/SEAM-harness-x-verification.md:253`: replace
  `len(R)==45 and c[0]==28 and c[1]==14 and c[2]==3` with the claim the
  surrounding prose actually makes — pre-v6 roots are EXPECTED to
  refuse and are not a regression: `c[1] > 0`, all three kinds are
  non-empty, and the three kinds partition the tracked roots exactly
  (`c[0]+c[1]+c[2] == len(R)`). Prose updated to state why a count is
  not pinned, and to stop repeating ERRATA E5's misidentification (see
  below).
- `docs/map/SEAM-manifest-x-schools.md:271`: replace `len(roots)==42`
  and `(n,m)==(11,3)` with the claim its prose makes — "counting roots
  older than v6 gives 14 and is the wrong baseline": assert `n > 0`,
  `m > 0`, and `n != n + m`, i.e. the two sets are genuinely different
  and neither is empty.

## Regression artifact

`experiments/2026-08-05-fix-expired-census-readers/repro.py` must keep
printing all four properties `True` (it is a measurement, so it does
not invert), and the two tests must pass **with the absence claim still
asserted**, which the pre-fix worktree experiment showed is NOT what
merely deleting the line achieves.

New conditions this fix must be tested against, beyond the existing
reproduction:

1. **The stamped half is actually exercised.** A fix that only relaxed
   the absence assertion would pass today with `stamped == 2` and would
   pass equally with `stamped == 0` — vacuous the moment the two rung-5
   roots are the only witnesses. The test must assert `stamped` is
   non-empty, so the claim has a witness or the test fails.
2. **Mutation proof for the map checks.** Per `DR-SCHEMA`'s
   falsification rules and `--audit`'s doctrine, each rewritten check
   must be shown to fail against a deliberately broken tree before it
   is written down — a check that passes when all roots are v6, or when
   the two sets are merged, is not a check.

## Existing tests at risk

From `grep -rn "_sweep_committed_roots\|recorded_module_fingerprints" tests/`:

- `tests/test_module_fingerprints.py` — the only file using the helper.
  Its other 18 tests do not call it and must keep passing UNCHANGED.
- No other test file references `_sweep_committed_roots`. The
  `recorded_module_fingerprints` reader itself is not modified, so
  every test of the reader's behaviour is untouched.

No fixture is being updated to accommodate defective behaviour: the
production reader (`src/deepreason/module_events.py`) does not change at
all, so there is nothing for a fixture to have depended on.

## Explicitly not changed

- **`src/` — nothing.** The reader is correct; only its callers'
  assertions were wrong. This tranche writes zero production lines,
  which is the strongest available form of "fix the readers, not the
  roots".
- **The run roots.** Not renamed, retired, gitignored or edited
  (GOAL.md's NOT-in-scope; the operator's instruction).
- **`docs/ERRATA.md`.** E5's misidentification of which roots are the
  no-manifest three is real (PARKED P1a) and out of scope; the rewritten
  prose in both map documents states the measured truth so nothing this
  tranche ships depends on E5, but the ledger entry is a separate job.
- **`Verified-at:` stamps** of the two map documents: NOT advanced. This
  tranche re-runs the two checks it rewrites, not each document's full
  check set. A stale stamp is honest; a false one is not.
- **The packaging-surface smoke ring** (`scripts/wheel_smoke.py`), newly
  required by `dr-implement-fix` as of `20f2c8d1`: checked and does not
  apply — no change site touches pyproject entry points, CLI commands,
  MCP tools/schema, or wheel layout.

## Estimated diff

~55 lines across 3 files (≈30 in `tests/test_module_fingerprints.py`,
≈12 and ≈12 in the two map documents). Well under the 150-line budget.

## Approval gate

GOAL.md class is `defect`; the estimate is ≤150 lines; no frozen surface
is touched (no `src/` change at all, and none of the five surfaces is
among the change sites). **Proceeds to `dr-implement-fix`** without
operator approval, per this skill's gate.
