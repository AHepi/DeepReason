# Solo Design: The Two-Ledger Controller

*Sealed entry for the autonomics head-to-head. Written by the operating
agent (Fable) and committed BEFORE the harness run on `pi-autonomics`
completed, without reading any of its candidates. Compare against the
harness frontier after the run; scoring criteria = the same
`std-autonomics` standard the harness designs face.*

## Claim

A self-calibrating harness is safe iff its controller can only ever
touch the **generator's** knobs, never the **tribunal's** — and every
calibration decision is itself an ordinary, attackable, replayable
artifact adjudicated by the court it cannot influence.

## Mechanism

### 1. The constitutional partition (the load-bearing idea)

Split every config knob into two ledgers, fixed at registration:

- **Generator ledger (controller-writable):** reasoning depth, completion
  caps, VS_K, batch size CRIT_BATCH_K (call structure only), model
  routing per role, school count, stance decay, spec injection, focus
  shares. By D2, these affect efficiency, never soundness.
- **Tribunal ledger (controller-forbidden, human/appellate-only):**
  ARG_CRIT_PER_CYCLE floors, TRIAL_PARAPHRASE_N, AUDIT_PERIOD,
  JUDGE_ERR_MAX, judge ensemble size, NEAR_DUP_EPS, anything read by
  adjudication, the gate, or the trial guard.

The Goodhart-critical property: **the controller may tune the defendant,
never the court.** A controller that could lower criticism intensity to
raise its survivor metric is structurally impossible, not just
forbidden by policy.

### 2. Policy-as-artifact

The controller emits `calibration_policy` artifacts (JSON: full knob
vector + the log-window evidence that justified each delta + its own
validity node ν). The scheduler applies the latest ACCEPTED policy
artifact at cycle start. Critics can attack a policy like anything else;
a standing attack suspends it and the scheduler reverts to the last
accepted policy (fail-static). Every update is a pure function of the
event-log prefix (no wall clock, no RNG) => byte-for-byte replayable.

### 3. Signal -> knob table (with damping)

| Logged signal (window W=10 cycles) | Knob | Update rule |
|---|---|---|
| finish_reason=length rate > 5% for a role | completion cap | x1.5, bounded by cap_max; lower x0.75 only after 3W clean AND p95 completion < 0.5 cap |
| valid-JSON rate < 0.9 for a role | json_mode / retry budget / model tier | escalate one step per W, never skip steps |
| admission-after-gate rate < 30% | diversity actuators | delegate to the EXISTING capture ladder (tail-weight, complement, spec injection) — reuse the actuator, don't duplicate it |
| survivors-per-gamma-token, per problem FAMILY | reasoning depth, routing | epsilon-greedy: 90% incumbent, 10% probe cycles on the alternate config; switch only on a sequential test over >= N probe cycles (the T2 lesson: count metrics are noise-dominated; single-run deltas never switch anything) |
| challenger model audit battery non-inferior (valid-JSON, attack validity, planted-flaw, survivor yield) at margin delta over N trials | per-role model routing | promote challenger; demote on the same test failing post-promotion |
| any problem with unmet criteria unworked for K cycles | focus share | aging priority queue: priority = age x unsolvedness; replaces manual FOCUS_PROBLEM locks with a liveness guarantee (every registered problem and experiment eventually funded) |

### 4. Goodhart detection: the frozen reference arm

A fixed pseudo-random (seeded from event seq) ~10% of cycles run at an
immutable REFERENCE policy compiled at root creation. This gives an
untunable baseline inside every run. The Goodhart alarm is divergence:
controlled-arm proxy metrics (admission, survivors/token) improving
while reference-normalized DEEP metrics (survivor HV, coverage, reach,
trial-guard block rate) degrade beyond a bound. The alarm is a capture
flag feeding the existing ladder, and it FREEZES the controller
(fail-static to reference policy) until a human or appellate ruling
unfreezes. The controller cannot see or influence which cycles are
reference cycles retroactively (they're determined by seq arithmetic).

## Scope

- covers: all generation-side tuning this project did by hand
  (truncation caps, reasoning policies, routing, batching, VS_K,
  starvation locks, school knobs)
- excludes: tribunal parameters (deliberately), provider probe design
  (composes with a policy compiler but is a separate problem), anything
  requiring wall-clock or randomness outside the log

## Forbidden cases (each rubric:std-autonomics)

1. A diff shows any tribunal-ledger knob changed by a controller policy
   artifact — constitutional violation, refutes the design.
2. Controlled-arm survivor yield rises over 3W while reference-arm
   normalized survivor HV or coverage falls beyond bound — the Goodhart
   case obtained and undetected by the alarm.
3. Any registered problem or pre-registered experiment goes unworked
   for > K cycles despite the aging queue — liveness refuted.
4. A knob flip-flops more than M times in W — damping failure.
5. Replay of a run reproduces different policy artifacts than the live
   run emitted — determinism refuted.
6. The controller emits a policy while its previous policy is under a
   standing attack (fail-static violated).

## Prose notes

The design deliberately reuses existing machinery as actuators (capture
ladder, appellate channel, gate) rather than inventing parallel
mechanisms — the controller is a small pure function from log windows to
policy artifacts, and ALL of its power is borrowed from structures that
are already attackable. The two novel commitments are the ledger
partition (structural, checkable by diff) and the frozen reference arm
(makes Goodhart a measurable divergence instead of a vibe). Cost: the
reference arm taxes ~10% of cycles; the probe arm ~10% — the price of
an untunable baseline and of never repolicying on noise.
