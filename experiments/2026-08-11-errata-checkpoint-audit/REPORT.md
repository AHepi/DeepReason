# Report: Item 2 — errata checkpoint compliance audit

Swept every `DELIVERY.md`/`VERIFY.md` committed on or after 2026-08-09
11:49:07 UTC (when the mandatory errata-checkpoint rule landed,
commit `2416c6f32`, in `dr-deliver-change`/`dr-verify-outcome`) for the
checkpoint's presence. Full findings and disposition are recorded
directly in `docs/ERRATA_EXECUTOR.md` (2026-08-11 entry), per that
ledger's own convention — this report exists only so the audit itself
has a discoverable tranche directory.

Summary: one real violation
(`experiments/2026-08-09-change-judge-evidence-review/DELIVERY.md`,
missing the checkpoint 35 minutes after the rule landed), one same-day
pre-rule gap recorded for completeness
(`experiments/2026-08-09-change-hard-question-set/DELIVERY.md`), two
tranches confirmed compliant. Also folded in Item 1's finding (the
`root_sweep.py` coverage gap, `docs/ERRATA.md` E18) per the task
handover's instruction to combine Items 1 and 2's errata work.

Not backfilling either DELIVERY.md in place — closed tranche artifacts
stay as delivered, per this repo's own precedent (E16/E17: "a closed
tranche's parked item, not edited"). The correction stands in the
process ledger.

## Errata

`docs/ERRATA_EXECUTOR.md`, 2026-08-11 entry (this audit's own
findings) and `docs/ERRATA.md` E18 (Item 1's finding, folded in here
per instruction).
