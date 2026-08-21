# Checklist for: Rung 3b — the frame-separation invariant

State: next=15 blockers=none. Step 9's STOP is ANSWERED — operator, verbatim,
       "Proceed at 312 (Recommended)", ledgered as REQUEST.md Amendment 1
       (R15/R16). Steps 1-14 complete; VALIDATION.md verdict PASS.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids this plan was built on (`dr-plan-steps` rule 5):
`DR-INV-frozen-surfaces` (read first; forecast CLEAR, computed),
`DR-SUB-calculus` (owns the new module), `DR-CON-standing-and-background`
(owns the standing-axis concept), `DR-SUB-adjudication` (produces `att`/`dep`;
read, never edited), `DR-SUB-ontology`, `DR-CON-warrants-and-attacks`.
No seam document exists for `calculus x adjudication` and none is created —
SPEC.md A3 and REQUEST.md §3 record why; the pair is added to
`SUB-calculus.md`'s `Seams-undocumented:` line in step 5.

- [x] 1. (S5, S6) Write `tests/test_calculus_frame_separation.py` — the gate,
      BEFORE the module it guards. Four tests: the mention/separation exhibit,
      the Theorem 7.3 extension, the violation with its five-way before/after
      capture, the unregistered-endpoint refusal.
      done-when: `python -m pytest tests/test_calculus_frame_separation.py -q`
      -> collection succeeds and every test FAILS on `ModuleNotFoundError:
      deepreason.calculus.separation` (a test that passes here is guarding
      nothing)

- [ ] 2. (S5, S6) [COMMIT] Commit the failing gate alone.
      done-when: `git status --porcelain` empty and `git log --oneline -1`
      names the test file

- [x] 3. (S1, S2, S3, S4) Write `src/deepreason/calculus/separation.py`:
      `_components`, `adjudication_component` (Def 7.1),
      `frame_separated` (Def 7.2), `Consultability`, `consultability` (R64),
      `FRAME_NOT_SEPARATED`, `FRAME_ENDPOINT_UNREGISTERED`, and the SCOPE
      BOUNDARY paragraph in the module docstring.
      done-when: `python -m pytest tests/test_calculus_frame_separation.py -q`
      -> `4 passed`

      DONE. `4 passed in 0.10s`. 111 lines (budgeted 82).

- [x] 4. (S2) Export the six public names from
      `src/deepreason/calculus/__init__.py`, additively.
      done-when: `python -c "import deepreason.calculus as c; assert
      {'Consultability','FRAME_NOT_SEPARATED','FRAME_ENDPOINT_UNREGISTERED',
      'adjudication_component','consultability','frame_separated'} <=
      set(c.__all__); assert {'CLAIM_SCHEMAS','ClaimDecodeError',
      'PremiseAttributionV1','ProblemSubjectV1','compile_interface','decode',
      'encode','ensure_problem_subject','problem_status',
      'problem_subject_missing','problem_subject_of'} <= set(c.__all__)"`
      -> exit 0 (both halves: the new names present AND every prior name kept)

      DONE. `exports ok: 17 names; new present, all 11 prior names kept`.
      Ordering follows the file's existing isort `order_by_type` convention:
      constants, then classes, then functions.

- [x] 5. (S10) Update `docs/map/SUB-calculus.md` in the SAME commit as the
      code: `Owns:` gains `separation.py`, `Seams-undocumented:` gains
      `calculus x adjudication`, a new section states the invariant, and a
      `Traps` entry records the mention-is-not-enough lesson. RUN each new
      check before writing it down.
      done-when: every `check:` line new to this document exits 0 when run
      by hand, pasted, AND `python tools/docs_verify.py --links` -> 0 failed

      DONE, all three new checks run by hand:

          test_a_mention... + test_wound_persistence...   -> 2 passed in 0.07s
          no-write + no-adjudication-import (structural)  -> check2 exit 0
          test_a_reach_case...is_unconsultable            -> 1 passed in 0.06s
          consultability-has-no-caller (structural)       -> check4 exit 0
          python tools/docs_verify.py --links
            -> docs_verify --links: 0 dangling reference(s), 60 document(s)

      Both structural checks were MUTATION-PROVED in a scratch copy before
      being written down (SCHEMA.md rule 3): injecting `harness.create_artifact`
      turned the first RED, and adding `from deepreason.adjudication.edges
      import build_dep` turned the second RED with
      `AssertionError: ['__future__', 'dataclasses', 'deepreason.adjudication.edges']`.

      One check was REWRITTEN before it was written down, because the first
      draft could not fail honestly: `! grep -q "calculus" premises.py` is false
      in the tree already (`premises.py` says "calculus 9.8" in two comments).
      Replaced with a census of `src/deepreason` outside the calculus package
      for the string `consultability`, paired with three positive anchors.

- [x] 6. (S10) Update `docs/map/CON-standing-and-background.md`: the invariant
      under *Invariants*, a row under *Where to change what*, and
      `Verified-at:` advanced on BOTH map documents.
      done-when: every `check:` line new to this document exits 0 when run by
      hand, pasted

      DONE. `python -c "from deepreason.calculus import consultability,
      frame_separated" && python -m pytest tests/test_calculus_frame_separation.py
      -q` -> `4 passed in 0.09s`. `Verified-at:` advanced to `5deec374` on BOTH
      documents, and only after their checks were re-run.

      Recorded because it nearly shipped silently: the first write of both map
      documents used an UNQUOTED heredoc, so bash expanded every backtick span
      and gutted the prose. Caught by reading the files back; both were
      restored with `git checkout --` and rewritten through a quoted heredoc.

- [x] 7. (S3, S8) Prove the structural claims the gate cannot get from a test:
      `separation.py` contains no write call (negative grep PAIRED with a
      positive anchor, SCHEMA.md rule 1) and imports nothing from
      `adjudication`.
      done-when: both SPEC.md S3/S8 `accept:` commands -> exit 0, pasted

      DONE. S3 accept -> `exit=0`. S8 accept -> `exit=0`.

- [x] 8. (S4) Prove the scope boundary held: no frame-assertion body, no
      standing view, no scope DSL.
      done-when: both SPEC.md S4 `accept:` commands -> exit 0, pasted

      DONE. S4 accept 1 (`poietic.frame-assertion.v1` still declared-and-unbuilt,
      refused with `claim-schema-not-implemented`) -> `exit=0`.
      S4 accept 2 (no `Consult_L`, `Background_L`, `standing_frames` or
      `frame_scope` anywhere in `src/deepreason/`) -> `exit=0`.

- [ ] 9. (S12/R10) Measure the diff against the 193-line budget.
      done-when: `python tools/diff_budget.py` (or `git diff --stat` against
      the base if the tool needs a ceiling argument) -> total changed lines
      recorded; if > 200, STOP and report what grew instead of proceeding

      **STOP — EXCEEDED.** `python tools/diff_budget.py c8071fc34 --ceiling 193
      --paths src/deepreason/calculus tests/test_calculus_frame_separation.py
      docs/map`:

          {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "c8071fc34",
           "areas": {"src/deepreason/calculus": 125,
                     "tests/test_calculus_frame_separation.py": 134,
                     "docs/map": 53},
           "total_insertions": 312, "ceiling": 193, "verdict": "EXCEEDED"}

      Variance against SPEC.md's itemization, line for line:

          separation.py          82 planned  111 actual  (+29)
          __init__.py             7 planned   14 actual  (+7)
          the four gate tests    82 planned  134 actual  (+52)
          SUB-calculus.md        14 planned   45 actual  (+31)
          CON-standing...md       8 planned   13 actual  (+5)
          -------------------------------------------------------
          total                 193 planned  312 actual (+119)

      NO REQUIREMENT GREW AND NO RUNG 4 MACHINERY IS PRESENT — the SIZE
      clause's own diagnostic, checked rather than asserted: step 8's two
      accept commands both exit 0, so `poietic.frame-assertion.v1` is still
      declared-and-unbuilt and no standing view or scope predicate exists
      anywhere in `src/`. `src/` ships exactly the seven public names SPEC.md
      S1/S2 named, and not one more.

      Reported to the operator per `dr-execute-step` step 6. Steps 12-15 are
      NOT executed until the answer arrives.

- [x] 10. (S11) Ring: `python -m pytest
      tests/test_calculus_frame_separation.py
      tests/test_calculus_claim_substrate.py tests/test_adjudication.py
      tests/test_premise_channel.py -q`
      done-when: `0 failed`, pasted (the claim-substrate file carries the
      `RefRole`-only-in-compiler.py structural test this census flagged
      MUST NOT MOVE)

      DONE. `58 passed in 1.10s`, 0 failed. The claim-substrate file's
      `test_the_compiler_is_the_only_authority_on_ref_roles` — the census's
      highest-risk hit, which globs `calculus/*.py` and asserts `RefRole`
      appears only in `compiler.py` — passes with `separation.py` in the glob.

- [x] 11. (S1..S10) [COMMIT] Commit code + exports + both map documents
      together (SCHEMA.md rule 1: the map moves in the same commit).
      done-when: `git status --porcelain` empty and the commit names all four
      files

      DONE. Blast-radius drift check at the checkpoint
      (`--against c8071fc34`): `frozen_surface_contacts: []`,
      `frozen_adjacent_contacts: []`, `frozen_surface_verdict: "CLEAR"`, and no
      `reachability` entry with `direction` `newly_dead` or `newly_live` (every
      direction is `null` or `unchanged`). The three new public functions read
      `UNREACHABLE` from `src/`, which is what SPEC.md S4 predicted in writing:
      "`consultability` has no CALLER in `src/` at the end of this rung. That is
      the boundary working, not an omission." No drift against SPEC.md's
      forecast or census.

- [x] 12. (S10) Map gate, FULL: `python tools/docs_verify.py`
      done-when: exactly the 3 pre-existing `CON-run-identity.md`
      shallow-clone failures from `docs/AUDIT_BASELINES.md`, 0 new; pasted.
      Then `python tools/docs_verify.py --audit` -> 0 findings on the
      documents this tranche touched

      DONE. `python tools/docs_verify.py` (FULL):

          docs_verify [full]: 60 documents, 928 checks, 4 workers
            FAIL CON-run-identity.md:200 (git log -M --diff-filter=R ...)
            FAIL CON-run-identity.md:202 -> fatal: ambiguous argument '1637e808'
            FAIL CON-run-identity.md:204 -> fatal: ambiguous argument 'f304fec1'
          docs_verify: 3 failed

      Exactly the recorded baseline (`docs/AUDIT_BASELINES.md`: "3 pre-existing
      failures, all CON-run-identity.md git-history checks — they require an
      unshallowed clone"). 0 new.

          python tools/docs_verify.py --audit -> 0 finding(s)

      0 findings repo-wide, so none of this tranche's four new checks is
      vacuous. Also run: `--links` -> 0 dangling, 60 documents; `--coverage`
      -> 2 findings, identical to the same command run at base c8071fc34 in a
      temporary worktree; `--stale` -> 6 documents, every entry judged in
      VALIDATION.md (5 pre-existing at base, 1 the unavoidable self-reference).

- [x] 13. (S11) Full gate: `python -m pytest tests/ -q -n 4`. Run it ALONE on
      an idle box — never concurrently with `docs_verify` (`dr-drive-harness`
      §5b).
      done-when: output ends `N passed, 0 failed`, pasted; N >= 3755 + 4.
      Any MCP-thread flake is isolated by re-running that file alone before
      it is attributed

      DONE. `3759 passed, 6 skipped in 910.19s (0:15:10)`. 0 failed.
      3759 = the 3755 baseline + this rung's 4 tests. No known-flaky MCP-thread
      test fired, so no isolation run was owed. Run ALONE on an idle box; the
      docs_verify runs above were sequenced after it, never concurrent.

- [x] 14. (S7/R8) MUTATION PROOF. Copy the tree to the session scratchpad,
      clear `__pycache__`, neuter `frame_separated` to `return True` in the
      COPY, run the violation test there, observe RED; then re-run it on the
      real tree and observe GREEN. The copy is discarded; the repo is never
      mutated.
      done-when: both runs pasted into VALIDATION.md with the mutated line
      shown, RED then GREEN

      DONE — TWO mutations, both pasted in VALIDATION.md S7.

      Mutation A neutered `frame_separated` to `return True`:
      `1 failed, 3 passed` (`AssertionError: assert not True` at
      test_calculus_frame_separation.py:114), then `4 passed` restored.

      Mutation A was NOT enough and the gap is recorded rather than glossed:
      it left `consultability` green, because the enforcement computes its own
      intersection from `_state_components` rather than calling
      `frame_separated`. So the check was disabled one level down instead —
      mutation B made `_components` forget every att/dep edge —
      and the enforcement went RED too: `assert True is False, where True =
      Consultability(consultable=True, code=None, detail=()).consultable`.
      `2 failed, 2 passed`, then `4 passed` restored. Both copies discarded;
      the repository was never mutated.

- [ ] 15. (all) [COMMIT] Push and confirm clean tree.
      done-when: `git status --porcelain` empty AND
      `git rev-parse HEAD origin/claude/calculus-rung3b-frame-separation-yqjxyt`
      prints the same sha twice
