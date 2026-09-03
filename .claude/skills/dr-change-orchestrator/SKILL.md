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
   Before asking, load `dr-ask-the-right-question`: derive the answer
   from the record and the operator's recorded values first; a fork
   the dominance test kills is decided and noted, not asked.
2. Anything you notice that is broken but not requested: into
   `PARKED.md` (a defect goes to the `deepreason-orchestrator`
   workflow later). Never fix it now. Write the entry for its future
   runner, at park time: one line of WHAT, then a ready-to-send prompt
   (route, one-goal statement, evidence pointers, end state) — the
   follow-up should cost the operator a paste, not an authoring
   session.
3. Stop conditions: a step fails twice the same way; the spec turns
   out to require touching frozen-record semantics (state digests,
   event application, replay formats, qualification subjects); the
   estimated diff exceeds SPEC.md's budget; or a requirement
   contradicts the record/codebase (report the contradiction, do not
   pick a side silently). Every stop follows the standard format —
   decision in ONE sentence, options priced, a recommendation with its
   reason — canonical in `dr-drive-harness` §6's calibration note.

## Map preflight (do this before routing, every time)

Full procedure, canonical: `dr-drive-harness` §4 — `docs/map/INDEX.md`
→ `INV-frozen-surfaces.md` → seam document (before either subsystem) →
record the resolved ids in the tranche's first artifact.

The map is maintained by the phases that change code, in the same
commit — see `dr-execute-step` and `dr-implement-fix`. Nothing else may
advance a `Verified-at:` stamp.

## Environment preflight

Same as `deepreason-orchestrator`: verify branch head, working-tree
state, `deepreason` importable (else `pip install -e .
--break-system-packages -q`); resync the branch if the container
rolled back. Do this once before routing. The full driving manual —
preflight, CLI lifecycle, ladders, where to look — is
`dr-drive-harness`; load it if this session has not run the harness
before. Also load `pinker-write-for-readers` once per session, BEFORE
your first message the operator will see: it binds every
operator-facing message (intermediary status reports included, not
just the final one) — worry first, the operator's own vocabulary
instead of terms of art (a message that has to define a term has
failed — CLAUDE.md Conventions, 2026-09-03), one closing analogy on
the final output.

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
tranche directory — canonical rationale in `dr-drive-harness` §1.

## Tranche layout

One directory per suggestion, e.g. `experiments/<date>-change-<slug>/`:
`REQUEST.md`, `SPEC.md`, `CHECKLIST.md`, `VALIDATION.md`,
`DELIVERY.md`, `PARKED.md`.

## Hard prohibitions

- No code changes outside `dr-execute-step`, and no step outside
  CHECKLIST.md.
- Never edit committed run roots; never commit `env`/credential files —
  both procedures canonical in `dr-drive-harness` §1/§3.
- Never mark a checklist step done without pasting its done-criterion
  output.
- Never report the change complete without the R-by-R reconciliation
  table from `dr-deliver-change`.
