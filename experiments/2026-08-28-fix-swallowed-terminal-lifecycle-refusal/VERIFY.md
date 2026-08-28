# VERIFY — measured against GOAL.md's five criteria

Every number below is a command's output, committed under `proof/`.

## Criterion 1 — the refusal is a TYPED exception carrying its counts

`build_stopped_lifecycle` over a real `outstanding_work_snapshot` raises
`UnfinishedWorkflowAuthorityError` with
`code="STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY"`,
`outstanding_work_count` and `unconsumed_bound_call_count`, and remains a
`ValueError` subclass carrying the historical message substring.

`tests/test_terminal_lifecycle_refusal_is_recorded.py
::test_the_stopped_refusal_is_typed_and_carries_the_counts_that_caused_it`
— **PASS**. Mutation (restore the bare `ValueError`) → RED,
`proof/mutation3_red.txt`.

## Criterion 2 — the handler is specific, and RECORDS what it caught

Fresh soak root minted with the fixed writer (`--case epoch3 --cycles 3`,
`proof/soak-report-after-epoch3-c3.json`, soak exit 0 clean):

`run-result.json` (`proof/after_run_result_refusal.json`):

```json
{
  "schema": "deepreason-terminal-lifecycle-refusal-v1",
  "code": "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY",
  "detail": "STOPPED refuses unfinished workflow authority: 11 outstanding work items, 0 unconsumed bound calls",
  "outstanding_work": 11,
  "unconsumed_bound_calls": 0
}
```

`run-status.json` (`proof/after_run_status.json`):
`{"state": "completed", "stop_reason": "budget_exhausted",
"terminal_lifecycle_refusal": "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY",
"token_spend": 139356}`

The recorded count of 11 is independently corroborated: `verify_root` on
that root reports `outstanding_work_orders` as a list of **11** ids, and 0
violations. The refusal record is not the writer's word about itself.

Mutations → RED: removing the typed `except`
(`proof/mutation1_red.txt`), restoring the original
`except ValueError: return None` (`proof/mutation2_red.txt`).

## Criterion 3 — `results` no longer claims the continuation

Same root, before and after (`proof/before_results.txt`,
`proof/after_results.txt`):

| line | before the fix | after |
|---|---|---|
| stands at a valid typed terminal | yes | yes |
| stop reason is resumable | yes | yes |
| carries the lifecycle decision `continue` resumes from | *(line did not exist)* | **no** |
| the run recorded this reason for refusing that receipt | *(line did not exist)* | **STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY** |
| ready for `amend` / `continue` | **yes** | **no** |

`deepreason continue` on that root: `CONTINUE_TYPED_STOP_REQUIRED`, rc=1 —
IDENTICAL before and after (`proof/before_continue.txt`,
`proof/after_continue.txt`). The two surfaces now agree, and they agree on
the refusal rather than on the promise, which is what P6 required.

**A note on the audit probe, so its output is not misread.**
`proof/q4_after.json` still prints `"surfaces_disagree": true`. That column
is computed inside the audit's own probe from
`reason in RESUMABLE_STOP_REASONS` — a hardcoded copy of the predicate
`results` USED TO consult. The probe measures the record, which is
unchanged; it does not measure the reader, which is what moved. The
reader's actual output is `proof/after_results.txt`.

## Criterion 4 — the CONTROL still works

`test_an_unrefused_terminal_still_reports_ready_and_records_no_refusal`:
an ordinary manifest-launched root carries its terminal lifecycle decision,
emits NO refusal key at all (`exclude_none=True`), and reports
`continuation_authority: True`, `amend_ready: True`. **PASS**.

Mutations → RED: dropping the third conjunct
(`proof/mutation4_red.txt`, which also proves criterion 3 is doing work),
and hard-wiring `amend_ready` to `False` (`proof/mutation5_red.txt`, which
proves the control is doing work).

## Criterion 5 — the gate, the map, and the record

- Full gate: see `proof/gate.txt` — **0 failed** required and met.
- `python tools/docs_verify.py` FULL mode: **4 failed**, exactly the
  session baseline (3 shallow-clone `CON-run-identity.md` git-history
  checks that cannot resolve in this container, and the 1 pre-existing
  falsified `INV-frozen-surfaces.md:181` census). `proof/docs_verify.txt`.
  One check of mine went red mid-tranche and was REBOUND rather than
  deleted: `SEAM-scheduler-x-workflow.md:120` asserted the literal string
  `"STOPPED refuses unfinished workflow authority"` inside
  `build_stopped_lifecycle`'s source, which the fix moved into the
  exception class. It now asserts the raise, the message on the class, and
  that the class subclasses `ValueError` — a strictly stronger binding of
  the same claim.
- Map moved in the same commits: `SUB-application.md` (a Traps entry with
  its own check), `SUB-workflow.md` (the typed refusal at its entry point),
  `SEAM-scheduler-x-workflow.md` (the stop-terminal row, and the rebound
  check). `Verified-at:` advanced on all three, having actually re-run
  their checks.

## Residue — what this tranche did NOT prove

Stated because "accepted does not mean true".

1. **Whether the refusal is the RIGHT behaviour is untouched and open.**
   Eleven outstanding work orders at a budget stop may or may not be a
   condition that ought to prevent continuation. This tranche made the
   current answer visible; P2 asks the operator for the right one. Every
   root that could not continue before still cannot continue.
2. **The gate regression injects the refusal rather than growing it.** The
   caller's handling is what is under test, and that is where the defect
   is; the refusal firing on real outstanding authority is proven
   separately (criterion 1, a real snapshot) and end to end by the 98-second
   soak (criterion 2), which is too slow to sit in the gate. Declared in
   the test's own docstring, not only here.
3. **No live run.** The fix is on write paths reached identically offline
   and online, and the operator's standing preference for live evidence is
   satisfied here by generated soak roots rather than hand-built fixtures.
   A live launch would add cost and no discrimination.
4. **Committed roots minted before this fix carry no refusal record**, so
   `results` reports their `lifecycle_refusal` as the typed absence
   `NO_LIFECYCLE_REFUSAL_RECORD` while correctly reporting
   `amend_ready: no`. The reader recovers WHETHER, not WHY, for those. A
   root is evidence and is never edited; that residue is permanent and
   correct.
