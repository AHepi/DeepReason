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
5. **Frozen-surface diff — paste it, empty or explained:**

        git diff --stat <tranche-base>..HEAD -- \
          src/deepreason/capabilities/state.py src/deepreason/harness.py \
          src/deepreason/invariants.py src/deepreason/run_manifest.py \
          src/deepreason/qualification.py

   Empty output is the expected result and is pasted as proof. Non-empty
   output is a FAIL unless REQUEST.md quotes the operator approving that
   exact surface — convention guards these files at design time, but this
   paste is the one MECHANICAL tripwire on the path, so it is not optional.

6. **Packaging-surface check.** If the change touched pyproject.toml,
   CLI entry points, the MCP server surface, or the wheel layout: run
   `python scripts/wheel_smoke.py` (plus `python -u
   scripts/wheel_operational_smoke.py` when the operational
   provider-facing surface moved) and paste the last lines. The smokes
   pin expected sets and hashes; a surface change whose commit did not
   update those pins is a FAIL. If the surface did not move, write
   "packaging surface untouched — smoke not owed": the skip must be a
   recorded decision, not an omission.

7. **Map validation — the documentation half of the gate:**

        python tools/docs_verify.py          # must report 0 failed
        python tools/docs_verify.py --audit  # must report 0 findings
        python tools/docs_verify.py --links  # must report 0 dangling
        python tools/docs_verify.py --coverage  # 0 findings on swept seams
        python tools/docs_verify.py --stale  # read; judge each entry

   A failing check is a FAIL verdict exactly like a failing test: it
   means a document now asserts something untrue about the tree, and
   shipping it is shipping a lie the next reader will act on.
   `--stale` is advisory, but every entry it lists must be either
   updated or explicitly dismissed in VALIDATION.md with the reason —
   silence about a stale document is how the map dies.
   Confirm too that behaviour the change ADDED is covered by at least
   one new map check. A change with no new check has documented nothing
   falsifiable. And if the change added a typed-record OBSERVABLE (a
   field, record type, or finding), confirm a sweep probe for it exists
   or is specced as its own follow-up commit — "sweep byte-identical"
   is trivially true for data the sweep never reads, so an observable
   with no probe and no written justification is a FAIL.
8. Requirement sweep: for every R in REQUEST.md, one line — which
   acceptance output demonstrates it, or why it is legitimately
   deferred (operator's words required). An R with neither is a FAIL:
   the work is incomplete no matter how green the gate is.
9. Assumption audit: list SPEC.md's assumptions A1..An in
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
    ## Map
    docs_verify: <N documents, M checks, 0 failed> : PASS|FAIL
    docs_verify --audit: <N findings> : PASS|FAIL
    docs_verify --links: <N dangling> : PASS|FAIL
    docs_verify --coverage: <N findings, M seams without a Sweep header> : PASS|FAIL
    docs_verify --stale: <each entry, updated or dismissed with reason>
    new checks added by this change: <ids/files, or "none - see why">
    record observables added vs sweep probes: <none | observable -> probe/justification>
    wheel smoke: <pasted tail | "packaging surface untouched — smoke not owed">
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
- No file other than VALIDATION.md (and PARKED.md) modified. A map
  document that needs updating is a FAIL routed back to
  `dr-execute-step`, not something validation fixes in passing —
  validation that edits the thing it validates proves nothing.
- Return to the orchestrator: PASS -> dr-deliver-change; FAIL ->
  dr-plan-steps with the FAIL detail.
