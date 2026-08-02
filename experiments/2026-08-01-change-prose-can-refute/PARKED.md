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
- **`render_batch_crit_pack` still prefix-clips its targets**
  (`llm/packs.py:594`, `content_text(target, blobs)[:content_chars]`) — the
  exact "ends abruptly" truncation `_document_excerpt` was written to avoid,
  and now the only crit path where R3 is unmet. S3 names `render_crit_pack`
  alone, so the batch path is left as it is rather than widened under this
  tranche. Related: after step 9, `_document_excerpt` has no caller anywhere;
  it is deliberately kept rather than deleted, because it is the right tool for
  this path if the operator wants R3 extended to it.
- Everything already parked in
  `experiments/2026-08-01-fix-adjudication-blindness/PARKED.md`, which carries
  the nine items from the jolt investigation plus the discarded detection flags.
