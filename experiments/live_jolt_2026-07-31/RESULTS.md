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

and a program whose last statement is `return results` — a NESTED mapping,
which is the natural shape for a 3x2x3 measurement grid.

The diagnostic blob (`blobs/a9/a91ae25a…`) names the refusal exactly:

    "path":  "/requested_observables"
    "error": "Value error, simulation observables must be plain identifiers"

That is `_observable_syntax` in `capabilities/models.py`, enforcing
`^[A-Za-z][A-Za-z0-9_]{0,63}$`. The proposal never reached the runtime
key-agreement check; it was refused at admission on NAME SYNTAX.

## Correction to an earlier reading of this run

**This segment first attributed the death to observable-set agreement** — item
9 on the NOT EXPRESSIBLE list — and drew from it a pattern: "two independent
live runs killed by rules JSON Schema cannot express." The blob does not
support that, and the corrected reading is worse for the sweep, not better:

- The killer was a `pattern`. **JSON Schema expresses it perfectly.** The sweep
  simply missed this field; `requested_observables` carried no `pattern` and
  the rule lived only in the Python validator.
- The field's own description never mentioned it either. It talked exclusively
  about key agreement. So the rule was in neither of the two places the model
  can read, and the rejection was the first and only statement of it.

So the "two not-expressible deaths" pattern was wrong. One run (turmite) died
on a rule the schema cannot carry. This one died on a rule the schema can carry
and did not. That is a plain miss in the C8 pattern sweep, not a limit of the
method — and it is a sharper indictment, because it was preventable by the
tranche's own stated rule.

## Fixed, 2026-08-01

`OBSERVABLE_NAME_PATTERN` now accepts an identifier or up to eight joined by
dots, on both the wire model and the draft, as an item-type `pattern` so it
validates AND renders. The runtime resolves a name literal-key-first and only
then traverses, in both the contained worker and the in-process runner, so the
change is strictly widening: every name that resolved before resolves to the
same value. The description states the rule. The eighteen names that killed
this run are pinned as a regression in
`tests/test_simulation_dotted_observables.py`.

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
