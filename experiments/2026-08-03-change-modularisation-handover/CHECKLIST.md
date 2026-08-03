# Checklist for: the modularisation handover for a Sonnet 5 executor

Re-read REQUEST.md + SPEC.md before every step. One step per invocation.

Map ids: none — touched files are `docs/HANDOVER_2026-08-03.md` and
`.claude/skills/dr-drive-harness/SKILL.md`, both outside `docs/map/`'s
charter; zero `src/` changes. docs_verify runs as the regression guard.

- [x] 1. (S1) Write `docs/HANDOVER_2026-08-03.md` per SPEC S1 a–f.
      done-when: greps per S1 acceptance all >= 1.
      OUTPUT: all greps >= 1 (claude-sonnet-5:1, Rungs 1-7 each:1,
      DESIGN-AND-STOP:4, dr-drive-harness:3, dr-ask-the-right-question:1,
      dr-change-orchestrator:7, R8:2, read-first present).

- [x] 2. (S3) Add the "Calibration for less capable executors" block to
      dr-drive-harness.
      done-when: grep -c -> 1.
      OUTPUT: 1.

- [x] 3. (S1, S3) Docs guard.
      done-when: `python tools/docs_verify.py` -> 0 failed; `--audit` ->
      0 findings.
      OUTPUT: docs_verify: 0 failed | --audit: 0 finding(s) | --links: 0
      dangling, 46 documents.

- [x] 4. (all) [COMMIT] Commit handover + skill edit + tranche artifacts;
      push with retry.
      done-when: porcelain empty; local HEAD == origin HEAD.
      OUTPUT: verified post-commit in VALIDATION.md.

- [x] 5. (all) Gate disposition: zero src/tests changes by construction.
      done-when: `git diff --stat <tranche-base>..HEAD -- src/ tests/` is
      EMPTY (paste), and the standing green gate (3290 passed, 0 failed at
      tree a31f1082; only docs/skills markdown has changed since) is cited
      with its instrument. If the diff is NOT empty, run the full gate
      instead.
      OUTPUT: diff EMPTY (0 lines) — zero src/tests changes in this
      tranche. Standing gate: 3290 passed, 7 skipped, 0 failed
      (python -m pytest tests/ -q -n 4 at tree a31f1082); every commit
      since touches only docs/ and .claude/skills/ markdown plus tranche
      artifacts, none of which any test imports.
