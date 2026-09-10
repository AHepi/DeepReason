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
