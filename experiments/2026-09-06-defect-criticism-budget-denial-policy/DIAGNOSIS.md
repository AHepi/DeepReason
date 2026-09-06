# DIAGNOSIS — one road absorbs the refusal, its sibling does not

The cause was established in the predecessor tranche and parked as P1; this
document states it in its own terms and REPRO.md demonstrates it. No new
record reading was needed: the run that motivated the whole line of work
(`run-c3f3bf10bc57d63e224a9f1c68bf1057`) already showed which road it took —
102 `criticism:` triggers, 0 `foreign-criticism:` triggers in its `log.jsonl`,
with a null `criticism_policy` in its manifest, which is exactly what selects
the direct road.

## The two roads, side by side

`Scheduler._arg_crit` chooses between them on the manifest's
`criticism_policy`:

| | direct batch road | foreign-school road |
|---|---|---|
| selected when | `criticism_policy` is null | it is set |
| dispatch | `crit_argumentative_batch` in a loop over batches | the same, per school |
| catches | `(SchemaRepairError, EndpointError)` | those **plus `WorkBudgetDenied`** |
| a refused batch | leaves the criticism pass, leaves the cycle, leaves the run | records a typed `budget_denied` attempt and a `CoverageDebtV1` whose `termination_reason` is `budget_exhausted`, then carries on |

So the same refusal is a survivable local event on one road and the end of the
run on the other. Nothing about the two roads' epistemology differs here — the
foreign road's answer is simply the one that was written down.

## What the predecessor tranche changed, and what it left

The cycle loop now absorbs a refusal on a SPENT ceiling and ends the run
cleanly as `budget_exhausted`. That made the common case correct. It left the
other case untouched by design: a refusal the ceiling could still have
afforded — one batch whose prompt is too long for the headroom — still leaves
the run and is published `operational_failure`.

REPRO.md's line A is that residue, isolated.

## What the fix must turn on

The same verdict the meter already stamps and the denial already carries:
`budget_exhausted`. When it is True the run must still end cleanly — that is
the operator's law of 2026-08-29 and the predecessor's whole result. When it
is False, this tranche decides what happens instead, and the operator's
instruction says the decision is configuration.

## What this is NOT

- Not a defect in `rules/crit.py`. Its re-raise is deliberate and load-bearing:
  the refusal arrives with its durable terminal already written, and a second
  transition after termination fails the run (live regression `run-e542c3c1`,
  `DR-SEAM-rules-x-workflow` Traps). The rule must keep re-raising; the CALLER
  is what decides.
- Not a defect in the cycle loop. It is doing what the predecessor tranche
  asked of it.
