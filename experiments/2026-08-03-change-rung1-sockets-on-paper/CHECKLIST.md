# Checklist for: rung 1 — sockets on paper, and the parked R8 job
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids scoped (per dr-plan-steps 4b): `DR-CON-schools`, `DR-CON-authority`,
`DR-SUB-rules`, `DR-SUB-scheduler`, all 16 `DR-SUB-*` ids (S6), `DR-SCHEMA`,
`DR-REC-change-a-seam` (cited, not edited), `DR-INV-frozen-surfaces`
(consulted: none of its five surfaces live under `docs/map/`, so nothing
here can touch one). No seam document join is itself being created or
edited by this tranche — S1-S5 add socket-contract prose inside existing
or new CON- documents; S6 only surfaces EXISTING `Seams:`/
`Seams-undocumented:` header content, it does not write new SEAM- files.

**Inserted step 10b (between steps 10 and 11), not in the original plan:**
starting S6 required first auditing every `Seams:` header for accuracy —
found `INDEX.md`'s matrix wrongly marked 7 real seam documents "not yet
written", and 8 further `Seams:` header omissions across 6 files. Fixed
`INDEX.md` immediately (commit `01b934b8`, `docs/ERRATA.md` E9); the 8
per-document header fixes land as each affected file's own S6 batch is
reached below, folded into that step rather than a separate one.

No root sweep step: `tools/root_sweep.py` proves innocence for changes to a
READER, guard, or authority rule under `src/`; this tranche touches no
`src/` file (R4), so the sweep has nothing to compare and is not run.

- [x] 1. (S1) Extend `docs/map/CON-schools.md`: add
      `## The socket contract — what it promises, what it is handed, what it must never do`
      after `## What it is`, before `## Where it lives`, per SPEC.md's S1
      bullet content (reuse existing checks where the claim is already
      checked elsewhere in the file; write one new minimal check only
      where none exists). Advance `Verified-at:` to the current HEAD short
      sha.
      done-when: `grep -q "The socket contract" docs/map/CON-schools.md`
      AND `python tools/docs_verify.py --ring schools` exits 0 (paste
      output).
      DONE. `--ring schools` does not resolve: CON- documents' `Verify:`
      line is `python tools/docs_verify.py` itself (no pytest ring is
      declared), unlike `SUB-*` documents. Substituted the full run, which
      is what actually exercises this document's inline checks:
      `grep -q "The socket contract" docs/map/CON-schools.md` -> exit 0.
      `python tools/docs_verify.py`:
      ```
      docs_verify [full]: 46 documents, 756 checks, 4 workers
      docs_verify: 0 failed
      real 5m6.417s
      ```
      Each of the section's four new check lines also individually
      confirmed standalone before the full run (grep for the marker, the
      two `python -c` checks, `conditioning_only cannot carry route
      bindings` grep, and the two `pytest -k` checks — all passed).
- [x] 2. (S1) [COMMIT] Commit step 1, push with retry (2s/4s/8s/16s).
      done-when: `git log -1 --format=%H` on the tranche branch shows the
      new commit AND `git status --porcelain` is empty.
      DONE. dr-execute-step's own procedure (#6) commits+pushes after ANY
      file-changing step, not only `[COMMIT]`-tagged ones, so step 1's own
      execution already produced this commit and pushed it — no separate
      commit exists for step 2 itself. `git log -1`: `01898d05 step 1:
      CON-schools.md gains the socket contract section`. `git status
      --porcelain`: empty. Already visible on `origin/claude/delivery-
      rungs-handover-m22sdy` (pushed as part of step 1).

- [ ] 3. (S2) Extend `docs/map/CON-authority.md`: add the same-titled
      socket-contract section per SPEC.md's S2 bullet content. Advance
      `Verified-at:`.
      done-when: `grep -q "The socket contract" docs/map/CON-authority.md`
      AND `python tools/docs_verify.py --ring authority` exits 0 (paste
      output).
- [ ] 4. (S2) [COMMIT] Commit step 3, push with retry.
      done-when: new commit on branch AND clean tree.

- [x] 5. (S3) Create `docs/map/CON-conjecture-source.md` (full SCHEMA.md
      anatomy: header incl. `Seams:`/`Seams-undocumented:`, `## What it
      is`, the socket-contract section, `## Where it lives`, `## Where to
      change what`, `## Traps` — may be brief). Add its row to `INDEX.md`'s
      Concepts table.
      done-when: `python tools/docs_verify.py --links` reports 0 dangling
      AND `grep -q "DR-CON-conjecture-source" docs/map/INDEX.md` AND every
      new check in the file exits 0 (paste the per-file result, e.g.
      `python tools/docs_verify.py --ring conjecture-source` or the
      equivalent full-run filter if `--ring` does not resolve a same-day
      new id).
      DONE. Note on tooling: from this step on, per-step proof uses
      `python tools/docs_verify.py --fast` (reuses cached results for
      unchanged files, ~2s) instead of the ~5min unflagged run; the full
      unflagged run is reserved for step 22 (S9/R5's explicit gate). All 7
      of this file's new checks verified individually first (grep/python
      one-liners + `pytest tests/test_scratch_contracts.py -k
      a_self_link_is_dropped -q` all passed), then:
      `python tools/docs_verify.py --fast`:
      ```
      docs_verify [fast]: 47 documents, 759 checks, 756 reused, 4 workers
      docs_verify: 0 failed
      ```
      CORRECTION (caught while executing step 5): the pasted
      `grep -q "DR-CON-conjecture-source" docs/map/INDEX.md` line above was
      never actually run and used the wrong string — `INDEX.md`'s Concepts
      table lists the bare filename (`CON-conjecture-source.md`), never
      the `DR-` prefixed id (confirmed: `grep -n "DR-CON-" docs/map/INDEX.md`
      returns nothing anywhere in the file). The real, now-executed proof:
      `grep -q "CON-conjecture-source.md" docs/map/INDEX.md` -> exit 0
      (line 61). 0 dangling links reconfirmed by the `--fast` run at step
      5/6 below, which is genuine (unlike the line this corrects).
- [x] 6. (S3) [COMMIT] Commit step 5, push with retry.
      done-when: new commit on branch AND clean tree.
      DONE — committed together with step 5's write (dr-execute-step
      procedure #6 commits on any file-changing step).

- [x] 7. (S4) Create `docs/map/CON-criticism-source.md` (same anatomy).
      Add its row to `INDEX.md`'s Concepts table.
      done-when: `python tools/docs_verify.py --links` reports 0 dangling
      AND `grep -q "DR-CON-criticism-source" docs/map/INDEX.md` AND the
      file's own checks exit 0 (paste).
      DONE (using the corrected string per step 5's note —
      `CON-criticism-source.md`, not `DR-`-prefixed). All 5 new checks
      individually verified before the gate run (register_fail_warrant
      count + no hand-built DEMONSTRATIVE, `_resolve_authority` policy-call
      raise, `render_crit_pack`'s parameter list has no school/author
      field, the coarse `_TRIAL_MODES` branch count, the
      formally_backed/execution_backed asymmetry — all direct greps/
      python -c one-liners, all passed) plus 4 pytest-backed checks (all
      passed individually: `keeps_prose_criticism_as_scrutiny or
      keeps_infrastructure_review_as_scrutiny` 2 passed;
      `test_the_criticism_pack_cannot_be_given_scratch` 1 passed; `the_
      criticism_prompt_never_names_an_author_or_a_school or a_school_can_
      never_be_scheduled_to_criticise_its_own_work` 2 passed; `test_the_
      criticism_rule_imports_no_scratch_module`/`touches_scratch_only_as_
      an_ordering_fence` 2 passed).
      `grep -q "CON-criticism-source.md" docs/map/INDEX.md` -> exit 0
      (line 62).
      `python tools/docs_verify.py --fast`:
      ```
      docs_verify [fast]: 48 documents, 760 checks, 760 reused
      docs_verify: 0 failed
      ```
- [x] 8. (S4) [COMMIT] Commit step 7, push with retry.
      done-when: new commit on branch AND clean tree.
      DONE — committed together with step 7's write.

- [x] 9. (S5) Create `docs/map/CON-scheduler-ranking.md` (same anatomy;
      cite the already-check-backed "operator's seed question wins ties"
      and "import-role never counts as survivor" claims from
      `SUB-scheduler.md`'s Traps rather than re-deriving new checks for
      them). Add its row to `INDEX.md`'s Concepts table.
      done-when: `python tools/docs_verify.py --links` reports 0 dangling
      AND `grep -q "DR-CON-scheduler-ranking" docs/map/INDEX.md` AND the
      file's own checks exit 0 (paste).
      DONE (correct string per step 5's note: `CON-scheduler-ranking.md`).
      All 6 new checks verified individually first (4 grep one-liners +
      the package-wide no-write/no-status-mutate check, all OK; the 3
      pytest-backed checks: `test_operator_question_outranks_spawns_at_
      cycle_zero`, `test_focus_family_restricts_selection`, `test_
      reflexive_budget_follows_lineage` — 3 passed).
      `grep -q "CON-scheduler-ranking.md" docs/map/INDEX.md` -> exit 0
      (line 63).
      `python tools/docs_verify.py --fast`:
      ```
      docs_verify [fast]: 49 documents, 760 checks, 759 reused, 4 workers
      docs_verify: 0 failed
      ```
- [x] 10. (S5) [COMMIT] Commit step 9, push with retry.
      done-when: new commit on branch AND clean tree.
      DONE — committed together with step 9's write. This completes R1
      (all five sockets: S1-S5).

- [x] 11. (S6) Batch A — add `## Seams` table (documented seams glossed
      from the seam doc's "The agreement"; undocumented pairs glossed
      honestly) to: `SUB-adjudication.md`, `SUB-amendment.md`,
      `SUB-application.md`, `SUB-bridge.md`.
      done-when: `for f in adjudication amendment application bridge; do
      grep -q "^## Seams" docs/map/SUB-$f.md || exit 1; done` exits 0 AND
      `python tools/docs_verify.py --links` reports 0 dangling.
      DONE, with a real bug caught and fixed along the way: adding the
      section broke `SUB-adjudication.md`'s existing "Where to change
      what" row-count check (it counted ALL `| ` lines in the whole file,
      which was safe when there was one table and stopped being safe once
      a second table existed). Fixed the check to scope to the section
      between `## Where to change what` and `## Traps` — a scoping fix,
      not a weakened assertion; the claim (11 rows, 6 hitting
      `tests/test_adjudication.py`) is unchanged and still verified true.
      Also folded in: `SUB-bridge.md`'s header corrected per the E9 audit
      (`DR-SEAM-bridge-x-llm` moved from `Seams-undocumented:` to `Seams:`
      — the file exists and is now cited in its own Seams table).
      `for f in adjudication amendment application bridge; do grep -q
      "^## Seams" docs/map/SUB-$f.md || exit 1; done` -> exit 0.
      `python tools/docs_verify.py --fast`:
      ```
      docs_verify [fast]: 49 documents, 760 checks, 758 reused, 4 workers
      docs_verify: 0 failed
      ```
- [x] 12. (S6) [COMMIT] Commit step 11, push with retry.
      done-when: new commit on branch AND clean tree.
      DONE — committed together with step 11's write.

- [x] 13. (S6) Batch B — same treatment for: `SUB-capabilities.md`,
      `SUB-evaluation.md`, `SUB-harness.md`, `SUB-llm.md`.
      done-when: `for f in capabilities evaluation harness llm; do grep -q
      "^## Seams" docs/map/SUB-$f.md || exit 1; done` exits 0 AND
      `python tools/docs_verify.py --links` reports 0 dangling.
      DONE. Also fixed per the E9 audit: `SUB-harness.md`'s header (both
      `DR-SEAM-harness-x-verification` and `DR-SEAM-harness-x-workflow`
      moved from `Seams-undocumented:` to `Seams:` — the header was
      entirely empty despite two real seam documents) and `SUB-llm.md`'s
      header (`DR-SEAM-bridge-x-llm` added). Several "deliberately absent"
      findings surfaced directly from each file's own existing checks
      (llm/ proven to never import verification/scheduler/harness; harness
      proven to never import llm) rather than guessed.
      `for f in capabilities evaluation harness llm; do grep -q "^##
      Seams" docs/map/SUB-$f.md || exit 1; done` -> exit 0.
      `python tools/docs_verify.py --fast`:
      ```
      docs_verify [fast]: 49 documents, 760 checks, 760 reused
      docs_verify: 0 failed
      ```
- [x] 14. (S6) [COMMIT] Commit step 13, push with retry.
      done-when: new commit on branch AND clean tree.
      DONE — committed together with step 13's write.

- [x] 15. (S6) Batch C — same treatment for: `SUB-manifest.md`,
      `SUB-ontology.md`, `SUB-periphery.md`, `SUB-rules.md`.
      done-when: `for f in manifest ontology periphery rules; do grep -q
      "^## Seams" docs/map/SUB-$f.md || exit 1; done` exits 0 AND
      `python tools/docs_verify.py --links` reports 0 dangling.
      DONE. Per the E9 audit: `SUB-manifest.md`'s header fixed
      (`DR-SEAM-llm-x-manifest` and `DR-SEAM-manifest-x-schools` moved
      from undocumented) and `SUB-ontology.md`'s (`DR-SEAM-evaluation-x-
      ontology` added). `SUB-rules.md`'s header was already fully correct
      (all 8 of its seam docs matched real files) — only the prose table
      was new. `manifest x rules` and `harness x rules` both confirmed
      deliberately absent from BOTH sides independently (manifest's own
      exclusion check names `rules`; rules' own check names `harness`).
      `for f in manifest ontology periphery rules; do grep -q "^## Seams"
      docs/map/SUB-$f.md || exit 1; done` -> exit 0.
      `python tools/docs_verify.py --fast`:
      ```
      docs_verify [fast]: 49 documents, 760 checks, 759 reused, 4 workers
      docs_verify: 0 failed
      ```
- [x] 16. (S6) [COMMIT] Commit step 15, push with retry.
      done-when: new commit on branch AND clean tree.
      DONE — committed together with step 15's write.

- [ ] 17. (S6) Batch D — same treatment for: `SUB-scheduler.md`,
      `SUB-scratch.md`, `SUB-verification.md`, `SUB-workflow.md`. This
      completes all 16 files.
      done-when: `for f in docs/map/SUB-*.md; do grep -q "^## Seams" "$f"
      || exit 1; done` exits 0 (whole-set proof, all 16) AND
      `python tools/docs_verify.py --links` reports 0 dangling.
- [ ] 18. (S6) [COMMIT] Commit step 17, push with retry.
      done-when: new commit on branch AND clean tree.

- [ ] 19. (S7) Add `## Triage: is a change isolated, or does it need
      REC-change-a-seam?` to `docs/map/SCHEMA.md`, placed directly before
      `## How to CHANGE the map`, per SPEC.md's S7 content (the decidable
      rule: seam-document membership or multi-document `Owns:` overlap
      triggers `REC-change-a-seam.md`; otherwise isolated). Advance
      `Verified-at:`.
      done-when: `grep -q "Triage: is a change isolated" docs/map/SCHEMA.md`
      AND `python tools/docs_verify.py --self-test` exits 0 (paste).
- [ ] 20. (S7) [COMMIT] Commit step 19, push with retry.
      done-when: new commit on branch AND clean tree.

- [ ] 21. (S8, R4) Scope-boundary proof: confirm zero `src/` changes across
      the whole tranche.
      done-when: `git diff --stat <tranche-base-sha>..HEAD -- src/` prints
      nothing (paste the empty result and the base sha it was measured
      against).
- [ ] 22. (S9, R5) Full map gate, all three modes, pasted in full:
      `python tools/docs_verify.py` (expect 0 failed),
      `python tools/docs_verify.py --audit` (expect 0 findings against the
      checks added in steps 1-19), `python tools/docs_verify.py --links`
      (expect 0 dangling).
      done-when: all three commands exit 0 and their output is pasted
      verbatim into the step's execution record.
- [ ] 23. (all) Full gate, confirmatory (no `src/` changed so no regression
      is expected; run per CLAUDE.md/dr-plan-steps boilerplate anyway):
      `python -m pytest tests/ -q -n 4`.
      done-when: output ends `N passed, 0 failed` (paste the final line).
- [ ] 24. (all) [COMMIT] Final push and cleanliness check.
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD` equals `git rev-parse origin/claude/delivery-rungs-handover-m22sdy`.
