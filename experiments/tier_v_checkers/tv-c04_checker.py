#!/usr/bin/env python
"""Checker for tv-c04 (Tier V, coding). Source: HumanEval/124 (OpenAI HumanEval, MIT).
Embeds the dataset's own reference solution and its own `check(candidate)`
test function; run with no args (self-test against the reference solution)
or with a path to a candidate .py file defining `valid_date`.
"""
import sys

PROMPT = '\ndef valid_date(date):\n    """You have to write a function which validates a given date string and\n    returns True if the date is valid otherwise False.\n    The date is valid if all of the following rules are satisfied:\n    1. The date string is not empty.\n    2. The number of days is not less than 1 or higher than 31 days for months 1,3,5,7,8,10,12. And the number of days is not less than 1 or higher than 30 days for months 4,6,9,11. And, the number of days is not less than 1 or higher than 29 for the month 2.\n    3. The months should not be less than 1 or higher than 12.\n    4. The date should be in the format: mm-dd-yyyy\n\n    for example: \n    valid_date(\'03-11-2000\') => True\n\n    valid_date(\'15-01-2012\') => False\n\n    valid_date(\'04-0-2040\') => False\n\n    valid_date(\'06-04-2020\') => True\n\n    valid_date(\'06/04/2020\') => False\n    """\n'
REFERENCE_SOLUTION_BODY = "    try:\n        date = date.strip()\n        month, day, year = date.split('-')\n        month, day, year = int(month), int(day), int(year)\n        if month < 1 or month > 12:\n            return False\n        if month in [1,3,5,7,8,10,12] and day < 1 or day > 31:\n            return False\n        if month in [4,6,9,11] and day < 1 or day > 30:\n            return False\n        if month == 2 and day < 1 or day > 29:\n            return False\n    except:\n        return False\n\n    return True\n"

# PROMPT may define helper functions the test suite calls directly (e.g.
# HumanEval/32's `poly`) -- exec it at module scope once so they resolve.
exec(PROMPT, globals())

def check(candidate):

    # Check some simple cases
    assert candidate('03-11-2000') == True

    assert candidate('15-01-2012') == False

    assert candidate('04-0-2040') == False

    assert candidate('06-04-2020') == True

    assert candidate('01-01-2007') == True

    assert candidate('03-32-2011') == False

    assert candidate('') == False

    assert candidate('04-31-3000') == False

    assert candidate('06-06-2005') == True

    assert candidate('21-31-2000') == False

    assert candidate('04-12-2003') == True

    assert candidate('04122003') == False

    assert candidate('20030412') == False

    assert candidate('2003-04') == False

    assert candidate('2003-04-12') == False

    assert candidate('04-2003') == False


def _load_reference():
    exec(PROMPT + REFERENCE_SOLUTION_BODY, globals())
    return globals()["valid_date"]


def _load_candidate(path):
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), globals())
    return globals()["valid_date"]


if __name__ == "__main__":
    candidate = _load_candidate(sys.argv[1]) if len(sys.argv) > 1 else _load_reference()
    try:
        check(candidate)
    except AssertionError as e:
        print("FAIL", str(e)[:200])
        sys.exit(1)
    print("PASS")
    sys.exit(0)
