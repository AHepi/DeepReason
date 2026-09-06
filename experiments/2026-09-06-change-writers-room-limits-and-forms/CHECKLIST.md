# CHECKLIST — the writer's room: limits, forms, census
State: next=1 blockers=none. Captured and specified 2026-09-06 on the operator's message 4 ("the limits need changing … permission to change the forms … only if the commitments exist outside conjecture artifacts"). R4 verified on the record before any step.

Re-read REQUEST.md + SPEC.md before every step. One step per invocation.
Map ids: DR-SUB-minireason, DR-SEAM-llm-x-minireason, DR-INV-seat-section-plugins, DR-INV-seat-section-sources, DR-CON-packs-and-token-economy, DR-INV-frozen-surfaces.

## T1 — the limits (S1)
- [ ] 1. (S1c) Red test first: a synthetic run whose everything section grows past the limit; assert every brief ≤ limit and every seat's directive byte-intact. done-when: 1 failed on the current allocation (paste).
- [ ] 2. (S1a) Reserve the mandatory sections; the free section gets the remainder; the notice is a count plus ≤3 ids. done-when: step-1 test green; `mini/tests/` 0 failed.
- [ ] 3. (S1b) Shallow forwards `model_profile`; `MiniFlowV1.brief_budget_chars`. done-when: `tests/test_shallow_reason.py` + mini ring 0 failed; a test shows a flow-declared budget wins.
- [ ] 4. [COMMIT] map (SUB-minireason, SEAM-llm-x-minireason Traps: P12 fixed), blast_radius CLEAR, diff_budget.

## T2 — the forms (S2)
- [ ] 5. Register the three room forms and `mini.flow.room.v1`; the seat's task in each schema description. done-when: registry lists them; the enumeration test covers them; ring 0 failed.
- [ ] 6. End-to-end room run against the stub: three kinds land; both goldens byte-identical. done-when: paste.
- [ ] 7. [COMMIT] map rows, blast_radius CLEAR, diff_budget.

## T3 — R4 enforced (S3)
- [ ] 8. `test_mini_room_separation.py`, mutation-proven. done-when: red under the planted write, green otherwise (paste both).
- [ ] 9. [COMMIT].

## T4 — the census (S4)
- [ ] 10. [COMMIT] `PREREG_CENSUS.md` + `census.py` sealed (sha in the message) before the run.
- [ ] 11. Live room run, 3 cycles, detached; typed terminal; directive intact 19/19. done-when: paste.
- [ ] 12. [COMMIT] `census.py` → RESULTS.md, the commitment seat first, every proposal quoted.
- [ ] 13. [COMMIT] VALIDATION.md (full gate, idle) + DELIVERY.md; push; clean.
