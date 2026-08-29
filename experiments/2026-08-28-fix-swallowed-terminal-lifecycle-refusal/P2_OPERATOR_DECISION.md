# P2 — the one question this window could not answer, and what it needs

Written at the close of the P6/P3 window. P6's own note says it best: *"This
also re-frames P2: the same swallow-versus-surface split is at work there."*
Tranche 1 made the split VISIBLE. Whether the current behaviour is RIGHT is
the operator's call, and this document exists so that call costs one reading
rather than a re-investigation.

## The question, in one sentence

**When a run's token budget denies a work reservation, is that an OPERATIONAL
FAILURE — or is it just the budget running out?**

## Why it matters, concretely

The two answers land a run in two different terminals, and only one of them
can ever be resumed (`workflow/lifecycle.py`,
`RESUMABLE_STOP_REASONS = {"converged", "budget_exhausted"}`):

| terminal | reached when | resumable |
|---|---|---|
| `budget_exhausted` | the cycle loop or token meter decides to stop | **yes** |
| `operational_failure` | `WorkBudgetDenied` escapes to the generic `except (Exception, SystemExit)` | **no** |

A run that hits `operational_failure` can never be continued or amended. The
tokens it spent are spent; the only route forward is a new run from the
beginning.

## The evidence, re-derived in this window rather than quoted

The audit (`experiments/2026-08-28-audit-run-problems/` §F-E) reports that the
denial is typed and durable BEFORE the raise. Re-checked here against the
source and against two committed roots:

**1. The denial is recorded durably, then raised — in that order.**
`workflow/transaction.py:691` — the exception's own docstring is the claim:

```python
class WorkBudgetDenied(RuntimeError):
    """Raised after a durable ``budget_denied`` terminal was appended."""
```

`budget_denied` is a declared member of `WorkTransitionKind` (`:125`) and a
legal `WorkTerminalV1.status` (`:623`). It is a first-class typed outcome,
not an error string.

**2. The recovery path says, in a comment, that this should NOT fail the run.**
`workflow/atomic_recovery.py:34-39`:

```python
# The durable typed budget denial is the complete outcome for
# this child; re-raise it as the budget signal so the standard
# typed-stop path handles it instead of failing the run.
raise WorkBudgetDenied(selected.terminal)
```

That is the code stating the intended behaviour. It is not what happens.

**3. It escapes, deliberately, and lands in the generic handler.**
`rules/crit.py:471-472` re-raises it past the abandon path:

```python
except WorkBudgetDenied:
    raise
```

**4. Two committed roots show the result — counted here, not quoted.**

| root | durable `budget_denied` work terminals | `error_type` | stop reason | resumable |
|---|---|---|---|---|
| `2026-08-22-change-epoch3-second-lineage/failed-attempt2-run-bb045538…` | **1** (of 57 work terminals) | `WorkBudgetDenied` | `operational_failure` | no |
| `2026-08-24-change-rung7-wounds-falls-succession/run` | **1** (of 40) | `WorkBudgetDenied` | `operational_failure` | no |

Both roots carry the typed denial ON the record and still ended as failures.
Their measured spend (this window's census): **165 466** and **116 319**
tokens — both of which those roots reported as `0` until this window's
Tranche 2, and neither of which can be continued.

**5. Other roots reach the resumable terminal on the same underlying
condition.** The `epoch3` soak root minted in Tranche 1 exhausted its budget
and reached `budget_exhausted`. So the split is not between two kinds of run;
it is between two ways the same condition can surface.

## What this window did NOT do, and why

Tranche 1 stopped a REFUSAL being swallowed. It did not change which terminal
any run reaches, and it deliberately did not decide whether outstanding
authority or a denied reservation SHOULD block continuation. Both are design
questions about what the harness ought to mean by "failed", and the
orchestrator's scope contract parks a design question found mid-defect rather
than answering it inside a defect tranche.

## What the operator's answer decides

**If a denied reservation is NOT an operational failure** (which the evidence
above favours — the denial is typed, durable, and recorded before anything
raises, and the recovery path's own comment says it should reach the typed
stop): `WorkBudgetDenied` gets a typed stop path to `budget_exhausted`, and
runs that hit it become continuable under a fresh budget. Cost: a defect
tranche in `scheduler/` and `workflow/`, which is a different window's cone.

**If it IS an operational failure**: nothing in the code changes, and the fix
is to the SURFACES — the run should say so at the point of denial rather than
arriving at a generic handler, and `results` should name the denial rather
than a bare `operational_failure`.

Either answer is implementable. What cannot be settled from the record is
which one the harness is supposed to mean, because that is a statement about
intent, not about behaviour.
