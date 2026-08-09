#!/usr/bin/env python
"""Checker for tv-c02 (Tier V, coding). Source: HumanEval/39 (OpenAI HumanEval, MIT).
Embeds the dataset's own reference solution and its own `check(candidate)`
test function; run with no args (self-test against the reference solution)
or with a path to a candidate .py file defining `prime_fib`.
"""
import sys

PROMPT = '\n\ndef prime_fib(n: int):\n    """\n    prime_fib returns n-th number that is a Fibonacci number and it\'s also prime.\n    >>> prime_fib(1)\n    2\n    >>> prime_fib(2)\n    3\n    >>> prime_fib(3)\n    5\n    >>> prime_fib(4)\n    13\n    >>> prime_fib(5)\n    89\n    """\n'
REFERENCE_SOLUTION_BODY = '    import math\n\n    def is_prime(p):\n        if p < 2:\n            return False\n        for k in range(2, min(int(math.sqrt(p)) + 1, p - 1)):\n            if p % k == 0:\n                return False\n        return True\n    f = [0, 1]\n    while True:\n        f.append(f[-1] + f[-2])\n        if is_prime(f[-1]):\n            n -= 1\n        if n == 0:\n            return f[-1]\n'

# PROMPT may define helper functions the test suite calls directly (e.g.
# HumanEval/32's `poly`) -- exec it at module scope once so they resolve.
exec(PROMPT, globals())

METADATA = {}


def check(candidate):
    assert candidate(1) == 2
    assert candidate(2) == 3
    assert candidate(3) == 5
    assert candidate(4) == 13
    assert candidate(5) == 89
    assert candidate(6) == 233
    assert candidate(7) == 1597
    assert candidate(8) == 28657
    assert candidate(9) == 514229
    assert candidate(10) == 433494437


def _load_reference():
    exec(PROMPT + REFERENCE_SOLUTION_BODY, globals())
    return globals()["prime_fib"]


def _load_candidate(path):
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), globals())
    return globals()["prime_fib"]


if __name__ == "__main__":
    candidate = _load_candidate(sys.argv[1]) if len(sys.argv) > 1 else _load_reference()
    try:
        check(candidate)
    except AssertionError as e:
        print("FAIL", str(e)[:200])
        sys.exit(1)
    print("PASS")
    sys.exit(0)
