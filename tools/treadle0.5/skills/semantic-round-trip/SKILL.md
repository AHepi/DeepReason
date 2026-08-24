---
name: semantic-round-trip
description: Blind back-translation audit of a formal pin (Reed 6). Amended per FR-15 (packet sizing) and the source cycle's packet-scope lesson - a review's narrow green must state what was NOT in its packet.
---

# Semantic Round-Trip (Reed 6)

<!-- PROMPT-CORE-BEGIN -->
Two roles, strictly separated; you are exactly one of them.

BACK-TRANSLATOR: you receive ONLY the formal pin text (clause plus
battery verdicts), never the source prose, intent notes, or record
narrative. Render, in plain language: (1) what the pin admits, (2) what
it excludes, (3) your classification of each battery instance as you
read the clause - your reading, not the recorded verdicts. Translate
what is written; never guess intent.

COMPARATOR: you receive the back-translation and the intended meaning.
Produce a divergence list; each item names what the back-translation
says, what the intent says, and the stage charged - CLAUSE, PROSE, or
BATTERY. No divergences: record ROUNDTRIP_CLEAN with the
back-translator's identity and date.

Rules for both:
1. The back-translator's independence is the instrument; any leakage of
   intent voids the audit - ROUNDTRIP_VOID, rerun fresh. An author
   back-translating their own pin is VOID by construction.
2. Divergences are findings; a BATTERY-staged divergence obligates a
   new minimal pair before the clause may be edited.
3. A clean round-trip is agreement between two readings, never proof of
   correctness; it upgrades nothing by itself.
4. PACKET RULES (FR-15): packets are assembled from named file slices
   through the review harness, sized under its ceiling. A reviewer
   returning empty at its length limit got too much input - shrink the
   packet (extract the claims); never raise the output budget.
5. PACKET-SCOPED GREENS: every verdict states what was NOT in the
   packet. A CONFORMS from a reviewer who saw two files is worth those
   two files; a MISSING on a claim that needs execution routes to
   run-the-code verification (FR-25), never to a bigger packet.
<!-- PROMPT-CORE-END -->
