# Parked — found while closing the jailbreak gate, deliberately not done

Each entry is written for its FUTURE RUNNER: one line of WHAT, then a
ready-to-send prompt. Starting any of these should cost the operator a paste.

---

## P1 — DERIVED security findings are invisible to the gate

WHAT: the gate reads `verify_root`'s own violations and filters them to
`_SECURITY_CHECKS`. `verify_root_report` ALSO derives security findings the
replay stream never produces (`transaction-authority`, `run-result-verification`),
and the gate cannot see them. This was a deliberate, measured choice — on the
12,991-event root there are 494 such findings, all `unknown v6 task kind
'defended_trial_step'`, i.e. version skew under the 2026-08-14 law, and gating
on them refuses a lawful root. What is NOT proven is the converse: that no real
tamper produces ONLY derived-channel findings and no legacy ones.

```
Route: deepreason-orchestrator, starting at dr-set-goal.

One goal: decide, on measurement, whether a record can be tampered with in a way
that produces SECURITY findings ONLY on verify_root_report's derived/terminal
streams and NONE in verify_root's legacy violation list -- and if it can, close
that hole without refusing lawful roots.

Read first, do not re-derive:
- experiments/2026-08-31-defect-jailbreak-gate-closure/VERIFY.md (residue 1) and
  proof/big_root_channels.json -- the 494 derived findings and why they are
  version skew rather than tampering.
- src/deepreason/verification/report.py:119-129 (_SECURITY_CHECKS) and the
  derived-finding producers that emit `transaction-authority` and
  `run-result-verification`.
- src/deepreason/runtime/continuation.py::security_channel_checks -- the shipped
  predicate.

METHOD, and it is a forge campaign not a code read: extend
experiments/2026-08-31-defect-jailbreak-gate-closure/proof/security_channel_
separation.py with mutations aimed at the DERIVED producers specifically --
a work order whose task kind is altered, a run-result whose verification summary
is edited, a transaction whose authority binding is rewritten -- on copies of a
committed root. For each, record BOTH channels. The finding is any mutation
where report.security is non-empty and verify_root's legacy security set is
empty: that is a tamper the shipped gate misses.

If none exists, say so and close this with the measurement -- a negative result
recorded is the deliverable. If one exists, the fix is NOT "switch to
report.security_valid": that road was measured and refuses a lawful root. It is
a narrower predicate over the derived stream that excludes the version-skew
class, and it needs its own collision run over the eight 2026-08-30 tests.

FROZEN: verification/ and invariants.py are consumed, never edited.
End state: a committed measurement either way, and if a hole exists, a gate that
closes it with the eight collision tests still green.
```

---

## P2 — a record too corrupt to REPLAY is not refused

WHAT: when `verify_root` cannot open or replay a root it returns the single
check `open` on the INTEGRITY channel (`src/deepreason/invariants.py:954-959`),
so the security-channel gate passes it. `open` cannot simply be promoted to the
security set: a legitimate v1-manifest root produces the same check name, and
promoting it resurrects collision 2
(`tests/test_continuation.py::test_continue_keeps_manifest_and_appends_after_stop`).
Whether such a root is continuable AT ALL is unmeasured — the other
preconditions may already refuse it, in which case this is theoretical.

```
Route: deepreason-orchestrator, starting at dr-set-goal.

One goal: measure whether a root corrupted badly enough that verify_root cannot
replay it is continuable or amendable today, and close the hole only if it is.

MEASURE BEFORE DESIGNING -- this may be a non-problem:
Copy experiments/2026-08-27-pc2b-symmetric-reasoning/run and corrupt it three
ways: (a) truncate log.jsonl mid-line, (b) insert a syntactically invalid JSON
line, (c) corrupt run-manifest.json. For each, record verify_root's checks,
verify_root_report's channels, and what `prepare_continuation` and `amend_run`
actually do. Model on proof/forge_amend_ready.py, copies only.

If all three already refuse for another typed reason, the hole is theoretical:
record the measurement, add it as a test so it stays closed, and stop.

If any is ACCEPTED, the design question is how to separate "cannot open because
tampered" from "cannot open because it is a v1 manifest the current version does
not read" -- the latter being lawful under the 2026-08-14 law. The detail string
distinguishes them today (UnsupportedRunManifestVersionError vs anything else)
but keying a security gate on an exception's repr is brittle and should be
argued, not assumed. Whatever is chosen must keep collision 2 green.

FROZEN: verification/ and invariants.py consumed, never edited.
End state: either a committed negative measurement plus a regression test, or a
gate extension with the eight collision tests still green.
```

---

## P3 — the gate is paid on roots that were going to be refused anyway

WHAT: `prepare_continuation` runs the gate as its last precondition, before its
first write. That is correct for security, but it means a root refused for an
unrelated reason (`CONTINUE_TYPED_STOP_REQUIRED`, raised later inside
`_prepare_owned_v4_continuation`) still pays a full re-derivation first —
seconds on a small root, ~6 minutes on the largest. Measured consequence:
`tests/test_continuation.py` went from under a minute to 562 s serial, and three
`SUB-application.md` map checks exceeded docs_verify's 300 s per-check ceiling
until they were narrowed. The operator-facing version is worse than the test
one: `deepreason continue` on a non-resumable root now makes them wait to be
told something cheap.

```
Route: deepreason-orchestrator, starting at dr-set-goal. This is an EFFICIENCY
tranche: the gate's coverage may not shrink by one root.

One goal: make the record-integrity gate cost nothing on a continuation that was
going to be refused for an unrelated reason, without letting any byte land in a
tampered root and without narrowing what the gate refuses.

Read first:
- experiments/2026-08-31-defect-jailbreak-gate-closure/VERIFY.md, the cost
  section -- 30 ms/event, linear, 356.76 s on the largest committed root, and
  the three map checks it broke.
- src/deepreason/runtime/continuation.py::prepare_continuation -- the gate sits
  after the parse_limit pair and before the run-stops/ history write (~:437).
  CONTINUE_TYPED_STOP_REQUIRED is raised much later, inside
  _prepare_owned_v4_continuation.

THE SHAPE OF THE FIX, and the trap in it: the cheap disqualifying facts live
behind a Harness build (~4 s/root, vs ~35 s for verify_root on the same roots --
about 8x cheaper), so hoisting them before the gate is a real reordering of
prepare_continuation's prologue, not a one-liner. The trap is that the run-stops/
history write currently happens BEFORE the typed-stop check, so any reordering
that puts the gate after that check also puts a write into a tampered root and
breaks tests/test_jailbreak_gate.py::test_a_refused_verb_writes_nothing_into_the_
tampered_root. Do not weaken that test: it is the property, not the obstacle.
Either move the history write later too, or find a cheaper disqualifier.

ACCEPTANCE, three parts, all required:
- tests/test_jailbreak_gate.py green, unmodified, including the byte-unchanged
  test.
- proof/forge_amend_ready.py still reads jailbreak_open: False.
- tests/test_continuation.py back under ~120 s serial, MEASURED and recorded.
If the third cannot be met without touching the first two, stop and report the
priced fork rather than trading the property for the seconds.

End state: the same refusals, sooner, with the timing committed as evidence.
```
