#!/usr/bin/env python
"""Checker for tv-c07 (Tier V, coding). Source: HumanEval/32 (OpenAI HumanEval, MIT).
Embeds the dataset's own reference solution and its own `check(candidate)`
test function; run with no args (self-test against the reference solution)
or with a path to a candidate .py file defining `find_zero`.
"""
import sys

PROMPT = 'import math\n\n\ndef poly(xs: list, x: float):\n    """\n    Evaluates polynomial with coefficients xs at point x.\n    return xs[0] + xs[1] * x + xs[1] * x^2 + .... xs[n] * x^n\n    """\n    return sum([coeff * math.pow(x, i) for i, coeff in enumerate(xs)])\n\n\ndef find_zero(xs: list):\n    """ xs are coefficients of a polynomial.\n    find_zero find x such that poly(x) = 0.\n    find_zero returns only only zero point, even if there are many.\n    Moreover, find_zero only takes list xs having even number of coefficients\n    and largest non zero coefficient as it guarantees\n    a solution.\n    >>> round(find_zero([1, 2]), 2) # f(x) = 1 + 2x\n    -0.5\n    >>> round(find_zero([-6, 11, -6, 1]), 2) # (x - 1) * (x - 2) * (x - 3) = -6 + 11x - 6x^2 + x^3\n    1.0\n    """\n'
REFERENCE_SOLUTION_BODY = '    begin, end = -1., 1.\n    while poly(xs, begin) * poly(xs, end) > 0:\n        begin *= 2.0\n        end *= 2.0\n    while end - begin > 1e-10:\n        center = (begin + end) / 2.0\n        if poly(xs, center) * poly(xs, begin) > 0:\n            begin = center\n        else:\n            end = center\n    return begin\n'

# PROMPT may define helper functions the test suite calls directly (e.g.
# HumanEval/32's `poly`) -- exec it at module scope once so they resolve.
exec(PROMPT, globals())

METADATA = {}


def check(candidate):
    import math
    import random
    rng = random.Random(42)
    import copy
    for _ in range(100):
        ncoeff = 2 * rng.randint(1, 4)
        coeffs = []
        for _ in range(ncoeff):
            coeff = rng.randint(-10, 10)
            if coeff == 0:
                coeff = 1
            coeffs.append(coeff)
        solution = candidate(copy.deepcopy(coeffs))
        assert math.fabs(poly(coeffs, solution)) < 1e-4


def _load_reference():
    exec(PROMPT + REFERENCE_SOLUTION_BODY, globals())
    return globals()["find_zero"]


def _load_candidate(path):
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), globals())
    return globals()["find_zero"]


if __name__ == "__main__":
    candidate = _load_candidate(sys.argv[1]) if len(sys.argv) > 1 else _load_reference()
    try:
        check(candidate)
    except AssertionError as e:
        print("FAIL", str(e)[:200])
        sys.exit(1)
    print("PASS")
    sys.exit(0)
