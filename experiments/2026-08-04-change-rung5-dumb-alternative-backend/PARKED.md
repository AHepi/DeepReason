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
