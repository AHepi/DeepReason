# Request: spec-phase judgment guardrails (P6 promotion)

Captured 2026-08-04, monitor session. Authority: the operator's verbatim
words below. Context: PARKED P6 in the rung-5 tranche — fixture-drift
forecasting was the weakest part of two consecutive specs, both misses
made under the MORE capable model, so the fix is mechanization, not
capability. Goal: make rungs 6 and 7 (pure DESIGN-AND-STOP, spec-only
deliverables) completable by Sonnet-class executors.

## Operator's words (verbatim)

> One process note worth your attention, in PARKED as P6: fixture-drift
> forecasting was the weakest part of two consecutive specs. Rung 4's
> prediction was too narrow; rung 5's spec predicted nothing and missed
> a rung 3 test that pinned "exactly one backend" — the very state this
> rung exists to change. The full gate caught both, and both were
> handled correctly rather than papered over, but a spec-phase habit of
> grepping for tests asserting on the thing being changed would have
> caught them earlier.
>
> I think that was maybe my fault. I used Opus 5 for half of rung 4 and
> all of Rung 5. Opus 5 is significantly more capable than Sonnet 5.
> What would need to improve to get 6 and 7 done with Sonnet 5. I mean
> workflow and tool wise?

Monitor proposed four improvements; offered to implement 1, 2 and 4 as
skill changes, noting item 3 (rung-6 folklore-promise inventory by
sources) belongs in the rung-6 instruction, not the general workflow.

> Ok do it.

## Requirements

- R1: Mechanize fixture-drift forecasting in `dr-spec-change` — a
  mandatory blast-radius census: grep tests/ and docs/map for every
  changed symbol/file, paste the hit list into SPEC.md, classify each
  hit expected-to-move or must-not-move.
- R2: A DESIGN-AND-STOP spec shape in `dr-spec-change` — mandatory
  Measurements section (every design claim a pasted command output) and
  priced Options table (files, frozen contact, lines, risk; rejections
  cite measurements). The rung-4 M1-M5 precedent made general.
- R3: A self-review rubric pass in `dr-spec-change`, run as the last
  act before committing/stopping — reviewer stance, any "no" routes
  back to the failing step.

## Constraints

- C1: Item 3 (source-inventory instruction for rung 6) is explicitly
  OUT of this tranche — it goes in the operator's rung-6 instruction.
- C2: General-use wording, not experiment-specific (the operator's
  standing rule for workflow promotions: "Remember it's for general
  use").
- C3: Skill files only; no src/, no map documents.
