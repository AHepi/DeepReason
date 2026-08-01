# Diagnosis: the merge exemption resolves a child slot by work id, and a repaired child is a different work

Primary cause: `_decomposition_merge_admits` walks a decomposition
completion's `child_work_ids` and, for each entry, looks the work id up
directly in `preparations` and demands the payload be a
`contract-decomposition-child.v1` bound to the activation transition. When an
atomic child is rejected and re-dispatched, the work that actually produces the
admitted candidate is a *different* work item whose payload is
`repair.semantic-task.v1` and whose decomposition authority is its
`parent_work_id`. The completion names that repair work — it must, because the
repair is what carries the admission — so the lookup returns a repair payload,
the schema test fails at that index, the exemption returns False, and the Conj
event falls through to the `not uniquely admitted` finding. Slot 0 of two of
this run's three merges is such a repair; the third has none.

Evidence:

  - `objects/workflow-contract-decomposition-completion-v1/*` — three
    completions. Per-child preparation payload schema, read from the record:

        3340c059d828  (Conj seq 110)  [0..5] all contract-decomposition-child.v1
        62b5e32458f8  (Conj seq 245)  [0] repair.semantic-task.v1  [1..5] child
        f8335acf8f40  (Conj seq 386)  [0] repair.semantic-task.v1  [1..5] child

    The two completions carrying a repair at slot 0 are exactly the two Conj
    events `verify_root` flags. This is the whole asymmetry.

  - Same objects, joined to `workflow-work-preparation-v1`: each repair's
    `parent_work_id` (`629db1453f3a`, `e102e396316d`) IS a
    `contract-decomposition-child.v1` whose `decomposition_transition_ref`
    (`6f570743ff43`, `9c7ca43b50e8`) is the transition its own completion
    names, and the repair inherits the parent's `contract_id`
    (`conjecturer.atomic-candidate.v1`), `route_lease` and `target_refs`
    identically. The chain the reader needs is present and durable; the reader
    simply does not walk it.

  - `objects/workflow-semantic-admission-v1` — for ALL THREE completions,
    every `child_semantic_admission_refs[i]` resolves to an admission whose
    `work_id` equals `child_work_ids[i]` and whose outcome is `admitted`,
    6 of 6 in each. Both repair works have an `admitted` admission of one ref.
    So the per-child admission gate passes on the flagged completions too.

  - `REPLAY_VALIDATION.json` `verification.violations` — the run recorded these
    same two findings about itself at write time, so the reader has been
    consistent and this is not checker drift.

  - Latest-child marker and effect refs, recomputed from the log: child
    provider seqs `[54,59,64,69,74,79] / [196,...,221] / [337,...,362]`, max
    equals the `conjecture-call:` seq the Conj event names in all three, and
    the event outputs are a subset of `admitted_effect_refs` in all three.

Implicated code:
  - `src/deepreason/invariants.py:534-545` — the per-child schema/transition
    gate, the only failing gate.
  - `src/deepreason/invariants.py:503` — the exemption's docstring, which
    claims it enforces "the same join the replay validator enforces".
  - `src/deepreason/workflow/replay.py:713-723` — the writer's repair branch,
    which resolves through `parent_work_id` under exactly the three guards the
    record shows satisfied. READ ONLY, not to be modified (GOAL.md).

Falsifiable prediction (for dr-reproduce):

    Build an offline decomposition merge in which exactly one atomic child is
    rejected and re-dispatched as repair.semantic-task.v1, and the completion
    names the repair work in that slot.

    expected: verify_root_report emits
      "event seq=<n>: Conj outputs are not uniquely admitted by their provider attempt"
    and the same fixture with no repaired child emits nothing.

    If a fixture with a repaired child verifies clean, this diagnosis is wrong.

Ruled out: **the latest-child marker gate** (`invariants.py:570`), the natural
rival — a repair adds a provider call, so it is plausible the merge's
`source_seq` stops being the maximum child seq and the exemption fails there
instead. Recomputed above from the log: `source_seq == max(child seqs)` holds
for all three completions, including both flagged ones. Also ruled out by the
same measurement: the admission gate and the `admitted_effect_refs` subset
test, both of which pass on the flagged completions.

Correction to GOAL.md's framing: seq 110 is **not** a clean control that passes
the primary admission test. Recomputing that test from the record gives
`matching_admissions` = 0 for seq 110, 245 AND 386, and 1 only for seq 482 and
747 (the two `conjecturer.turn.v6` events). All three atomic-contract merges
depend entirely on the exemption; the difference between them is inside it, at
the schema gate, and nowhere else. The prior investigation raised this and the
record confirms it.
