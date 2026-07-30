# Parked — out of this tranche's goal

## D2a — a capability transition cannot say why it denied a program

Parked by explicit operator instruction ("Park D2a").

`CapabilityTransitionV1` has no detail field, so the validator's message
("sandboxed Python must define exactly one simulate function") is
discarded and the record carries only `reason_code=invalid_model_program`.
An operator reading the record cannot tell which of the validator's ten
distinct rejection paths fired. Adding the field means changing a
capability-state record — `capabilities/state.py` digests and event
application are named frozen in CLAUDE.md — so it needs its own tranche
and its own approval.

Not urgent after D2b: once the contract is disclosed, the common cause of
`invalid_model_program` (the model never knew the rule) is gone, so the
missing detail is diagnostic debt rather than an active blocker.

## D1a — the wire contract still describes the old, stricter quote rule

Carried forward from `2026-07-30-fix-citation-quote-check/PARKED.md`,
where it was parked "for the D2 tranche, which is about what the pack
tells the model and will have to pay this cost once for both changes
rather than twice."

That reasoning was sound and it is NOT being followed, deliberately. The
operator's approval reads "approved for D2b only" and enumerates exactly
two disclosures — the `simulate(inputs, rng)` contract and the
`requested_observables` rule. `EvidenceRefClaimV1`'s quote docstring is
neither. Folding it in would widen the approved pack surface on my own
authority, which is the failure the frozen-surface stop exists to
prevent; the fact that it would be cheap now is an argument for asking,
not for assuming.

The cost of not folding it in, stated so the operator can price it: the
same two baselines will have to be regenerated a second time when D1a is
approved. Nothing else is lost — the text is stricter than the harness
enforces, so a model that obeys it verifies.

## P4 — TOKEN_ACCOUNTING.json counts research records as simulation records

Operator instruction: investigate further, do not fix. Full entry in
`experiments/2026-07-30-change-amendment-epochs/PARKED.md`.

## Q1 — an unquoted citation is recorded as "byte-verified"

Checked in the previous tranche and found INTENDED at the contract level;
the residue is that the ledger event carries only the code, not the
`quoted` flag, so FINDINGS.md overstates what was compared. Full entry in
`experiments/2026-07-30-fix-citation-quote-check/PARKED.md`.
