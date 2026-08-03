# Parked — noticed or deferred during this tranche, deliberately not done

- **R8, deferred in the operator's own words** ("the sub documents never
  mentions the seam documents they're involved with, and how to tell
  whether a modification is just isolated or requires directions from
  rec-seam document. But this job is a later task. For now, focus on the
  others."): a later tranche should (a) make every `docs/map/SUB-*.md`
  cross-reference the SEAM documents it participates in — note the
  `Seams:`/`Seams-undocumented:` headers already exist, so the job is
  likely surfacing them in prose plus the missing half — and (b) add a
  triage rule to SCHEMA.md or the SUB template for deciding isolated
  modification vs. REC-change-a-seam-guided modification. Ready-made
  inputs: `docs/map/SCHEMA.md` anatomy section, `REC-change-a-seam.md`
  steps 1-2, INDEX.md's seam matrix.
- A docs_verify mode for `.claude/skills/` checks — still parked from the
  dr-ask-the-right-question tranche.
- Flaky under parallel load:
  `tests/test_v6_nonconjecture_recovery.py::test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`
  failed once in a `-n 4` full gate on a loaded box (761s run), passed
  solo, with its file, and in the immediate full-gate rerun (3290/0).
  Zero src/tests changes in the failing tranche. Defect-family candidate:
  reproduce under load, diagnose order/timing dependence.
