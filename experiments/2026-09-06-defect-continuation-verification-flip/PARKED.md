# PARKED — the continuation-verdict tranche

Noticed while diagnosing; not this tranche's goal. Each is a ready-to-send
prompt for its own window.

## P1 — an open work order does not affect the verdict, and the continuation gate cannot see one

**What.** `verify_root` lists outstanding work orders in its own stats and
does not let them touch `valid`. The pre-continuation ARM R root reported
`violations: 0` while its stats named three open work orders — the same three
whose honest closure the post-continuation verdict then condemned. Separately,
`_continuation_authority` (`src/deepreason/application/results.py:625`) reads
only whether the workflow state carries a terminal lifecycle decision or an
open resume decision; it consults neither the replay verdict nor those open
work orders, and `continue`/`amend` refuse on SECURITY-channel findings while
`attempt-validity` is an INTEGRITY finding. So the operator's 2026-08-29 law —
continuation is integrity-gated, "I don't want a jailbroken run to be
continuable" — is served by a gate thinner than its words. Nothing was
tampered with in this incident; this is exposure, not a breach.

Why not folded into this tranche: it is a POLICY question rather than a defect
against a documented guarantee. Making an unterminated work order invalidate a
record would condemn every operationally-failed root ever committed, and that
is the operator's call, not a fix.

```
EXECUTOR WINDOW — DESIGN-AND-STOP: what should an open work order mean?
Read CLAUDE.md (the 2026-08-29 law on clean stops and integrity-gated
continuation). Load dr-change-orchestrator and pinker-write-for-readers.
GOAL: decide, in writing and with the operator's word, what a record with
outstanding work orders should mean for (a) `verify_root`'s `valid`, and
(b) whether `continue`/`amend` may proceed. Evidence to read first:
experiments/2026-09-06-defect-continuation-verification-flip/DIAGNOSIS.md
(the before-verdict's stats list the three open work orders beside
violations: 0) and application/results.py::_continuation_authority with its
own docstring on why it reads the lifecycle and not the reason. Price at
least three roads: a new typed finding on an INTEGRITY channel; a
SECURITY-channel finding (which would block continuation, and would condemn
existing roots); a disclosure only, with the gate reporting the count. Census
every committed root for outstanding work orders BEFORE proposing, so the
operator sees how many roots each road moves. STOP at SPEC.md with the
options priced; frozen surface 3 contact is likely, so request any grant
there before code. OUT OF SCOPE: the attempt-validity classification (its own
tranche).
```

## P2 — the check's own name is wider than the agreement it enforces

**What.** `attempt-validity` bundles four different rules (dropped, failure,
semantic rejection, success) whose only shared subject is "the attempt trace
must agree with the call's outcome". The seam that owns that agreement,
`DR-SEAM-llm-x-verification`, documents the split-legs incident but does not
state this one: what a NON-ADMITTED semantic admission implies about the
trace. If this tranche's fix lands, that sentence should be written into the
seam with a check; if it does not, the gap is still worth closing.

**PARTLY LANDED, 2026-09-09.** The fix landed, and with it the seam gained the
one sentence this defect broke — a non-admitted call is classified by its
trace, with a `check:` that fails if the classifier stops agreeing. What is
still parked is the REST of the census the prompt below asks for: the
`admitted`, `dropped` and `transport_failure` clauses, each derived from
`invariants.py` as it then stands, so the seam states the whole agreement
rather than the half a defect forced. Send the prompt as written; it will find
one clause already there.

```
EXECUTOR WINDOW — CHANGE (map only, no code): write the missing seam agreement
Read CLAUDE.md and docs/map/SCHEMA.md. Load dr-change-orchestrator.
GOAL: DR-SEAM-llm-x-verification states, with a column-0 `check:`, what each
semantic-admission outcome implies about the call's attempt trace — admitted:
one final wire-valid attempt; rejected/schema_exhausted: at most one final
wire-valid attempt; transport_failure: none. Derive each clause from
src/deepreason/invariants.py as it stands when you run, not from this note,
and make the check fail if the classifier stops agreeing. No src/ changes.
```
