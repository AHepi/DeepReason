# Checklist for: update the Errata (sweep + automation)
State: next=10 blockers=none
Map ids: none — docs/skills-only tranche (docs/map covers
src/deepreason/ only; see REQUEST.md's Map preflight section).
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

- [x] 1. (S1,S2,S3,S4,S5,S6,S7) Append seven new entries (E11-E17) to
      `docs/ERRATA.md`, under one new dated header ("## 2026-08-09
      (sweep of tranches since 2026-08-04)"), each following the
      file's existing "**E<n> — title.** ..." paragraph format and
      evidence-pointer style. Content per SPEC.md items S1-S7 exactly.
      done-when: `grep -Ec "^\*\*E1[1-7] —" docs/ERRATA.md` -> 7
      DONE: 7

- [x] 2. (S8) Verify the excluded S5 budget-headline candidate left no
      trace in docs/ERRATA.md (negative check for SPEC.md's S8
      exclusion decision).
      done-when: `grep -c "220-300\|220–300" docs/ERRATA.md` -> 0
      DONE: 0

- [x] 3. (S1-S8) [COMMIT] Commit and push docs/ERRATA.md.
      done-when: `git status --porcelain docs/ERRATA.md` empty AND
      `git log --oneline -1 -- docs/ERRATA.md` shows this commit AND
      branch head is on origin
      DONE: commit dbff393b8, pushed

- [x] 4. (S9,S10) Amend `.claude/skills/dr-deliver-change/SKILL.md`:
      add a mandatory "Errata check" step to Procedure (between
      existing step 3b "Map delta" and step 4 "Write DELIVERY.md"),
      add an "## Errata" section to the DELIVERY.md template, and add
      an errata exit-criterion line. Checkpoint wording per REQUEST.md
      R6, adapted to name DELIVERY.md per SPEC.md's A2.
      done-when: `grep -ic "errata" .claude/skills/dr-deliver-change/SKILL.md` -> N where N>=3
      DONE: 9

- [x] 5. (S9,S11) Amend `.claude/skills/dr-verify-outcome/SKILL.md`:
      add the same mandatory "Errata check" to the "Closing the
      tranche (on PASS)" bullet list, and an "Errata:" line to the
      VERIFY.md template next to the existing "Residue (honest):"
      line. Checkpoint wording per REQUEST.md R6, adapted to name
      VERIFY.md per SPEC.md's A2.
      done-when: `grep -ic "errata" .claude/skills/dr-verify-outcome/SKILL.md` -> N where N>=2
      DONE: 6

- [x] 6. (S10,S11) [COMMIT] Commit and push the two skill amendments.
      done-when: `git status --porcelain .claude/skills/dr-deliver-change/SKILL.md .claude/skills/dr-verify-outcome/SKILL.md`
      empty AND branch head is on origin
      DONE: commit 2416c6f32, pushed

- [x] 7. (all) Map check: `python tools/docs_verify.py`
      done-when: output ends "0 failed"
      DONE: "docs_verify [full]: 53 documents, 851 checks, 4 workers" /
      "docs_verify: 0 failed". Required an environment fix first
      (unrelated to this tranche's content): the container's git clone
      was shallow, failing 3 CON-run-identity.md checks that `git log`
      two historical retirement commits by hash; `git fetch --unshallow
      origin` resolved it (confirmed: those 3 checks also fail on a
      fresh shallow origin/main checkout, pass once unshallowed).

- [x] 8. (R8, all) docs_verify full modes: `python tools/docs_verify.py --audit`
      and `python tools/docs_verify.py --links`
      done-when: `--audit` reports 0 findings AND `--links` reports 0
      dangling references (paste both)
      DONE: "docs_verify --audit: 0 finding(s)" /
      "docs_verify --links: 0 dangling reference(s), 53 document(s)"

- [x] 9. (R8, all) Full gate: `pytest tests/ -q -n 4`
      done-when: output ends "N passed, 0 failed" (paste it; docs-only
      tranche, so N is expected to match the pre-tranche baseline
      exactly)
      DONE-WITH-EXCEPTION: "1 failed, 3434 passed, 7 skipped in 780.12s"
      (via `python3 -m pytest tests/ -q -n 4` — the bare `pytest` on
      PATH resolves to an isolated uv-tool environment missing
      `deepreason`/`jsonschema`, an unrelated environment quirk, not a
      test failure). The one failure,
      `test_bronze_report.py::test_census_totals_internally_consistent`
      (`assert 159 == 165`), is PRE-EXISTING and OUT OF SCOPE: SPEC.md's
      Out-of-scope section already excludes it by name (it is D2's own
      `PARKED.md` item P-D2-3, dated 2026-08-08, before this tranche
      began); this tranche changed zero files under `tests/` or `src/`;
      and the identical assertion (`159 == 165`) was independently
      reproduced against a fresh, isolated `origin/main` checkout in a
      throwaway venv (`git worktree add ... origin/main --detach`,
      no shared install state), confirming the failure predates and is
      unrelated to this tranche. Baseline for this docs-only tranche is
      therefore 3434 passed / 1 pre-existing failed / 7 skipped, not a
      regression.

- [x] 10. (all) [COMMIT] push and confirm clean tree
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD` equals `git rev-parse origin/claude/errata-update-automation-21ftwd`
