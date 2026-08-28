# PARKED — audit of the P-T1 technique run (2026-08-28)

Nothing here is fixed in this window; this is a read-only audit. Each entry is
a ready-to-send prompt for a future runner.

**Already covered elsewhere — do NOT duplicate.** These audit findings are
fully covered by the technique tranche's own `PARKED.md` and need no new
prompt: P3 (`token_spend: 0`, confirmed on two roots), P5 (`amend` accepts what
`continue` refuses), P6 (`continue` refuses every root — confirmed here on
epoch 6, still the highest-value prompt in either tranche), P9's design
question (the trigger question it poses first is unchanged).

New prompts follow: **A1** (Q2), **A2** (Q3/Q4a), **A3** (a one-line
correction to the technique tranche's P7), **A4** (Q5a, a sharpening of P9),
**A5** (Q3b).

---

## A1 — a manifest can promise a judge ensemble it can never call, and says nothing

**What.** The P-T1 ladder set `JUDGE_SEATS_ENABLED: true`,
`ADJUDICATION_STATUS_AUTHORITY_ENABLED: true` and
`ENGAGED_CRITICISM_AUTHORITY: defended_trial`, and compiled
`rubric_policy: "require_cross_family"` — a cross-family JUDGE requirement.
The compiled manifest carries `criticism_policy: null` and **no
`compile_notices` at all**. Zero judge calls in six epochs, and no threshold
any epoch could have approached.

Highest-ranked finding in the audit because it is the one that violates a
ledgered operator law rather than merely costing a result.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect).

Goal, one sentence: make a compiled manifest DISCLOSE, as a typed compile
notice, that it declares judge machinery no criticism policy can ever reach,
so "everything on" cannot silently mean "judges off".

Evidence, all committed (branch claude/spec-to-code-technique-k5209o,
read-only):
  experiments/2026-08-27-change-technique-run/run/run-manifest.json
      -> criticism_policy: null; rubric_policy: "require_cross_family";
         compile_notices key ABSENT
  experiments/2026-08-27-change-technique-run/run-config.yaml:157-168
      -> JUDGE_SEATS_ENABLED true, ADJUDICATION_STATUS_AUTHORITY_ENABLED true,
         ARGUMENTATIVE_AUTHORITY observe_only, ENGAGED_CRITICISM_AUTHORITY
         defended_trial
  experiments/2026-08-27-change-technique-run/build_manifest_pt1.py
      -> never constructs a criticism_policy
  experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md Q2
  every epoch's record: zero trial events, all warrants type=demonstrative

The trace, already done -- confirm it, do not re-derive it:
  src/deepreason/preparation.py:499-511
      the ONLY consumer of ENGAGED_CRITICISM_AUTHORITY; builds criticism_policy
      on the MANAGED path, which a hand-built manifest bypasses
  src/deepreason/scheduler/scheduler.py:1430-1449
      criticism_policy is None -> the fallback branch at :1488, which passes no
      argumentative_authority
  src/deepreason/rules/crit.py:1673-1678, :101-104, :61-62
      policy_call=False -> _authority(config) -> ARGUMENTATIVE_AUTHORITY
  src/deepreason/authority.py:95
  src/deepreason/rules/crit.py:1608-1620 and :2189-2200
      _TRIAL_MODES is the only road to run_argument_trial_from_case

Read docs/map/CON-criticism-source.md FIRST -- its Traps section already names
this exact diagnostic ("read compile_notices on the manifest FIRST"), and the
finding is that the notice it points at was never written. Then
CON-authority.md and SEAM-adjudication-x-authority.md. Check
INV-frozen-surfaces.md before designing: compile notices ride the manifest,
and ERRATA E44 records what moves a qualification subject digest -- a new
NOTICE must not.

The question to answer explicitly, because it decides the shape:
is the defect (a) that a hand-built manifest can omit criticism_policy at all,
or (b) that omitting it produces no disclosure? The all-configurations law
(2026-08-12) says a configuration that parses COMPILES and discloses -- so the
answer is probably (b) and the fix is a notice, NOT a refusal. Do not make
this a compile-time denial.

Also decide whether the notice belongs on the ARGUMENTATIVE_AUTHORITY /
ENGAGED_CRITICISM_AUTHORITY divergence generally: a run that sets one to
observe_only and the other to defended_trial has a contradiction the operator
cannot currently see.

End state: a manifest with judge seats or a cross-family rubric policy and no
criticism_policy compiles carrying a typed notice naming what cannot be
reached; a regression test compiles this tranche's own configuration and
asserts the notice; qualification subject digests are byte-unchanged (assert
it, per ERRATA E44); full gate 0 failed; map moved in the same commit.
```

---

## A2 — a denied token reservation can consume a cycle forever, and the run reports the cycles as worked

**What.** Epoch 6 reported `completed` / `budget_exhausted`, **24 of 24
cycles**. Only 4 of those cycles did any work. Cycles 5-23 each attempted one
conjecture call against the same crashed simulation package, were denied at
the reservation, recorded `dropped-call`, and consumed the cycle. 19
`dropped-call` events, 40 `budget-denied:token-budget` occurrences, zero
provider calls, zero tokens.

This is the same typed condition as the technique tranche's P2, on a third
path P2 does not cover. **Fix P2 and this one together, or P2's fix will land
on two of at least four handlers.**

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect). Sequence it WITH the technique
tranche's PARKED.md P2 -- same condition, and P2's design question ("is a
denied reservation on an exhausted budget an operational failure at all?")
must be answered once for all handlers, not per site.

Goal, one sentence: stop a denied token reservation from consuming cycles
without progress, so a run that has exhausted its token budget terminates on
that fact instead of spinning out its cycle budget and reporting the spun
cycles as worked.

Reproduce (offline, no provider, no credential):
  drive scripts/cycle_soak.py on a case whose token budget is set below one
  cycle's burn, and assert that the cycle counter does not advance while no
  provider call is made. This shape is NOT currently asserted anywhere -- the
  soak's A2 assertion treats budget_exhausted as clean and cannot see it.

Evidence, all committed (branch claude/spec-to-code-technique-k5209o,
read-only):
  experiments/2026-08-27-change-technique-run/run/log.jsonl
      seq 835-842 -- the five-event shape, repeated identically for cycles
      5 through 23: cycle heartbeat, conjecture Control, budget-denied
      Control, dropped-call Measure, four allocation signals
      census: 19 dropped-call, 40 budget-denied:token-budget
  experiments/2026-08-27-change-technique-run/run/run-status.json
      -> state completed, stop_reason budget_exhausted, cycle 24,
         token_spend 772482 of 800000
  experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md Q3 and Q4a
      (the per-cycle token attribution table: cycles 0-3 carry all 85 calls
       and all 772482 tokens; cycles 5-23 carry none)

The mechanism, traced -- confirm it, do not re-derive it:
  src/deepreason/workflow/transaction_service.py:402  raises WorkBudgetDenied
  src/deepreason/workflow/transaction.py:691-696      the exception
  src/deepreason/scheduler/scheduler.py:1822-1824     _drop(error); return True
  src/deepreason/scheduler/scheduler.py:2052-2053     return True -> _cycles += 1
      and RETURN, before _select_problem at :2055
  the other handlers that must be decided together:
      src/deepreason/rules/crit.py:471-472   (raise -> epoch 0's death)
      src/deepreason/scheduler/scheduler.py:2350-2364 (continue)
      src/deepreason/scheduler/scheduler.py:768-771   (return)
      src/deepreason/rules/conj.py:1908, src/deepreason/informal/trial.py:174,
      src/deepreason/workflow/repair_transaction.py:382

Read docs/map/SEAM-capabilities-x-rules.md and SEAM-llm-x-workflow.md before
designing; check INV-frozen-surfaces.md first (stop reasons and run-status
formats sit near the replay-validation surface).

The question to answer explicitly: should a cycle that did no work count as a
cycle? "24 of 24 cycles" is currently reported for a run that worked 4, which
makes every per-cycle figure in that tranche's RESULTS documents wrong. If the
answer is no, the fix touches what a cycle IS, which is larger than a handler
change -- price it before choosing.

Do NOT fix this by making the capability path raise: that would convert
epoch 6's clean terminal into epoch 0's death, which is the wrong half of P2's
disagreement to standardise on.

End state: a token-exhausted run cannot advance its cycle counter without a
provider call; the soak gains an assertion that would fail today; a regression
test names run 456885c569c0f4f70477df38dd5dda9986ef81443c0a386f3956f85f3446df8c
in its docstring; full gate 0 failed; map moved in the same commit.
```

---

## A3 — one-line correction to the technique tranche's PARKED.md P7

**What.** P7 instructs its runner to "locate the retry policy at file:line and
confirm no typed backoff bound exists." **A bound does exist**, and a runner
who sets out to confirm its absence will either waste time or write something
false.

`llm/endpoints.py:16` defines `_BACKOFFS = (2, 4, 8)`;
`request_with_retries` (`:51-70`) is bounded at 4 attempts and ~14 s of sleep
per call. The 18 minutes is that bound multiplied across the battery:
80 cases × ~14 s ≈ 19 min, against the measured 18 min.

P7's two named defects are both still correct and unchanged: the
**classification** (`endpoints.py:15` puts 429 in `_RETRYABLE_HTTP`, and the
battery has no account-level short-circuit) and the **legibility** (`:59-60`
keeps the HTTP code only for non-retryable errors; `:70` stringifies it into
prose and the typed record stores `ENDPOINT_ERROR`).

**Action:** when P7 is run, strike the phrase "confirm no typed backoff bound
exists" and substitute "the per-call bound is `endpoints.py:16` `_BACKOFFS =
(2, 4, 8)`, 4 attempts, ~14 s; the defect is the classification at `:15` and
the absence of a battery-level short-circuit, not an unbounded ladder." No
separate tranche is owed for this — it is a correction to a prompt, and this
paragraph is the correction.

---

## A4 — sharpening for the technique tranche's P9 (do not run separately)

**What.** P9's census is correct and its design question is unchanged. One
fact it does not carry, which changes the shape of the work:

`src/deepreason/ontology/problem.py:20-30` already declares
`SpawnTrigger.SUCCESSOR`, marked **"INERT VOCABULARY: producers = 0 … retained
only so pre-v2 roots still parse on replay; its presence asserts no producer
and licenses no new one"**, decommissioned when `scan_spawns` stopped on
refutation (H1, Rung 3a) and guarded by a source scan
(`tests/test_decommissioned_pipeline_stays_out.py`).

So the capability was **built and deliberately removed**, not merely never
written. Whoever runs P9 must therefore answer H1 — *a failure redirects
attention, it does not spawn* (the same principle `premises.py:630-633` cites
for the premise channel) — before writing any producer, and must expect the
decommission source scan to go red. Add these three pointers to P9's evidence
list; the prompt is otherwise unchanged.

---

## A5 — the wander cap cannot see capability cycles, and its disclosure says otherwise

**What.** `_disclose_wander`'s docstring (`scheduler.py:1229`) promises "the
reading every cycle". Epoch 6 recorded 4 readings across 24 cycles — exactly
the 4 that reached `_select_problem`. The capability paths emit their own
`cycle` heartbeat (`scheduler.py:1802`, `:1950`, `:2030`) and return before
selection, so the cap is not consulted on them, while `_cycles` increments
(`:2053`) and `_seed_cycles` (`:1226`) cannot.

Low severity: on this record the bias is conservative (it makes the cap
throttle sooner, not later). It is filed because the signal contract's own
terms make an undisclosed reading a contract question, not a tidiness one.

**Ready-to-send prompt:**

```
Route: dr-change-orchestrator (a signal-contract question, not a defect --
nothing is broken; a declared reading is not what it says it is).

Goal, one sentence: make the seed-lineage share signal mean what its own
disclosure says, by deciding whether a capability cycle belongs in the wander
cap's denominator and emitting the reading on every cycle that counts.

Evidence, all committed (branch claude/spec-to-code-technique-k5209o,
read-only):
  experiments/2026-08-27-change-technique-run/run/log.jsonl
      -> 4 allocation.seed-lineage-share.v1 Measures across 24 cycles
         (seq 73, 321, 339, 648); 1 allocation.wander-throttled.v1 (seq 649)
      -> epoch 1's root, by contrast: 12 readings across 12 cycles
  experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md Q3

Pointers:
  src/deepreason/scheduler/scheduler.py:1229  the "every cycle" docstring
  src/deepreason/scheduler/scheduler.py:1130-1149  where decide() is called
  src/deepreason/scheduler/scheduler.py:2052-2061  the capability return that
      skips _select_problem and _disclose_wander
  src/deepreason/scheduler/scheduler.py:1226  where _seed_cycles increments
  src/deepreason/wander.py  LineageReading, and the SIGNALS tuple

Read docs/map/INV-signal-contract.md FIRST -- this is a VERSIONED-layer
question (the registry and the policy algorithm may change; the protocol over
them may not), and REC-revise-allocation-policy.md is the recipe. Note the
FROZEN row that binds the answer: allocation touches EFFICIENCY, NEVER
EVIDENCE -- whatever is decided must not let the cap read an outcome.

The question to answer first: is a cycle spent on a capability step a cycle
the seed lineage could have won? If yes, the denominator is right and only the
disclosure is missing. If no, the reading is currently computed against a
population that includes cycles no lineage competed for, and the fix is to the
reading, not the emitter.

End state: the reading's cadence matches its documented contract; a regression
test drives a run with capability cycles and asserts the emitted count; the
policy's behaviour on the committed epoch 6 record is unchanged or its change
is stated; full gate 0 failed; map moved in the same commit.
```

---

## A6 — the anti-E28 receipt reports that the premise channel never fired, on a run where it fired

**What.** `scheduler.py:2065-2072` emits `premise.work-invited.v1` so that "a
mechanism nobody triggers" is visible on the record. It recorded **0 in all
four committed roots**. In epoch 6 the invitation demonstrably reached two
critic prompts and produced a standing critic-role premise + attribution pair
on the seed problem.

The receipt reads `premise_work_invited(selected_problem)` at cycle START; the
pack computes the invitation per criticism TARGET mid-cycle. In epoch 6 both
events fell inside cycle 0, and the attribution filed in that same cycle then
flipped the predicate False (`premises.py:638-639`) before the next selection
boundary.

This audit's own first census was wrong because of it — evidence that the
receipt actively misleads a reader rather than merely under-reporting.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect).

Goal, one sentence: make the premise-channel receipt report whether the
invitation actually fired, so the record answers "did this mechanism ever
run" correctly.

Evidence, all committed (branch claude/spec-to-code-technique-k5209o,
read-only):
  experiments/2026-08-27-change-technique-run/run/log.jsonl
      -> zero "premise.work-invited.v1" Measures across the whole run
      -> the invitation prompt blobs 98e3b56dcb33... and 20c3f7b621b2...
         referenced at seq 141 and seq 180 (both inside cycle 0)
  the same root's state: standing_attributions == 1, a CRITIC-role premise +
      attribution pair (09cff5b9abfa..., b38afbf002e6...) on problem
      question-9e8800977c3e1deaf5b034b93db38959, both ACCEPTED
  the other three roots: 0 attributions, 0 receipts (consistent there)
  experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md Q1

Pointers:
  src/deepreason/scheduler/scheduler.py:2065-2072  the receipt, sampled on the
      SELECTED problem at cycle start
  src/deepreason/rules/crit.py:1477 and :1641 (_batch_premise_invitation)
      where the invitation is actually computed, per TARGET, mid-cycle
  src/deepreason/premises.py:625-645  premise_work_invited -- note :638-639,
      a standing attribution flips it False
  src/deepreason/premises.py:68  PREMISE_INVITE_AFTER = 2

Read docs/map/CON-problem-layer-lifecycle.md before designing.

The question to answer first: should the receipt move to where the invitation
is DECIDED (crit.py, per target, which is what actually happens), or should
the cycle-start sample be retained and a second receipt added at the decision
site? Moving it is smaller and truer; adding one keeps the cycle-boundary
reading someone may already depend on. Say which and why.

Watch the boundary: the receipt is a Measure -- attention evidence, never a
status (C5, and the invitation carries no penalty for declining). Do not let
the fix make filing or declining a premise consequential.

End state: a run in which the invitation reaches a critic pack records a
receipt saying so; a regression test drives the cycle-0 timing that produced
the false zero and would fail today; full gate 0 failed; map moved in the same
commit.
```
