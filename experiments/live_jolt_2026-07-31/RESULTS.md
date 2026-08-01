# Jolt run: the second death on a rule the schema cannot carry

Dated 2026-07-31. Model glm-5.2, thinking OFF, fresh home.
Run `run-b4d6dfda0c20676a864a051fbc97bda4`, state **failed**, 218 s, cycle 0.

## What was asked

Invent a runtime jolt that moves a language model out of an attractor without
changing model family, fine-tuning, or leaving the per-call layer. The model
was given this harness's own schools mechanism as the incumbent, extracted from
source, and 648 real measurements of its own collapse.

## Outcome, in typed order

    setup_rc=0
    qualify_rc=0   qualify_seconds=211    tier full, cache_reused False
    reason_rc=4    reason_seconds=218
    state=failed
    error   V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at
            /workflow/insufficient_capability_by_route_seat
    stop    operational_failure, cycle 0

Admissions: 13 admitted, 9 rejected, 3 schema_exhausted.

Rejection pointers:

    4  /requested_observables
    3  /candidates/4/abstention
    2  <none>

## The cause

The model filed a simulation declaring eighteen observables in dotted form:

    animal.baseline.distinct, animal.baseline.top_mass,
    animal.baseline.normalized_entropy, animal.schools.distinct, ...

and a program whose last statement is `return results` — a NESTED mapping. The
contract's rule is that every name in `requested_observables` must be a KEY of
the returned mapping. A dotted path is a traversal, not a key, so none of the
eighteen matched and the proposal was refused; repairs did not converge and the
seat exhausted its smallest authorized contract.

## The finding, and it is now a pattern

Observable-set agreement — "every name must be a key of what the program
returns" — is item 9 on the NOT EXPRESSIBLE list in
`../2026-07-31-schema-sweep/SWEEP.md`. JSON Schema cannot state a relationship
between one field's values and the runtime output of another field's program.

That makes **two independent live runs killed by rules on that list**:

    turmite run-bc3e8797b3e0609eddb324299c8257bd   _not_a_self_link
    jolt    run-b4d6dfda0c20676a864a051fbc97bda4   observable-set agreement

Both runs qualified at tier `full`. Both had every schema-expressible rule
satisfied. Both died on prose. One is an anecdote; two, on different contracts
with different models of failure, is the shape of the remaining risk — and it
is only visible now because the sweep removed the failures that used to mask
it.

The honest reading of rule A2 after these two runs: encoding what CAN be
encoded worked, and it relocated the failure rather than removing it. The
residual is concentrated exactly where the sweep said it would be, which is
some vindication of the analysis and no comfort at all about the outcome.

## A cheap fix this suggests, not implemented here

The dotted-name failure is not a model error so much as an interface guess. The
model reached for `animal.baseline.distinct` because a nested result is the
natural shape for a 3x2 measurement grid, and flattening it is an arbitrary
convention it had no way to infer. Two options, both small:

1. **Accept dotted paths** as traversals into the returned mapping. This makes
   the natural shape legal and costs one resolver.
2. **State the flattening rule in the schema description** where the
   observables are declared, with an example of a legal name. The rule stays
   prose but stops being invisible.

(1) is better: it removes the failure rather than documenting it.

## What went right

Qualification passed at tier `full` with `cache_reused: False` on a fresh home
— glm-5.2 thinking-off, 320 cases, the same configuration that scored 11/20 and
9/20 on `scratch.link` before the schema sweep.

The model engaged the actual problem. Its simulation was a genuine measurement
design: three conditions (baseline, schools, temperature_max) x two tasks x
three statistics including a normalized entropy it introduced itself, which is
a better collapse statistic than the top-mass the question supplied. That is
the shape of an answer to requirement 3, and it was thrown away over a naming
convention.

## Residue

- The question was not answered. No jolt mechanism was proposed, defended or
  refuted; the run died before a cycle completed.
- One run, one model. The dotted-observable failure is a single instance,
  though the underlying rule is the same class as the turmite failure.
- The 648 probe measurements stand on their own and are reported in
  `dossier/JOLT_MEASUREMENTS.md` regardless of the run's outcome. The finding
  that per-call seeds are inert and that prompt jolts can CREATE collapse
  (`card` 0.42 -> 1.00 under `anti_anchor_fewshot`) does not depend on the
  harness run at all.
