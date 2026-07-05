# The Self-Calibrating Harness — Run Report and the Solo Showdown

*2026-07-05. The user-selected hard problem (candidate A): design the
mechanism by which the harness calibrates its own generation knobs
without the feedback loop becoming a capture vector. Two phases run
(25 focus-locked breadth cycles + 25 released cycles), ~2.27M tokens,
surviving two container restarts with zero state loss (append-only log;
replay byte-for-byte). Phase 3 is HELD pending review, per instruction.
The operating agent's own sealed design (committed blind at `caa0194`,
before any harness output existed) is scored against the frontier below.*

## Headline numbers

- **79 surviving self-calibration designs** on the seed problem (from
  519 artifacts, 148 warrants, 1,947 events; 90 survivors root-wide).
- Trial guard earned its keep at scale: **117 invalid conviction
  attempts blocked** (88 referential-integrity, 27 ensemble-split) vs
  36 valid rubric convictions admitted — a 0.24 conviction survival
  rate. Attack validity 0.93.
- **Spec transmission 0.92 mean over 99 injections** — the diversity
  machinery's best score yet, visible in the result: the frontier spans
  genuinely distinct design families, not variations on one idea.
- All four schools active; zero capture interventions across 50 cycles.

## The design space the harness found (by family)

1. **Adversarial calibration markets** (~24 designs): a controller and
   an anti-controller make zero-sum bets over knob changes; tuning
   power comes from winning bets, so optimizing a recorded outcome
   metric becomes a losing strategy against the adversary. Self-stated
   forbidden cases include controller/anti-controller collusion.
2. **Causal isolation / graph surgery** (~34): knobs update through a
   FIXED causal model of process effects (truncation -> cap; schema
   errors -> json_mode) that is never itself updated from measured
   outcomes — Goodhart requires closing the loop through the outcome,
   so the loop is simply never closed there.
3. **Process-only signal diets / sufficiency meta-critics** (~15–20):
   outcome metrics (survivors, admission rates) are BANNED as inputs
   entirely; only process degradations (finish_reason=length, JSON
   invalidity, retry counts) may drive knobs, frozen as auditable
   constraints.
4. **Safety kernels / control barrier functions** (~7): a formal safe
   envelope per knob; updates outside the envelope are rejected
   regardless of what any metric says.
5. **Frozen baselines / shadow arms** (~4): immutable reference
   configurations to measure drift against.

## The showdown: harness vs the sealed solo design

The solo design (`experiments/solo_autonomics_design.md`, sealed at
commit `caa0194`) proposed: a generator/tribunal **knob-ledger
partition**, **policy-as-attackable-artifact** with fail-static revert,
a **frozen reference arm** (~10% of cycles at an immutable policy, so
Goodhart appears as measurable divergence), and an **aging liveness
queue** replacing manual focus locks.

**Where they converged** (independent arrival = evidence the idea is
load-bearing): freezing something the controller cannot touch
(20 designs freeze constraints/baselines; the solo design freezes the
tribunal ledger and the reference policy); fail-static behavior; and
separating what may drive tuning from what tuning may touch.

**What the harness found that the solo design lacks** — the user's
original challenge ("a modification you haven't considered yet") is
met, three times:

- the **adversarial market** structure (an anti-controller as a
  standing internal red team for every knob change);
- **causal-model surgery** (the solo design lets outcome metrics in,
  guarded by the reference arm; the causal family shows a stricter
  alternative — identify knob->process effects once, never re-fit from
  outcomes);
- **control-barrier envelopes** (formal per-knob safe regions, cheaper
  than a reference arm for hard limits like caps).

**What the solo design has that the frontier mostly lacks**:

- **liveness/anti-starvation** — the tinkering record's most repeated
  real failure (two experiments starved) is addressed by only ~2 of 79
  designs; the aging queue fills a gap the harness under-weighted;
- an explicit **signal-vs-knob two-axis partition** (most harness
  designs partition signals OR constrain updates; few state the
  knob-side constitutional line as sharply);
- the reference arm as a *quantitative* Goodhart detector (divergence
  bound) rather than a qualitative prohibition — only ~4 designs have
  an equivalent.

**Honest verdict on "should you have just asked me":** the harness
produced three structural mechanisms the solo designer did not think
of, at ~2.27M tokens; the solo designer produced a more complete
single design (liveness, quantitative detection) at ~5k tokens.
Neither dominates. The obvious synthesis — market or causal-surgery
core, ledger partition as constitution, reference arm as detector,
aging queue for liveness — is better than either source, and only
exists because both ran.

## Proposed phase 3 (held, ~400k reserve)

1. Register the sealed solo design into the root as an ordinary
   candidate — let the same critics and judges attack it.
2. Focus-locked discrimination + strict-hardening pass over the top
   family representatives (market vs causal-surgery vs process-diet),
   forcing pairwise rulings and hardened compound designs.
3. Convert whatever survives into the actual controller implementation
   spec (the code change to scheduler/config).

## Bookkeeping

Run spend ~2.27M (phase 1: ~1.17M across restart; phase 2: 1.10M).
Cumulative ~7.4M of the 8M budget; **~600k remains** (phase 3 fits).
