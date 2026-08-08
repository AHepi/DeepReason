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
   pick a side silently). Every stop presented to the operator leads
   with the decision needed in ONE sentence, the options priced, and a
   recommendation with its reason — a stop the operator must
   interrogate is half a stop.

## Map preflight (do this before routing, every time)

`docs/map/` is the navigation layer over 125k lines of source. Scoping
from grep instead of from the map is how a change misses a call site.

1. Read `docs/map/INDEX.md` and resolve the work to ids:
   `DR-SUB-<pkg>`, `DR-CON-<concept>`, `DR-SEAM-<a>-x-<b>`.
2. If the work spans two things, **read the SEAM document first**. It
   says which fraction of each side is actually involved, which is
   usually small. Reading both subsystem documents first is reading ten
   times more than you need. The file is `docs/map/SEAM-<a>-x-<b>.md`,
   sides in alphabetical order; the worked recipe for changing one is
   `docs/map/REC-change-a-seam.md`.
3. Read `docs/map/INV-frozen-surfaces.md` BEFORE designing anything.
   Discovering a frozen surface after the code is written is the
   expensive order to discover it in.
4. Record the resolved ids in the tranche's first artifact (GOAL.md or
   REQUEST.md). Every later phase starts from the same map.

If the map has no id for something the work touches, that is a finding,
not a blocker: say so, and creating the missing document becomes part of
the tranche. `docs/map/SCHEMA.md` is the contract for writing one.

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
before. Also load `dr-explain-to-operator` once per session, BEFORE
your first message the operator will see: it binds every
operator-facing message (intermediary status reports included, not
just the final one) — worry first, technical terms glossed in plain
language as you go, one closing analogy on the final output.

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
