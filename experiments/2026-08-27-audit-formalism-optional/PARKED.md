# PARKED — findings this read-only tranche does not fix

This audit changed nothing under `src/` or `tests/`. Each item below is a
ready-to-send prompt: starting the follow-up should cost a paste, not an
authoring session.

---

## P1 — the atomic-decomposition fallback discards admitted children on a budget denial

**What.** `rules/conj.py::_v6_atomic_conjecture_fallback` accumulates child
candidates in a local list and returns only after looping over ALL children.
There is no `WorkBudgetDenied` handler inside the loop, so a denial on child *n*
throws away children `0..n-1` that were already admitted and paid for. In P-C2b
this lost the run's best construction: two of six children were admitted
(`atomic_conjecture_output_admitted` × 2) and the rest hit
`token_budget_denied` (50 such terminals in that root).

Not a formalism finding — the census confirmed the dropped candidate was the
same kind as the four that were scored — but a real and expensive defect.

```
Route through deepreason-orchestrator.

GOAL (one tranche, one goal): a token-budget denial partway through an atomic
conjecture decomposition must not discard the children already admitted.

Evidence, all committed:
  experiments/2026-08-27-audit-formalism-optional/EXEMPLARS.md   -- the full trace
  experiments/2026-08-27-pc2b-symmetric-reasoning/run            -- the root
    log.jsonl seq 58, 63: llm.attempt_trace[0].valid == true, contract_id
      "conjecturer.atomic-candidate.v1"
    objects/workflow-work-terminal-v1: 2 atomic_conjecture_output_admitted,
      50 budget_denied/token_budget_denied
    objects/workflow-contract-decomposition-transition-v1: maximum_children 6
    the ONLY Conj event is seq 99, carrying four candidates from the seq-90
      conjecturer.turn.v6 call -- seq 58 and 63 minted nothing
  src/deepreason/rules/conj.py:450  _v6_atomic_conjecture_fallback
  src/deepreason/workflow/transaction_service.py:402  raise WorkBudgetDenied

DIAGNOSE FROM THE RECORD FIRST, then read the code. The question the fix must
answer: when children 0..n-1 are admitted and child n is budget-denied, is the
right terminal (a) return the partial candidate set with a typed
partial-decomposition disclosure, or (b) recover the admitted children on the
next attempt through workflow/atomic_recovery.py, which already exists for
exactly this shape? Price both against the all-configurations law -- disclose,
never die -- and against replay determinism before choosing.

Frozen surfaces: none expected. The decomposition transition record format IS a
manifest-adjacent schema, so check docs/map/INV-frozen-surfaces.md before
touching objects/workflow-contract-decomposition-transition-v1.

END STATE: a regression test that drives a six-child decomposition with the
budget exhausted at child 2 and asserts the two admitted candidates survive to
a Conj event; the full gate green; docs/map/CON-conjecture-kinds.md and
SUB-workflow.md Traps entries naming P-C2b.
```

---

## P2 — the `coverage` Pareto axis prices formality (the audit's one UNLAWFUL-PENALTY)

**What.** `PARETO_AXES = ["hv", "reach", "coverage"]`, `frontier()` maximises
every axis, and `coverage` is `0.0` when an artifact carries no EVALUABLE
commitment. A prose survivor is therefore dominated by an otherwise-identical
formally-backed one and leaves the frontier — and `frontier_delta` feeds the
stop decision. The law: *"its absence grants no disadvantage."*

```
Route through dr-change-orchestrator (this is a design change to a scored axis,
not a defect repair -- the operator decides what coverage should mean).

OPERATOR DECISION NEEDED FIRST, then the change:
  An artifact with no evaluable commitment currently scores coverage 0.0 --
  the same score as an artifact whose battery FAILED. Should "nothing to
  check" and "checked and failed" share a coordinate?

Three roads, priced:
  (a) NOT-MEASURED, not zero. Drop an artifact with an empty battery out of the
      coverage comparison rather than scoring it 0.0 (dominance computed on the
      axes both artifacts actually have). Smallest change; makes prose
      incomparable rather than last. Cost: `frontier()` currently treats a
      missing score as 0.0 by documented design, so this touches
      capture/pareto.py's contract, and every committed root's frontier moves.
  (b) Neutral default. Score an empty battery at the population mean or at 1.0
      ("nothing forbids it, nothing refutes it"). Cheapest; also the least
      honest, since it invents a measurement.
  (c) Leave it and disclose. Keep the axis and add a typed
      `coverage_not_measured` disclosure per survivor, so a reader can see
      which frontier exclusions were kind-driven. No behaviour change.

Evidence, all committed and re-runnable:
  experiments/2026-08-27-audit-formalism-optional/repro_coverage_rank.py
    -- exit 0 = reproduced; three legs, one of them a mutation proof
  experiments/2026-08-27-audit-formalism-optional/VERDICT.md section 2
  src/deepreason/scheduler/scheduler.py:216-234   run_report / coverage
  src/deepreason/capture/pareto.py:9              frontier
  src/deepreason/config.py:353                    PARETO_AXES
  LIVE FOOTPRINT: experiments/2026-08-12-live-grounded-extension-expansion/run
    -- exactly two score triples among 233 survivors: 146 prose at
       (0.0, 0.0, 0.0), 87 formal at (0.0, 0.0, 1.0); frontier == the 87.

Read BEFORE designing: docs/map/INV-frozen-surfaces.md, then
docs/map/CON-scheduler-ranking.md and CON-conjecture-kinds.md (R-g).
Note the 2026-08-14 law: old roots owe the future nothing, so a moved frontier
on historical roots is NOT by itself a reason to reject a road.

END STATE: the chosen road implemented; repro_coverage_rank.py updated to
assert the NEW behaviour (and to fail if the penalty returns); an architecture
test that goes red if a new Pareto axis is added whose zero value is reachable
by carrying no commitment; the full gate green; CON-conjecture-kinds.md's
"Where to change what" table and a Traps entry updated in the same commit.
```

---

## P3 — prose criticism is 1.4 % of status-changing traffic (an operator decision, not a defect)

**What.** A DEMONSTRATIVE warrant changes a status under every mode. An
ARGUMENTATIVE one requires `ADJUDICATION_STATUS_AUTHORITY_ENABLED` (default
`False`) plus a non-`observe_only` `ARGUMENTATIVE_AUTHORITY` (default
`observe_only`) plus a cross-family judge ensemble that survives referential-
integrity, unanimity and paraphrase screens. Measured across 6 789 committed
artifacts: **8 argumentative warrants against 551 demonstrative.**

This is a penalty on prose CRITICISM. The standing law speaks of conjectures;
the 2026-08-27 commissioning words explicitly name criticism too. It is parked
rather than filed as a violation because the asymmetry has a stated ground and
because the operator's own 2026-08-09 law is wary of judges.

```
Route through dr-ask-the-right-question FIRST, then dr-change-orchestrator only
if the operator wants a change.

THE QUESTION FOR THE OPERATOR (do not design before it is answered):
  A formal refutation always changes a status. A prose refutation changes none
  unless you switch judges on, and you have said you would prefer to do without
  them ("they prosecute without any discernable discrimination", 2026-08-09).
  Measured over every committed root: 8 prose warrants, 551 formal ones.
  Is that the price you intend prose criticism to pay, or do you want a
  judge-free road by which an argument alone can change a status?

If the answer is "I want a judge-free road", the design constraints are already
ledgered and must be read first:
  experiments/2026-08-14-change-calculus-reconciliation-v2/RECONCILIATION.md
    -- the siren example, R26/R27: X must fall BY ARGUMENT ALONE, and the
       design's answer was to route it through a PROGRAM (the premise rent
       battery) rather than to let prose mint a warrant directly. That is the
       precedent to either extend or overturn.
  CLAUDE.md, the 2026-08-09 solo-run law: any road must work for a solo model.
  src/deepreason/informal/trial.py:920 and the guards around it.
  src/deepreason/config.py:504-509.

Evidence: experiments/2026-08-27-audit-formalism-optional/VERDICT.md section 4;
TABLES.md (warrant rows); KIND_CENSUS.json.

END STATE if a change is wanted: a specified road, its solo-compatibility
argued explicitly, and its determinism story stated (what replays byte-for-byte
when the decisive input is an argument).
```

---

## P4 — nine STRUCTURAL-GAP rows share one root cause, and no one has priced it

**What.** `SITES.md`'s nine STRUCTURAL-GAP rows reduce to one predicate:
`measures/demarcation.py::crit` — *does the artifact carry any registered
commitment?* Through it, an artifact that declares nothing is shut out of reach
(`measures/reach.py:137`), the knowledge view (`views/knowledge.py:52`),
promotion nomination (`calculus/nomination.py:182`, `:260`) and two promotion
criteria (`calculus/promotion.py:239`, `:550`). None of this is unlawful — an
interface that forbids nothing genuinely has no attack surface — but the law's
spirit says a gap must not quietly become a penalty, and nobody has written
down what a prose road through it would look like.

```
Route through dr-audit-orchestrator (a scoped read-only follow-up), or park
indefinitely -- this is a design question, not a defect.

GOAL: one document (docs/map/CON-attack-surface-and-prose.md, or a section in
CON-conjecture-kinds.md) that states, for each of the five consumers of
`measures/demarcation.py::crit`, what a commitment-free prose artifact would
need in order to have a road there, and what it would cost.

The five: measures/reach.py:137 (reach), views/knowledge.py:52 (knowledge
view), calculus/nomination.py:182/:260 (nomination), calculus/promotion.py:239
(subject-demarcation), calculus/promotion.py:550 (rent).

Evidence: experiments/2026-08-27-audit-formalism-optional/SITES.md, the
STRUCTURAL-GAP section; KIND_CENSUS.json shows reach>0 on 1 of 6 789 artifacts
and the knowledge view non-empty on 1, so the gap's live cost is currently
almost entirely theoretical -- SAY SO in the document rather than implying
prose is being shut out of something the record shows anyone reaching.

END STATE: the document, with a `check:` per load-bearing claim per
docs/map/SCHEMA.md, and docs_verify green. No code changes.
```

---

## P5 — `oracle.EXEC_PROGRAMS` has never fired in a committed run

**What.** Across 55 roots and 6 789 artifacts, **zero** carry a commitment in
`EXEC_PROGRAMS`. Every execution-supremacy branch (`crit.py:1544`,
`crit.py:2157`, `vision.py:91`), the counterexample channel
(`packs.py:200`, `:1050`), the counterexample retry (`crit.py:1551`, `:2174`)
and `_standing_recrit_pool`'s kind ordering (`scheduler.py:1396-1416`) are
gated on a predicate no committed run has ever satisfied.

Noted, not fixed. It matters for this audit because it means the tree's
strongest LAWFUL-PROTECTION surface — the one the law explicitly permits — is
also its least exercised, and any future tranche reasoning about
formal/informal balance from code alone will over-weight it.

```
Route through dr-audit-orchestrator (broken dimension) if anyone wants this
turned into a finding; otherwise leave parked.

GOAL: decide whether the EXEC_PROGRAMS path is DEAD (no public route
constructs the first such commitment -- the state DR-CON-conjecture-kinds
already records for the property-oracle counterexample path, "full chain:
experiments/2026-08-08-live-two-seat-ab-s6/PARKED.md P1") or merely UNUSED.

Evidence: experiments/2026-08-27-audit-formalism-optional/KIND_CENSUS.json --
`execution_backed` is false for all 6 789 artifacts. The reference-census
recipe is dr-audit-dead's.

END STATE: a row in an AUDIT_REPORT.md saying DEAD or UNUSED with the reference
chain, and -- if DEAD -- a parked prompt to either build the missing
constructor or retire the branches. No code changes in the audit itself.
```
