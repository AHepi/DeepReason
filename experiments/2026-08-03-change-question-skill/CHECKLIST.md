# Checklist for: "create a skill for less intelligent LLMs ask the right questions in relation to this harness"

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids: none — `.claude/skills/` is outside `docs/map/` coverage by the
map's charter (REQUEST.md map note; INDEX.md: "docs/map describes
src/deepreason/"). No `src/` file changes in this tranche, so no seam or
subsystem document moves; docs_verify still runs as the regression guard
that the wiring edits broke nothing the map pins (CLAUDE.md is grepped by
map checks).

- [x] 1. (S1) Write `.claude/skills/dr-ask-the-right-question/SKILL.md`:
      frontmatter (name, description with load triggers) + the six
      sections of SPEC S1, worked examples only from committed artifacts.
      done-when: all of
        `grep -c "^## " .claude/skills/dr-ask-the-right-question/SKILL.md`
        -> 6, and
        `grep -q "name: dr-ask-the-right-question" <file>` -> exit 0, and
        `grep -q "86f1248e" <file>` -> exit 0 (dr-decide-or-ask provenance),
        and `grep -cE "ERRATA|Traps|experiments/2026-08" <file>` -> >= 4.
      OUTPUT: sections: 6 | frontmatter: ok | provenance: ok | refs: 14
      (first run showed 7 sections — the Exit-criterion H2; demoted to a
      bold paragraph to match the criterion as written, content unchanged)

- [x] 2. (S1) [COMMIT] Commit the new skill file alone (message cites R1,
      R3, R4), push with retry.
      done-when: `git log --oneline -1` shows the skill commit AND
      `git status --porcelain` shows no `.claude/skills/` entries.
      OUTPUT: b66b7f52 step 1-2: dr-ask-the-right-question, the
      question-discipline skill | porcelain: no .claude/skills entries;
      pushed.

- [x] 3. (S2a-c) Add the routing sentence to the three skill files:
      `deepreason-orchestrator/SKILL.md` (scope-contract stop conditions),
      `dr-change-orchestrator/SKILL.md` (scope contract item 1),
      `dr-spec-change/SKILL.md` (step 2, questions-for-operator branch).
      done-when: `grep -l "dr-ask-the-right-question"` over the three
      files lists all three.
      OUTPUT: all three listed (deepreason-orchestrator,
      dr-change-orchestrator, dr-spec-change).

- [x] 4. (S2d) Add the one routing line to CLAUDE.md's "Which workflow to
      use" section, after the cross-routing paragraph.
      done-when: `grep -c "dr-ask-the-right-question" CLAUDE.md` -> 1.
      OUTPUT: CLAUDE.md refs: 1.

- [x] 5. (S2) Docs regression guard: the wiring edits must not break any
      map check that greps CLAUDE.md or the skills tree.
      done-when: `python tools/docs_verify.py` -> 0 failed AND
      `python tools/docs_verify.py --audit` -> 0 findings.
      OUTPUT: docs_verify: 0 failed | docs_verify --audit: 0 finding(s).

- [ ] 6. (S2, S3) [COMMIT] Commit the four wiring edits (message cites R5,
      C1 and notes S3's survey lives in SPEC.md), push with retry.
      done-when: `git status --porcelain` empty AND
      `git ls-remote origin claude/handover-defect-audit-33pv3d` equals
      local HEAD.

- [ ] 7. (all) Full gate (no `src/` changed; the gate is the standing
      proof of that).
      done-when: `python -m pytest tests/ -q -n 4` output ends
      "<N> passed, <k> skipped" with 0 failed — paste output.

- [ ] 8. (all) [COMMIT] Tranche artifacts current (CHECKLIST boxes ticked
      with pasted outputs), committed, pushed, tree clean.
      done-when: `git status --porcelain` empty AND branch head on origin.
