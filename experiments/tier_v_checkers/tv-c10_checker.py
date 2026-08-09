#!/usr/bin/env python
"""Checker for tv-c10 (Tier V, coding). Source: HumanEval/132 (OpenAI HumanEval, MIT).
Embeds the dataset's own reference solution and its own `check(candidate)`
test function; run with no args (self-test against the reference solution)
or with a path to a candidate .py file defining `is_nested`.
"""
import sys

PROMPT = "\ndef is_nested(string):\n    '''\n    Create a function that takes a string as input which contains only square brackets.\n    The function should return True if and only if there is a valid subsequence of brackets \n    where at least one bracket in the subsequence is nested.\n\n    is_nested('[[]]') ➞ True\n    is_nested('[]]]]]]][[[[[]') ➞ False\n    is_nested('[][]') ➞ False\n    is_nested('[]') ➞ False\n    is_nested('[[][]]') ➞ True\n    is_nested('[[]][[') ➞ True\n    '''\n"
REFERENCE_SOLUTION_BODY = "    opening_bracket_index = []\n    closing_bracket_index = []\n    for i in range(len(string)):\n        if string[i] == '[':\n            opening_bracket_index.append(i)\n        else:\n            closing_bracket_index.append(i)\n    closing_bracket_index.reverse()\n    cnt = 0\n    i = 0\n    l = len(closing_bracket_index)\n    for idx in opening_bracket_index:\n        if i < l and idx < closing_bracket_index[i]:\n            cnt += 1\n            i += 1\n    return cnt >= 2\n\n    \n"

# PROMPT may define helper functions the test suite calls directly (e.g.
# HumanEval/32's `poly`) -- exec it at module scope once so they resolve.
exec(PROMPT, globals())

def check(candidate):

    # Check some simple cases
    assert candidate('[[]]') == True, "This prints if this assert fails 1 (good for debugging!)"
    assert candidate('[]]]]]]][[[[[]') == False
    assert candidate('[][]') == False
    assert candidate(('[]')) == False
    assert candidate('[[[[]]]]') == True
    assert candidate('[]]]]]]]]]]') == False
    assert candidate('[][][[]]') == True
    assert candidate('[[]') == False
    assert candidate('[]]') == False
    assert candidate('[[]][[') == True
    assert candidate('[[][]]') == True

    # Check some edge cases that are easy to work out by hand.
    assert candidate('') == False, "This prints if this assert fails 2 (also good for debugging!)"
    assert candidate('[[[[[[[[') == False
    assert candidate(']]]]]]]]') == False


def _load_reference():
    exec(PROMPT + REFERENCE_SOLUTION_BODY, globals())
    return globals()["is_nested"]


def _load_candidate(path):
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), globals())
    return globals()["is_nested"]


if __name__ == "__main__":
    candidate = _load_candidate(sys.argv[1]) if len(sys.argv) > 1 else _load_reference()
    try:
        check(candidate)
    except AssertionError as e:
        print("FAIL", str(e)[:200])
        sys.exit(1)
    print("PASS")
    sys.exit(0)
