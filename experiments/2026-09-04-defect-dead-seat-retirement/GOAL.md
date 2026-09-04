<!-- tranche: 2026-09-04-defect-dead-seat-retirement -->

# Goal: one unusable seat must not kill a run that still has a healthy seat

Class: defect

## Observed (from the typed record only; no implementation code read in this phase)

Motivating root: **P-A1, run `4565139800f5ca02`**,
`experiments/2026-09-01-live-all-modules-p-a1/run/` — opened READ-ONLY.

`deepreason stop-report experiments/2026-09-01-live-all-modules-p-a1/run`
(run 2026-09-04, transcript at `proof/stop_report.txt`) reports, verbatim:

- **The stop.** `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at
  /workflow/insufficient_capability_by_route_seat: route seat has terminally
  exhausted its smallest authorized contract`. State `failed`, stop_reason
  `operational_failure`, at cycle 5 of a 3 000 000-token budget with
  1 093 086 spent.
- **Which seat.** The stop object
  (`objects/workflow-route-seat-insufficient-capability-v1/6d38272…json`)
  names exactly one: `route_lease {"endpoint_id": "ollama-glm-5.3", "role":
  "conjecturer", "seat": 1}`, `reason:
  "smallest_authorized_contract_schema_exhausted"`, having walked the ladder
  `conjecturer.turn.v6` ×5 → `conjecturer.atomic-candidate.v1` ×2.
- **The other seat was healthy.** Section 3 of the same report:

  | seat | endpoint | attempts | invalid | zero-token | faults |
  |---|---|---|---|---|---|
  | conjecturer#0 | ollama-deepseek-v4-pro-0813 | 30 | 14 | 0 | none |
  | conjecturer#1 | ollama-glm-5.3 | 17 | 12 | 6 | HTTPError ×1, RemoteDisconnected ×23 |
  | defender#0 | ollama-glm-5.3 | 8 | 6 | 4 | RemoteDisconnected ×18 |
  | argumentative_critic#0 | ollama-deepseek-v4-pro-0813 | 12 | 1 | 0 | none |

  Every fault in the run is on the ONE endpoint `ollama-glm-5.3` (41
  `RemoteDisconnected` in total). The deepseek seats recorded **zero** faults
  and **zero** zero-token returns across 42 attempts.
- **The report's own classification.** ENVIRONMENT: SUPPORTED — "transport
  wall: 41 RemoteDisconnected on endpoint ollama-glm-5.3". CONFIGURATION:
  RULED OUT. Both conjecturer seats passed qualification 20/20 first-pass with
  0 repairs on every form.
- **The stop did not secure continuation.** Section 5: `continue: REFUSED —
  the record carries TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL`; `amend`
  likewise REFUSED. The run is not resumable when the provider returns.

Restated as ONE checkable statement: **when one route seat exhausts its
contract ladder, the run terminates `operational_failure` on that seat alone —
the scheduler has no way to stand the seat down and dispatch to the seats that
are still answering, and the resulting terminal refuses `continue`.**

Second, weaker observation, recorded because the fix must not create it: there
is currently **no typed seat-retirement record of any kind**. `deepreason
results` and `progress.jsonl` carry per-seat health counters (merged
2026-09-03, `runtime/provider_health.py`) and a typed dead-seat-streak notice,
but nothing that says a seat was stood down.

## Authority for this tranche

- `experiments/2026-09-02-defect-provider-transport-faults/PARKED.md` **P1**,
  the parked prompt, read in full and treated as part of this instruction.
- That tranche's `FIX.md` §5 offered three roads (A notice-only, B stop
  cleanly, C stand the seat down and continue). The operator took **road A**
  then, and has now chosen **road C** — this tranche.
- The 2026-08-29 law (exhaustion is a clean stop; every stop secures
  continuation; continuation is integrity-gated) governs the all-seats-dead
  case.
- The 2026-08-28 ungated-seats law governs the switch: a gate is switchable
  per run and switching it emits a typed WARNING, never a refusal, never
  silence.
- The 2026-08-12 all-configurations law governs every consumer of a shrunk
  seat set: disclose, never die.
- The 2026-09-03 progress law: success is progress over the no-harness
  baseline. A run that survives on one seat and keeps eliminating error beats
  a run that dies with a healthy seat idle.

## Success criterion (machine-decidable)

Against the deterministic offline stub, in a new committed suite:

    python -m pytest tests/test_dead_seat_retirement.py -q
    # expected: all pass, and every test mutation-proven RED on the pre-fix
    # tree (RED transcript committed under proof/).

The suite pins, one test per clause:

1. **The P-A1 shape survives.** Two conjecturer seats; seat 1's endpoint
   always faults, seat 0 always answers. The run reaches a **clean terminal**
   having completed cycles, and the terminal is NOT `operational_failure`.
2. **The retirement is typed.** The record carries a seat-retirement fact
   naming the seat instance, the endpoint, and the reason, readable off the
   committed root by a reader — not prose in a message.
3. **The scheduler keeps dispatching.** After the retirement, at least one
   later provider call is recorded on seat 0 and **zero** later calls on
   seat 1.
4. **`deepreason results` reports it.** The retirement appears in the typed
   results surface; a run with no retirement prints a typed absence, never an
   omitted key.
5. **All seats dead stops CLEAN and resumes.** Every seat's endpoint faults →
   the run terminates on a stop reason that is not `operational_failure`, and
   `stop-report` section 5 says `continue: ACCEPTED` (the 2026-08-29 law).
   The resumed run then completes against a recovered stub.
6. **The switch is per-run configuration and warns.** Retirement defaults ON;
   turning it OFF reproduces today's behaviour exactly (the run dies on the
   exhausted seat); and the non-default setting emits a typed warning that is
   recorded, never silent.
7. **Every enumerated consumer of the seat set handles a shrunk set.** For
   each consumer FIX.md enumerates (allocation signals, ensemble
   requirements, judge pairing, criticism policy bindings), either a test
   shows it working on the shrunk set, or a test shows it emitting a typed
   disclosure. No consumer raises.

Plus the whole-tree gate:

    python -m pytest tests/ -q -n 4
    # expected: 0 failed (pre-authorized baselines per docs/AUDIT_BASELINES.md
    # are recorded, not stopped on)
    python tools/docs_verify.py
    # expected: no NEW failure attributable to this tranche

## Map ids (resolved before design; seams read before subsystems)

| touched | id | document |
|---|---|---|
| the exhaustion terminal and the contract ladder | `DR-SUB-workflow` | `docs/map/SUB-workflow.md` |
| who dispatches to which seat, and what happens when one refuses | `DR-SEAM-scheduler-x-workflow` | `docs/map/SEAM-scheduler-x-workflow.md` |
| cycles, budgets, seat and school dispatch | `DR-SUB-scheduler` | `docs/map/SUB-scheduler.md` |
| role → provider request: `select_lease`, `EndpointLease`, the one-profile mint | `DR-CON-seats` | `docs/map/CON-seats.md` |
| the allocation controller against the route lease | `DR-SEAM-llm-x-scheduler` | `docs/map/SEAM-llm-x-scheduler.md` |
| per-seat signals keyed by seat instance | `DR-INV-signal-contract` | `docs/map/INV-signal-contract.md` |
| provider health counters, the streak notice | `DR-SUB-llm` | `docs/map/SUB-llm.md` |
| `progress.jsonl`, `deepreason results`, `stop-report` | `DR-SUB-application` | `docs/map/SUB-application.md` |
| the stop's typed terminal and whether `continue` is accepted | `DR-CON-run-identity` | `docs/map/CON-run-identity.md` |
| where a per-run switch enters and where it can be lost | `DR-CON-configuration-stages` | `docs/map/CON-configuration-stages.md` |
| what may not be changed without a grant | `DR-INV-frozen-surfaces` | `docs/map/INV-frozen-surfaces.md` |

Read order enforced: `INDEX.md` → `INV-frozen-surfaces.md` → the seams → the
subsystems. `INV-frozen-surfaces.md` was read in full before this goal was
written; its surface-2 (`harness.py`) and surface-4 (`run_manifest.py`) rules
are what make the two forecast contacts below STOP conditions rather than
ordinary work.

## In scope

1. `src/deepreason/scheduler/` — seat dispatch and the exhaustion path.
2. `src/deepreason/workflow/` — the route-seat terminal, and the run terminal
   for the all-seats-dead case.
3. The retirement record and its surfacing under `src/deepreason/runtime/`,
   `src/deepreason/application/`, `src/deepreason/cli/`, plus the per-run
   switch in `src/deepreason/config.py`.

## NOT in scope

- **The nearest tempting neighbour: the transport layer itself.** The retry
  policy, streaming, `DEFAULT_TIMEOUT_S`, `TIMEOUT_FACTORS`, `_BACKOFFS` and
  the wall all shipped 2026-09-03 and are NOT re-derived or re-tuned here.
  This tranche consumes the counters they publish.
- The model-profile registry (`llm/providers.py`, `llm/split.py`).
- Re-seating a retired seat onto a different model, or any second mint — a
  retired seat stays retired for the run.
- Un-retiring a seat that recovers mid-run (parked if the design wants it).
- Making a run CONTINUE across a provider outage automatically; clause 5 asks
  only that the terminal permits `continue`, not that anything resumes by
  itself.
- The `dropped-call` signal overload (PARKED P6 of the prior tranche).
- `PARKED.md` P3, P4, P5, P7 of the prior tranche.
- Any live reasoning run beyond ONE optional guarded check, and only if cheap.
  The offline proof is the proof.
- No committed run root is modified. P-A1's root is read-only evidence.

## Forecast STOP conditions specific to this tranche

Both are forecast now so the design does not discover them late:

1. **A new typed event kind is a surface-2 contact (`harness.py`).** The
   executor instruction requires this be forecast honestly in FIX.md with
   `tools/blast_radius.py` rows pasted, and requires preferring the existing
   notice channel if it can carry retirement without a new kind. FIX.md must
   dispose of that cheaper road explicitly.
2. **A new `Config` knob is a surface-4 contact (`run_manifest.py`)** — the
   `data.pop` recipe in `_versioned_source_config_data`, which the 2026-08-23,
   2026-08-26 and 2026-09-03 grants all followed. Note the 2026-09-03 grant's
   own lesson: a MODEL-valued dropped field cannot round trip; flat scalars
   are what the carriage machinery accepts.

Either contact is a DESIGN-AND-STOP: FIX.md is committed, the turn ends, and
no production code is written until the operator answers.

## Budget

**Stated honestly as an exception the executor instruction already
authorises.** `dr-set-goal`'s default is ≤150 changed lines and one commit.
This goal binds four obligations the instruction states as one goal — the
typed retirement, continued dispatch on the survivors, the consumer census
with a disclosure where a consumer cannot shrink, and the clean continuable
all-dead stop. Planned: one commit per obligation, ~350–450 changed lines
including tests. If any single obligation alone threatens ~150 lines of
production code, that obligation is split and the remainder parked.

Stop conditions inherited from orchestrator: yes. Additionally: STOP AND ASK
on either forecast frozen contact above, on any change to manifest or route
bytes, and on anything requiring a file another window owns.
