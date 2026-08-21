# Spec for: Rung 1b-ii — the consumption side of the signal contract

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.

Map ids resolved (CLAUDE.md map preflight): `DR-INV-signal-contract` (owner),
`DR-REC-add-signal`, `DR-REC-revise-allocation-policy`, `DR-INV-frozen-surfaces`,
`DR-SUB-scheduler` (hosts the controller's map prose), `DR-SUB-verification`
(hosts `_configured_role_cap`'s map prose), `DR-SUB-llm` (adapter endpoints /
seat resolution). No seam document exists for `scheduler x signal-contract` —
`INV-signal-contract.md`'s own header records it as `Seams-undocumented`. That
absence is carried forward, not filled here: writing it is neither requested nor
required by any R.

## Items

### S1 (R1, R2, C1) — signals keyed by seat instance

Files: `src/deepreason/allocation.py` (new), `src/deepreason/controller.py`.

Before: `Controller._process_signals` pools every provider call for a role into
one window keyed by `call.role`; `_current_caps` takes the WIDEST `max_tokens`
across a role's endpoint ensemble; `_apply_cap` writes the new cap onto EVERY
endpoint bound to that role. Two structurally asymmetric seats filled by one
conjecturer therefore share one window, one cap and one dwell counter, and
cannot be throttled independently.

After: the unit of allocation is the SEAT INSTANCE. `allocation.py` owns the
naming:

    seat_instance(role, seat, seats_bound) -> "conjecturer"      (seats_bound == 1)
                                          -> "conjecturer#1"     (seats_bound > 1)
    split_seat_instance("conjecturer#1")  -> ("conjecturer", 1)

`_process_signals` windows per seat instance, reading the seat index off
`LLMCall.attempt_trace[-1].seat` (the field `LLMAttempt` already carries;
absent trace -> seat 0). `_current_caps`, `_anchor_envelopes`, `_authority`,
`_clean_streak`, `_propose` and `_apply_cap` all key on the seat instance, and
`_apply_cap` writes only that seat's endpoint.

C1 is honoured by the naming rule, not by an exception to it: a role bound to
exactly ONE seat HAS one seat instance, and that instance's canonical name is
the bare role name. The `#<seat>` suffix appears only where there is more than
one seat to tell apart. Every configuration that exists in a committed root is
single-seat-per-role for the roles the controller steers, so no knob and no
Measure input changes spelling for any recorded topology.

accept:
    python -m pytest tests/test_allocation_signal_consumption.py -q -k seat_instance
    -> passes, including `test_two_asymmetric_seats_throttle_independently`
       (one seat truncating, one clean; the truncating seat's cap moves and the
       clean seat's does not) and
       `test_a_single_seat_role_keeps_the_bare_role_spelling`.

### S2 (R1) — seat identity comes from the record, not from a new role

Files: `src/deepreason/allocation.py`.

R1 names `seat-bindings.v1` as the place seat identity lives. Traced (this is
step 2's mechanism-verification duty): `seat_events.py::SeatBindingV1` carries
`group -> provider/model/profile_digest`, where `group` is a ROLE GROUP, and
`seat_bindings_for_run` projects a single `"default"` entry when no `--seat`
flag was ever bound. It therefore identifies WHICH MODEL sits in a role group,
and is emitted once per run. It does NOT distinguish the individual seats
WITHIN a role's endpoint ensemble, which is the thing R2 requires be throttled
independently. The per-call seat index that does distinguish them is
`LLMAttempt.seat` (`ontology/event.py`, `seat: int = Field(ge=0)`), already
written on every attempt and already cross-checked against
`SchoolRouteReceiptV1.seat` by `LLMCall._school_route_matches_attempts`.

Resolution, recorded rather than silently substituted (dr-spec-change step 2's
named-mechanism rule): the tranche delivers the PROPERTY R1/R2 ask for —
per-seat-instance keying — from `LLMAttempt.seat`, and `seat-bindings.v1`
remains the run-level identity stamp it already is. No role is added anywhere
(R3), and no new field is written to the record.

accept:
    grep -n "attempt_trace" src/deepreason/controller.py -> at least one hit
    ! grep -q "V3_CANONICAL_ROLES\|roles\[.new" src/deepreason/allocation.py
    python -m pytest tests/test_allocation_signal_consumption.py::test_seat_identity_is_read_from_the_attempt_trace -q -> passes

### S3 (R3) — no role added; the qualification subject digest does not move

Files: `tests/test_allocation_signal_consumption.py`.

Before: nothing pins the shipped preparation manifest's qualification subject
digest against a controller/signal change.

After: a test pins the measured baseline. Measured at this tranche's base commit
(M1 below): `d47cb2bf27021474aa17933bc3dcfeeb5dfb1c23b0cfe49452941aace39088dc`.
Any change that adds a role, or that moves `compile_notices` on the shipped
path, moves this digest and fails the test — which is the ~14-minute battery
this requirement exists to protect.

accept:
    python -m pytest tests/test_allocation_signal_consumption.py::test_the_shipped_qualification_subject_digest_does_not_move -q -> passes

### S4 (R8) — the three status reads become declared signals

Files: `src/deepreason/allocation.py`, `src/deepreason/controller.py`,
`src/deepreason/signals.py`.

Before: `controller.py` reads `self.harness.state.status.get(...)` in three
places — `_rehydrate_process_state` (find the last ACCEPTED policy),
`_under_unresolved_attack` (REFUTED / SUSPENDED_UNSUPPORTED -> fail-static),
`_revert_to_last_accepted` (find the last ACCEPTED policy again). Those reads
know how contestation is SPELLED in the adjudication layer, which is exactly
the "consumer that has been taught about a subsystem" the contract forbids.

After: two declared signals, read through `allocation.py`:

    allocation.policy-authorized.v1  unit=event  staleness=run
    allocation.policy-contested.v1   unit=event  staleness=run

`allocation.py` owns the single translation from graph status to signal;
`controller.py` asks by name and contains no `state.status` read at all.

accept:
    ! grep -q "state\.status" src/deepreason/controller.py
    python -m pytest tests/test_signal_contract.py::test_the_controller_reads_no_graph_status -q -> passes

### S5 (R4) — the compiled configuration matrix

Files: `tests/test_allocation_signal_consumption.py`.

Before: no test compiles a set of configuration classes and asserts the
controller attaches to each.

After: a parametrised matrix over the four classes R4 names, each resolved to a
compiled `RunManifest` (Q3's resolution, A3 below):

| class | compiled as |
|---|---|
| solo | `compile_run_manifest(..., single_model=<one model in every seat>)` |
| no-schools | `Config(SCHOOL_SEATS_ENABLED=False)` (the shipped default) |
| judges-off | `Config(JUDGE_SEATS_ENABLED=False)`, no `judge` role bound |
| legacy-on | `Config(LEGACY_CRITICISM_ENABLED=True)`, `criticism_policy=None` |

For each class the test asserts, in R4's own three parts: (a) it COMPILES —
`compile_run_manifest` returns a manifest, no exception; (b) the CONTROLLER
ATTACHES — a `Controller` constructed over an adapter built from
`manifest.roles` emits a `controller-authority` record with a non-empty
`steerable` list; (c) EVERY POLICY-REFERENCED SIGNAL HAS A PRODUCER —
`allocation.open_loop_signals(bound_roles) == ()`.

accept:
    python -m pytest tests/test_allocation_signal_consumption.py -q -k matrix
    -> 4 parametrised cases pass

### S6 (R5, R6, R7) — the typed open-loop notice

Files: `src/deepreason/allocation.py`, `src/deepreason/controller.py`.

Before: nothing states which signals a topology cannot produce. A topology in
which nothing can ever attack a controller policy runs its fail-static branch
as decoration, silently.

After: `allocation.py` declares the policy-referenced signal set and one
producer predicate per signal, decided from the BOUND ROLES alone (Q2's
resolution, A2 below):

| signal | producer present when |
|---|---|
| `allocation.seat-truncation.v1` | any role is bound (a provider call can happen) |
| `allocation.seat-repair.v1` | any role is bound |
| `dropped-call` | any role is bound (the drop site fires on a routed call) |
| `allocation.policy-authorized.v1` | any role is bound (adjudication labels every artifact) |
| `allocation.policy-contested.v1` | `argumentative_critic` is bound — it is the only seat that emits an attack, and both contested statuses (`REFUTED`, and `SUSPENDED_UNSUPPORTED` via the support cascade in `adjudication/support.py`) are downstream of one |

Two disclosure surfaces, both typed, neither fatal (R7):

1. `allocation.open_loop_notices(bound_roles) -> tuple[CompileNoticeV1, ...]`,
   reusing the established type verbatim — `code="ALLOCATION_OPEN_LOOP"`,
   `message="allocation open-loop for signal <name>"`,
   `pointer="/roles"`, `resolution=` the seat that would close the loop.
   `CompileNoticeV1` is IMPORTED, never modified, and imported inside the
   function so the signal interface stays importable without the manifest
   module.
2. `_state_authority`'s `controller-authority` payload gains an `open_loop`
   key (R6: "extend the controller-authority record the E28 fix
   established"), listing the same signal names, sorted.

accept:
    python -m pytest tests/test_allocation_signal_consumption.py -q -k open_loop
    -> passes, including `test_a_critic_less_topology_compiles_with_a_typed_notice`
       (compile succeeds AND a notice naming
       `allocation.policy-contested.v1` is produced) and
       `test_the_controller_authority_record_carries_the_open_loop`.

### S7 (R9) — pay down five entries of the migration debt

Files: `src/deepreason/signals.py`, `tests/test_signal_contract.py`.

Before: 89 of 97 registry entries carry `unit="unspecified"`,
`staleness="unspecified"`.

After: the five entries this tranche has the evidence to fix — because this
tranche defines exactly when each is emitted and how long a consumer may
believe it — get real values. Semantics prose is left BYTE-IDENTICAL (C1):

| entry | unit | staleness | why |
|---|---|---|---|
| `controller-update` | event | cycle | one bounded update; superseded by the next cycle's policy |
| `controller-authority` | event | run | episode-deduplicated; the last one stated is in force for the run |
| `controller-rehydration` | event | run | a resume-time restatement of the limits in force |
| `controller-hold:` (prefix) | event | cycle | one cycle's hold decision |
| `dropped-call` | event | run | the controller counts these cumulatively across the whole log (`_new_transport_drops`), so an occurrence stays usable for the run |

`MIGRATION_DEBT` falls 89 -> 84 — by exactly the five fixed, not one more.

accept:
    python -c "from deepreason.signals import unspecified_declarations as u; print(len(u()))" -> 84
    python -m pytest tests/test_signal_contract.py -q -> passes

### S8 (R10, R11) — efficiency, never evidence

Files: `tests/test_allocation_signal_consumption.py`.

Before: `test_forbidden1_*` and `test_forbidden2_*` in `tests/test_controller.py`
pin the ledger partition and the signal diet. Nothing pins the NEW risk this
tranche creates: seat identity is provenance-shaped, and a provenance-shaped key
reaching adjudication is the one thing the harness forbids by construction.

After: three checks, strongest first.

- **Differential (the load-bearing one).** Two runs over an identical scripted
  log — one stepped by a `Controller` whose seats are deliberately asymmetric
  (one seat truncating, one clean, so the seat key demonstrably drives different
  decisions), one with no controller at all. Assert the two runs' `state.status`
  maps, warrant sets, and `att`/`dep` edge sets are EQUAL. If a seat key ever
  reaches a label, the two diverge.
- **Ledger.** A policy artifact body containing a TRIBUNAL knob and a
  status-shaped knob is fed to `_validated_policy_knobs`; assert both are
  dropped and neither reaches an endpoint.
- **Architecture.** `allocation.py` imports nothing from
  `schools`/`rules`/`informal`/`capture` (the same predicate
  `test_the_allocation_controller_consumes_only_the_interface` applies to
  `controller.py`), and neither module names a warrant-writing or
  status-writing entry point.

R11's MUTATION PROOF runs on the differential test: in a scratch copy (never in
the repo — CLAUDE.md, scratch files), `is_generator_knob` is broken to admit
tribunal knobs and the controller is made to write one status; the test must go
RED; the copy is discarded and both runs pasted into VALIDATION.md.

accept:
    python -m pytest tests/test_allocation_signal_consumption.py -q -k evidence -> passes
    mutation: same command against the mutated scratch copy -> FAILS (pasted)

### S9 (R12) — the map moves in the same commits

Files: `docs/map/INV-signal-contract.md`, `docs/map/REC-add-signal.md`,
`docs/map/REC-revise-allocation-policy.md`.

Before: `INV-signal-contract.md` says seat-instance keying is "**not yet
built** — Rung 1b-ii", states the debt as 89, and carries a Trap saying 1b-i
half-delivered the rung. `REC-revise-allocation-policy.md` says the open-loop
mechanism "lands in Rung 1b-ii".

After: the INV document gains a section per delivered clause (seat-instance
keying, the compiled matrix, the open-loop notice), each with an executable
`check:` that would FAIL if the behaviour regressed; the debt number falls to
84; the "half-delivered" Trap is REWRITTEN to say when it was fixed, never
deleted (SCHEMA.md's rule); `Verified-at:` advances only after that document's
own checks are re-run. The two recipes lose their "not yet built" forward
references.

accept:
    python tools/docs_verify.py -> failures == the 3 pre-existing
      CON-run-identity.md shallow-clone failures named in C8, and no others
    python tools/docs_verify.py --audit -> no new refused check

### S10 (R13, C4) — delivery shape

Files: `VALIDATION.md`, `DELIVERY.md`.

R-by-R reconciliation with pasted proof for every R, closing with one line
naming the configuration classes the controller attaches to and the count of
registry entries still undeclared. Commit and push at every phase boundary with
2s/4s/8s/16s retry.

accept: `DELIVERY.md` contains a row for each of R1-R13 and the closing line.

## Assumptions (operator may override)

A1 (Q1): **Knob names are not registry signal names, so C1 does not bind their
spelling — but the design keeps them unchanged anyway.** C1's stated reason is
that "decline reasons and Measure inputs are compared against recorded roots";
knob names appear only inside a controller POLICY BODY and inside
`controller-update`'s payload, and ERRATA E28 measured that **zero of the 104
committed logs in `experiments/` contain a controller policy body at all**. The
suffix rule in S1 nevertheless leaves every single-seat topology spelled exactly
as today. Assumed; operator may override by asking for an unconditional
`role#seat` spelling.

A2 (Q2): **"Producer" is decided from the bound roles alone**, per the table in
S6. The smallest reading that is still checkable at compile time: a signal has a
producer in a topology iff that topology contains a component that can emit it.
Assumed; operator may override by naming further topology inputs (engine
profile, control-plane mode) as producer conditions.

A3 (Q3): **The four configuration classes resolve to the four compiled shapes in
S5's table** — the shipped `Config` gates that carry those names
(`SCHOOL_SEATS_ENABLED`, `JUDGE_SEATS_ENABLED`, `LEGACY_CRITICISM_ENABLED`) and
`compile_run_manifest`'s `single_model` argument. Assumed; operator may override
with different fixtures.

A4 (Q4): **The controller stops reading `harness.state` for status entirely**;
`allocation.py` owns the one translation and is the only place that names
`Status`. Assumed as the reading that actually delivers "never by teaching a
consumer about a subsystem"; the weaker reading (keep the read, just name it)
would leave the spelling of contestation inside the consumer.

A5 (Q5): **Five entries are fixed** — the four controller signals plus
`dropped-call` — because this tranche's own work is what establishes their
staleness bounds. Every other migrated entry stays `unspecified`, honestly.
Assumed; operator may override by naming more.

A6 (scope): **R37-R41 (attribution-priority allocation policy, Amendment 3) are
NOT delivered here.** The program's Amendment 3 table lands them "at Rung
1b-ii"; the operator's tranche message scopes this window to clauses (2), (4),
(5) plus the debt. Parked with a ready-to-send prompt, not dropped. Assumed; the
operator may fold them in, which would roughly double the budget.

## Questions for operator (STOP if non-empty)

**Q-STOP-1 — frozen-surface contact.** `tools/blast_radius.py` reports
`frozen_surface_verdict: CONTACT`. Per `dr-spec-change` step 3 this stops the
tranche here until the operator's words are given. The computed list is pasted
verbatim in "Frozen-surface contact forecast" below; the priced options and the
recommendation are in "Decision sheet" below.

## Out of scope (explicit)

- **Attribution-priority policy forms, the depth/breadth sensitivity dial, and
  the signals that detect which form is needed (R37-R41).** Not requested by
  this tranche's message; parked.
- **A `scheduler x signal-contract` seam document.** `INV-signal-contract.md`
  records the seam as undocumented; writing it is not requested.
- **Emitting the open-loop notice from `compile_run_manifest`.** Not requested —
  R5's own next sentence names the `controller-authority` record as the
  mechanism — and it would touch a frozen surface AND move the qualification
  subject digest for any topology that triggers it.
- **A dedicated `dr-signals` workflow/skill.** R35 forbids it until two recipe
  failures are recorded; this tranche records none so far.
- **Fixing `INV-frozen-surfaces.md`'s "governing principle" paragraph**, which
  still states the cross-version obligation the operator RETIRED on 2026-08-14.
  Not requested here, and already recorded elsewhere: `docs/ERRATA.md` E36,
  landed by the Rung 3b tranche on 2026-08-21, with a ready-to-send prompt in
  that tranche's PARKED.md P3. Not re-parked here.

## Frozen-surface contact forecast

`tools/blast_radius.py --files src/deepreason/controller.py
src/deepreason/signals.py src/deepreason/invariants.py
tests/test_signal_contract.py tests/test_controller.py
docs/map/INV-signal-contract.md docs/map/REC-add-signal.md
docs/map/REC-revise-allocation-policy.md --symbols cap_envelope
is_generator_knob clamp Controller _state_authority _process_signals
_configured_role_cap SIGNAL_DECLARATIONS PREFIX_DECLARATIONS
unspecified_declarations`

`frozen_surface_verdict: CONTACT`

`frozen_surface_contacts` (verbatim):

```json
[
 {"surface": "replay-validation record formats (invariants.py)",
  "tier": "DIRECT",
  "target": "src/deepreason/invariants.py",
  "detail": "target file is surface path src/deepreason/invariants.py"},
 {"surface": "replay-validation record formats (invariants.py)",
  "tier": "SYMBOL_INDIRECT", "target": "cap_envelope",
  "detail": "'cap_envelope' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"},
 {"surface": "replay-validation record formats (invariants.py)",
  "tier": "SYMBOL_INDIRECT", "target": "is_generator_knob",
  "detail": "'is_generator_knob' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"},
 {"surface": "replay-validation record formats (invariants.py)",
  "tier": "SYMBOL_INDIRECT", "target": "Controller",
  "detail": "'Controller' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"},
 {"surface": "replay-validation record formats (invariants.py)",
  "tier": "SYMBOL_INDIRECT", "target": "_configured_role_cap",
  "detail": "'_configured_role_cap' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"},
 {"surface": "manifest schemas and validators (run_manifest.py)",
  "tier": "SYMBOL_INDIRECT", "target": "clamp",
  "detail": "'clamp' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact)"}
]
```

`frozen_adjacent_contacts` (verbatim): `[]`

`consumers.qualification_digest` (verbatim):

```json
[{"target": "clamp", "tier": "PLAUSIBLE",
  "detail": "referenced in src/deepreason/run_manifest.py"}]
```

`consumers.wheel_smoke_pins` (verbatim): `[]`

Unresolved `reachability` entries the gate could not judge (also a STOP trigger
under step 3): `Controller`, `SIGNAL_DECLARATIONS`, `PREFIX_DECLARATIONS` —
`status_current: "UNKNOWN"`; `unspecified_declarations` — `"UNREACHABLE"`.
Cross-checked by hand per step 5 (the gate says in writing that it cannot judge
these): `Controller` is constructed at `scheduler/scheduler.py` and in 25 test
sites; `SIGNAL_DECLARATIONS`/`PREFIX_DECLARATIONS` are consumed by the derived
`SIGNALS`/`PREFIXES` views in the same module and by `tests/test_signal_contract.py`;
`unspecified_declarations` is called only from `tests/test_signal_contract.py`,
which is what a census helper is for.

**Reading of the contacts, with evidence (the operator decides, not this
document):**

1. `src/deepreason/invariants.py` DIRECT — REAL, and it is a READER fix.
   `_configured_role_cap` resolves a knob's anchoring cap by
   `manifest.roles.get(knob[len("cap:"):])`. Given `cap:conjecturer#1` it finds
   no role, returns `None`, and the unanchored `[500, 2500]` default rejects
   every limit a compiled route (`max_tokens=16384`) could authorize. The fix
   splits the seat suffix and anchors to that seat's own route. **No output
   format changes**; `INV-frozen-surfaces.md`'s own rule is "readers may be
   fixed freely, writers and formats may not". Roughly 12 lines.
2. The four `SYMBOL_INDIRECT` invariants.py entries are the same contact seen
   through the symbols, not four more.
3. `run_manifest.py` via `clamp` — FALSE POSITIVE, measured:
   `grep -n "clamp" src/deepreason/run_manifest.py` returns only
   `_reserved_fractions_are_clamped` and `clamp_reserved_attention_fractions`,
   a different symbol imported from `deepreason.config`. The gate states its own
   method as "grep-based; not proof of semantic contact". `run_manifest.py` is
   NOT a target file of this change and the same evidence disposes of the
   `qualification_digest` PLAUSIBLE row.

## Blast-radius census

Every hit from the gate's `consumers.tests` and `consumers.map_checks`,
classified. None omitted.

**Tests**

| target | hits | verdict |
|---|---|---|
| `src/deepreason/signals.py` | `tests/test_signals.py:52` | MUST NOT MOVE — the AST scan of emitted-vs-declared tags; adding declarations cannot break it |
| `cap_envelope` | `tests/test_controller_steering_parity.py:38,184,187,192,194,198,204` | EXPECTED TO MOVE — S1 changes envelope resolution for seat-suffixed knobs; the single-seat assertions must stay green unchanged |
| `is_generator_knob` | `tests/test_controller_steering_parity.py:39,203,208,209` | MUST NOT MOVE — `cap:<anything>` already qualifies; the seat suffix rides the existing prefix rule |
| `clamp` | `tests/test_all_configs_allowed_remainder.py:439`, `tests/test_intake_form.py:52`, `tests/test_seats_evidence_law.py:460` | MUST NOT MOVE — same false-positive symbol as above (`clamp_reserved_attention_fractions`); verified by grep |
| `Controller` | `tests/test_controller.py` ×13, `tests/test_controller_steering_parity.py` ×10, `tests/test_model_firewall.py:56`, `tests/test_v6_controller3_replay_verification.py:122` | MUST NOT MOVE — every one is single-seat, so every knob keeps its bare-role spelling. This is the row the whole suffix rule exists to protect, and the row to watch first if the ring goes red |
| `_process_signals` | `tests/test_controller.py:94,96` | EXPECTED TO MOVE — line 94/96 asserts the returned dict's KEYS; keys become seat instances (identical strings for single-seat) |
| `SIGNAL_DECLARATIONS` | `tests/test_signal_contract.py:25,39,53,78,89,90` | EXPECTED TO MOVE — four new declarations join it |
| `PREFIX_DECLARATIONS` | `tests/test_signal_contract.py:23,39,54,78,91,92` | EXPECTED TO MOVE — `controller-hold:`'s unit/staleness change |
| `unspecified_declarations` | `tests/test_signal_contract.py:28,65` | EXPECTED TO MOVE — `MIGRATION_DEBT` 89 -> 84 |

**Map documents**

| target | hits | verdict |
|---|---|---|
| `src/deepreason/controller.py` | `CON-standing-and-background.md:137`, `INV-signal-contract.md:40`, `REC-revise-allocation-policy.md:42,43`, `SEAM-ontology-x-rules.md:130`, `SUB-scheduler.md:4,173,184` | EXPECTED TO MOVE: `INV-signal-contract.md`, `REC-revise-allocation-policy.md` (S9). MUST NOT MOVE: `CON-standing-and-background.md`, `SEAM-ontology-x-rules.md`, `SUB-scheduler.md` — re-verified by `docs_verify` at the boundary; if one moves, the design changed something it did not intend to |
| `src/deepreason/signals.py` | `INV-signal-contract.md:4`, `REC-add-signal.md:21,35`, `SUB-harness.md:131,175`, `SUB-rules.md:133,134`, `SUB-scheduler.md:114,115` | EXPECTED TO MOVE: the two owned by this contract. MUST NOT MOVE: `SUB-harness.md`, `SUB-rules.md`, `SUB-scheduler.md` |
| `src/deepreason/invariants.py` | 55 hits across `INV-frozen-surfaces.md`, `SEAM-harness-x-verification.md`, `SUB-verification.md`, and 12 further documents | MUST NOT MOVE — the reader fix changes no output format, so no `check:` over `invariants.py` may move. `SUB-verification.md:163,174` (which name `_configured_role_cap`) is the one to re-read by hand, and its prose gets the seat sentence if its check turns out to describe the anchor |
| `tests/test_signal_contract.py` | `INV-signal-contract.md:3,48,58,64`, `REC-add-signal.md:3,33,40`, `REC-revise-allocation-policy.md:40` | EXPECTED TO MOVE — these are the contract's own checks |
| `tests/test_controller.py` | `CON-scheduler-ranking.md:39,78`, `INV-signal-contract.md:65`, `REC-revise-allocation-policy.md:3,40`, `SEAM-scheduler-x-rules.md:84,210`, `SUB-scheduler.md:3,125,145,173,197` | MUST NOT MOVE except the two contract documents |
| `cap_envelope` | `REC-revise-allocation-policy.md:31,42`, `SUB-scheduler.md:169,173`, `SUB-verification.md:163,174` | EXPECTED TO MOVE: `REC-revise-allocation-policy.md`. MUST NOT MOVE: `SUB-scheduler.md`, `SUB-verification.md` unless their prose describes the anchor, in which case the sentence gains the seat case |
| `is_generator_knob` | `SUB-scheduler.md:173` | MUST NOT MOVE |
| `clamp` | `REC-revise-allocation-policy.md:31,42`, `SEAM-llm-x-workflow.md:235,299,303,306,311` | MUST NOT MOVE — the `SEAM-llm-x-workflow.md` hits are the false-positive symbol |
| `Controller` | `SEAM-llm-x-workflow.md:66,182`, `SUB-scheduler.md:152` | MUST NOT MOVE |
| `_configured_role_cap` | `SUB-verification.md:163,174` | EXPECTED TO MOVE — the seat-suffix case is a new sentence there if the existing prose states the anchoring rule |
| `SIGNAL_DECLARATIONS` | `INV-signal-contract.md:20,25`, `REC-add-signal.md:19,35` | EXPECTED TO MOVE |
| `PREFIX_DECLARATIONS` | `INV-signal-contract.md:20`, `REC-add-signal.md:20,35` | EXPECTED TO MOVE |
| `docs/map/REC-add-signal.md`, `docs/map/REC-revise-allocation-policy.md` | `INV-signal-contract.md:84` | MUST NOT MOVE — the existence check, unaffected |

Manual cross-check required by step 5 for the shapes the gate cannot resolve
(string labels, not Python identifiers): `grep -rn "cap:conjecturer\|cap:judge"
tests/ docs/map/` -> 14 hits, all in `tests/test_controller.py` and
`tests/test_controller_steering_parity.py`, all single-seat, all MUST NOT MOVE.

## Decision sheet — Q-STOP-1

**Decision needed, in one sentence:** may this tranche change 12 lines of one
READER function in `src/deepreason/invariants.py` (`_configured_role_cap`), so
that a per-seat cap knob anchors to that seat's own compiled route?

The gate's computed contact list is pasted verbatim above; the options below are
priced against it, not against a summary of it.

| option | what it does | files | frozen contact | ~lines | risk |
|---|---|---|---|---|---|
| **A (recommended)** | Fix `_configured_role_cap` to split the `#<seat>` suffix and anchor to `manifest.roles[role][seat].max_tokens`. Single-seat knobs take the identical path they take today. | +`invariants.py` | `invariants.py`, READER only, no output format change | 632 total, 12 of them here | Lowest. `INV-frozen-surfaces.md`'s own rule permits reader fixes; the 2026-08-14 law retired the cross-version obligation the surface was guarding; the full gate plus `docs_verify` are the instruments |
| **B** | Ship seat keying WITHOUT the reader fix. | no `invariants.py` | none | 620 | **Highest, and it is a known hole, not a risk.** A multi-seat steered run writes `cap:role#1`; replay validation anchors it to the unanchored `[500, 2500]` default and refuses a limit a 16384-token route authorized. That is shipping a run that cannot verify — the thing the harness exists to prevent |
| **C** | Drop per-seat knobs; key only the SIGNAL WINDOW by seat, leave one shared cap per role. | no `invariants.py` | none | ~500 | Fails R2 outright: "two structurally asymmetric seats filled by one conjecturer must throttle independently" is not delivered, only measured |
| **D** | Stop the tranche and ask for a rung of its own for the reader fix. | none now | none | 0 now | Two round trips for 12 lines of reader, and clauses (2), (4), (5) stay undelivered meanwhile |

**Recommendation: A**, for three reasons that are in the record rather than in
this document's judgment. (1) `INV-frozen-surfaces.md` states the asymmetry
itself: "readers may be fixed freely, writers and formats may not" — this is a
reader, and M5 shows what it currently gets wrong. (2) The operator's 2026-08-14
law retired the cross-version obligation that made replay-side changes expensive;
within-version integrity, which is untouched, is covered by the ordinary gate
(C2 says exactly this). (3) B is not a cheaper A — it is a recorded defect
shipped deliberately, and C returns a rung that measures seats but cannot
throttle them.

**One thing this document will not decide for you:** the gate fires
`frozen_surface_verdict: CONTACT` for ANY change to `Controller`,
`cap_envelope`, or `is_generator_knob`, because all three are named inside
`invariants.py` and the gate matches by grep. Every future controller tranche
will therefore stop here too. Whether that is the gate working or the gate
crying wolf is an operator call, not this tranche's, and it is not being decided
here.

## Measurements

M1: baseline qualification subject digest of the shipped preparation manifest,
at this tranche's base commit:

    $ python -c "from deepreason.qualification import qualification_subject_digest; \
      from deepreason.preparation import qualification_subject_manifest; \
      from tests.test_public_v6_facade import _profile; p=_profile(); \
      m=qualification_subject_manifest(p); print(sorted(m.roles)); \
      print(m.compile_notices); print(qualification_subject_digest(m,p))"
    ['argumentative_critic', 'conjecturer', 'defender', 'grounding_reviewer',
     'judge', 'property_designer', 'summarizer', 'synthesizer', 'thesis',
     'variator', 'vision_critic']
    None
    d47cb2bf27021474aa17933bc3dcfeeb5dfb1c23b0cfe49452941aace39088dc

Supports S3, and supports the S6 claim that the shipped path binds
`argumentative_critic` and is therefore never open-loop.

M2: the registry census at base:

    $ python -c "from deepreason.signals import SIGNAL_DECLARATIONS, PREFIX_DECLARATIONS, \
      unspecified_declarations as u; print(len(SIGNAL_DECLARATIONS)+len(PREFIX_DECLARATIONS), len(u()))"
    97 89

Supports S7's arithmetic (89 - 5 = 84).

M3: the `clamp` frozen contact is a substring false positive:

    $ grep -n "clamp" src/deepreason/run_manifest.py
    357:    def _reserved_fractions_are_clamped(cls, data):
    358:        """The manifest-side mirror of `ScratchpadConfig`'s clamp. Both sides
    367:        from deepreason.config import clamp_reserved_attention_fractions
    370:            clamped = clamp_reserved_attention_fractions(
    375:        if clamped == (exploratory, underexposed):
    378:        data["exploratory_fraction"], data["underexposed_fraction"] = clamped
    2668:        from deepreason.config import clamp_reserved_attention_fractions
    2670:        clamped = clamp_reserved_attention_fractions(
    2673:        if clamped != (source.exploratory_fraction, source.underexposed_fraction):
    2682:                    f" -> {clamped[0]},{clamped[1]}"

Supports the "FALSE POSITIVE" reading of contact 3 and of the
`qualification_digest` PLAUSIBLE row.

M4: seat identity is already per-attempt in the record:

    $ grep -n "seat: int" src/deepreason/ontology/event.py
    68:    seat: int = 0
    110:    seat: int = Field(ge=0)

Supports S2's substitution of `LLMAttempt.seat` for `seat-bindings.v1` as the
per-seat key, and the claim that no new record field is written.

M5: `_configured_role_cap` would mis-anchor a seat-suffixed knob:

    $ sed -n '3586,3599p' src/deepreason/invariants.py
        def _configured_role_cap(knob: str) -> int | None:
            ...
            caps = [ route.max_tokens
                     for route in (manifest.roles.get(knob[len("cap:"):], ()) or ())
                     ... ]
            return max(caps) if caps else None

Supports the "REAL, and it is a READER fix" reading of contact 1.

## Budget

Itemised:

| item | files | ~lines |
|---|---|---|
| S1/S2/S4/S6 interface | `src/deepreason/allocation.py` (new) | 120 |
| S1/S4/S6 consumption | `src/deepreason/controller.py` | 70 |
| S4/S6/S7 registry | `src/deepreason/signals.py` | 55 |
| contact 1 reader fix | `src/deepreason/invariants.py` | 12 |
| S1/S3/S5/S6/S8 tests | `tests/test_allocation_signal_consumption.py` (new) | 260 |
| S4/S7 contract tests | `tests/test_signal_contract.py` | 35 |
| S1 fixture follow-on | `tests/test_controller.py` | 15 |
| S9 map | `docs/map/INV-signal-contract.md` | 55 |
| S9 map | the two `REC-` recipes | 10 |

    $ python3 -c "print(sum([120,70,55,12,260,35,15,55,10]))"
    632

**~632 lines, 5 commits.** Production code is 257 of that
(`python3 -c "print(sum([120,70,55,12]))"` -> 257); tests and map are 375.

**Not split, and the reason is argued rather than asserted.** The skill's
~300-line trigger asks for a split proposal. Splitting SC-2 from SC-4/SC-5 would
ship seat-instance keying with nothing that proves any configuration class still
attaches, and ship an open-loop notice with no keying for it to be open about —
which is exactly the half-delivery `INV-signal-contract.md`'s own Trap warns a
reader not to conclude was a drop. Rung 1b-i recorded the same overrun twice and
recorded the correction as belonging to the ESTIMATOR, not the work (its
DELIVERY.md finding 3). The five commits are themselves the split: interface,
consumption, notice, debt, map+delivery.

Frozen surfaces touched: **`invariants.py` (reader only, 12 lines) — FLAGGED,
operator's words required (Q-STOP-1).**

Rubric: 6/6 yes — every R has a spec item with a machine-decidable accept (R1
S1/S2, R2 S1, R3 S3, R4 S5, R5 S6, R6 S6, R7 S6, R8 S4, R9 S7, R10 S8, R11 S8,
R12 S9, R13 S10); blast-radius census pasted and every hit classified;
frozen-surface contact forecast recorded with the tool's own list verbatim;
every mechanism the request names traced to code it reaches (`seat-bindings.v1`
traced and the substitution recorded in S2; `CompileNoticeV1` traced and reused
unmodified; the `controller-authority` record traced to `_state_authority`);
DESIGN-AND-STOP sections not required but Measurements/Options supplied for the
stop; nothing untraceable to an R/C number.
