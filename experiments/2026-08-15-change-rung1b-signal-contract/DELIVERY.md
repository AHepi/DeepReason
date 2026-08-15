# DELIVERY — Rung 1b-i: the signal contract, declaration side

Verdict: **DELIVERED.** VALIDATION.md PASS.

| # | Requirement | Delivered |
|---|---|---|
| L1 | the registry is a contract: name, unit, producer-agnostic semantics, staleness | YES — `SignalDeclaration`, closed `Unit`/`Staleness` vocabularies |
| L2 | the existing registry is included, not superseded | YES — all 89 entries migrated, prose carried verbatim as `semantics`; `SIGNALS`/`PREFIXES` derived, content-identical |
| L3 | interface-only consumption, pinned by an architecture test | YES — passes today; exists to fail when breached |
| L4 | INV document + two REC recipes | YES — `DR-INV-signal-contract`, `DR-REC-add-signal`, `DR-REC-revise-allocation-policy` |
| L5 | no skill or workflow | YES — the operator's two-failures tripwire respected |
| L6 | map moves with the code | YES — one commit |
| L7 | old roots replay unchanged | **RETIRED** by the 2026-08-14 law, mid-tranche |

## The one design decision worth stating

`unit` and `staleness` are `"unspecified"` for all 89 migrated entries, and no
value was invented for any of them. Inventing a unit for a signal whose author
never stated one would be fabrication dressed as rigour, and it would have made
the contract look complete while carrying 89 guesses. Instead the debt is
counted, pinned, and allowed only to shrink — and a NEW signal may not use the
marker at all, which is exactly what the operator's clause (1) asks for: the
contract binds new setups.

## Findings

1. **Clause (3)'s boundary already held.** `controller.py` imports only
   `deepreason.ontology`. The architecture test is therefore not a fix; it is a
   tripwire, and the INV document says so rather than claiming credit.
2. **Two of the three layers were already implemented in substance** —
   `cap_envelope`/`clamp` are the FREE layer, `_policy_payload` already reads
   policy from a registered artifact. What was missing was the layering as a
   stated, checkable protocol.
3. **The diff-budget ceiling was exceeded for the second consecutive rung**, both
   times because required map documentation outran a ceiling set on
   production-code intuition. Production was 101 lines against a 450–650 estimate
   for all six clauses. The correction belongs to the estimator, not the work,
   and is recorded in SPEC.md Amendment 1.

## Not delivered here — Rung 1b-ii

SC-2 (seat-instance keying), SC-4 (compiled topology matrix), SC-5 (the typed
`allocation open-loop for signal X` notice), and the migration of the
controller's three direct `harness.state.status.get(...)` reads into declared
signals. Rung 1b is complete only when 1b-ii lands; see PARKED.md.
