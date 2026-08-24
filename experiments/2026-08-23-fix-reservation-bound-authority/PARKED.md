# PARKED — noticed while fixing the bound authority, deliberately not fixed

One tranche, one goal (GOAL.md). Each entry is a finding with a ready-to-send
prompt, not open work for this window.

---

## P1-bound — `preview_request`'s endpoint fallback is unreachable, and its unreachability is load-bearing

**What:** `_completion_cap` reads
`getattr(endpoint, "max_tokens", lease.route.max_tokens)` on the branch for
routes that declare no qualified capacity. The default never fires for the
production endpoint: `OpenAICompatEndpoint.__init__` declares
`max_tokens: int | None = None` (`llm/endpoints.py:261,275`) and
`_endpoint_from_spec` passes `spec.get("max_tokens")` (`llm/adapter.py:1710`),
so the attribute is always PRESENT and may be `None`. `int(None or 0)` is `0`.

A role spec that omits `max_tokens` on a legacy route therefore books a
completion bound of **zero**, not the route's. Against a finite ceiling that is
safe by accident — `TokenMeter.reserve` fails closed on a missing bound and a
zero bound under-books rather than over-books — but the code reads as though a
fallback protects it, and it does not. This tranche did not touch it because
the attempt-3 shape never reaches that branch (every route declared
`context_window_tokens`), and widening the change would have put an untested
branch in a bound-arithmetic commit.

```
Route: deepreason-orchestrator (defect, small).

One goal: make the completion cap for a route with no qualified capacity come
from a value that is actually defined, so a role spec omitting max_tokens
cannot book a zero completion bound while the source reads as if a route
fallback protected it.

Evidence, already committed:
  - experiments/2026-08-23-fix-reservation-bound-authority/DIAGNOSIS.md Step 3,
    final paragraph -- the getattr/None analysis.
  - experiments/2026-08-23-fix-reservation-bound-authority/repro/
    cap_divergence.py, case "role spec omits max_tokens": booked 0.
  - src/deepreason/llm/endpoints.py:261,275 and src/deepreason/llm/adapter.py
    :1710 -- where the None originates.
  - src/deepreason/llm/adapter.py::LLMAdapter._completion_cap -- the one
    definition to change.

Read first: docs/map/SEAM-llm-x-workflow.md (its Traps entry on the single cap
definition -- do NOT reintroduce a second expression to fix this), and
docs/map/SUB-llm.md.

Design question the tranche must answer, not assume: whether the right value is
`lease.route.max_tokens` when the endpoint's is None (making the fallback real),
or whether a None endpoint cap on a route with no declared allowance should be
a typed refusal at build_adapter time. The all-configurations law (CLAUDE.md,
2026-08-12) says compile never refuses, so the second is likely wrong at
compile and right at first use -- price both.

End state: a regression test pinning the chosen value for a route with no
context_window_tokens and an endpoint carrying max_tokens=None; full gate 0
failed.
```

---

## P2-bound — nothing checks that a census could have found what it reports missing

**What:** `ERRATA` E47 records that P6-epoch3's elimination scanned for
`"max_tokens": <n>` over a root whose controller policy spells the value
`"cap:conjecturer": 20480` inside an `inline:` JSON string. The search could not
have succeeded, and its empty result was read as a negative finding for a day.
E42 is the same failure with a different key. The lesson is now written down
twice and mechanised zero times.

```
Route: dr-change-orchestrator (change; tooling plus one map document).

One goal: give a census over typed records a cheap way to state which record
types it read, so an empty result is distinguishable from a search that could
not have found anything.

Evidence, already committed:
  - docs/ERRATA.md E47 (this failure) and E42 (the same shape, joined on the
    convenient key rather than the frozen one).
  - experiments/2026-08-23-fix-reservation-bound-authority/repro/
    attempt3_census.py -- a census that DOES enumerate its record types
    (_objects(root, kind) per kind) and can serve as the shape to generalise.

Read first: docs/map/SCHEMA.md (the check: contract) and CLAUDE.md's evidence
conventions ("Accepted does not mean true").

Design question the tranche must answer, not assume: whether this is a helper
in tools/ that lists a root's object kinds and warns when a census names none
of them, or purely a documented recipe (REC-) for writing one. The authoring
-skills E1 tripwire applies: do not build a workflow for this before two
recorded recipe failures -- there are now two recorded CENSUS failures, which is
not the same thing.

Do NOT respond by adding a rule that all censuses must be reviewed. The failure
was not inattention; both censuses were careful and both were wrong about their
own coverage.

End state: an instrument or recipe that would have caught E42 and E47,
demonstrated against both roots.
```

---

## Not parked here

**P5-epoch3** (whether a token-bounded run should reach a resumable terminal)
stays where it is, in
`experiments/2026-08-22-change-epoch3-second-lineage/PARKED.md`. It lives in the
same two files this tranche touched and was deliberately not folded in.
