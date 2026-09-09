# DIAGNOSIS — the ceiling has a clean-stop road, and the v6 denial is not on it

One primary cause. Derived from the typed record first; code was read only to
name the line the record already pointed at.

## What the record says, before any code

At the epoch-0 terminal (commit `ebdfe976e`) of root
`run-c3f3bf10bc57d63e224a9f1c68bf1057`:

| fact | where |
|---|---|
| the last Control event before the stop carries trigger `budget-denied:token-budget` on work `sha256:dcd8fa45…` | `log.jsonl` seq 1165 |
| the very next event is `lifecycle_stopped` | `log.jsonl` seq 1166 |
| the published message is `token budget denied transactional work sha256:dcd8fa45…` | `run-status.json` |
| spend 495 362 against a ceiling of 500 000 | `run-status.json` |
| every seat in the run is capped at 8 192 completion tokens | `run-manifest.json` `roles` |
| the criticism road taken was the DIRECT one: 102 `criticism:` triggers, 0 `foreign-criticism:` triggers | `log.jsonl` |
| `criticism_policy` is null, which is what selects that road | `run-manifest.json` |
| the record itself is sound: 0 violations, re-derived | `runs/armR/ARMR_RESULTS.json` |

Two things follow from the record alone, without opening a source file.

**The budget really was spent.** The ceiling left at most 4 638 tokens. Every
seat this run could dispatch to is capped at 8 192 completion tokens, so no
further call — of any prompt length, including an empty one — could ever have
been reserved. The denial was not one oversized request against a budget with
room; it was the end of the budget.

**The message is a raised exception, not a decision.** `token budget denied
transactional work <work id>` is the text an exception carries, and it reached
`run-status.json` through the field that publishes `str(error)`. So the run did
not DECIDE to stop; something threw, and the terminalizer caught it.

## The cause

`Scheduler.run` already owns a clean budget-stop road, and it is typed on the
wrong exception.

`src/deepreason/scheduler/scheduler.py:3578` catches `TokenBudgetExceeded`,
records the drop, closes the workflow shadow, and `break`s out of the cycle
loop with no stop decision. `application/text_runs.py:407-410` then resolves
`scheduler_reason or "budget_exhausted"`, and line 420 takes the branch that
writes a typed STOPPED lifecycle receipt. That road is the operator's law of
2026-08-29 already implemented: a clean terminal that secures continuation.

The v6 transactional path does not raise `TokenBudgetExceeded`. When the meter
refuses a reservation, `workflow/transaction_service.py:414-442` appends the
durable `budget_denied` terminal and raises **`WorkBudgetDenied`** — a plain
`RuntimeError`, raised `from` the `TokenBudgetExceeded` that caused it.
`WorkBudgetDenied` is not a subclass of `TokenBudgetExceeded`, so the cycle
loop's budget arm does not see it.

The escape route this run took:

1. `rules/crit.py:471` re-raises `WorkBudgetDenied` deliberately — the typed
   terminal is already durable and a second transition after termination is a
   well-formedness failure (the recorded `run-e542c3c1` incident, seam
   `DR-SEAM-scheduler-x-workflow` Traps).
2. `scheduler.py:1601-1604` — `_arg_crit`'s direct batch road — catches only
   `(SchemaRepairError, EndpointError)`.
3. `Scheduler.run`'s budget arm catches only `TokenBudgetExceeded`.
4. `application/text_runs.py:1562` catches `(Exception, SystemExit)` and
   publishes `stop_reason="operational_failure"` with `message=str(error)`.

Step 4 is where the classification is WRITTEN; steps 2 and 3 are why it is
reached. Nothing on that path ever asks whether the budget was spent — the
catch-all cannot, because by then the only thing left of the denial is its
message.

## What distinguishes "spent" from "denied for another reason"

`llm/budget.py::TokenMeter.reserve` refuses in three distinguishable shapes,
and only one of them is the ceiling ending the run:

| shape | raised when | is the budget spent? |
|---|---|---|
| no prompt bound | a finite ceiling and no way to bound the prompt | **no** — a fail-closed plumbing refusal |
| no completion bound | a finite ceiling and `max_tokens` unknown | **no** — same |
| `total + reserved + amount > budget` | the booking will not fit | **only sometimes** |

The third shape covers both cases the goal must separate. The separating
quantity is the remaining headroom against the denied request's own completion
cap:

    remaining = budget - total - reserved
    spent     = remaining < max_tokens

When `remaining < max_tokens`, no dispatch at that cap can ever be served
again, whatever its prompt — the budget has nothing left, and the stop is the
ceiling. When `remaining >= max_tokens`, the refusal was about THIS prompt's
length; a shorter one still fits, budget remains, and the stop is not clean.

Applied to the record: remaining ≤ 4 638, cap 8 192 → spent. The predicate
classifies the observed root the way the operator's law requires, and it does
so from quantities the meter already holds.

## What this is NOT

- Not a defect in what the run recorded. `verify_root` re-derives 0
  violations on this root.
- Not `_arg_crit`'s missing exception arm alone. Adding `WorkBudgetDenied`
  there would let the cycle continue past a ceiling that has nothing left,
  which is a worse answer than stopping. The loop, not the criticism road, is
  where a spent budget belongs.
- Not the terminalizer's catch-all. It classifies correctly for everything it
  can see; the denial should never have reached it.

## Confidence, and what would refute this

Refuted if a run reproduces `stop_reason: operational_failure` on a
`WorkBudgetDenied` after the cycle loop's budget arm accepts it, or if the
observed root's denial turns out to carry a shape other than budget pressure.
REPRO.md builds the smallest offline artifact that decides both.
