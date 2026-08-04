# Request: Execute Rung 6 — qualify plugins the way models are qualified
Captured: 2026-08-04 from the operator's session-opening message, plus
the Rung 6 section of `docs/HANDOVER_2026-08-03.md` which the operator's
message names as the thing to execute (same adoption pattern rung 1 used:
"operator words authorizing it: this handover, adopted by the operator").

## Verbatim

> Branch claude/delivery-rungs-handover-m22sdy. Preflight per
> dr-drive-harness: resync the branch, editable install, read CLAUDE.md.
> Then read docs/HANDOVER_2026-08-03.md — rungs 1–5 are delivered; the
> newest experiments/*/DELIVERY.md files are the state.
> Execute Rung 6 via dr-change-orchestrator. It is DESIGN-AND-STOP: route
> through dr-spec-change ONLY. The deliverable is SPEC.md with acceptance
> checks and a cost analysis, committed and pushed — then STOP and present
> it. Do not plan or execute steps until I reply in my own words.
> Build the folklore-promise inventory by walking sources, not recall:
> every docs/map/CON-*.md document's invariants and Traps sections,
> CLAUDE.md's hard-won invariants list, and docs/ERRATA.md.
> P7 (the parked verify_root defect) stays parked. One rung only.

> `docs/HANDOVER_2026-08-03.md`, Rung 6 section, adopted by this request:
> "### Rung 6 — qualify plugins the way models are qualified
> [DESIGN-AND-STOP]
> Route: `dr-change-orchestrator` through dr-spec-change ONLY.
> Goal: a SPEC for a conformance battery a registered module must pass
> before a run accepts it — including promises that are currently
> folklore (e.g. "the operator's seed question always wins rank ties").
> Deliverable is SPEC.md with acceptance checks and a cost analysis.
> STOP after committing SPEC.md; present it; do not plan or execute
> steps until the operator replies in their own words."

## Requirements

R1 (process): "Preflight per dr-drive-harness: resync the branch,
editable install, read CLAUDE.md." — DONE before this ledger was opened
(see below).

R2 (process): "Then read docs/HANDOVER_2026-08-03.md — rungs 1–5 are
delivered; the newest experiments/*/DELIVERY.md files are the state." —
DONE before this ledger was opened.

R3 (process): "Execute Rung 6 via dr-change-orchestrator."

R4 (process): "It is DESIGN-AND-STOP: route through dr-spec-change
ONLY."

R5 (artifact): "The deliverable is SPEC.md with acceptance checks and a
cost analysis, committed and pushed"

R6 (process): "then STOP and present it."

R7 (process): "Do not plan or execute steps until I reply in my own
words."

R8 (artifact): "Build the folklore-promise inventory by walking
sources, not recall: every docs/map/CON-*.md document's invariants and
Traps sections, CLAUDE.md's hard-won invariants list, and
docs/ERRATA.md."

R9 (process): "P7 (the parked verify_root defect) stays parked."

R10 (process): "One rung only."

R11 (artifact, from the adopted handover text): "a SPEC for a
conformance battery a registered module must pass before a run accepts
it — including promises that are currently folklore (e.g. 'the
operator's seed question always wins rank ties')."

## Standing constraints

C1: "It is DESIGN-AND-STOP: route through dr-spec-change ONLY." — the
operator's message; binds R3-R7, forbids `dr-plan-steps`/
`dr-execute-step`/`dr-validate-change`/`dr-deliver-change` in this
tranche.

C2: "Do not plan or execute steps until I reply in my own words." —
the operator's message; the tranche ends at a committed, pushed SPEC.md
and an ended turn, not an implementation.

C3: "P7 (the parked verify_root defect) stays parked." — the operator's
message; P7 is documented in
`experiments/2026-08-04-change-rung5-dumb-alternative-backend/DELIVERY.md`
("Post-delivery 3", Arm B's `attempt-validity` violation) and must not
be fixed, investigated as a fix target, or folded into this SPEC.

C4: "One rung only." — the operator's message; no rung 7 work in this
tranche.

C5 (from the adopted handover, Executor calibration section): "Stop
conditions are hard stops, not suggestions. When a rung says
DESIGN-AND-STOP, the deliverable is a document and the tranche ends
there — implementation without the operator's reply is a defect you
caused."

C6 (from the adopted handover, Executor calibration section): "The
frozen surfaces (`docs/map/INV-frozen-surfaces.md`) bind every rung:
state digests, harness event application, replay-validation formats,
manifest schemas AND validators, qualification subjects."

C7 (from `docs/HANDOVER_2026-08-03.md`, Rung 3's ERRATA E10 correction,
generalized rule for remaining rungs): "accept lines state PROPERTIES;
any named mechanism is a suggestion the spec phase must verify for
reachability." Binds how R11's acceptance checks must be written.

C8 (from `.claude/skills/dr-spec-change/SKILL.md`, landed 2026-08-04 in
`experiments/2026-08-04-change-spec-judgment-guardrails/`, itself
scoped "Out of scope: Rung-6 folklore-promise source inventory (C1 —
goes in the operator's rung-6 instruction)" — i.e. this tranche is the
instruction that discharges it): DESIGN-AND-STOP specs require a
Measurements section (every load-bearing claim backed by pasted command
output), a priced Options table, a Blast-radius census, and a final
six-question rubric pass before the spec is considered done.

## Open questions (for dr-spec-change)

Q1: "the operator's seed question always wins rank ties" is given as
one EXAMPLE folklore promise ("e.g."). The full inventory must be built
by walking `docs/map/CON-*.md` Invariants/Traps, `CLAUDE.md`'s hard-won
invariants list, and `docs/ERRATA.md` per R8 — the words do not name an
exhaustive list, so the spec phase must derive one and record how each
candidate promise was found (source pointer), not just assert it exists.

Q2: "a registered module" — the rung-4/5 precedent scoped "registered
modules" to `SCHOOL_POPULATION` only (operator confirmed A1 in rung 4's
post-delivery). Rung 6's words do not restate that scope. The spec
phase must decide whether the conformance battery covers
`SCHOOL_POPULATION` only (consistent with the confirmed A1) or is
designed generally with `SCHOOL_POPULATION` as the sole populated
instance, and record which.

Q3: "a conformance battery ... must pass before a run accepts it" does
not say what happens on failure (run refuses to start? registration
itself is refused? a warning is recorded?) — the spec phase must choose
the smallest reading consistent with the existing registry precedent
(`verification/registry.py`: fingerprint pinned at registration,
re-checked on call) and record the assumption.

Q4: "a cost analysis" is not scoped further — the spec phase must
decide what it costs (wall-clock per battery run, whether it reruns
per-registration or is cached, interaction with the qualification
cache) and price it, following the rung-4 M1-M5 measured-precedent
style C8 requires.

## Amendments

(none yet)
