# CHECKLIST — the writer's room: limits, forms, census
State: next=8 blockers=none. T1 and T2 committed; full docs_verify (1419 checks, six known rows) recorded at step 7. Steps 1-3 done (limits fixed, configurable, tested). Captured and specified 2026-09-06 on the operator's message 4 ("the limits need changing … permission to change the forms … only if the commitments exist outside conjecture artifacts"). R4 verified on the record before any step.

Re-read REQUEST.md + SPEC.md before every step. One step per invocation.
Map ids: DR-SUB-minireason, DR-SEAM-llm-x-minireason, DR-INV-seat-section-plugins, DR-INV-seat-section-sources, DR-CON-packs-and-token-economy, DR-INV-frozen-surfaces.

## T1 — the limits (S1)
- [x] 1. (S1c) Red test first: a synthetic run whose everything section grows past the limit; assert every brief ≤ limit and every seat's directive byte-intact. done-when: 1 failed on the current allocation (paste).

      ```
      $ python -m pytest mini/tests/test_mini_brief_limits.py -q     (before the fix)
      E   AssertionError: ['mini:brief-clipped', 'mini:brief-clipped']
      FAILED ...::test_every_brief_fits_and_every_directive_is_intact   -> 1 failed in 1.36s
      RED as predicted: three cycles of long content on compact, two briefs clipped.
      ```
- [x] 2. (S1a) Reserve the mandatory sections; the free section gets the remainder; the notice is a count plus ≤3 ids. done-when: step-1 test green; `mini/tests/` 0 failed.

      ```
      sources.py: `_everything_text` (count + newest 3 ids + "and N more; every id is in the record");
        the section is re-selected until it fits AS RENDERED (header + notice + entries), newest never withheld.
      seats.py: `render_mini_brief` renders once; if over `brief_limit_chars` and the layout has the
        everything section, hands it limit − (everything else) and renders again (floor 400).
      loop.py: supplies `brief_limit_chars` beside the share.
      $ python -m pytest mini/tests/test_mini_brief_limits.py -q  -> 1 passed
      $ python -m pytest mini/tests/ -q  -> 165 passed, 1 skipped   (one test updated to the new
        notice shape, predicted by SPEC S1a: the newest three withheld ids are named, the rest counted)
      ```
- [x] 3. (S1b) Shallow forwards `model_profile`; `MiniFlowV1.brief_budget_chars`. done-when: `tests/test_shallow_reason.py` + mini ring 0 failed; a test shows a flow-declared budget wins.

      ```
      flow.py: `brief_budget_chars: int | None = None`, refused typed if < 1 (MINI_FLOW_BRIEF_BUDGET_INVALID)
      loop.py: prompt_limit = flow's figure or profile preset; token_budget follows it; `_call_stage`
        passes `pack_budget_tokens` -> call.py `call(..., pack_budget=None)` -> `clip_pack(prompt, profile, pack_budget)`
      shallow.py: `frozen_binding["model_profile"] = profile.model_profile` (always forwarded)
      tests: test_a_flow_declared_brief_budget_wins_over_the_profile_preset (9 000 on compact: briefs
        > 4 800 reach the stub whole, no clip marker); test_a_non_positive_brief_budget_is_refused_typed;
        tests/test_shallow_reason.py::test_the_provider_profile_model_profile_reaches_the_engine
        (standard / frontier / compact each reach the engine); three fixed-signature engine stubs
        (two in test_shallow_reason.py, one in test_seat_section_home.py) gain `model_profile`;
        test_the_bare_question_form_is_unchanged now states the new shape.
      $ python -m pytest tests/test_shallow_reason.py -q                  -> 14 passed
      $ python -m pytest tests/test_seat_section_home.py tests/test_shallow_reason.py -q -> 27 passed
      $ python -m pytest mini/tests/ -q                                   -> 167 passed, 1 skipped
      $ python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q -> 15 passed
      ```
- [x] 4. [COMMIT] map (SUB-minireason, SEAM-llm-x-minireason Traps: P12 fixed), blast_radius CLEAR, diff_budget.

      ```
      map: SUB-minireason "The limit, and the reserve rule" (+2 checks: the limits test; render_mini_brief
        reads brief_limit_chars/brief_budget_chars and the FREE_SECTION constants), the flow section
        (brief_budget_chars + typed refusal in the existing check); SEAM-llm-x-minireason: the clip
        paragraph (caller's figure), Traps: the P8 entry gains "THEN IT BIT ANYWAY ... FIXED" (+1 check).
      $ python tools/docs_verify.py --fast  -> 6 failed, the six known rows only (new checks green)
      $ python tools/docs_verify.py --audit -> 1 finding, the known SEAM-llm-x-rules.md:54
      $ python tools/docs_verify.py (FULL)  -> running detached at commit time; result pasted at step 7,
        stamps advanced only then.
      $ python tools/blast_radius.py --files sources.py seats.py loop.py flow.py call.py shallow.py
          --symbols render_mini_brief run_shallow_question _call_stage MiniFlowV1 --against HEAD
        verdict: CLEAR | contacts: [] | adjacent: []      (bare `call` alone gives the known grep false positives)
      $ python tools/diff_budget.py HEAD --ceiling 260 --paths mini/minireason src/deepreason
        {"areas": {"mini/minireason": 102, "src/deepreason": 8}, "total_insertions": 110, "verdict": "WITHIN"}
      $ python tools/diff_budget.py HEAD --ceiling 220 --paths mini/tests tests
        {"areas": {"mini/tests": 131, "tests": 32}, "total_insertions": 163, "verdict": "WITHIN"}
      ```

## T2 — the forms (S2)
- [x] 5. Register the three room forms and `mini.flow.room.v1`; the seat's task in each schema description. done-when: registry lists them; the enumeration test covers them; ring 0 failed.

      ```
      mini_form_ids(): [... 'mini.commitment.room.v1', 'mini.conjecturer.room.v1', 'mini.critic.room.v1' ...] (7)
      resolve_mini_flow('mini.flow.room.v1'): brief_budget_chars 12000, shells seat.mini.{conjecturer,critic,commitment}.room.v1
      schema description (commitment): "COMMITMENT SEAT. Read the TARGET CONJECTURE and propose the commitments ..."
      $ python -m pytest mini/tests/ -q  -> 167 passed, 1 skipped   (the enumeration test iterates every
        registered form, so the three new ones are covered without an edit)
      ```
- [x] 6. End-to-end room run against the stub: three kinds land; both goldens byte-identical. done-when: paste.

      ```
      mini/tests/test_mini_room_forms.py: registered beside the stored ones; the seat's task in each
        schema (and "do not answer the problem" in the commitment seat's); required fields about+body /
        content only, no maxLength; end to end 2 cycles: 4 conjectures, objections + proposals about
        existing conjectures, labels appended to intact prose ([kind: refuted-if], [would settle: ...],
        [angle: mechanism]), "SEAT." on every wire before any brief text, no brief clipped, the critic
        shown no proposal and no objection.
      First run hit a repair prompt (the canonical candidate requires a typicality the room does not
        ask for) -> compile at the neutral 0.5; then:
      $ python -m pytest mini/tests/test_mini_room_forms.py -q  -> 3 passed
      $ python -m pytest mini/tests/ -q  -> 170 passed, 1 skipped
      $ python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py mini/tests/test_mini_flow.py -q -> 24 passed
      ```
- [x] 7. [COMMIT] map rows, blast_radius CLEAR, diff_budget.

      ```
      map: SUB-minireason forms section ("Seven ship", the room forms, the task-in-schema rule, +1 check);
        flow section ("Three ship", the room flow in the existing check). Verified-at on SUB-minireason and
        SEAM-llm-x-minireason advanced to 391d5bb31: the FULL run on that tree ->
        docs_verify [full]: 82 documents, 1419 checks; 6 failed -- the six known rows only.
      $ python tools/docs_verify.py --fast  -> 6 failed (the same six) ; --audit -> 1 finding (the known one)
      $ python tools/blast_radius.py --files forms.py seats.py flow.py --symbols MiniRoomProposals
          MiniRoomCritic MiniRoomConjecturer ROOM_FLOW_ID --against HEAD -> verdict: CLEAR, contacts [], adjacent []
      $ python tools/diff_budget.py HEAD --paths mini/minireason -> 195 insertions (T2); T1 was 110:
        tranche code so far 305 against SPEC's 260 -> EXCEEDED, disclosed and re-baselined in SPEC §Budget
        (the room models carry the seat's task in their docstrings, ~60 lines the estimate did not price).
      $ python tools/diff_budget.py HEAD --paths mini/tests -> 110 (T2); tests so far 273 against 220 -> EXCEEDED, disclosed.
      ```

## T3 — R4 enforced (S3)
- [ ] 8. `test_mini_room_separation.py`, mutation-proven. done-when: red under the planted write, green otherwise (paste both).
- [ ] 9. [COMMIT].

## T4 — the census (S4)
- [ ] 10. [COMMIT] `PREREG_CENSUS.md` + `census.py` sealed (sha in the message) before the run.
- [ ] 11. Live room run, 3 cycles, detached; typed terminal; directive intact 19/19. done-when: paste.
- [ ] 12. [COMMIT] `census.py` → RESULTS.md, the commitment seat first, every proposal quoted.
- [ ] 13. [COMMIT] VALIDATION.md (full gate, idle) + DELIVERY.md; push; clean.
