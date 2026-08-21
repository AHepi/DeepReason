# Checklist for: Rung 3b — the frame-separation invariant

State: next=1 blockers=none
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

- [ ] 1. (S5, S6) Write `tests/test_calculus_frame_separation.py` — the gate,
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

- [ ] 3. (S1, S2, S3, S4) Write `src/deepreason/calculus/separation.py`:
      `_components`, `adjudication_component` (Def 7.1),
      `frame_separated` (Def 7.2), `Consultability`, `consultability` (R64),
      `FRAME_NOT_SEPARATED`, `FRAME_ENDPOINT_UNREGISTERED`, and the SCOPE
      BOUNDARY paragraph in the module docstring.
      done-when: `python -m pytest tests/test_calculus_frame_separation.py -q`
      -> `4 passed`

- [ ] 4. (S2) Export the six public names from
      `src/deepreason/calculus/__init__.py`, additively.
      done-when: `python -c "import deepreason.calculus as c; assert
      {'Consultability','FRAME_NOT_SEPARATED','FRAME_ENDPOINT_UNREGISTERED',
      'adjudication_component','consultability','frame_separated'} <=
      set(c.__all__); assert {'CLAIM_SCHEMAS','ClaimDecodeError',
      'PremiseAttributionV1','ProblemSubjectV1','compile_interface','decode',
      'encode','ensure_problem_subject','problem_status',
      'problem_subject_missing','problem_subject_of'} <= set(c.__all__)"`
      -> exit 0 (both halves: the new names present AND every prior name kept)

- [ ] 5. (S10) Update `docs/map/SUB-calculus.md` in the SAME commit as the
      code: `Owns:` gains `separation.py`, `Seams-undocumented:` gains
      `calculus x adjudication`, a new section states the invariant, and a
      `Traps` entry records the mention-is-not-enough lesson. RUN each new
      check before writing it down.
      done-when: every `check:` line new to this document exits 0 when run
      by hand, pasted, AND `python tools/docs_verify.py --links` -> 0 failed

- [ ] 6. (S10) Update `docs/map/CON-standing-and-background.md`: the invariant
      under *Invariants*, a row under *Where to change what*, and
      `Verified-at:` advanced on BOTH map documents.
      done-when: every `check:` line new to this document exits 0 when run by
      hand, pasted

- [ ] 7. (S3, S8) Prove the structural claims the gate cannot get from a test:
      `separation.py` contains no write call (negative grep PAIRED with a
      positive anchor, SCHEMA.md rule 1) and imports nothing from
      `adjudication`.
      done-when: both SPEC.md S3/S8 `accept:` commands -> exit 0, pasted

- [ ] 8. (S4) Prove the scope boundary held: no frame-assertion body, no
      standing view, no scope DSL.
      done-when: both SPEC.md S4 `accept:` commands -> exit 0, pasted

- [ ] 9. (S12/R10) Measure the diff against the 193-line budget.
      done-when: `python tools/diff_budget.py` (or `git diff --stat` against
      the base if the tool needs a ceiling argument) -> total changed lines
      recorded; if > 200, STOP and report what grew instead of proceeding

- [ ] 10. (S11) Ring: `python -m pytest
      tests/test_calculus_frame_separation.py
      tests/test_calculus_claim_substrate.py tests/test_adjudication.py
      tests/test_premise_channel.py -q`
      done-when: `0 failed`, pasted (the claim-substrate file carries the
      `RefRole`-only-in-compiler.py structural test this census flagged
      MUST NOT MOVE)

- [ ] 11. (S1..S10) [COMMIT] Commit code + exports + both map documents
      together (SCHEMA.md rule 1: the map moves in the same commit).
      done-when: `git status --porcelain` empty and the commit names all four
      files

- [ ] 12. (S10) Map gate, FULL: `python tools/docs_verify.py`
      done-when: exactly the 3 pre-existing `CON-run-identity.md`
      shallow-clone failures from `docs/AUDIT_BASELINES.md`, 0 new; pasted.
      Then `python tools/docs_verify.py --audit` -> 0 findings on the
      documents this tranche touched

- [ ] 13. (S11) Full gate: `python -m pytest tests/ -q -n 4`. Run it ALONE on
      an idle box — never concurrently with `docs_verify` (`dr-drive-harness`
      §5b).
      done-when: output ends `N passed, 0 failed`, pasted; N >= 3755 + 4.
      Any MCP-thread flake is isolated by re-running that file alone before
      it is attributed

- [ ] 14. (S7/R8) MUTATION PROOF. Copy the tree to the session scratchpad,
      clear `__pycache__`, neuter `frame_separated` to `return True` in the
      COPY, run the violation test there, observe RED; then re-run it on the
      real tree and observe GREEN. The copy is discarded; the repo is never
      mutated.
      done-when: both runs pasted into VALIDATION.md with the mutated line
      shown, RED then GREEN

- [ ] 15. (all) [COMMIT] Push and confirm clean tree.
      done-when: `git status --porcelain` empty AND
      `git rev-parse HEAD origin/claude/calculus-rung3b-frame-separation-yqjxyt`
      prints the same sha twice
