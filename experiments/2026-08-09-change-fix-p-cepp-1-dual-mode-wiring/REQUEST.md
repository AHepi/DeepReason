# Request: fix dual seat wiring and test with a short live run
Captured: 2026-08-09, from the operator's message immediately following
the CP1-M tranche's final delivery message (which itself recommended
"fixing P-CEPP-1's wiring looks worth it... decision is the operator's").

## Verbatim

> fix dual seat wiring and test with a short live run. Read Claude.md
> first

The only prior operator words that give "dual seat wiring" its referent
are the ORIGINAL task instruction that opened the CP1-M tranche (same
conversation, same operator authority chain):

> Also read the patrol RESULTS.md's non-determinism correction... The
> dual-mode verdict — can models author working checkers for real
> historical claims, rates by model, and therefore is fixing P-CEPP-1's
> wiring worth it (recommendation, decision the operator's)

and CP1-M's own closing recommendation (this session's prior turn,
addressed to the operator, answered with "yes... my recommendation is
that fixing P-CEPP-1's wiring is worth doing — the decision is yours"),
which the operator's "fix dual seat wiring" message is a direct reply
to authorizing.

## Requirements

R1 (behavior): "fix dual seat wiring" — read, per the referent chain
above, as: fix P-CEPP-1 (`experiments/2026-08-08-corpus-enrichment-
patrol-pilot/PARKED.md`'s own ready-to-send prompt: "Wire
`conjecturer.turn.v7` to a real `ContractSchemaRepairGrantV1` in
`_compile_contract_schema_repair_policy` (`run_manifest.py:2473`) so a
live run configured for v7 can actually validate and dispatch a
`program:candidate_checker` eval-kind commitment through the `encoder`
seat").

R2 (process): "test with a short live run" — a live (not offline-only)
harness run must be executed after the fix lands, configured to
exercise the newly-wired path, and its outcome reported.

R3 (process): "Read Claude.md first" — CLAUDE.md must be (re-)read
before acting on R1/R2.

## Standing constraints

C1: CLAUDE.md (checked into the repo, binding on every session per its
own header and the system prompt's framing) — "Frozen surfaces (never
touch without explicit operator approval)" names `src/deepreason/
run_manifest.py` among files never touched without explicit operator
approval; R1 requires touching exactly that file. This request IS the
explicit approval for this specific, named change.

C2: CLAUDE.md — "Iterate on the RING, gate at the BOUNDARY... run the
affected test files while iterating, and the whole suite only at a
phase boundary" and "Gate discipline: 0 failed is the only acceptable
result."

C3: CLAUDE.md — "Commits: one defect or one change per commit; message
states what, why, the live evidence (run ids), and 'Full gate: N passed,
0 failed' when code changed. Push with retry (2s/4s/8s/16s backoff)."

C4: CLAUDE.md — "The map moves in the SAME COMMIT as the code — a
separate 'update docs' commit is the commit that gets dropped."

C5: CLAUDE.md, Live runs section — "Launch detached, never foreground:
... Arm the snapshot loop and a monitor" and "Judge only typed
outcomes: run state, stop_reason, the ladder's audit JSON, `verify_root`,
FINDINGS.md" — governs how R2's live run must be conducted and judged.

## Open questions (for dr-spec-change)

Q1: "a short live run" does not specify which question, how many
cycles/tokens, which models/seats, or which operator key to use. CP1-M's
own env file
(`experiments/2026-08-09-cp1m-stratification-retrodiction/env`) already
holds both verified-working operator keys in this container — reusable,
or the operator may want a fresh/different key for this test.

Q2: The exact shape of the `ContractSchemaRepairGrantV1` for v7 (ceiling
value, whether it mirrors v6's `CONJECTURE_SCHEMA_REPAIR_CEILING`
exactly or needs its own) is not specified by the operator's words —
`PARKED.md`'s ready-to-send prompt says only "a real
`ContractSchemaRepairGrantV1`", not its parameters.

Q3: Whether "test with a short live run" means ANY live run that reaches
a v7-configured manifest and dispatches a `program:candidate_checker`
commitment (minimal proof), or specifically a run that produces a
CONFIRMED/refuted verdict via the dual-mode channel (a stronger,
costlier proof) — the operator's words underdetermine which bar counts
as "tested."

## Amendments

(none yet)
