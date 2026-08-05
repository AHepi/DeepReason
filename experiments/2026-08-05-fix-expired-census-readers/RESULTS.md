# Results — expired census readers

## 2026-08-05 — four red instruments, one cause, fixed in the readers

**What was observed.** At `6ad6c42c` four instruments were red against a
tree whose committed evidence was correct: two tests
(`tests/test_module_fingerprints.py`, `2 failed, 3336 passed`) and two
map checks (`SEAM-harness-x-verification.md:253`,
`SEAM-manifest-x-schools.md:271`, `docs_verify: 2 failed`). All four
bisected to a single commit, `f6d41bff` — rung 5's live A/B arm A — which
committed two run roots. The same two tests report `20 passed` at its
parent and `2 failed, 18 passed` at it.

**What the record showed.** Every instrument pinned a CENSUS of
committed run roots as the evidence for a claim that does not depend on
the count. Measured on the day: all four underlying claims were still
true while all four instruments were red — absence is valid on roots
written before the module-fingerprint feature (31 roots), presence is
valid on roots written after it (2), some roots are expected to refuse
to open (14), and "raising" and "no manifest" remain different sets
(11 vs 3 under `experiments/`). A census is a fact with an expiry date;
any tranche that commits a run root falsifies it.

The test-side defect was narrower than the failure count suggested: a
single assertion inside a `functools.lru_cache`d helper that both tests
share. `test_the_census_of_committed_roots_is_unchanged` was collateral
damage — its own assertions are a partition identity, an existence
claim and a floor, none of which can expire. Deleting the offending
line alone made both tests pass, which is how the collateral-damage
reading was confirmed rather than assumed.

**What was fixed.** The readers, not the roots — the operator's
instruction and `DR-INV-frozen-surfaces`' governing principle agreeing
independently. Zero `src/` lines changed: the production reader
(`module_events.recorded_module_fingerprints`) was always correct.

- The helper returns a three-way partition split by each root's OWN
  record, so no root is named and the split cannot go stale.
- The renamed test asserts BOTH halves its docstring always claimed,
  plus a non-empty-witness guard so the presence half cannot pass
  vacuously.
- Both map checks assert the partition and non-emptiness their prose
  actually claims, and pin no count. Every surviving number is a dated
  measurement citing its commit, marked do-not-re-pin.
- Both documents gained a `Traps` entry.
  `SEAM-harness-x-verification`'s records that this check expired
  TWICE — 42/25 → 45/28 at the stress triplet (`docs/ERRATA.md` E3), and
  45/28/14/3 → 47/30/14/3 at rung 5 — and that the first fix, updating
  the numerals, is what guaranteed the second occurrence.

**What the record now shows.** Full gate `3338 passed, 7 skipped, 0
failed`; `docs_verify` `51 documents, 815 checks, 0 failed`; `--audit` 0
findings, so the greenness was not bought by making anything vacuous;
`--links` 0 dangling. Test population unchanged at 3338 — assertions
were restated, not removed, and the two tests now assert strictly more
than before.

**Residue — what remains unproven or undone.**

- *The class is not fixed, only four instances of it.* Nothing prevents
  a fifth census assertion being written tomorrow. `--audit` catches
  vacuous checks; no instrument distinguishes a count that is a property
  from a count that is a fact with an expiry date.
- *A `src/` mutation inside a git worktree is never loaded* — the
  editable install resolves `deepreason` to the main tree regardless.
  This tranche's first mutation proof passed spuriously for that reason
  and was caught only because the result looked implausible. `DR-SCHEMA`
  actively recommends worktrees for falsification without noting it
  (P1e).
- *The workflow gap that produced this is untouched* (P1b):
  `dr-deliver-change` measures before the live-evidence commits it
  enables, so rung 5's `DELIVERY.md` proof line was true when written
  and false hours later.
- *`docs/ERRATA.md` E5 still misidentifies which roots are the
  no-manifest three* (P1a). The prose written here states the measured
  truth, so nothing shipped depends on E5, but the ledger is wrong.
- *P7 remains parked*, still visible as one `attempt-validity` violation
  on the round-robin arm.
- *One measurement in this tranche was corrupted and is recorded as
  such*: a gate run made while `docs_verify` was running concurrently
  reported three MCP thread-timing failures that do not reproduce
  unloaded. Accepted does not mean true, and neither does green measured
  on a box you loaded yourself.
