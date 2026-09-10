# Parked — found during this tranche, not fixed here

## P1 — `terminal.continuation_authority` and the security channel disagree, and nothing reconciles them

**What.** On the live root
`experiments/2026-09-09-fix-solo-criticism-authority/runs/home-solo/runs/run-02818acc38961781e2e820d0d6b591fb`
the stop report's section 5 says `continue: ACCEPTED` and
`record_security_violations` is empty, while `deepreason results --verify` on
the same bytes says `valid: false` with 76 security findings. The 2026-08-29
operator law gates continuation on the record verifying intact, and
`DR-SUB-workflow`'s own Traps entry records that the STOPPED receipt "never
AUTHORIZES a continuation, which the SECURITY-channel integrity gate decides at
continue/amend time (`docs/ERRATA.md` E61)". So there are two security readings
of one record and they do not agree on what "the security channel" means. This
tranche removes the 75 false findings; it does NOT decide which reading the gate
should consult, and after the fix the two verdicts agree by coincidence rather
than by construction.

**Ready-to-send prompt.**

```
Route through deepreason-orchestrator (dr-set-goal first). One goal: the
continuation gate and `deepreason results --verify` read the same security
channel, or one document says in typed terms why they read different ones.

Evidence, all read-only:
- experiments/2026-09-10-defect-defended-trial-authority-census/VERIFY.md, the
  section "What this does to the continuation gate" -- the two verdicts stated
  side by side on one committed root, before and after this tranche's fix.
- docs/ERRATA.md E61 and docs/map/SUB-workflow.md's Traps entry on the STOPPED
  receipt -- the claim that a security-channel integrity gate decides
  continuation at continue/amend time.
- src/deepreason/workflow/lifecycle.py (record_security_violations) vs
  src/deepreason/verification/report.py (the security channel of
  VerificationReportV2) -- the two populations.

Settle the question before designing: are these meant to be the same set? The
2026-08-29 law says a run whose record fails replay validation or carries
unresolved containment-breach evidence is REFUSED continuation. If the report's
security channel is the intended authority, the gate is open today on records
the instrument calls invalid, and closing it changes which runs may continue --
which is an operator decision, not a defect fix.

verification/ is frozen surface 3: run tools/blast_radius.py before designing
and price the roads in FIX.md; do not implement without a grant.
```

## Not parked here, because another tranche already owns them

- The open-work-order policy question (a v6 root whose terminal epoch remains
  open and uncommitted) — parked elsewhere and left there, per this tranche's
  brief.

## P2 — `tools/blast_radius.py` reports CLEAR for every change inside `verification/`, which is half of frozen surface 3

**What.** The disclosure gate's `FROZEN_SURFACES` registry
(`tools/blast_radius.py:110-132`) spells surface 3 as the single path
`src/deepreason/invariants.py`. Its owning document spells it
"Replay-validation record formats — `invariants.py`, `verification/`"
(`DR-INV-frozen-surfaces` §3), and CLAUDE.md's third-lane section states the
count explicitly: five surfaces spanning SEVEN paths, "because surface 3 covers
both `invariants.py` and `verification/`". So every change under
`src/deepreason/verification/` computes `frozen_surface_verdict: CLEAR` and a
disclosure summary that says in words "This change touches none of the five
frozen surfaces". Measured this tranche on
`--files src/deepreason/verification/report.py`
(`experiments/2026-09-10-defect-defended-trial-authority-census/proof/BLAST_RADIUS.txt`),
with a control run naming the five registry paths that returns all five as
`DIRECT` — so the CLEAR is a registry gap, not a semantic verdict.

**Why it matters.** The gate exists because a tranche once found surface
contact in its own prose and committed anyway (its module docstring's 2026-08-09
incident). A window that trusts this gate over the owning document will edit a
frozen surface believing it was told there was none to edit — the same failure
the gate was built to prevent, arriving through the gate itself. Six paths under
`verification/` carry containment and report semantics, including the two the
2026-08-27 escape fix needed an explicit grant for.

**Ready-to-send prompt.**

```
Route through deepreason-orchestrator (dr-set-goal first). One goal:
tools/blast_radius.py reports CONTACT for a change inside
src/deepreason/verification/, because its frozen-surface registry spells
surface 3 the way the owning document spells it.

Evidence, all read-only:
- experiments/2026-09-10-defect-defended-trial-authority-census/proof/BLAST_RADIUS.txt
  -- CLEAR on verification/report.py, and the control run showing the tool
  reports DIRECT for every registry path when named. The gap is the registry,
  not the computation.
- tools/blast_radius.py:110-132 -- FROZEN_SURFACES, five entries, one path each.
- docs/map/INV-frozen-surfaces.md §3 heading -- "invariants.py, verification/".
- CLAUDE.md, the treadle section -- five surfaces, seven paths, and why the
  count differs from the path count.

Decide the shape before coding: a registry entry can be a path PREFIX (a
directory) or a list of paths, and _frozen_contacts currently compares
`entry["path"] in normed_files`, an exact-match test. Whichever you choose, the
tool's own self-test (its --selftest fixtures) must gain a case that goes RED if
a directory-scoped surface stops matching a file inside it -- the gate's own
standard, which docs_verify --audit applies to map checks and this tool has no
equivalent auditor for.

Check whether any OTHER surface in that registry is also spelled narrower than
its document before you close the tranche; do not widen only the one this
finding names.

tools/ is not a frozen surface, so this needs no grant. It is small: one
registry entry, one comparison, one self-test case.
```
