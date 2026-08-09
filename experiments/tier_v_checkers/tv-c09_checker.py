#!/usr/bin/env python
"""Checker for tv-c09 (Tier V, coding). Source: HumanEval/156 (OpenAI HumanEval, MIT).
Embeds the dataset's own reference solution and its own `check(candidate)`
test function; run with no args (self-test against the reference solution)
or with a path to a candidate .py file defining `int_to_mini_roman`.
"""
import sys

PROMPT = '\ndef int_to_mini_roman(number):\n    """\n    Given a positive integer, obtain its roman numeral equivalent as a string,\n    and return it in lowercase.\n    Restrictions: 1 <= num <= 1000\n\n    Examples:\n    >>> int_to_mini_roman(19) == \'xix\'\n    >>> int_to_mini_roman(152) == \'clii\'\n    >>> int_to_mini_roman(426) == \'cdxxvi\'\n    """\n'
REFERENCE_SOLUTION_BODY = '    num = [1, 4, 5, 9, 10, 40, 50, 90,  \n           100, 400, 500, 900, 1000] \n    sym = ["I", "IV", "V", "IX", "X", "XL",  \n           "L", "XC", "C", "CD", "D", "CM", "M"] \n    i = 12\n    res = \'\'\n    while number: \n        div = number // num[i] \n        number %= num[i] \n        while div: \n            res += sym[i] \n            div -= 1\n        i -= 1\n    return res.lower()\n'

# PROMPT may define helper functions the test suite calls directly (e.g.
# HumanEval/32's `poly`) -- exec it at module scope once so they resolve.
exec(PROMPT, globals())

def check(candidate):

    # Check some simple cases
    assert candidate(19) == 'xix'
    assert candidate(152) == 'clii'
    assert candidate(251) == 'ccli'
    assert candidate(426) == 'cdxxvi'
    assert candidate(500) == 'd'
    assert candidate(1) == 'i'
    assert candidate(4) == 'iv'
    assert candidate(43) == 'xliii'
    assert candidate(90) == 'xc'
    assert candidate(94) == 'xciv'
    assert candidate(532) == 'dxxxii'
    assert candidate(900) == 'cm'
    assert candidate(994) == 'cmxciv'
    assert candidate(1000) == 'm'

    # Check some edge cases that are easy to work out by hand.
    assert True


def _load_reference():
    exec(PROMPT + REFERENCE_SOLUTION_BODY, globals())
    return globals()["int_to_mini_roman"]


def _load_candidate(path):
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), globals())
    return globals()["int_to_mini_roman"]


if __name__ == "__main__":
    candidate = _load_candidate(sys.argv[1]) if len(sys.argv) > 1 else _load_reference()
    try:
        check(candidate)
    except AssertionError as e:
        print("FAIL", str(e)[:200])
        sys.exit(1)
    print("PASS")
    sys.exit(0)
