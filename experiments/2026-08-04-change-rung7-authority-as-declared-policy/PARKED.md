# Parked — noticed during rung 7, not done

## P1 — FOUR instruments have been red since rung 5, and TWO delivered DELIVERY.md claims are stale

**Upgraded 2026-08-04, after the full gate ran.** This entry originally
recorded two failing map checks. The full gate then found two failing
TESTS with the same cause, and the cause turns out to be a
mis-specified test rather than a bad commit. The original analysis is
kept below the upgrade; nothing in it was wrong, it was incomplete.

### The four red instruments

    docs_verify: 51 documents, 815 checks, 2 failed
      FAIL SEAM-harness-x-verification.md:253  (pins 45/28/14/3, is 47/30/14/3)
      FAIL SEAM-manifest-x-schools.md:271      (pins 42 under experiments/, is 44)

    pytest tests/ -q -n 4: 2 failed, 3336 passed, 7 skipped in 663.27s
      FAILED tests/test_module_fingerprints.py::test_every_committed_root_reads_as_having_no_module_fingerprints
      FAILED tests/test_module_fingerprints.py::test_the_census_of_committed_roots_is_unchanged

### First bad commit, bisected

    a4c52c5b rung 5: full-tier qualification recorded; run roots deferred   20 passed
    f6d41bff rung 5 A/B arm A: default backend, completed and replay-valid   2 failed, 18 passed
    1f20a6bd rung 5 A/B complete: both arms recorded                        2 failed, 18 passed

`f6d41bff` is the first bad commit. Proven pre-existing independently of
this tranche: the same two tests fail at rung 7's tranche base
`2cc3fd50` in a clean detached worktree containing none of this
tranche's work.

### The actual defect: the TEST is wrong, not the roots

`tests/test_module_fingerprints.py::_sweep_committed_roots` asserts

    assert recorded_module_fingerprints(harness) == (), root

for EVERY committed root. Its own docstring states the intended claim:

    "R8: absence is the VALID answer on every root written **before this
     feature**, not an error and not an empty-because-unreadable."

Those are different claims. The intended one is that the READER
TOLERATES ABSENCE — an invariant. The implemented one is that NO
COMMITTED ROOT CARRIES A STAMP — a fact with an expiry date, true only
until someone commits a run performed after rung 4's writer landed.
Rung 4 shipped the writer and this test in the same tranche, so the
first live run committed thereafter was guaranteed to break it. Rung 5's
A/B arms were that run, and they are correct evidence, correctly
committed.

So the fix is almost certainly in the test, not in the roots and not in
the two map checks' numerals: assert that roots written before the
feature read as absent AND that roots written after read as present,
rather than that every root reads as absent. Note that
`_committed_roots()` uses exactly the instrument this tranche's SPEC.md
M6c used (`git ls-files` + `/log.jsonl` → 47), so the two agree about
the world and disagree only about what should be asserted of it.

### The two stale claims

`experiments/2026-08-04-change-rung5-dumb-alternative-backend/DELIVERY.md`
states:

> **Proof:** full gate 3338 passed / 0 failed; `docs_verify` 0 failed,
> `--audit` 0, `--links` 0, `--coverage` 0; 42-root sweep byte-identical

Both the gate claim and the `docs_verify` claim were TRUE when measured
at the offline-work commit `7fdff121`, and both went false at
`f6d41bff` — inside the same tranche, in its post-delivery segments.
The arithmetic corroborates it exactly: 3338 = 3336 passed + 2 failed,
the same test population, two of which now fail. Neither claim is
dishonest; neither says which commit it was measured at, and the
tranche kept committing evidence after its final measurement.

**The generalizable lesson, which is the part worth keeping:** a
delivered tranche that continues to commit artifacts after its final
measurement invalidates its own proof line, and nothing in the workflow
currently re-measures at that point. `dr-deliver-change` runs before the
live-evidence commits it enables. This is a workflow gap, not an
individual mistake, and it is the second time the record has been
bitten by a measurement whose commit was not stated (ERRATA E3, E5, E8
are the earlier family).

### Original entry (2026-08-04, before the gate ran)

**Found:** capturing rung 7a's `docs_verify` baseline at tranche base
`27e088cb`, before this tranche changed anything.

**Found:** 2026-08-04, capturing rung 7a's `docs_verify` baseline at
tranche base `27e088cb`, before this tranche changed anything.

**What the record shows:**

    docs_verify [full]: 50 documents, 807 checks, 4 workers
    FAIL SEAM-harness-x-verification.md:253  -> AssertionError: (47, {0: 30, 1: 14, 2: 3})
    FAIL SEAM-manifest-x-schools.md:271      -> AssertionError: 44
    docs_verify: 2 failed

Both are the same root cause, and neither was caused by this tranche
(`find experiments/2026-08-04-change-rung7-authority-as-declared-policy
-name log.jsonl` → 0).

- `SEAM-harness-x-verification.md:253` pins the git-tracked root census
  at `len(R)==45 and c[0]==28 and c[1]==14 and c[2]==3`. It is now
  **47 / 30 / 14 / 3**.
- `SEAM-manifest-x-schools.md:271` pins the `experiments/` census at
  `len(roots)==42`. It is now **44**.

**Cause:** rung 5's post-delivery live A/B committed two run roots —
`f6d41bff` ("rung 5 A/B arm A") and `1f20a6bd` ("rung 5 A/B complete") —
at `experiments/2026-08-04-change-rung5-dumb-alternative-backend/
{ab,rr}-home/runs/run-9a6be78e…`. Committing them was correct; they are
the typed evidence the A/B produced. Nothing re-ran `docs_verify` after
them, so the two census checks have been failing ever since.

**The stale claim.** `experiments/2026-08-04-change-rung5-dumb-alternative-backend/DELIVERY.md`
states "`docs_verify` 0 failed, `--audit` 0, `--links` 0, `--coverage` 0".
That was TRUE when measured, at the offline-work commit `7fdff121` —
and the A/B roots landed in the three post-delivery segments AFTER it.
The claim is not dishonest; it is out of date, and its document does not
say which commit it was measured at. This is the ERRATA E3 shape
recurring ("the pre-v6 census check went stale-false the day it
mattered") with a new trigger: not a stamp advanced without a re-run,
but a delivered tranche continuing to commit evidence after its final
measurement.

**Why it is parked, not fixed here.** (a) The operator scoped this
tranche to "7a only (the seam document, docs-only)". (b) The
orchestrator's cross-routing rule: a defect found mid-change is PARKED,
not fixed. (c) The fix is not obviously "change 45 to 47" — this is the
same census-instrument confusion that already owns TWO errata entries
(E5, the unreproducible 45-root baseline; E8, citing the wrong
instrument for a verdict flip), so choosing between updating the
numerals and making the checks instrument-relative is a judgement that
deserves its own tranche rather than a drive-by edit inside a seam
document's tranche.

**Consequence for 7a, declared rather than hidden:** SPEC.md 7a's accept
said "`docs_verify` full mode 0 failed". That is unreachable without
fixing someone else's staleness, so this tranche's acceptance is
DELTA-based instead: exactly these two pre-existing failures and no
others, with the check count risen by the number this tranche added.
CHECKLIST.md steps 1 and 10 are amended accordingly and say so.

**Suggested disposition:** its own small tranche —
`deepreason-orchestrator` (it is a defect: two checks assert something
false) or a map-maintenance change tranche. It should decide, once, for
both checks, whether a root census belongs in a check at all given that
every future tranche committing a root will break it again. That is the
question worth answering; the numerals are not.

---

## P2 — `SUB-adjudication.md`'s seam table row for authority described the pair as "indirect, not absent" while `Seams-undocumented:` listed it

Not a defect — the row was accurate and honest. Recorded only because
7a resolves it, and the resolution is the kind that should be visible:
the row moves from "undocumented" to naming `DR-SEAM-adjudication-x-authority`.
No action owed beyond 7a itself.

---

## P3 — `CON-authority.md`'s `Seams:` header was entirely empty

Same ERRATA E9 shape as `SUB-harness.md`'s empty header (seven seam
documents existed while six owning headers said otherwise). `CON-authority`
had no `Seams:` entries at all despite participating in real, documented
agreements. 7a adds one (`DR-SEAM-adjudication-x-authority`); the other
three pairs it lists as undocumented (`authority x manifest`,
`authority x rules`, `authority x scheduler`) remain undocumented and
are NOT this tranche's job. Worth noting that `authority x rules` is
arguably the highest-value of the three, since it is where 7b would
land.

---

## P4 — the `argumentative_authority_mode` error-message asymmetry

Carried forward from SPEC.md's Out-of-scope. `_resolve_authority`'s
refusal names which vocabulary the value belongs to
(`ARGUMENTATIVE_AUTHORITY_NOT_MANIFEST_BOUND: … is a Config-only mode`);
`argumentative_authority_mode`'s does not (`unsupported argumentative
authority: defended_trial`, indistinguishable from a typo).
`CON-authority.md` already records the asymmetry and pins both messages
so improving the weaker one fails a check rather than passing silently.
Not requested; a natural 7b companion.

---

## P5 — the dead `single_family_trial` Config value

Carried forward from SPEC.md's Out-of-scope and from
`CON-schools.md`'s Traps ("cannot complete a trial … parked as dead
weight, not removed"). 7b's consolidation will make it more visible, not
less. Removing it is a behavior decision, not a refactor.
