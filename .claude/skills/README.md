# The DeepReason skill set — how the workflow is organised

Repo law (CLAUDE.md): route ALL substantive work through one of the two
workflow families. One tranche, one goal; every tranche lives in
`experiments/<date>-<slug>/` and its ledger is the authority for that work.

## Family 1 — something is broken or suspicious

Entry point: `deepreason-orchestrator`. Phases in order, one artifact each:

| Phase | Skill | Owns the artifact |
|---|---|---|
| 1 | `dr-set-goal` | GOAL.md — one bounded, falsifiable goal |
| 2 | `dr-diagnose` | DIAGNOSIS.md — one cause, from the record first |
| 3 | `dr-reproduce` | REPRO.md — the defect demonstrated offline |
| 4 | `dr-propose-fix` | FIX.md — smallest correct fix, no code yet |
| 5 | `dr-implement-fix` | the fix commit + regression test + map update |
| 6 | `dr-verify-outcome` | VERIFY.md — PASS/FAIL against GOAL.md |

## Family 2 — the operator suggests a change

Entry point: `dr-change-orchestrator`. The authority is the operator's
verbatim words, ledgered in REQUEST.md; every artifact cites R-numbers.

| Phase | Skill | Owns the artifact |
|---|---|---|
| 1 | `dr-capture-request` | REQUEST.md — verbatim words, split into Rs |
| 2 | `dr-spec-change` | SPEC.md — interpretation, in writing |
| 3 | `dr-plan-steps` | CHECKLIST.md — ordered steps, one criterion each |
| 4 | `dr-execute-step` | one checked step per invocation (the only skill in this family that may modify the tree) |
| 5 | `dr-validate-change` | VALIDATION.md — every acceptance check re-run |
| 6 | `dr-deliver-change` | DELIVERY.md — R-by-R reconciliation |

## Cutting across both families

| Skill | Load when |
|---|---|
| `dr-drive-harness` | starting any session that runs, modifies, or diagnoses the harness — the driving manual: preflight, CLI lifecycle, ladders, and where to look (map order, frozen surfaces, record-first diagnosis) |
| `dr-ask-the-right-question` | an operator message is ambiguous or terse; any phase says "stop and ask"; evidence contradicts expectation — routes questions to the cheapest authority (record → framework → operator) |

## The rules that hold it together

- Cross-routing is strict: a defect found mid-change is PARKED, not
  fixed; a change wished for mid-defect is PARKED, not implemented.
- Both families begin with a MAP PREFLIGHT (`docs/map/INDEX.md` →
  `INV-frozen-surfaces.md` → the seam document,
  `docs/map/SEAM-<a>-x-<b>.md`, before either subsystem; recipe:
  `docs/map/REC-change-a-seam.md`).
- The map moves in the SAME commit as the code it describes.
- Commit and push the tranche directory at every phase boundary — the
  container can vanish at any time.
- Where the truth lives: CLAUDE.md (law) → `docs/map/INDEX.md`
  (navigation) → `experiments/*/RESULTS.md` (what is proven) →
  `docs/ERRATA.md` (what was corrected) → each tranche's PARKED.md
  (what is deliberately not done).
