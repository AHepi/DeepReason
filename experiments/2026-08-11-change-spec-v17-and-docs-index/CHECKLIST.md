# Checklist for: v1.7 spec amendment + docs/INDEX.md (Q1+Q2 approved)

State: next=1 blockers=none
Map ids: none — confirmed no `src/deepreason/` subsystem is touched
(SPEC.md's frozen-surface forecast: zero `src/` files targeted), and
`docs/map/INDEX.md` itself states its scope is "describes
`src/deepreason/`" — this tranche is pure documentation, outside the
map's own scope by design, not an oversight.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per `dr-execute-step` invocation.

- [ ] 1. (S1) Draft `docs/harness-spec-v1.7-amendment.md`, six sections
      (seats/seat-bindings.v1, conjecturer.turn.v7, candidate_checker,
      school-seat routing, adjudication-blindness/blind-same-model
      judges, config referee), v1.6-style "Status and scope" opening
      stating it amends and does not modify v1.3-v1.6.
      done-when: `test -f docs/harness-spec-v1.7-amendment.md` and each
      of the six surface names appears at least once with a concrete
      file/symbol citation.
- [ ] 2. (S2) Update `CLAUDE.md` line 311's directory-map entry to
      read "v1.3 + v1.4/v1.5/v1.6/v1.7 amendments".
      done-when: `grep -q "v1.4/v1.5/v1.6/v1.7" CLAUDE.md`.
- [ ] 3. (S1, S2) [COMMIT] Commit the amendment file + CLAUDE.md
      update together (same commit, per the map-moves-with-code
      convention SPEC.md cites).
      done-when: `git log -1 --stat` shows both files; `git push`
      succeeds.
- [ ] 4. (S3) Draft `docs/INDEX.md`: sections for Reference (→
      `docs/map/INDEX.md`, the spec series), Explanation (→
      `experiments/*/RESULTS.md`), Decisions (→ `docs/proposals/`),
      Corrections (→ `docs/ERRATA.md`/`ERRATA_EXECUTOR.md`).
      done-when: `test -f docs/INDEX.md` and it links all four target
      paths by exact string.
- [ ] 5. (S3) [COMMIT] Commit `docs/INDEX.md` alone; confirm
      `git diff --stat` for this commit shows zero rename (`R`) lines.
      done-when: `git push` succeeds; `git show --stat HEAD` has no
      `=>` rename markers.
- [ ] 6. (all) Docs check: `python tools/docs_verify.py`
      done-when: failure count is unchanged from this tranche's own
      pre-change baseline (3 pre-existing `CON-run-identity.md`
      shallow-clone failures, confirmed unrelated in Item 1's own
      audit) — no NEW failures introduced by the new files.
- [ ] 7. (all) [COMMIT] Push and confirm clean tree.
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD` equals `git rev-parse origin/<branch>`.
