# Fix: resolve a merge child's decomposition authority through its repair chain

Guarantee restored: a decomposition merge verifies exactly when every slot's
admitted candidate is authorised by a `contract-decomposition-child.v1` of that
merge's activation transition — whether the slot's work IS that child or a
repair re-dispatched from it.

Change sites (exhaustive):

  - `src/deepreason/invariants.py`, new helper immediately above
    `_decomposition_merge_admits` — `_decomposition_child_authority(child_work_id)`
    returns the preparation that carries a merge slot's decomposition
    authority. If the slot's payload is not `repair.semantic-task.v1` it
    returns that preparation unchanged. If it is, it walks `parent_work_id`,
    requiring the parent to match the repair on `contract_id`, `route_lease`
    and `target_refs`, and repeats. A bounded `seen` set makes it cycle-safe.
    Returns `None` on any break in the chain.
  - `src/deepreason/invariants.py:535` (inside the per-child loop) —
    `preparations.get(child_work_id)` becomes
    `_decomposition_child_authority(child_work_id)`. Two lines. The existing
    schema and `decomposition_transition_ref` tests are UNCHANGED and now apply
    to the resolved authority.

Nothing else moves. In particular the provider-attempt lookup and the
per-child admission test below keep using the raw `child_work_id`, because the
work that actually ran is the work that holds the attempt and the admission —
only the AUTHORITY is inherited.

Why this shape rather than "accept a repair payload here": the loop is copied
from two existing precedents rather than invented. `workflow/replay.py:713-723`
is the writer's own atomic-repair authority check and uses exactly these three
parent guards; `invariants.py:647-672` (`_prepared_school_id`) is the same
bounded `parent_work_id` walk already living in this file. The record confirms
all three guards hold for both live repairs (`contract_id`
`conjecturer.atomic-candidate.v1`, `route_lease` and `target_refs` identical to
the parent).

Regression artifact: `tests/test_v6_engaged_repair_verification.py`
  - `::test_merge_whose_child_was_repaired_verifies_clean[first-child]` and
    `[latest-child]` — currently FAILING, must invert to passing.
  - `::test_the_repaired_child_slot_really_names_repair_work[first-child]` and
    `[latest-child]` — currently passing, must STAY passing (proves the
    inversion is not a fixture that stopped repairing).

New conditions this fix must additionally be tested against, because the walk
is new behaviour and the reproduction does not cover them:
  - a repair whose `parent_work_id` names a work that is not in this
    completion's transition — must still fail closed;
  - a repair chain that terminates at something other than a
    `contract-decomposition-child.v1` (e.g. the pre-decomposition source work)
    — must still fail closed;
  - a repair whose parent disagrees on `contract_id`, `route_lease` or
    `target_refs` — must still fail closed.

AMENDED during dr-implement-fix. None of the three is constructible as a
TARGETED negative, and the reason is a property worth recording rather than a
gap to apologise for. All three require a record naming a parent the writer
would not have named, and `preparations` is loaded via `objects.get(object_id)`
from a digest-verified store: editing any preparation record raises
`corrupt object record` and the run fails closed on `workflow-decision` before
the pairing check ever runs. Measured — tampering `contract_id` on the five
repair preparations of a `repair_child=0` root yields

    workflow-decision: event seq=34: transaction output is unavailable:
      ValueError('corrupt object record: .../workflow-work-preparation-v1/9268...json')

So the guards cannot be exercised by a forged record at all; they can only be
reached by a genuinely authored one, which the writer does not produce. That is
a stronger guarantee than the three negatives would have given, and it is what
gets tested instead: one negative asserting that a tampered repair preparation
fails closed. The parent-guard branches inside the helper are therefore
defence-in-depth against a future writer change, not against an attacker, and
this file says so rather than claiming coverage the tranche does not have.

Existing tests at risk (from grep over `_decomposition_merge_admits` and
`contract-decomposition-child`):
  - `test_merge_conj_bound_to_non_child_work_fails_closed` — MUST KEEP PASSING.
    This is the nearest thing to a false positive for this fix: it rebinds the
    merge to a rejected PATCH's provider call, and that patch is itself
    `repair.semantic-task.v1` work. It should still fail closed because that
    repair descends from the pre-decomposition source work and is in no
    completion's `child_work_ids`, so the exemption returns False at its first
    gate before the walk is ever reached. Predicted, and to be measured — if
    this test flips to passing the fix is wrong and must be withdrawn.
  - `test_merge_conj_bound_to_non_latest_child_fails_closed` — keep passing;
    untouched, the marker gate is not modified.
  - `test_fabricated_valid_attempt_on_wire_invalid_turn_fails_closed` — keep
    passing; different check entirely.
  - `test_rejected_wire_valid_patches_and_merge_conj_verify_clean` — keep
    passing; the no-repair merge is unaffected.
  - `tests/test_v6_constrained_scratch_execution.py` mentions
    `contract-decomposition-child.v1` but does not exercise this exemption.

None of these fixtures depended on the defective behaviour, so none is updated.
No assertion is weakened anywhere.

Predicted effects, to be measured in dr-verify-outcome and not assumed:
  1. A verdict sweep over every root under `experiments/` that
     `verify_root_report` can open, captured before and after: EXACTLY ONE line
     differs — `run-b4d6dfda0c20676a864a051fbc97bda4` goes
     `integrity=False pairing=2` to `integrity=True pairing=0`. Every other
     line byte-identical, including the roots that raise
     `UnsupportedRunManifestVersionError`.
  2. `tests/test_v6_engaged_repair_verification.py` goes 7 passed / 2 failed to
     9 passed.
  3. Full gate stays at 0 failed.

Explicitly not changed:
  - `src/deepreason/workflow/replay.py`. It is the tempting neighbour — reader
    and writer disagree, so either could move — but CLAUDE.md requires the
    READER to change so committed roots stay valid, and a writer change would
    alter what future runs record without making this root verifiable.
  - The `contract-decomposition-child.v1` schema test and the
    `decomposition_transition_ref` equality test. The chain must still
    TERMINATE at a child of this exact transition; the fix only teaches the
    reader how to reach it. A repair whose chain ends anywhere else resolves to
    a preparation that fails the unchanged gate, or to `None`, and the
    exemption still returns False.
  - No replay-validation record format. This changes what is accepted, never
    what is written.

Estimated diff: ~40 lines across 1 file (plus the already-committed test
changes). Well under the 150-line budget.

Approval gate: GOAL.md class is `defect`; the estimate is <=150 lines; no
frozen surface is touched (no state digest, no event application order, no
manifest schema, no qualification subject, no record format). Proceeds to
`dr-implement-fix`.
