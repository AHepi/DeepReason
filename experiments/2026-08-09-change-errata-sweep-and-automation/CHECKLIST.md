# Checklist for: update the Errata (sweep + automation)
State: next=3 blockers=none
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

- [ ] 3. (S1-S8) [COMMIT] Commit and push docs/ERRATA.md.
      done-when: `git status --porcelain docs/ERRATA.md` empty AND
      `git log --oneline -1 -- docs/ERRATA.md` shows this commit AND
      branch head is on origin

- [ ] 4. (S9,S10) Amend `.claude/skills/dr-deliver-change/SKILL.md`:
      add a mandatory "Errata check" step to Procedure (between
      existing step 3b "Map delta" and step 4 "Write DELIVERY.md"),
      add an "## Errata" section to the DELIVERY.md template, and add
      an errata exit-criterion line. Checkpoint wording per REQUEST.md
      R6, adapted to name DELIVERY.md per SPEC.md's A2.
      done-when: `grep -ic "errata" .claude/skills/dr-deliver-change/SKILL.md` -> N where N>=3

- [ ] 5. (S9,S11) Amend `.claude/skills/dr-verify-outcome/SKILL.md`:
      add the same mandatory "Errata check" to the "Closing the
      tranche (on PASS)" bullet list, and an "Errata:" line to the
      VERIFY.md template next to the existing "Residue (honest):"
      line. Checkpoint wording per REQUEST.md R6, adapted to name
      VERIFY.md per SPEC.md's A2.
      done-when: `grep -ic "errata" .claude/skills/dr-verify-outcome/SKILL.md` -> N where N>=2

- [ ] 6. (S10,S11) [COMMIT] Commit and push the two skill amendments.
      done-when: `git status --porcelain .claude/skills/dr-deliver-change/SKILL.md .claude/skills/dr-verify-outcome/SKILL.md`
      empty AND branch head is on origin

- [ ] 7. (all) Map check: `python tools/docs_verify.py`
      done-when: output ends "0 failed"

- [ ] 8. (R8, all) docs_verify full modes: `python tools/docs_verify.py --audit`
      and `python tools/docs_verify.py --links`
      done-when: `--audit` reports 0 findings AND `--links` reports 0
      dangling references (paste both)

- [ ] 9. (R8, all) Full gate: `pytest tests/ -q -n 4`
      done-when: output ends "N passed, 0 failed" (paste it; docs-only
      tranche, so N is expected to match the pre-tranche baseline
      exactly)

- [ ] 10. (all) [COMMIT] push and confirm clean tree
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD` equals `git rev-parse origin/claude/errata-update-automation-21ftwd`
