# CHECKLIST — P4

Order is forced by `DR-SEAM-rules-x-workflow` "How to change it": record →
service → replay → rule → recovery. Do not reorder.

| # | Step | Done-criterion | State |
|---|---|---|---|
| 1 | **S1 — the record.** `ContextNamespace.EVIDENCE` + `EVD_` prefix; `plan_kind` gains `"citable"` | A1 | ✅ `tests/test_v6_transaction_qualification.py tests/test_v6_controller3_replay_verification.py` — 39 passed |
| 2 | **S2 — the render split.** `citable_legend(...) -> CitableLegend(text, shown)`; `render_citable_blocks` becomes its wrapper | A2 | ✅ both A2 tests pass |
| 3 | **S3 — the conjecturer half (M1, M2).** Universe unconditional; a `citable` plan built from `shown` and re-filtered against the pack | A3, A4 | ✅ **mutation-checked** — restoring the `bound_dossier is not None` gate fails both |
| 4 | **S4 — layer 3 (M4).** `EVIDENCE_REF_NOT_EXPOSED` + the `exposed_block_ids` binding, read from the receipt | A5, A6 | ✅ three tests pass |
| 5 | **S5 — layer 2 (M3).** `QuotedEvidenceRefV1`; `premise_evidence` on both critic contracts and their wire mirrors | A7, A8 | ✅ `contract_id` values unchanged; wheel smoke green |
| 6 | **S6 — layer 4 (M5, M6).** Critic pack carries the legend under invitation; `_file_attribution` checks and registers; `PremiseAttributionV1.citation_ref`; the compiler's DEPENDENCE | A9, A10, A11 | ✅ all through the real `Scheduler` loop |
| 7 | **S7 — the recovery half.** `nonconjecture_recovery`'s two critic-exposure assertions narrow to SOURCE entries | A12 | ✅ **mutation-checked** — widening `exposed` raises `NonConjectureRecoveryAuthorityError` |
| 8 | **[COMMIT]** map + full gate | map in the same commit; gate 0 failed; docs_verify at baseline; budget measured | ✅ **3682 passed, 7 skipped, 0 failed** (idle); docs_verify 60 docs / 916 checks / 3 failed, all `CON-run-identity`; budget EXCEEDED and disclosed |
| 9 | **A13 — the combined loop proof** | one offline run where a derived problem's conjecturer sees the legend AND a premise attribution is filed with a byte-checked quote | ⚠️ **PARTIAL.** Both halves proven separately, each through a real loop (A3/A4 through `conj` under a v6 manifest; A9/A10 through `Scheduler`). No single run does both — VALIDATION.md "What was not proven" states the consequence |
| 10 | **M7** — A19 stays deferred | recorded; no pilot attempted | ✅ R62's policy block is discharged by this tranche; the credential block stands |

## Map documents moved in the same commit

`SUB-evidence.md` (**new** — the package had no covering document),
`INDEX.md`, `SUB-calculus.md`, `CON-criticism-source.md`,
`SEAM-rules-x-workflow.md`, `SEAM-rules-x-scratch.md`,
`SEAM-schools-x-scratch.md`, `CON-packs-and-token-economy.md`.
