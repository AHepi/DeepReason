# Request: rung 2, tranche 2 — the engaged_criticism_policy Config switch
Captured: 2026-08-03. Authority is two sources, both quoted verbatim: (1)
the rung-2 opening message's TRANCHE 2 text, first captured in
`experiments/2026-08-03-change-rung2-config-inventory/REQUEST.md` and
re-quoted here so this tranche is self-contained; (2) this session's
clarifying exchange that authorized opening this tranche now, ahead of
the operator's "TRANCHE 3" message which named it as a precondition.

## Verbatim

> TRANCHE 2 — one switch: engaged_criticism_policy in v6_policy.py
> (hard-coded observe_only) becomes a Config value PRESERVING observe_only
> as the default. Creating the switch is in scope. FLIPPING ANY DEFAULT IS
> THE OPERATOR'S DECISION, NEVER YOURS.
>
> ACCEPTANCE per switch tranche: full gate `python -m pytest tests/ -q -n 4`
> 0 failed (never bare pytest); root sweep `python tools/root_sweep.py`
> byte-identical before/after (42 rows, 11 ERROR expected — see ERRATA
> E5/E6/E8 before interpreting it); a test proving the switch's default
> equals prior behavior; map updated in the SAME commit as the code.
>
> CONSTRAINTS: frozen surfaces bind everything
> (docs/map/INV-frozen-surfaces.md). One rung per tranche; never let a
> tranche touch two rungs. Known flake:
> test_grounded_counterexample_recovery_does_not_invent_override_on_repeat
> can fail once under -n 4; rerun before diagnosing. Commit and push at
> every phase boundary. PARKED.md holds everything noticed but not done.
> Stop conditions are hard stops. Where a spec is silent, load
> dr-ask-the-right-question and route the question to the cheapest
> authority — do not improvise.
>
> — operator's rung-2 opening message, first captured in
> `experiments/2026-08-03-change-rung2-config-inventory/REQUEST.md`

> The known first candidate: `engaged_criticism_policy` authority in
> `v6_policy.py` (hard-coded observe_only) — NOTE: creating the switch
> with the current default is EXECUTE; flipping any default is the
> operator's decision, never yours.
>
> — `docs/HANDOVER_2026-08-03.md`, "The program: seven rungs, in order",
> rung 2

> Operator authorization for rung 2, TRANCHE 3 (after the
> engaged_criticism_policy switch tranche is delivered — never in the
> same tranche as it).
>
> — operator's message opening this session's continuation, before this
> tranche existed

> Do the switch tranche first. Be read Claude.md first
>
> — operator's answer to my clarifying question (I had checked both
> branches' records, found no engaged_criticism_policy switch tranche had
> ever been opened despite the "TRANCHE 3" message naming it as a
> precondition, and asked how to proceed)

## Requirements

R1 (behavior): "one switch: engaged_criticism_policy in v6_policy.py
(hard-coded observe_only) becomes a Config value PRESERVING observe_only
as the default."

R2 (process): "Creating the switch is in scope."

R3 (process): "FLIPPING ANY DEFAULT IS THE OPERATOR'S DECISION, NEVER
YOURS."

R4 (process): "full gate `python -m pytest tests/ -q -n 4` 0 failed
(never bare pytest)."

R5 (process): "root sweep `python tools/root_sweep.py` byte-identical
before/after (42 rows, 11 ERROR expected — see ERRATA E5/E6/E8 before
interpreting it)."

R6 (artifact): "a test proving the switch's default equals prior
behavior."

R7 (process): "map updated in the SAME commit as the code."

R8 (process): "Do the switch tranche first." — this tranche's own
authorization to proceed now, ahead of tranche 3.

## Standing constraints

C1: "frozen surfaces bind everything (docs/map/INV-frozen-surfaces.md)."

C2: "One rung per tranche; never let a tranche touch two rungs." — this
tranche is rung 2 only, and this specific switch only (not the bridge
unification named in the operator's "TRANCHE 3" message, which is
explicitly a separate, later tranche).

C3: "Known flake:
test_grounded_counterexample_recovery_does_not_invent_override_on_repeat
can fail once under -n 4; rerun before diagnosing."

C4: "Commit and push at every phase boundary."

C5: "Stop conditions are hard stops. Where a spec is silent, load
dr-ask-the-right-question and route the question to the cheapest
authority — do not improvise."

C6: "Be read Claude.md first" — done this session before this tranche
opened.

C7: "docs/ERRATA_EXECUTOR.md now has a numbering rule — your entries use
XE<n> ids from now on (XE1 next), never X<n>." — operator's message
opening this session's continuation. Binding on this and all future
tranches this session; not itself a requirement of this tranche's
deliverable, but a standing constraint on how I ledger observations
about it.

## Open questions (for dr-spec-change)

Q1: R1 says "becomes a Config value" — no field name is specified. The
existing precedent (`ARGUMENTATIVE_AUTHORITY`, `TEXT_RUBRIC_AUTHORITY`,
etc.) and INVENTORY.md's own Group A naming ("Criticism authority") don't
pin an exact identifier.

Q2: R1/R6 require "a test proving the switch's default equals prior
behavior" — no specific test file or assertion shape is given. Does this
mean a NEW test, or extending an existing test that already exercises
`engaged_criticism_policy`/`_config_for_profile`?

Q3: `CriticismPolicyV1.authority` is a frozen 2-value manifest `Literal`
(`observe_only`/`defended_trial`). R1 is silent on whether the new
`Config` field's own value-space should mirror those exact two values
(a `Literal["observe_only", "defended_trial"]`) or use a different
vocabulary that then translates — INVENTORY.md's Group A entry flagged
this switch as "no `Config` field exists for this specific preset choice
(unlike `ARGUMENTATIVE_AUTHORITY`, which governs a *different* code path)"
without settling the exact field shape.

## Amendments

(none yet)
