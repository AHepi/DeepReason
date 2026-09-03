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

Run 2026-09-03 on this branch. Test file sha256
`03c84608a418455df5ea341d5ead01fde65c7c0c8ddfedd6fe00069d37c68858`,
identical at every step and identical to `06b0d9fd9`'s copy — verified
by `sha256sum` against `git show 06b0d9fd9:tests/...` before the first
run and printed again at each step below.

| step | tree | `pytest tests/test_scheduler_v6_context_plan_retry.py -q` |
|---|---|---|
| 2 | fix applied | **5 passed** |
| 3-4 | retry line restored to the pre-fix expression, nothing else | **2 failed, 3 passed** |
| 5 | fix restored | **5 passed** |

The two that fail under the mutation are exactly the structural pair —
`test_only_the_dispatch_rule_may_plan_conjecture_context` and
`test_conj_dispatch_uses_the_rule_at_every_site` — with the assertion

    assert '_plan_conjecture_context' == '_dispatch_conjecture_context_plan'

That is the same result the originating commit recorded on its own tree
("restoring the old retry line gives 2 failed / 3 passed, restoring the
fix gives 5 passed, with identical test bytes"). The proof now holds on
main.

`git diff --stat` on `scheduler.py` after step 5 shows zero drift from
the applied fix: the mutation left nothing behind.

Full log: `mutation.log` in this directory.

## The map checks are mutation-proven too

The two re-expressed map checks (DIAGNOSIS.md §Map) were run against
three separate mutations, to show neither was weakened into a check
that cannot fail:

| mutation | `SEAM-scheduler-x-workflow` check | `SEAM-schools-x-scratch` check |
|---|---|---|
| M1 — retry site restored to the direct planner call (the defect itself) | **rc=1 (red)** | rc=0 |
| M2 — the v6 rule deleted from the owner | **rc=1 (red)** | rc=0 |
| M3 — the owner stops forwarding the raw allocated `school_id` | rc=0 | **rc=1 (red)** |
| none (final tree) | rc=0 | rc=0 |

Each check goes red on its OWN claim and stays green on the other's,
which is what a check that is anchored rather than merely long looks
like. `SEAM-schools-x-scratch`'s claim was never single-ownership — it
pins that the plan receives the RAW allocated school id while `conj`
receives the leased-or-`None` form — so its indifference to M1 and M2
is correct, not a gap. Single-ownership is carried by
`SEAM-scheduler-x-workflow` and by the regression file.
