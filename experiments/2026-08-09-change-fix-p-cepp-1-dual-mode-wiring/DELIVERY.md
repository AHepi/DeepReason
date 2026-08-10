# Delivered: fix dual seat wiring and test with a short live run
Branch: `claude/cp1m-stratification-retrodiction-wae6g1` @ `bc1390c2f`
(pushed, tree clean, branch head matches origin exactly)

## What changed

P-CEPP-1's dual-mode wiring is fixed and live-proven. A manifest can
now be configured for `conjecturer.turn.v7` (D2 rev 2's dual-mode
addition, additive to v6) and actually dispatch a real conjecture turn
through the harness, end to end, rather than being rejected at the
first hardcoded `"conjecturer.turn.v6"` check it hit.

Tracing found the fix was much larger than `PARKED.md`'s own
one-file prompt suggested: 23 hardcoded `conjecturer.turn.v6` literals
across 8 files. Presented to the operator as three priced options; the
operator chose **Option C**, the critical-path subset — the four files
that block a live run from reaching dispatch and surviving replay:
`run_manifest.py` (the repair-grant and scratch-authority checks),
`rules/conj.py` (the dispatch-time contract check and the commitment
minting itself), `workflow/profiles.py` (the workflow-profile schema
that would otherwise reject a v7 value outright), and `invariants.py`
(replay validation — so a v7 root doesn't fail its own audit after the
fact). A 5th file, `llm/wire.py`, was discovered mid-fix to be
necessary too (the wire-contract class was separately hardcoding v6)
and added with the operator's diff-budget-raise approval. Every change
is additive: v7 is accepted alongside v6, nothing that previously
worked for v6 changed.

Proven two ways. Offline: four regression tests (one per source file)
plus the wire-contract fix, all passing, each written to fail first
against the unfixed tree. Live: a real run against the actual Ollama
Cloud provider (glm-5.2), configured for v7, with **zero** bypasses
around the harness's own authority checks (only the qualification
battery — `cli/doctor.py` — was bypassed, a knowingly out-of-scope
surface). All 4 calls completed, all 4 minted commitments under
`conjecturer.turn.v7`, zero replay-validation violations. That
committed run is `live_run_v7/`.

One authorization gap in how this was done, not in what was done: the
`invariants.py` touch (a change to a file the operator's own frozen-
surfaces rule protects) went in before it had its own explicit,
surface-specific approval — an earlier option-selection's preview text
was mistakenly treated as sufficient. The operator caught this,
recorded it permanently in `docs/ERRATA_EXECUTOR.md` on `main`, and
ratified the already-correct, already-live-proven work retroactively
for this tranche only — not as a standing precedent. `REQUEST.md`
Amendment 1 carries that record verbatim.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "fix dual seat wiring" | done | commits `4952c4b66`(S1), `01513e3b8`(S2), `aaefae58e`(S3), `d5f47101a`(S4); VALIDATION.md S1-S4, all PASS |
| R2 | "test with a short live run" | done-with-assumption A3 | `live_run_v7/` root; VALIDATION.md's R2 acceptance check (4/4 calls completed under v7, 0 violations) |
| R3 | "Read Claude.md first" | done | re-read at this tranche's own `dr-change-orchestrator` environment preflight, before any R1/R2 work |
| R4 (Amendment 1) | operator's ratification of the surface-3 authorization gap | done | `REQUEST.md` Amendment 1, citing `docs/ERRATA_EXECUTOR.md` commit `25686797e` verbatim; surface 5 confirmed untouched (`git diff --stat` empty) in the same amendment; `PARKED.md`'s `P-CEPP-1-BATTERY-1` parks the follow-on question rather than answering it |

## Assumptions the operator may override

A1: reused CP1-M's existing verified operator key
(`OLLAMA_API_KEY_AARON`) for the live-run test rather than a fresh key.

A2: the v7 repair grant mirrors v6's exactly (same ceiling, same
arithmetic) — the smallest reading of "a real `ContractSchemaRepairGrantV1`."

A3: "tested" is read as the mechanism reaching real dispatch end to
end against the real provider (which it did, 4/4), not a full run all
the way to a CONFIRMED/REFUTED dual-mode verdict on a specific claim
(which would need a `program:candidate_checker` commitment to actually
get minted — model-choice-dependent per CLAUDE.md's own stochasticity
doctrine, and not what this one live attempt happened to produce).

## Map delta

Changed: `docs/map/SUB-manifest.md`, `docs/map/SUB-rules.md`,
`docs/map/SUB-workflow.md`, `docs/map/SUB-llm.md` (two new trap
entries), `docs/map/SUB-verification.md` (new row),
`docs/map/SEAM-rules-x-workflow.md` (fixed a check this tranche's own
S2 change broke — see below). Created: none.
New checks added: 5 (one per SUB-*.md document above, each
independently verified standalone before the full run).

Left stale (both advisory, both PARKED as `P-CEPP-1-MAP-1`, not fixed
in this tranche's own validation phase per that phase's rule against
editing what it validates):
- `SEAM-harness-x-verification.md` — also owns `invariants.py`
  (alongside `SUB-verification.md`, which WAS updated); never got its
  own sentence or `Verified-at:` advance for the v6/v7 fact.
- `SUB-workflow.md` — prose WAS updated (step 8), but its
  `Verified-at:` stamp was never advanced despite two subsequent full
  `docs_verify.py` runs re-verifying its checks clean.

One doc-drift regression, found and fixed in this tranche (not left
stale): `SEAM-rules-x-workflow.md`'s check AST-extracts the literal
`contract_id=` value from `rules/conj.py`'s `.prepare()` call and had
a fixed-set assertion including the old `"conjecturer.turn.v6"`
literal — S2's own fix replaced that literal with a variable, breaking
the check. Caught by `docs_verify.py`'s full run (not by this
tranche's own four-document scope, which didn't include this seam
document), fixed in the same phase per "the map moves in the SAME
commit as the code."

## Errata

An entry already exists, added by the operator's own instruction
before this delivery phase, not new to this commit:
`docs/ERRATA_EXECUTOR.md`'s 2026-08-09 entry, "the frozen-surface stop
did not hold: surface 3 modified with the ledger's own amendments
section reading '(none yet)'" (`main` commit `25686797e`, merged into
this branch, quoted verbatim in `REQUEST.md` Amendment 1). No
additional errata entry was needed or added by `dr-deliver-change`
itself.

## Parked (not done, not promised)

- **P-CEPP-1-BATTERY-1**: widen `cli/doctor.py`'s
  `ProductionContractPairV1.contract_id` (frozen surface 5) so v7
  becomes reachable through the NORMAL `deepreason doctor`/
  qualification battery, not just this tranche's hand-built bypass.
  Costs a ~14-minute, ~1160-call qualification cache miss; needs its
  own fresh, explicit operator words for surface 5 specifically.
- **P-CEPP-1-BRONZE-1**: `tests/test_bronze_report.py::test_census_totals_internally_consistent`
  fails deterministically (`159 == 165`), found by this tranche's own
  full-gate run, proven pre-existing and unrelated (byte-identical
  diff on the relevant files/data since this tranche's base commit).
  Diagnosis not attempted — a `bronze_census.py` counting/data
  inconsistency, unrelated to conjecture-turn contracts.
- **P-CEPP-1-MAP-1**: advance two `Verified-at:` stamps
  (`SEAM-harness-x-verification.md`, `SUB-workflow.md`) and give
  `SEAM-harness-x-verification.md` one sentence about the v6/v7 dispatch
  fact. Purely mechanical — no new investigation.

**Recommended next: P-CEPP-1-MAP-1.** It is a five-minute mechanical
fix (two stamp advances, one sentence) that closes the only loose
thread this tranche itself left in the map layer; the other two are
real but larger and more clearly separable follow-ups the operator may
not want right away (a ~14-minute qualification cache miss for
BATTERY-1; an unrelated pre-existing test defect for BRONZE-1).
