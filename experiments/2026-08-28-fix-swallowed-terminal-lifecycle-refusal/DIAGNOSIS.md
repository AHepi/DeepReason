# DIAGNOSIS — one bare `except ValueError` erases a correct refusal

Derived from the typed record BEFORE code reading, per the orchestrator's
scope contract clause 2. Code line numbers are cited only after the record
established the fact.

## What the record says (evidence, not prose)

Fresh offline root, `scripts/cycle_soak.py --case epoch3 --cycles 3`
(reproduced in this window; `proof/q4_before.json`,
`proof/soak-report-epoch3-c3.json`):

| fact | source | value |
|---|---|---|
| `state` | `run-status.json` | `completed` |
| `stop_reason` | `run-status.json`, `run-stop.json` | `budget_exhausted` |
| `verify_root` verdict | `REPLAY_VALIDATION.json` (stored) | valid, 0 violations |
| terminal commitment | replayed `workflow_state` | present |
| terminal lifecycle decision | replayed `workflow_state` | **absent** |
| lifecycle decisions, any kind | replayed `workflow_state` | **0** |
| outstanding work orders at stop | replayed `workflow_state` | **11** |

Both surfaces, run against that same root (`proof/before_results.txt`,
`proof/before_continue.txt`):

```
$ deepreason results <root>
  stands at a valid typed terminal: yes (terminal epoch 0)
  stop reason is resumable: yes
  ready for `deepreason amend` / `deepreason continue`: yes

$ deepreason --root <root> continue --budget cycles=2 --token-budget 50000
  CONTINUE_TYPED_STOP_REQUIRED
```

This is the audit's finding reproduced on a root minted on today's `main`,
not read off a committed one — so it is a live defect, not history.

## The primary cause, named

`workflow/lifecycle.py:216` refuses CORRECTLY:

```python
if snapshot.outstanding_work or snapshot.unconsumed_bound_call_seqs:
    raise ValueError("STOPPED refuses unfinished workflow authority")
```

11 outstanding work orders at stop. The refusal is right and this tranche
does not touch it.

`application/text_runs.py:245-246` then erases it:

```python
except ValueError:
    return None
```

`return None` falls through to `write_stop_record`, which writes a bare
`run-stop.json` with `reason="budget_exhausted"` and NO lifecycle decision.
Nothing anywhere records that a transition was rejected.

## Why the two surfaces then disagree — two independent predicates

| surface | predicate it evaluates | on this root |
|---|---|---|
| `results` | `application/results.py:431-438` — `stop["reason"] in RESUMABLE_STOP_REASONS` AND a valid replay terminal binding | **True** |
| `continue` | `runtime/continuation.py:218-364` — `workflow_state.terminal_lifecycle_decision is not None` OR `current_resume_decision is not None` | **False** |

Neither consults the other, and the fact that separates them — that the
STOPPED transition was refused — is written nowhere. `results` is not
lying about anything it can see; it cannot see the refusal, because the
refusal left no trace.

## Two supporting observations

1. **The writer's own docstring already states the intended contract and the
   reader does not honour it.** `text_runs.py:193-196`: *"Returns `None`
   when this root cannot carry the receipt (no owned control plane, or the
   workflow holds unfinished authority) — the caller then keeps the bare
   stop record and **the terminal stays non-resumable, exactly as before**."*
   The terminal IS non-resumable. `results` says it is resumable. The
   docstring is the specification the reader violates.

2. **The `except` cannot tell a refusal from a bug.**
   `build_stopped_lifecycle` raises `ValueError` in six distinct places
   (`only a deterministic terminal decision may emit STOPPED`, `exhaustion
   STOPPED requires unchanged controller state`, `lifecycle stop differs
   from deterministic StopController`, `lifecycle controller state does not
   replay exactly`, `lifecycle decision differs from its run-stop record`,
   and this one), and `outstanding_work_snapshot` raises a seventh
   (`outstanding work belongs to another manifest`). All seven land in one
   bare handler that answers every one of them with silence.

## The categorical statement

This is a WORKAROUND OF A TYPED REFUSAL, which CLAUDE.md forbids by name
("Never work around a REFUSED_* or typed stop"). The defect is not that the
lifecycle refuses; it is that the refusal is answered with `return None`
and no record.

## Not the cause (hypotheses closed)

- **A regression in the writer between 2026-08-25 and today.** WITHDRAWN by
  P6 itself and re-confirmed here: `build_stopped_lifecycle` is behaving to
  its own contract on both roots. The control root (P-R1) simply had zero
  outstanding work.
- **A reader bug in `results.py` alone.** Insufficient: correcting only the
  reader would leave the refusal unrecorded, so no operator could learn WHY.
- **Cross-family configuration / cycle- vs token-bound stopping.** Both
  WITHDRAWN by P6 against the P-R1 control; the offline `epoch3` case here
  is SOLO and reproduces regardless.
