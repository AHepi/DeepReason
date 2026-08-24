---
name: example-battery
description: Concrete example battery before any clause about a term's meaning (Reed 1) - positives, distinct near-misses, boundaries - with refutation modes (COLLAPSE/SPLIT) for invariances and a separability statement for option decisions (FR-20).
---

# Example Battery (Reed 1)

<!-- PROMPT-CORE-BEGIN -->
Before any clause about a term's meaning is written, build its battery.

1. Construct, as small concrete structures in the fragment language:
   >=3 POSITIVE instances the intended meaning must admit; >=3
   NEAR-MISS negatives, each a minimal pair with a positive - identical
   except in one named respect; >=1 BOUNDARY case genuinely undecided,
   recorded OPEN with the question stated.
2. Structures are explicit and tiny: name the sorts, list the elements,
   give every relation extensionally. No instance lives only in prose.
3. Near-misses are pairwise DISTINCT in the clause that admits them: a
   battery's discriminating power is the count of distinct negative
   SHAPES, not of N labels. Corollary (FR-20): one fixture per
   structurally distinct CAUSE - a property tested only along the axis
   where it cannot fail is untested (the source cycle's cycle collapser
   saw only positive cycles; negation cycles escaped it).
4. REFUTATION MODES (FR-20): declare, per pair, which failure it
   detects - COLLAPSE (the rejected reading gives both members the same
   status where the intent separates them) or SPLIT (it separates
   members the intent holds equal). An INVARIANCE can only be refuted
   by SPLIT; a battery with no SPLIT pair cannot test one, and must say
   so rather than appear to.
5. SEPARABILITY STATEMENT (FR-20): when the battery serves a decision
   among named options, end the battery (before the registry) with a
   section stating, per option pair, which instance separates them - or
   declaring the pair observationally inseparable. See FORMAT.md rule 5.
6. Juxtapose positives beside their near-miss partners, one line naming
   the single difference. Acceptance is the digest checker:
   battery_digest.py --write && --verify.
<!-- PROMPT-CORE-END -->
