# Design for: overhaul the .claude/skills/ set

## Keep/merge/delete table

Finding, stated plainly before the table: CENSUS.md's evidence-binding
pass (Phase A) found ZERO skills with no bound evidence (authoring-skills
E1's literal DELETE bar) and ZERO pairs of skills whose PURPOSE overlaps
enough to combine into one file without breaking S2 ("route on which
artifact is missing" — each surviving phase owns one distinct artifact;
merging two phases would collapse that routing granularity). What Phase A
actually found is ten clusters of DUPLICATED RULE TEXT (CENSUS.md's
"Cross-file duplication clusters") spread across otherwise-distinct
files — the correct authoring-skills fix for that is S3 DELTA-editing
(state the rule once, point to it elsewhere), not merging files. One
exception is argued below: `.claude/skills/README.md`.

| File | Verdict | Reason (cites CENSUS.md) |
|---|---|---|
| `.claude/skills/README.md` | **DELETE candidate** | Evidence binding: "MERGE candidate — thin distinct content once clusters 1/3 are deduplicated." Its two phase tables and "rules that hold it together" list are now a THIRD copy of the same routing summary already in CLAUDE.md's "Which workflow to use" section (which every session reads at preflight, per `dr-drive-harness` §1) and `dr-drive-harness` §6 ("Routing to the workflows"). No committed session-start procedure directs a reader to open `.claude/skills/README.md` specifically before those two. Deletion is a candidate, not a foregone conclusion — flagged here for the operator's word per R12, not executed. |
| `.claude/skills/authoring-skills/SKILL.md` | KEEP, unchanged | This tranche's own binding authority; out of scope by construction (REQUEST does not ask this tranche to revise it). |
| `.claude/skills/deepreason-orchestrator/SKILL.md` | KEEP, DELTA-edit | Dedup clusters 1 (map preflight), 2 (env preflight — currently restates the full block dr-drive-harness already owns instead of delegating, unlike its sibling router), 4 (root retirement), 5 (credentials), 8 (stop-format) into one-line pointers at `dr-drive-harness`. |
| `.claude/skills/dr-ask-the-right-question/SKILL.md` | KEEP, unchanged | Canonical source others point to (cluster 8's stop-format recommendation cites its dominance-test procedure); not itself a duplication target. |
| `.claude/skills/dr-capture-request/SKILL.md` | KEEP, unchanged | No cluster touches it; E21-evidenced. |
| `.claude/skills/dr-change-orchestrator/SKILL.md` | KEEP, DELTA-edit | Dedup clusters 1 (map preflight), 3 (commit-every-boundary), 8 (stop-format) into pointers at `dr-drive-harness`. Its env-preflight delegation (cluster 2) is ALREADY correct — kept as the model the sibling router copies. |
| `.claude/skills/dr-deliver-change/SKILL.md` | KEEP, DELTA-edit | S5 renumber: fold "3b"/"3c" into the main numbered procedure (authoring-skills S5: "renumber on insert"). Errata-checkpoint clause (cluster 10) stays localized — it is a terminal-artifact-specific requirement, not boilerplate, and its twin in `dr-verify-outcome` is genuinely a different family's terminal artifact, not a copy-paste duplicate. |
| `.claude/skills/dr-diagnose/SKILL.md` | KEEP, unchanged | No cluster touches it; E6/E16-evidenced. |
| `.claude/skills/dr-drive-harness/SKILL.md` | KEEP, becomes canonical | Absorbs (already mostly holds) the single stated version of clusters 1, 2, 3, 4, 5, 6, 7, 8: map preflight, env preflight, commit-every-boundary, root retirement, credentials, detached-launch+monitor, typed-outcomes-only, stop-format. Every other file that needs one of these points here instead of restating it. |
| `.claude/skills/dr-execute-step/SKILL.md` | KEEP, DELTA-edit | Dedup cluster 8 (stop-format) into a pointer. Cluster 9 (map-obligations): THIS file stays canonical for "the one code-changing skill in Family 2" — `dr-implement-fix` points here instead of restating (mirrors the already-good pattern at dr-implement-fix-5/dr-spec-change-20). |
| `.claude/skills/dr-explain-to-operator/SKILL.md` | KEEP, unchanged | KEEP-by-direct-mandate (CENSUS.md evidence-binding flag); the one skill whose evidence class is an operator law, not a corrected incident — stated honestly, not treated as thinner authority. |
| `.claude/skills/dr-implement-fix/SKILL.md` | KEEP, DELTA-edit | Dedup cluster 4 (root retirement), cluster 9 (map-obligations — shrink to a pointer at `dr-execute-step`'s canonical version plus the one Family-1-specific difference: "fix" not "step"). ALSO: mechanize its diff budget check — it currently reads `git diff --stat` against FIX.md's ceiling by eye where `dr-execute-step` already calls `tools/diff_budget.py` for the identical purpose; this is a genuine G3/X2 gap (no named GATE + mechanical trigger) this overhaul's own R4 charter (flag ungated negations, W3) exists to close, not a new feature — bringing FIX.md's budget check up to the tool `tools/diff_budget.py` already provides for any ceiling/path. |
| `.claude/skills/dr-plan-steps/SKILL.md` | KEEP, DELTA-edit | S5 renumber: fold "4b"/"4c" into the main list. Dedup cluster 3 (commit-every-boundary) into a pointer. |
| `.claude/skills/dr-propose-fix/SKILL.md` | KEEP, unchanged | No cluster touches it. |
| `.claude/skills/dr-reproduce/SKILL.md` | KEEP, unchanged | No cluster touches it. |
| `.claude/skills/dr-set-goal/SKILL.md` | KEEP, unchanged | Thinnest evidence binding found (no ERRATA-class corrected failure), but not a DELETE candidate under E1's letter (no failure found is not a demonstrated failure) and no duplication flagged. Flagged honestly in CENSUS.md rather than silently kept. |
| `.claude/skills/dr-spec-change/SKILL.md` | KEEP, DELTA-edit | S5 fix: fold the un-lettered "one more guardrail" clause into item 3's own numbering instead of an appended afterthought sentence. |
| `.claude/skills/dr-validate-change/SKILL.md` | KEEP, DELTA-edit | S5 renumber: fold "4a2"/"4a3"/"4b" into the main numbered procedure — the single biggest S5 offender in the set. |
| `.claude/skills/dr-verify-outcome/SKILL.md` | KEEP, unchanged | Errata-checkpoint clause stays (twin of dr-deliver-change's, by design — see that row); flagged as untested (never yet exercised by a real Family-1 delivery), a residue note for DELIVERY.md, not a defect to fix here. |

Net: 0 forced merges, 1 delete candidate (README.md, pending the
operator's word), 8 files unchanged, 10 files get scoped DELTA edits
(9 dedup only + 1 that also closes a genuine G3/X2 gate on
dr-implement-fix). This is the finding to present at the Phase-B STOP,
not a predetermined outcome — REQUEST's phrasing anticipated
deletions/merges; the evidence supports mostly deduplication instead,
and that divergence is stated here rather than forced.

## The new set

One row per surviving skill (every KEEP row above; README.md excluded
pending the operator's word on its DELETE candidacy). GATE = the
mechanical pass condition this skill's own Exit criteria already state
or, where the keep/merge/delete table calls for a DELTA, will state
after Phase C. LEDGER write = what this skill's own artifact records;
LEDGER read = what the PRECEDING artifact must already contain (G4: an
obligation is an input, not a trailing output).

### Family 1 — defect (`deepreason-orchestrator`)

| Skill | Entry | Exit | GATE / pass condition | LEDGER write | LEDGER read |
|---|---|---|---|---|---|
| `dr-set-goal` | a problem statement | `GOAL.md` | every template field filled; Success criterion is a command + expected output (machine-decidable) | GOAL.md: Class, Observed, Success criterion, In/NOT-in scope, Budget | the problem statement itself (first phase, no prior ledger) |
| `dr-diagnose` | `GOAL.md` | `DIAGNOSIS.md` | >=2 evidence pointers (>=1 non-code), a falsifiable prediction, no code modified | DIAGNOSIS.md: Primary cause, Evidence, Implicated code, Falsifiable prediction, Ruled out | GOAL.md's Observed line + Success criterion |
| `dr-reproduce` | DIAGNOSIS.md's falsifiable prediction | `REPRO.md` + one runnable artifact | pasted output demonstrably shows the defect today; production code untouched | REPRO.md: Form, Artifact, Current output, Confirms diagnosis, Post-fix expectation | DIAGNOSIS.md's Falsifiable prediction |
| `dr-propose-fix` | `DIAGNOSIS.md` + `REPRO.md` | `FIX.md` | approval gate: class `defect` + diff <=150 lines + no frozen surface -> proceed; else STOP for operator direction | FIX.md: Guarantee restored, Change sites, Regression artifact, Existing tests at risk, Explicitly not changed, Estimated diff | REPRO.md's Post-fix expectation + DIAGNOSIS.md's Primary cause |
| `dr-implement-fix` | approved `FIX.md` | one pushed commit (fix + regression test + map update) | full gate 0 failed; `docs_verify` 0 failed; **(DELTA)** `tools/diff_budget.py` run against FIX.md's Estimated-diff ceiling, mirroring dr-execute-step, replacing the current by-eye `git diff --stat` compare; Traps entry added same commit | the commit itself (diff, regression test, map Traps entry) — no separate markdown ledger | FIX.md's Change sites + Regression artifact + Estimated diff (now gate-checked mechanically) |
| `dr-verify-outcome` | GOAL.md's success criterion + the pushed fix | `VERIFY.md` | criterion command's actual output matches GOAL.md's expected output; errata line states an id or explicit "errata: none" | VERIFY.md: Criterion command+output, Historical roots re-checked, Live attempt, Verdict, Residue, Errata | GOAL.md's Success criterion (the verbatim command) |

### Family 2 — change (`dr-change-orchestrator`)

| Skill | Entry | Exit | GATE / pass condition | LEDGER write | LEDGER read |
|---|---|---|---|---|---|
| `dr-capture-request` | the operator's message(s) | `REQUEST.md` | every R/C contains a verbatim quote; zero interpretation performed | REQUEST.md: Verbatim, R1..Rn, C1..Cn, Q1..Qn, Amendments | the operator's message(s) directly (first phase) |
| `dr-spec-change` | `REQUEST.md` | `SPEC.md` | rubric line "n/n yes" present; frozen-surface/blast-radius sections are tool output pasted verbatim, never hand-summarized; budget arithmetic pasted; every R number appears in some S item | SPEC.md: Items S1..Sn, Assumptions, Questions, Frozen-surface forecast, Blast-radius census, Budget, Rubric | REQUEST.md's R1..Rn, C1..Cn |
| `dr-plan-steps` | `SPEC.md` | `CHECKLIST.md` | every S-number covered by >=1 step; every step has one done-criterion | CHECKLIST.md: State: line, numbered steps + done-when criteria, [COMMIT] tags | SPEC.md's S1..Sn items |
| `dr-execute-step` | `CHECKLIST.md` with an unchecked step | one more checked step with pasted PROOF | done-criterion command's actual output matches expected, or the contradiction is recorded and the step stays unchecked | CHECKLIST.md: checked box + PROOF text + State: line advance | CHECKLIST.md's own State: line (next step) + that step's done-criterion text |
| `dr-validate-change` | SPEC.md's acceptance checks + a fully-checked `CHECKLIST.md` | `VALIDATION.md` (PASS/FAIL) | every SPEC.md acceptance check RE-RUN (not trusted from CHECKLIST's pasted output) with real output; full gate 0 failed; frozen-surface diff pasted empty-or-explained; four `docs_verify` modes green | VALIDATION.md: per-item PASS/FAIL, gate output, requirement sweep, assumptions carried, Verdict | SPEC.md's acceptance-check text (re-run fresh) |
| `dr-deliver-change` | a PASS `VALIDATION.md` | `DELIVERY.md` | R-by-R reconciliation covers every R (no `not-done` rows — a FAIL routes back instead); Errata section states entry-id(s) or explicit "errata: none" | DELIVERY.md: Reconciliation table, Assumptions, Map delta, Errata, Parked | REQUEST.md's R1..Rn (walked again, fresh) + VALIDATION.md's Verdict |

### Cross-cutting (loaded, not phased — no sequential artifact handoff)

| Skill | Entry | Exit | GATE / pass condition | LEDGER write | LEDGER read |
|---|---|---|---|---|---|
| `dr-ask-the-right-question` | an ambiguous/terse message, or a phase's "stop and ask" trigger | a decision recorded INLINE in whichever artifact the calling phase owns (e.g. SPEC.md's Assumptions section) | every question is answered-with-a-command (record), answered-with-a-citation (framework), decided-and-recorded (dominance test), or sitting in ONE batched question set | none of its own — writes into the calling phase's ledger | the calling phase's own draft + CLAUDE.md's recorded operator values |
| `dr-drive-harness` | session start | none (a consulted manual, not a produced artifact) | self-check only ("every claim ends in a typed artifact, every plan started from INDEX.md/INV-frozen-surfaces.md") — no mechanical GATE of its own | none — this Phase B design makes it the CANONICAL SOURCE eight other files point to instead of restating (see clusters 1-8) | none (it is the read target, not a reader, for the clusters it now owns) |
| `dr-explain-to-operator` | session start, before the first operator-facing message | none (a continuous wording discipline, not a produced artifact) | **none mechanical** — flagged honestly: the one skill in the whole set with no GATE at all, consistent with its KEEP-by-mandate evidence class (CENSUS.md) rather than KEEP-by-corrected-incident | none | none |

## The router

Two router files survive unchanged in identity (per SPEC.md A2: one
PRECEDENCE list per skill set means per FAMILY, not one merged router —
the two families have disjoint routing tables and CLAUDE.md's own
"Which workflow to use" section names both as separate entry points).
Each gets the DELTA edits from the keep/merge/delete table (dedup
clusters 1/2/3/4/5/8 into pointers at `dr-drive-harness`) but keeps its
own loop and its own PRECEDENCE list — S1 permits this because a router
file OWNING the loop is the one place "then pick the next phase" is
correct, not a defect.

### `deepreason-orchestrator/SKILL.md` — Family 1 (defect) router

Routing table (unchanged, already correct — keyed on missing artifact,
per S2):

    No GOAL.md -> dr-set-goal
    GOAL.md, no DIAGNOSIS.md -> dr-diagnose
    DIAGNOSIS.md, no demonstration -> dr-reproduce
    Reproduction, no FIX.md -> dr-propose-fix
    FIX.md, code unchanged -> dr-implement-fix
    Code changed, outcome unverified -> dr-verify-outcome
    dr-verify-outcome PASS -> tranche complete
    dr-verify-outcome FAIL -> dr-diagnose (with failure evidence appended)

PRECEDENCE list (highest wins; write the winner in the text now, per S4):

1. Frozen-surface / hard prohibitions (never touch `capabilities/
   state.py` digests, `harness.py` event application, replay-validation
   formats — regardless of what any lower rule below would otherwise
   permit).
2. Cross-routing scope contract: one tranche = one GOAL.md; anything
   else noticed goes to PARKED.md, never into the current work.
3. No-phase-skipping (the routing table itself — may not implement
   without FIX.md, may not write FIX.md without DIAGNOSIS.md, etc.).
4. Stop conditions (command fails twice the same way; evidence
   contradicts the goal; diff would exceed ~150 lines).
5. `dr-ask-the-right-question`'s dominance test, before any question
   reaches the operator.

### `dr-change-orchestrator/SKILL.md` — Family 2 (change) router

Routing table (unchanged, already correct):

    No REQUEST.md -> dr-capture-request
    REQUEST.md, no SPEC.md (or new requirements appended) -> dr-spec-change
    SPEC.md approved, no CHECKLIST.md -> dr-plan-steps
    CHECKLIST.md has an unchecked step -> dr-execute-step (exactly one)
    All steps checked, no VALIDATION.md -> dr-validate-change
    VALIDATION.md PASS -> dr-deliver-change
    VALIDATION.md FAIL -> dr-plan-steps (re-plan the failing steps only)

PRECEDENCE list:

1. Frozen-surface / hard prohibitions (SPEC.md's mandatory forecast;
   ANY plausible contact halts before `dr-plan-steps` runs, regardless
   of schedule pressure).
2. The ledger rule: REQUEST.md is the single source of authority; a new
   operator message is APPENDED verbatim before acting on it, never
   absorbed silently into the current step (this tranche's own
   Amendment 1/R24 is the worked example).
3. Scope contract: implement what REQUEST.md says; broken-but-not-
   requested goes to PARKED.md, never fixed in passing.
4. The routing table itself (missing-artifact order).
5. Stop conditions (a step fails twice the same way; the estimated
   diff exceeds SPEC.md's budget — **DELTA note**: per R24, "exceeds
   SPEC.md's budget" no longer triggers a STOP on size alone unless
   SPEC.md itself states an explicit ceiling; a requirement contradicts
   the record/codebase).
6. `dr-ask-the-right-question`'s dominance test, before any question
   reaches the operator.
