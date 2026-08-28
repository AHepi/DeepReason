# PARKED — not built here, deliberately

This experiment measured DISTINCTNESS and stopped there. Everything below is
registered as out of scope for this tranche and is left as a ready-to-send
prompt, not as code.

## Why D is the shape to park

Leg 2, at the calibrated metric, over 9 repetitions and 3 questions:

| arm | overall M1 | worst question | M2 | distinct ideas / 1k tokens |
|---|---|---|---|---|
| A direct | 5.1 | 1.7 | 0.1621 | 0.38 |
| B stratified | 6.4 | 5.7 | 0.2636 | 0.40 |
| C verbalized sampling | 17.6 | 3.4 | 0.2568 | 3.16 |
| **D stratified + VS** | **20.0** | **12.0** | **0.3146** | 3.12 |

D leads on overall distinctness and on the threshold-free distance, and it is
the only arm that never drops below 12 on any question — C collapses to 3.4
on the geometry construction question where D holds 12.0. C is marginally
cheaper per distinct idea; D is the one that does not fall over.

**This is not a quality claim.** No arm was shown to produce BETTER
conjectures. That is exactly what leg 3 below is for, and it is the reason
nothing is being wired in on this evidence alone.

## The parked prompt

One prompt, two legs, in the order they must run: the criticism leg first,
because it is what licenses the configuration leg.

```
Tranche: wire the winning conjecture-generation shape into DeepReason as
configuration, and first test whether its extra distinctness survives
criticism.

Read experiments/2026-08-28-diversity-generation/ in full before designing:
PREREG.md, PREREG_LEG2.md (both frozen before their data existed), RESULTS.md,
and metrics_leg2.json. The headline it establishes, and its limit:
direction-stratified verbalized sampling (arm D) produces ~4x the distinct
conjectures of repeated direct asking at ~8x the token efficiency per distinct
idea, with no yield cost — and DISTINCTNESS IS ALL THAT WAS MEASURED. Nothing
about quality was shown, and the registered hypotheses H1-H3 are INCONCLUSIVE
because the effect is question-dependent: on a tightly constrained geometric
construction question, verbalized sampling alone gave almost nothing (3.4 vs
1.7 for direct) and only the planning call lifted it (12.0). Treat that column
as the design constraint, not as noise.

LEG 3 FIRST — survival under criticism, in-harness. Route through
dr-change-orchestrator. The question this leg settles: does a more distinct
conjecture population survive criticism at the same rate, a better rate, or a
worse one? Design it as a matched-budget in-harness comparison between the
current conjecturer shape and arm D's shape, on a seed question from the
committed record, judged ONLY on typed outcomes — survivor counts,
defended-trial counts, stop_reason, verify_root — never on model prose.
Pre-register the survival criterion before any live call, and register in
advance what result would show arm D produces MORE candidates that criticism
kills, which is the outcome that would sink the whole idea. Follow CLAUDE.md's
live-run rules: green cycle_soak on the launch config before any ladder
launch, detached launch, snapshot loop.

LEG 4, only if leg 3 does not sink it — the configuration surface. Bind by the
modularity law (operator 2026-08-26: "There needs to be a priority that
enforces modularity. Customisation needs to be easy."): the generation shape
must be reachable as CONFIGURATION or a registered, versioned artifact, never
by editing code, behind a declared interface on the signal-contract pattern
(FROZEN change protocol, VERSIONED registry/policy, FREE parameters), with an
architecture test that goes RED when a consumer bypasses the interface or when
using the customization point requires a code edit. Read
docs/map/INDEX.md and the relevant SEAM document before either subsystem, and
docs/map/INV-frozen-surfaces.md before designing anything.

Three binding constraints carried forward from this experiment:

1. The verbalized probability numbers are a STEERING DEVICE, fabricated by
   construction. Nothing downstream may read them as estimates — not to rank,
   filter, weight, or order. This is the companion of the standing law that
   seats change how content is GENERATED, never what counts as EVIDENCE.
   experiments/2026-08-28-diversity-generation/analyse.py carries a
   mutation-proven AST guard enforcing exactly this; reuse the pattern.
2. The planning call must run on a FRESH context and must never be seeded with
   any prior candidate. Kong et al. (research note §6) found every prompt
   intervention failed inside a self-conditioning loop; the arm measured here
   is single-shot and stateless, and it stops being the measured arm the
   moment its own output feeds back into it.
3. Formalism is an option, never an obligation (operator, standing). A
   direction list must not become a schema that penalizes an informal
   conjecture, and no generation shape may weight outcomes on conjecture KIND.

Do not re-run the distinctness measurement. It is done, its raw record is
committed, and its residue is stated.
```

## Also parked

- **The geometry exception itself.** Why direction stratification lifts a
  constrained construction question while verbalized sampling does not is
  unexplained. The alternative explanation stated in RESULTS.md §4 — that a
  construction question simply admits less textual room, depressing an
  embedding metric independently of idea count — is not excluded here and
  would need a different instrument (e.g. scoring the actual constructions)
  to separate.
- **k and the direction count.** k=10 and 6 directions were taken from the
  external note's rows 7 and 5 and held constant. Neither was swept.
- **The divergence clause** (note row 6, grade B): registered exclusion in
  PREREG.md §4, never tested here, plausibly additive and cheap.
- **Other models.** Everything here is one model on one provider.
