# e31-constr-004 — construction problem (forbidden_words)

Class 2 (program-checkable construction, parameterization
randomized at benchmark build time).

## Task

Construct a binary string of length 15 with (P1) exactly 6 ones and (P2) none of the forbidden substrings '0110', '1010', '1100' occurring anywhere.  Submit the string as a JSON string (candidate.json).

## Verification

The trusted checker (CheckSpec `e31-constr-004-check`, runner `command`, argv `['python3', 'checker.py', 'candidate.json']`) is sealed in the holdout namespace and
revealed only post-hoc; its content address is listed in the
manifest.  Solvability was certified at build time by exhaustive
brute force (census sealed with the answer key).
