#!/usr/bin/env python
"""Checker for tv-c08 (Tier V, coding). Source: HumanEval/20 (OpenAI HumanEval, MIT).
Embeds the dataset's own reference solution and its own `check(candidate)`
test function; run with no args (self-test against the reference solution)
or with a path to a candidate .py file defining `find_closest_elements`.
"""
import sys

PROMPT = 'from typing import List, Tuple\n\n\ndef find_closest_elements(numbers: List[float]) -> Tuple[float, float]:\n    """ From a supplied list of numbers (of length at least two) select and return two that are the closest to each\n    other and return them in order (smaller number, larger number).\n    >>> find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.2])\n    (2.0, 2.2)\n    >>> find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0])\n    (2.0, 2.0)\n    """\n'
REFERENCE_SOLUTION_BODY = '    closest_pair = None\n    distance = None\n\n    for idx, elem in enumerate(numbers):\n        for idx2, elem2 in enumerate(numbers):\n            if idx != idx2:\n                if distance is None:\n                    distance = abs(elem - elem2)\n                    closest_pair = tuple(sorted([elem, elem2]))\n                else:\n                    new_distance = abs(elem - elem2)\n                    if new_distance < distance:\n                        distance = new_distance\n                        closest_pair = tuple(sorted([elem, elem2]))\n\n    return closest_pair\n'

# PROMPT may define helper functions the test suite calls directly (e.g.
# HumanEval/32's `poly`) -- exec it at module scope once so they resolve.
exec(PROMPT, globals())

METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2]) == (3.9, 4.0)
    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0]) == (5.0, 5.9)
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.2]) == (2.0, 2.2)
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.0]) == (2.0, 2.0)
    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1]) == (2.2, 3.1)


def _load_reference():
    exec(PROMPT + REFERENCE_SOLUTION_BODY, globals())
    return globals()["find_closest_elements"]


def _load_candidate(path):
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), globals())
    return globals()["find_closest_elements"]


if __name__ == "__main__":
    candidate = _load_candidate(sys.argv[1]) if len(sys.argv) > 1 else _load_reference()
    try:
        check(candidate)
    except AssertionError as e:
        print("FAIL", str(e)[:200])
        sys.exit(1)
    print("PASS")
    sys.exit(0)
