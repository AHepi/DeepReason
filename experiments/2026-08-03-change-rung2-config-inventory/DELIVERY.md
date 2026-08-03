# Delivered: rung 2, tranche 1 — buried choices become visible switches (inventory)
Branch: `claude/delivery-rungs-handover-m22sdy` @ `d9b40d42` (pushed, tree
clean).

## What changed

`experiments/2026-08-03-change-rung2-config-inventory/INVENTORY.md` now
lists twelve hard-coded behavior-choice candidates that could become
named `Config` values, grouped by shape: five preset-level mode/boolean
switches with no `Config` home at all (Group A, including
`engaged_criticism_policy`'s `authority="observe_only"` — rung 2's own
named example); a distinct finding not anticipated going in (Group B) —
`config.py` already declares `BridgeConfig` as a typed home for exactly
the bridge preset's shape, but `v6_policy.py::engaged_bridge_source()`
bypasses it with a hard-coded dict whose values differ from
`BridgeConfig`'s own defaults on three of five fields; six env-var-sourced
switches that parallel `Config` without going through it (Group C); and
one item of hard-coded content that is not actually a mode switch (Group
D, `STANCE_LIBRARY`). Every pointer was checked twice — once during
execution, once fresh during a from-scratch second validation pass — and
one genuine inaccuracy was caught and fixed along the way (see below). No
`src/` file changed; no `docs/map/` document changed. This tranche stops
here, as instructed: the inventory is presented for review, and no switch
— including the named `engaged_criticism_policy` one — is built until the
operator picks a candidate.

This tranche's own validation pass caught a real mistake in its own
deliverable: `INVENTORY.md` initially named one candidate's environment
variable `DEEPREASON_DISABLE_V6_LAUNCH_ENV`, a string that does not exist
anywhere in the source — the actual value read from `os.environ`
(`runtime/launch_policy.py:22`) is `DEEPREASON_DISABLE_V6_LAUNCHES`. The
error came from conflating the Python constant's NAME
(`V6_LAUNCH_DISABLE_ENV`) with the STRING it holds. `dr-validate-change`'s
own re-verify-fresh discipline found it on the first validation pass; a
narrow re-plan fixed the one line and a second, from-scratch validation
pass re-checked all twelve pointers (not a sample) to confirm nothing else
had the same problem. Logged as `docs/ERRATA_EXECUTOR.md` X5 (the
validation FAIL loop firing correctly a second time, on a different defect
class than rung 1's).

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Gather the hard-coded behavior choices that could become named Config values" | done-with-assumption A1 | commits `fb63d271` (findings), `835248fb` (correction); VALIDATION.md S1, second pass |
| R2 | "Deliverable: the inventory document, with a map/code pointer and current hard-coded value for each candidate" | done-with-assumption A2 | `INVENTORY.md`, all 12 pointers re-verified fresh; VALIDATION.md S1, second pass |
| R3 | "Zero src/ changes in this tranche" | done | `git diff --stat b73db3ba..HEAD -- src/` empty, both validation passes |
| R4 | "THEN STOP. Present the inventory; further switches wait for the operator to pick them. Do not start rung 3 or any other rung." | done | this document; no tranche-2 or rung-3 work anywhere in the tranche's diff, confirmed both validation passes |
| R5 | "one switch: engaged_criticism_policy in v6_policy.py ... becomes a Config value PRESERVING observe_only as the default" | deferred (operator's own words: "TRANCHE 2 — one switch: ...", explicitly split from "TRANCHE 1 — inventory only") | separate, not-yet-opened tranche |
| R6 | "FLIPPING ANY DEFAULT IS THE OPERATOR'S DECISION, NEVER YOURS" | deferred, same as R5 | tranche 2 |
| R7 | "ACCEPTANCE per switch tranche: full gate 0 failed; root sweep byte-identical; a test proving the switch's default equals prior behavior; map updated in the SAME commit as the code" | deferred, same as R5 | tranche 2 |
| R8 | "Route: dr-change-orchestrator, one switch per tranche" (rung 2's own route line for tranche 2) | deferred, same as R5 | tranche 2 |

## Assumptions the operator may override

A1: the sweep is general ("hard-coded behavior choices"), not narrowed
to authority-shaped values, but practically bounded to the three
preset/policy-shaped files (`v6_policy.py`, `runtime/launch_policy.py`,
`capabilities/policy.py`) plus rung 1's five mapped sockets plus
`config.py` as baseline — not an exhaustive scan of all ~125k lines.

A2: the inventory is a plain `experiments/`-tranche Markdown document
(tables: candidate / pointer / value / note), not a `docs/map/SCHEMA.md`-
anatomy document — this is not a load-bearing map claim.

## Map delta

No map change. `git diff --stat b73db3ba..HEAD -- docs/map/` is empty,
confirmed in both validation passes. `docs/ERRATA_EXECUTOR.md` gained one
entry (X5) — outside `docs/map/`, and outside this tranche's own R1-R4
scope, but within the session-wide standing constraint (C3) the operator's
opening message established: log a guardrail that fired as designed.

## Parked (not done, not promised)

See `PARKED.md` in full. Summary: tranche 2 itself (the operator's own
next step); Group B (`BridgeConfig` vs `engaged_bridge_source()` —
flagged as worth explicit attention, since it's a different shape of fix
than Group A's literal switches); Group C's env-var switches (plausibly
`Config`-shaped but a larger invocation-surface question); the two
launch-policy env vars (probably the wrong shape for `Config` at all —
deliberately launch-only rollback levers); `STANCE_LIBRARY` (content, not
a switch); and an unbounded full-repo sweep beyond this tranche's stated
methodology.
