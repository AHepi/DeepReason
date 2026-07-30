---
name: dr-validate-change
description: Prove the completed change against every acceptance check in SPEC.md and the full DeepReason gate, producing VALIDATION.md. Use when every CHECKLIST.md step is checked. Validates only; never patches.
---

# Validate the change

Input: SPEC.md's acceptance checks + the finished checklist. Output:
VALIDATION.md with verdict PASS or FAIL. You run checks and record
outcomes. You do not fix anything — a failure routes back to
re-planning with evidence, which is cheaper than a hidden patch that
invalidates the checklist's audit trail.

## Procedure

1. Re-read REQUEST.md, SPEC.md, CHECKLIST.md in full. Yes, again —
   this is the phase that catches forgotten requirements, and it can
   only catch what it re-reads.
2. Run EVERY acceptance check in SPEC.md, in item order, even ones a
   checklist step already ran — steps prove local progress; this
   phase proves the assembled whole. Paste each real output.
3. Run the regression ring: the full gate
   (`pytest tests/ -q -n 4`) must end **0 failed**. A failure you
   caused is a FAIL verdict; a pre-existing failure you can prove
   pre-dates the change (`git stash` → rerun → `git stash pop`) is
   recorded as such and does not block, but goes to PARKED.md.
4. Behavior-preservation spot-check: if the change touched a reader
   or validator of the append-only record, re-run `verify_root` on
   one known-good committed root and one defect-era root — prior
   verdicts must be unchanged except where SPEC.md says otherwise.
5. Requirement sweep: for every R in REQUEST.md, one line — which
   acceptance output demonstrates it, or why it is legitimately
   deferred (operator's words required). An R with neither is a FAIL:
   the work is incomplete no matter how green the gate is.
6. Assumption audit: list SPEC.md's assumptions A1..An in
   VALIDATION.md so the delivery surfaces them to the operator.

## VALIDATION.md template

    # Validation for: <request headline>
    ## Acceptance checks
    S1: <command> -> <pasted output> : PASS|FAIL
    ...
    ## Full gate
    <last line pasted, e.g. "3107 passed, 7 skipped"> : PASS|FAIL
    ## Record-behavior preservation
    <root>: <unchanged | changed as specified> (or "n/a")
    ## Requirement sweep
    R1: demonstrated by S1 output | deferred (operator: "<quote>")
    ...
    ## Assumptions carried
    A1: <one line>
    ## Verdict: PASS | FAIL
    FAIL detail: <which check, real output, suspected step>

## Exit criteria

- VALIDATION.md committed and pushed, every acceptance check run with
  pasted output, every R swept.
- No file other than VALIDATION.md (and PARKED.md) modified.
- Return to the orchestrator: PASS -> dr-deliver-change; FAIL ->
  dr-plan-steps with the FAIL detail.
