# REPRO — the defect, demonstrated on main before any patch

Two halves, both offline, both on this branch at base `5df7246ad`.

## Half 1 — the asymmetry, on UNFIXED main

Script: `repro_prefix.py` (below, and preserved in this directory).
Structural by AST over the module that actually imports, not by
grepping: `_plan_conjecture_context` occurs in this module's own prose,
and a string search would score a comment as a call site.

Output, verbatim, run 2026-09-03 on `5df7246ad`:

```
context_plan assignments in Scheduler.step: 3
  line  252 (rel):  context_plan = self._plan_conjecture_context(problem, school_id)
  line  256 (rel):  context_plan = None
  line  315 (rel):  context_plan = self._plan_conjecture_context(problem, school_id)

_plan_conjecture_context call sites inside step: 2
v6 null-outs (context_plan = None): 1

VERDICT: REPRODUCED -- two planner call sites, only ONE null-out.
The second (ConjectureContextStale retry) hands conj a live plan.

rules/conj.py guard the retry value reaches:
    conjecture_context_plan is not None:
    raise ValueError("v6 conjecture context must be planned after durable work preparation")
```

Two planner calls, one v6 null-out. The unguarded one is the
`ConjectureContextStale` retry, and the value it produces meets a
`raise` on the other side of the seam. That is the whole defect, and
it is the shape the record's two roots stopped on
(DIAGNOSIS.md §Record evidence).

## Half 2 — the mutation proof, ON MAIN, after the fix

The originating branch proved the fix by mutation
(`06b0d9fd9`: "restoring the old retry line gives 2 failed / 3 passed,
restoring the fix gives 5 passed, with identical test bytes"). That
proof is re-run here, on main, because a proof performed on another
tree is a claim about that tree.

Protocol, exactly:

1. Apply the fix and the regression file.
2. GREEN: `python -m pytest tests/test_scheduler_v6_context_plan_retry.py -q`.
3. MUTATE — restore ONLY the pre-fix retry line
   (`context_plan = self._plan_conjecture_context(problem, school_id)`
   at the `except ConjectureContextStale:` site), nothing else.
4. RED: the same command, same test bytes.
5. Restore the fix; confirm GREEN again.
6. Record the test file's sha256 at every step; identical throughout,
   or the proof is void.

Results are recorded in §Results below, filled in after the run.

## Results

<!-- filled after the mutation run -->
