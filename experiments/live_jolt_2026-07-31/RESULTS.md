# Jolt run: three epochs, three different walls

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

---

## 2026-08-01, epoch 3: the run completes, and the wall moves twice more

Run `run-b4d6dfda0c20676a864a051fbc97bda4`, state **completed**, cycle 6,
`stop_reason: budget_exhausted`, 174469 / 200000 tokens. Epoch 1 died at cycle
0; epoch 2 never minted a root at all. This is the first time this question has
run to a stop.

    qualify_rc=0  342 s   tier full, cache_reused False, state ready
    reason_rc=5   856 s   state completed, cycle 6
    audit_rc=0
    72 standing, 0 accepted, 0 refuted, 63 positions formally accepted

Two capability channels were exercised and both are typed in the record:

    ResearchFetchProposalV1  research_logits_api
      proposed -> validated -> granted -> compiled -> dispatched -> succeeded
      -> result_packaged -> consumed          (evidence_registered)
    SimulationProposalV1     sim_entropy_overlap_sep
      proposed -> validated -> DENIED         (invalid_model_program)

### Epoch 2, and a regression that was mine

Between epochs the qualification battery caught a defect the offline gate did
not. `scratch.block.compact.v1` fell from 20/20 to 2/20 and the tier fell to
`shallow`, so `reason` was refused at preparation with
`QUALIFICATION_TIER_SHALLOW`. Cause: putting `experiment_refs` /
`bears_on_refs` on that seat. `WireContract.validate_json` parses to a dict and
calls `model_validate`, which is strict, so a JSON array could not become a
`tuple` field. Separately, that seat sees only `SCR_###` handles, and in 3 of 3
reproduction calls the model filled `bears_on_refs` with `["SRC_001",
"SRC_002"]` transliterated from what it could see. Both fixed by taking
provenance off that seat entirely; re-probed at 5/5. Full detail in the commit.

The lesson is about the gate, not the field: every test built those models in
Python with tuples, and nothing pushed a JSON DOCUMENT through the contract,
which is the only path a provider response ever takes.

### The third ambiguous-rule death, this time at execution

The simulation was denied `invalid_model_program`. The program:

    def simulate(inputs, rng):
        baseline_animal = {'elephant': 12}
        ...
        def entropy(hist):
            import math
            ...

The AST guard refuses any import in model-authored source
(`simulation may not import or mutate scope`), verified directly against
`CONTAINED_WORKER_SOURCE_V1`. The contract says "math is available and nothing
else may be imported" — which the model read as permission to import math.

Note what was lost. The program is otherwise exactly what the question asked
for: per-task histograms transcribed into the program text, entropy AND
set-overlap against baseline, no mean across tasks and no boolean. It is a
direct attempt at requirement 3's separation of diversity from degradation, and
it was thrown away over a word.

That is now the third run-affecting failure of the same shape: a rule the model
could not read correctly from where it was stated. `_not_a_self_link`
(unstatable), `simulation observables must be plain identifiers` (statable and
missed), and now "math is available" (stated, but ambiguous between "already
bound" and "importable"). The cheap fix is a wording change — "`math` is
ALREADY BOUND in the program namespace; do not import it, and no import
statement of any kind is permitted" — and it is NOT made here.

### An integrity violation, parked and undiagnosed

`verify_root` on this root returns **integrity_valid: False**:

    workflow-call-pairing  event seq=245: Conj outputs are not uniquely
                           admitted by their provider attempt
    workflow-call-pairing  event seq=386: (same)

What is established:

- It is not a long-run artifact. Every other root in `experiments/` with 400+
  events was checked — 22 of them, up to 1591 events, five longer than this one
  — and all report `pairing=0`.
- The two flagged events are structurally indistinguishable from seq 110, which
  is NOT flagged: same rule `Conj`, same contract
  `conjecturer.atomic-candidate.v1`, six outputs, one attempt, valid first pass.
- It is not output collision. No two `Conj` events in this run share an output.

What is NOT established: the cause, and whether this tranche's changes produced
it or merely produced the first trajectory that surfaces it. Per the tranche
rule a defect found mid-change is PARKED, so it is recorded here and not fixed.
It is the most serious open item in this file.

### Residue

- The question is still not answered. 72 claims stand, 0 accepted, 0 refuted;
  the run stopped on budget, not on convergence. Standing is not accepted.
- The dotted-observable fix was NOT exercised live. The model chose flat names
  (`baseline_entropy`, `temp_max_overlap_with_baseline`). The fix removed a wall
  this run did not walk into; the offline regression remains the only proof.
- One run, one model. The capability channels are stochastic across identical
  runs, so a channel this run used says nothing about the next.
- The integrity failure above means this root is not replay-valid. Nothing in
  this segment should be read as resting on a verified record until it is.
