# Pre-plan: the coder seat as a tool — delegated executable authoring

Status: PROPOSED. Written 2026-08-08 by the monitor session. Authority
is the operator's own words (verbatim, the design intent this plan
serves):

> The thing I'm bugged by: the coder is supposed to function like a
> tool for a less coding capable conjecturer model. Although it's not
> necessary.
>
> Notice how some models are better at understanding abstract problems
> while others are better at coding. That's what this split is
> supposed to capture.

And, reframing what the previous plan (RECORD_LIFECYCLE_DEFECT_PLAN.md
Rung L2) had classified as a defect:

> Actually no. This could be a feature. It tells us something minor
> about what models fit best in which roles.

## What the tree says today (verified against the S1 census and S6's
## live record)

- Every executable payload an LLM authors in a live run — simulation
  proposal rule JSON, observables, capability-channel content — is
  authored by the CONJECTURER (census M18/M19, `rules/conj.py:555,
  1774`). `workloads/simulation.py` and `capabilities/simulation.py`
  only manage the lifecycle of proposals that already exist; no coding
  role sits anywhere on the public path.
- The only coding-shaped role, `property_designer` (`coder` group's
  sole member), is unreachable — the property-oracle bootstrap
  circularity (S6 PARKED P1, oracle.py:431/395).
- The cost of this arrangement is already in the record: both cycle-0
  run deaths (turmite `_not_a_self_link`; jolt `simulation observables
  must be plain identifiers`) were executable-authoring failures — a
  reasoning model writing machine-checkable content and getting the
  machine-checkable part wrong. This is precisely the work the
  operator's split wants delegatable to a coding-strong model.
- S6's throughput finding (gemma conjectures faster than glm
  criticizes; record ends with foreign-criticism debt at budget
  exhaustion) is REFRAMED per the operator: a model-role fit SIGNAL,
  not a defect. It is measurement input for roster choices, and its
  operational remedy remains `deepreason continue` — which is why the
  continue-crash fix (L1) survives from the previous plan unchanged.

## The design in one sentence

When a coder seat is bound, the conjecturer proposes INTENT in its own
language (what to simulate, what to check, what would falsify) and the
coder seat's model AUTHORS the executable payload from that intent —
two attributed signatures on one typed proposal; when no coder seat is
bound, the conjecturer authors its own payloads exactly as today,
byte-identical (the operator's "although it's not necessary" — an
optional tool, never a new obligation).

## The ladder

### Rung T1 — executable-authoring census  [MEASURE ONLY, no code]
Enumerate every surface where LLM output contains executable or
machine-validated content: simulation proposals (M18/M19 path — schema,
validation pipeline, the cycle-0 diagnostic-blob evidence), the
property-oracle machinery (what it would offer a live run if reachable
— its adjudication pipeline exists end-to-end but only `lambda_run`
can mint its trigger; folds the old plan's L4 census in), formal/code
workload content, website workflow scripts. For each: the payload
schema, where validation happens, what the historical authoring
failure rate has been (committed roots + the schema sweep's
not-expressible list). Also measure the intent/code boundary each
schema permits — can rule JSON be split into "described intent" vs
"authored encoding" without a schema change? Deliverable: measured
table; `docs/map/CON-executable-authoring.md`. Accept: every surface
in the table with a real example from a committed root; docs_verify
green.

### Rung T2 — the delegation seam  [DESIGN-AND-STOP]
The danger rung; SPEC only, measurements not arguments. Decisions:
- **Handoff shape.** Conjecturer emits typed intent; a coder-role call
  compiles it to the executable payload; the proposal records BOTH
  parts and both authors (seat attribution per call already works —
  S3/S5's kit). Where exactly the second call happens (inside the
  conjecture rule? a scheduler phase like the property-design step?)
  is priced from T1's call-graph, not assumed.
- **First surface.** Simulation authoring is the presumptive first
  delegation target (it has recorded failures and full typed
  validation to judge success against); property checkers ride the
  same seam only if T1 shows the property machinery is worth wiring
  (else P1's dead limb is documented, not wired).
- **Role vocabulary.** `GROUP_ROLES["coder"]` re-points at the new
  authoring role(s); `property_designer`'s fate is decided here with
  operator words — absorbed, wired, or documented as experiment-only.
- **Default equivalence.** No coder seat bound → zero behavior change,
  proven byte-identically (the whole gate must not notice); this is
  the same reader-before-writer, absence-tolerant discipline every
  rung of the seat program used.
- **Qualification.** The coder seat's battery must cover the authoring
  contract (frozen surface 5 territory — priced, and any contact needs
  fresh operator words; no prior grant carries, per R20's precedent).
STOP: operator words on the chosen shape before T3 plans anything.

### Rung T3 — implement  [EXECUTE, after T2 approval]
Per the approved spec, with the established discipline: reader first
for any new typed record (authoring-attribution fields), contract
fence, writer last, sweep probe separate, full gate, map in the same
commit.

### Rung T4 — the payoff demonstration  [LIVE A/B + research data]
Abstract-strong conjecturer + coding-strong coder seat vs. the same
conjecturer authoring its own payloads. Judge from typed outcomes
only: proposal validation pass rate, cycle-0 deaths, dispatch success,
per-seat attribution. This is simultaneously the feature's acceptance
demonstration and the first designed measurement of the operator's
model-role fit thesis — it feeds the criticism-symmetry program's
roster logic (CRITICISM_SYMMETRY_RESEARCH_PREPLAN.md) alongside S6's
throughput-ratio signal. Offline regression is the proof; one live
attempt is the demonstration.

## Relation to the previous plan (RECORD_LIFECYCLE_DEFECT_PLAN.md)

- **L1 (continue crash) stands unchanged** — a real defect with a
  committed fixture; the remedy for budget-stop debt must not crash,
  whatever else is true. Highest priority alongside T1.
- **L2 is RECLASSIFIED per the operator's words above**: the
  throughput imbalance is a measurement signal, not a defect. No
  scheduler landing-pattern work; the invalid-at-stop state's remedy
  is `continue` (hence L1), and the signal itself is recorded as
  research input.
- **L3 (seat bindings in run identity) stands** — still a real trap,
  still needs its own spec and operator words; unblocked timing.
- **L4 is absorbed** into T1 (census) and T2 (decision with operator
  words).

## Order and cost

L1 (defect fix, fixture committed — can start now, own window) ∥ T1
(half a day to a day, pure measurement — can start now, own window) →
T2 (a day of measured design + one operator decision) → T3 (one to
two tranches) → T4 (one live A/B + its qualification batteries; each
new model/combination pays one ~14-min battery, cached). L3 scheduled
wherever a gap appears; it blocks nothing here (the question-variation
work-around from S6 remains the documented road).
