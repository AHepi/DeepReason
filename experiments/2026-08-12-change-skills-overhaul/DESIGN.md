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
