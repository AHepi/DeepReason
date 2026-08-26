# PARKED — W6, the token-flow map

Five findings. This window measures; it fixes nothing, anywhere (PROGRAM.md,
"What this program will not do"). Each entry is one line of WHAT and then a
ready-to-send prompt. Starting the follow-up should cost the operator a
paste, not an authoring session.

Priority order as this window would rank it: **P1** (a run's spend reads as
zero) is the cheapest fix with the widest blast radius, because it corrupts
the one sanctioned retrieval surface. **P4** (the pack accounting is
computed and thrown away) is the one that most limits future measurement.
**P5** is not a defect and must not be sent as one.

---

## P1 — `run-status.json` reports `token_spend: 0` on every non-terminal root

**What.** 18 of 54 committed roots carry `token_spend: 0` while
`TOKEN_ACCOUNTING.json` and `log.jsonl` agree exactly on a real figure.
Every affected root is `failed` or `running`. P-C1 ARM H — 702 789 tokens —
reads zero, and `deepreason results`, the one sanctioned retrieval surface,
prints that zero. A reader cannot tell "spent nothing" from "spent
everything and died". Evidence: `METER_RECONCILIATION.json`,
`roots_where_status_is_zero_but_log_is_not`.

```
Route: deepreason-orchestrator.

One goal: make a run's recorded token spend readable on a root that did
not reach a clean terminal.

The defect. 18 of the 54 committed run roots carry `token_spend: 0` in
run-status.json while TOKEN_ACCOUNTING.json and the sum over log.jsonl
agree exactly on a real, large figure. Every affected root is in state
`failed` or `running`; every root in state `completed` is correct. So the
field is stamped only at a clean terminal, and on any other root it reads
as a spend of zero rather than as an absence.

Why it matters more than it looks. `deepreason results ROOT --json` is the
ONE retrieval surface for a run's typed outcome (dr-drive-harness section
2), and it prints that zero. On P-C1 ARM H — experiments/2026-08-25-change-
constructive-frontier/run, run id 1950b3d0ee228113, a 702 789-token run
that died at cycle 15 — `deepreason results` reports `token_spend: 0`. The
repo's own convention is that an absent fact prints as a TYPED ABSENCE and
is never omitted or defaulted; a silent zero breaks that convention in the
direction that reads as a fact.

Evidence to start from, no re-derivation needed:
  experiments/2026-08-26-run-anatomy-program/W6-token-flow/
    METER_RECONCILIATION.json  -- per-root, the three instruments side by
                                  side; `roots_where_status_is_zero_but_
                                  log_is_not` is 18
  Reproduce with: deepreason results experiments/2026-08-25-change-
    constructive-frontier/run --json | grep token_spend

End state. Either the field carries the real spend on a non-terminal root,
or it reports a typed absence that `results` renders as one. NOT a zero.
Decide which by reading how the other absences in `results` are typed
(`_absent`, NO_FRONTIER_RECORD and friends in src/deepreason/application/
results.py) and match them. Regression test asserts a non-terminal root's
spend is readable and is not 0 when the log says otherwise.
```

---

## P2 — `token-accounting.v1` has no field for report-pass tokens

**What.** The post-terminal ledger and composition passes ("bridge") spend
real provider tokens that land in no counter: `token-accounting.v1` carries
`bridge_provider_calls` but no bridge token field at all. 428 624 tokens
across 9 roots fall outside `inquiry_provider_tokens`; worst case 138 396
of 330 396 in one root, 41.9 % of that run, accounted as zero. And the
counter is inconsistent with itself: in one root 9 of 12 bridge calls WERE
folded into the inquiry total and 3 were not.

```
Route: deepreason-orchestrator.

One goal: make the report-composition pass's provider tokens countable,
and make the inquiry counter's boundary consistent.

The defect, two halves.

(a) NO COUNTER. TOKEN_ACCOUNTING.json (schema token-accounting.v1) carries
`bridge_provider_calls` and `bridge_repairs` but no bridge TOKEN field.
The post-terminal ledger and composition passes -- contracts
bridge.ledger.v3, bridge.ledger-batch.v1, bridge.composition.v2,
bridge.composition-batch.v1 -- spend real provider tokens that therefore
appear in no counter anywhere. Program-wide that is 504 116 tokens over 48
calls, 4.6% of all spend, and per-root it reaches 41.9%:
experiments/live_tri_2026-07-27/run-faa5feae126bc2558ea9c6d8d200a90c spent
138 396 of its 330 396 tokens composing its own report, and its accounting
says `bridge_provider_calls: 0`.

(b) INCONSISTENT BOUNDARY. In experiments/live_research_2026-07-29/narrow/
runs/run-7d8723fbe8626c71db880826c244d332, 9 of 12 bridge calls WERE folded
into `inquiry_provider_tokens` and 3 were not (accounting says 314 308, the
log says 351 440, and the 37 132 residual is 3 calls, not the whole report
pass). So the same counter includes bridge spend in some runs and excludes
it in others.

Evidence to start from:
  experiments/2026-08-26-run-anatomy-program/W6-token-flow/
    METER_RECONCILIATION.json  -- `residual_log_minus_accounting` and
                                  `residual_explained_by_report_purpose`
                                  per root; 9 roots non-zero, 8 explained
    FLOW_AGGREGATE.json        -- `program_by_purpose` -> `report`

NOTE BEFORE DESIGNING: TOKEN_ACCOUNTING.json's schema is a record format.
Check docs/map/INV-frozen-surfaces.md before changing its shape -- adding a
field to a committed record schema may be a frozen-surface change requiring
explicit operator approval, and finding that out after the code is written
is the expensive order.

End state. Every provider token in a root is inside exactly one counter, and
the same call class is counted the same way in every root. Regression test
asserts the sum over the counters equals the sum over log.jsonl for a
fixture root that runs a report pass.
```

---

## P3 — qualification spends tokens that the record does not carry

**What.** The qualification battery is a real, repeated cost — CLAUDE.md
budgets ~1 160 calls and ~14 minutes for a cache miss — and
`production-contract-qualification.json` records cases, repair counts and
verdicts but **no tokens**. P-C1's own qualification ran 80 cases with 4
repairs; what it cost is not in the record. Every "by purpose" number in
this window is therefore inquiry-only, and says so.

```
Route: deepreason-orchestrator.

One goal: record the qualification battery's provider token cost in the
qualification artifact, so a run's total cost is derivable from the record.

The gap. production-contract-qualification.json (schema deepreason-
production-contract-doctor-v1) records, per pair and per case:
first_pass_valid, eventual_valid, repair_count, scope_violations,
semantic_admission -- and no token count of any kind. CLAUDE.md budgets a
qualification cache MISS at roughly 1 160 provider calls and ~14 minutes,
so this is not a rounding error; it is plausibly comparable to a whole
reason run. P-C1's battery: 80 cases across 4 pairs, 4 repairs, 1
unqualified pair re-exercised (experiments/2026-08-25-change-constructive-
frontier/qualify.json).

Consequence today: the RUN ANATOMY PROGRAM's D10 tables cover inquiry
provider spend only, and cannot state what a run cost end to end. A cache
HIT costs ~1s and should record a token cost of zero with usage_known
true, which is a different statement from the silence there is now.

Evidence to start from:
  experiments/2026-08-25-change-constructive-frontier/qualify.json
  experiments/2026-08-25-change-constructive-frontier/run/
    production-contract-qualification.json
  experiments/2026-08-26-run-anatomy-program/W6-token-flow/RESULTS.md,
    "Residue" item 1

Follow TOKEN_ACCOUNTING.json's own convention for an unknown: it already
carries `embedding_usage.usage_known: false` and `preflight_provider_usage.
usage_known: false`, which is how this codebase says "not measured" without
saying "zero". Whatever is added should be able to say the same thing.

NOTE BEFORE DESIGNING: anything altering qualification subject digests is a
FROZEN SURFACE (CLAUDE.md, docs/map/INV-frozen-surfaces.md). Adding a token
field must not change what the subject digest covers, or every cached
qualification in every home is invalidated. Establish that first.

End state. A qualification artifact states its provider token cost, or
states a typed absence. Regression test asserts the subject digest is
unchanged by the addition.
```

---

## P4 — the pack's per-section accounting is computed and thrown away

**What.** `AllocationResult.accounting()` in
`src/deepreason/packs/allocate.py` computes exactly the table needed to say
where a prompt token went — `target_tokens`, `allocated_tokens`,
`mandatory_overflow`, and per section `tokens` / `source_tokens` /
`dropped` / `cache_group` — and nothing persists it. A grep for
`mandatory_overflow` or `allocated_tokens` across all 54 committed roots
returns **0**. This window had to re-derive the section table by parsing
rendered prompt blobs, which can only report what the model was SHOWN and
is structurally blind to what the budget CUT.

```
Route: dr-change-orchestrator (this is an addition, not a defect).

One goal: persist the pack allocator's own per-section accounting into the
record, so what the budget dropped is recoverable.

The situation. src/deepreason/packs/allocate.py already builds the exact
table: AllocationResult.accounting() returns target_tokens,
allocated_tokens, mandatory_overflow, and per section {tokens,
source_tokens, dropped, cache_group}. Its only caller in the whole tree is
-- none; grep 'accounting()' finds one unrelated hit in application/
text_runs.py. Nothing writes it to a log, an object or a blob: grepping
mandatory_overflow or allocated_tokens across all 54 committed run roots
returns 0 roots.

Why it matters. A dropped section leaves NO header and NO placeholder in
the rendered prompt (docs/map/CON-packs-and-token-economy.md, "NO SILENT
CAPS" -- absence is the only signal). So a prompt blob cannot distinguish
"the run had no admitted evidence" from "the budget cut the evidence
legend". The disclosure mechanism (DISCLOSED_ON_DROP, the context-withheld
notice) covers exactly four sections; every other drop is invisible after
the fact. W6 measured the pack anatomy from blobs and could only report
what the model was shown -- see experiments/2026-08-26-run-anatomy-program/
W6-token-flow/PACK_ANATOMY.json and RESULTS.md "Residue" item 4.

What W6 could then answer that it cannot now: how often a section is
dropped, which ones, at what budget, and whether mandatory_overflow is ever
non-zero in a live run.

Scope note, so this stays small: this is a WRITE of an already-computed
value at the point of render. It is not a change to allocation, to
priorities, or to any budget. Read docs/map/INV-frozen-surfaces.md first --
the record formats are frozen and a new object family or log field may need
explicit operator approval before design, not after.

End state. Each provider call's record carries its pack's section
accounting. A test asserts a dropped section is recoverable from the record
for a pack rendered under a budget that drops one.
```

---

## P5 — 41.2 % of P-C1 ARM H went to a problem the run spawned about its own critic

**What.** ARM H spent 373 903 tokens (53.2 %) on the operator's seed
question and 289 676 (41.2 %) on `audit:ritual`, a problem the run created
at log seq 345 of 3 200 with provenance `{"trigger": "audit-critic"}`.
Before that spawn, 100 % of spend was on the seed question; after it, 48.3 %.

**This is NOT parked as a defect and must not be sent as one.** The record
shows the allocation; it does not show that the allocation was wrong. The
run may have been doing exactly what a debt sweep is meant to do. What the
record does establish is that the behaviour is expensive and, before this
window, unmeasured — so the question is worth putting, and it is a design
question for the operator, not a bug report.

```
Route: dr-ask-the-right-question first, then whichever family the operator's
answer selects. Do NOT open this as a defect.

The measurement, not the accusation. In P-C1 ARM H (experiments/2026-08-25-
change-constructive-frontier/run, run id 1950b3d0ee228113, 702 789 tokens,
292 provider calls), the budget divides:

  the operator's seed question   61 calls   373 903 tokens   53.2%
  audit:ritual                  203 calls   289 676 tokens   41.2%
  repair re-asks (no pack)       28 calls    39 210 tokens    5.6%

audit:ritual is "audit the critic: adjudication-ritual flags sustained
(§11.3)", provenance {"trigger": "audit-critic"}, spawned at log seq 345 of
3 200 -- about two cycles in. It then spawned disc:audit:ritual,
"discriminate between 20 surviving rivals", at seq 603. Before seq 345,
100.0% of spend was on the seed question; after it, 48.3%.

The competing arm, ARM S, spent 100% of a matched 709 454 tokens on the
instance -- it has no mechanism for spawning anything -- and beat ARM H by
a factor of 33 on best score.

The question for the operator, and it is genuinely open:

  Is a self-spawned audit problem entitled to compete for budget with the
  seed question on equal terms, or should the seed question hold a floor?

CLAUDE.md already records a related invariant -- "The operator's seed
question always wins scheduler rank TIES" -- which is a tie-break rule and
not a budget floor, and nothing in this record suggests the tie-break
failed. So the honest framing is: the existing rule is doing what it says,
and the measurement asks whether what it says is what the operator wants.

Three roads, priced:
  (a) leave it -- the audit ritual is criticism doing its job, and a run
      that never audits its own critic is worse, not cheaper. Costs
      nothing, changes nothing.
  (b) a seed-question budget floor -- a declared minimum share the seed
      problem cannot be scheduled below. Cheapest real change; needs a
      design decision about what the floor is and what happens when the
      seed problem has nothing to do.
  (c) make it visible instead of governed -- report per-problem spend in
      `deepreason results` so a run's drift is legible while it happens,
      and decide later. Smallest blast radius; answers nothing on its own.

Evidence to start from:
  experiments/2026-08-26-run-anatomy-program/W6-token-flow/
    PC1_POSTMORTEM.json   -- the_line_that_matters, the_spawn, by_problem
    RESULTS.md            -- the P-C1 segment
```
