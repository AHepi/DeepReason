"""Independent oracle for the turmite question. NOT shown to the model.

Semantics per dossier: turn by rule[c], advance the cell, then jump forward by
a stride of (c+1) using the NEW facing, where c is the state found on arrival.
Cells passed over are not visited.

This is deliberately not Langton's ant. Under the standard unit-stride rule
`RL` is the famous highway-builder (period 104); here it builds none, and
`RLR`, which builds none under the standard rule, builds one at period 38.
Recalled turmite results are therefore inverted, not merely inapplicable.
"""
TURNS = {"L": 1, "R": -1, "N": 0, "U": 2}
DIRS = [(0, 1), (-1, 0), (0, -1), (1, 0)]


def detect(rule, steps, tail=200_000):
    k = len(rule)
    grid = {}
    x = y = 0
    f = 0
    xs = []
    for step in range(steps):
        c = grid.get((x, y), 0)
        f = (f + TURNS[rule[c]]) % 4
        grid[(x, y)] = (c + 1) % k
        dx, dy = DIRS[f]
        stride = c + 1
        x, y = x + dx * stride, y + dy * stride
        if step >= steps - tail:
            xs.append((x, y, f))
    for p in range(1, 3000):
        if len(xs) <= 3 * p:
            break
        x0, y0, f0 = xs[0]
        x1, y1, f1 = xs[p]
        if f0 != f1:
            continue
        d = (x1 - x0, y1 - y0)
        if d == (0, 0):
            continue
        ok = True
        for j in range(1, min(150, (len(xs) - 1) // p)):
            xa, ya, fa = xs[j * p]
            if (j + 1) * p >= len(xs):
                break
            xb, yb, fb = xs[(j + 1) * p]
            if fa != fb or (xb - xa, yb - ya) != d:
                ok = False
                break
        if ok:
            return {"period": p, "drift": d, "cells": len(grid)}
    return None


if __name__ == "__main__":
    import sys
    rules = sys.argv[1:]
    for r in rules:
        res = detect(r, 2_000_000)
        print(f"{r:10} {'HIGHWAY' if res else 'none':10} {res or ''}")
