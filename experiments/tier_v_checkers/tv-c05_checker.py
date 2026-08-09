#!/usr/bin/env python
"""Checker for tv-c05 (Tier V, coding). Source: HumanEval/109 (OpenAI HumanEval, MIT).
Embeds the dataset's own reference solution and its own `check(candidate)`
test function; run with no args (self-test against the reference solution)
or with a path to a candidate .py file defining `move_one_ball`.
"""
import sys

PROMPT = '\ndef move_one_ball(arr):\n    """We have an array \'arr\' of N integers arr[1], arr[2], ..., arr[N].The\n    numbers in the array will be randomly ordered. Your task is to determine if\n    it is possible to get an array sorted in non-decreasing order by performing \n    the following operation on the given array:\n        You are allowed to perform right shift operation any number of times.\n    \n    One right shift operation means shifting all elements of the array by one\n    position in the right direction. The last element of the array will be moved to\n    the starting position in the array i.e. 0th index. \n\n    If it is possible to obtain the sorted array by performing the above operation\n    then return True else return False.\n    If the given array is empty then return True.\n\n    Note: The given list is guaranteed to have unique elements.\n\n    For Example:\n    \n    move_one_ball([3, 4, 5, 1, 2])==>True\n    Explanation: By performin 2 right shift operations, non-decreasing order can\n                 be achieved for the given array.\n    move_one_ball([3, 5, 4, 1, 2])==>False\n    Explanation:It is not possible to get non-decreasing order for the given\n                array by performing any number of right shift operations.\n                \n    """\n'
REFERENCE_SOLUTION_BODY = '    if len(arr)==0:\n      return True\n    sorted_array=sorted(arr)\n    my_arr=[]\n    \n    min_value=min(arr)\n    min_index=arr.index(min_value)\n    my_arr=arr[min_index:]+arr[0:min_index]\n    for i in range(len(arr)):\n      if my_arr[i]!=sorted_array[i]:\n        return False\n    return True\n'

# PROMPT may define helper functions the test suite calls directly (e.g.
# HumanEval/32's `poly`) -- exec it at module scope once so they resolve.
exec(PROMPT, globals())

def check(candidate):

    # Check some simple cases
    assert candidate([3, 4, 5, 1, 2])==True, "This prints if this assert fails 1 (good for debugging!)"
    assert candidate([3, 5, 10, 1, 2])==True
    assert candidate([4, 3, 1, 2])==False
    # Check some edge cases that are easy to work out by hand.
    assert candidate([3, 5, 4, 1, 2])==False, "This prints if this assert fails 2 (also good for debugging!)"
    assert candidate([])==True


def _load_reference():
    exec(PROMPT + REFERENCE_SOLUTION_BODY, globals())
    return globals()["move_one_ball"]


def _load_candidate(path):
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), globals())
    return globals()["move_one_ball"]


if __name__ == "__main__":
    candidate = _load_candidate(sys.argv[1]) if len(sys.argv) > 1 else _load_reference()
    try:
        check(candidate)
    except AssertionError as e:
        print("FAIL", str(e)[:200])
        sys.exit(1)
    print("PASS")
    sys.exit(0)
