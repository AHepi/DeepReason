# Checklist for: pipeline census — Rung D1 of the dual-mode conjecture program
State: next=8 blockers=none
Map ids scoped (per SPEC.md's map preflight): DR-SUB-capabilities,
DR-SUB-evaluation, DR-SUB-rules, DR-SUB-scheduler,
DR-CON-criticism-source, DR-CON-warrants-and-attacks,
DR-CON-capability-lifecycle, DR-CON-packs-and-token-economy,
DR-INV-frozen-surfaces. No SEAM document names the not-yet-existing
DR-CON-conjecture-kinds; it is an isolated new CON- document per
SCHEMA.md's triage rule (recorded in SPEC.md's map preflight section).
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

- [x] 1. (S3) REQUEST.md committed and pushed.
      done-when: `git show fbb5608c --stat` shows REQUEST.md created. DONE.
- [x] 2. (S4) SPEC.md committed and pushed.
      done-when: `git show 1144c283 --stat` shows SPEC.md created. DONE.
- [x] 3. (S5) Create CENSUS.md with its header and an empty section
      skeleton for all seven measurement sections (Executable-commitment
      paths, Criticism dispatch per kind, Refutation semantics per kind,
      R-g audit, Load-knob inventory, Historical encoding-failure
      evidence, plus a Summary), M-numbering starting at M1.
      done-when: `test -f experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md` -> exit 0. DONE.
- [x] 4. (S5) Gather and write "Executable-commitment paths": pasted
      commands for the four named paths (simulation/research proposal
      channels, `lambda_run`, the dead property-oracle path, safe-skeleton
      forbidden-case compilation) plus the bounded grep for any path
      these miss (exec/eval/compile/subprocess/ast.parse/Commitment(eval=)),
      each hit classified.
      done-when: CENSUS.md's "Executable-commitment paths" section has
      >=5 M-numbered rows, each followed by a fenced command+output block.
      DONE — M1-M5 written; M5's bounded grep found one adjacent
      surface (admission/adapters.py) reported as out-of-scope, not a
      new commitment path.
- [x] 5. (S5) [COMMIT] Commit and push CENSUS.md's first section.
      done-when: `git log --oneline -1` message names this step; push
      confirmed (retry 2s/4s/8s/16s on failure). DONE.
- [x] 6. (S6) Gather and write "Criticism dispatch per kind": the
      crit_program vs crit_argumentative/crit_argumentative_batch
      selection caller, pack-rendering kind-conditionals,
      ARGUMENTATIVE_AUTHORITY read+enforcement sites, and
      execution_backed/formally_backed semantics in rules/warrants.py.
      done-when: CENSUS.md's "Criticism dispatch per kind" section has
      >=4 M-numbered rows with pasted commands.
      DONE — M6-M9 written; M6 found a genuine kind-conditional
      scheduling term (_standing_recrit_pool ordering) flagged forward
      to the R-g audit section (S8) rather than judged here.
- [x] 7. (S6) [COMMIT] Commit and push.
      done-when: pushed, confirmed on origin. DONE.
- [ ] 8. (S7) Gather and write "Refutation semantics per kind": the
      DEMONSTRATIVE path (rules/crit.py:805), what a trial-guarded prose
      refutation can/cannot do, and suspended_unsupported dependent
      mechanics.
      done-when: CENSUS.md's "Refutation semantics per kind" section has
      >=3 M-numbered rows with pasted commands.
- [ ] 9. (S7) [COMMIT] Commit and push.
      done-when: pushed, confirmed on origin.
- [ ] 10. (S8) Run the R-g audit's three bounded greps (scheduler
      ranking terms; crit.py kind-conditional rendering; workflow/
      scheduler acceptance branches), read every hit, and record an
      explicit CONFIRMS/REFUTES verdict per sub-search with evidence.
      done-when: CENSUS.md's "R-g audit" section has three sub-sections
      (a)/(b)/(c), each with a pasted command and an explicit verdict
      line.
- [ ] 11. (S8) [COMMIT] Commit and push.
      done-when: pushed, confirmed on origin.
- [ ] 12. (S9) Gather and write the "Load-knob inventory" table: every
      budget/period/ceiling/share knob in config.py, v6_policy.py,
      capabilities/policy.py, run_manifest.py's CriticismPolicyV1, and
      scratch/ attention budgets, with name/location/unit/default/
      mint-time-vs-live-read columns, each mint-vs-live determination
      backed by a pasted command showing the actual read site.
      done-when: CENSUS.md's "Load-knob inventory" table has >=10 rows,
      each with a location cell that is a file:line.
- [ ] 13. (S9) [COMMIT] Commit and push.
      done-when: pushed, confirmed on origin.
- [ ] 14. (S10) Write the classification script/command for the
      historical encoding-failure evidence corpus (every
      experiments/**/log.jsonl root plus the named turmite/jolt roots),
      run it, and paste the fraction with numerator/denominator and
      per-root breakdown; quote the turmite/jolt diagnostic blobs
      verbatim.
      done-when: CENSUS.md's "Historical encoding-failure evidence"
      section has the pasted classification command, its output, and
      both named blobs quoted.
- [ ] 15. (S10) [COMMIT] Commit and push.
      done-when: pushed, confirmed on origin.
- [ ] 16. (S11) Write `docs/map/CON-conjecture-kinds.md` per SCHEMA.md's
      anatomy, with a `check:` line for every load-bearing claim, using
      S6-S8's CENSUS.md findings as its body.
      done-when: `test -f docs/map/CON-conjecture-kinds.md` -> exit 0;
      first line is `<!-- DR-CON-conjecture-kinds -->`.
- [ ] 17. (S11) Add `docs/map/CON-conjecture-kinds.md` to INDEX.md's
      concept table so `docs_verify --links` can resolve references to
      it.
      done-when: `grep -q "CON-conjecture-kinds.md" docs/map/INDEX.md`
      -> exit 0.
- [ ] 18. (S11) Run `python tools/docs_verify.py` and
      `python tools/docs_verify.py --audit` and
      `python tools/docs_verify.py --links`; fix any failing check IN
      THE NEW DOCUMENT ONLY (no other docs/map file is touched this
      tranche) until all three are clean.
      done-when: full-mode output ends "0 failed"; `--audit` reports 0
      findings; `--links` exits 0 (paste all three).
- [ ] 19. (S11) [COMMIT] Commit and push the new map document.
      done-when: pushed, confirmed on origin.
- [ ] 20. (S13) Record any defect noticed during steps 4-18 in
      PARKED.md with a ready-to-send `dr-set-goal` prompt, in the same
      shape as the S1/S6 tranches' own PARKED.md. If none found, record
      that explicitly in CENSUS.md's Summary instead of creating an
      empty PARKED.md.
      done-when: either PARKED.md exists with >=1 entry, or CENSUS.md's
      Summary states "no defects found this tranche" (mutually
      exclusive, one must hold).
- [ ] 21. (all) Write CENSUS.md's Summary section: one line per
      requirement R6-R11 pointing at its section, and the R-g audit's
      overall verdict stated plainly.
      done-when: CENSUS.md has a "Summary" section with 6 lines, one
      per R6-R11.
- [ ] 22. (all) [COMMIT] Commit and push the finished CENSUS.md.
      done-when: pushed, confirmed on origin.
- [ ] 23. (all) Map check: `python tools/docs_verify.py`
      done-when: output ends "0 failed" (paste it).
- [ ] 24. (all) Audit check: `python tools/docs_verify.py --audit`
      done-when: output reports 0 findings (paste it).
- [ ] 25. (all) Full gate: `python -m pytest tests/ -q -n 4`
      done-when: output ends "N passed, M failed" (paste it verbatim);
      any failure is read against S6's PARKED P1/P3 per SPEC.md
      Assumption A5 before being called a regression.
- [ ] 26. (all) [COMMIT] push and confirm clean tree.
      done-when: `git status --porcelain` is empty AND
      `git log --oneline -1 origin/claude/pipeline-census-d1-c9h41d`
      matches local HEAD.

## Amendments
(none yet — re-planning after a validation failure appends here,
never rewrites checked steps above)
