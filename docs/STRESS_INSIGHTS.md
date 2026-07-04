# Stress-Test Campaign — Insights Report

*2026-07-04. Eight pre-registered tests (`experiments/stress_plan.md`),
run after the budget was raised to 8M tokens. Campaign spend: 1,296,032
tokens across 13 runs, all hard-capped. Verdicts below are against the
expectations stated BEFORE the runs; one falsifier fired and is reported
first, per house rules. Structured data:
`experiments/results/stress_campaign_report.json`.*

## The falsification: reasoning-off is not universally free (T2)

Three matched 5-cycle tides arms: reasoning **off** (18.1k tokens, 4
survivors), **1000-token budget** (30.7k, 4), **provider default**
(40.3k, 7). The pre-registered falsifier — "off loses >30% of
survivors" — **fired** (−43%). The clean D2 story ("generator depth is
pure cost") does not hold on free-prose problems, though it held on the
skeleton-format republic suite (earlier demo: quality flat, 62% cheaper).
Cost *per survivor* still favors off (4.5k vs 5.8k) and diversity was
flat, but the defensible policy is now **per-suite calibration, not
blanket reasoning-off**. Small n (one run per arm) — a replication with
multiple seeds would firm this up.

## The commercial insight: the downgrade is asymmetric (T1)

Flash-everything (pro kept as second judge seat): the *criticism*
machinery held completely — critic valid-JSON 1.0, attack validity 1.0,
6 rubric convictions, 12 invalid convictions correctly blocked. But **0
survivors in 10 cycles** (pro baseline: 3–6): flash conjectures cannot
survive competent criticism. Audit-certified routing: **flash for
critic/defender/variator/judge seats, pro for the conjecturer** — the
expensive model is only needed where boldness is, not where judgement is.

## The integrity results

- **T4 (adversarial terrain)**: the falsifiability gate held on hostile
  ground. Zodiac question, 8 cycles: 3 refuted; the 3 survivors are
  either genuinely scientific candidates (self-fulfilling stereotype
  feedback; seasonal birth effects with the canonical hemisphere-reversal
  falsifier) or mechanically-dressed claims whose self-stated forbidden
  cases are real experiments that would kill them (sunspot-hormone claim:
  "effects stable across solar cycle phases" — which is the observed
  reality). No "cosmic energy" survived. Caveat, honestly: argument alone
  enforces falsifiability-*shape*, not truth — refuting the sunspot claim
  requires grounding (a research backend feeding the known data as
  demonstrative evidence), which is exactly what λ-grounding is for.
- **T5 (judge under 3x audit pressure)**: first live audit hits (2
  paraphrase-invariance hits), guard blocks rose as predicted, and
  conviction survival went UP (0.43 vs ~0.21 at normal pressure) — more
  screens filtered noisy convictions without destroying valid ones.
  attack_validity dipped to 0.909 — first invalid attack observed live.
- **T6 (distributed operation)**: two independently grown graphs merged
  losslessly; **replay byte-for-byte after merge**; post-merge cycles
  healthy (guard blocking, 3 refutations, 6 survivors). Grow-separately,
  union, continue is live-verified.
- **T7 (relapse pressure)**: mature-root cycles still admit 2–3 of 3
  candidates — the gate blocks resubmissions without starving novelty.

## Endurance and diversity (T3)

30 cycles, 8 schools, slow stance decay, two problem families in one
root: attack validity 1.0 throughout, zero capture interventions, zero
reseeds, all 8 schools built lineage (novelty contributions 0.40–0.56),
spec transmission 0.75 (n=25). Cost: **164k for 30 cycles** — the
compounded economies (reasoning policy + batched criticism) run the
system at ~5k/cycle where the first live runs burned ~30k.

## Staged criteria worked — after the dilution lesson (T0)

The focus-locked strict-phase redo produced 16 candidates (unfocused
attempt: 0 — the scheduler's rotation had starved the strict problem,
same failure as the λ pilot). Result: 11 accepted, including hardened
versions of sandbox ideas (formally-verified speculative packs,
event-log-driven memo table, Merkle-treed pack fragments) and **two
accepted negative results** ("semantic memoization cannot be fully
hardened"; "learned compression loses its advantage under strict
replay") while an over-strong universal impossibility claim was
refuted. Operational rule adopted: **phase transitions get FOCUS_PROBLEM
by default.**

## The cache question, re-measured at volume (T8, free)

Post-campaign: exact hit rate 2.0% → **11.1%**, prefix reuse 29% →
**40.6%** (stable-prefix ordering + root resumes add real overlap). Both
still below the refuted designs' floors — they stay refuted, and the
reinstatement machinery stays untested — but the trend says overlap
grows with resume-heavy usage; re-measure before dismissing the exact
cache forever.

## Instrumentation gaps found (fix list)

1. **Gate diagnostics are not persisted** — anti-relapse blocks live in
   scheduler memory only; a finished run can't be audited for block
   counts. Fix: log gate blocks as Measure events.
2. Judge valid-JSON runs low on small samples (0.4–0.75) — the repair
   retry always recovers, but the judge prompt/caps deserve a pass.
3. planted_flaw_error_rate has still never been exercised live.
4. T0 overspent its cap by 1.6% (meter checks pre-spend; the final call
   crosses). Acceptable, but worth documenting as expected behavior.

## Budget

Campaign 1.30M; cumulative ~4.9M of 8M spent; **~3.1M remains**.
