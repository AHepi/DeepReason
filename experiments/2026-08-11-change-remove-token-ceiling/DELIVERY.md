# Delivered: remove the 200k per-run token limit
Branch: claude/remove-token-ceiling-w8k3mf @ effbbd1f4b9b11755b50b8e3a61d20241c601ed9 (pushed, tree clean)

## What changed

The 200,000-token ceiling on a run's total token budget is gone. Every
site that enforced it has been found and removed: `preparation.py`'s
`PUBLIC_MAX_TOKEN_BUDGET` constant and the validator branch that rejected
budgets above it (the public `deepreason reason` command and the MCP
`start_run` tool both route through this one validator); the intake
form's separate `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` check;
`shallow.py`'s own, independent `SHALLOW_MAX_TOKEN_BUDGET` (the reduced
"MiniReason" fallback engine had its own copy of the same ceiling); and
the MCP tool schema's advertised `"maximum"` value, which would otherwise
have kept describing a ceiling that no longer exists. The only rule left
on a token budget is that it be a positive whole number — an operator can
now ask for any budget size. `docs/AGENT.md`'s public operating guide was
updated to say so. A related documentation gap turned up while scoping
this change (`docs/map/`, the navigation layer over the codebase, had
never recorded who owns `intake_form.py` and `shallow.py`) and was closed
in the same commit as the behavior change, as the map's own rules
require.

Along the way, the full test suite caught one thing the initial search
missed: a test that hardcoded the number `200001` instead of referring to
the ceiling by name, so it didn't show up in a name-based search. That
test has been split into two — one still proving the *cycle*-count limit
(12 cycles, unrelated and untouched) still works, and a new one proving a
budget request over the old token ceiling now succeeds instead of being
refused.

Nothing that stores or replays a run's permanent record was touched. A
mechanical check compared the four files that record and verify a run's
history byte-for-byte before and after this change, and a real, already-
completed run was re-verified byte-identical before and after — proof
that no past run's saved outcome changed meaning.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "gets rid of the 200k token limit per run" | done | commits `6a488b97e`, `d4e146b55`; VALIDATION S1-S4 |
| R2 | "locate EVERY site that enforces a 200,000-token per-run budget ceiling ... and remove the ceiling" | done | commits `6a488b97e`, `d4e146b55`, `45e544f4b`; VALIDATION S1-S5 + Requirement sweep |
| R3 | "Per-call completion caps and all OTHER ceilings are out of scope; only the per-run token budget ceiling goes" | done | VALIDATION R3: `PUBLIC_MAX_CYCLES`, `PACK_TOKEN_BUDGET`, `Route.max_tokens`/`context_window_tokens`, `config.py` all confirmed untouched |
| R4 | frozen surfaces 3/4 touchable "IF AND ONLY IF the ceiling lives there... only in the widening direction" | done (not exercised) | VALIDATION Frozen surfaces: empty diff on all five surfaces — the ceiling never lived there, so the grant was never needed |
| R5 | "readers must widen, never narrow ... the tranche proves it" | done | VALIDATION S11: `verify_root_report` byte-identical before/after on a real committed root |
| R6 | "surface-4's own trap: change the Pydantic model AND its validator together" | done (not applicable) | VALIDATION S13/S12: surface 4 not touched, so the trap does not apply — recorded rather than silently skipped |
| R7 | "if IntakeFormV1's schema changes, the MCP schema sha moves — update ALL FOUR pin locations ... regenerate FORM_DR1" | done | commit `6a488b97e` (both wheel-smoke pins); VALIDATION S8/S8b/S9 — 2 of the 4 named pins actually needed the edit (the other 2 pin the MCP tool-NAME set, unaffected by this schema-property change; traced, not silently skipped) |
| R8 | "if removing the ceiling drifts the qualification subject digest, REPORT the requalification consequence" | done | VALIDATION S10: no contact found — reported as none, not silently assumed |
| R9 | errata check: "search committed documents ... If a committed document claims removal that never shipped, that is a docs/ERRATA.md entry ... If no such claim exists, 'errata: none'" | done | VALIDATION S6 — search found no such claim; see Errata section below |
| R10 | "affected-test ring while iterating; full gate once at the boundary" | done | CHECKLIST steps 9/13/13b/14; VALIDATION Full gate (run twice — once catching a real regression, once confirming the fix) |
| R11 | "docs_verify full (baseline: 3 pre-existing shallow-clone failures)" | done | VALIDATION Map: `3 failed`, exactly the named baseline, 0 new |
| R12 | "Map moves in the same commit as code" | done | commit `6a488b97e` carries both the behavior code and (via a follow-up same-tranche commit `d4e146b55`) the map ownership fix, both authored before validation |
| R13 | "Commit and push every phase boundary (retry 2s/4s/8s/16s)" | done | full `git log` on the branch — a commit + push at every phase and execution checkpoint |
| R14 | "Deliver with R-by-R reconciliation" | done | this table |
| R15 | "no stops" / C3 pre-answered authority | done | 0 operator stops across 26 checklist steps, 1 amendment, and 6 workflow phases |

## Assumptions the operator may override

A1: `SHALLOW_MAX_TOKEN_BUDGET` (the reduced-engine `--shallow` mode's own,
separate copy of the same ceiling) was read as in-scope and removed
alongside the others, even though SCOPE's example list didn't name
`shallow.py` by file. If shallow mode was meant to keep a budget cap,
that is a one-line revert (`experiments/2026-08-11-change-remove-token-
ceiling/SPEC.md` S3).

A2: "config validation" and "CLI argument validation" (SCOPE's phrasing)
both turned out to be the SAME enforcement site — `preparation.py`'s one
validator, which every public entry point (the `reason` command, MCP's
`start_run`) routes through. There was no separate ceiling anywhere in
`config.py` or in the CLI's own argument parsing to find or remove.

## Map delta

Changed: `docs/map/SUB-application.md` (`Owns:` header gained
`src/deepreason/intake_form.py`, `src/deepreason/shallow.py` — both were
touched by this tranche and previously owned by no map document).
Created: none. New checks: 0 (reasoning in VALIDATION.md's Map section:
the map never encoded the 200k ceiling as a checkable claim to begin
with, so there was nothing to invert, and the `Owns:` addition is a
structural ownership fact, not a new falsifiable behavioral claim).
`docs/AGENT.md` was also updated, but it is the public operating guide,
not a `docs/map/` document. Left stale: none (`docs_verify --stale`
reports 0 documents worth re-reading).

## Errata

errata: none. R9's search (`docs/TOKEN_ECONOMY.md`, every tranche
`DELIVERY*.md`/`RESULTS.md`, `docs/proposals/`, plus every doc matching a
loose "200,000"/ceiling pattern) found no committed document claiming
this ceiling was already removed or scheduled for removal. The operator's
own recollection ("It should have been removed, but is still there") does
not correspond to any written prior claim — it stands as the operator's
account, not a documented-and-broken promise, so no `docs/ERRATA.md`
entry was warranted.

## Parked (not done, not promised)

none — no defect or neighboring improvement was found and set aside
during this tranche; everything discovered (the `test_public_v6_facade.py`
gap) was in R1/R2's own scope and fixed as Amendment 1, not parked.
recommended next: none.
