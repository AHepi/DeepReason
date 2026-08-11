# Consolidated decision sheet — Items 3-6, all STOPs in one place

Everything below is committed, DESIGN-ONLY (zero code shipped, zero
frozen surfaces touched), and waiting on your words. Recommendations
are marked; nothing proceeds without an explicit answer.

## Q1 — the spec update (Item 3)

Six of eight surfaces your program named (seats, the seat-binding
schema, the v7 wire contract, candidate_checker, school-seat routing,
adjudication-blindness/blind-judge structure, config referee) are real
and shipped on `main` today but never mentioned in the harness spec
(v1.3 + v1.4/v1.5/v1.6). Two (`LEGACY_CRITICISM_ENABLED`,
`SCHOOL_SEATS_ENABLED`) exist only on the still-unmerged adjudication
branch.

**Draft a new v1.7 amendment now, covering the six on-`main` surfaces,
deferring the two branch-only flags to a later amendment once that
branch merges?** *(Recommended — waiting helps nothing; the six are
already real and already undocumented.)* Or wait for the branch to
merge and cover all eight at once?

## Q2 — docs reorganization (Item 6)

`docs/` has 100 files and several coexisting naming styles, but only
one document is actually declared superseded, and the load-bearing
paths (the map's 854 automated checks, the errata ledgers, the spec
series) are clearly identifiable and would not need to move.

**Add one new `docs/INDEX.md` navigation page now (zero renames, zero
risk), and treat any actual file moves as a separate future
tranche?** *(Recommended.)* Or do more now, or wait?

## Q3 — how far does "per role" go? (Item 4)

Today, mixed-model runs already report readiness per role and already
run a full certification battery per distinct model AND for the whole
combination together. What's missing is a readable failure message.

**Add readable messages only (small, safe, ships immediately)?**
*(Recommended.)* Or change what "qualified" means so already-certified
models can mix without a fresh combination-wide battery (real
cost savings, but touches code we've locked down as needing your
explicit go-ahead each time it changes)?

## Q4 — who gets the new intake tool by default? (Item 5)

Your words asked for a checked-file tool as the default "for small
models." Research this session found the same reasoning (no
back-and-forth to lose track of, one line to fix and re-check) helps
every caller equally, not just small ones.

**Make the checked-file tool the default for everyone, keeping the old
prose form only as generated documentation?** *(Recommended.)* Or keep
it scoped to small models only, as literally asked?

## What's already done, no decision needed

- **Sweep instrument fixed** (Item 1): a real gap in the root-checking
  tool — it was comparing test-run identities by name only, not by
  content — is closed. Confirmed nothing changes: every run that
  passed before still passes, byte for byte.
- **Errata caught up** (Item 2): one real gap where a closing checklist
  step was skipped is now on record; one older gap that predates the
  rule is noted for completeness, not treated as a violation.
- **Full test suite**: 3437 passing, 1 known pre-existing failure
  unrelated to anything done this session (already on record from a
  prior session, not re-diagnosed here), 0 new failures.
- **Nothing locked-down was touched**: verified directly, not assumed.

## One combined reply is enough

A single message answering Q1-Q4 (recommended options, or your own
choices) unblocks every stopped design in this program.
