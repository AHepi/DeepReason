# e31-constr-003 — construction problem (sidon_residue)

Class 2 (program-checkable construction, parameterization
randomized at benchmark build time).

## Task

Construct a list of 6 distinct integers, each in [1, 20], such that (P1) all pairwise sums are distinct (Sidon property) and (P2) the total sum is congruent to 2 mod 5.  Submit the list as JSON (candidate.json).

## Verification

The trusted checker (CheckSpec `e31-constr-003-check`, runner `command`, argv `['python3', 'checker.py', 'candidate.json']`) is sealed in the holdout namespace and
revealed only post-hoc; its content address is listed in the
manifest.  Solvability was certified at build time by exhaustive
brute force (census sealed with the answer key).
