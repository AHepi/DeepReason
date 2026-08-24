---
name: model-zoo-discipline
description: Protocol for building and maintaining the finite-structure model zoo and running bounded expansion search (Warp W2). Use when constructing candidate countermodels, verifying member certificates, adding separation witnesses, or attempting a total expansion for an acceptance gate such as DSF-A1.
---

# Model Zoo Discipline (Warp W2)

<!-- PROMPT-CORE-BEGIN -->
You are building or checking finite structures for a frozen theory whose
axiom rows have executable evaluators (the twin).

1. A structure enters the zoo only with a member certificate: member id,
   sorts and bounds, twin verdict for EVERY axiom row, distinctions it
   witnesses, construction provenance, content hashes. No certificate,
   no member.
2. Soundness side: on any zoo change, re-run the twin over every member;
   a member failing any axiom row is quarantined, never silently edited.
3. Tightness side: every distinction the calculus asserts in prose needs
   a separation witness pair - two members alike except for that
   distinction. Record which distinctions still lack witnesses.
4. Expansion search: to discharge a non-entailment, search for a TOTAL
   expansion satisfying every axiom row while falsifying the target row,
   within DECLARED bounds. Encode rows as constraints and let the finite
   search run; do not hand-assemble a 70-component structure from memory.
5. Bounds are part of the result. "No expansion within bounds B" is a
   typed negative; NEVER report it as "no expansion exists". "Expansion
   found" ships the structure, its certificate, and an independent replay
   command.
6. A partial fragment structure is never a model of the whole theory by
   fiat; only an accepted total expansion counts, per the acceptance
   gate.
7. Class looseness is specified, not accidental: when you rely on
   perturbing a member, cite the frozen variation criterion that keeps
   the perturbation in-class, or file the criterion first.
<!-- PROMPT-CORE-END -->
