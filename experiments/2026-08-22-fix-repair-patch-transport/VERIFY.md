# VERIFY — the fix against `GOAL.md`'s success criterion

Commits: `97a964583` (code + tests + map), plus the tranche artifacts and
`docs/ERRATA.md` E42.

## Criterion 1 — every lossless spelling is applied; the substantive loss is not

    python experiments/2026-08-22-fix-repair-patch-transport/repro.py
    # exit 0

    batch-critic.v2                  #1  applied replace /cases/0/premise_evidence/0/block
    batch-critic.v2                  #1  applied replace /cases/0/premise_evidence/0/block
    batch-critic.v2                  #2  applied replace /cases/0/premise_evidence/1/block
    batch-critic.v2                  #2  applied replace /cases/0/premise_evidence/0/block
    conjecturer.atomic-candidate.v1  #1  DISCARDED at the wire
    conjecturer.atomic-candidate.v1  #2  applied remove /candidate/checker_specs/0/id
    conjecturer.atomic-candidate.v1  #3  applied remove /candidate/checker_specs/0/terms
    conjecturer.atomic-candidate.v1  #4  applied remove /candidate/checker_specs/0/terms
    conjecturer.turn.v6              #1  applied replace /scratch_proposal/links/0/to_ref
    conjecturer.turn.v6              #1  applied replace /scratch_proposal/links/0/to_ref
    conjecturer.turn.v6              #2  applied replace /scratch_proposal/links/1/to_ref
    conjecturer.turn.v6              #3  applied replace /scratch_proposal/unresolved_questions/0/related_refs
    conjecturer.turn.v6              #4  applied replace /scratch_proposal/unresolved_questions/1/related_refs

    no lossless spelling is discarded

Twelve of thirteen recorded responses are now read at their authorized pointer,
against seven before. The thirteenth — `atomic-candidate #1`, `old`/`new` in
place of `value` — is still discarded, which is the intended outcome.

## Criterion 2 — the fatal grant survives

`conjecturer.turn.v6` repair #4, the last grant of the chain that exhausted the
seat and ended the run, now applies
`replace /scratch_proposal/unresolved_questions/1/related_refs`. Before the fix
it was discarded at the wire.

**Stated honestly, and no further.** This proves the patch is applied, not that
the whole turn then validated. Re-deriving that would require reconstructing
the run's alias tables to rebuild `ConjecturerTurnWireContractV6`, which this
tranche did not do. What the record does show, without reconstruction: the
dispatched envelope at #4 listed exactly one remaining diagnostic
(`unresolved questions may use only visible/local scratch refs`), the baseline
at that pointer was `["SRC_005","SRC_008","NEW_002"]` — two formal source
aliases where only local scratch refs are admissible — and the patch replaces
it with `["NEW_002"]`, removing precisely the two illegal refs. The
structurally identical patch at the sibling slot had been accepted one grant
earlier. The residue is that "the run would have completed" remains unproven;
"the run would not have died at this grant" is proven.

## Criterion 3 — an off-target patch is still a typed refusal

`test_off_target_patch_remains_a_typed_scope_violation` builds a patch in a
now-tolerated wrapper (`{"patch": {"operation": …, "pointer": …}}`) aimed
outside `authorized_pointers` and asserts `apply_repair_patch` still raises
`RepairScopeViolation` with code `REPAIR_SCOPE_VIOLATION`. `apply_repair_patch`
and `enforce_repair_subtree` are byte-unchanged.

## Criterion 4 — no unmetered retry loop

`workflow/repair_transaction.py` is unchanged. `resolve_schema_repair_grant`,
`maximum_schema_repairs`, the per-repair `prepare`/`issue`/`terminate` cycle
and `V6_PATCH_REPAIR_CEILING` are all untouched, so the number of provider
calls a contract may make is exactly what it was. The fix removes the reason
grants were wasted; it does not make waste free.

## Criterion 5 — instruments

| instrument | result |
|---|---|
| `python -m pytest tests/ -q -n 4` | PENDING — running at time of writing; this row is updated in the closing commit, and the tranche is not complete until it reads 0 failed |
| `python -m pytest tests/test_v6_patch_repair_and_wire.py -q` | 24 passed |
| `python tools/docs_verify.py` (full) | 970 checks, 3 failed — the three pre-existing `CON-run-identity.md` git-archaeology checks that cannot pass in a shallow clone. No new failure. |

## Mutation proof (both directions)

Each mutation applied to `src/deepreason/llm/repair.py` alone, then reverted:

| mutation | caught by |
|---|---|
| container key set narrowed back to `repair.patch.v1` only | `…epoch1_patch_spellings…`, `…off_target_patch_remains…` |
| `pointer` -> `path` synonym removed | `…epoch1_patch_spellings…`, `…off_target_patch_remains…` |
| echo drop disabled | `…epoch1_patch_spellings…`, `…echoes_are_dropped_only_when_they_match` |
| echo drop made unconditional (value equality ignored) | `…echoes_are_dropped_only_when_they_match` |
| `old`/`new` read as `value` (widened past losslessness) | `…substantive_patch_loss_is_still_rejected` |

No mutation passes. The last two are the guards in the opposite direction: they
fail if the tolerance is widened, not narrowed.

## Live proof

Not owed by this tranche (`GOAL.md`); the relaunch tranche owns it. Note also
CLAUDE.md's standing fact that capability-channel behaviour is stochastic
across identical runs, so one live attempt would not settle a rate question
anyway. The offline regression over recorded bytes is the proof here.

## What happens now when a seat returns a well-formed patch at the wrong pointer

It is refused, exactly as before: `apply_repair_patch` raises
`RepairScopeViolation`, the attempt is terminalized as a typed rejection in the
run's record, and it consumes one of the contract's metered repair grants —
nothing about that path was changed, and nothing may now reach a pointer
outside the dispatched `authorized_pointers`.
