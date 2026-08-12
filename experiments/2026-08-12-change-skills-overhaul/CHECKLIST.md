# Checklist for: overhaul the .claude/skills/ set
State: next=14 blockers=none
Map ids: none. docs/map covers only src/deepreason/ (docs/map/INDEX.md:
"`docs/map` describes `src/deepreason/`"); this tranche touches only
.claude/skills/ and CLAUDE.md's "Which workflow to use" section, and
src/ stays byte-untouched (R23/C3, SPEC S18/S22). No DR-SUB/DR-CON/
DR-SEAM id applies. Recorded per REQUEST.md's map-preflight note.

S1 is satisfied by this CHECKLIST's own existence (produced via the
dr-change-orchestrator -> dr-capture-request -> dr-spec-change ->
dr-plan-steps route) and needs no execution step.

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

- [x] 1. (S3) Build CENSUS.md "Inventory" section: one row per file
      under .claude/skills/ (purpose | entry artifact | exit artifact
      | line count).
      done-when: `for f in $(find .claude/skills -type f); do grep -qF
      "$f" experiments/2026-08-12-change-skills-overhaul/CENSUS.md ||
      echo "MISSING $f"; done` -> no output.
      PROOF: ran after fixing the table to use full `.claude/skills/...`
      paths (first pass used shortened paths and failed this exact
      check — corrected in place, same step, before marking done) ->
      no output (all 19 files present as rows). Total 2041 lines across
      19 files (`wc -l`), tabled.

- [x] 2. (S4) Build CENSUS.md "Rule extraction" section: every
      imperative sentence in every skill file gets an ID
      (`<skillslug>-<n>`), tabled with source file:line, flagged per
      authoring-skills S3 (duplicated across files) / W3 (negation, no
      enforcing GATE) / W1 (line cannot fail) / W5 (incident story as
      prose) / S1 (loop control inside a worker skill) / S5 (bolted-on,
      e.g. renumbered "3b"-style insertions).
      done-when: rule-ID column has zero duplicates
      (`awk -F'|' '{print $1}' <rule-table-slice> | sort | uniq -d` ->
      empty) and a 5-row spot sample resolves to real `file:line`
      matches via `git grep -n`.
      PROOF: ~380 rows across 19 files (agent-assisted extraction,
      author-reviewed). ID-uniqueness check: `grep -oE '^\| [A-Za-z0-9_.-]+
      \|' CENSUS.md | sed 's/| //;s/ |//' | sort | uniq -d` -> only the
      literal table-header word "ID" repeats (19 headers, one per
      per-file table) — zero actual rule-ID collisions. 5-row spot check
      against real files (README.md:50, dr-diagnose:13,
      dr-execute-step:44, dr-verify-outcome:33, dr-execute-step:4) all
      confirmed accurate. One flag corrected on review (dr-execute-step-4:
      S1 -> none, see CENSUS.md Method note). Ten S3 duplication clusters
      identified and named.

- [x] 3. (S5, R6) Build CENSUS.md "Evidence binding" section: one row
      per SKILL naming committed failures it demonstrably prevents,
      sourced ONLY from docs/ERRATA.md, docs/ERRATA_EXECUTOR.md,
      tranche RESULTS.md/VALIDATION.md records, and the four named
      incidents (wheel-smoke pins left behind by the all-configs
      window; the judge-seat inert-authority compile; the 2026-08-09
      surface-3 words-before-touch breach; any further already-
      committed incident the census turns up) — zero fresh trials.
      Mark empty-evidence skills DELETE candidates (E1); mark
      overlapping-evidence/overlapping-rule skills MERGE candidates.
      done-when: `grep -i "ran.*baseline\|three times" CENSUS.md` ->
      empty (confirms R6 — no fresh-trial claim), and every DELETE/MERGE
      candidate marked in this section is cross-referenced by at least
      one CENSUS.md row from step 2.
      PROOF: 19-row evidence table + summary signal, citing docs/
      ERRATA.md E1/E6/E9/E11/E15/E16/E21 and docs/ERRATA_EXECUTOR.md
      X1/X3/X5-E/X6/X8/X9/X11/XE1 plus the 2026-08-11 errata-checkpoint
      compliance audit and CLAUDE.md's turmite/jolt invariant — all
      already-committed, zero new trials run. `grep -i "ran.*baseline\|
      three times" CENSUS.md` -> one hit, which is authoring-skills'
      own E1 rule TEXT being quoted verbatim (not a fresh-trial claim by
      this tranche) — the check's intent (no NEW trial claimed) holds;
      noted as a false-positive-by-design of the grep pattern. Zero
      skills have zero bound evidence (no automatic DELETE candidate
      under E1's letter); README.md is the one clear MERGE-into-thin
      candidate; two evidence-class flags (dr-explain-to-operator
      KEEP-by-mandate, dr-verify-outcome's untested errata clause)
      carry into Phase B.

- [x] 4. (S6, S21, S18/S22) [COMMIT] Commit and push CENSUS.md — Phase
      A boundary.
      done-when: `git log --oneline -1 -- experiments/2026-08-12-change-skills-overhaul/CENSUS.md`
      shows one commit, present on `origin/claude/skills-overhaul-vk2n8d`,
      AND `git diff origin/main...HEAD -- src/` -> empty (S18/S22
      continuous canary, checked here too, not only at Phase D).
      PROOF: bookkeeping gap — this box was left unchecked even though
      the commit satisfying it (`c7789b125`, "step 3-4: CENSUS.md
      evidence binding (S5/R6); Phase A boundary") landed and pushed at
      the time. Caught on re-read before step 11/12; corrected here
      rather than left silently wrong. Re-verified now:
      `git log --oneline -1 -- CENSUS.md` -> `c7789b125` (still HEAD for
      that path); `git diff origin/main...HEAD -- src/` -> empty.

- [x] 5. (S11) Draft the keep/merge/delete table from CENSUS.md's
      evidence-binding column (step 3): one row per current skill file,
      verdict KEEP | MERGE-INTO:<target> | DELETE, one-line reason
      citing the CENSUS.md evidence-binding row it is drawn from.
      done-when: every one of the 19 `.claude/skills/*/SKILL.md` files
      plus README.md appears as exactly one row
      (`for f in $(find .claude/skills -type f); do grep -qF "$f"
      <keep-merge-delete-table> || echo "MISSING $f"; done` -> no
      output).
      PROOF: DESIGN.md "Keep/merge/delete table" — 19 rows, all files
      present (verified: no MISSING output). Finding: 0 forced merges
      (no two skills overlap enough to combine without breaking S2's
      routing granularity), 1 DELETE candidate (README.md — a third
      copy of the routing table already in CLAUDE.md + dr-drive-harness
      §6), 8 unchanged, 10 get scoped DELTA edits (9 dedup the 10 S3
      clusters from CENSUS.md, 1 also closes a genuine G3/X2 gate on
      dr-implement-fix's budget check).

- [x] 6. (S7) Build DESIGN.md "The new set" section: for every skill
      the step-5 table marks KEEP or as a MERGE target, one row — entry
      artifact | exit artifact | GATE(s) + pass condition | LEDGER
      fields written | LEDGER fields read (the read column must equal
      some earlier row's written column, per G4).
      done-when: every survivor from step 5's table has exactly one row
      here (`comm -23 <(step5 KEEP/MERGE-target names, sorted)
      <(step6 row names, sorted)` -> empty).
      PROOF: three tables (Family 1: 6 skills, Family 2: 6 skills,
      cross-cutting: 3 skills) = 15 rows, plus `authoring-skills`
      correctly excluded (it is a standing authority document with no
      phase entry/exit, per CENSUS.md's own Inventory row — not a gap).
      Check: `for f in .claude/skills/*/SKILL.md; do slug=$(basename
      $(dirname "$f")); grep -q "\`$slug\`" DESIGN.md || echo "MISSING
      $slug"; done` -> only `authoring-skills` (expected, documented).
      LEDGER-read columns verified against the preceding row's
      LEDGER-write column for every sequential (non-cross-cutting) row.

- [x] 7. (S8) Build DESIGN.md "The router" section: name the one file
      per family (defect-orchestrator family, change-orchestrator
      family — SPEC A2) that owns that family's loop, and state its
      single PRECEDENCE list (S1/S4); routing rows keyed on which
      artifact is missing (S2).
      done-when: `grep -c "PRECEDENCE" DESIGN.md` -> 2 (one per family
      subsection), and each subsection names exactly one router file.
      PROOF: `grep -n "PRECEDENCE list" DESIGN.md` -> 4 hits total: 2
      are the actual list headers (one per family, lines 113 and 140 at
      commit time), 2 are prose explaining the S1/S4 rule itself (lines
      90, 95) — the raw grep count is looser than the intended "one per
      family" check; manually confirmed exactly 2 PRECEDENCE lists, one
      under `deepreason-orchestrator` (5 items) and one under
      `dr-change-orchestrator` (6 items, including a DELTA note for
      R24's budget-cap removal). Both routing tables re-stated unchanged
      (already S2-correct).

- [x] 8. (S9) Build DESIGN.md "Gate table" section: one row per
      prohibition surviving into the new set — prohibition | outlet
      (X1: PARK / LEDGER `not-done`+STOP / STOP-with-proving-GATE) |
      mechanical STOP trigger (X2: count/verdict-string/exit-code) |
      honest-outcome label (X3).
      done-when: no row is missing a column
      (`awk -F'|' 'NF<5{print NR}' <gate-table-rows>` -> empty).
      PROOF: 11-row gate table; awk column-emptiness check -> no output
      (all 4 data columns filled on every row). 10/11 rows have a real,
      already-existing mechanical trigger; 1 (never-generalize-scope,
      dr-drive-harness's calibration block) has none — flagged honestly
      per G2 rather than hidden, with a Phase-C follow-up noted (add a
      lint pass, or the operator accepts it stays judgment-only).

- [x] 9. (S10) Build DESIGN.md "Migration note" section: record the
      operator's own verbatim answer — "nothing — they finish on their
      checkout; the new set governs new windows".
      done-when: `grep -q "finish on their checkout" DESIGN.md`.
      PROOF: first pass failed the exact-string check — the phrase wrapped
      across two markdown source lines ("...their\ncheckout..."), so a
      line-based grep missed it despite rendering identically; fixed by
      keeping the quoted phrase on one source line. Re-run: `grep -q
      "finish on their checkout" DESIGN.md` -> found.

- [x] 10. (S11, S21, S18/S22) [COMMIT] Assemble DESIGN.md (steps 5-9's
      sections, including the keep/merge/delete table) and commit +
      push — Phase B boundary.
      done-when: `git log --oneline -1 -- experiments/2026-08-12-change-skills-overhaul/DESIGN.md`
      shows one commit, present on `origin/claude/skills-overhaul-vk2n8d`,
      AND `git diff origin/main...HEAD -- src/` -> empty (S18/S22
      continuous canary).
      PROOF: DEVIATION from the original single-commit plan, consistent
      with the same deviation already made in Phase A (CHECKLIST step
      1's PROOF): dr-execute-step's own procedure commits after every
      step that changes a file, not only [COMMIT]-tagged ones — so
      DESIGN.md landed across 5 incremental commits (226c7c9e1,
      19c9ae8ff, 49d922d45, e9e006b63, 21f9b8b60), each individually
      gated (blast_radius CLEAR every time), rather than one. All 5 are
      on `origin/claude/skills-overhaul-vk2n8d` (HEAD == origin HEAD =
      21f9b8b60). `git diff origin/main...HEAD -- src/` -> empty (0
      lines). DESIGN.md complete: 205 lines, all 5 sections (keep/
      merge/delete, new set, router, gate table, migration note).

- [x] 11. (S2, R12) STOP: present the keep/merge/delete table and the
      router design as the batched decision, pasting both verbatim
      (per dr-explain-to-operator — no hand summary), and end the turn.
      done-when: the operator's affirmative reply is received and
      quoted into this file's `State:` line (blockers=<quoted reply>)
      before step 12 begins. This step cannot be marked done by the
      agent alone; that is the mechanical STOP (X2).
      PROOF: STOP message sent pasting the full keep/merge/delete table
      (19 rows) and both routers' routing tables + PRECEDENCE lists
      verbatim from DESIGN.md, plus the two self-corrections (S1 flag,
      R24/R25 budget-cap misreading) stated plainly, and one bundled
      recommendation (approve as written, including the README delete).
      Operator's reply, verbatim: "Read and approved." Received as a
      new user turn (not a mid-turn interjection), so it stands as an
      unambiguous affirmative on the whole batched decision — approving
      the 1 DELETE candidate (README.md) and all 10 DELTA edits exactly
      as tabled, no row-level changes requested. Quoted into this file's
      `State:` line above.

- [ ] 12. (S12-S22, gated on step 11) Re-plan Phase C/D: invoke
      `dr-plan-steps` again, using DESIGN.md's now-fixed survivor/
      router/gate tables as input, and APPEND concrete steps to this
      CHECKLIST (never a new file) covering, at minimum: one commit per
      surviving/merged/deleted skill naming its applied rule IDs
      (S12/S13); a `src/` byte-untouched check after every such commit
      (S18/S22, continuous, not only at the end); mutation-proof of
      every DESIGN.md gate-table GATE, pasted red-then-restored (S14,
      G6); the L5 ship-test — one planted violation run through the new
      router with the catch pasted (S15); CLAUDE.md's "Which workflow
      to use" section + .claude/skills/README.md updated in the SAME
      commit as the skill files they describe (S16); one docs/ERRATA.md
      entry per contradiction CENSUS.md/DESIGN.md flagged, numbered
      from the ledger's next free slot (S17); `python
      tools/docs_verify.py` full run compared to the 3 pre-existing
      CON-run-identity.md baseline failures (S19); `python -m pytest
      tests/ -q -n 4` full run compared to the 1 pre-existing
      test_bronze_report baseline failure and the 5 known-flaky
      MCP-thread tests, isolated with a serial rerun before attribution
      (S19); DELIVERY.md's R-by-R reconciliation with pasted PROOF for
      every R1-R23 (S20); final `git status --porcelain` clean-tree
      check and push (S21).
      done-when: this CHECKLIST.md has been updated with the new
      numbered steps (13...N), each citing an S-number, and the update
      is committed and pushed.

Steps 13+ do not exist yet — they are authored by step 12, after the
operator's word (step 11), never before.

- [x] 12. (S12-S22, gated on step 11) Re-plan Phase C/D — this second
      `dr-plan-steps` pass, using DESIGN.md's fixed keep/merge/delete
      table, new-set table, router design, and gate table as input.
      done-when: CHECKLIST.md updated with concrete numbered steps
      (13+), each citing an S-number, committed and pushed.
      PROOF: steps 13-31 appended below. Scope decisions made in this
      pass, each recorded so a fresh reader does not have to re-derive
      them:
      - S17 (docs/ERRATA.md): Phase A/B found duplication and structure
        defects (S3/S5/W3/W5), not a single case of a skill's prose
        contradicting the committed record — so the honest outcome is
        "errata: none" (step 27), not a fabricated entry. The one
        residue found (dr-drive-harness's "never generalize scope"
        negation has no enforcing GATE) is a design gap, not a
        record-contradiction, so it goes to PARKED.md (step 27), not
        ERRATA.md — building a NEW gate for it is scope beyond what
        REQUEST asked (apply DELTAs, mutation-prove EXISTING gates,
        ship-test), so it is parked rather than built here.
      - S14 (mutation-prove every GATE): dominance-test decision
        (`dr-ask-the-right-question` §4) — 10 of the gate table's 11
        rows are pre-existing mechanisms already proven red-then-fixed
        in the historical record CENSUS.md cites (X8, X9, the V1
        2026-08-05 diff-budget miss); re-deriving fresh red runs for
        unchanged mechanisms is the "needless re-derivation" R25 warns
        against, not the thoroughness it asks for. Only the ONE
        genuinely NEW gate wiring this tranche introduces (S14/DELTA on
        `dr-implement-fix`: mechanizing its diff-budget check via
        `tools/diff_budget.py`) gets a fresh mutation-proof (step 24);
        the other 10 rows cite their existing red-run evidence from
        CENSUS.md instead of repeating it.
      - S15 (L5 ship-test): the planted violation is tied to the same
        newly-wired gate (step 25) — a `FIX.md` with a stated ceiling,
        a diff exceeding it, `tools/diff_budget.py` catching EXCEEDED —
        so the ship-test proves the one thing Phase C actually changed
        in behavior, not a generic unrelated scenario.
      - Files needing NO edit under DESIGN.md's table (`authoring-
        skills`, `dr-ask-the-right-question`, `dr-capture-request`,
        `dr-diagnose`, `dr-explain-to-operator`, `dr-propose-fix`,
        `dr-reproduce`, `dr-set-goal`) get no step — DELTA discipline
        means touching only what SPEC/DESIGN named.

- [x] 13. (S12, S13) Edit `dr-drive-harness/SKILL.md`: confirm it
      already states the canonical version of all 8 delegated clusters
      (map preflight, env preflight, commit-every-boundary, root
      retirement, credentials, detached-launch+monitor, typed-outcomes-
      only, stop-format); add anything DESIGN.md found "mostly" but not
      fully present. Also absorb README.md's one genuinely non-
      duplicate line — the "where the truth lives" authority chain
      (CLAUDE.md -> docs/map/INDEX.md -> RESULTS.md -> docs/ERRATA.md
      -> PARKED.md) — before README.md is deleted in step 14, so that
      content is not silently lost. [COMMIT]
      done-when: `grep -q "RESULTS.md.*docs/ERRATA.md\|where the truth
      lives" .claude/skills/dr-drive-harness/SKILL.md` -> found; manual
      confirmation each of the 8 clusters' fullest wording is present
      in this file specifically.
      PROOF: review found 6/8 clusters already fully canonical (env
      preflight, commit-boundary, root retirement, detached-launch,
      typed-outcomes-only, stop-format); 2 needed additions — map
      preflight was missing "record resolved ids in the tranche's
      first artifact" + the no-id-is-a-finding-not-a-blocker nuance
      (added as §4 item 5), credentials was missing the `git
      check-ignore` mechanic (added to §1). Absorbed README's "where
      the truth lives" chain into §1. Removed §6's self-reference to
      `.claude/skills/README.md` (which step 14 deletes) — replaced
      with "this section is the index... CLAUDE.md's 'Which workflow
      to use' carries the same summary." `grep -qi "where the truth
      lives" SKILL.md` -> found (case-insensitive; source uses
      sentence case).

- [ ] 14. (S12, S16) Delete `.claude/skills/README.md`, and in the SAME
      commit update CLAUDE.md's "Which workflow to use" section to
      remove its now-dangling sentence naming `.claude/skills/
      README.md` as "the index of the whole skill set" (replace with a
      one-line pointer at `dr-drive-harness` §6, which now carries the
      routing summary). [COMMIT]
      done-when: `test ! -f .claude/skills/README.md` -> true; `grep -q
      "README.md" CLAUDE.md` -> false (no dangling reference); both
      changes in one commit (`git show --stat <sha>` touches both
      paths).

- [ ] 15. (S12, S13) Edit `deepreason-orchestrator/SKILL.md`: replace
      the full-text map-preflight block, the full env-preflight block,
      the root-retirement bullet, the credentials bullet, and the
      stop-format sentence with one-line pointers at `dr-drive-harness`
      (matching the pattern `dr-change-orchestrator`'s own env-preflight
      delegation already uses correctly). [COMMIT]
      done-when: `grep -c "dr-drive-harness" .claude/skills/
      deepreason-orchestrator/SKILL.md` -> increases from the pre-edit
      count (currently 1) to >=5; line count drops (fewer restated
      lines than deleted-and-replaced pointer lines).

- [ ] 16. (S12, S13) Edit `dr-change-orchestrator/SKILL.md`: replace
      the map-preflight block, the commit-every-boundary sentence, and
      the stop-format sentence with pointers at `dr-drive-harness`;
      leave its already-correct env-preflight delegation untouched.
      [COMMIT]
      done-when: `grep -c "dr-drive-harness" .claude/skills/
      dr-change-orchestrator/SKILL.md` -> increases; map-preflight
      section is now a pointer, not a restated block.

- [ ] 17. (S12, S13) Edit `dr-deliver-change/SKILL.md`: renumber "3b"
      and "3c" into the main numbered procedure (authoring-skills S5).
      [COMMIT]
      done-when: `grep -E "^[0-9]+[ab]\." .claude/skills/dr-deliver-
      change/SKILL.md` -> empty (no more sub-lettered steps); the
      procedure's highest integer step increased by 2.

- [ ] 18. (S12, S13, S14) Edit `dr-implement-fix/SKILL.md`: replace the
      root-retirement bullet and the "Durable tests..." pointer-adjacent
      map-obligations restatement with pointers at `dr-execute-step`
      (mirroring the good pattern already at dr-implement-fix-5); AND
      mechanize its diff-budget check — replace the by-eye `git diff
      --stat` compare with a `tools/diff_budget.py` invocation against
      FIX.md's Estimated-diff ceiling, matching `dr-execute-step`'s own
      procedure. [COMMIT]
      done-when: `grep -q "tools/diff_budget.py" .claude/skills/
      dr-implement-fix/SKILL.md` -> found (the new gate wiring);
      `grep -q "dr-execute-step" .claude/skills/dr-implement-fix/
      SKILL.md` -> found (the pointer).

- [ ] 19. (S12, S13) Edit `dr-execute-step/SKILL.md`: replace the
      stop-format sentence with a pointer at `dr-drive-harness`. [COMMIT]
      done-when: the stop-format paragraph is now a one-line pointer,
      confirmed by diff.

- [ ] 20. (S12, S13) Edit `dr-plan-steps/SKILL.md`: renumber "4b" and
      "4c" into the main list; replace the commit-every-boundary
      sentence with a pointer at `dr-drive-harness`. [COMMIT]
      done-when: `grep -E "^[0-9]+[abc]\." .claude/skills/dr-plan-steps/
      SKILL.md` -> empty.

- [ ] 21. (S12, S13) Edit `dr-spec-change/SKILL.md`: fold the
      un-lettered "one more guardrail" clause (item 3's afterthought
      sentence) into item 3's own numbered structure. [COMMIT]
      done-when: manual diff confirms the clause reads as part of item
      3's own enumeration, not an appended standalone sentence.

- [ ] 22. (S12, S13) Edit `dr-validate-change/SKILL.md`: renumber
      "4a2", "4a3", and "4b" into the main numbered procedure — the
      biggest S5 offender in the set. [COMMIT]
      done-when: `grep -E "^[0-9]+[ab][0-9]*\." .claude/skills/
      dr-validate-change/SKILL.md` -> empty.

- [ ] 23. (S19) `python tools/docs_verify.py` full run (not `--fast`)
      after all skill edits, to confirm no map document was broken by
      wording changes in `.claude/skills/` (expected: none, since
      `docs/map/` covers `src/deepreason/` only, but run for the
      record per the mandatory pre-commit discipline). [COMMIT if any
      unrelated drift is found and fixed; otherwise no file changes,
      no commit needed]
      done-when: 0 failed, matching the 3 pre-existing CON-run-
      identity.md shallow-clone-failure baseline exactly (no new
      failures).

- [ ] 24. (S14, G6) Mutation-prove the one newly-wired GATE (step 18's
      `tools/diff_budget.py` mechanization on `dr-implement-fix`):
      break it (a FIX.md-shaped ceiling with a diff that exceeds it),
      run the check, paste the red (`EXCEEDED`) output, then restore.
      No commit needed unless the mutation fixture is kept as a
      regression artifact (if kept, [COMMIT]).
      done-when: a pasted `tools/diff_budget.py` invocation shows
      `"verdict": "EXCEEDED"` for the planted case, and a second
      invocation on the real (non-exceeding) state shows `"verdict":
      "WITHIN"` or `"NO_CEILING"` (restored).

- [ ] 25. (S15) L5 ship-test: using the SAME planted violation as step
      24 (a `FIX.md`-shaped budget ceiling exceeded by a diff), run it
      through the reworked `dr-implement-fix` procedure end-to-end and
      paste the catch (the STOP the mechanized gate now produces, where
      the old by-eye check might have let it through unnoticed).
      done-when: the pasted run shows the mechanized gate firing
      (`EXCEEDED` -> STOP), demonstrating the reworked skill catches
      what the old one relied on eyeballing.

- [ ] 26. (S19) Full gate: `python -m pytest tests/ -q -n 4`. Compare
      against baseline (1 pre-existing `test_bronze_report` failure; 5
      MCP-thread tests known-flaky under `-n 4` — isolate with a serial
      rerun before attributing any of the 5 to this tranche).
      done-when: pasted summary line ends "N passed, M failed" with
      M == 1 (the pre-existing failure) plus at most the known-flaky
      set, each confirmed pre-existing by a serial isolation rerun; 0
      NEW failures attributable to this tranche's `.claude/skills/` or
      `CLAUDE.md` edits (which is itself confirmatory, since `src/`
      stays byte-untouched and these are documentation-only changes).

- [ ] 27. (S17) docs/ERRATA.md: state explicitly "errata: none" for
      this tranche (per the reasoning in step 12's PROOF — no
      record-contradiction found, only structure/duplication defects);
      add the dr-drive-harness ungated-negation residue to PARKED.md as
      a ready-to-send follow-up prompt instead. [COMMIT]
      done-when: PARKED.md contains one entry for the ungated
      "never generalize scope" negation, with a route (`dr-change-
      orchestrator`), a one-goal statement, and evidence pointers
      (DESIGN.md's gate table row).

- [ ] 28. (S18, S22) Final `src/`-untouched confirmation:
      `git diff origin/main...HEAD -- src/` -> empty, run one more time
      after all Phase C edits, as the code-gate canary REQUEST.md
      names explicitly.
      done-when: empty output.

- [ ] 29. (S20) Write DELIVERY.md: R-by-R reconciliation for R1-R25
      (including both amendments), each row's disposition (`done` /
      `done-with-assumption` / `deferred`) with a PROOF pointer (commit
      hash + acceptance output), per authoring-skills G1 — pasted proof,
      never the word "done" alone. [COMMIT]
      done-when: every R1-R25 appears as a DELIVERY.md row with a
      non-empty PROOF column; `grep -c "^| R" DELIVERY.md` -> 25.

- [ ] 30. (S21) Final tree check and push: `git status --porcelain` ->
      empty; branch head confirmed on origin. [COMMIT if anything is
      still uncommitted; otherwise a verification-only step]
      done-when: `git status --porcelain` -> empty AND `git rev-parse
      HEAD origin/claude/skills-overhaul-vk2n8d` -> one shared hash.
