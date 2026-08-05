# Parked — rung 5 (deliberately dumb alternative)

Noticed during this tranche, deliberately NOT done here.

P1. **The live A/B is not run.** R13 stops before it and asks for
credentials. Not a gap in the offline work — the socket is proven
offline — but the comparison the handover calls "valuable" remains
unmade, and this tranche records that as unproven rather than implied.

P2. **A map check can pass while the prose beside it is false.**
`SEAM-schools-x-scheduler`'s fingerprint row said the stamp fires "at
construction" while its own `check:` two lines below asserted it does
NOT. Rung 4 moved the code and updated the check without updating the
sentence. Fixed here in passing. The general point is worth someone's
attention: `docs_verify` validates checks, not the prose they sit under,
so a document can be green and still mislead its next reader.

P3. **The offline fixture cannot see allocation divergence in
provenance.** A mock endpoint returning one candidate makes both
backends' runs settle on school-0, so the dumb allocation shows up only
as less work done, not as different work. A fixture with per-school
distinguishable responses would show more — worth building if a later
rung needs to compare backends on outcomes rather than on volume.

P4. **`_ACTIVE_BACKEND_ID` is now process-global mutable state.** The
scoped selector restores it, including on exceptions, and tests pin
that. But nothing prevents a future caller from assigning the module
attribute directly and leaking a backend across runs in one process. A
stricter design (thread-local, or selection threaded through Scheduler)
was not built because it was not asked for and would have touched the
ten call sites the seam exists to keep untouched.

P5. **Rung 4's PARKED items remain open** — the other two registries
(operator-confirmed parked), `INV-frozen-surfaces`' `Owns:`-vs-surface
ambiguity, its unqualified `Config` invitation, and `pyproject.toml`'s
`dev` extra not producing a runnable gate.

P6. **Fixture-drift forecasting is the weakest part of two consecutive
specs.** Rung 4's D9 predicted count assertions and missed an allow-list
and a content test; rung 5's spec predicted nothing and missed a rung 3
registry test. Both were caught by the full gate and handled correctly,
but a spec-phase habit of grepping for tests that assert on the thing
being changed would have caught both earlier and cheaper.

## In-flight note (2026-08-04, during the live A/B)

The two run homes (`ab-home/runs/`, `rr-home/`) are deliberately NOT
committed while the ladder is running. The harness is appending to
`log.jsonl` as this is written, and committing a root mid-append would
capture a torn tail and present it as evidence — the failure mode
`DR-SEAM-harness-x-verification` exists to prevent, where a reader repairs
or misreads a partial record. They are committed once the ladder exits and
`verify_root` has judged them, which is the only point at which a root is
evidence rather than a file.

## P7 (DEFECT, found by the live A/B — parked, NOT fixed)

**A live run under the round-robin backend produced a root that fails
`verify_root`.** Arm B, `rr-home/runs/run-9a6be78e1e79184a0bd89923b957586c`:

    attempt-validity: event seq=17: failed call must contain no valid
                      attempt, got [0]

Characterised, not theorised (the blob-before-theory rule):
- seq 17 is a `Rule.CONTROL` event carrying a conjecturer LLM call.
- Its attempt trace has ONE attempt: `attempt=0`, `validation_path=''`
  (i.e. it parsed valid), `raw_ref` present, no diagnostic ref.
- `invariants.py:3695` classified the call's `expected_outcome` as
  `FAILURE_REQUIRED`, and that arm forbids ANY valid attempt.
- So the disagreement is between the workflow's expected call OUTCOME and
  the recorded attempt VALIDITY. It is not an allocation-layer fact:
  school allocation decides which schools work a problem, not how a
  provider call's attempt trace is recorded.
- Neither arm has a call with `ok=False` (`default` 31 calls, `roundrobin`
  24 calls, 0 failed in both), so "failed" here is the verifier's derived
  classification, not a transport failure.

**What this is NOT evidence of.** It is not evidence that round-robin
CAUSES the defect. The honest reading is that a different allocation drove
the workflow down a path arm A did not take. Whether the same path is
reachable under the default backend is UNKNOWN from one sample —
CLAUDE.md's own standing fact is that capability/provider paths are
stochastic across identical runs, and one live attempt that misses a path
is inconclusive for that path.

**Not fixed here.** A defect found mid-change is PARKED, not fixed; and
`invariants.py` is frozen surface 3, which this tranche has no
authorization to touch. It routes to `deepreason-orchestrator` as its own
tranche, where diagnosis starts from the typed record — which now exists
and is committed.

**Worth noting for the rung programme:** this is the deliberately dumb
backend earning its keep beyond its charter. Rung 5 asked it to prove the
socket real; it also worked as a cheap fuzzer over run shapes, which is an
argument for keeping it registered rather than deleting it after the rung.
