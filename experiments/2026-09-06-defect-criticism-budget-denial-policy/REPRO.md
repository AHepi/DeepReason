# REPRO — one refused batch, two questions

`proof/repro.py`, against the code at `f8d97c4a1`-and-after. Output at
`proof/repro_before.txt`:

```
A. refusal with budget REMAINING, default config:   run ended: WorkBudgetDenied (1 batch call(s))
B. refusal on a SPENT ceiling, default config:      run ended: WorkBudgetDenied (1 batch call(s))
C. Config carries a criticism budget-denial knob:   False
```

## What each line demonstrates

The scheduler is built offline — a mock conjecturer and a mock critic, no
provider — over four admitted targets, and `crit_argumentative_batch` is
replaced by a function that refuses. Nothing but `_arg_crit`'s own exception
arms decides what happens next.

**A is P1.** A refusal the ceiling could still have afforded ends the run.
One batch of four targets was refused and nothing else was tried.

**B is the boundary the fix must not cross.** A refusal on a spent ceiling
leaves `_arg_crit` too — and it must keep doing so, because the cycle loop
above it is what turns that into the clean `budget_exhausted` terminal the
operator's law requires. B and A look identical here and must not look
identical after the fix.

**C is R2.** There is no configuration for any of this today. The behaviour is
whatever the exception arm was written to do, which is precisely what the
modularity law forbids.

## Faithfulness

The road under test is the one the motivating run took: a null
`criticism_policy` selects the direct batch road, and the reproduction drives
`_arg_crit` directly rather than a stand-in for it.

It does NOT reproduce the token arithmetic — the refusal is injected rather
than earned from a real meter. That is deliberate: what the meter does with
its numbers was settled and measured in the predecessor tranche, and repeating
it here would test that work rather than this one. What this tranche must
still measure with real numbers is R2's claim that the knob changes SPEND, and
VERIFY.md holds that to a figure from the meter.
