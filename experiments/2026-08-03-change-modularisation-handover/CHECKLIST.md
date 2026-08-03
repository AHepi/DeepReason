# Checklist for: the modularisation handover for a Sonnet 5 executor

Re-read REQUEST.md + SPEC.md before every step. One step per invocation.

Map ids: none — touched files are `docs/HANDOVER_2026-08-03.md` and
`.claude/skills/dr-drive-harness/SKILL.md`, both outside `docs/map/`'s
charter; zero `src/` changes. docs_verify runs as the regression guard.

- [ ] 1. (S1) Write `docs/HANDOVER_2026-08-03.md` per SPEC S1 a–f.
      done-when: greps per S1 acceptance all >= 1.

- [ ] 2. (S3) Add the "Calibration for less capable executors" block to
      dr-drive-harness.
      done-when: grep -c -> 1.

- [ ] 3. (S1, S3) Docs guard.
      done-when: `python tools/docs_verify.py` -> 0 failed; `--audit` ->
      0 findings.

- [ ] 4. (all) [COMMIT] Commit handover + skill edit + tranche artifacts;
      push with retry.
      done-when: porcelain empty; local HEAD == origin HEAD.

- [ ] 5. (all) Gate disposition: zero src/tests changes by construction.
      done-when: `git diff --stat <tranche-base>..HEAD -- src/ tests/` is
      EMPTY (paste), and the standing green gate (3290 passed, 0 failed at
      tree a31f1082; only docs/skills markdown has changed since) is cited
      with its instrument. If the diff is NOT empty, run the full gate
      instead.
