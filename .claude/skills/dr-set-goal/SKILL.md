---
name: dr-set-goal
description: Turn a vague DeepReason problem statement into one bounded, falsifiable tranche goal (GOAL.md). Use at the start of every tranche, before any diagnosis or code reading.
---

# Set the tranche goal

Input: a problem statement (from the operator, a failed run, RESULTS.md,
or PARKED.md). Output: exactly one `GOAL.md`. Nothing else. You do not
read source code in this phase beyond confirming a file exists.

## Procedure

1. Restate the problem as ONE observable, checkable statement about the
   record or the tests. Good: "run-9175f0ec terminated budget_denied on
   all 8 question turns with zero provider calls." Bad: "the scheduler
   has issues."
2. Classify it:
   - `defect` — record/tests show behavior contradicting a documented
     guarantee (spec §, docstring, RESULTS.md claim).
   - `regression-risk` — behavior is undocumented but a change would
     alter it.
   - `capability-gap` — nothing is broken; something is missing.
   Only `defect` tranches may proceed to implementation without
   explicit operator approval; the other two stop after FIX.md
   (proposal) and report.
3. Write the success criterion as a command + expected output. It must
   be decidable by a machine, e.g.:
   - "`verify_root(<root>)` returns zero `conjecture-context`
     violations" or
   - "`pytest tests/test_x.py::test_y` passes and the full gate stays
     at 0 failed."
4. Write the boundary list: files/subsystems presumed in scope (max 3),
   and an explicit NOT-IN-SCOPE line for the nearest tempting neighbor.
5. Size check: if you cannot imagine the fix under ~150 changed lines
   and one commit, split the problem and pick the FIRST piece only;
   put the rest in PARKED.md.

## GOAL.md template (fill every field; delete nothing)

    # Goal: <one line>
    Class: defect | regression-risk | capability-gap
    Observed: <one sentence, with the record/test evidence pointer>
    Success criterion (machine-decidable):
        <command>
        <expected output>
    In scope: <max 3 paths/subsystems>
    NOT in scope: <the nearest tempting thing you will not touch>
    Budget: <=150 changed lines, 1 commit, <n> hours
    Stop conditions inherited from orchestrator: yes

## Exit criteria

- GOAL.md exists in the tranche directory, committed and pushed.
- You have NOT proposed a cause, a fix, or read implementation code.
- Return to the orchestrator.
