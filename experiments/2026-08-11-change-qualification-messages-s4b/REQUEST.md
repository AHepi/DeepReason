# Request: per-role qualification error messages + a human-readable error surface, replacing the convoluted form with a schema-first intake tool

Captured: 2026-08-11 from the operator's seven-item program handover (a
single verbatim paragraph covering the change-family items of the
program: qualification-per-role/error-messages, and the human-readable
error surface + intake tool).

## Verbatim

> "The errata need to be checked and updated. The Spec needs updating,
> but carefully. The per role qualification needs to be per role with
> added error messages. Error messages are not human readable so this
> is where a fully kitted human readable surface needs creating. The
> form you showed is very convoluted and may not work for smaller
> models. So I'm thinking a tool should be the default for small
> models... The form also needs to be simple enough for a coding human
> to fill out and for later documentation. So maybe doing a bit of
> research on accepted standards will help. This repo is messy so maybe
> finding an appropriate format will be helpful. Sweep and smoke need to
> be checked. If they are out of date, that's a debugging error that
> goes into errata."

(The errata, spec, and sweep/smoke sentences are captured here verbatim
for completeness of the source paragraph, but are routed to Items 1, 2,
3, and 6 as separate investigation tranches per CLAUDE.md's cross-routing
rule — this REQUEST.md's own R-numbers below cover only the change-family
obligations: per-role qualification error messages and the human-readable
surface + intake tool.)

## Requirements

R1 (behavior): "The per role qualification needs to be per role with
added error messages." — qualification must be evaluated PER ROLE
(not only as one combination subject), and each qualification failure
must carry an added error message.

R2 (artifact): "Error messages are not human readable so this is where
a fully kitted human readable surface needs creating." — today's typed
error messages are not human-readable; a complete ("fully kitted")
human-readable surface must be created to sit alongside them.

R3 (process): "The form you showed is very convoluted and may not work
for smaller models." — the existing form (FORM_DR1_RUN_APPLICATION.md,
the interactive/prose intake artifact previously shown to the operator)
is judged too convoluted and is flagged as possibly unusable by smaller
models.

R4 (artifact): "So I'm thinking a tool should be the default for small
models..." — the operator's own proposed direction: a tool (not the
convoluted form) should be the DEFAULT intake path, at minimum for
smaller models.

R5 (behavior): "The form also needs to be simple enough for a coding
human to fill out and for later documentation." — whatever the intake
artifact becomes, it must be simple enough for a human developer to
fill out by hand, and suitable as documentation afterward.

R6 (process): "So maybe doing a bit of research on accepted standards
will help." — the operator directs a research step into accepted
(external, established) standards before designing the intake surface.

R7 (process): "This repo is messy so maybe finding an appropriate
format will be helpful." — (this line is captured here as it appears in
the same breath as R6's research directive, but its subject — docs/
organization — is Item 6's docs-format research, not this tranche's
intake-form design; kept here verbatim for provenance, routed to Item 6.)

## Standing constraints

C1: "The Spec needs updating, but carefully." — routed to Item 3; not
this tranche's obligation, but binds the program: spec changes are
append-only amendments, never edits to existing spec text (CLAUDE.md
map section: "never edit existing spec text").

C2 (from the task handover, not the operator's own paragraph but a
binding instruction on how this request must be executed): "Item 4 —
... DESIGN-AND-STOP; frozen surface 5 — no code without fresh operator
words." — R1/R2/R4/R5 may be designed (SPEC.md, decision sheet) this
window but no code may land without an explicit operator go-ahead
after this tranche's STOP.

C3 (from the task handover): the monitor's recommendation to VERIFY,
not inherit — "a schema'd file = the whole DR-1 conditional logic as
validation rules" — is a recommendation to weigh during dr-spec-change,
not a decision already made; C4 below is the counter-consideration the
same handover names.

C4 (from the task handover): "a validated file + validator beats an
interactive wizard for small models... and should be the default for
EVERY caller, not only small models" — the monitor's reasoning to weigh
against R4's narrower "default for small models" framing; dr-spec-change
must reconcile R4's verbatim scope against this broader recommendation
explicitly, not silently adopt the broader one.

## Open questions (for dr-spec-change)

Q1: R1 says qualification "needs to be per role" — does this mean
implementing S4b's parked Option 1 (per-role provenance qualification,
described in experiments/2026-08-06-change-qualification-per-seat-s4/
PARKED.md and its SPEC.md revision-1 "Option 1" sketch), or something
narrower (e.g. just per-role ERROR MESSAGES on top of the existing
Option 2b combination-subject qualification, without changing the
qualification unit itself)? PARKED.md already flags Option 1 as
frozen-surface-5 contact requiring its own dr-spec-change STOP — this
open question is exactly that STOP.

Q2: R2's "fully kitted" is not defined — does it mean every typed
error/refusal code across the whole public surface, or only
qualification-failure codes (the ones R1 is about)? The task handover's
Item 5 broadens this explicitly to "every typed error code across the
public surface" — dr-spec-change should adopt that broader scope and
say so, since it is the more specific, later instruction covering the
same ground.

Q3: R4's "default for small models" vs C4's "default for every caller"
— which scope does the SPEC adopt? dr-spec-change must decide and state
its reasoning; this is the single largest design fork in the tranche.

Q4: Is the "tool" in R4 a CLI validating command only, an MCP tool only,
or both? The task handover's Item 5 says both explicitly (CLI + MCP
tool wrapping the same validator) — dr-spec-change should adopt that.

## Amendments

(none yet — append-only; future operator words land here)
