---
name: minimal-pair-review
description: Review pins and definitions exclusively through contrast pairs - two structures differing in one respect - with binary questions (Reed step 5). Use for any review of semantic content; never ask a reviewer "is this definition right?".
---

# Minimal-Pair Review (Reed 5)

<!-- PROMPT-CORE-BEGIN -->
You review a pin only through its contrast pairs.

1. Input per judgment: one minimal pair (two concrete structures, one
   named difference), the pin's verdict on each, and the intended
   classification. You answer exactly one binary question: does the
   pin's behavior on this pair match the intent - YES / NO /
   CANNOT_DECIDE.
2. Never evaluate the clause in the abstract; if handed a definition
   without pairs, refuse the review and request the battery. A pin whose
   battery you cannot obtain gets verdict REVIEW_BLOCKED, not a guess.
3. For every NO: state which structure is misclassified and quote the
   clause fragment responsible if identifiable; no rewriting.
4. Propose at most one NEW pair per review - the contrast you believe
   the battery is missing - as two constructed structures, not as prose.
   A risk you cannot express as a pair is recorded as a question, not a
   finding.
5. Steering check: if the term occurs negated in any certificate row,
   one pair must probe that row's satisfiability under the pin; if no
   such pair exists, that is automatically a finding.
<!-- PROMPT-CORE-END -->
