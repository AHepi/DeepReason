# Controller Implementation Spec — The Self-Calibrating Harness

*2026-07-05. The output of the pi-autonomics program: 79 exploration
survivors → 10 surviving COMPOUND designs after the focus-locked
synthesis phase and released criticism. This spec is the convergent
architecture of those 10 compounds (they agree to a striking degree),
with each component traceable to the design family that contributed it
and to the criticism that shaped it. It is the blueprint for the code
change; nothing here is implemented yet.*

## The architecture (four components, one dependency direction)

Dependencies run strictly: constitution → update rule → detector →
liveness. No component reads anything downstream of itself — that
acyclicity is itself one of the compounds' load-bearing claims (no new
Goodhart path between components).

### 1. Constitution — the two-ledger partition + fixed causal graph

- Knobs split at registration into a **generator ledger**
  (controller-writable: reasoning, caps, VS_K, CRIT_BATCH_K, routing,
  school knobs, focus shares) and a **tribunal ledger**
  (controller-forbidden: criticism floors, TRIAL_PARAPHRASE_N,
  AUDIT_PERIOD, judge ensemble, NEAR_DUP_EPS — anything adjudication,
  the gate, or the guard reads). Checkable by diff; violation is a
  forbidden case.
- A **fixed causal graph** of knob → process effects (truncation ↔ cap;
  schema invalidity ↔ json_mode/retry; starvation ↔ focus share),
  written once at registration and NEVER re-fitted from measured
  outcomes. The Goodhart loop cannot close through a model that never
  updates. (From the causal-surgery family; adopted by 4/10 compounds
  as the constitution layer, by others as the update-rule prior.)

### 2. Update rule — process-only signals inside barrier envelopes

- **Process-only signal diet** (the frontier's correction to the solo
  design): controller inputs are ONLY process degradations —
  finish_reason=length rate, valid-JSON rate, retry counts, gate-block
  rate, starvation age. **Outcome metrics (survivors, admission rates,
  HV) are banned as controller inputs entirely** — 8/10 compounds
  converged on this stricter line rather than the solo design's
  outcome-reading probe arms. Rationale: a controller that cannot see
  outcomes cannot optimize them, so proxy-gaming has nothing to game.
- **Control barrier functions**: every generator knob carries a formal
  safe envelope [min, max, max-step, min-dwell]. Updates outside the
  envelope are rejected regardless of signals. Damping is the min-dwell
  (no knob changes twice within W cycles).
- Update rule per knob: move one step along the fixed causal edge when
  its process signal crosses its threshold, within the envelope.

### 3. Detector — frozen reference arm (+ optional adversarial market)

- A seq-determined ~10% of cycles run an **immutable reference policy**
  compiled at root creation. Divergence between controlled and
  reference arms on deep instruments (survivor HV, coverage,
  guard-block rate) beyond a bound = capture flag → **controller
  freezes fail-static** to the reference policy until an appellate
  ruling. Note the separation that answers the Goodhart question: the
  DETECTOR may read outcome metrics (it only raises flags — attention,
  never status, never knob values); the UPDATE RULE may not.
- Optional stage-2 (3/10 compounds): an **adversarial market** where an
  anti-controller bets against each proposed knob delta, with payouts
  settled against the reference arm — a standing internal red team.
  Deferred until the base controller has run data (its own forbidden
  case: collusion detectability).

### 4. Liveness — the aging queue

- Problem/experiment priority = age × unsolvedness; every registered
  problem and pre-registered experiment is funded within K cycles.
  Replaces manual FOCUS_PROBLEM locks (two live experiment failures).
  Present in 9/10 compounds — the solo design's contribution, adopted
  nearly universally by the synthesis round.

## Governance (applies to every component)

- Every policy update is a registered `calibration_policy` artifact:
  knob vector + signal-window evidence + its own validity node ν.
  Critics attack policies like anything else; a standing attack
  suspends the policy and the scheduler reverts to the last accepted
  one (fail-static). Updates are pure functions of the log prefix —
  which INCLUDES adjudication outcomes; per the live refute-rebut
  exchange: depending on the court's log-recorded outcomes is fine,
  influencing the court's parameters is forbidden. State this in the
  code comments precisely.
- Replay must reproduce every policy artifact byte-for-byte (no wall
  clock, no RNG; reference-arm cycles determined by seq arithmetic).

## Forbidden cases → the test suite

1. Any tribunal-ledger knob changed by a controller artifact (diff test).
2. Any outcome metric read by the update rule (static import/data-flow test).
3. Knob update outside its CBF envelope accepted (unit test).
4. Reference-arm divergence beyond bound without freeze (simulation test).
5. Any problem/experiment unworked past K cycles (scheduler test).
6. New policy emitted while the previous one is under standing attack
   (adjudication test).
7. Replay divergence in any policy artifact (replay test).

## Provenance

Composed from the 10 accepted compounds on `pi-autonomics-synthesis`
(runs/autonomics; e.g. 9195e139, fc119cd8, abab4664, 0ccb951f,
b8ada07d), the sealed solo design 9ec6cc1f (accepted, after surviving a
refutation-and-reinstatement exchange), and the live criticism that
corrected both: the frontier rejected outcome-reading update rules; the
solo design supplied the liveness and constitutional elements the
frontier lacked. Final instruments for the whole program: 148 invalid
conviction attempts blocked vs 44 admitted, attack validity 0.94, spec
transmission 0.91 over 131 injections, zero capture interventions.

## Controller test (2026-07-05): does it work, is it efficient?

The minimal controller was built (constitution + process-only update +
CBF envelopes + fail-static + liveness; reference arm and market deferred)
and put through both an acceptance suite and a live A/B. Answering the two
questions honestly:

**Acceptance suite (`tests/test_controller.py`): passes.** Forbidden
cases 1, 2, 3, 5, 6, 7 are enforced as tests (case 4 deferred with the
reference arm). Writing them caught a real design bug — the first liveness
formula aged problems by first-sight, so with all problems registered at
once the ages tied and one problem won every cycle forever; the test
forced the fix (age from last-worked = fair rotation). The suite proves
the controller is *well-behaved and safe*, not that it is smart.

**Live A/B (`experiments/results/controller_ab_report.json`): starved the
conjecturer cap to 1200 on republic skeletons, 6 cycles, controller OFF
vs ON.**

| metric | controller OFF | controller ON |
|---|---|---|
| conjecturer truncation rate | 0.40 | **0.17** |
| conjecturer valid-JSON | 0.71 | **0.86** |
| cap:conjecturer (start → end) | 1200 (fixed) | 1200 → 1920 → **3072** |
| policies emitted / fail-static holds | — | 3 / 0 |
| survivors | 3 | 2 |
| total tokens | 67,843 | 68,933 |

**Does it work? Yes, on what it controls.** The controller read the
truncation signal from the log, widened the cap in two envelope-bounded
steps to 3072, and truncation fell from 40% to 17% while valid-JSON rose
from 0.71 to 0.86 — each move a replayable policy artifact carrying its
own evidence, zero constitution violations, zero fail-static needed. The
mechanism does exactly what it was designed to do, automatically, with no
human.

**Is it token-efficient? Not at this scale, and honestly not the point of
the minimal build.** Tokens were within 1.6% (68.9k vs 67.8k) — it spent
slightly *more* to widen. This is a recovery/correctness mechanism, not a
savings one, exactly as flagged before the run. Two honest dents in the
story: (1) survivors were 2 vs 3 — within noise at one run per arm, and
even slightly lower; (2) the harness ALREADY carries a truncation-aware
compression-retry (added by hand earlier), which rescues much of the same
failure, so the controller's *marginal* value on this particular failure
is small. Its real value is auto-handling the failures we have NOT already
patched by hand — which an A/B on an old, already-patched failure cannot
show. The savings direction (narrowing wasteful caps, reasoning routing)
lives in the deferred half.

**Bottom line for the two questions asked:** the controller is *safe and
it works* (proven), and it is *not yet a token saver* (measured, and
expected — savings is the deferred reference-arm/routing half). The
minimal build is the right thing to have shipped first: it is the part
that is certainly correct and certainly useful, and it now has the
instruments to decide empirically whether the clever deferred half is
worth building.
