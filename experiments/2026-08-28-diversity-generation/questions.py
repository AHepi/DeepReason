#!/usr/bin/env python3
"""The three frozen question strings, in one place, importing nothing.

PREREG.md §3 is the authority for WHY each string reads as it does --
including the two registered exclusions (Q1's attachment-grounding sentence,
Q2's checker wire-format contract), both registered before any provider call.

A shared module with no imports is the only way the driver and the analyser
can read the same bytes without one of them keeping a copy, and two copies
of a prompt are two prompts.
"""

# Q1 -- the P-T1 seed question, from experiments/2026-08-27-change-technique-run/
# PREREG.md §1 on branch claude/spec-to-code-technique-k5209o (read-only).
# The second sentence ("Ground every claim in the attached record ...") is
# excluded: this experiment attaches no record.  PREREG §3/Q1.
TECHNIQUE = (
    "What is the best technique for turning an abstract specification into "
    "executable code — such that the result actually holds its "
    "commitments?"
)

# Q2 -- the P-C1/P-C2 construction subject, from
# experiments/2026-08-25-change-constructive-frontier/question.py.  The
# checker wire-format tail is excluded because it is an output contract
# incompatible with all four arms' output contracts, which would make M3 a
# measurement of format collision.  PREREG §3/Q2.
GEOMETRY = (
    "Construct a configuration of 13 points in the unit square achieving "
    "the largest minimum triangle area you can; the score is the smallest "
    "area among all 286 triangles formed by triples of your 13 points, "
    "every point must lie in [0,1]x[0,1] and all 13 points must be "
    "distinct."
)

# Q3 -- written in PREREG.md §3, not taken from the record.
DECAY = (
    "Why do long-running software systems become harder to change over "
    "time, even when every individual change was reviewed, tested, and "
    "locally correct?"
)

QUESTIONS = {"technique": TECHNIQUE, "geometry": GEOMETRY, "decay": DECAY}
