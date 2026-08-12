# Checklist for: overhaul the .claude/skills/ set
State: next=9 blockers=none
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

- [ ] 4. (S6, S21, S18/S22) [COMMIT] Commit and push CENSUS.md — Phase
      A boundary.
      done-when: `git log --oneline -1 -- experiments/2026-08-12-change-skills-overhaul/CENSUS.md`
      shows one commit, present on `origin/claude/skills-overhaul-vk2n8d`,
      AND `git diff origin/main...HEAD -- src/` -> empty (S18/S22
      continuous canary, checked here too, not only at Phase D).

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

- [ ] 9. (S10) Build DESIGN.md "Migration note" section: record the
      operator's own verbatim answer — "nothing — they finish on their
      checkout; the new set governs new windows".
      done-when: `grep -q "finish on their checkout" DESIGN.md`.

- [ ] 10. (S11, S21, S18/S22) [COMMIT] Assemble DESIGN.md (steps 5-9's
      sections, including the keep/merge/delete table) and commit +
      push — Phase B boundary.
      done-when: `git log --oneline -1 -- experiments/2026-08-12-change-skills-overhaul/DESIGN.md`
      shows one commit, present on `origin/claude/skills-overhaul-vk2n8d`,
      AND `git diff origin/main...HEAD -- src/` -> empty (S18/S22
      continuous canary).

- [ ] 11. (S2, R12) STOP: present the keep/merge/delete table and the
      router design as the batched decision, pasting both verbatim
      (per dr-explain-to-operator — no hand summary), and end the turn.
      done-when: the operator's affirmative reply is received and
      quoted into this file's `State:` line (blockers=<quoted reply>)
      before step 12 begins. This step cannot be marked done by the
      agent alone; that is the mechanical STOP (X2).

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
