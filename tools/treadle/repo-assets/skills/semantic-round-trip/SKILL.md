---
name: semantic-round-trip
description: Blind back-translation audit of a formal pin or definition (Reed step 6) - a fresh agent with no access to the source prose renders the formal text in plain language; divergence from intent is a mapping defect localized by stage. Use before sealing any pin record and when auditing existing pins.
---

# Semantic Round-Trip (Reed 6)

<!-- PROMPT-CORE-BEGIN -->
Two roles, strictly separated; you are exactly one of them.

BACK-TRANSLATOR: you receive ONLY the formal pin text (clause plus
battery verdicts), never the source prose, intent notes, or record
narrative. Render, in plain language: (1) what the pin admits, (2) what
it excludes, (3) the classification of each battery instance as you read
the clause - your reading, not the recorded verdicts. Do not guess
intent; translate what is written.

COMPARATOR: you receive the back-translation and the intended meaning
(source prose, intent notes). Produce a divergence list: each item names
what the back-translation says, what the intent says, and the stage
charged - CLAUSE (formal text fails to say the intent), PROSE (intent
was never stated precisely), or BATTERY (instances underdetermine the
difference). No divergences means record ROUNDTRIP_CLEAN with the
back-translator's identity and date.

Rules for both:
1. The back-translator's independence is the instrument; any leakage of
   intent voids the audit - record ROUNDTRIP_VOID and rerun fresh.
2. Divergences are findings, filed like review findings; a BATTERY-
   staged divergence obligates a new minimal pair before the clause may
   be edited.
3. A clean round-trip is evidence of agreement between two readings,
   never proof of correctness; it upgrades nothing by itself.
<!-- PROMPT-CORE-END -->
