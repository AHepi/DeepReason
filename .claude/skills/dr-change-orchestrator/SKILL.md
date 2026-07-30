---
name: dr-change-orchestrator
description: Entry point for implementing an operator-suggested change to DeepReason. Routes through capture, spec, plan, stepwise execution, validation, and delivery — one phase at a time, with a verbatim request ledger nothing may drift from. Use when the operator says "add", "change", "make it", "I want", or suggests any modification.
---

# DeepReason change orchestrator

The operator has suggested a change. Your job is to implement exactly
that change — not the change you would have designed, not the
neighboring improvement, not a partial version you forgot to finish.
This workflow differs from `deepreason-orchestrator` (defects): there
is no diagnosis; the authority is the OPERATOR'S WORDS, and every
phase traces back to them.

## The ledger rule (the anti-forgetting mechanism)

`REQUEST.md` is the single source of authority. It holds the
operator's suggestion VERBATIM, split into numbered requirements
(R1, R2, ...). Every later artifact cites requirement numbers.

- **Before starting ANY phase, re-read REQUEST.md and CHECKLIST.md in
  full.** Context windows lose earlier turns; the ledger does not.
- If the operator sends a new message mid-workflow: APPEND it to
  REQUEST.md verbatim as new numbered requirements (or amendments
  "R2a supersedes R2") BEFORE acting on it, then route to
  `dr-spec-change` to reconcile. Never absorb new instructions
  silently into the current step.
- A requirement is never deleted, only marked `superseded-by:<n>` or
  `deferred (operator approved <where>)`.

## Scope contract

1. Implement what REQUEST.md says. Where it is silent, choose the
   smallest reasonable interpretation and RECORD the assumption in
   SPEC.md; where two readings differ materially in effort or
   behavior, stop and ask — one batched question, not a dribble.
   Before ANY question, run dr-decide-or-ask: derive the answer from
   the operator's recorded values first; only genuine forks earn
   their attention, always led by a recommendation.
2. Anything you notice that is broken but not requested: one line in
   `PARKED.md` (a defect goes to the `deepreason-orchestrator`
   workflow later). Never fix it now.
3. Stop conditions: a step fails twice the same way; the spec turns
   out to require touching frozen-record semantics (state digests,
   event application, replay formats, qualification subjects); the
   estimated diff exceeds SPEC.md's budget; or a requirement
   contradicts the record/codebase (report the contradiction, do not
   pick a side silently).

## Environment preflight

Same as `deepreason-orchestrator`: verify branch head, working-tree
state, `deepreason` importable (else `pip install -e .
--break-system-packages -q`); resync the branch if the container
rolled back. Do this once before routing.

## Routing table

| State of the tranche | Route to |
|---|---|
| Operator words not yet in REQUEST.md | `dr-capture-request` |
| REQUEST.md exists, no SPEC.md (or new requirements appended) | `dr-spec-change` |
| SPEC.md approved, no CHECKLIST.md | `dr-plan-steps` |
| CHECKLIST.md has an unchecked step | `dr-execute-step` (exactly one step) |
| All steps checked, no VALIDATION.md | `dr-validate-change` |
| VALIDATION.md verdict PASS | `dr-deliver-change` |
| VALIDATION.md verdict FAIL | back to `dr-plan-steps` with the failure appended (re-plan the failing steps only) |

After EVERY phase (and every executed step): commit and push the
tranche directory. The container can vanish at any time.

## Tranche layout

One directory per suggestion, e.g. `experiments/<date>-change-<slug>/`:
`REQUEST.md`, `SPEC.md`, `CHECKLIST.md`, `VALIDATION.md`,
`DELIVERY.md`, `PARKED.md`.

## Hard prohibitions

- No code changes outside `dr-execute-step`, and no step outside
  CHECKLIST.md.
- Never edit committed run roots; never commit `env`/credential files.
- Never mark a checklist step done without pasting its done-criterion
  output.
- Never report the change complete without the R-by-R reconciliation
  table from `dr-deliver-change`.
