# Checklist for: "a skill that teaches other LLMs how to run the harness properly and where to look"

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids: none — every touched file (`.claude/skills/`, `README.md`,
`CLAUDE.md`) is outside `docs/map/`'s charter; zero `src/` changes.
docs_verify runs as the regression guard (map checks grep CLAUDE.md and
README-adjacent paths).

- [x] 1. (S1) Write `.claude/skills/dr-drive-harness/SKILL.md` — six
      sections per SPEC S1, index-over-authorities style.
      done-when: `grep -c "^## " <file>` -> 6; frontmatter grep ok; one
      grep hit each for deepreason-orchestrator, dr-change-orchestrator,
      dr-ask-the-right-question, REC-change-a-seam, INV-frozen-surfaces,
      "SEAM-<a>-x-<b>".
      OUTPUT: sections: 6 | frontmatter: ok | all six greps >= 1
      (INV-frozen-surfaces: 2, SEAM-<a>-x-<b>: 2).

- [x] 2. (S1) [COMMIT] Commit the driving skill alone; push with retry.
      done-when: commit on origin; porcelain shows no .claude/skills
      entries.
      OUTPUT: recorded in the step-2 commit hash below (git log).

- [x] 3. (S3) Write `.claude/skills/README.md` — the organising index.
      done-when: contains both family names, all 12 phase skills, both
      cross-cutting skills, `dr-drive-harness`; `wc -l` <= 80.
      OUTPUT: lines: 55; all 16 skills present (no MISSING).

- [x] 4. (S2, S6) Wire the workflows: both orchestrators gain the
      dr-drive-harness preflight sentence (S2) AND the explicit seam
      pointers in Map preflight item 2 (S6); dr-plan-steps 4b and
      dr-execute-step map obligations gain the same seam pointers (S6).
      done-when: `grep -l dr-drive-harness` lists both orchestrators;
      `grep -l REC-change-a-seam` over the four S6 files lists all four.
      OUTPUT: S2 both orchestrators listed; S6 all four listed.

- [x] 5. (S4) CLAUDE.md: driving-skill routing line + skills README
      pointer in "Which workflow to use"; docs/ERRATA.md added to the
      session-start truth chain.
      done-when: `grep -c dr-drive-harness CLAUDE.md` >= 1 AND
      `grep -c "ERRATA" CLAUDE.md` >= 1.
      OUTPUT: dr-drive-harness: 1 | ERRATA: 1.

- [x] 6. (S5) README.md: add "Operating this repository" (absorbing
      "Developer-only source work"), compress "Unsupported and historical
      boundaries", no does/how cuts.
      done-when: `grep -c dr-drive-harness README.md` >= 1; `wc -l` < 363;
      grep hits remain for "Install and operate", "amend", "MCP public
      facade", "Architecture and safety".
      OUTPUT: dr-drive-harness: 1 | lines: 357 (< 363) | all four
      headings kept. Two repetition trims (amend lead-in; MCP amendment
      paragraph now defers to the CLI amend section).

- [x] 7. (S2-S6) Docs regression guard.
      done-when: `python tools/docs_verify.py` -> 0 failed AND `--audit`
      -> 0 findings.
      OUTPUT: docs_verify: 0 failed | --audit: 0 finding(s) | --links:
      0 dangling, 46 documents.

- [x] 8. (S2-S6, S7) [COMMIT] Commit wiring + CLAUDE.md + README + skills
      README + PARKED.md (S7 deferred-R8 entry); push with retry.
      done-when: porcelain empty; local HEAD == origin HEAD.

- [ ] 9. (all) Full gate.
      done-when: `python -m pytest tests/ -q -n 4` -> 0 failed (paste).

- [ ] 10. (all) [COMMIT] Tranche artifacts current, committed, pushed,
      tree clean.
      done-when: porcelain empty AND branch head on origin.
