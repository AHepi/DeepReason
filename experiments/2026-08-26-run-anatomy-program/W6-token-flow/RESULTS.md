# RESULTS — W6, the token-flow map

Dated honest-ledger segments. Every number traces to a committed
instrument in this directory run against the committed roots; the
instrument name is given with each claim. Model prose is not evidence here
and neither is mine. "Accepted does not mean true" — and in this window it
turns out not to mean *good* either, which is most of the finding.

---

## 2026-08-26 — where 10 958 450 tokens went

**Headline: two tokens in three that DeepReason has ever spent were spent
asking, not answering.** Over 54 committed roots and 3 155 provider calls,
7 467 145 of 10 958 450 tokens are prompt-side (68.1 %). A quarter of the
whole — 2 694 889 tokens, 24.6 % — went to calls whose output the harness
then rejected. `flow.py` → `FLOW_AGGREGATE.json`; full tables in
`TABLES.md`.

The prompt-side share is not spread evenly. It concentrates exactly where
the harness's own machinery is thickest:

| | prompt share |
|---|---:|
| adjudication (judge rulings, defences) | 84.8 % |
| generation | 69.9 % |
| criticism | 65.2 % |
| report composition | 44.4 % |

A judge ruling averages 1 113 tokens of which **94.1 %** is prompt: 358 172
prompt tokens against 22 428 completion tokens across 342 rulings. The
judge seat reads enormously and says almost nothing.

### The single clearest overhead number

On `conjecturer.turn.v6` — the main generation contract, 816 calls and
5 679 006 tokens, over half the program's entire spend — a packed prompt
averages 5 410 estimated tokens, of which **70.2 % is the output-contract
JSON Schema**. The problem, the criteria, the evidence, the neighbourhood
and the steering together are 27.2 %. The fixed toll (role preamble plus
schema) is 72.0 % of the prompt. `pack_anatomy.py` → `PACK_ANATOMY.json`,
`by_contract_and_form`.

Inside the 27.2 % that IS pack, the split is protocol 29.6 %, frame
(problem + criteria) 19.9 %, evidence 18.2 %, steering 16.3 %, prior
candidates 16.0 %.

### The pack does not grow

Expected a context that swells cycle over cycle; the record says no. Mean
provider prompt tokens per packed `conjecturer.turn.v6` call, P-C1 ARM H,
cycles 1 → 16: 6 155, 6 204, 4 810, 6 277, 6 257, 4 865, 6 286, 6 286,
4 898, 6 286, 6 286, 4 898, 6 282. It oscillates between two values and
never trends. P-R1 is the same shape at a higher level (≈8 350 / ≈6 900).
The pack budget caps it, so a fifteen-cycle run does not accumulate
context — it re-pays for a bounded one, 292 times.
`pack_anatomy.py` → `PACK_GROWTH.json`.

Recorded because the first version of this table was wrong in an
instructive way: it mixed repair re-asks into each cycle's mean, and the
dips that produced read as a shrinking pack. Splitting by prompt form
removed them. Nothing shrank; the instrument was averaging two different
prompts.

### The repair bill

**456 repair re-asks, 1 382 831 tokens, 12.6 % of the program's spend,
80.7 % of it prompt-side.** A repair sends the model its own rejected JSON
back verbatim — 1 115 875 provider prompt tokens, of which 839 301
(estimated) are the returned rejected value and 194 383 the diagnostic
envelope. Two forms, 390 patch re-asks and 66 full-value re-asks.

Two independent instruments agree on the 456: `flow.py` counts repair
transitions in `workflow-work-lifecycle-transition-v1`, `pack_anatomy.py`
counts repair-shaped prompt blobs, and neither knows about the other.

---

## 2026-08-26 — P-C1 ARM H: a line-item post-mortem of 702 789 tokens

**Headline: 41.2 % of ARM H's budget was spent on a problem the run
invented about its own critic, not on the question the operator asked.**
`pc1_postmortem.py` → `PC1_POSTMORTEM.json`.

| line item | calls | tokens | share |
|---|---:|---:|---:|
| the operator's seed question | 61 | 373 903 | 53.2 % |
| `audit:ritual`, spawned by the run | 203 | 289 676 | 41.2 % |
| repair re-asks (no pack, no problem line) | 28 | 39 210 | 5.6 % |

`audit:ritual` — "audit the critic: adjudication-ritual flags sustained
(§11.3)", provenance `{"trigger": "audit-critic"}` — appears at log seq
**345 of 3 200**, about two cycles in. It then spawns `disc:audit:ritual`,
"discriminate between 20 surviving rivals", at seq 603. The record splits
cleanly on that event:

| | tokens | share on the seed question |
|---|---:|---:|
| before seq 345 | 66 842 | **100.0 %** |
| after seq 345 | 635 947 | **48.3 %** |

ARM S spent 100 % of its 709 454 tokens on the instance, because it has no
mechanism for spawning anything.

What the 53.2 % bought: 132 constructions attempted, 15 checker-valid, 117
checker-refuted (114 `CLAIM_INFLATED`, 3 `WRONG_COUNT`), **0 above the
run's own registered 0.005 floor, 0 survivors**. A read-only replay of the
root agrees and sharpens it: the harness's own status for all 132
construction artifacts is **refuted** — every one. The root's 909 accepted
artifacts are criticisms, verdicts and ritual outputs, not constructions.

So the operator's question — what fraction of ARM H's 702 789 tokens
produced anything that survived? — has an exact answer, and it is **zero**.
Not a small fraction: none. `cross_arm.py` → `CROSS_ARM.json`.

### The cross-arm ratio

At a matched budget (`T_S/T_H = 1.009`, admissible per that tranche's
PREREG §4):

| | ARM H | ARM S |
|---|---:|---:|
| tokens per attempted candidate | 5 324.2 | 13 138.0 |
| **tokens per valid candidate** | **46 852.6** | **30 845.8** |
| tokens per above-floor candidate | **undefined (0)** | 54 573.4 |
| prompt-side share | 79.8 % | 1.2 % |

**The one number is 1.519**: the apparatus paid 1.52x what blind sampling
paid per checker-confirmed construction. It is also the most generous
number available, because "valid" only means the checker confirmed the
claim. On the registered floor ARM H's cost per useful construction is not
large, it is undefined.

The prompt side states the same thing more starkly. ARM S poses the
instance in **163.9** prompt tokens. ARM H's mean generation prompt is
**3 959.5**. **24.2x the prompt to ask the same question** — and 70 % of
that prompt is the JSON Schema.

---

## 2026-08-26 — three token instruments, 27 disagreements

Each root states its provider spend three times. **27 of 54 roots
disagree**, in two clean classes. `flow.py` → `METER_RECONCILIATION.json`.

**Class A, 18 roots: `run-status.json` reports `token_spend: 0` while the
accounting and the log agree exactly on a real figure.** Every affected
root is `failed` or `running`. P-C1 ARM H, a 702 789-token run, reads zero
— and `deepreason results`, the one sanctioned retrieval surface, prints
that zero. A reader cannot distinguish "spent nothing" from "spent
everything and died".

**Class B, 9 roots: `TOKEN_ACCOUNTING.json` undercounts the log**, by
428 624 tokens in total. In 8 of the 9 the residual is exactly the
report-purpose spend: the post-terminal ledger and composition passes run
after the budget is exhausted and land in no counter, because
`token-accounting.v1` carries `bridge_provider_calls` but **no bridge token
field at all**. Worst case, `live_tri_2026-07-27/run-faa5feae…`: 138 396
of 330 396 tokens — 41.9 % of that run — spent composing its own report and
accounted as zero. The ninth root is worse than incomplete, it is
inconsistent: in `live_research_2026-07-29/narrow/run-7d87…`, 9 of 12
bridge calls were folded into `inquiry_provider_tokens` and 3 were not.

Both classes are PARKED, not fixed (`PARKED.md` P1, P2). This window
measures.

A third instrument caveat, found while building this one and worth as much
as either: **`attempt_trace.repair_scope` is populated on only 128 of the
456 repair re-asks.** It names the JSON pointer a repair was aimed at when
one was named. An earlier draft of `flow.py` read it as the repair marker
and reported the repair bill 3.6x too low. The record's own marker is the
`work_prepared` lifecycle transition's `trigger_ref`.

---

## 2026-08-26 — the two-call check: nothing to measure yet

**The split-budget protocol has never been exercised.** Across all 54
roots and 3 155 attempts, attempts carrying a non-empty `split_leg`: **0**.

The three split fields are present on 717 attempts in the 5 newest roots —
those written by code that has the feature — and every one is empty. The
only split content anywhere in the record is a typed notice,
`split-budget:repair-authorization-is-single-leg`, on 96 repair attempts:
the split budget declining to split a repair authorisation.

The W6 prompt asked for "the shipped fix's first field measurement". There
is none. No committed run has taken a split leg, so there is no extraction
pass to price and nothing it recovered. Reporting a zero cost here would be
reporting a success; the honest statement is that the instrument has no
reading because the mechanism has not fired.

---

## Residue — what this window did NOT establish

1. **Qualification tokens are unrecorded, everywhere.** The qualification
   battery is a real and repeated cost (CLAUDE.md budgets ~1 160 calls,
   ~14 min for a cache miss), and `production-contract-qualification.json`
   records cases, repairs and verdicts but **no tokens**. P-C1's own
   qualification ran 80 cases with 4 repairs; its token cost is not in the
   record and cannot be re-derived from it. Every "by purpose" number in
   this window therefore covers *inquiry* spend only. Parked as P3.

2. **Embedder and research-fetch usage are typed absences, not zeroes.**
   `TOKEN_ACCOUNTING.json` says so itself: `embedding_usage.usage_known:
   false`, `preflight_provider_usage.usage_known: false`. Not counted here,
   and not assumed to be small.

3. **The fate column is exact for un-decomposed conjecture and coarse
   elsewhere.** The downstream-window rule is self-checked and agrees with
   the explicit `conjecture-call:<seq>` backref 465 times out of 465, and
   every one of the 412 admitted `conjecturer.turn.v6` calls has artifacts
   in its window. For decomposition legs it does not: 291 of the 344
   admitted atomic legs create nothing in their own window, because the work
   banks in the sibling leg that completes the decomposition. Those 1 044 545 tokens are reported in their own
   class rather than as waste, but they are not attributed to an outcome.

4. **Pack sections that the allocator DROPPED are invisible.** A dropped
   section leaves no header and no placeholder, so `PACK_ANATOMY.json`
   reports what the model was SHOWN, never what the budget cut.
   `AllocationResult.accounting()` computes exactly the table that would
   close this gap — target, allocated, per-section, dropped flags,
   `mandatory_overflow` — and **nothing persists it**: a grep for
   `mandatory_overflow` or `allocated_tokens` across all 54 committed roots
   returns 0 roots. Parked as P4.

5. **`batch-critic.v2` cannot be sectioned at all** — 1 384 calls,
   2 804 637 tokens, 25.6 % of the program — because
   `render_batch_crit_pack` is not on the pack IR. Its prompt is split into
   preamble / schema / body and no further. Whether its 74.3 % body is
   evidence, targets or boilerplate is not answerable from the record as it
   stands.

6. **"Bought an artifact that ended accepted" is a structural measure, not
   a quality one.** It says the harness never refuted the artifact. P-C1 is
   the proof that the two can come apart completely: 909 accepted artifacts
   and 0 surviving constructions in the same root.

7. **No causal claim is made about the 41.2 %.** The record shows that
   `audit:ritual` was spawned by an `audit-critic` trigger and that spend on
   the seed question fell from 100 % to 48.3 % afterwards. Whether that
   spawn is a defect, a debt-sweep working as designed, or the right call
   badly timed is a question for a fixing family, not for a census. Parked
   as P5 with that framing intact.

8. **One call in 3 155 has no work terminal.** Log seq 2413 of
   `2026-08-25-change-constructive-frontier/void-inert-battery-run-6913328037a61ca6`
   — a repair re-ask at attempt index 3, arrival invalid — has a provider
   attempt and a semantic admission but no `workflow-work-terminal-v1`
   object. That root died `failed / operational_failure`, so a transaction
   in flight at the moment of death having no terminal is the expected
   shape of a crash rather than a gap in the record. It is carried through
   the tables as `outcome: no-terminal-record` (2 276 tokens) rather than
   folded into a neighbouring class.

9. **144 calls across 7 roots have no cycle.** Cycle is assigned from
   `progress.jsonl`'s cumulative token marks, because `log.jsonl` stamps no
   cycle on an event at all. A root that never recorded a completed cycle —
   every one of these 7 died at cycle 0 to 2 — gets `cycle: null` rather
   than a guess, and drops out of the growth curves. Any per-cycle table in
   this window therefore covers 3 011 of 3 155 calls.
