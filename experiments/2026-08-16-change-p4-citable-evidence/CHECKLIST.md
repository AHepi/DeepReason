# CHECKLIST — P4

Order is forced by `DR-SEAM-rules-x-workflow` "How to change it": record →
service → replay → rule → recovery. Do not reorder.

| # | Step | Done-criterion | State |
|---|---|---|---|
| 1 | **S1 — the record.** `ContextNamespace.EVIDENCE` + `EVD_` prefix; `plan_kind` gains `"citable"` | A1: an `EVD_001` item validates in the evidence namespace and is refused in every other; `SRC_001` is refused in the evidence namespace. `python -m pytest tests/test_v6_transaction_qualification.py tests/test_workflow_replay*.py -q` green | ☐ |
| 2 | **S2 — the render split.** `citable_legend(blocks, blobs) -> CitableLegend(text, shown)`; `render_citable_blocks` becomes its wrapper | A2: `shown` contains exactly the blocks whose excerpt is in `text` — a block whose bytes are unrecoverable is in neither | ☐ |
| 3 | **S3 — the conjecturer half (M1, M2).** Universe becomes unconditional; a `citable` plan is appended from `shown` | A3: a DERIVED problem's pack contains the block-id legend. A4: the call's exposure receipt contains one evidence-namespace item per shown block, with the block's `text_sha256` | ☐ |
| 4 | **[COMMIT]** map + ring | `SUB-evidence.md` written and green; `docs_verify --ring`; `python -m pytest tests/test_v6_conjecture*.py tests/test_evidence*.py tests/test_attached_evidence*.py -q` | ☐ |
| 5 | **S4 — layer 3 (M4).** `EVIDENCE_REF_NOT_EXPOSED` + the `exposed_block_ids` binding; the conjecture admission passes the set from the PLAN | A5: a citation to a real dossier block that was not exposed to that call records `EVIDENCE_REF_NOT_EXPOSED`. A6: with the keyword omitted, every existing check is unchanged | ☐ |
| 6 | **S5 — layer 2 (M3).** `QuotedEvidenceRefV1`; `premise_evidence` on the two critic contracts and their wire mirrors | A7: `QuotedEvidenceRefV1(block=..., quote=None)` is a validation error; `EvidenceRefClaimV1` still admits `quote=None`. A8: `contract_id` values are unchanged | ☐ |
| 7 | **S6 — layer 4 (M5, M6).** Critic pack carries the legend under invitation; `_file_attribution` checks and registers; `PremiseAttributionV1.evidence_ref`; the compiler's DEPENDENCE | A9: an attribution filed with a verified quote carries a DEPENDENCE ref onto the citation artifact. A10: an attribution filed with an unverified quote carries none and files the failed check. A11: the premise ref is still MENTION | ☐ |
| 8 | **S7 — the recovery half.** `nonconjecture_recovery`'s two critic-exposure assertions narrow to SOURCE entries | A12: a resumed critic whose call exposed evidence items recovers identically; `python -m pytest tests/test_v6_nonconjecture_recovery.py -q` green | ☐ |
| 9 | **[COMMIT]** map + full gate | map moves in the same commit; `python -m pytest tests/ -q -n 4` 0 failed; `python tools/docs_verify.py` at the 3-failure `CON-run-identity` baseline; `tools/diff_budget.py` measured and disclosed | ☐ |
| 10 | **A13 — the loop proof.** One offline run of the ACTUAL loop where a derived problem's conjecturer sees the legend and a premise attribution is filed with a byte-checked quote | the end-to-end test passes; no hand-built receipt anywhere in it | ☐ |
| 11 | **M7** — A19 stays deferred | recorded in VALIDATION.md; no pilot run attempted | ☐ |
