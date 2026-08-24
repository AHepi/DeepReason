---
name: term-pinning
description: Protocol for assigning candidate finite meanings to uninterpreted terms of a frozen calculus (Warp W1), and for typing the DISPOSITION of every open item - DECIDE, PROPOSE, or ESCALATE. Use for any PIN-* record work. Amended per FR-21.
---

# Term Pinning (Warp W1)

<!-- PROMPT-CORE-BEGIN -->
You are pinning terms for a frozen calculus. Pins are candidate meanings,
never truths; a pin record proves nothing and moves no readiness count
unless it says so explicitly.

1. Take the cluster the frozen catalog order assigns; never pin ahead of
   the declared sequence, never pin a term outside the cluster.
2. METHOD RULE: each pin is the WEAKEST meaning that (i) makes every
   frozen occurrence of the term well-typed and (ii) preserves every
   distinction the calculus states in prose at those occurrences. If two
   candidates tie, take the one committing to less; if none satisfies
   both, record the term OPEN with the obstruction stated.
3. Before drafting, build the occurrence table: every location of the
   term, its polarity there, and the row type. Any term negated in both
   a certificate row and an N-row is steering-sensitive: flag it and
   state how the pin avoids making the certificate row vacuous.
4. After drafting, run the vacuity probe: each certificate row the term
   occurs in stays satisfiable AND falsifiable under the pin; record
   both directions.
5. Declare the bucket of every pin (definition / acceptance axiom /
   import / bridge). A pin requiring an unjustified bridge is not a pin;
   it is a named OPEN item.
6. DISPOSITION TYPING (FR-21): every open item in the record carries
   exactly one disposition -
   DECIDE: yours to answer, and answered here, with the authority named;
   PROPOSE: the owner's; give every live option with its consequence.
     A view of your own is permitted ONLY marked as a view, in its own
     paragraph, separated from the options - "no recommendation" beside
     a recommendation in prose is a defect;
   ESCALATE: two authorities conflict; state both sides and decide
     nothing, including by omission. A decision NOT to do specified
     work is a decision and types as PROPOSE or ESCALATE, never DECIDE.
7. Enumerate the dependency cone without changing any count; every
   count in the record is recomputed by a guard, never remembered
   (mapping-table rule 4).
8. Label equality is never identity; an original term is never
   identified with a fragment predicate.
<!-- PROMPT-CORE-END -->
