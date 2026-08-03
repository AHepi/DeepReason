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

No root sweep step: `tools/root_sweep.py` proves innocence for changes to a
READER, guard, or authority rule under `src/`; this tranche touches no
`src/` file (R4), so the sweep has nothing to compare and is not run.

- [ ] 1. (S1) Extend `docs/map/CON-schools.md`: add
      `## The socket contract — what it promises, what it is handed, what it must never do`
      after `## What it is`, before `## Where it lives`, per SPEC.md's S1
      bullet content (reuse existing checks where the claim is already
      checked elsewhere in the file; write one new minimal check only
      where none exists). Advance `Verified-at:` to the current HEAD short
      sha.
      done-when: `grep -q "The socket contract" docs/map/CON-schools.md`
      AND `python tools/docs_verify.py --ring schools` exits 0 (paste
      output).
- [ ] 2. (S1) [COMMIT] Commit step 1, push with retry (2s/4s/8s/16s).
      done-when: `git log -1 --format=%H` on the tranche branch shows the
      new commit AND `git status --porcelain` is empty.

- [ ] 3. (S2) Extend `docs/map/CON-authority.md`: add the same-titled
      socket-contract section per SPEC.md's S2 bullet content. Advance
      `Verified-at:`.
      done-when: `grep -q "The socket contract" docs/map/CON-authority.md`
      AND `python tools/docs_verify.py --ring authority` exits 0 (paste
      output).
- [ ] 4. (S2) [COMMIT] Commit step 3, push with retry.
      done-when: new commit on branch AND clean tree.

- [ ] 5. (S3) Create `docs/map/CON-conjecture-source.md` (full SCHEMA.md
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
- [ ] 6. (S3) [COMMIT] Commit step 5, push with retry.
      done-when: new commit on branch AND clean tree.

- [ ] 7. (S4) Create `docs/map/CON-criticism-source.md` (same anatomy).
      Add its row to `INDEX.md`'s Concepts table.
      done-when: `python tools/docs_verify.py --links` reports 0 dangling
      AND `grep -q "DR-CON-criticism-source" docs/map/INDEX.md` AND the
      file's own checks exit 0 (paste).
- [ ] 8. (S4) [COMMIT] Commit step 7, push with retry.
      done-when: new commit on branch AND clean tree.

- [ ] 9. (S5) Create `docs/map/CON-scheduler-ranking.md` (same anatomy;
      cite the already-check-backed "operator's seed question wins ties"
      and "import-role never counts as survivor" claims from
      `SUB-scheduler.md`'s Traps rather than re-deriving new checks for
      them). Add its row to `INDEX.md`'s Concepts table.
      done-when: `python tools/docs_verify.py --links` reports 0 dangling
      AND `grep -q "DR-CON-scheduler-ranking" docs/map/INDEX.md` AND the
      file's own checks exit 0 (paste).
- [ ] 10. (S5) [COMMIT] Commit step 9, push with retry.
      done-when: new commit on branch AND clean tree.

- [ ] 11. (S6) Batch A — add `## Seams` table (documented seams glossed
      from the seam doc's "The agreement"; undocumented pairs glossed
      honestly) to: `SUB-adjudication.md`, `SUB-amendment.md`,
      `SUB-application.md`, `SUB-bridge.md`.
      done-when: `for f in adjudication amendment application bridge; do
      grep -q "^## Seams" docs/map/SUB-$f.md || exit 1; done` exits 0 AND
      `python tools/docs_verify.py --links` reports 0 dangling.
- [ ] 12. (S6) [COMMIT] Commit step 11, push with retry.
      done-when: new commit on branch AND clean tree.

- [ ] 13. (S6) Batch B — same treatment for: `SUB-capabilities.md`,
      `SUB-evaluation.md`, `SUB-harness.md`, `SUB-llm.md`.
      done-when: `for f in capabilities evaluation harness llm; do grep -q
      "^## Seams" docs/map/SUB-$f.md || exit 1; done` exits 0 AND
      `python tools/docs_verify.py --links` reports 0 dangling.
- [ ] 14. (S6) [COMMIT] Commit step 13, push with retry.
      done-when: new commit on branch AND clean tree.

- [ ] 15. (S6) Batch C — same treatment for: `SUB-manifest.md`,
      `SUB-ontology.md`, `SUB-periphery.md`, `SUB-rules.md`.
      done-when: `for f in manifest ontology periphery rules; do grep -q
      "^## Seams" docs/map/SUB-$f.md || exit 1; done` exits 0 AND
      `python tools/docs_verify.py --links` reports 0 dangling.
- [ ] 16. (S6) [COMMIT] Commit step 15, push with retry.
      done-when: new commit on branch AND clean tree.

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
