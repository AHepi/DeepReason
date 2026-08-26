# W5 — RESULTS: were the signals working, and did steering ever do anything?

Window W5 of the RUN ANATOMY PROGRAM, dimension **D7 — Signals**, answering
the operator's phrase *"were signals working"*. Read-only throughout: this
tranche measured committed roots and fixed nothing. Every number below is
re-derivable by `python3 census.py && python3 render.py` from this
directory.

Population: the nine roots that ran after the Rung 1b-ii signal-consumption
tranche landed 2026-08-21, listed in `GOAL.md`. The declared-but-silent
census widens to all 54 inventoried roots, because the question asks
"ever".

---

## Segment 1 — 2026-08-26 — the census

### The four headline answers

**1. Signals were produced, but most declared names have never carried a
value.** 32 of the 111 declared names have ever been emitted in any of the
54 committed roots; 79 never have. Inside the nine-root population, 26
names carry values.

**2. Two declared staleness bounds are exceeded or unrelied-on; the rest
hold.** Only 27 of 111 names declare a bound at all — 84 carry the
`unspecified` migration-debt marker, which is a recorded absence of a
promise, not a promise kept. Of the 27: 14 PASS, 11 are NOT-APPLICABLE
(never emitted), 1 has no consumer, and 1 —
`capture14.hysteresis-mode.v1` — is relied on for up to 14 cycles against
a declared bound of `cycle`.

**3. The allocation controller read process signals and decided 47 times.
Not one decision reached the wire.** Every one of the 47 knob-moves stayed
inside its control barrier, was logged as a replayable policy artifact, and
was never the `max_tokens` of any dispatch that seat made afterwards. In
`experiments/2026-08-25-change-constructive-frontier/run` the conjecturer
cap was driven 32768 → 20480 → 12800 → 8000 → 5000 → 3125 → 1953 → 1221 →
800 across sixteen cycles while every single dispatch went out at 32768.

**4. The efficiency-never-evidence boundary held on live data.** Zero
violations across all nine roots. Every label change inside a
signal-emitting or decision-applying event was a controller policy
artifact's own status, which the design permits (P6).

### Why steering does nothing — the causal chain, all of it in the record

This is not speculation reconstructed after the fact; each step below is a
committed root or a committed source comment naming the root it fixed.

| # | when | what the record shows |
|---|---|---|
| 1 | 2026-08-22, run `40e713b30a147dfc` | The controller narrowed both caps to 20480 at `log.jsonl` seq 442. At seq 577 the route firewall refused: `dropped-call` carrying `ROUTE_LEASE_MISMATCH role='conjecturer' seat=0 field=max_tokens expected=32768 actual=20480`. Run over at cycle 2. This is ERRATA **E43**'s mirror case, and it is the ONE root where a controller decision provably reached the endpoint object. |
| 2 | 2026-08-22 | E43's fix relaxed `EndpointLease.verify` from equality to a ceiling (`llm/firewall.py:288`, `cap > route.max_tokens`). A narrowed cap stopped being terminal. |
| 3 | 2026-08-23, run `bb0455384ea09b5b` attempt 3 | Died at seq 555 with `dropped-call` = `transactional reservation bound differs from rendered request`. `Adapter._completion_cap`'s docstring names this run as the defect it replaced: "two reads happen at different instants and a controller may settle a seat between them". |
| 4 | 2026-08-23 onward | The fix makes `_completion_cap` return `lease.route.max_tokens` whenever the route declares `context_window_tokens`, ignoring "the endpoint's currently settled cap" — deliberately, because the ceiling "is the only value stable across the booking window". |
| 5 | 2026-08-24 → 2026-08-25, all seven later roots | The controller still writes `endpoint.max_tokens` (`Controller._apply_cap`). Nothing reads it. `transport_limits["max_tokens"]` comes from the reservation's `completion_bound_tokens`, and `attempt_trace` entries are constructed with `**transport_limits` (`llm/adapter.py:1611`) — so the trace records the number actually sent. It is a route-declared cap in **every dispatch of all 54 committed roots**. |

Each fix was correct for the failure in front of it. Their composition is
that the allocation controller now has no consumer: it reads process
signals, proposes inside its envelope, logs an attackable policy, applies
the value to an object nothing downstream consults, and the run proceeds
exactly as it would have with no controller at all.

**The failure mode changed from loud to silent.** Before E43's fix, an
ineffective steering decision killed the run and named itself in a typed
drop. After it, the same decision is recorded as a successful policy and
disappears.

### What "tuned and nothing changed" looks like as rows

`experiments/2026-08-25-change-constructive-frontier/run` (P-C1 ARM H),
`cap:conjecturer`, sixteen cycles. The full cycle-by-cycle table is
generated into `DECISIONS_AND_EFFECT.md`; the decision cycles alone:

| cycle | tuned to | dispatched `max_tokens` | conjectures | criticisms |
|---|---|---|---|---|
| 0 | — (route cap 32768) | 32768 | 4 | 38 |
| 1 | 20480 | 32768 | 4 | 46 |
| 3 | 12800 | 32768 | 0 | 0 |
| 5 | 8000 | 32768 | 4 | 48 |
| 7 | 5000 | 32768 | 0 | 0 |
| 9 | 3125 | 32768 | 4 | 33 |
| 11 | 1953 | 32768 | 0 | 0 |
| 13 | 1221 | 32768 | 4 | 32 |
| 15 | 800 | 32768 | 1 | 5 |

Conjectures per cycle are flat at 4 in every cycle that ran a conjecture
phase, across a 41× nominal reduction in the conjecturer's completion cap.
Cycles 3, 7 and 11 produced neither a conjecture nor a criticism — those
are capability steps, not a cap biting, and they are named here rather than
dropped because a zero in a table that argues "nothing changed" has to be
accounted for. Cycle 15's drop to 1 is the run terminating.

### One thing the record does NOT let us conclude

**Zero of 583 post-decision dispatches produced more completion tokens than
the cap then in force.** That number is consistent with the caps being
enforced — and it is equally consistent with them being ignored, because
no call in the population ever wanted more completion than even the
tightest applied cap allowed. The outputs never tested the cap. The
evidence that the caps were not in force is the dispatch envelope itself
(`attempt_trace.max_tokens`), not the completions, and it should be cited
that way and no other.

### The declared-but-silent census

79 of 111 names never carried a value in any committed root. Most are
ordinary: they describe paths no committed run took. Six are structural:

- **Four of the five `allocation.POLICY_SIGNALS`** —
  `allocation.seat-truncation.v1`, `allocation.seat-repair.v1`,
  `allocation.policy-authorized.v1`, `allocation.policy-contested.v1` —
  have **no emit site anywhere in `src/`**. They are computed in-process:
  `Controller._process_signals` reads `event.llm.truncated`/`.attempts`
  directly, and `allocation.policy_is_authorized`/`policy_is_contested`
  read `harness.state.status`. This is the EXPECTED state, and this census
  reports it as measured rather than as a discovery — but it means four of
  the five names the policy is said to "read" are documentation of an
  interface, not entries in a record anyone can audit. Only `dropped-call`
  is auditable, and it fired twice.
- **`controller-update`** is declared with a real unit (`event`) and a real
  staleness (`cycle`) — one of the five the Rung 1b-ii paydown fixed — and
  has no emit site either. The only test naming it asserts its ABSENCE.

### Eight tags emitted that the registry does not declare

18,151 Measure events across the 54 roots carry a tag that is in no
registry entry: `criticism.coverage-debt.v1` (11,764),
`v6-model-phase-deferred.v1` (2,668), `criticism.attempt.v1` (1,767),
`criticism.assignment.v1` (1,742), `defended-trial-deferred` (119),
`module-fingerprints.v1` (38), `contract-decomposition-effect` (31),
`seat-bindings.v1` (22).

`signals.py` opens by promising that a reader following the log "never
meets an undocumented tag", and names exactly TWO families that carry no
signal string by design (HV estimates and reach sweeps, recognised by
payload — of which the whole corpus contains exactly one event). The eight
above are a third class the module does not mention: six are typed-record
SCHEMA identity tags written through `record_*` helpers, and two are
signal literals bound to a variable before the call. `tests/test_signals.py`
scans for `record_measure(inputs=[<literal>...])` heads, so all eight
escape it. The registry's enforcement is a literal-SHAPE check, not a
completeness check.

### Open-loop notices: none, and none expected

All nine roots carry exactly one `controller-authority` record with
`scope: full`, `unsteerable: {}` and `open_loop: []`. Re-deriving the
census independently through `allocation.open_loop_signals` over each
root's own `run-manifest.json` gives the same empty answer: every root
binds `argumentative_critic`, the only producer predicate that can fail.
So the question "was the openness real or spurious" has no live instance
to adjudicate — the disclosure path is unexercised in this population, and
its proof remains the offline regression.

### Seat-instance keying, live for the first time

`experiments/2026-08-25-poietics-program/run` (P-R1) binds the judge role
to two seats, and its `controller-authority` record lists `judge#0` and
`judge#1` as separate steerable seat instances while all eleven
single-seat roles keep their bare names. That is the operator's 2026-08-14
clause — one conjecturer may sit in structurally asymmetric seats that
need throttling independently — visible in a committed live record.
Neither judge seat was ever tuned.

### The E43 ceiling binds nothing here, and the record says why

The prompt asks for a decision clamped by the E43 lease ceiling. There is
none. `Controller._lease_ceiling` clamps a proposal DOWNWARD to the leased
`max_tokens`, so it can only bind on a WIDENING proposal. All 47 decisions
are narrowings: `truncation_rate` is `0.0` and `repair_rate` is `0.0` in
every `evidence` block of every policy artifact in the population, so
`_propose`'s widening branch was never entered. The ceiling is proven
offline (`tests/test_route_lease_maxtokens_tuning.py`) and untested live.
That is a row, not a gap.

---

## The residue — what is not shown, stated plainly

**Counterfactuals are outside what any record can hold.** The record shows
that 47 tuning decisions changed no dispatch envelope. It cannot show what
would have happened had they taken effect. Whether a conjecturer capped at
800 completion tokens would have produced worse conjectures, cheaper ones,
or the same ones is not a fact about these roots — it is a fact about roots
that were never run. Nothing in this census licenses a claim about the
value of steering, only about whether steering occurred. Answering the
counterfactual needs an A/B live run, and that is a different tranche.

**"Nothing changed downstream" is a claim about the typed record, not
about the run.** The census compares dispatch envelopes, completion tokens,
truncation counts, conjectures per cycle and criticisms per cycle. If a
tuning decision changed something the record does not type, this census
cannot see it. The strong form of the claim rests on one field only —
`attempt_trace.max_tokens`, built from `transport_limits` — and that field
alone is what carries the finding.

**Whether the inert steering is a defect is not decided here.**
`_completion_cap`'s behaviour is deliberate and documented, and it fixed a
real death. Whether the allocation controller should have a consumer at
all, or should be retired, or should book its own value, is a design
question for the operator. This tranche parks it; it does not answer it.

**The consumer table is source-derived and hand-verified.** `CONSUMERS` in
`census.py` names three readers, each confirmed by reading the code. A
reader that consumes a signal through indirection this census did not
follow would be missed, and the staleness verdicts for such a signal would
be wrong in the safe direction (`NO-CONSUMER` where a consumer exists).

**Nine roots is a small population, and four of the nine died before cycle
3.** The controller-decision figures rest largely on the three long roots
(P-R1 at 12 cycles, ARM H at 16, the void-inert battery at 12). Where a
finding depends on one root it is named.

**The silence census counts emission, not reachability.** A name with zero
emissions may be perfectly reachable by a configuration no committed root
used. The census says "never emitted here", never "unreachable" — except
for the six where the absence of an emit site in `src/` was checked
directly and is stated as such.

**Accepted does not mean true.** These are the numbers the committed
instrument re-derives from the committed roots. They are not a claim that
the instrument asks every question worth asking about D7.
