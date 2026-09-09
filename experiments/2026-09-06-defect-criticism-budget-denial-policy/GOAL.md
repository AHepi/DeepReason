# GOAL — one refused criticism batch must not end the run, and the choice must be configuration

Tranche opened 2026-09-06, immediately after
`experiments/2026-09-06-defect-budget-exhausted-classification/`, which parked
this as P1.

## The operator's instruction, verbatim

> "ok do P1. And ensure config is plugged in so that it can affect token
> allocation during a run."

Two obligations, and the second is not decoration. R1 is P1 as parked. R2 says
the answer must be reachable as CONFIGURATION and must be LIVE — a knob whose
setting changes what the run does with its remaining tokens, not a field that
is recorded and ignored. That is the modularity law of 2026-08-26 ("every
behavior a run can vary is reachable as configuration or a registered,
versioned artifact — never by editing code", stated as a PRIORITY) and the
ungated-seats law of 2026-08-28 ("maximum configurable surface").

## Map preflight

| id | why |
|---|---|
| `DR-SEAM-scheduler-x-workflow` | read FIRST: how the cycle loop absorbs a typed workflow denial; carries the Traps entry this tranche's predecessor wrote |
| `DR-SEAM-rules-x-workflow` | the criticism rule's own denial handling — it re-raises deliberately, and that must not change |
| `DR-SUB-scheduler` | owns `_arg_crit`, the road that drops the batch |
| `DR-SUB-llm` | owns the meter whose verdict decides exhausted from not-exhausted |
| `DR-SUB-manifest` | owns `run_manifest.py`, where a new `Config` field's versioned-source line must go |
| `DR-INV-frozen-surfaces` | frozen surface 4 and the documented `Config` recipe |

**Frozen-surface reading.** A new `Config` field is the documented home for a
per-run mode (`INV-frozen-surfaces.md`, "Where authority is allowed to live
instead"), and that recipe is not finished without its
`data.pop(...)` line in `run_manifest.py::_versioned_source_config_data` —
which is a CONTACT with frozen surface 4. The operator's instruction to plug
config in is the authority for the field; the pop is the recipe's obligatory
second half, not a separate choice, and this tranche proves it moved no
digest rather than asserting it.

## The defect (R1)

`scheduler.py::_arg_crit`'s direct batch road — the one a run with no
criticism policy takes — catches only `(SchemaRepairError, EndpointError)`
around `crit_argumentative_batch`. Its sibling `_foreign_arg_crit` also
catches `WorkBudgetDenied` and records a typed coverage outcome. So one
criticism batch the token budget refuses ends the whole run, even when the
budget could still afford other work.

## Success criterion (falsifiable)

Committed, mutation-proven regression tests prove all four:

1. **R1 — a refusal the ceiling could still afford does not end the run.** The
   cycle continues, and the record says what went uncriticised through the
   existing `criticism.dispatch.v1` declaration, so no reader can mistake
   "nobody attacked it" for "the critics looked and found nothing".
2. **A refusal on a SPENT ceiling still ends the run cleanly** as
   `budget_exhausted` — the predecessor tranche's guarantee, unmoved.
3. **R2 — the knob is configuration and it is LIVE.** The behaviour is chosen
   by a `Config` field, every value is reachable, and two settings of that one
   field produce DIFFERENT measured token spend on the same scenario. A branch
   test alone does not satisfy this; the proof is a number from the meter.
4. **R2 — the knob costs no digest.** No qualification subject digest and no
   manifest golden moves, measured before and after.

Full gate at the boundary with no NEW failure against the recorded
`origin/main` baseline (3 pre-existing organiser failures, parked as P2 of the
predecessor tranche). `docs_verify` no worse than its 8 pre-existing failures.
Map moves in the same commit, with a `Traps` entry.

## Out of scope (park, do not fix)

- The same missing arm on the conjecture, bridge, scratch-authoring and
  referee roads. P1 named criticism; each other road has its own correct
  answer and its own record obligation.
- The organiser failures (predecessor's P2).
- Any change to what a SPENT ceiling does.
