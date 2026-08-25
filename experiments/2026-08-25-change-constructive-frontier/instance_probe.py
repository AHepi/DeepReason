#!/usr/bin/env python3
"""The measurement behind SPEC.md S1's instance choice (REQUEST.md R9, R10).

R10 gives two selection criteria -- simplest checker, unsettled search space
-- and a third consideration follows from R1 (the problem must force
imagination).  None of the three is decided by preference here: this script
produces the numbers SPEC.md S1 quotes, and re-running it reproduces them
exactly, because every random draw is seeded.

It is a PROBE, not an instrument: it never runs during the experiment and
nothing in P-C1 imports it.  Its only job is to make the instance choice
re-derivable by someone who does not trust the prose.

Usage:  python instance_probe.py
"""
from __future__ import annotations

import itertools
import math
import random

N_BAND = (13, 14, 15, 16)
SAMPLES = 2000


def heilbronn(points) -> float:
    """Minimum triangle area over all triples.  One cross product, no roots."""
    return min(
        abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))
        for a, b, c in itertools.combinations(points, 3)
    ) / 2


def packing(points) -> float:
    """Largest common radius: half the least pairwise distance, or the least
    distance to a wall, whichever binds.  Note the square root and the fact
    that validity is coupled to the score -- SPEC.md S1(a)."""
    d = min(
        math.hypot(a[0] - b[0], a[1] - b[1])
        for a, b in itertools.combinations(points, 2)
    )
    w = min(min(x, y, 1 - x, 1 - y) for x, y in points)
    return min(d / 2, w)


def main() -> int:
    print("== (d) dynamic range: random uniform draws, seeded ==")
    for n in N_BAND:
        rng = random.Random(7)
        vals = sorted(
            heilbronn([(rng.random(), rng.random()) for _ in range(n)])
            for _ in range(SAMPLES)
        )
        print(
            f"  heilbronn n={n}  median={vals[SAMPLES // 2]:.6f}  "
            f"best-of-{SAMPLES}={vals[-1]:.6f}"
        )
    for n in N_BAND:
        rng = random.Random(7)
        vals = sorted(
            packing([(rng.random(), rng.random()) for _ in range(n)])
            for _ in range(SAMPLES)
        )
        print(
            f"  packing   n={n}  median={vals[SAMPLES // 2]:.6f}  "
            f"best-of-{SAMPLES}={vals[-1]:.6f}"
        )

    print()
    print("== (b) the top of the band is DEGENERATE for packing ==")
    grid = [
        (i / 3 * 0.75 + 0.125, j / 3 * 0.75 + 0.125)
        for i in range(4)
        for j in range(4)
    ]
    print(f"  packing n=16, the 4x4 grid: r={packing(grid):.6f}  (= 1/8 exactly, the proven optimum)")

    print()
    print("== (c) at n=13 the OBVIOUS answers score zero ==")
    n = 13
    circle = [
        (0.5 + 0.5 * math.cos(2 * math.pi * i / n), 0.5 + 0.5 * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]
    rings = (
        [(0.5 + 0.5 * math.cos(2 * math.pi * i / 8), 0.5 + 0.5 * math.sin(2 * math.pi * i / 8)) for i in range(8)]
        + [(0.5 + 0.22 * math.cos(2 * math.pi * i / 4 + 0.4), 0.5 + 0.22 * math.sin(2 * math.pi * i / 4 + 0.4)) for i in range(4)]
        + [(0.5, 0.5)]
    )
    frame = [
        (0, 0), (1, 0), (0, 1), (1, 1), (0.5, 0), (0.5, 1), (0, 0.5), (1, 0.5),
        (0.28, 0.3), (0.72, 0.28), (0.3, 0.72), (0.7, 0.7), (0.5, 0.47),
    ]
    rng = random.Random(3)
    jitter = [
        ((i % 4) / 3.4 + 0.08 + rng.uniform(-0.09, 0.09),
         (i // 4) / 3.4 + 0.08 + rng.uniform(-0.09, 0.09))
        for i in range(n)
    ]
    for name, pts in (
        ("circle of 13, r=0.5", circle),
        ("8-ring + 4-ring + centre", rings),
        ("4 corners + 4 edge midpoints + 5 inner", frame),
        ("jittered 4x4 grid", jitter),
    ):
        print(f"  {name:40s} {heilbronn(pts):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
