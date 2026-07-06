# Stress campaign findings

Offline campaign (`scripts/stress_test.py`, zero LLM tokens) pushing the
core harness past normal sizes and shapes, plus a targeted security probe.
CI regressions in `tests/test_stress.py` and `tests/test_security.py`.

## Finding 1 — CRITICAL: RCE via predicate `eval` (FIXED)

**Severity: critical (arbitrary code execution reachable from ordinary
criticism of LLM output).**

`ForbiddenCase.eval` was an unconstrained `str`. `compile_forbidden_
commitments` copies it verbatim into a registered `Commitment`, and a
`predicate:` eval reaches `programs.evaluate`, which ran
`eval(arg, {"__builtins__": {}, ...})`. That sandbox is escapable via the
classic object-subclasses walk:

```
[c for c in ().__class__.__base__.__subclasses__()
 if c.__name__=='catch_warnings'][0]()._module.__builtins__['open'](...)
```

Since a skeleton candidate is LLM output, and `crit_program` evaluates
every candidate's evaluable commitments on every cycle, **model output
could execute arbitrary code on the host** — a foundational violation of
the "LLM is untrusted bounded data" trust model. Proven end-to-end by
writing a file from a candidate.

**Fix (two layers, defense-in-depth):**
1. `ForbiddenCase.eval` now rejects anything but `rubric:`/`program:` —
   untrusted content can't specify an inline predicate, so the malicious
   skeleton fails to parse and never registers a commitment.
2. `programs.evaluate` AST-validates every predicate before `eval`,
   rejecting dunder attribute/name access (the escape's necessary
   ingredient) and `**` (integer-bomb DoS). Every legitimate predicate
   (`len`/`in`/comprehensions over `content`) is untouched.

Regressions: `tests/test_security.py` (4 tests). The same class of bug
exists in MiniReason's `checks.py` and is fixed on the `claude/mini-harness`
branch.

## Finding 2 — verify_root is O(n²) (documented scaling limit)

`invariants.verify_root` calls `harness.transitions()`, which on a cold
harness re-adjudicates **per event** to reconstruct the status-change
history (profile at n=2000: 4010 `_adjudicate` calls, 28s of 30s total).
Timings: 1000 artifacts ≈ 4s; 4000 artifacts ≈ 89s.

This is inherent — a per-event transition history needs the status after
each event, and grounded extension isn't incrementally cheap in general
(a deep attack can flip many statuses at once). It is **not a correctness
bug**: verify_root is an occasional offline audit, and real runs hold
hundreds-to-low-thousands of artifacts. Noted rather than optimized to
avoid risking the audit tool's correctness. If auditing very large roots
becomes routine, the fix is a single-pass transition computation that
memoizes grounded labels across events.

Secondary note: verify_root's transitions check compares two *cold*
`transitions()` results, so it tests fresh-vs-fresh determinism rather
than incremental-vs-fresh equivalence. Still catches nondeterminism;
weaker than the intended incremental-shadow check.

## What held up (no defects)

- **Deep attack chains** (depth 600): grounded status alternates
  correctly to the tip; base parity exact; zero violations.
- **Wide fan-in** (800 attackers on one target): refuted, clean.
- **Deep dependence cascade** (depth 500): refuting the root suspends all
  499 dependents as `suspended_unsupported`; zero violations.
- **Pathological content** (5 MB, RTL/snowman/NUL/control bytes, empty,
  10k newlines): byte-for-byte round-trip through the blob store.
- **Durability**: torn final log line tolerated (prior events intact);
  verify_root does not crash on a missing content blob.
- **Corruption detection**: duplicate seq, seq gap, and dangling object
  reference are all caught; log truncation from the end is correctly
  treated as a valid earlier state (== time-travel), not a violation.
