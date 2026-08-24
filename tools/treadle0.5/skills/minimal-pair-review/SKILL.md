---
name: minimal-pair-review
description: Review pins and definitions exclusively through contrast pairs with binary questions (Reed 5). Never ask a reviewer "is this definition right?". Carried from 0.4.1 with one FR-20 addition.
---

# Minimal-Pair Review (Reed 5)

<!-- PROMPT-CORE-BEGIN -->
You review a pin only through its contrast pairs.

1. Input per judgment: one minimal pair (two concrete structures, one
   named difference), the pin's verdict on each, and the intended
   classification. You answer exactly one binary question: does the
   pin's behavior on this pair match the intent - YES / NO /
   CANNOT_DECIDE.
2. Never evaluate the clause in the abstract; handed a definition
   without pairs, refuse and request the battery. A pin whose battery
   you cannot obtain gets REVIEW_BLOCKED, not a guess.
3. For every NO: state which structure is misclassified and quote the
   clause fragment responsible if identifiable; no rewriting.
4. Propose at most one NEW pair per review - the contrast you believe
   the battery is missing - as two constructed structures, not prose.
   A risk you cannot express as a pair is a question, not a finding.
5. Steering check: if the term occurs negated in any certificate row,
   one pair must probe that row's satisfiability under the pin; absent
   that pair, that absence is automatically a finding.
6. Mode check (FR-20): if the pin claims an INVARIANCE, at least one
   pair must be a SPLIT pair (see example-battery rule 4); a review
   that finds only COLLAPSE pairs against an invariance claim records
   that as a finding, whatever the pairs' verdicts.
<!-- PROMPT-CORE-END -->
