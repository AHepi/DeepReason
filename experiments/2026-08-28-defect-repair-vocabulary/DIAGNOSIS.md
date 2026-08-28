# Diagnosis: two hand-maintained repair-`mode` vocabularies, written to and read from the same payload field, intersect in `patch` alone

Primary cause: `mode` on a `repair.semantic-task.v1` work payload has exactly
one writer and one authority-checking reader, and they were typed
independently. The writer is
`workflow/repair_transaction.py:295` (`"mode": turn.mode`), copying the field
straight off `V6RepairTurn`, whose type is
`Literal["initial", "whole_object_syntax", "patch"]`
(`llm/repair.py:1505`). Because the writer only runs inside the repair loop
`for repair_index in range(1, maximum_repairs + 1)` and
`V6PatchRepairSession.turn` returns `mode="initial"` only for `attempt == 0`
(`llm/repair.py:1568-1573`), the set of values a payload can actually carry is
`{"whole_object_syntax", "patch"}` — `whole_object_syntax` when no parseable
baseline exists yet (`llm/repair.py:1612`), `patch` once one does
(`llm/repair.py:1581`). The reader is
`workflow/nonconjecture_recovery.py:1002`,
`_authority(mode in {"patch", "full"}, "repair mode is invalid")`. `full` is a
name for the whole-object case that nothing in `src/` has ever emitted; the
reader's own next line, `if mode == "full": return tuple(pointers), raw_value`
(`nonconjecture_recovery.py:1029-1030`), implements exactly the
`whole_object_syntax` semantics — return the raw response as the complete
replacement candidate, applying no patch. So the reader was written to handle
the whole-object mode and named it something the writer never says. Every
`whole_object_syntax` payload that reaches `_repair_authority` therefore raises
`NonConjectureRecoveryAuthorityError("repair mode is invalid")`, deterministically
on payload shape rather than stochastically.

Evidence:
  - `experiments/2026-08-28-audit-run-problems/probes/q5_repair_vocabulary.py`
    (run on this tree at 2a5e984c8, exit 0, five PASS lines) -> both
    vocabularies asserted against live source and all three committed roots;
    intersection is `{'patch'}`; `full` emitted nowhere in `src/`;
    `whole_object_syntax` emitted by the producer and rejected by the checker.
  - `experiments/2026-08-28-audit-run-problems/probes/q5_repair_payloads.json`
    -> 56 repair payloads across three roots: 36 `whole_object_syntax`, 20
    `patch`, 0 `full`, 0 `initial`. Confirms both that the illegal value is the
    COMMON one and that `initial` never reaches a payload. Structural split, the
    one the fix turns on: every `whole_object_syntax` row carries
    `authorized_pointers: []` and `repair_index: 1`; every `patch` row carries a
    non-empty canonical pointer list.
  - `origin/claude/spec-to-code-technique-k5209o`,
    `experiments/2026-08-27-change-technique-run/failed-epoch5-run-456885c5.../run-status.json`
    -> `state: "failed"`, `stop_reason: "operational_failure"`,
    `message: "repair mode is invalid"`, `cycle: 2`, `phase: "stop"`.
  - the same root's `run-result.json` -> `error_type:
    "NonConjectureRecoveryAuthorityError"`, `error: "repair mode is invalid"`,
    `mode: "route_seat_compact_recovery"`, `event_horizon_seq: 417`, and a
    `contract_decompositions` block whose `atomic_work_attempts` are
    parent/child pairs of `work_kind: "atomic_child"` (repair_index 0) and
    `work_kind: "schema_repair"` (repair_index 1, and 2 for
    `candidate-slot-003`) under `atomic_contract_id:
    "conjecturer.atomic-candidate.v1"`.
  - AUDIT_REPORT.md §F-D -> the audit's own tabulation of the same two
    vocabularies and the same per-root payload counts (cause LOCATED there;
    this phase adds the call-site attribution below and the reader's `full`
    branch as the evidence for WHICH side is wrong).

Call site (audit residue item 3, settled from the record before the repro
confirms it): the failing reader is reached through
`workflow/atomic_recovery.py:68-71`
(`if preparation.task_kind.value == "repair": _pointers, repaired =
_repair_authority(...)`), called from
`rules/conj.py:531` inside `_v6_atomic_conjecture_fallback` — the branch that,
finding a decomposition child work item whose preparation payload already
matches, recovers its stored output instead of re-dispatching
(`rules/conj.py:517-533`). `recover_atomic_child_output` selects
`descendants[-1]` among `repair.semantic-task.v1` items whose
`parent_work_id` is the child's own preparation id, which is precisely the
parent/child chain the epoch-5 `run-result.json` records for each
`candidate-slot-00N`. The alternative reader,
`nonconjecture_recovery.py:1194`, sits in `recover_nonconjecture_admission`
and would report a NON-conjecture task; epoch 5's decomposition is under the
CONJECTURER seat (`role: "conjecturer"`, `source_contract_id:
"conjecturer.turn.v6"`), so that path is not the one taken.

Implicated code:
  - `src/deepreason/llm/repair.py:1505`   the producer's `mode` Literal
  - `src/deepreason/workflow/nonconjecture_recovery.py:1002` the retyped set
  - `src/deepreason/workflow/atomic_recovery.py:68-71`  the live call site

Falsifiable prediction (what dr-reproduce must show):
    A stub-driven offline run that builds one atomic decomposition child whose
    latest `repair.semantic-task.v1` descendant carries
    `mode == "whole_object_syntax"` and `authorized_pointers == []`, then calls
    `recover_atomic_child_output(harness, manifest, service, root_item,
    contract)`, raises
    `NonConjectureRecoveryAuthorityError("repair mode is invalid")` on the
    pre-fix tree — from `_repair_authority`, reached via
    `atomic_recovery.py:68-71`, with the traceback naming
    `recover_atomic_child_output` and NOT
    `recover_nonconjecture_admission`. The same call returns a compiled,
    admitted child output on the fixed tree.

Ruled out: "the vocabulary is fine and the CALLER is wrong — a
`whole_object_syntax` child should never reach the authority at all." Refuted
by the reader itself: `nonconjecture_recovery.py:1029-1030` carries a dedicated
whole-object branch (`if mode == "full": return tuple(pointers), raw_value`)
that returns the raw response as the whole candidate with no patch applied.
A reader that had no business seeing whole-object repairs would not carry a
whole-object branch. Refuted a second time by the payload census: a
`whole_object_syntax` child is a durable repair work item with its own
provider attempt and its own admitted terminal (epoch 5's `run-result.json`
shows `terminal_status: "completed"` on five of them), so refusing to
terminalize it would strand real, already-paid-for work rather than protect
anything. The bug is the NAME, not the reachability.

Also ruled out, cheaply: a recurrence of a recorded trap. `docs/map/`'s
`Traps` sections for `SEAM-llm-x-workflow`, `SEAM-rules-x-workflow` and
`SUB-workflow` carry four repair-related entries (the repaired child is a
different work item; a budget denial is not a recovery failure; a repair's own
`diagnostic_ref` is the NEXT turn's; repair capacity is reserved before the
provider answers). None names the mode vocabulary. `grep -rn 'repair mode'
docs/map/ tests/` returns nothing. This is a NEW failure mode and earns a new
`Traps` entry in the fix commit.
