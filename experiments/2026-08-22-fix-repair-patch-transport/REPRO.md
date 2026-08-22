# REPRO — the diagnosed cause, demonstrated offline

    python experiments/2026-08-22-fix-repair-patch-transport/repro.py
    # exit 1 while the defect is present

`repro.py` reads the committed epoch-1 root READ-ONLY, joins every repair
provider attempt to the preparation payload that froze its authority before
issue, and replays each recorded raw response verbatim through the live
transport path (`tolerant_patch_value` -> `RepairPatchV1`).

## Result on the unfixed tree (2026-08-22, HEAD 32492cdb8)

    batch-critic.v2                  #1  DISCARDED at the wire
    batch-critic.v2                  #1  applied replace /cases/0/premise_evidence/0/block
    batch-critic.v2                  #2  DISCARDED at the wire
    batch-critic.v2                  #2  DISCARDED at the wire
    conjecturer.atomic-candidate.v1  #1  DISCARDED at the wire
    conjecturer.atomic-candidate.v1  #2  applied remove /candidate/checker_specs/0/id
    conjecturer.atomic-candidate.v1  #3  DISCARDED at the wire
    conjecturer.atomic-candidate.v1  #4  applied remove /candidate/checker_specs/0/terms
    conjecturer.turn.v6              #1  applied replace /scratch_proposal/links/0/to_ref
    conjecturer.turn.v6              #1  applied replace /scratch_proposal/links/0/to_ref
    conjecturer.turn.v6              #2  applied replace /scratch_proposal/links/1/to_ref
    conjecturer.turn.v6              #3  applied replace /scratch_proposal/unresolved_questions/0/related_refs
    conjecturer.turn.v6              #4  DISCARDED at the wire

    DEFECT PRESENT: 5 lossless spellings discarded

## What it establishes

- **No line reads `OFF TARGET`.** The premise the tranche was opened on does
  not reproduce, because it did not happen (`DIAGNOSIS.md` Finding 0).
- Six responses never reach `apply_repair_patch`. Five of them are lost purely
  on transport spelling; the sixth (`atomic-candidate #1`) offers `old`/`new`
  where the contract requires `value` and is a correct rejection
  (`DIAGNOSIS.md` Finding 2), so `repro.py` excludes it by name from the
  failure count rather than by a rule that might quietly absorb it later.
- `conjecturer.turn.v6 #4` — the last grant of the chain that exhausted the
  seat and ended the run — is among the five.

## Falsifier

If a future change makes `atomic-candidate #1` read as `applied`, tolerance has
been widened past losslessness and this reproduction is no longer a proof of
the right thing. The regression test carries the same assertion.
