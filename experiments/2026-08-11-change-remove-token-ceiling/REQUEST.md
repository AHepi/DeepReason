# Request: remove the 200k per-run token limit
Captured: 2026-08-11 from the task-dispatch message (operator authority quoted 2026-08-12) and the enclosing tranche instructions.

## Map preflight (recorded before any other artifact)

Resolved ids (docs/map/INDEX.md routing):
- `DR-CON-run-identity` — owns `src/deepreason/preparation.py`, where `PUBLIC_MAX_TOKEN_BUDGET = 200_000` and its enforcing validator live.
- `DR-SUB-manifest` — **frozen surface 4** (`run_manifest.py` schemas AND validators). Checked: the per-run token ceiling does NOT live in `run_manifest.py`'s `budget_policy` (a free-form dict, no fixed ceiling). Surface 4 is NOT touched by this change unless later investigation finds otherwise.
- `DR-SUB-periphery` — owns `src/deepreason/mcp_server.py`, which republishes `PUBLIC_MAX_TOKEN_BUDGET` as a JSON Schema `maximum` for the MCP `start_run`/`validate_intake` tool's `budget.token_budget` field.
- **Map gap found:** `src/deepreason/intake_form.py` and `src/deepreason/shallow.py` — both top-level files under `src/deepreason/`, both touched by this change (intake form's `token_budget` ceiling validator; the separate shallow-mode `SHALLOW_MAX_TOKEN_BUDGET` ceiling) — appear in NO map document's `Owns:` list. This is a finding, not a blocker (dr-change-orchestrator scope contract); closing it is folded into this tranche's map-move-with-code step.
- `INV-frozen-surfaces.md` read in full before scoping (see SPEC.md's frozen-surface reasoning).

## Verbatim

> Change tranche: remove the 200k per-run token limit. Route through
> dr-change-orchestrator, run all phases through dr-deliver-change WITHOUT
> stopping — the operator has pre-answered the questions below. Do not stop
> to raise concerns; the historical token-expense caution behind this limit
> is explicitly retired by the operator ("tokens are cheap" is standing law,
> CLAUDE.md).

> AUTHORITY for REQUEST.md, operator verbatim (2026-08-12): "gets rid of the
> 200k token limit per run. It should have been removed, but is still there.
> Do not ask other window to raise concern and stop. There are no critical
> cautions except old misdirected concerns about token expense."

> SCOPE: locate EVERY site that enforces a 200,000-token per-run budget
> ceiling — config validation, run_manifest compile/validators, the intake
> form (INTAKE_TOKEN_BUDGET_CEILING and IntakeFormV1's field constraint),
> CLI argument validation, and any doc/map/check that states the ceiling —
> and remove the ceiling (an operator may request any positive budget).
> Per-call completion caps and all OTHER ceilings are out of scope; only the
> per-run token budget ceiling goes.

> PRE-GRANTED (operator's words above are the ledgered approval, scoped to
> this one ceiling): touching frozen surfaces 3 (replay-validation formats)
> and 4 (manifest schema AND validator) is authorized IF AND ONLY IF the
> ceiling lives there, and only in the widening direction. Constraints that
> are law, not cautions: (a) readers must widen, never narrow — every
> committed root (all ≤200k) must replay valid byte-unchanged, and the
> tranche proves it (targeted verify_root_report on a known-good root, plus
> by-inspection: removing an upper bound cannot invalidate a value under it);
> (b) surface-4's own trap: change the Pydantic model AND its validator
> together; (c) if IntakeFormV1's schema changes, the MCP schema sha moves —
> update ALL FOUR pin locations in the SAME commit (scripts/wheel_smoke.py,
> scripts/wheel_operational_smoke.py, tests/test_mcp.py SUPPORTED_TOOLS
> context, tests/test_mcp_help.py — the four-pin lesson, VALIDATION_ii) and
> regenerate FORM_DR1 via tools/render_form_dr1.py --check; (d) if removing
> the ceiling drifts the qualification subject digest, REPORT the
> requalification consequence in DELIVERY.md — do not stop over it.

> ERRATA CHECK (operator: "should have been removed") — search committed
> documents (TOKEN_ECONOMY.md, tranche DELIVERYs, proposals) for any claim
> that this limit was already removed or scheduled for removal. If a
> committed document claims removal that never shipped, that is a
> docs/ERRATA.md entry (next free number — check the ledger tail, it moves)
> in the same commit as the fix. If no such claim exists, "errata: none".

> GATE: affected-test ring while iterating; full gate once at the boundary
> (known baseline: 1 pre-existing test_bronze_report failure; 5 MCP-thread
> timing tests are known-flaky under -n 4 — re-run in isolation before
> attributing). docs_verify full (baseline: 3 pre-existing shallow-clone
> failures in CON-run-identity.md). Map moves in the same commit as code.
> Commit and push every phase boundary (retry 2s/4s/8s/16s). Deliver with
> R-by-R reconciliation; no stops.

## Requirements

R1 (behavior): "gets rid of the 200k token limit per run" — remove
`PUBLIC_MAX_TOKEN_BUDGET`'s 200,000 ceiling enforcement so an operator may
request any positive per-run token budget.

R2 (process): "locate EVERY site that enforces a 200,000-token per-run
budget ceiling — config validation, run_manifest compile/validators, the
intake form (INTAKE_TOKEN_BUDGET_CEILING and IntakeFormV1's field
constraint), CLI argument validation, and any doc/map/check that states the
ceiling — and remove the ceiling."

R3 (behavior): "Per-call completion caps and all OTHER ceilings are out of
scope; only the per-run token budget ceiling goes." (scope fence, not an
obligation to change anything else)

R4 (process): frozen surfaces 3 and 4 may be touched "IF AND ONLY IF the
ceiling lives there, and only in the widening direction."

R5 (process): "readers must widen, never narrow — every committed root
(all ≤200k) must replay valid byte-unchanged, and the tranche proves it
(targeted verify_root_report on a known-good root, plus by-inspection:
removing an upper bound cannot invalidate a value under it)."

R6 (process): "surface-4's own trap: change the Pydantic model AND its
validator together" (conditional on surface 4 actually being touched).

R7 (process): "if IntakeFormV1's schema changes, the MCP schema sha moves —
update ALL FOUR pin locations in the SAME commit (scripts/wheel_smoke.py,
scripts/wheel_operational_smoke.py, tests/test_mcp.py SUPPORTED_TOOLS
context, tests/test_mcp_help.py) and regenerate FORM_DR1 via
tools/render_form_dr1.py --check."

R8 (process): "if removing the ceiling drifts the qualification subject
digest, REPORT the requalification consequence in DELIVERY.md — do not stop
over it."

R9 (process): errata check — "search committed documents ... for any claim
that this limit was already removed or scheduled for removal. If a
committed document claims removal that never shipped, that is a
docs/ERRATA.md entry ... in the same commit as the fix. If no such claim
exists, 'errata: none'."

R10 (process): "affected-test ring while iterating; full gate once at the
boundary" — pytest gate discipline as stated.

R11 (process): "docs_verify full (baseline: 3 pre-existing shallow-clone
failures in CON-run-identity.md)."

R12 (process): "Map moves in the same commit as code."

R13 (process): "Commit and push every phase boundary (retry
2s/4s/8s/16s)."

R14 (process): "Deliver with R-by-R reconciliation; no stops."

R15 (process): "Do not ask other window to raise concern and stop... Do not
stop to raise concerns."

## Standing constraints

C1: "tokens are cheap" is standing law (CLAUDE.md operator design law,
2026-08-08) — cited as the reason the historical caution behind this limit
no longer applies.
C2: "Never NEVER push to a different branch without explicit permission" —
tranche develops on `claude/remove-token-ceiling-w8k3mf` (the dispatch
branch) per the outer task-dispatch instructions.
C3: pre-answered — "Do not ask other window to raise concern and stop.
There are no critical cautions except old misdirected concerns about token
expense" — this closes off the normal stop-and-ask paths for this tranche;
`dr-ask-the-right-question`'s dominance test is satisfied by this
standing answer for any fork this quote already resolves.

## Open questions (for dr-spec-change)

Q1: whether `SHALLOW_MAX_TOKEN_BUDGET` (a distinct 200_000 constant in
`shallow.py`, guarding the *shallow* MiniReason entry point, not the V6
managed-run intake) is "the 200k per-run token limit" R1 refers to. The
words say "per run" without naming which run kind; SCOPE's enumerated site
list (config validation, run_manifest, intake form, CLI) does not name
`shallow.py` explicitly, but it is the same shape of ceiling on the same
quantity (a run's token budget) enforced the same way. Resolved in
dr-spec-change under the dominance test: since C1/C3 retire the caution for
ALL per-run token ceilings and SCOPE says "any doc/map/check that states
the ceiling", not naming shallow.py is an omission of an example, not an
exclusion — both ceilings are in scope.

Q2: what "config validation" (named in SCOPE's site list) refers to,
since no per-run token ceiling was found in `config.py` itself. Resolved
in dr-spec-change by reporting what was actually found instead of what the
prose predicted (record-first discipline).

## Amendments

(none yet)
