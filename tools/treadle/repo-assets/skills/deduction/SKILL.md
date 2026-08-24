---
name: deduction
description: Propose machine-checkable derivations in a frozen rule system (treadle deduction stage). Use for proof-search tasks where the target is a theory row and acceptance replays every step with derivation_check.py. One rule application per step, everything cited, honest grades, CANNOT_DERIVE as a first-class outcome.
---

# Deduction (proof search under replay)

<!-- PROMPT-CORE-BEGIN -->
You propose derivations; a deterministic checker replays them. Your
proposal has no authority until every step replays.

1. Output exactly one derivation file conforming byte-exactly to the
   READ-ONLY REFERENCE grammar (zoo/derivations/FORMAT.md) and using
   ONLY rule ids from the READ-ONLY REFERENCE rules profile. If either
   reference is absent from your context, report BLOCKED.
2. One rule application per step. No gaps, no "clearly", no combined
   steps. Every premise cited by step id; PREMISE leaves cite theory
   row ids and state no formula.
3. Formulas are written in the theory's s-expression condition language,
   byte-exactly -- the conclusion must equal the target row's condition
   as bytes, not as a paraphrase.
4. Grades are honest: a step never claims more authority than the
   propagation rule allows from its premises.
5. When the checker fails you, the error is STEP-ADDRESSED. Repair the
   addressed step; do not reshuffle the whole proof to route around a
   misunderstanding you have not diagnosed.
6. If you cannot complete a derivation within your budget, emit
   BLOCKED.md containing CANNOT_DERIVE, the closest partial derivation,
   and which gap defeated you. NEVER pad a pseudo-proof to look
   complete, and NEVER claim non-derivability -- your failure to find a
   route is evidence about you, not about the calculus; non-entailment
   claims belong to countermodel search.
<!-- PROMPT-CORE-END -->
