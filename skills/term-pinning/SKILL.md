---
name: term-pinning
description: Protocol for assigning candidate finite meanings to uninterpreted original-side terms of a frozen calculus (Warp W1). Use for any PIN-* record work - selecting a cluster, drafting weakest-meaning pins, polarity and vacuity checking, and recording OPEN remainders. Enforces the least-commitment method rule with machine-assisted side conditions.
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
   term, its polarity there (positive / negated / mixed), and the row
   type (certificate, N-row, control). Any term negated in both a
   certificate row and an N-row is steering-sensitive: flag it, and state
   in the record how the pin avoids making the certificate row vacuously
   easy or impossible.
4. After drafting, run the vacuity probe: for each certificate row the
   term occurs in, confirm the row is still satisfiable and still
   falsifiable under the pin. Record both directions.
5. Declare the bucket of every pin (definition / acceptance axiom /
   import / bridge). A pin requiring an unjustified source-level bridge
   is not a pin; it is a named OPEN item.
6. Enumerate the dependency cone (which rows, records, and future
   discharges the pin touches) without changing any count.
7. Label equality is never identity; an original term is never identified
   with a fragment predicate.
<!-- PROMPT-CORE-END -->
