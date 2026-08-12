# Request: overhaul the .claude/skills/ set

Captured: 2026-08-12 from the operator's task message (relayed via the
change-tranche task description that opened this session) and the
operator's verbatim 2026-08-12 words quoted inside it.

## Verbatim

> Change tranche: overhaul the .claude/skills/ set per the committed
> authority .claude/skills/authoring-skills/SKILL.md. Route through
> dr-change-orchestrator (yes — the current workflow rewrites itself;
> it is the last thing it does in its current form). ONE batched STOP
> at the end of Phase B; no other stops.

> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/skills-overhaul-vk2n8d origin/main; git merge-base
> --is-ancestor 49486fe5f HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`, never
> bare pytest. Read CLAUDE.md in full, then
> .claude/skills/authoring-skills/SKILL.md in full — it is the binding
> authority for every artifact this tranche writes, including its own
> tranche documents where applicable.

> AUTHORITY for REQUEST.md, operator verbatim (2026-08-12): "The
> workflow is failing big time. Using the already available evidence
> to rewrite the setup. Forget the trials I was proposing. ... start
> with the overhaul of skills according to the document I have
> attached."

> OPERATOR OVERRIDE, ledgered: authoring-skills E1's run-three-times
> baseline is satisfied by ALREADY COMMITTED evidence — docs/ERRATA.md,
> docs/ERRATA_EXECUTOR.md, tranche RESULTS/VALIDATION records, and the
> recent incident set (wheel-smoke pins left behind by the all-configs
> window despite the same-commit rule being written down; the
> judge-seat run compiled inert authority settings the roster prose
> asserted were on; the surface-3 words-before-touch breach of
> 2026-08-09). No new trials.

> PHASE A — CENSUS (read-only). (1) Inventory every file under
> .claude/skills/ — one row each: purpose, entry/exit state, line
> count. (2) Rule extraction: every imperative rule in every skill,
> assigned an ID, tabled with its source file. Flag per
> authoring-skills: duplicated rules across files (S3), negations with
> no enforcing GATE (W3), lines that cannot fail (W1), incident stories
> carried as prose (W5), loop control inside worker skills (S1),
> bolted-on rules (S5). (3) Evidence binding: for each SKILL, the
> committed failures it demonstrably prevents (errata ids, tranche
> records, incident dates). A skill with no bound evidence is a DELETE
> candidate (E1); overlapping skills are MERGE candidates. CENSUS.md is
> the artifact.

> PHASE B — DESIGN. (1) The new set: for each surviving SKILL — its
> one entry artifact, one exit artifact, its GATEs with pass
> conditions, its LEDGER writes/reads (G4/G5: obligations open the
> NEXT step, live requirement rows). (2) The ROUTER: one file owning
> the loop and the single PRECEDENCE list (S1/S4); routing decided by
> which artifact is missing (S2). (3) The GATE table: every prohibition
> paired with its outlet (X1), every STOP trigger mechanical (X2),
> every honest outcome labeled (X3). (4) Migration note: what happens
> to windows in flight on the old skills (answer: nothing — they
> finish on their checkout; the new set governs new windows).
> DESIGN.md + the keep/merge/delete table. STOP HERE: present the
> keep/merge/delete list and the router design as the batched decision
> — deletions execute only on the operator's word.

> PHASE C — EXECUTE (after the word). Rewrite by DELTA discipline: one
> commit per skill (or per merge/delete), each commit message naming
> the rule IDs applied. New/rewritten skills contain zero narrative,
> zero negation-without-gate, operation-shaped lines only. Mutation-
> prove every GATE once (G6: break the guarded thing, watch red,
> restore — paste the red run as PROOF in the tranche record). L5
> ship-test: plant one violation the reworked set should catch, run
> the workflow against it, paste the catch. Update CLAUDE.md's "Which
> workflow to use" section and .claude/skills/README.md in the SAME
> commits as the skills they describe. Where an old skill's prose
> claimed something the record contradicts, that is a
> docs/ERRATA.md entry (next free number — check the ledger tail; it
> has moved five times this week).

> PHASE D — VALIDATE + DELIVER. The gates here are mostly the
> tranche's own L5/G6 proofs plus: docs_verify full (baseline: 3
> pre-existing CON-run-identity.md shallow-clone failures), full
> pytest gate once (baseline: 1 pre-existing test_bronze_report
> failure; 5 MCP-thread tests known-flaky under -n 4, isolate before
> attributing) — the code gate is a canary that no skill edit leaked
> into src/, which stays byte-untouched this tranche. DELIVERY.md
> reconciles R-by-R with PROOF per authoring-skills G1 — pasted gate
> output, not the word "done". Commit and push every phase boundary
> (retry 2s/4s/8s/16s).

> PARKED BY DESIGN (do not do here): the full repo sweep/smoke re-pin
> audit (next tranche, operator-ordered); any src/ change; CLAUDE.md
> sections other than the workflow-routing section.

## Requirements

R1 (process): "Route through dr-change-orchestrator" — this tranche
   runs under the change-workflow, phase by phase.

R2 (process): "ONE batched STOP at the end of Phase B; no other
   stops." — the workflow must not stop at any other point.

R3 (artifact): "PHASE A — CENSUS (read-only)... (1) Inventory every
   file under .claude/skills/ — one row each: purpose, entry/exit
   state, line count." → CENSUS.md inventory table.

R4 (artifact): "(2) Rule extraction: every imperative rule in every
   skill, assigned an ID, tabled with its source file. Flag per
   authoring-skills: duplicated rules across files (S3), negations
   with no enforcing GATE (W3), lines that cannot fail (W1), incident
   stories carried as prose (W5), loop control inside worker skills
   (S1), bolted-on rules (S5)." → CENSUS.md rule table with flags.

R5 (artifact): "(3) Evidence binding: for each SKILL, the committed
   failures it demonstrably prevents (errata ids, tranche records,
   incident dates). A skill with no bound evidence is a DELETE
   candidate (E1); overlapping skills are MERGE candidates." →
   CENSUS.md evidence-binding table + keep/merge/delete signal.

R6 (behavior): "authoring-skills E1's run-three-times baseline is
   satisfied by ALREADY COMMITTED evidence... No new trials." — do not
   run fresh E1 trials; cite the named committed evidence sources
   instead.

R7 (artifact): "PHASE B — DESIGN. (1) The new set: for each surviving
   SKILL — its one entry artifact, one exit artifact, its GATEs with
   pass conditions, its LEDGER writes/reads (G4/G5...)." → DESIGN.md
   per-skill table.

R8 (artifact): "(2) The ROUTER: one file owning the loop and the
   single PRECEDENCE list (S1/S4); routing decided by which artifact
   is missing (S2)." → DESIGN.md router design.

R9 (artifact): "(3) The GATE table: every prohibition paired with its
   outlet (X1), every STOP trigger mechanical (X2), every honest
   outcome labeled (X3)." → DESIGN.md gate table.

R10 (artifact): "(4) Migration note: what happens to windows in
   flight on the old skills (answer: nothing — they finish on their
   checkout; the new set governs new windows)." → DESIGN.md migration
   note (answer given verbatim by the operator).

R11 (artifact): "DESIGN.md + the keep/merge/delete table." → both
   committed at Phase B boundary.

R12 (process): "STOP HERE: present the keep/merge/delete list and the
   router design as the batched decision — deletions execute only on
   the operator's word." — hard stop after Phase B; do not execute
   Phase C without an explicit operator go-ahead.

R13 (behavior, deferred by R12): "PHASE C — EXECUTE (after the word).
   Rewrite by DELTA discipline: one commit per skill (or per
   merge/delete), each commit message naming the rule IDs applied."

R14 (behavior, deferred by R12): "New/rewritten skills contain zero
   narrative, zero negation-without-gate, operation-shaped lines
   only."

R15 (behavior, deferred by R12): "Mutation-prove every GATE once (G6:
   break the guarded thing, watch red, restore — paste the red run as
   PROOF in the tranche record)."

R16 (behavior, deferred by R12): "L5 ship-test: plant one violation
   the reworked set should catch, run the workflow against it, paste
   the catch."

R17 (behavior, deferred by R12): "Update CLAUDE.md's 'Which workflow
   to use' section and .claude/skills/README.md in the SAME commits as
   the skills they describe."

R18 (behavior, deferred by R12): "Where an old skill's prose claimed
   something the record contradicts, that is a docs/ERRATA.md entry
   (next free number — check the ledger tail; it has moved five times
   this week)."

R19 (artifact, deferred by R12): "PHASE D — VALIDATE + DELIVER... the
   code gate is a canary that no skill edit leaked into src/, which
   stays byte-untouched this tranche."

R20 (artifact, deferred by R12): "docs_verify full (baseline: 3
   pre-existing CON-run-identity.md shallow-clone failures), full
   pytest gate once (baseline: 1 pre-existing test_bronze_report
   failure; 5 MCP-thread tests known-flaky under -n 4, isolate before
   attributing)."

R21 (artifact, deferred by R12): "DELIVERY.md reconciles R-by-R with
   PROOF per authoring-skills G1 — pasted gate output, not the word
   'done'."

R22 (process): "Commit and push every phase boundary (retry
   2s/4s/8s/16s)."

R23 (process, scope boundary): "PARKED BY DESIGN (do not do here):
   the full repo sweep/smoke re-pin audit (next tranche,
   operator-ordered); any src/ change; CLAUDE.md sections other than
   the workflow-routing section."

## Standing constraints

C1: ".claude/skills/authoring-skills/SKILL.md ... it is the binding
   authority for every artifact this tranche writes, including its own
   tranche documents where applicable." — SETUP paragraph. Every
   artifact this tranche produces (REQUEST.md, SPEC.md, CHECKLIST.md,
   CENSUS.md, DESIGN.md, DELIVERY.md included) must itself obey W1-W6,
   G1-G7, X1-X3 where applicable.

C2: "Use `python -m pytest`, never bare pytest." — SETUP paragraph.

C3: "src/, which stays byte-untouched this tranche." — Phase D
   paragraph; reinforced by R23's "any src/ change" park.

C4: "Never edit a committed run root's contents" / retirement
   discipline — inherited standing rule from CLAUDE.md, applies if any
   experiment root is touched (not expected in this tranche).

## Open questions (for dr-spec-change)

Q1: R12's operator go-ahead for Phase C — what form counts as "the
   operator's word"? (Likely: an explicit follow-up message after the
   Phase B STOP; dr-spec-change should record the mechanical trigger.)

Q2: The keep/merge/delete table format and the router file's name/path
   are not specified beyond "one file" — dr-spec-change should record
   the smallest reasonable choice (e.g. keep the existing
   `deepreason-orchestrator` / `dr-change-orchestrator` names if they
   survive as routers, or name new ones only if none currently owns a
   single PRECEDENCE list per family).

Q3: Two skill FAMILIES exist (defect-orchestrator, change-orchestrator)
   sharing cross-cutting skills. Does "one file owning the loop" (R8)
   mean one router per family (two routers total) or a literal single
   router file for both families? — the CLAUDE.md context this session
   was given states "Both families now begin with a MAP PREFLIGHT" and
   keeps them as two named entry points, suggesting two routers stay;
   dr-spec-change should confirm against authoring-skills S1/S4 (S4
   says "one PRECEDENCE list per skill set" — implying per-family, not
   global).

## Amendments

(append-only; none yet)
