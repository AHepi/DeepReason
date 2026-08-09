#!/usr/bin/env python
"""Checker for tv-c03 (Tier V, coding). Source: HumanEval/127 (OpenAI HumanEval, MIT).
Embeds the dataset's own reference solution and its own `check(candidate)`
test function; run with no args (self-test against the reference solution)
or with a path to a candidate .py file defining `intersection`.
"""
import sys

PROMPT = '\ndef intersection(interval1, interval2):\n    """You are given two intervals,\n    where each interval is a pair of integers. For example, interval = (start, end) = (1, 2).\n    The given intervals are closed which means that the interval (start, end)\n    includes both start and end.\n    For each given interval, it is assumed that its start is less or equal its end.\n    Your task is to determine whether the length of intersection of these two \n    intervals is a prime number.\n    Example, the intersection of the intervals (1, 3), (2, 4) is (2, 3)\n    which its length is 1, which not a prime number.\n    If the length of the intersection is a prime number, return "YES",\n    otherwise, return "NO".\n    If the two intervals don\'t intersect, return "NO".\n\n\n    [input/output] samples:\n    intersection((1, 2), (2, 3)) ==> "NO"\n    intersection((-1, 1), (0, 4)) ==> "NO"\n    intersection((-3, -1), (-5, 5)) ==> "YES"\n    """\n'
REFERENCE_SOLUTION_BODY = '    def is_prime(num):\n        if num == 1 or num == 0:\n            return False\n        if num == 2:\n            return True\n        for i in range(2, num):\n            if num%i == 0:\n                return False\n        return True\n\n    l = max(interval1[0], interval2[0])\n    r = min(interval1[1], interval2[1])\n    length = r - l\n    if length > 0 and is_prime(length):\n        return "YES"\n    return "NO"\n'

# PROMPT may define helper functions the test suite calls directly (e.g.
# HumanEval/32's `poly`) -- exec it at module scope once so they resolve.
exec(PROMPT, globals())

def check(candidate):

    # Check some simple cases
    assert candidate((1, 2), (2, 3)) == "NO"
    assert candidate((-1, 1), (0, 4)) == "NO"
    assert candidate((-3, -1), (-5, 5)) == "YES"
    assert candidate((-2, 2), (-4, 0)) == "YES"

    # Check some edge cases that are easy to work out by hand.
    assert candidate((-11, 2), (-1, -1)) == "NO"
    assert candidate((1, 2), (3, 5)) == "NO"
    assert candidate((1, 2), (1, 2)) == "NO"
    assert candidate((-2, -2), (-3, -2)) == "NO"


def _load_reference():
    exec(PROMPT + REFERENCE_SOLUTION_BODY, globals())
    return globals()["intersection"]


def _load_candidate(path):
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), globals())
    return globals()["intersection"]


if __name__ == "__main__":
    candidate = _load_candidate(sys.argv[1]) if len(sys.argv) > 1 else _load_reference()
    try:
        check(candidate)
    except AssertionError as e:
        print("FAIL", str(e)[:200])
        sys.exit(1)
    print("PASS")
    sys.exit(0)
