# e31-constr-005 — construction problem (displaced_permutation)

Class 2 (program-checkable construction, parameterization
randomized at benchmark build time).

## Task

Construct a permutation p of 0..7 such that (P1) p has no fixed point, (P2) no index i has |p[i] - i| in {1, 2}, and (P3) the sum of |p[i] - i| over all i is congruent to 0 mod 3.  Submit p as a JSON list (candidate.json).

## Verification

The trusted checker (CheckSpec `e31-constr-005-check`, runner `command`, argv `['python3', 'checker.py', 'candidate.json']`) is sealed in the holdout namespace and
revealed only post-hoc; its content address is listed in the
manifest.  Solvability was certified at build time by exhaustive
brute force (census sealed with the answer key).
