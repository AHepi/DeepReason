# REPRO — the cause, offline, in twelve lines of behaviour

`proof/repro.py`, run against the code as committed at `2d2cdc5bb`. Output
captured verbatim at `proof/repro_before.txt`:

```
A. TokenBudgetExceeded absorbed by the cycle loop: (True, None)
B. WorkBudgetDenied  absorbed by the cycle loop: (False, 'WorkBudgetDenied')
C. spent-ceiling denial carries budget_exhausted: ABSENT
C. oversized-request denial carries budget_exhausted: ABSENT
```

## What each line demonstrates

**A and B are the cause.** The same event — a dispatch refused by the token
meter — is absorbed by `Scheduler.run` when it arrives as
`TokenBudgetExceeded` and escapes the whole run when it arrives as
`WorkBudgetDenied`. The scheduler is built offline (a mock conjecturer, no
provider); `step` is replaced by a function that raises, so nothing but the
loop's own exception arms decides the outcome. B is the observed root's
terminal in miniature: the denial leaves the scheduler, and everything above
it can only call that a breakage.

**C is why the fix cannot simply widen the arm.** Two denials are built from
the meter's own arithmetic:

| denial | ceiling | already spent | request | remaining |
|---|---|---|---|---|
| spent ceiling (the observed root's numbers) | 500 000 | 495 362 | 3 000 chars + 8 192 cap | 4 638 |
| oversized request | 500 000 | 0 | 3 000 000 chars + 8 192 cap | 500 000 |

Both raise. Neither carries anything a caller can read to tell them apart, so
today the only two available answers are "treat every denial as the ceiling"
(which would make the second a clean stop, and the goal forbids that) or
"treat none of them as the ceiling" (today's behaviour, which the operator's
law forbids). The separating quantity exists inside `TokenMeter.reserve` and
is thrown away at the `raise`.

## Faithfulness to the observed root

The reproduction uses the root's own numbers — ceiling 500 000, spend
495 362, seat completion cap 8 192 (`run-manifest.json` `roles`, every seat) —
so the first denial in C is the arithmetic of the denial at `log.jsonl`
seq 1165, and the remaining headroom it reports (4 638) is the headroom that
run had left.

It does NOT reproduce the criticism road that carried the denial
(`_arg_crit`'s direct batch dispatch, selected by the run's null
`criticism_policy`). That road is upstream of the cause and needs a provider;
what it contributes — that `WorkBudgetDenied` reaches `Scheduler.run`
unabsorbed — is what B demonstrates directly.

## Residue

The reproduction does not show what the terminal LOOKS like once the loop
absorbs the denial. That is the fix's own claim, and VERIFY.md proves it on
the published record of a run driven through the real `deepreason run` path.
