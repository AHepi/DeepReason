# Checklist for: implement the parked skills-overhaul follow-ups
State: next=3 blockers=none
Map ids: none — same reasoning as the prior tranche (docs/map covers
only src/deepreason/; this tranche touches .claude/skills/ and
docs/ERRATA.md only). src/ and tests/ stay byte-untouched (C2).

- [x] 1. (R1, Q1-resolution) Operator answered Q1 "judgement only and
      approved to continue": record the accepted exception as
      docs/ERRATA.md E24 (next free number), and add a one-clause
      pointer to it from dr-drive-harness's own rule text. [COMMIT]
      done-when: `grep -q "^\*\*E24" docs/ERRATA.md` -> found; `grep -q
      "E24" .claude/skills/dr-drive-harness/SKILL.md` -> found.

- [x] 2. (S1, R2) Trim dr-ask-the-right-question's one remaining W5 row
      (dr-ask-the-right-question-16) to rule + bare citation, matching
      the pattern from the prior tranche's 8 other trims. [COMMIT]
      done-when: `git diff --stat .claude/skills/
      dr-ask-the-right-question/SKILL.md` shows a small, confined
      change.

- [ ] 3. `python tools/docs_verify.py` full run, since docs/ERRATA.md
      (a committed document) changed. [no commit needed unless drift
      found]
      done-when: 0 failed beyond the 3 pre-existing CON-run-identity.md
      baseline.

- [ ] 4. Final src/+tests/ untouched confirmation and clean-tree check.
      done-when: both diffs empty; `git status --porcelain` empty.

- [ ] 5. Write DELIVERY.md: R1/R2 reconciliation with PROOF. [COMMIT]
      done-when: both R1 and R2 appear as rows with non-empty PROOF.
