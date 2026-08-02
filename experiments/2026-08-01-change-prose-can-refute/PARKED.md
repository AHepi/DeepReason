# Parked

One line each. Noticed while capturing this request, not part of it.

- `authority.py` `trial_authority_for` computes `mode = text_authority_mode(...)`
  and discards it — the same compute-then-throw-away shape as the detector in
  `invariants.py:4040-4048`. Worth a sweep for other instances.
- **An operator decision, surfaced at step 8, deliberately not taken here.**
  SPEC.md's A1 read R4's "formal claims" as `programs.evaluable`. The line the
  code actually enforces is `execution_backed` (`rules/warrants.py:24`), which
  is narrower: only EXEC-oracle commitments (exec / property / dataset_oracle)
  that all currently pass. A `predicate:` commitment is `evaluable` but NOT
  execution-backed, so a target carrying only predicates is open to prose
  refutation. Whether R4 means to protect those too is the operator's call;
  widening the guard would change what every existing run may do, so it is not
  done under an assumption. Asserted as-is in
  `test_the_formal_boundary_is_execution_backing_and_not_evaluability`.
- Everything already parked in
  `experiments/2026-08-01-fix-adjudication-blindness/PARKED.md`, which carries
  the nine items from the jolt investigation plus the discarded detection flags.
