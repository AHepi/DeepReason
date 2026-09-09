# Results — the continuation verification flip

## 2026-09-09 — the check was too strict, and it had been for a month

**What was observed.** One committed root, three events, two contradictory
verdicts from one instrument minutes apart. ARM R's
`run-c3f3bf10bc57d63e224a9f1c68bf1057` verified with zero violations before a
continuation and with three `attempt-validity` violations after it, over events
142, 215 and 295 that were byte-identical at both commits.

**What the record showed.** The events never changed. What changed is that
three work orders still open when the run died were CLOSED by the continuation
— a semantic admission `schema_exhausted` over the attempt the original run had
already recorded, plus a typed terminal, with no model call and
`logged_tokens_this_run: 0`. `_controller_v3_history` classified any call whose
semantic admission exists and is not `admitted` as `FAILURE_REQUIRED`, whose
`attempt-validity` clause forbids a wire-valid attempt. A semantic
non-admission is exactly the case where the wire reply DID parse, so the rule
was wrong about a legitimate record. The permissive category already existed —
`SEMANTIC_REJECTION` — but the only route into it demanded a durable
patch-repair chain a conjecturer call closed by a resume can never present.

**Which road the record chose.** R-STRICT, as GOAL.md framed the fork: the
check was too strict after a resume and the run's events were always sound.
R-WEAK survives only in the narrow form DIAGNOSIS.md stated — a record whose
own stats list open work orders still verifies `valid: true` — and that is a
policy question about what `valid` should mean, PARKED as P1, not fixed here.

**What was fixed.** `_is_patch_repair_semantic_rejection(row, admission)`
became `_is_semantic_rejection(row)`: a non-admitted call whose final attempt
is wire-valid is a semantic rejection; anything else stays a failure. One
predicate and one call site, 19 insertions and 33 deletions, inside frozen
surface 3 under an operator grant given 2026-09-09.

**What the record now shows.** Both roots the census found — ARM R's three
calls and the 2026-08-04 root's one, which had said `valid: false` since the
day it was written — re-derive to zero `verify_root` violations, without either
root being touched. The stored `REPLAY_VALIDATION.json` files are unchanged and
still say `valid: false`; they are verdicts written by an earlier reader, which
the 2026-08-14 law makes legal rather than contradictory.

**The residue, stated as residue.**

- The defect predates the continuation by a month. ARM R did not create it; it
  produced a second instance in a way that made two verdicts collide in public.
  Every clean verdict written before 2026-09-09 on a root carrying a wire-valid
  semantically-rejected call was reading the same reader.
- One tripwire is gone, and that was the price of the grant: a record CLAIMING
  a wire-valid reply was semantically rejected is now accepted. Measured, not
  assumed — a committed mutation test in
  `tests/test_v6_engaged_repair_verification.py` asserted the refusal and now
  asserts its absence, with the grant in its docstring.
- Neither `deepreason results --verify` root reaches zero violations, and that
  is not this fix's business: the residual `run-result-verification` finding
  reads the verdict each run STORED in its own `RunResult` record when it
  terminalized. A committed root is never edited, so that echo stands.
- P1 (what an open work order should mean for `valid`, and for whether
  `continue`/`amend` may proceed) is untouched and ready to send.

**Verdict: PASS**, offline. The all-roots census moved exactly two verdicts,
both from dirty to clean, and left all 67 previously-clean roots clean. The
full gate reported 4 failed, 5169 passed; all four are other people's — three
pre-existing `test_organiser_seat.py` failures reproduced on the pre-fix tree,
and one documented `-n 4` thread-timing flake that passes serially. Detail and
every pasted output live in VERIFY.md.
