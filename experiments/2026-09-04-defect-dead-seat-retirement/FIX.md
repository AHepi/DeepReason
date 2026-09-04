<!-- tranche: 2026-09-04-defect-dead-seat-retirement -->

# Fix: retire a seat where the seat is CHOSEN, and stop clean only when no seat is left

**Guarantee restored (one sentence):** a route seat that the record shows is
finished — its contract ladder exhausted, or its provider dead for a configured
streak — is stood down by a typed receipt, the scheduler keeps dispatching to
the seats that remain, and the run terminates only when NO seat remains, on a
clean stop reason that `continue` accepts.

Design authority: `REPRO.md` for where the retirement decision must live;
`DIAGNOSIS.md` for the mechanism; the map for what may not move; the operator's
2026-08-29, 2026-08-28 and 2026-08-12 laws for the terminal, the switch and the
consumers.

---

## 1. The one thing the reproduction decided, and it is not the obvious one

The obvious fix is an exception arm: catch `RunManifestError` in the school
loop beside the two arms already there. **The reproduction refutes it.** With
one problem in the run, the dead seat's next dispatch carries the payload whose
atomic decomposition the exhaustion left incomplete, and `rules/conj.py` enters
its recovery branch — `workflow/atomic_recovery.py:40`,
`ValueError("atomic child is terminally failed")` — **before the
insufficient-capability guard is consulted at all.** P-A1 missed that road only
because it had many problems.

So retirement is decided where the seat is CHOSEN, not where a dispatch is
refused: the school is dropped from `assigned` before `conj` is entered, and
both roads close with one change. Both are pinned in the committed suite, so a
fix that closes one and not the other stays red.

## 2. FROZEN SURFACES — the honest forecast, computed rather than asserted

`tools/blast_radius.py`'s own output over every file this design touches, pasted
verbatim (full JSON at `proof/blast_radius.txt`):

```
python tools/blast_radius.py --files \
  src/deepreason/scheduler/scheduler.py src/deepreason/runtime/stop.py \
  src/deepreason/workflow/lifecycle.py src/deepreason/signals.py \
  src/deepreason/config.py src/deepreason/run_manifest.py \
  src/deepreason/application/results.py src/deepreason/application/text_runs.py \
  src/deepreason/runtime/provider_health.py

"frozen_surface_verdict": "CONTACT"
"frozen_surface_contacts": [
  {"surface": "manifest schemas and validators (run_manifest.py)",
   "tier": "DIRECT",
   "target": "src/deepreason/run_manifest.py",
   "detail": "target file is surface path src/deepreason/run_manifest.py"}
]
"frozen_adjacent_contacts": []
"disclosure_summary": "This change touches 1 of the five frozen surfaces ...
   manifest schemas and validators (run_manifest.py). 4 test file(s) and 8 map
   document(s) assert on the touched targets today."
```

### 2a. Surface 2 (`harness.py`) — FORECAST, and AVOIDED. Zero contact.

The executor instruction forecast a new typed event kind as a surface-2 contact
and asked that the existing notice channel be preferred if it can carry
retirement. **It can, and the row above proves the avoidance rather than
claiming it: `harness.py` appears in neither contact list.** Three reasons, in
the order they were checked:

1. **For the exhaustion trigger, the typed record already exists.**
   `RouteSeatInsufficientCapabilityV1` is minted per seat by
   `TransactionService.terminate` and lands in
   `WorkflowReplayState.insufficient_capability_by_route_seat`, keyed
   `(role, seat, endpoint_id, route_sha256)`. It already carries the seat, the
   endpoint, the contract ladder it walked and the reason. Nothing about a
   retirement needs a second record of the same fact; what was missing was a
   reader, which is exactly the side this repository's own asymmetry says may
   be fixed freely.
2. **For the streak trigger and the standdown decision, `record_measure` is
   the channel, and it is already carrying its sibling.** A Measure event takes
   string `inputs` and registers no object schema, so `harness.py`'s schema map
   is untouched. `provider.dead-seat-streak.v1` was added exactly this way on
   2026-09-03 and is emitted at `scheduler.py:3155`.
3. **A new object kind would have cost the grant AND bought nothing.** The
   2026-09-04 surface-2 grant (the section plan) was granted because the record
   it wanted had no home in any existing family. This one has two homes.

### 2b. Surface 4 (`run_manifest.py`) — CONTACT. **GRANT REQUESTED HERE, before code.**

**What moves: ONE line** in `_versioned_source_config_data`, at four spaces,
unconditional, joining the twenty-odd knobs already there:

```python
    data.pop("SEAT_RETIREMENT_POLICY", None)
```

**Insertions only: 1 and 0.** No schema, no validator, no Pydantic model, no
field, no digest input.

Why the line must exist, and why it is the SAFE side of the choice: without it
the new `Config` field enters `engine_config_json`, which moves
`source_config_hash`, every manifest digest, and every qualification subject
digest — the ~14-minute battery re-runs for every home for a knob whose
behaviour contract is unchanged. The pop is what PREVENTS that. This is the
`ENGAGED_CRITICISM_AUTHORITY` incident (`docs/ERRATA.md` E44) avoided by doing
the documented thing, and it is the same recipe as the 2026-08-23 (two lines),
2026-08-26 (three) and 2026-09-03 (three) grants.

**A flat scalar, not a model, and that is a measured constraint rather than a
preference.** The 2026-09-03 grant records what a model-valued dropped field
costs: `_strict_carried_value` refuses to coerce a dict back into a model, by
design, so a run setting the knob compiles and then refuses to rebuild. That
grant's own first implementation used a nested model and had to be split into
three scalars. This design ships ONE scalar for that reason.

**One knob, not two.** The threshold is NOT a new field: the streak threshold
is `TRANSPORT_DEAD_SEAT_STREAK`, which already exists, is already popped under
the 2026-09-03 grant, and already means exactly "consecutive zero-byte returns
on one seat". A second threshold would be a second spelling of one fact.

Why the knob is on `Config` at all rather than a constant: the modularity law
(2026-08-26) — every behavior a run can vary is reachable as configuration,
never by editing code — and the ungated-seats law (2026-08-28), which requires
every gate to be switchable per run.

### 2c. The three surfaces that stay at zero, and why the design owes them nothing

- `capabilities/state.py`, `invariants.py`, `verification/`: no `verify_root`
  check is added, no record format moves, and no digest input changes. The
  design was read against these surfaces, not through them.
- `qualification.py` and the frozen-adjacent `route_fingerprint`: no `Route`
  field moves, `route_sha256` is byte-identical, and `frozen_adjacent_contacts`
  is EMPTY above.

**This section is a DESIGN-AND-STOP.** The turn ends with FIX.md committed and
no production code written, per the executor instruction ("Any contact is a
STOP before code").

---

## 3. The change

### 3.1 `src/deepreason/runtime/seat_retirement.py` (NEW, ~90 lines) — the ONE derivation

Read-only over the record and the config, on the `provider_health.py` pattern
it sits beside. Pure in the sense that matters: it decides nothing that is not
already durable.

- `retired_seats(harness, config) -> dict[tuple[str, int], SeatRetirement]`.
  Two triggers, both derived from facts the record already holds:
  - **`contract_exhausted`** — the seat's key is in
    `harness.workflow_state.insufficient_capability_by_route_seat`. Carries the
    outcome's own id, so the receipt points at the record rather than restating
    it.
  - **`provider_dead`** — the seat instance is in
    `dead_seats(seat_health(harness), config.TRANSPORT_DEAD_SEAT_STREAK)`,
    the shipped 2026-09-03 derivation, **reused and not re-derived**. There is
    one transport classifier in this repository and this module does not become
    the second.
- Gated by `config.SEAT_RETIREMENT_POLICY`: `"retire-dead-seats.v1"` (shipped
  default, ON) or `"off"`. **An unknown id falls back to the shipped default
  and discloses `fallback_from`, never refuses** — the all-configurations law
  applied to a policy selector, exactly as `llm/transport_policy.py` and
  `wander.py` do it.

**The invariant this module must not break, stated because the obvious
implementation breaks it:** retirement does NOT change `seats_bound`.
`allocation.seat_instance(role, seat, seats_bound)` spells a one-seat role as
the bare role name and a two-seat role as `role#n`; if retiring seat 1 made the
role one-seated, every signal name, every `cap:` knob and every recorded Measure
input would change spelling **mid-run**, and the run's own earlier rows would
stop matching its later ones. `seats_bound` stays the CONFIGURED count for the
life of the run. Pinned by its own test.

### 3.2 `src/deepreason/signals.py` (~16 lines) — two declarations, no policy entry

- `seat.retired.v1` — unit `count`, staleness `run`; inputs
  `[signal, seat instance, endpoint id, trigger, evidence ref]`. Semantics
  state the boundary the seats law requires: it says this seat will not be
  dispatched again in this run **and nothing else** — not that its model is
  wrong, not that its earlier work is suspect, and never an input to any
  status.
- `seat.retirement-disabled.v1` — the ungated-seats law's typed WARNING,
  emitted once per run when `SEAT_RETIREMENT_POLICY` is `"off"`. Switching a
  gate off is never silent.

Both are `record_measure` receipts on the `provider.dead-seat-streak.v1`
pattern, **not** `POLICY_SIGNALS` entries: nothing consumes either to steer
anything, so neither needs a producer predicate and neither reaches a
controller. `PARKED.md` P6 of the prior tranche records why that restraint is
deliberate. The name is spelled as a LITERAL at each emit site, because
`tests/test_signals.py`'s census reads the literal and a variable makes the
emission invisible to the check that exists to catch an undeclared signal
(`SEAM-scheduler-x-workflow.md` Traps, the `v6-model-phase-deferred.v1` hole).

### 3.3 `src/deepreason/scheduler/scheduler.py` (~80 lines) — enforcement at the CHOICE

- **`step()`, the school loop (`:2300-2347`).** After `school_leases` is
  resolved and BEFORE the `for school_id in assigned:` loop, partition
  `assigned` by retirement and drop the retired schools. This is the site
  `REPRO.md` identified, and it closes both death roads because `conj` is never
  entered for a retired seat. Emit `seat.retired.v1` once per seat, deduped by
  the shipped `_measure_recorded` search over the record — so a RESUMED run
  neither re-discloses nor falls silent, the property the 2026-09-03 emit site
  already has.
- **`_foreign_arg_crit()` (`:1697-1714`).** Drop resolved batches whose critic
  lease is retired, in the batch-resolution pass that already exists precisely
  so "one bad binding leaves no partial provider spend". The targets those
  batches would have covered land in the coverage debt that is already built
  at `:1846-1863`, with `outstanding_school_ids` naming them and
  `termination_reason="ordinary_stop"` — **an existing Literal value; no
  record format changes.**
- **The all-seats-dead terminal.** At the top of `run()`'s cycle loop, when
  every conjecturer seat is retired, set
  `last_stop_decision = StopDecision(stop=True, reason="provider_unavailable")`,
  call the existing `_record_stop(...)`, and break — the same shape the loop
  already uses for `TokenBudgetExceeded`. `_record_stop` writes the STOPPED
  lifecycle receipt through `build_stopped_lifecycle` for any v4/v5/v6
  controller-mode manifest, which is what makes the terminal continuable.

### 3.4 The clean, continuable terminal (~8 lines across two files)

- `runtime/stop.py` — `"provider_unavailable"` joins the `StopReason` Literal.
  Purely widening: no committed root can carry a value that did not exist.
- `workflow/lifecycle.py` — the same string joins **`RESUMABLE_STOP_REASONS`**
  (the 2026-08-29 law: every terminal leaves checkpoints sufficient for
  relaunch) and **`_RUNTIME_DECIDED_STOP_REASONS`** (the loop decides it, not
  the controller, so the receipt must declare that no controller authority was
  consumed — omit this and `build_stopped_lifecycle` re-derives a controller
  evaluation that never happened and raises). It does **NOT** join
  `COMPOSABLE_STOP_REASONS`: that file's own comment says the two sets are
  separate precisely so a resumption change cannot silently widen what may be
  composed, and a run that stopped because nothing could answer has not earned
  a composition.

Why a NEW reason rather than reusing one: `operational_failure` is already
resumable, but it is a FAILURE terminal, and the operator's own 2026-08-29
wording is that an exhausted budget "terminates as `budget_exhausted` (clean),
never `operational_failure`". A provider that stopped answering is the same
shape of fact. `stuck` is clean but is not resumable and means something else.

### 3.5 `src/deepreason/config.py` (~4 lines) — ONE flat scalar

`SEAT_RETIREMENT_POLICY: str = "retire-dead-seats.v1"`, defaulting ON, with the
`"off"` value and its warning. See §2b for why one scalar and not a model, and
why the threshold is not a second field.

### 3.6 `src/deepreason/application/results.py` (~35 lines) — where an operator already looks

`seat_retirement_summary(harness)` beside `provider_health_summary`, the same
read-only derivation so the two surfaces cannot disagree, and a
`## Seat retirement` block in `render_results` next to `## Provider health`.
`_absent("NO_SEAT_RETIREMENT")` when nothing was retired — a typed absence, one
new `ABSENCE_REASONS` code, never an omitted key. `SUB-llm.md` already wrote the
instruction down for the embedder: *"surface the fallback where the operator
already looks."*

### 3.7 `src/deepreason/run_manifest.py` (1 line) — the grant of §2b, and nothing else.

---

## 4. The consumer census — every consumer of a fixed seat set, disposed

GOAL.md clause 7 requires each to be shown handling a shrunk set or emitting a
typed disclosure, and never to raise.

| # | consumer | site | what a shrunk seat set does to it | disposition |
|---|---|---|---|---|
| 1 | **school → conjecturer seat bindings** | `control_plane_policy.school_execution.bindings`, resolved by `resolve_school_role_lease`; consumed in `step()`'s school loop | a retired seat's schools would dispatch and die | **handled**: those schools are dropped from `assigned` before dispatch; the retirement receipt is the disclosure (§3.3) |
| 2 | **criticism policy bindings** | `criticism_policy.bindings`, `plan_foreign_criticism` / `compile_criticism_assignments`, `_foreign_arg_crit` | a retired critic seat's batch would dispatch and die | **handled**: batch dropped in the existing pre-spend resolution pass; uncovered targets recorded in the coverage debt already built there (§3.3) |
| 3 | **foreign-criticism coverage floor** | `policy.minimum_foreign_school_coverage`, `scheduler.py:1851` | fewer live critic schools can put coverage permanently below the floor | **typed disclosure, not a crash**: `complete` goes False and `CoverageDebtV1` records `outstanding_school_ids` with `termination_reason="ordinary_stop"`. Existing shape, existing values. Whether an unmeetable floor should itself stop a run is NOT decided here — parked |
| 4 | **judge ensemble** | `adapter._select_judge_ensemble` → `require_cross_family_judge_ensemble` (≥2 seats AND ≥2 families) or `require_cross_school_judge_ensemble` | retiring one of two judge seats makes the ensemble unobtainable | **typed disclosure**: judge summons are skipped for the rest of the run beside the existing `if not self.adapter.has_role("judge") or not config.JUDGE_SEATS_ENABLED: continue` guard at `:1437`, with one `seat.retired.v1` receipt naming the judge seat. The ensemble predicate is NOT relaxed — the amended judge law rests on cross-family pairing, and a design that quietly ran a one-judge ensemble would trade a 0-2.5% false-conviction regime for a 47-60% one |
| 5 | **allocation signals** | `allocation.seat_instance(role, seat, seats_bound)`, every `cap:` knob | a shrunk `seats_bound` would rename every signal mid-run | **handled by not shrinking it**: §3.1's invariant, with its own test. Allocation touches efficiency, never evidence, and this change gives it nothing new to read |
| 6 | **single-seat roles** (defender, summarizer, thesis, grounding_reviewer, synthesizer, variator, property_designer, vision_critic) | `select_lease(leases, role, 0)` | retiring the only seat of a role means that role cannot run at all | **typed disclosure**: the phase is skipped with a `seat.retired.v1` receipt, exactly as the deferral path already skips a phase whose seat lacks a grant. It does NOT stop the run — P-A1's `defender#0` was on the dead endpoint while the whole conjecture/criticism circuit on the healthy endpoint still had work to do |
| 7 | **the run itself** | `Scheduler.run()` | every conjecturer seat retired means no new conjecture can be made | **clean stop** `provider_unavailable`, continuable (§3.3, §3.4) |

**Rows 3, 4 and 6 are disclosures rather than repairs, and that is the
all-configurations law rather than a shortcut**: a topology that cannot produce
something COMPILES and says so. It is also the shape the signal contract
already uses for an allocation open loop.

---

## 5. Regression artifact

`tests/test_dead_seat_retirement.py`, currently **2 failed**
(`proof/repro_red.txt`), must invert, plus these NEW conditions:

1. the P-A1 shape reaches a clean terminal having completed cycles on seat 0
   (GOAL clause 1);
2. the retirement is typed and readable off the record, naming seat, endpoint
   and trigger (clause 2);
3. after retirement, later provider calls land on seat 0 and **zero** on
   seat 1 (clause 3);
4. `deepreason results` reports the retirement, and prints a typed absence on a
   run with none (clause 4);
5. **every** seat's endpoint faulting terminates `provider_unavailable`, and
   `stop-report` §5 says `continue: ACCEPTED`; the resumed run then completes
   against a recovered stub (clause 5);
6. `SEAT_RETIREMENT_POLICY="off"` reproduces today's death exactly, and emits
   `seat.retirement-disabled.v1` (clause 6);
7. one test per census row 3, 4, 6 above: coverage debt records the outstanding
   schools; judge summons are skipped rather than raising; a single-seat role's
   phase is skipped rather than raising (clause 7);
8. `seats_bound` and therefore every `seat_instance` spelling is unchanged by a
   retirement (§3.1's invariant);
9. an unknown `SEAT_RETIREMENT_POLICY` falls back and discloses rather than
   refusing;
10. the retirement receipt is emitted ONCE per seat across a resumed run.

Each mutation-proven RED before its fix.

## 6. Existing tests at risk (from grep; each must KEEP PASSING, none is updated)

| test | why it is at risk | disposition |
|---|---|---|
| `test_v6_insufficient_capability_terminal.py` (5 tests) | pins that a terminal route seat refuses redispatch and that another route stays authorized | keeps passing — the refusals are untouched; retirement stops the CALLER from reaching them |
| `test_v6_insufficient_capability_reporting.py` | pins the exhaustion projection in the result model | keeps passing — no record or projection field moves |
| `test_signals.py::` the AST census | a new signal without a declaration fails it | keeps passing — both names are declared and spelled as literals at their emit sites |
| `test_the_shipped_qualification_subject_digest_does_not_move` | the whole point of §2b's pop line | keeps passing (and is a pre-authorized baseline either way) |
| `test_manifest_config_disclosure.py::test_every_dropped_field_the_managed_path_can_set_round_trips` | a dropped field must still round trip through its carriage notice | keeps passing — a flat scalar is what that machinery accepts (§2b) |
| `test_results_command.py` absence-code tests | one new top-level key and one new absence code | keeps passing — the key is present on every root and the code is declared |
| `test_error_catalog.py` | reads `application/results.py` | keeps passing — additive block |
| `test_judge_ensemble_boundary.py` | pins the cross-family predicate | keeps passing — the predicate is NOT relaxed (census row 4) |
| `test_lifecycle_operation_parity.py`, `test_checkpoint_hardening.py`, `test_l1_continue_resumable_crash.py` | read `RESUMABLE_STOP_REASONS` | keep passing — the set widens by one value no committed root carries |

## 7. Explicitly not changed

- **The nearest tempting neighbour: what CAUSES a seat to exhaust.** A
  transport fault still spends the schema-repair budget, so an unreachable
  provider is still recorded as an incapable model. `PARKED.md` P1. This fix
  routes around an exhausted seat; it does not change what exhausts one.
- The transport layer, the retry policy, streaming, `DEFAULT_TIMEOUT_S`,
  `TIMEOUT_FACTORS`, `_BACKOFFS` — all shipped 2026-09-03 and consumed here,
  not re-derived.
- **Un-retiring a seat that recovers.** A retired seat stays retired for the
  run. Parking it rather than building it is deliberate: un-retirement needs a
  liveness probe, which is a provider call spent on a seat the run has decided
  not to use, and the operator has not asked for one.
- Re-seating a retired seat onto another model; any second mint.
- The `dropped-call` signal overload; `COMPOSABLE_STOP_REASONS`; every
  `verify_root` check; every record format; the four other frozen surfaces.
- No committed run root.

## 8. Map, moving in the SAME commit

- `SEAM-scheduler-x-workflow.md` — a new `Traps` entry naming run
  `4565139800f5ca02` and BOTH death roads, with a `check:` that goes red if
  either the school-loop partition or the atomic road's coverage disappears.
- `CON-seats.md` — retirement as a seat lifecycle fact, and the `seats_bound`
  invariant of §3.1 with its own check.
- `SUB-application.md` — the results block, with a `check:` that fails if it
  disappears.
- `INV-frozen-surfaces.md` — the granted §2b contact recorded in the same form
  as the nine before it.
- `INV-signal-contract.md` / `REC-add-signal.md` — followed exactly for both
  declarations.

## 9. Estimated diff

~270 lines of production code across 8 files (1 new), plus ~230 lines of tests
and the map. **Over `dr-set-goal`'s 150-line default, as GOAL.md predicted and
bounded**: four obligations the executor instruction binds into one goal. No
single obligation exceeds ~90 lines. Landing as three commits — the derivation
and its enforcement, the terminal and the switch, the surfacing and the census
— each with its own green ring, one full gate at the boundary.

---

## Approval gate — STOP

Class is `defect`; the diff exceeds 150 lines by the executor instruction's own
framing; and there is **one frozen-surface contact, requested in §2b**. Under
`dr-propose-fix`'s rule and the executor instruction's own "Any contact is a
STOP before code", this is a hard stop. Everything outside `run_manifest.py`'s
single `data.pop` line is ordinary defect work needing no grant.

**The decision needed, in one sentence:** may the design add one unconditional
`data.pop("SEAT_RETIREMENT_POLICY", None)` line to
`_versioned_source_config_data` — insertions only, 1 and 0, whose effect is to
keep every manifest and qualification digest byte-identical — so the retirement
switch can be a per-run configuration value rather than a code edit?

---

## Operator disposition, 2026-09-04

Asked as ONE question, per `dr-ask-the-right-question` §4: the frozen-surface
grant was the only fork that survived the dominance test, and the question
embedded `tools/blast_radius.py`'s own `BLAST_RADIUS_RESULT_V1` rows as that
section requires.

- **§2b frozen-surface grant: GRANTED.** "Grant it (recommended)" — the one
  unconditional four-space `data.pop("SEAT_RETIREMENT_POLICY", None)` line in
  `_versioned_source_config_data`, insertions only, 1 and 0. The grant covers
  that line and nothing else; every other frozen surface stays untouched and
  `frozen_adjacent_contacts` remains empty. Ledgered in
  `INV-frozen-surfaces.md` by this tranche, in the same form as the nine before
  it.

### Decided without asking (dominant under the operator's recorded values) — override any time

Three forks were derived rather than escalated, each with the ruling that
decides it. Recorded here so the reasoning is reviewable rather than assumed.

1. **The all-seats-dead terminal is a NEW clean stop reason,
   `provider_unavailable`, not a reuse of `operational_failure`.** The
   2026-08-29 law's own wording decides it: an exhausted budget "terminates as
   `budget_exhausted` (clean), never `operational_failure`". A provider that
   stopped answering is the same shape of fact, and `operational_failure` —
   though already continuable — is a FAILURE terminal. `blast_radius` reports
   no frozen contact on `runtime/stop.py` or `workflow/lifecycle.py`, and the
   widening is one value no committed root can carry.
2. **A retired judge seat skips judge summons rather than stopping the run,
   and the cross-family predicate is NOT relaxed.** The all-configurations law
   (disclose, never die) gives the first half; the amended judge law
   (2026-08-28) gives the second — the measured 0-2.5% false-conviction regime
   is the cross-family one, and every looser configuration measured over-
   convicts at 47-60%, so quietly running a one-judge ensemble would trade the
   good regime for the bad one to avoid a skip.
3. **A retired single-seat role skips its phase rather than stopping the run.**
   Same law, and P-A1 is the case in point: `defender#0` sat on the dead
   endpoint while the conjecture and criticism circuit on the healthy endpoint
   still had work to do.

Implementation proceeds under `dr-implement-fix` on this disposition.

---

## Amendment 1 — 2026-09-04, during implementation: the census's own change sites

`dr-implement-fix` rule 1 requires a missed change site to amend this document
before the work continues rather than after. §4's census rows 4 and 6 state
obligations — a retired judge seat skips summons, a retired single-seat role
skips its phase — but §3 named neither the mechanism nor the sites, and both
obligations are real crashes rather than tidiness: a retired seat's lease is
unchanged, so every preflight still passes and the dispatch reaches the
insufficient-capability guard and raises.

**The mechanism, two methods on `Scheduler`:**

- `_role_available(role)` — `adapter.has_role(role)` AND at least one live
  seat. Falls back to `has_role` alone where there is no lease table, so a
  pre-v6 or mock topology is unchanged. Emits the seat's retirement receipt on
  the way past.
- `_judge_ensemble_available()` — `_role_available("judge")` AND, where the
  ensemble is two or more seats, no judge seat retired. **The cross-family
  predicate is NOT relaxed** (§4 row 4): with a seat gone the ensemble is
  unobtainable, so the phase is skipped rather than run one-judge.

**The sites, exhaustive** (`scheduler.py`, line numbers before this change):

| site | role | becomes |
|---|---|---|
| 825 | argumentative_critic (config referee) | `_role_available` |
| 1530 | argumentative_critic (criticism circuit) | `_role_available` — a retired critic takes the existing "the impossibility must surface" branch, which is already a typed disclosure |
| 2685 | variator (premise rent) | `_role_available` |
| 2786 | conjecturer (property program) | `_role_available` |
| 2909 | vision_critic | `_role_available` |
| 3033 | variator (lazy HV) | `_role_available` |
| 1441 | judge (rubric trial) | `_judge_ensemble_available` |
| 2234 | judge (pairwise discrimination) | `_judge_ensemble_available` |
| 2707 | judge + variator (audit step) | both |
| 2827 | property_designer + judge | both |

**Two sites deliberately NOT changed, and why**: `2321` and `2410` read
`has_role("synthesizer")` inside a condition guarded by
`schema_version == 6` being FALSE. Operations parity (2026-08-13) makes v6 the
only path a current run takes, so both are unreachable today; changing an
unreachable condition would be churn this workflow forbids. Recorded rather
than silently skipped.

Cost: ~35 lines, inside §9's ceiling.

---

## Amendment 2 — 2026-09-04, during implementation: four sites the gate found

`dr-implement-fix` rule 5 says an unpredicted gate failure means the fix is
wrong. Four failures were unpredicted and none of them says that; each is
recorded here with what it actually was, because "unpredicted" is exactly the
category a tranche is tempted to absorb silently.

1. **A test double lacking a method the real object grew.**
   `tests/test_config_referee.py` binds `Scheduler._maybe_config_referee` to a
   `SimpleNamespace` stand-in, and that gate now asks the SCHEDULER whether a
   role has a dispatchable seat rather than asking the ADAPTER whether the role
   exists. Two stand-ins gain `_role_available`; one negative case gains its
   `False`. A double that stops matching the object it doubles is a fixture
   update, not a weakened assertion — the assertions are untouched.

2. **An adapter without a lease table.**
   `tests/test_v6_scheduler_model_phase_deferral.py`'s `_Adapter` double has no
   `leases`, and `_role_available` read it directly. The fix is in PRODUCTION
   and is the honest expression of what §3.1 already documented: an adapter
   with no lease table cannot have a retired seat, because retirement is keyed
   by the frozen route identity a lease carries. `getattr(self.adapter,
   "leases", None) or {}` at the three sites that read it.

3. **A stale tranche tripwire that had outlived its tranche.**
   `tests/test_wire_contract_id_map.py::test_this_tranche_opens_neither_frozen_caller`
   diffed the WORKING TREE against `e91f4fcc3` — the seat-shell tranche's base
   — and asserted five files were unchanged. It was GREEN at this tranche's
   base (measured: `git diff --name-only e91f4fcc3 643dd8ea1 -- run_manifest.py
   invariants.py` is empty), and the operator's granted line turned it red.
   Once its own tranche merged, that check could no longer tell that tranche's
   diff from every later tranche's, so it had become a permanent bar on five
   files that GRANTS EXIST TO OPEN. **Re-aimed, not relaxed**: the range is now
   `e91f4fcc3 643dd8ea1`, which is the diff its docstring is about, so it
   re-derives its own claim forever. The `forbidden` set is untouched and the
   check can still fail.

4. **Two map census counts that a new file legitimately moved.**
   `SEAM-harness-x-workflow.md:48` and `CON-successor-questions.md:305` pin
   "files naming both `harness` and `workflow`" at 60. `runtime/
   seat_retirement.py` reads `harness.workflow_state` to find the exhausted
   seats, so the count is 61. Both bumped, and the seam document now says WHY
   the number moved and that it is a coincidence census rather than a coupling
   measure — a bare number that moves without a reason is how the next reader
   learns to distrust it.

**Pre-existing red, NOT touched** (each fails at the tranche base for reasons
this tranche did not create, and "do not fix it while you are there" is a
prohibition): `SEAM-llm-x-rules.md:54` (an unparseable check opener),
`CON-run-identity.md:211/213/215` (git-history checks against revisions this
container's clone does not carry), `INV-frozen-surfaces.md:206` (the
transport-failure census, a recorded baseline), `INV-frozen-surfaces.md:830`
(a check that reads a branch this container has not fetched).

---

## Amendment 3 — 2026-09-04: the size gate, and a claim I had to correct

`tools/diff_budget.py` against §9's ceiling:

```
python tools/diff_budget.py 643dd8ea1 --ceiling 270 --paths <the eight production paths>
"total_insertions": 492, "ceiling": 270, "verdict": "EXCEEDED"
  scheduler.py 194 | seat_retirement.py 162 | results.py 79 | signals.py 31
  lifecycle.py 9 | stop.py 5 | config.py 5 | run_manifest.py 7
```

492 against 270: 296 executable lines, 31 lines of signal semantics that
`REC-add-signal.md` step 2 requires, and 165 lines of comments and docstrings.

**A correction I owe this document.** The first time I put this to the operator
I priced all 209 non-executable lines as "conventions the repo requires". That
was wrong and they caught it. CLAUDE.md:362 — "Comments state constraints the
code cannot show — never narration of the change or its history" — is a
RESTRICTION on what a comment may say, not a requirement to write one, and no
rule anywhere mandates a production docstring (CLAUDE.md:233 and
`dr-implement-fix` govern TEST docstrings only). Only the 31 lines of signal
semantics were actually mandated. Recorded here because pricing a choice as an
obligation is exactly how an over-budget diff gets waved through, and this
document is where the next reader would look for whether that happened.

**Operator disposition: LAND IT AS IS.** Their words: "Keep the prose. I
misunderstood you. That's just good practice".

The overrun itself is not prose: the code alone is 296 against a 270 estimate,
and the excess is Amendment 1's ten call sites where §4's census had costed
two. Every line traces to a clause of GOAL.md; no scope was added.

## Verification at the boundary

- `python -m pytest tests/ -q -n 4` → **4976 passed, 6 skipped, 0 failed**
  (21m25s).
- `python tools/docs_verify.py` → **6 failed**, down from 14 before this
  tranche's map work. All six are the pre-existing set named in Amendment 2;
  the eight this change touched are green.
- `proof/mutation_proofs.txt` — three mutations, each turning the suite red:
  retirement never firing (11 of 15 red), the all-dead stop reporting
  `operational_failure` (3 red), the school loop not skipping a retired seat
  (7 red). Restored tree: 15 passed.
