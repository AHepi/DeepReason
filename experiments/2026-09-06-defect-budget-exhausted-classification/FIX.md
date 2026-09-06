# FIX — put the v6 denial on the clean road that already exists, and only when the ceiling is spent

## The shape of the fix, in one sentence

The meter says whether its refusal means the ceiling has nothing left; the
denial carries that answer out of the transactional service; and the cycle
loop's existing budget arm — the one that already ends a run clean — accepts
the denial when, and only when, the answer is yes.

Nothing new is invented. `Scheduler.run` already absorbs
`TokenBudgetExceeded` and breaks with no stop decision, and
`application/text_runs.py:407-431` already turns that into
`stop_reason: budget_exhausted`, a typed STOPPED lifecycle receipt and
`checkpoint.json`. The v6 denial has simply never been on that road.

## Frozen-surface reading — no grant needed

`tools/blast_radius.py` over the four files this fix touches, with the new
symbol declared, returns `"frozen_surface_verdict": "CLEAR"`.

Declaring the generic method names `run` and `check` instead returns
`CONTACT` with **eight rows, all `SYMBOL_INDIRECT`** — the tool's own
grep-collision tier, which it labels "not proof of semantic contact". Each is
disposed of the same way, and the disposal is checkable rather than argued:

| rows | disposal |
|---|---|
| `capabilities/state.py` ← `run`; `harness.py` ← `run`, `check`; `invariants.py` ← `run`, `check`; `run_manifest.py` ← `run`, `check`; `qualification.py` ← `run` | the words appear in those files, the referents do not: no frozen file names `TokenMeter`, `TokenBudgetExceeded`, `deepreason.llm.budget`, `Scheduler.run` or `TokenMeter.check` anywhere (`grep -rn "llm.budget\|TokenMeter\|TokenBudgetExceeded"` over all five plus `verification/` returns nothing) |
| 2 frozen-ADJACENT rows (`route_fingerprint`) | the fix touches no route, lease, firewall or fingerprint |

And positively: `budget_exhausted` is already a `StopReason`
(`runtime/stop.py:20`), already in `RESUMABLE_STOP_REASONS`, already in
`COMPOSABLE_STOP_REASONS` and already in `_RUNTIME_DECIDED_STOP_REASONS`
(`workflow/lifecycle.py`). No stop vocabulary moves, no record format
changes, no digest is recomputed, no `Config` field is added — so
`_versioned_source_config_data` is untouched and no qualification subject
digest can move.

## The change, file by file

### 1. `src/deepreason/llm/budget.py` — decide it where the numbers are

`TokenMeter` is the only object holding the ceiling, the spend, the
outstanding reserves and the refused request's cap at the same instant. Every
refusal it raises is stamped with three fields:

- `budget_remaining` — `budget - total - reserved`, or `None` with no ceiling.
- `budget_minimum_dispatch` — the smallest booking any further dispatch of
  the refused shape needs, which is its completion cap (a prompt bound is
  never negative), or `None` when the cap itself is unknown.
- `budget_exhausted` — the answer, by one rule:

> **The ceiling is spent when its remaining headroom cannot cover another
> dispatch: nothing left at all, or less than the refused shape's completion
> cap.**

Applied to the three refusals `reserve()` can raise, and to `check()`:

| refusal | `budget_minimum_dispatch` | spent? |
|---|---|---|
| `total + reserved + amount > budget` | the request's `max_tokens` | when headroom < that cap |
| no prompt bound | the request's `max_tokens` | same test |
| no completion bound | `None` (unknown cap) | only if headroom ≤ 0 |
| `check()` — total already at or past the ceiling | `None` | always (headroom ≤ 0) |

A module function reads the answer back:

    def budget_denial_exhausted(error) -> bool:
        return bool(getattr(error, "budget_exhausted", True))

**The default is True, deliberately.** Every raise site that predates this
field is a ceiling already reached, and every existing caller treats those as
clean stops. A default of False would silently reclassify stops this tranche
was not asked to touch.

### 2. `src/deepreason/workflow/transaction.py` — carry it across the exception change

`WorkBudgetDenied` gains a `budget_exhausted` attribute, **defaulting False**,
and an optional constructor keyword. False is right for the default because
the other construction site (`workflow/atomic_recovery.py:39`) rebuilds a
denial from a terminal recorded in an earlier epoch: that is evidence about a
past reservation, not about what the current ceiling can still book.

### 3. `src/deepreason/workflow/transaction_service.py` — one argument

`reserve_dispatch` already catches the `TokenBudgetExceeded` it re-raises
`from`. It passes that error's verdict to the denial it raises. The durable
`budget_denied` terminal and its transition are unchanged — same record, same
`reason_code`, same trigger.

### 4. `src/deepreason/scheduler/scheduler.py` — one arm, one guard

`Scheduler.run`'s budget arm widens to `(TokenBudgetExceeded,
WorkBudgetDenied)` and opens with:

    if not budget_denial_exhausted(e):
        raise

Everything after that guard is the existing body, unchanged: record the drop,
close the workflow shadow, `break`. A denial the ceiling could still have
afforded re-raises and reaches the terminalizer exactly as it does today.

**Why this arm and not the terminalizer's catch-all.** The catch-all cannot
tell the difference — by the time it runs, the only thing left of the denial
is its message — and building a clean terminal inside a failure handler would
be a second copy of a sequence that already exists, which is how the two
launch paths drifted before they were unified. Putting the denial on the one
existing road keeps a single publisher for every clean stop.

**Why not widen `_arg_crit`'s exception arm instead.** That would let the
cycle continue past a ceiling with nothing left — every subsequent dispatch
denied, the run grinding to no purpose. The loop, not the criticism road, is
where a spent budget belongs. (`_arg_crit`'s narrower arm is real and is
PARKED, not fixed here: see PARKED.md.)

## What the tests must prove

Committed regression tests, in `tests/test_budget_exhausted_classification.py`:

1. **The rule, at the meter.** The observed root's own numbers (ceiling
   500 000, spend 495 362, cap 8 192) produce `budget_exhausted: True`; an
   oversized single request against an untouched ceiling produces `False`;
   both fail-closed shapes are covered; a denial with no metadata reads True.
2. **Exhausted → clean, through the real run path.** A run driven through
   `deepreason run --run-manifest` whose cycle raises an exhausted denial
   publishes `state: completed`, `stop_reason: budget_exhausted` — and meets
   the checkpoint obligation of the same law: `checkpoint.json` written, a
   typed STOPPED lifecycle receipt carrying that reason, and
   `prepare_continuation` accepting the root.
3. **Not exhausted → unchanged.** The same run with a denial the ceiling
   could still have afforded publishes `state: failed`,
   `stop_reason: operational_failure`.

Each is mutation-proven: reverting the guard, the arm, or the rule turns a
named assertion red, captured under `proof/`.

## Diff budget

Production code, four files, well under the 150-line stop condition:
roughly 35 lines in `budget.py`, 10 in `transaction.py`, 3 in
`transaction_service.py`, 10 in `scheduler.py`. Plus tests and the map, which
moves in the same commit.

## Approval gate

No frozen surface is contacted, so no operator grant is required and this
tranche does not stop here. Recorded in these terms so a later reader can
check the claim rather than trust it.
