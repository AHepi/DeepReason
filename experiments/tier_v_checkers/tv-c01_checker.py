#!/usr/bin/env python
"""Checker for tv-c01 (Tier V, coding). Source: HumanEval/129 (OpenAI HumanEval, MIT).
Embeds the dataset's own reference solution and its own `check(candidate)`
test function; run with no args (self-test against the reference solution)
or with a path to a candidate .py file defining `minPath`.
"""
import sys

PROMPT = '\ndef minPath(grid, k):\n    """\n    Given a grid with N rows and N columns (N >= 2) and a positive integer k, \n    each cell of the grid contains a value. Every integer in the range [1, N * N]\n    inclusive appears exactly once on the cells of the grid.\n\n    You have to find the minimum path of length k in the grid. You can start\n    from any cell, and in each step you can move to any of the neighbor cells,\n    in other words, you can go to cells which share an edge with you current\n    cell.\n    Please note that a path of length k means visiting exactly k cells (not\n    necessarily distinct).\n    You CANNOT go off the grid.\n    A path A (of length k) is considered less than a path B (of length k) if\n    after making the ordered lists of the values on the cells that A and B go\n    through (let\'s call them lst_A and lst_B), lst_A is lexicographically less\n    than lst_B, in other words, there exist an integer index i (1 <= i <= k)\n    such that lst_A[i] < lst_B[i] and for any j (1 <= j < i) we have\n    lst_A[j] = lst_B[j].\n    It is guaranteed that the answer is unique.\n    Return an ordered list of the values on the cells that the minimum path go through.\n\n    Examples:\n\n        Input: grid = [ [1,2,3], [4,5,6], [7,8,9]], k = 3\n        Output: [1, 2, 1]\n\n        Input: grid = [ [5,9,3], [4,1,6], [7,8,2]], k = 1\n        Output: [1]\n    """\n'
REFERENCE_SOLUTION_BODY = '    n = len(grid)\n    val = n * n + 1\n    for i in range(n):\n        for j in range(n):\n            if grid[i][j] == 1:\n                temp = []\n                if i != 0:\n                    temp.append(grid[i - 1][j])\n\n                if j != 0:\n                    temp.append(grid[i][j - 1])\n\n                if i != n - 1:\n                    temp.append(grid[i + 1][j])\n\n                if j != n - 1:\n                    temp.append(grid[i][j + 1])\n\n                val = min(temp)\n\n    ans = []\n    for i in range(k):\n        if i % 2 == 0:\n            ans.append(1)\n        else:\n            ans.append(val)\n    return ans\n'

# PROMPT may define helper functions the test suite calls directly (e.g.
# HumanEval/32's `poly`) -- exec it at module scope once so they resolve.
exec(PROMPT, globals())

def check(candidate):

    # Check some simple cases
    print
    assert candidate([[1, 2, 3], [4, 5, 6], [7, 8, 9]], 3) == [1, 2, 1]
    assert candidate([[5, 9, 3], [4, 1, 6], [7, 8, 2]], 1) == [1]
    assert candidate([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]], 4) == [1, 2, 1, 2]
    assert candidate([[6, 4, 13, 10], [5, 7, 12, 1], [3, 16, 11, 15], [8, 14, 9, 2]], 7) == [1, 10, 1, 10, 1, 10, 1]
    assert candidate([[8, 14, 9, 2], [6, 4, 13, 15], [5, 7, 1, 12], [3, 10, 11, 16]], 5) == [1, 7, 1, 7, 1]
    assert candidate([[11, 8, 7, 2], [5, 16, 14, 4], [9, 3, 15, 6], [12, 13, 10, 1]], 9) == [1, 6, 1, 6, 1, 6, 1, 6, 1]
    assert candidate([[12, 13, 10, 1], [9, 3, 15, 6], [5, 16, 14, 4], [11, 8, 7, 2]], 12) == [1, 6, 1, 6, 1, 6, 1, 6, 1, 6, 1, 6]
    assert candidate([[2, 7, 4], [3, 1, 5], [6, 8, 9]], 8) == [1, 3, 1, 3, 1, 3, 1, 3]
    assert candidate([[6, 1, 5], [3, 8, 9], [2, 7, 4]], 8) == [1, 5, 1, 5, 1, 5, 1, 5]

    # Check some edge cases that are easy to work out by hand.
    assert candidate([[1, 2], [3, 4]], 10) == [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
    assert candidate([[1, 3], [3, 2]], 10) == [1, 3, 1, 3, 1, 3, 1, 3, 1, 3]


def _load_reference():
    exec(PROMPT + REFERENCE_SOLUTION_BODY, globals())
    return globals()["minPath"]


def _load_candidate(path):
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), globals())
    return globals()["minPath"]


if __name__ == "__main__":
    candidate = _load_candidate(sys.argv[1]) if len(sys.argv) > 1 else _load_reference()
    try:
        check(candidate)
    except AssertionError as e:
        print("FAIL", str(e)[:200])
        sys.exit(1)
    print("PASS")
    sys.exit(0)
