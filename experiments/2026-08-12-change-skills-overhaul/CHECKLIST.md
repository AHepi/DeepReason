# Checklist for: overhaul the .claude/skills/ set
State: next=1 blockers=none
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

- [ ] 1. (S3) Build CENSUS.md "Inventory" section: one row per file
      under .claude/skills/ (purpose | entry artifact | exit artifact
      | line count).
      done-when: `for f in $(find .claude/skills -type f); do grep -qF
      "$f" experiments/2026-08-12-change-skills-overhaul/CENSUS.md ||
      echo "MISSING $f"; done` -> no output.

- [ ] 2. (S4) Build CENSUS.md "Rule extraction" section: every
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

- [ ] 3. (S5, R6) Build CENSUS.md "Evidence binding" section: one row
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

- [ ] 4. (S6, S21, S18/S22) [COMMIT] Commit and push CENSUS.md — Phase
      A boundary.
      done-when: `git log --oneline -1 -- experiments/2026-08-12-change-skills-overhaul/CENSUS.md`
      shows one commit, present on `origin/claude/skills-overhaul-vk2n8d`,
      AND `git diff origin/main...HEAD -- src/` -> empty (S18/S22
      continuous canary, checked here too, not only at Phase D).

- [ ] 5. (S11) Draft the keep/merge/delete table from CENSUS.md's
      evidence-binding column (step 3): one row per current skill file,
      verdict KEEP | MERGE-INTO:<target> | DELETE, one-line reason
      citing the CENSUS.md evidence-binding row it is drawn from.
      done-when: every one of the 19 `.claude/skills/*/SKILL.md` files
      plus README.md appears as exactly one row
      (`for f in $(find .claude/skills -type f); do grep -qF "$f"
      <keep-merge-delete-table> || echo "MISSING $f"; done` -> no
      output).

- [ ] 6. (S7) Build DESIGN.md "The new set" section: for every skill
      the step-5 table marks KEEP or as a MERGE target, one row — entry
      artifact | exit artifact | GATE(s) + pass condition | LEDGER
      fields written | LEDGER fields read (the read column must equal
      some earlier row's written column, per G4).
      done-when: every survivor from step 5's table has exactly one row
      here (`comm -23 <(step5 KEEP/MERGE-target names, sorted)
      <(step6 row names, sorted)` -> empty).

- [ ] 7. (S8) Build DESIGN.md "The router" section: name the one file
      per family (defect-orchestrator family, change-orchestrator
      family — SPEC A2) that owns that family's loop, and state its
      single PRECEDENCE list (S1/S4); routing rows keyed on which
      artifact is missing (S2).
      done-when: `grep -c "PRECEDENCE" DESIGN.md` -> 2 (one per family
      subsection), and each subsection names exactly one router file.

- [ ] 8. (S9) Build DESIGN.md "Gate table" section: one row per
      prohibition surviving into the new set — prohibition | outlet
      (X1: PARK / LEDGER `not-done`+STOP / STOP-with-proving-GATE) |
      mechanical STOP trigger (X2: count/verdict-string/exit-code) |
      honest-outcome label (X3).
      done-when: no row is missing a column
      (`awk -F'|' 'NF<5{print NR}' <gate-table-rows>` -> empty).

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
