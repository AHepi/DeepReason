<!-- DR-REC-add-signal -->
Verified-at: f39ff839
Verify: python -m pytest tests/test_signal_contract.py -q
Owns: 
Seams: 
Seams-undocumented: 

# Recipe — add a signal

A new setup adds a signal by DECLARING it. It never teaches a consumer about a
subsystem. If you find yourself editing a consumer to understand where a number
came from, stop: that is the wiring the contract replaced
(`DR-INV-signal-contract`).

## The steps

1. **Name it for what it means, not for who emits it.** `criticism.coverage-debt.v1`
   is a fact about the graph; `scheduler-emitted-debt` is a fact about a caller.
2. **Add one `SignalDeclaration`** to `SIGNAL_DECLARATIONS` (exact name) or
   `PREFIX_DECLARATIONS` (a family sharing a prefix) in
   `src/deepreason/signals.py`:
   - `unit` — from the closed vocabulary. If none fits, the vocabulary is what
     needs the change, in its own step, with a reason.
   - `semantics` — producer-agnostic: what one occurrence MEANS, and what a
     consumer may conclude from it. Say what it is NOT evidence of.
   - `staleness` — how long an observation stays usable. This is the field
     consumers get wrong; a signal with no bound invites a stale read.
   - **`unspecified` is not available to you.** It marks the pre-contract
     migration only, and the census test fails if the count rises.
3. **Emit it** through the existing `record_measure` path. The AST scan in
   `tests/test_signals.py` fails on an emitted tag that is not declared — that
   check predates the contract and still does its job.
4. **Run** `python -m pytest tests/test_signal_contract.py tests/test_signals.py -q`.

`check: grep -q "SIGNAL_DECLARATIONS" src/deepreason/signals.py && grep -q "PREFIX_DECLARATIONS" src/deepreason/signals.py`

## Paying down the debt

To give a migrated signal a real unit and staleness: replace its `unspecified`
values in place, lower `MIGRATION_DEBT` in `tests/test_signal_contract.py` by
the number you fixed, and say in the commit message what evidence fixed it. The
census only falls, so a wrong guess is visible and reversible; a guess dressed
as a measurement is neither.

## What this recipe may NOT do

- It may not add a branch to a consumer. Allocation reads the interface only.
- It may not let a signal reach a label. Allocation touches efficiency, never
  evidence (`DR-INV-signal-contract`, FROZEN layer).
- It may not widen the unit or staleness vocabulary silently — that is a
  VERSIONED-layer change with its own recorded decision.

## If this recipe fails you

Record the failure in your tranche's PARKED.md, naming this file. **Two**
recorded failures is the tripwire for building a dedicated workflow; one is a
recipe that needs a better sentence.
