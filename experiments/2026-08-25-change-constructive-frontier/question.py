#!/usr/bin/env python3
"""The P-C1 question, in one place, importing nothing.

SPEC.md S7/S8, REQUEST.md R18, R21.

WHY THIS FILE EXISTS.  Both arms must ask the model EXACTLY the same thing,
or the experiment measures the prompt instead of the machinery.  ARM H gets
this string through `build_manifest_pc1.py`, where one byte of drift mints a
different run id; ARM S gets it through `arm_s.py`, which may not import
anything from `deepreason` (R21: "no harness machinery").  A shared module
with no imports at all is the only way both can read the same bytes without
one of them keeping a copy -- and two copies of a prompt are two prompts.

The first sentence is R18's registered template with N and <objects>
instantiated.  Everything after it states the scoring rule and the wire
format (SPEC.md S2), without which R15 is not mechanisable: a candidate
nobody can parse cannot have its claim checked by program.
"""

QUESTION = (
    "Construct a configuration of 13 points in the unit square achieving "
    "the largest minimum triangle area you can; every candidate must state "
    "its coordinates and claimed score, and survives only if the checker "
    "confirms it. Score = the smallest area among all 286 triangles formed "
    "by triples of your 13 points; every point must lie in [0,1]x[0,1] and "
    "all 13 points must be distinct. State the construction in exactly this "
    "form, one point per line: a line \"POINT x y\" for each of the 13 "
    "points, with x and y written as decimals with at most 6 decimal "
    "places, then a final line \"CLAIM v\" giving your claimed minimum "
    "triangle area as a decimal. A claim the checker cannot confirm is "
    "refuted."
)
