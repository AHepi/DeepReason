# Checklist for: implement the parked skills-overhaul follow-ups
State: next=none (tranche complete, all 5 steps checked) blockers=none
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

- [x] 3. `python tools/docs_verify.py` full run, since docs/ERRATA.md
      (a committed document) changed. [no commit needed unless drift
      found]
      done-when: 0 failed beyond the 3 pre-existing CON-run-identity.md
      baseline.
      PROOF: `docs_verify [full]: 53 documents, 859 checks` -> `3
      failed`, all three at CON-run-identity.md:195/197/199, the exact
      same shallow-clone-gap baseline as the prior tranche. Zero new
      failures. No file changes; no commit needed.

- [x] 4. Final src/+tests/ untouched confirmation and clean-tree check.
      done-when: both diffs empty; `git status --porcelain` empty.
      PROOF: `git diff origin/main...HEAD -- src/ tests/` -> empty (0
      lines). `git status --porcelain` showed only this file's own
      pending step-3 PROOF edit at check time — expected before commit,
      not a residual gap.

- [x] 5. Write DELIVERY.md: R1/R2 reconciliation with PROOF. [COMMIT]
      done-when: both R1 and R2 appear as rows with non-empty PROOF.
      PROOF: `grep -cE "^\| R[0-9]+ "` -> 2. Both rows carry commit
      `8cd61452d` as their proof pointer. Errata: E24 stated. Parked:
      none — both P1/P2 closed.
