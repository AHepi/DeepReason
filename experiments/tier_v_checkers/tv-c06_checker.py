#!/usr/bin/env python
"""Checker for tv-c06 (Tier V, coding). Source: HumanEval/25 (OpenAI HumanEval, MIT).
Embeds the dataset's own reference solution and its own `check(candidate)`
test function; run with no args (self-test against the reference solution)
or with a path to a candidate .py file defining `factorize`.
"""
import sys

PROMPT = 'from typing import List\n\n\ndef factorize(n: int) -> List[int]:\n    """ Return list of prime factors of given integer in the order from smallest to largest.\n    Each of the factors should be listed number of times corresponding to how many times it appeares in factorization.\n    Input number should be equal to the product of all factors\n    >>> factorize(8)\n    [2, 2, 2]\n    >>> factorize(25)\n    [5, 5]\n    >>> factorize(70)\n    [2, 5, 7]\n    """\n'
REFERENCE_SOLUTION_BODY = '    import math\n    fact = []\n    i = 2\n    while i <= int(math.sqrt(n) + 1):\n        if n % i == 0:\n            fact.append(i)\n            n //= i\n        else:\n            i += 1\n\n    if n > 1:\n        fact.append(n)\n    return fact\n'

# PROMPT may define helper functions the test suite calls directly (e.g.
# HumanEval/32's `poly`) -- exec it at module scope once so they resolve.
exec(PROMPT, globals())

METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate(2) == [2]
    assert candidate(4) == [2, 2]
    assert candidate(8) == [2, 2, 2]
    assert candidate(3 * 19) == [3, 19]
    assert candidate(3 * 19 * 3 * 19) == [3, 3, 19, 19]
    assert candidate(3 * 19 * 3 * 19 * 3 * 19) == [3, 3, 3, 19, 19, 19]
    assert candidate(3 * 19 * 19 * 19) == [3, 19, 19, 19]
    assert candidate(3 * 2 * 3) == [2, 3, 3]


def _load_reference():
    exec(PROMPT + REFERENCE_SOLUTION_BODY, globals())
    return globals()["factorize"]


def _load_candidate(path):
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), globals())
    return globals()["factorize"]


if __name__ == "__main__":
    candidate = _load_candidate(sys.argv[1]) if len(sys.argv) > 1 else _load_reference()
    try:
        check(candidate)
    except AssertionError as e:
        print("FAIL", str(e)[:200])
        sys.exit(1)
    print("PASS")
    sys.exit(0)
