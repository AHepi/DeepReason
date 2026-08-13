# Census of .claude/skills/ (Phase A, read-only)

## Inventory

| File | Purpose | Entry artifact | Exit artifact | Lines |
|---|---|---|---|---|
| `.claude/skills/README.md` | Index over both families: phase tables, cross-cutting skills, and the shared rules that hold the set together. Not itself a workflow phase. | n/a (reference document) | n/a (reference document) | 56 |
| `.claude/skills/authoring-skills/SKILL.md` | Standing authority for writing/editing/retiring any skill or workflow file (this tranche's own binding authority). | a skill/workflow file being created, reviewed, or retired | none — it is a rule set an author consults, not a phase that hands off an artifact | 146 |
| `.claude/skills/deepreason-orchestrator/SKILL.md` | Family 1 (defect) router: selects exactly one subskill by which artifact is missing, holds the family's scope contract, map preflight, environment preflight, and hard prohibitions. | a problem statement (implicit; the family's actual first artifact is GOAL.md, produced by the subskill it routes to) | none directly — routes to whichever of GOAL/DIAGNOSIS/REPRO/FIX/fix-commit/VERIFY the routing table names next | 124 |
| `.claude/skills/dr-ask-the-right-question/SKILL.md` | Cross-cutting: routes any question to the cheapest authority (record -> framework -> operator), the dominance test for deciding-without-asking, and the wrong-question table. | an ambiguous/terse operator message, a phase's "stop and ask", or evidence contradicting expectation | none — its output is a decision recorded inline in whichever artifact the calling phase owns (no artifact of its own) | 150 |
| `.claude/skills/dr-capture-request/SKILL.md` | Family 2 phase 1: copies the operator's suggestion verbatim and splits it into numbered requirements. | the operator's message(s) | `REQUEST.md` | 59 |
| `.claude/skills/dr-change-orchestrator/SKILL.md` | Family 2 (change) router: the ledger rule, scope contract, map/environment preflight, routing table keyed on missing artifact, hard prohibitions. | an operator-suggested change | none directly — routes to whichever of REQUEST/SPEC/CHECKLIST/checked-step/VALIDATION/DELIVERY the routing table names next | 127 |
| `.claude/skills/dr-deliver-change/SKILL.md` | Family 2 phase 6: final commit/push, R-by-R reconciliation, map-delta and errata reporting. | a PASS `VALIDATION.md` | `DELIVERY.md` | 90 |
| `.claude/skills/dr-diagnose/SKILL.md` | Family 1 phase 2: locates one primary cause from the typed record (map Traps first, then the record's priority-ordered sources), no code change. | `GOAL.md` | `DIAGNOSIS.md` | 95 |
| `.claude/skills/dr-drive-harness/SKILL.md` | Cross-cutting driving manual: session preflight, public CLI lifecycle, live-run ladder rules, where to look before modifying/when diagnosing, process hygiene, routing index. | session start (no code artifact) | none — an index over other authorities (CLAUDE.md, docs/map, the workflow skills), not itself artifact-producing | 198 |
| `.claude/skills/dr-execute-step/SKILL.md` | Family 2 phase 4: executes exactly one unchecked `CHECKLIST.md` step, proves its done-criterion, updates the map in the same commit if behaviour changed, commits and pushes. The only Family-2 skill allowed to modify the tree. | `CHECKLIST.md` with >=1 unchecked step | one more checked step with pasted proof (loops; final exit is "all steps checked") | 147 |
| `.claude/skills/dr-explain-to-operator/SKILL.md` | Cross-cutting communication discipline: worry-first, in-line glossing on every intermediary message, exactly one closing analogy on every final output. | session start, before the first operator-facing message | none — a wording discipline applied to every message, not an artifact | 101 |
| `.claude/skills/dr-implement-fix/SKILL.md` | Family 1 phase 5: applies an approved `FIX.md` with a regression test, runs outward test rings, updates the map in the same commit. The only Family-1 skill allowed to modify production code. | approved `FIX.md` | one pushed commit (fix + regression test + map update) | 103 |
| `.claude/skills/dr-plan-steps/SKILL.md` | Family 2 phase 3: converts `SPEC.md` into an ordered, one-done-criterion-per-step checklist; scopes from the map first; plans map-update and `[COMMIT]` checkpoints. | `SPEC.md` | `CHECKLIST.md` | 82 |
| `.claude/skills/dr-propose-fix/SKILL.md` | Family 1 phase 4: designs the smallest correct fix as `FIX.md`; DeepReason-specific design rules (record is law, frozen surfaces need a flag, budgets/priorities as guarantees, counters count one thing); no code change. | `DIAGNOSIS.md` + `REPRO.md` | `FIX.md` | 58 |
| `.claude/skills/dr-reproduce/SKILL.md` | Family 1 phase 3: demonstrates the diagnosed cause with the smallest offline artifact (record replay > unit test > in-memory check); no live runs, no code change. | `DIAGNOSIS.md`'s falsifiable prediction | `REPRO.md` + one runnable artifact | 63 |
| `.claude/skills/dr-set-goal/SKILL.md` | Family 1 phase 1: turns a vague problem statement into one bounded, falsifiable, machine-decidable goal. | a problem statement (operator, failed run, RESULTS.md, or PARKED.md) | `GOAL.md` | 56 |
| `.claude/skills/dr-spec-change/SKILL.md` | Family 2 phase 2: maps every REQUEST.md requirement to a concrete, machine-decidable spec item; mandatory blast-radius/frozen-surface gate calls; budget arithmetic; rubric pass. | `REQUEST.md` | `SPEC.md` | 196 |
| `.claude/skills/dr-validate-change/SKILL.md` | Family 2 phase 5: re-runs every SPEC.md acceptance check plus the full gate, frozen-surface diff, packaging check, map validation; verdict PASS/FAIL; never patches. | `SPEC.md`'s acceptance checks + a fully-checked `CHECKLIST.md` | `VALIDATION.md` (PASS or FAIL) | 117 |
| `.claude/skills/dr-verify-outcome/SKILL.md` | Family 1 phase 6: proves the fix against `GOAL.md`'s success criterion, optionally one guarded live run; verdict PASS/FAIL; never patches. | `GOAL.md`'s success criterion + the pushed fix | `VERIFY.md` (PASS or FAIL) | 73 |

Total: 19 files, 2041 lines (`wc -l .claude/skills/README.md .claude/skills/*/SKILL.md`).

Files with no per-invocation exit artifact (README.md, authoring-skills,
the two family routers, and the three cross-cutting advisory skills —
dr-ask-the-right-question, dr-drive-harness, dr-explain-to-operator) are
flagged here for the evidence-binding pass below: authoring-skills S1
("One SKILL = one loop iteration... Entry and exit states are named
artifacts on disk") is written for WORKER skills; whether a router or an
advisory skill is exempt from S1/S2, or is itself evidence of S1 pressure
("loop control inside a worker skill" — see Rule extraction, W-class and
S-class flags below), is carried into the Rule extraction and Evidence
binding sections rather than resolved here.

## Rule extraction

Method: every imperative/normative sentence in every file, one row per
sentence, in file order. ID = `<skillslug>-<n>`; `authoring-skills`'s own
canonical rule IDs (E1-E4, S1-S5, W1-W6, G1-G7, X1-X3, L1-L5) are used
as-is for that file rather than re-numbered. Flags apply only when a
sentence actually exhibits the defect (absence of a flag is an assertion,
not silence), drawn from authoring-skills: S3 (duplicated across files),
W3 (ungated negation), W1 (cannot fail), W5 (incident story as prose), S1
(loop control inside a worker skill), S5 (bolted-on / sub-lettered
insertion). DUP is resolved separately below as named clusters, not a
per-row cross-reference — a mechanical per-row tag would scatter the
same finding across dozens of rows instead of stating it once where a
Phase-B reader needs it.

Extraction was agent-assisted (line-by-line read of all 19 files against
this method) and spot-checked here against the actual files
(`sed -n '<n>p' <file>`) at five points across five different files —
README.md:50, dr-diagnose/SKILL.md:13, dr-execute-step/SKILL.md:44,
dr-verify-outcome/SKILL.md:33, and one negative check — all confirmed
accurate. One flag is corrected below (dr-execute-step-4: S1 removed —
"do not read ahead / do not batch steps" is anti-batching scope
discipline stated FOR a worker skill, not the S1 defect itself, which is
a worker skill embedding "then pick the next phase" routing logic;
flagging the warning against the defect as the defect would invert the
rule's own intent).

### README.md (`readme`)

| ID | file:line | sentence | flags |
|---|---|---|---|
| readme-1 | .claude/skills/README.md:3 | "Repo law (CLAUDE.md): route ALL substantive work through one of the two workflow families." | none |
| readme-2 | .claude/skills/README.md:4 | "One tranche, one goal" | W1 |
| readme-3 | .claude/skills/README.md:44 | "Cross-routing is strict: a defect found mid-change is PARKED, not fixed; a change wished for mid-defect is PARKED, not implemented." | S3 (dup cluster: cross-routing) |
| readme-4 | .claude/skills/README.md:46 | "Both families begin with a MAP PREFLIGHT (`docs/map/INDEX.md` -> `INV-frozen-surfaces.md` -> the seam document, `docs/map/SEAM-<a>-x-<b>.md`, before either subsystem; recipe: `docs/map/REC-change-a-seam.md`)." | S3 (dup cluster: map preflight) |
| readme-5 | .claude/skills/README.md:50 | "The map moves in the SAME commit as the code it describes." | S3 (dup cluster: map preflight) |
| readme-6 | .claude/skills/README.md:51 | "Commit and push the tranche directory at every phase boundary — the container can vanish at any time." | S3 (dup cluster: commit-every-boundary) |

### authoring-skills/SKILL.md (`authoring-skills`)

Non-canonical imperative sentences:

| ID | file:line | sentence | flags |
|---|---|---|---|
| authoring-skills-1 | .claude/skills/authoring-skills/SKILL.md:8 | "Any line here that violates a rule below is a defect: file an erratum against this file, by ID." | none |
| authoring-skills-2 | .claude/skills/authoring-skills/SKILL.md:11 | "Edit by DELTA against an ID." | none (=L1, restated) |
| authoring-skills-3 | .claude/skills/authoring-skills/SKILL.md:12 | "Never regenerate this file wholesale." | W3 |
| authoring-skills-4 | .claude/skills/authoring-skills/SKILL.md:16 | "Use these exact words everywhere; a synonym is a defect." | none |

Canonical rule-list rows (own IDs; flags "none" unless the document
violates its own rule):

| ID | file:line | sentence | flags |
|---|---|---|---|
| E1 | .claude/skills/authoring-skills/SKILL.md:31 | "Before writing a SKILL, run the task three times without it and record the failures. No failures -> do not write it." | none |
| E2 | .claude/skills/authoring-skills/SKILL.md:35 | "A SKILL ships with the eval set from E1. It exists only while it beats the no-skill baseline on that set." | none |
| E3 | .claude/skills/authoring-skills/SKILL.md:37 | "Re-run the baseline on every model change. Delta <= 0 -> delete the SKILL." | none |
| E4 | .claude/skills/authoring-skills/SKILL.md:39 | "Budget rule: to add a line, name the line it displaces." | none |
| S1 | .claude/skills/authoring-skills/SKILL.md:45 | "One SKILL = one loop iteration. The loop lives in the router. 'Then pick the next phase' appearing in a worker file is a defect." | none |
| S2 | .claude/skills/authoring-skills/SKILL.md:48 | "Entry and exit states are named artifacts on disk, not descriptions. Route on which artifact is missing." | none |
| S3 | .claude/skills/authoring-skills/SKILL.md:50 | "A rule lives in exactly one file: the one in context when the rule fires." | none |
| S4 | .claude/skills/authoring-skills/SKILL.md:53 | "When two rules could collide, write the winner in the text now. There is one PRECEDENCE list per skill set, in the router." | none |
| S5 | .claude/skills/authoring-skills/SKILL.md:55 | "Renumber on insert. `3b` is evidence a rule was bolted on where it kept failing; move it to where it is read (see G4)." | none |
| W1 | .claude/skills/authoring-skills/SKILL.md:60 | "Each line names an operation: a command, a file read/write, a comparison. Test: can it fail?" | none |
| W2 | .claude/skills/authoring-skills/SKILL.md:63 | "Bind instructions to available actions with concrete verbs." | none |
| W3 | .claude/skills/authoring-skills/SKILL.md:65 | "State the positive action. Each surviving 'never' must be enforced by a GATE (see X1)." | none |
| W4 | .claude/skills/authoring-skills/SKILL.md:69 | "No narrative, persona, urgency, or emotional framing." | W3 (self: no named GATE for this rule in-file — flagged, not corrected, per this document's own erratum-by-ID clause) |
| W5 | .claude/skills/authoring-skills/SKILL.md:73 | "No incident stories. Mechanize the lesson as a GATE, mutation-prove the GATE, delete the story." | none |
| W6 | .claude/skills/authoring-skills/SKILL.md:76 | "One worked example beats a paragraph of description. At most one per section." | none |
| G1 | .claude/skills/authoring-skills/SKILL.md:81 | "Every completion claim carries PROOF." | none |
| G2 | .claude/skills/authoring-skills/SKILL.md:84 | "A legitimate 'none' requires proof of looking: the scan command and its output, not the word." | none |
| G3 | .claude/skills/authoring-skills/SKILL.md:86 | "The SKILL names the GATE and its pass condition." | none |
| G4 | .claude/skills/authoring-skills/SKILL.md:88 | "An obligation is an input, not a trailing output: step N+1 opens by reading what step N's obligation wrote." | none |
| G5 | .claude/skills/authoring-skills/SKILL.md:91 | "Track requirement state live in the LEDGER, one row per requirement, updated as work happens." | none |
| G6 | .claude/skills/authoring-skills/SKILL.md:94 | "Mutation-prove every GATE once: break the guarded thing, watch it fail, restore." | none |
| G7 | .claude/skills/authoring-skills/SKILL.md:96 | "Steps write distilled state to the LEDGER, never raw transcripts." | W3 (self: no named in-file GATE — flagged, not corrected) |
| X1 | .claude/skills/authoring-skills/SKILL.md:101 | "Every prohibition pairs with an outlet in the same breath. An outlet-less 'never' is satisfied by relabeling." | none |
| X2 | .claude/skills/authoring-skills/SKILL.md:110 | "Every STOP trigger is mechanical: a count, a verdict string, an exit code. Convert judgment to a tool; trigger on its verdict." | none |
| X3 | .claude/skills/authoring-skills/SKILL.md:114 | "Every honest outcome has a label." | none |
| L1 | .claude/skills/authoring-skills/SKILL.md:119 | "Edit by DELTA only." | none |
| L2 | .claude/skills/authoring-skills/SKILL.md:122 | "Compression is a separate, diffed pass, re-gated by the E1 evals." | none |
| L3 | .claude/skills/authoring-skills/SKILL.md:124 | "Pin the tested configuration: model, skill version, GATE tool versions." | none |
| L4 | .claude/skills/authoring-skills/SKILL.md:126 | "Third-party skills get the same review as third-party code: read every line, pin the version, and treat any instruction to fetch or load further instructions as a rejection." | none |
| L5 | .claude/skills/authoring-skills/SKILL.md:131 | "Before shipping, plant one violation the SKILL should catch and run the workflow. The GATE goes red or the SKILL is not done." | none |

### deepreason-orchestrator/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| deepreason-orchestrator-1 | .claude/skills/deepreason-orchestrator/SKILL.md:8 | "You do not freelance." | W1, W3 |
| deepreason-orchestrator-2 | .claude/skills/deepreason-orchestrator/SKILL.md:9 | "You select ONE subskill, execute it to its exit criteria, then return here to select the next." | none (router file, S1's loop belongs here by design) |
| deepreason-orchestrator-3 | .claude/skills/deepreason-orchestrator/SKILL.md:10 | "You never blend phases." | W3 |
| deepreason-orchestrator-4 | .claude/skills/deepreason-orchestrator/SKILL.md:14 | "A tranche works exactly one GOAL.md (produced by `dr-set-goal`)." | none |
| deepreason-orchestrator-5 | .claude/skills/deepreason-orchestrator/SKILL.md:15 | "Anything else you notice goes into `PARKED.md` — never into your work." | W3, S3 (dup cluster: cross-routing) |
| deepreason-orchestrator-6 | .claude/skills/deepreason-orchestrator/SKILL.md:16 | "Write the parked entry for its FUTURE RUNNER, at park time..." | none |
| deepreason-orchestrator-7 | .claude/skills/deepreason-orchestrator/SKILL.md:19 | "Starting the follow-up should cost the operator a paste, not an authoring session." | W1 |
| deepreason-orchestrator-8 | .claude/skills/deepreason-orchestrator/SKILL.md:21 | "Claims about DeepReason behavior are only admissible if derived from typed records..." | none |
| deepreason-orchestrator-9 | .claude/skills/deepreason-orchestrator/SKILL.md:24 | "Your own summary of what code 'probably does' is not evidence." | none |
| deepreason-orchestrator-10 | .claude/skills/deepreason-orchestrator/SKILL.md:26 | "You may not implement without an approved FIX.md." | none |
| deepreason-orchestrator-11 | .claude/skills/deepreason-orchestrator/SKILL.md:27 | "You may not write FIX.md without a DIAGNOSIS.md." | none |
| deepreason-orchestrator-12 | .claude/skills/deepreason-orchestrator/SKILL.md:27 | "You may not write DIAGNOSIS.md without a reproduction or record-derived trace." | none |
| deepreason-orchestrator-13 | .claude/skills/deepreason-orchestrator/SKILL.md:29 | "Stop and report (do not improvise) when: a command fails twice the same way; evidence contradicts the goal; the fix requires touching frozen-record semantics...; or the diff would exceed ~150 changed lines." | none |
| deepreason-orchestrator-14 | .claude/skills/deepreason-orchestrator/SKILL.md:34 | "Before any stop becomes a question to the operator, load `dr-ask-the-right-question`..." | none |
| deepreason-orchestrator-15 | .claude/skills/deepreason-orchestrator/SKILL.md:44 | "Read `docs/map/INDEX.md` and resolve the work to ids..." | S3 (dup cluster: map preflight) |
| deepreason-orchestrator-16 | .claude/skills/deepreason-orchestrator/SKILL.md:46 | "If the work spans two things, **read the SEAM document first**." | S3 (dup cluster: map preflight) |
| deepreason-orchestrator-17 | .claude/skills/deepreason-orchestrator/SKILL.md:52 | "Read `docs/map/INV-frozen-surfaces.md` BEFORE designing anything." | S3 (dup cluster: map preflight) |
| deepreason-orchestrator-18 | .claude/skills/deepreason-orchestrator/SKILL.md:55 | "Record the resolved ids in the tranche's first artifact (GOAL.md or REQUEST.md)." | S3 (dup cluster: map preflight) |
| deepreason-orchestrator-19 | .claude/skills/deepreason-orchestrator/SKILL.md:58 | "If the map has no id for something the work touches, that is a finding, not a blocker..." | S3 (dup cluster: map preflight) |
| deepreason-orchestrator-20 | .claude/skills/deepreason-orchestrator/SKILL.md:64 | "Nothing else may advance a `Verified-at:` stamp." | W3, S3 (dup cluster: map preflight) |
| deepreason-orchestrator-21 | .claude/skills/deepreason-orchestrator/SKILL.md:68 | "load it [dr-drive-harness] if this session has not run the harness before" | S3 (dup cluster: env preflight — this row delegates correctly; the block below at rows 23-24 does NOT) |
| deepreason-orchestrator-22 | .claude/skills/deepreason-orchestrator/SKILL.md:70 | "Also load `dr-explain-to-operator` once per session, BEFORE your first message the operator will see." | none |
| deepreason-orchestrator-23 | .claude/skills/deepreason-orchestrator/SKILL.md:75 | "Verify, in order: [git log; git status; pip install; ls experiments/*/env]" | S3 (dup cluster: env preflight — duplicates dr-drive-harness §1's own block instead of pointing at it) |
| deepreason-orchestrator-24 | .claude/skills/deepreason-orchestrator/SKILL.md:82 | "If anything was stale: resync the working branch..." | S3 (dup cluster: env preflight) |
| deepreason-orchestrator-25 | .claude/skills/deepreason-orchestrator/SKILL.md:100 | "If `dr-verify-outcome` reports FAIL, route back to `dr-diagnose` with the failure evidence appended — do not patch forward from intuition." | none |
| deepreason-orchestrator-26 | .claude/skills/deepreason-orchestrator/SKILL.md:107 | "Commit and push this directory at every phase boundary (the container can vanish at any time)." | S3 (dup cluster: commit-every-boundary) |
| deepreason-orchestrator-27 | .claude/skills/deepreason-orchestrator/SKILL.md:115 | "Never modify a committed run root's contents." | S3 (dup cluster: root-retirement) |
| deepreason-orchestrator-28 | .claude/skills/deepreason-orchestrator/SKILL.md:116 | "Run roots are retired, never edited: `git mv run-<id> <state>-epochN-run-<id>` and commit the rename BEFORE any relaunch..." | S3 (dup cluster: root-retirement) |
| deepreason-orchestrator-29 | .claude/skills/deepreason-orchestrator/SKILL.md:119 | "Never commit credential material." | S3 (dup cluster: credentials) |
| deepreason-orchestrator-30 | .claude/skills/deepreason-orchestrator/SKILL.md:120 | "`env` files are gitignored; check with `git check-ignore` before writing near them." | S3 (dup cluster: credentials) |
| deepreason-orchestrator-31 | .claude/skills/deepreason-orchestrator/SKILL.md:121 | "Never run the full live ladder to test a code hypothesis — that is `dr-verify-outcome`'s final step only..." | W3 |
| deepreason-orchestrator-32 | .claude/skills/deepreason-orchestrator/SKILL.md:124 | "Never widen the goal because the codebase 'needs' it." | W3 |

### dr-ask-the-right-question/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-ask-the-right-question-1 | .claude/skills/dr-ask-the-right-question/SKILL.md:17 | "Ascend only when the cheaper one genuinely cannot answer." | none |
| dr-ask-the-right-question-2 | .claude/skills/dr-ask-the-right-question/SKILL.md:28 | "Cite the instrument with the number." | none |
| dr-ask-the-right-question-3 | .claude/skills/dr-ask-the-right-question/SKILL.md:33 | "Model prose is never evidence." | none |
| dr-ask-the-right-question-4 | .claude/skills/dr-ask-the-right-question/SKILL.md:34 | "If your answer to a record-question does not end in a command output or a file path, you have not asked the record yet." | none |
| dr-ask-the-right-question-5 | .claude/skills/dr-ask-the-right-question/SKILL.md:51 | "The operator's words are AUTHORITY, so treat them the way the harness treats a record — quote them verbatim into the ledger, then interpret them in writing." | none |
| dr-ask-the-right-question-6 | .claude/skills/dr-ask-the-right-question/SKILL.md:54 | "If you find yourself paraphrasing the operator from memory, you have already lost the thread." | W1 |
| dr-ask-the-right-question-7 | .claude/skills/dr-ask-the-right-question/SKILL.md:59 | "Before any theory about a failure or a surprise, in order: 1. Which instrument produced this? Name it." | none |
| dr-ask-the-right-question-8 | .claude/skills/dr-ask-the-right-question/SKILL.md:63 | "What does the typed artifact say verbatim?" | none |
| dr-ask-the-right-question-9 | .claude/skills/dr-ask-the-right-question/SKILL.md:69 | "Do two instruments agree?" | none |
| dr-ask-the-right-question-10 | .claude/skills/dr-ask-the-right-question/SKILL.md:74 | "Has this gone wrong here before?" | none |
| dr-ask-the-right-question-11 | .claude/skills/dr-ask-the-right-question/SKILL.md:77 | "What would falsify my current reading? If nothing could, it is not a reading, it is a mood." | none |
| dr-ask-the-right-question-12 | .claude/skills/dr-ask-the-right-question/SKILL.md:83 | "Before composing ANY question to the operator, derive their answer from what they have already said..." | none |
| dr-ask-the-right-question-13 | .claude/skills/dr-ask-the-right-question/SKILL.md:92 | "The dominance test: would every reasonable operator holding those values choose the same option? Then the fork is false — decide, act, and record one line." | none |
| dr-ask-the-right-question-14 | .claude/skills/dr-ask-the-right-question/SKILL.md:100 | "Batch every such fork into ONE question set per tranche; lead with your recommendation and its one-sentence reason..." | none |
| dr-ask-the-right-question-15 | .claude/skills/dr-ask-the-right-question/SKILL.md:105 | "When the earning reason is frozen-surface contact, the question MUST embed `tools/blast_radius.py`'s `BLAST_RADIUS_RESULT_V1` result." | none |
| dr-ask-the-right-question-16 | .claude/skills/dr-ask-the-right-question/SKILL.md:110 | "the operator cannot be the blast-radius calculator for a 125,000-line codebase" | W5 |
| dr-ask-the-right-question-17 | .claude/skills/dr-ask-the-right-question/SKILL.md:118 | "When you are genuinely uncertain between two readings, do not pick one and build — and do not ask yet either." | none |
| dr-ask-the-right-question-18 | .claude/skills/dr-ask-the-right-question/SKILL.md:118 | "Write BOTH readings as alternatives the record can decide between, each with the evidence that would prove it." | none |
| dr-ask-the-right-question-19 | .claude/skills/dr-ask-the-right-question/SKILL.md:123 | "Then collect the deciding evidence." | none |
| dr-ask-the-right-question-20 | .claude/skills/dr-ask-the-right-question/SKILL.md:144 | "Before you send any question upward or act on any assumption: every question you almost asked is either answered-with-a-command, answered-with-a-citation, decided-and-recorded, or sitting in ONE batched question set." | none |

### dr-capture-request/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-capture-request-1 | .claude/skills/dr-capture-request/SKILL.md:8 | "You quote; you do not paraphrase, improve, or fill gaps." | none |
| dr-capture-request-2 | .claude/skills/dr-capture-request/SKILL.md:15 | "Copy the operator's suggestion VERBATIM into a quoted block." | none |
| dr-capture-request-3 | .claude/skills/dr-capture-request/SKILL.md:16 | "If the suggestion spans several messages, quote each with its position." | none |
| dr-capture-request-4 | .claude/skills/dr-capture-request/SKILL.md:17 | "Do not trim 'context' — trimmed context is how inputs get forgotten." | W3 |
| dr-capture-request-5 | .claude/skills/dr-capture-request/SKILL.md:19 | "Split into atomic requirements R1..Rn." | none |
| dr-capture-request-6 | .claude/skills/dr-capture-request/SKILL.md:20 | "Split conjunctions ('do X and then Y' -> R1: X, R2: Y)." | none |
| dr-capture-request-7 | .claude/skills/dr-capture-request/SKILL.md:21 | "Keep the operator's own words in each requirement; add nothing." | none |
| dr-capture-request-8 | .claude/skills/dr-capture-request/SKILL.md:23 | "Capture constraints stated anywhere in the conversation that bind this change..." | none |
| dr-capture-request-9 | .claude/skills/dr-capture-request/SKILL.md:27 | "Mark each requirement's kind: `behavior`, `artifact`, `process`." | none |
| dr-capture-request-10 | .claude/skills/dr-capture-request/SKILL.md:30 | "List open questions Q1..Qn — places where the words genuinely underdetermine the work." | none |
| dr-capture-request-11 | .claude/skills/dr-capture-request/SKILL.md:31 | "Do NOT answer them here." | none |
| dr-capture-request-12 | .claude/skills/dr-capture-request/SKILL.md:57 | "REQUEST.md committed and pushed." | none |
| dr-capture-request-13 | .claude/skills/dr-capture-request/SKILL.md:58 | "Zero interpretation performed: every R and C contains a quote." | none |
| dr-capture-request-14 | .claude/skills/dr-capture-request/SKILL.md:59 | "Return to the orchestrator." | none |

### dr-change-orchestrator/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-change-orchestrator-1 | .claude/skills/dr-change-orchestrator/SKILL.md:8 | "Your job is to implement exactly that change — not the change you would have designed, not the neighboring improvement, not a partial version you forgot to finish." | none |
| dr-change-orchestrator-2 | .claude/skills/dr-change-orchestrator/SKILL.md:21 | "Before starting ANY phase, re-read REQUEST.md and CHECKLIST.md in full." | none |
| dr-change-orchestrator-3 | .claude/skills/dr-change-orchestrator/SKILL.md:23 | "If the operator sends a new message mid-workflow: APPEND it to REQUEST.md verbatim..., then route to `dr-spec-change` to reconcile." | none |
| dr-change-orchestrator-4 | .claude/skills/dr-change-orchestrator/SKILL.md:26 | "Never absorb new instructions silently into the current step." | W3 |
| dr-change-orchestrator-5 | .claude/skills/dr-change-orchestrator/SKILL.md:28 | "A requirement is never deleted, only marked `superseded-by:<n>` or `deferred (operator approved <where>)`." | none |
| dr-change-orchestrator-6 | .claude/skills/dr-change-orchestrator/SKILL.md:33 | "Implement what REQUEST.md says." | none |
| dr-change-orchestrator-7 | .claude/skills/dr-change-orchestrator/SKILL.md:33 | "Where it is silent, choose the smallest reasonable interpretation and RECORD the assumption in SPEC.md; where two readings differ materially, stop and ask — one batched question, not a dribble." | none |
| dr-change-orchestrator-8 | .claude/skills/dr-change-orchestrator/SKILL.md:37 | "Before asking, load `dr-ask-the-right-question`: derive the answer from the record and the operator's recorded values first..." | none |
| dr-change-orchestrator-9 | .claude/skills/dr-change-orchestrator/SKILL.md:40 | "Anything you notice that is broken but not requested: into `PARKED.md`." | S3 (dup cluster: cross-routing) |
| dr-change-orchestrator-10 | .claude/skills/dr-change-orchestrator/SKILL.md:42 | "Never fix it now." | W3, S3 (dup cluster: cross-routing) |
| dr-change-orchestrator-11 | .claude/skills/dr-change-orchestrator/SKILL.md:43 | "Write the entry for its future runner, at park time..." | none |
| dr-change-orchestrator-12 | .claude/skills/dr-change-orchestrator/SKILL.md:47 | "Stop conditions: a step fails twice the same way; the spec turns out to require touching frozen-record semantics...; the estimated diff exceeds SPEC.md's budget; or a requirement contradicts the record/codebase." | none |
| dr-change-orchestrator-13 | .claude/skills/dr-change-orchestrator/SKILL.md:53 | "Every stop presented to the operator leads with the decision needed in ONE sentence, the options priced, and a recommendation with its reason." | S3 (dup cluster: stop-format, echoed near-verbatim in dr-drive-harness and dr-execute-step) |
| dr-change-orchestrator-14 | .claude/skills/dr-change-orchestrator/SKILL.md:62 | "Read `docs/map/INDEX.md` and resolve the work to ids..." | S3 (dup cluster: map preflight) |
| dr-change-orchestrator-15 | .claude/skills/dr-change-orchestrator/SKILL.md:64 | "If the work spans two things, **read the SEAM document first**." | S3 (dup cluster: map preflight) |
| dr-change-orchestrator-16 | .claude/skills/dr-change-orchestrator/SKILL.md:70 | "Read `docs/map/INV-frozen-surfaces.md` BEFORE designing anything." | S3 (dup cluster: map preflight) |
| dr-change-orchestrator-17 | .claude/skills/dr-change-orchestrator/SKILL.md:73 | "Record the resolved ids in the tranche's first artifact (GOAL.md or REQUEST.md)." | S3 (dup cluster: map preflight) |
| dr-change-orchestrator-18 | .claude/skills/dr-change-orchestrator/SKILL.md:76 | "If the map has no id for something the work touches, that is a finding, not a blocker..." | S3 (dup cluster: map preflight) |
| dr-change-orchestrator-19 | .claude/skills/dr-change-orchestrator/SKILL.md:81 | "Nothing else may advance a `Verified-at:` stamp." | W3, S3 (dup cluster: map preflight) |
| dr-change-orchestrator-20 | .claude/skills/dr-change-orchestrator/SKILL.md:86 | "Do this once before routing." | none |
| dr-change-orchestrator-21 | .claude/skills/dr-change-orchestrator/SKILL.md:110 | "After EVERY phase (and every executed step): commit and push the tranche directory." | S3 (dup cluster: commit-every-boundary) |
| dr-change-orchestrator-22 | .claude/skills/dr-change-orchestrator/SKILL.md:121 | "No code changes outside `dr-execute-step`, and no step outside CHECKLIST.md." | W3 |
| dr-change-orchestrator-23 | .claude/skills/dr-change-orchestrator/SKILL.md:123 | "Never edit committed run roots; never commit `env`/credential files." | W3, S3 (dup cluster: root-retirement, credentials) |
| dr-change-orchestrator-24 | .claude/skills/dr-change-orchestrator/SKILL.md:125 | "Never mark a checklist step done without pasting its done-criterion output." | none |
| dr-change-orchestrator-25 | .claude/skills/dr-change-orchestrator/SKILL.md:126 | "Never report the change complete without the R-by-R reconciliation table from `dr-deliver-change`." | none |

### dr-deliver-change/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-deliver-change-1 | .claude/skills/dr-deliver-change/SKILL.md:10 | "Delivery is reconciliation, not celebration: its job is to make any gap between what was asked and what was done impossible to miss." | none |
| dr-deliver-change-2 | .claude/skills/dr-deliver-change/SKILL.md:15 | "Final tree check: `git status --porcelain` must be empty..." | none |
| dr-deliver-change-3 | .claude/skills/dr-deliver-change/SKILL.md:18 | "Build the reconciliation table from REQUEST.md's verbatim requirements — walk EVERY R number, including amendments and superseded ones." | none |
| dr-deliver-change-4 | .claude/skills/dr-deliver-change/SKILL.md:24 | "`not-done` — forbidden here; that is a FAIL, go back" | none |
| dr-deliver-change-5 | .claude/skills/dr-deliver-change/SKILL.md:25 | "Surface the assumptions (from VALIDATION.md) and PARKED.md contents as explicit lists." | none |
| dr-deliver-change-6 | .claude/skills/dr-deliver-change/SKILL.md:26 | "Parked items are offered as candidate next tranches, never silently promised — each with its ready-to-send prompt, and the close RECOMMENDS one next item." | none |
| dr-deliver-change-7 | .claude/skills/dr-deliver-change/SKILL.md:31 | "**Report the map delta.** ..." | S5 (source sub-numbers this "3b") |
| dr-deliver-change-8 | .claude/skills/dr-deliver-change/SKILL.md:36 | "'No map change' is a legitimate answer...say it rather than omitting the section." | S5 |
| dr-deliver-change-9 | .claude/skills/dr-deliver-change/SKILL.md:38 | "**Errata check — mandatory, before DELIVERY.md is committed.** ... If yes, the `docs/ERRATA.md` entry lands in the SAME commit as DELIVERY.md." | S5 (source sub-numbers this "3c"), S3 (dup cluster: errata-checkpoint, echoed in dr-verify-outcome) |
| dr-deliver-change-10 | .claude/skills/dr-deliver-change/SKILL.md:43 | "If no, state 'errata: none' explicitly...state it, do not omit the section." | S5, S3 (dup cluster: errata-checkpoint) |
| dr-deliver-change-11 | .claude/skills/dr-deliver-change/SKILL.md:46 | "Write DELIVERY.md leading with the outcome in plain sentences a reader who saw none of the work can follow." | none |
| dr-deliver-change-12 | .claude/skills/dr-deliver-change/SKILL.md:48 | "No process narration ('first I read the file...')." | W3 |
| dr-deliver-change-13 | .claude/skills/dr-deliver-change/SKILL.md:49 | "If the request touched experiments/live evidence: append the dated segment to the relevant RESULTS.md..." | none |
| dr-deliver-change-14 | .claude/skills/dr-deliver-change/SKILL.md:52 | "Commit and push it." | none |
| dr-deliver-change-15 | .claude/skills/dr-deliver-change/SKILL.md:84 | "Everything pushed; tree clean; DELIVERY.md committed." | none |
| dr-deliver-change-16 | .claude/skills/dr-deliver-change/SKILL.md:85 | "DELIVERY.md's Errata section states either the added entry id(s) or 'errata: none' — never omitted, never silent." | none |
| dr-deliver-change-17 | .claude/skills/dr-deliver-change/SKILL.md:87 | "The report (its content, not a pointer to it) is presented to the operator as the final message of the tranche." | none |

### dr-diagnose/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-diagnose-1 | .claude/skills/dr-diagnose/SKILL.md:8 | "You read the record first and the code second." | none |
| dr-diagnose-2 | .claude/skills/dr-diagnose/SKILL.md:9 | "You change nothing." | none |
| dr-diagnose-3 | .claude/skills/dr-diagnose/SKILL.md:13 | "Before opening the record, read the `Traps` section of the map document covering the suspect subsystem." | none |
| dr-diagnose-4 | .claude/skills/dr-diagnose/SKILL.md:19 | "This is not a substitute for the record: the record still decides, and a trap that merely LOOKS like your symptom is a hypothesis to test against the blob, not an answer." | none |
| dr-diagnose-5 | .claude/skills/dr-diagnose/SKILL.md:66 | "Only after the record narrows the cause to a mechanism do you open the implicated source file, and only that file plus at most two neighbors." | none |
| dr-diagnose-6 | .claude/skills/dr-diagnose/SKILL.md:70 | "Attribute, don't infer: 'cycle 0 selected conn:X (seq 32)' beats any reading of `_select_problem`." | none |
| dr-diagnose-7 | .claude/skills/dr-diagnose/SKILL.md:72 | "When a prior attempt failed differently, diff the two records, not the two vibes." | none |
| dr-diagnose-8 | .claude/skills/dr-diagnose/SKILL.md:74 | "If you find a SECOND independent cause, put it in PARKED.md and continue with the primary." | none |
| dr-diagnose-9 | .claude/skills/dr-diagnose/SKILL.md:76 | "If the record contradicts GOAL.md's Observed line, stop and return to the orchestrator saying so." | none |
| dr-diagnose-10 | .claude/skills/dr-diagnose/SKILL.md:93 | "DIAGNOSIS.md committed and pushed; PARKED.md updated if applicable." | none |
| dr-diagnose-11 | .claude/skills/dr-diagnose/SKILL.md:94 | "No code modified. No fix sketched beyond the mechanism name." | W3 |

### dr-drive-harness/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-drive-harness-1 | .claude/skills/dr-drive-harness/SKILL.md:27 | "Always `python -m pytest`, never bare `pytest` (PATH shim)." | none |
| dr-drive-harness-2 | .claude/skills/dr-drive-harness/SKILL.md:28 | "Credentials are recreated from the operator's handover, never committed." | S3 (dup cluster: credentials) |
| dr-drive-harness-3 | .claude/skills/dr-drive-harness/SKILL.md:29 | "Commit and push at every phase boundary — work between pushes is work at risk." | S3 (dup cluster: commit-every-boundary) |
| dr-drive-harness-4 | .claude/skills/dr-drive-harness/SKILL.md:30 | "Then read, in order: CLAUDE.md, the newest `experiments/*/RESULTS.md` segments, `docs/ERRATA.md`." | none |
| dr-drive-harness-5 | .claude/skills/dr-drive-harness/SKILL.md:33 | "Re-entering mid-tranche needs no conversation history: every tranche is resumable from its committed artifacts alone." | none |
| dr-drive-harness-6 | .claude/skills/dr-drive-harness/SKILL.md:35 | "Read the tranche dir's CHECKLIST.md `State:` line, then REQUEST.md/SPEC.md, and continue." | none |
| dr-drive-harness-7 | .claude/skills/dr-drive-harness/SKILL.md:38 | "If a session cannot resume from the artifacts, the previous session under-committed; record that gap, reconstruct, and commit." | none |
| dr-drive-harness-8 | .claude/skills/dr-drive-harness/SKILL.md:57 | "qualify opt-ins must match reason opt-ins (`--attached-evidence` <=> `--attach`)" | none |
| dr-drive-harness-9 | .claude/skills/dr-drive-harness/SKILL.md:58 | "provider reasoning must be EXPLICITLY disabled for ollama when required (unset is not off — the refusal is typed)" | none |
| dr-drive-harness-10 | .claude/skills/dr-drive-harness/SKILL.md:69 | "Retire by rename (`git mv run-<id> <state>-epochN-run-<id>`) and COMMIT THE RENAME FIRST." | S3 (dup cluster: root-retirement) |
| dr-drive-harness-11 | .claude/skills/dr-drive-harness/SKILL.md:70 | "Never edit a committed root — to change the question or add evidence, `deepreason amend` then `continue`." | S3 (dup cluster: root-retirement) |
| dr-drive-harness-12 | .claude/skills/dr-drive-harness/SKILL.md:72 | "Launch detached, never foreground: from the ladder's directory, `setsid nohup ./<ladder>.sh & disown`." | S3 (dup cluster: detached-launch, echoed in dr-verify-outcome) |
| dr-drive-harness-13 | .claude/skills/dr-drive-harness/SKILL.md:73 | "Arm the snapshot loop and a monitor on the newest root's `progress.jsonl` plus the driver log's `rc=` lines — alert on failure signatures, not just success." | S3 (dup cluster: detached-launch) |
| dr-drive-harness-14 | .claude/skills/dr-drive-harness/SKILL.md:77 | "Judge only typed outcomes: run state, stop_reason, the audit JSON, `verify_root`, FINDINGS.md." | S3 (dup cluster: typed-outcomes-only, echoed in dr-verify-outcome) |
| dr-drive-harness-15 | .claude/skills/dr-drive-harness/SKILL.md:84 | "Never scope a change by grepping 125k lines." | W3 |
| dr-drive-harness-16 | .claude/skills/dr-drive-harness/SKILL.md:87 | "`docs/map/INDEX.md` — resolve the work to ids." | S3 (dup cluster: map preflight) |
| dr-drive-harness-17 | .claude/skills/dr-drive-harness/SKILL.md:89 | "`docs/map/INV-frozen-surfaces.md` — **first, always**: five surfaces are not yours to change." | S3 (dup cluster: map preflight) |
| dr-drive-harness-18 | .claude/skills/dr-drive-harness/SKILL.md:90 | "Readers may be fixed; formats may not." | none |
| dr-drive-harness-19 | .claude/skills/dr-drive-harness/SKILL.md:93 | "If the change spans two things, the seam document BEFORE either subsystem." | S3 (dup cluster: map preflight) |
| dr-drive-harness-20 | .claude/skills/dr-drive-harness/SKILL.md:98 | "`docs/map/SCHEMA.md` before writing or editing any map document." | none |
| dr-drive-harness-21 | .claude/skills/dr-drive-harness/SKILL.md:99 | "The map moves in the SAME commit as the code, or it becomes a document that lies." | S3 (dup cluster: map preflight) |
| dr-drive-harness-22 | .claude/skills/dr-drive-harness/SKILL.md:109 | "any change to that surface updates the pins and re-runs the smoke in the SAME commit — or the instrument rots silently" | W5 (incident: "found 2026-08-05: red for a week after an entry-point addition, unnoticed") |
| dr-drive-harness-23 | .claude/skills/dr-drive-harness/SKILL.md:115 | "Iterate with `--fast`; run the FULL mode at least once before any commit that touches `src/`" | W5 (incident: "proven at commit `55b16ce9`...") |
| dr-drive-harness-24 | .claude/skills/dr-drive-harness/SKILL.md:122 | "Record first, code second, theory last." | W1 |
| dr-drive-harness-25 | .claude/skills/dr-drive-harness/SKILL.md:133 | "always cite the instrument with the number" | S3 (dup cluster: cite-the-instrument, echoed in dr-ask-the-right-question) |
| dr-drive-harness-26 | .claude/skills/dr-drive-harness/SKILL.md:135 | "When the cause is located, do not fix it inline: route it." | none |
| dr-drive-harness-27 | .claude/skills/dr-drive-harness/SKILL.md:139 | "**Kill by PID, never by pattern.**" | W5 (incident: "the 2026-08-05 smoke tranche killed its own session twice this way") |
| dr-drive-harness-28 | .claude/skills/dr-drive-harness/SKILL.md:142 | "**Never run the full gate concurrently with `docs_verify`**..." | W5 (incident: "three corrupted gate measurements across two tranches") |
| dr-drive-harness-29 | .claude/skills/dr-drive-harness/SKILL.md:146 | "One instrument at a time, on an otherwise idle box." | none |
| dr-drive-harness-30 | .claude/skills/dr-drive-harness/SKILL.md:147 | "**A surprising measurement taken under load is not a measurement.**" | none |
| dr-drive-harness-31 | .claude/skills/dr-drive-harness/SKILL.md:148 | "Re-run idle before recording it, and say which run you recorded." | none |
| dr-drive-harness-32 | .claude/skills/dr-drive-harness/SKILL.md:149 | "**Long work launches detached**...a foreground process dies with the session." | S3 (dup cluster: detached-launch) |
| dr-drive-harness-33 | .claude/skills/dr-drive-harness/SKILL.md:151 | "Scratch and temp files go to the session scratchpad, never the repo." | W3 |
| dr-drive-harness-34 | .claude/skills/dr-drive-harness/SKILL.md:173 | "Cross-routing is strict: a defect found mid-change is PARKED, not fixed; a change wished for mid-defect is PARKED, not implemented." | S3 (dup cluster: cross-routing) |
| dr-drive-harness-35 | .claude/skills/dr-drive-harness/SKILL.md:179 | "execute them literally rather than improvising a summary of them" | none |
| dr-drive-harness-36 | .claude/skills/dr-drive-harness/SKILL.md:179 | "Never generalize an instruction beyond its stated scope; if a spec seems silent about your case, that is a question, not an invitation to infer." | none |
| dr-drive-harness-37 | .claude/skills/dr-drive-harness/SKILL.md:182 | "A multi-step program...runs one step per tranche — finishing a step early is never a reason to start the next in the same tranche." | none |
| dr-drive-harness-38 | .claude/skills/dr-drive-harness/SKILL.md:184 | "Stop conditions and DESIGN-AND-STOP gates are hard stops: the deliverable at a gate is a committed document and an ended turn, not an implementation." | none |
| dr-drive-harness-39 | .claude/skills/dr-drive-harness/SKILL.md:186 | "every stop presented to the operator leads with the decision needed in ONE sentence, the options priced, and a recommendation with its reason" | S3 (dup cluster: stop-format) |
| dr-drive-harness-40 | .claude/skills/dr-drive-harness/SKILL.md:189 | "Style, per the operator's recorded preference: answer their actual worry first; say what a scary finding does NOT mean before what it does; own the workflow's own contribution to any confusion; and close hard explanations with one short, accurate everyday analogy." | S3 (dup cluster: explain-to-operator, restates dr-explain-to-operator's own rules 2nd-hand) |

### dr-execute-step/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-execute-step-1 | .claude/skills/dr-execute-step/SKILL.md:9 | "You do this for ONE step, then return." | none |
| dr-execute-step-2 | .claude/skills/dr-execute-step/SKILL.md:15 | "Re-read REQUEST.md (including Amendments) and CHECKLIST.md in full." | none |
| dr-execute-step-3 | .claude/skills/dr-execute-step/SKILL.md:15 | "Find the FIRST unchecked step. That is your entire job." | none |
| dr-execute-step-4 | .claude/skills/dr-execute-step/SKILL.md:16 | "Do not read ahead 'to be efficient'; do not batch steps." | none (corrected from agent's S1 — see Method note above) |
| dr-execute-step-5 | .claude/skills/dr-execute-step/SKILL.md:18 | "Confirm the step still makes sense against the tree (a prior step may have failed silently)." | none |
| dr-execute-step-6 | .claude/skills/dr-execute-step/SKILL.md:20 | "If the tree contradicts the step...do not improvise: record the contradiction under the step, commit, and return to the orchestrator." | none |
| dr-execute-step-7 | .claude/skills/dr-execute-step/SKILL.md:23 | "Only files this step's spec item names may change." | none |
| dr-execute-step-8 | .claude/skills/dr-execute-step/SKILL.md:24 | "Mid-step discoveries...go to PARKED.md or, if the change cannot land without them, back through dr-spec-change as an amendment — never just typed in." | none |
| dr-execute-step-9 | .claude/skills/dr-execute-step/SKILL.md:27 | "Run the done-criterion command." | none |
| dr-execute-step-10 | .claude/skills/dr-execute-step/SKILL.md:27 | "Paste its real output (trimmed to the relevant lines) under the step." | none |
| dr-execute-step-11 | .claude/skills/dr-execute-step/SKILL.md:28 | "If it does not match expected: the step is NOT done — leave it unchecked, record the output and one line on the mismatch, and return to the orchestrator." | none |
| dr-execute-step-12 | .claude/skills/dr-execute-step/SKILL.md:30 | "Two failures of the same step = stop condition; the stop report leads with the decision needed in ONE sentence, the candidate routes priced, and a recommendation with its reason." | S3 (dup cluster: stop-format) |
| dr-execute-step-13 | .claude/skills/dr-execute-step/SKILL.md:35 | "**If this step changed behaviour, update the map in the SAME commit**." | S3 (dup cluster: map-same-commit, echoed in dr-implement-fix) |
| dr-execute-step-14 | .claude/skills/dr-execute-step/SKILL.md:37 | "If it changed the packaging surface..., update `scripts/wheel_smoke.py`'s pinned expectations and re-run the smoke in the same commit too — no gate runs it for you." | S3 (dup cluster: wheel-smoke-pins, echoed in dr-implement-fix, dr-validate-change) |
| dr-execute-step-15 | .claude/skills/dr-execute-step/SKILL.md:41 | "Mark the box, update CHECKLIST.md — including its header State: line — which is what a fresh session resumes from." | none |
| dr-execute-step-16 | .claude/skills/dr-execute-step/SKILL.md:44 | "if the step is tagged [COMMIT] (or changed any file): `git add` this step's files, then run `python tools/diff_budget.py`..." | none |
| dr-execute-step-17 | .claude/skills/dr-execute-step/SKILL.md:47 | "WITHIN/NO_CEILING: continue." | none |
| dr-execute-step-18 | .claude/skills/dr-execute-step/SKILL.md:48 | "EXCEEDED is a STOP in the standard format...not a footnote" | W5 (incident: "193 insertions landed against a <=150 ceiling with no stop, V1 tranche 2026-08-05"), S3 (dup cluster: budget-exceeded-stop, echoed in dr-implement-fix) |
| dr-execute-step-19 | .claude/skills/dr-execute-step/SKILL.md:50 | "Alongside it, run `python tools/blast_radius.py`...and diff its output against SPEC.md's own sections." | none |
| dr-execute-step-20 | .claude/skills/dr-execute-step/SKILL.md:57 | "Any `frozen_surface_contacts` entry not already named in SPEC.md...is DRIFT — a STOP in the exact same format as `diff_budget.py`'s own EXCEEDED, never a footnote." | W5 (incident: "the 2026-08-09 incident's own fix, mechanized") |
| dr-execute-step-21 | .claude/skills/dr-execute-step/SKILL.md:64 | "No drift: continue. Then commit and push now." | none |
| dr-execute-step-22 | .claude/skills/dr-execute-step/SKILL.md:74 | "A step that changes what a caller may do...updates the covering `SUB-`/`CON-`/`SEAM-` document **in the same commit**." | S3 (dup cluster: map-same-commit) |
| dr-execute-step-23 | .claude/skills/dr-execute-step/SKILL.md:77 | "A step that changes an interaction updates the `SEAM-` document before the subsystem ones." | none |
| dr-execute-step-24 | .claude/skills/dr-execute-step/SKILL.md:84 | "New behaviour needs a new check at column 0 that would fail if the behaviour regressed." | S3 (dup cluster: new-check-required, echoed in dr-implement-fix, dr-validate-change) |
| dr-execute-step-25 | .claude/skills/dr-execute-step/SKILL.md:85 | "Run it before you write it down." | none |
| dr-execute-step-26 | .claude/skills/dr-execute-step/SKILL.md:86 | "Advance `Verified-at:` only if you re-ran that document's checks." | S3 (dup cluster: verified-at-honesty, echoed in dr-implement-fix) |
| dr-execute-step-27 | .claude/skills/dr-execute-step/SKILL.md:87 | "`python tools/docs_verify.py` must pass before you commit; a failure is a failed step, exactly like a failed test." | none |
| dr-execute-step-28 | .claude/skills/dr-execute-step/SKILL.md:89 | "A step that only writes tests or records evidence changes no map document." | none |
| dr-execute-step-29 | .claude/skills/dr-execute-step/SKILL.md:90 | "Do not touch stamps you did not verify." | W3 |
| dr-execute-step-30 | .claude/skills/dr-execute-step/SKILL.md:98 | "**Pin to committed, immutable evidence.** A test or check may open only roots and fixtures that `git ls-files` knows..." | W5 (incident: "docs/ERRATA.md E7: four checks pinned to never-committed roots...") |
| dr-execute-step-31 | .claude/skills/dr-execute-step/SKILL.md:104 | "**Anchor to meaning, not form.** Prefer behavior, structure, or counts over literal source text." | none |
| dr-execute-step-32 | .claude/skills/dr-execute-step/SKILL.md:112 | "Never pin line numbers." | W3 |
| dr-execute-step-33 | .claude/skills/dr-execute-step/SKILL.md:113 | "**Mutation-prove it can fail, before writing it down.** Break the guarded thing, watch the test/check/probe go red, restore." | none |
| dr-execute-step-34 | .claude/skills/dr-execute-step/SKILL.md:115 | "For equality tests, keep a permanent companion mutation test in the suite." | none |
| dr-execute-step-35 | .claude/skills/dr-execute-step/SKILL.md:119 | "**Compare typed outcomes, and exclude wall-clock RECURSIVELY.**..." | W5 (incident: "a top-level-only scrub left `llm.ms` inside `attempt_trace` and a 1-in-3 flake") |
| dr-execute-step-36 | .claude/skills/dr-execute-step/SKILL.md:123 | "Diagnose flakes to the exact field; never widen an exclusion on a guess." | W3 |
| dr-execute-step-37 | .claude/skills/dr-execute-step/SKILL.md:125 | "**Tolerate absence in old records.** Any test or sweep probe reading the typed record must accept every existing committed root...assert the attribute exists before reading it." | none |
| dr-execute-step-38 | .claude/skills/dr-execute-step/SKILL.md:133 | "Match the surrounding code's idiom, naming, and comment density." | W1 |
| dr-execute-step-39 | .claude/skills/dr-execute-step/SKILL.md:134 | "Comments state constraints the code cannot show, never narrate the change." | none |
| dr-execute-step-40 | .claude/skills/dr-execute-step/SKILL.md:136 | "Test docstrings name the motivating requirement or record." | none |
| dr-execute-step-41 | .claude/skills/dr-execute-step/SKILL.md:138 | "Never weaken an existing assertion to make a step pass; that is a failed step, not a passed one." | none |

### dr-explain-to-operator/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-explain-to-operator-1 | .claude/skills/dr-explain-to-operator/SKILL.md:34 | "**1. Every message: worry first.** The first sentence answers what the operator is actually anxious to know...before any mechanism." | none |
| dr-explain-to-operator-2 | .claude/skills/dr-explain-to-operator/SKILL.md:37 | "When a finding sounds like bad news, state what it does NOT mean for their intent before what it does mean." | none |
| dr-explain-to-operator-3 | .claude/skills/dr-explain-to-operator/SKILL.md:38 | "Corrections to your own earlier claims are stated plainly, once, without hedging." | none |
| dr-explain-to-operator-4 | .claude/skills/dr-explain-to-operator/SKILL.md:41 | "**2. Every INTERMEDIARY message: gloss technical terms conservatively.**..." | none |
| dr-explain-to-operator-5 | .claude/skills/dr-explain-to-operator/SKILL.md:43 | "Conservative means: when unsure whether the operator holds the term, gloss it." | none |
| dr-explain-to-operator-6 | .claude/skills/dr-explain-to-operator/SKILL.md:46 | "Keep the precise term AND add the meaning; never replace precision with vagueness." | W3 |
| dr-explain-to-operator-7 | .claude/skills/dr-explain-to-operator/SKILL.md:47 | "The gloss says what the thing IS and what it DOES for the operator's intent" | none |
| dr-explain-to-operator-8 | .claude/skills/dr-explain-to-operator/SKILL.md:61 | "Never cite a requirement number, artifact name, commit hash, or error code without saying in the same breath what it says or what it means for the work." | W3 |
| dr-explain-to-operator-9 | .claude/skills/dr-explain-to-operator/SKILL.md:67 | "**3. Every FINAL output: full style plus exactly ONE analogy.**..." | none |
| dr-explain-to-operator-10 | .claude/skills/dr-explain-to-operator/SKILL.md:75 | "The analogy is required, singular, and must actually fit: a wrong analogy is worse than none, so test it against the mechanism before writing it." | none |
| dr-explain-to-operator-11 | .claude/skills/dr-explain-to-operator/SKILL.md:78 | "Intermediary messages need no analogy; the final one always does." | none |

### dr-implement-fix/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-implement-fix-1 | .claude/skills/dr-implement-fix/SKILL.md:14 | "**Touch only FIX.md's change sites.**" | none |
| dr-implement-fix-2 | .claude/skills/dr-implement-fix/SKILL.md:15 | "If implementation reveals a needed site FIX.md missed, STOP: amend FIX.md first (one commit), then continue." | none |
| dr-implement-fix-3 | .claude/skills/dr-implement-fix/SKILL.md:18 | "**Write the regression test first**, converting the REPRO artifact: it fails before your change, passes after." | none |
| dr-implement-fix-4 | .claude/skills/dr-implement-fix/SKILL.md:20 | "Its docstring names the live run/record that motivated it..." | none |
| dr-implement-fix-5 | .claude/skills/dr-implement-fix/SKILL.md:22 | "Build it to `dr-execute-step`'s 'Durable tests, checks, and probes' rules..." | none (delegates to canonical location — good practice, not duplication) |
| dr-implement-fix-6 | .claude/skills/dr-implement-fix/SKILL.md:26 | "Apply the code change." | none |
| dr-implement-fix-7 | .claude/skills/dr-implement-fix/SKILL.md:26 | "Comments state the constraint the code cannot show...never the change's history or your reasoning." | S3 (dup cluster: comment-discipline, echoed verbatim-in-spirit in dr-execute-step-39) |
| dr-implement-fix-8 | .claude/skills/dr-implement-fix/SKILL.md:29 | "**Run outward rings, stop at first failure**" | none |
| dr-implement-fix-9 | .claude/skills/dr-implement-fix/SKILL.md:35 | "The full gate must report **0 failed**." | none |
| dr-implement-fix-10 | .claude/skills/dr-implement-fix/SKILL.md:36 | "A pre-existing failure you did not cause: stop, report, do not 'fix it while you're there.'" | none |
| dr-implement-fix-11 | .claude/skills/dr-implement-fix/SKILL.md:38 | "If FIX.md's change sites touch the packaging surface..., one more ring the gate does not run: `python scripts/wheel_smoke.py`..." | S3 (dup cluster: wheel-smoke-pins) |
| dr-implement-fix-12 | .claude/skills/dr-implement-fix/SKILL.md:41 | "A gate failure caused by your change is information: if a fixture depended on the defective behavior, update it minimally; if the failure is NOT predicted by FIX.md, your fix is wrong — revert." | none |
| dr-implement-fix-13 | .claude/skills/dr-implement-fix/SKILL.md:46 | "Never weaken an assertion to green." | W3, S3 (dup cluster: never-weaken-assertion, echoed in dr-execute-step-41) |
| dr-implement-fix-14 | .claude/skills/dr-implement-fix/SKILL.md:47 | "If a live run root is needed...retire the old root...commit the rename FIRST as its own commit, then proceed." | S3 (dup cluster: root-retirement) |
| dr-implement-fix-15 | .claude/skills/dr-implement-fix/SKILL.md:51 | "**Update the map in THIS commit**" | S3 (dup cluster: map-same-commit) |
| dr-implement-fix-16 | .claude/skills/dr-implement-fix/SKILL.md:52 | "Before committing: compare the ACTUAL changed lines (`git diff --stat`) against FIX.md's budget ceiling." | none |
| dr-implement-fix-17 | .claude/skills/dr-implement-fix/SKILL.md:53 | "Exceeding it is a STOP in the standard format...not a footnote" | W5 (incident: "recorded miss: 193 insertions against <=150, V1 tranche 2026-08-05"), S3 (dup cluster: budget-exceeded-stop) |
| dr-implement-fix-18 | .claude/skills/dr-implement-fix/SKILL.md:57 | "Then commit once, push with retry:" | none |
| dr-implement-fix-19 | .claude/skills/dr-implement-fix/SKILL.md:70 | "**Same commit, not a follow-up.** A separate 'update docs' commit is a commit that gets dropped." | S3 (dup cluster: map-same-commit) |
| dr-implement-fix-20 | .claude/skills/dr-implement-fix/SKILL.md:72 | "**Every fix earns a `Traps` entry**..." | none |
| dr-implement-fix-21 | .claude/skills/dr-implement-fix/SKILL.md:75 | "Never delete an old Traps entry — rewrite it to say it was fixed and when." | none |
| dr-implement-fix-22 | .claude/skills/dr-implement-fix/SKILL.md:77 | "**Advance `Verified-at:` only if you re-ran that document's checks.**" | S3 (dup cluster: verified-at-honesty) |
| dr-implement-fix-23 | .claude/skills/dr-implement-fix/SKILL.md:79 | "**A new invariant needs a new check**, at column 0, that would fail if the invariant broke." | S3 (dup cluster: new-check-required) |
| dr-implement-fix-24 | .claude/skills/dr-implement-fix/SKILL.md:81 | "If you cannot write one, the claim is too vague to record." | none |
| dr-implement-fix-25 | .claude/skills/dr-implement-fix/SKILL.md:82 | "Run before committing: `python tools/docs_verify.py` ... `python tools/docs_verify.py --audit`" | none |
| dr-implement-fix-26 | .claude/skills/dr-implement-fix/SKILL.md:88 | "`--stale` is advisory: read what it lists, update what your change actually invalidated." | none |
| dr-implement-fix-27 | .claude/skills/dr-implement-fix/SKILL.md:92 | "No drive-by refactors, renames, TODO cleanups, or formatting churn." | W3 |
| dr-implement-fix-28 | .claude/skills/dr-implement-fix/SKILL.md:93 | "No new dependencies, no config default changes, unless FIX.md lists them as change sites." | none |
| dr-implement-fix-29 | .claude/skills/dr-implement-fix/SKILL.md:95 | "Never edit committed run roots; never commit `env` files." | W3, S3 (dup cluster: root-retirement, credentials) |

### dr-plan-steps/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-plan-steps-1 | .claude/skills/dr-plan-steps/SKILL.md:10 | "Execution will do NOTHING that is not a step here, so missing steps here means missed work later." | none |
| dr-plan-steps-2 | .claude/skills/dr-plan-steps/SKILL.md:11 | "Plan against that." | W1 |
| dr-plan-steps-3 | .claude/skills/dr-plan-steps/SKILL.md:15 | "Dependencies first, verification interleaved..." | none |
| dr-plan-steps-4 | .claude/skills/dr-plan-steps/SKILL.md:19 | "One step = one action with ONE done-criterion..." | none |
| dr-plan-steps-5 | .claude/skills/dr-plan-steps/SKILL.md:21 | "If a step needs the word 'and', split it." | none |
| dr-plan-steps-6 | .claude/skills/dr-plan-steps/SKILL.md:22 | "Include the boring steps that get forgotten..." | none |
| dr-plan-steps-7 | .claude/skills/dr-plan-steps/SKILL.md:29 | "Every step cites its spec item (S-number)." | none |
| dr-plan-steps-8 | .claude/skills/dr-plan-steps/SKILL.md:30 | "A step with no S-number is scope creep — delete it or send it to PARKED.md." | none |
| dr-plan-steps-9 | .claude/skills/dr-plan-steps/SKILL.md:31 | "**Scope from the map before planning steps.** ..." | S5 (source sub-numbers this "4b"), S3 (dup cluster: map preflight) |
| dr-plan-steps-10 | .claude/skills/dr-plan-steps/SKILL.md:36 | "Name those ids in CHECKLIST.md's header so execution starts from the same map the plan was built on." | S5 |
| dr-plan-steps-11 | .claude/skills/dr-plan-steps/SKILL.md:38 | "A change whose ids you cannot name is a change you have not scoped." | S5 |
| dr-plan-steps-12 | .claude/skills/dr-plan-steps/SKILL.md:39 | "**Plan the map update as part of the step that changes behaviour**, never as a trailing 'update docs' step." | S5 (source sub-numbers this "4c"), S3 (dup cluster: map-same-commit) |
| dr-plan-steps-13 | .claude/skills/dr-plan-steps/SKILL.md:41 | "A trailing documentation step is the one that gets dropped when a tranche runs long." | S5, W5 |
| dr-plan-steps-14 | .claude/skills/dr-plan-steps/SKILL.md:42 | "If a seam document must be CREATED, that is its own step, and it comes BEFORE the code steps." | S5 |
| dr-plan-steps-15 | .claude/skills/dr-plan-steps/SKILL.md:45 | "Mark checkpoint steps `[COMMIT]` at natural boundaries..." | none |
| dr-plan-steps-16 | .claude/skills/dr-plan-steps/SKILL.md:47 | "The container can vanish; work between commits is work at risk." | S3 (dup cluster: commit-every-boundary) |
| dr-plan-steps-17 | .claude/skills/dr-plan-steps/SKILL.md:73 | "Touch only the steps implicated by the failure...never rewrite history of checked steps — their pasted outputs are the audit trail." | none |
| dr-plan-steps-18 | .claude/skills/dr-plan-steps/SKILL.md:79 | "CHECKLIST.md committed and pushed; every S-number covered by >=1 step; every step has a done-criterion." | none |
| dr-plan-steps-19 | .claude/skills/dr-plan-steps/SKILL.md:81 | "No code changed in this phase." | W3 |

### dr-propose-fix/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-propose-fix-1 | .claude/skills/dr-propose-fix/SKILL.md:9 | "You may read code freely now, but you still change nothing." | none |
| dr-propose-fix-2 | .claude/skills/dr-propose-fix/SKILL.md:13 | "**Smallest semantic change that makes the reproduction invert.**..." | none |
| dr-propose-fix-3 | .claude/skills/dr-propose-fix/SKILL.md:16 | "**The record is law.** Never change what is WRITTEN to the append-only record to fix what is READ from it." | none |
| dr-propose-fix-4 | .claude/skills/dr-propose-fix/SKILL.md:18 | "Fix readers (validators, gates, accessors) so old committed roots stay valid." | none |
| dr-propose-fix-5 | .claude/skills/dr-propose-fix/SKILL.md:19 | "A fix that invalidates existing replay-valid roots is wrong by definition." | none |
| dr-propose-fix-6 | .claude/skills/dr-propose-fix/SKILL.md:21 | "**Frozen surfaces need a flag, not a patch.**...FIX.md must say so and stop for operator approval." | none |
| dr-propose-fix-7 | .claude/skills/dr-propose-fix/SKILL.md:25 | "**Budgets and priorities are guarantees.**..." | none |
| dr-propose-fix-8 | .claude/skills/dr-propose-fix/SKILL.md:30 | "**Counters count one thing.**..." | none |
| dr-propose-fix-9 | .claude/skills/dr-propose-fix/SKILL.md:51 | "Class `defect` (per GOAL.md) with diff estimate <=150 lines and no frozen surface: proceed to `dr-implement-fix`." | none |
| dr-propose-fix-10 | .claude/skills/dr-propose-fix/SKILL.md:53 | "Anything else: stop, present FIX.md, await operator direction." | none |
| dr-propose-fix-11 | .claude/skills/dr-propose-fix/SKILL.md:57 | "FIX.md committed and pushed. No production code changed." | none |

### dr-reproduce/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-reproduce-1 | .claude/skills/dr-reproduce/SKILL.md:10 | "You still change no production code." | none |
| dr-reproduce-2 | .claude/skills/dr-reproduce/SKILL.md:19 | "Reuse existing test helpers...do not invent new scaffolding when a helper exists." | none |
| dr-reproduce-3 | .claude/skills/dr-reproduce/SKILL.md:25 | "Acceptable as evidence, but pair it with form 1 or 2 for the regression artifact." | none |
| dr-reproduce-4 | .claude/skills/dr-reproduce/SKILL.md:28 | "NEVER reproduce by launching a live provider run." | none |
| dr-reproduce-5 | .claude/skills/dr-reproduce/SKILL.md:29 | "Live runs are for `dr-verify-outcome`, at most once, and only if the goal demands it." | none |
| dr-reproduce-6 | .claude/skills/dr-reproduce/SKILL.md:33 | "The reproduction must mirror the live conditions the record shows, not a convenient simplification." | none |
| dr-reproduce-7 | .claude/skills/dr-reproduce/SKILL.md:35 | "If admission auto-accepted import-role artifacts before cycle 0, your fixture registers those artifacts too." | none |
| dr-reproduce-8 | .claude/skills/dr-reproduce/SKILL.md:36 | "A reproduction that passes for a different reason than the live failure will approve a wrong fix." | none |
| dr-reproduce-9 | .claude/skills/dr-reproduce/SKILL.md:38 | "One assertion states the DEFECT...phrased so it inverts cleanly post-fix." | none |
| dr-reproduce-10 | .claude/skills/dr-reproduce/SKILL.md:40 | "Respect frozen-record invariants in fixtures...fixture WellFormednessError means your fixture is wrong, not the harness." | none |
| dr-reproduce-11 | .claude/skills/dr-reproduce/SKILL.md:54 | "If the reproduction REFUTES the diagnosis: write that in REPRO.md, commit, and return to the orchestrator routing back to `dr-diagnose`." | none |
| dr-reproduce-12 | .claude/skills/dr-reproduce/SKILL.md:56 | "A refuted diagnosis is a successful phase, not a failure." | none |
| dr-reproduce-13 | .claude/skills/dr-reproduce/SKILL.md:61 | "The artifact demonstrably shows the defect today (output pasted)." | none |
| dr-reproduce-14 | .claude/skills/dr-reproduce/SKILL.md:62 | "Production code untouched." | none |

### dr-set-goal/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-set-goal-1 | .claude/skills/dr-set-goal/SKILL.md:10 | "You do not read source code in this phase beyond confirming a file exists." | none |
| dr-set-goal-2 | .claude/skills/dr-set-goal/SKILL.md:14 | "Restate the problem as ONE observable, checkable statement about the record or the tests." | none |
| dr-set-goal-3 | .claude/skills/dr-set-goal/SKILL.md:18 | "Classify it: `defect`...`regression-risk`...`capability-gap`..." | none |
| dr-set-goal-4 | .claude/skills/dr-set-goal/SKILL.md:24 | "Only `defect` tranches may proceed to implementation without explicit operator approval; the other two stop after FIX.md and report." | none |
| dr-set-goal-5 | .claude/skills/dr-set-goal/SKILL.md:27 | "Write the success criterion as a command + expected output." | none |
| dr-set-goal-6 | .claude/skills/dr-set-goal/SKILL.md:27 | "It must be decidable by a machine" | none |
| dr-set-goal-7 | .claude/skills/dr-set-goal/SKILL.md:33 | "Write the boundary list: files/subsystems presumed in scope (max 3), and an explicit NOT-IN-SCOPE line." | none |
| dr-set-goal-8 | .claude/skills/dr-set-goal/SKILL.md:35 | "Size check: if you cannot imagine the fix under ~150 changed lines and one commit, split the problem and pick the FIRST piece only." | none |
| dr-set-goal-9 | .claude/skills/dr-set-goal/SKILL.md:39 | "GOAL.md template (fill every field; delete nothing)" | none |
| dr-set-goal-10 | .claude/skills/dr-set-goal/SKILL.md:54 | "GOAL.md exists in the tranche directory, committed and pushed." | none |
| dr-set-goal-11 | .claude/skills/dr-set-goal/SKILL.md:55 | "You have NOT proposed a cause, a fix, or read implementation code." | W3 |

### dr-spec-change/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-spec-change-1 | .claude/skills/dr-spec-change/SKILL.md:8 | "Input: REQUEST.md (re-read it in FULL first, including amendments)." | none |
| dr-spec-change-2 | .claude/skills/dr-spec-change/SKILL.md:15 | "For EVERY R in REQUEST.md (no skips — walk the numbers in order), write a spec item..." | none |
| dr-spec-change-3 | .claude/skills/dr-spec-change/SKILL.md:20 | "If the readings differ only in minor detail: pick the smallest reasonable one and record it under Assumptions..." | none |
| dr-spec-change-4 | .claude/skills/dr-spec-change/SKILL.md:24 | "If the readings differ materially...STOP after committing SPEC.md — present the batched questions." | none |
| dr-spec-change-5 | .claude/skills/dr-spec-change/SKILL.md:26 | "Never start implementation with a material ambiguity open." | W3 |
| dr-spec-change-6 | .claude/skills/dr-spec-change/SKILL.md:28 | "First load `dr-ask-the-right-question` and run each candidate question through it..." | none |
| dr-spec-change-7 | .claude/skills/dr-spec-change/SKILL.md:33 | "A mechanism the request NAMES...is a suggestion, not a requirement." | none |
| dr-spec-change-8 | .claude/skills/dr-spec-change/SKILL.md:34 | "Verify it actually reaches the code this change touches (trace the call path) before adopting it." | none |
| dr-spec-change-9 | .claude/skills/dr-spec-change/SKILL.md:35 | "If it cannot, that is a material contradiction: deliver the PROPERTY the requirement wants and record the contradiction in writing, or fork to the operator." | none |
| dr-spec-change-10 | .claude/skills/dr-spec-change/SKILL.md:38 | "Never adopt a named mechanism unverified, and never deviate from it silently." | none |
| dr-spec-change-11 | .claude/skills/dr-spec-change/SKILL.md:43 | "Frozen-surface contact forecast — mandatory, in writing." | none |
| dr-spec-change-12 | .claude/skills/dr-spec-change/SKILL.md:44 | "Run `python tools/blast_radius.py`...and record its result in SPEC.md's 'Frozen-surface contact forecast' section." | none |
| dr-spec-change-13 | .claude/skills/dr-spec-change/SKILL.md:49 | "'none expected' counts, but only after actually running the gate — a hand-checked 'none' is no longer sufficient once the gate exists to check it." | none |
| dr-spec-change-14 | .claude/skills/dr-spec-change/SKILL.md:51 | "ANY plausible contact...stops the tranche HERE: commit SPEC.md and obtain the operator's words before `dr-plan-steps` runs." | none |
| dr-spec-change-15 | .claude/skills/dr-spec-change/SKILL.md:55 | "The STOP message...MUST embed `tools/blast_radius.py`'s computed `frozen_surface_contacts` list verbatim, never a hand-written summary of it." | none |
| dr-spec-change-16 | .claude/skills/dr-spec-change/SKILL.md:58 | "A STOP that describes contact without pasting the tool's own list is not this checkpoint" | none |
| dr-spec-change-17 | .claude/skills/dr-spec-change/SKILL.md:70 | "For changes that add data to the typed record, one more guardrail: the absence-tolerant READER lands before the writer emits..." | S5 (afterthought clause "one more guardrail" appended mid-item-3) |
| dr-spec-change-18 | .claude/skills/dr-spec-change/SKILL.md:74 | "And a new typed-record OBSERVABLE...needs a sweep probe proposed for it in the spec..." | S5 |
| dr-spec-change-19 | .claude/skills/dr-spec-change/SKILL.md:77 | "The probe change is its own SEPARATE commit — extending `tools/root_sweep.py` resets the byte-identity baseline..." | S5 |
| dr-spec-change-20 | .claude/skills/dr-spec-change/SKILL.md:82 | "Build every proposed test, check, and probe to `dr-execute-step`'s 'Durable tests, checks, and probes' rules..." | none (delegates to canonical location) |
| dr-spec-change-21 | .claude/skills/dr-spec-change/SKILL.md:86 | "Blast-radius census — mandatory, pasted, BEFORE any fixture-drift prediction." | none |
| dr-spec-change-22 | .claude/skills/dr-spec-change/SKILL.md:90 | "paste its `consumers.tests`/`consumers.map_checks` fields into SPEC.md's 'Blast-radius census' section and classify EVERY hit." | none |
| dr-spec-change-23 | .claude/skills/dr-spec-change/SKILL.md:93 | "The manual grep...is RETAINED as a required cross-check specifically for anything the gate's own `reachability` field reports `UNKNOWN`." | none |
| dr-spec-change-24 | .claude/skills/dr-spec-change/SKILL.md:109 | "5. DESIGN-AND-STOP shape. When the deliverable IS the spec...two more sections are mandatory." | none |
| dr-spec-change-25 | .claude/skills/dr-spec-change/SKILL.md:114 | "**Measurements**: every load-bearing design claim is a pasted command output." | none |
| dr-spec-change-26 | .claude/skills/dr-spec-change/SKILL.md:115 | "A claim with no measurement is an assumption and is moved to Assumptions." | none |
| dr-spec-change-27 | .claude/skills/dr-spec-change/SKILL.md:117 | "**Options**: every considered option priced...and every rejection cites a measurement, not a preference." | none |
| dr-spec-change-28 | .claude/skills/dr-spec-change/SKILL.md:120 | "Set the budget: total estimated changed lines and commits." | none |
| dr-spec-change-29 | .claude/skills/dr-spec-change/SKILL.md:121 | "If over ~300 lines, propose a split into ordered sub-tranches..." | none |
| dr-spec-change-30 | .claude/skills/dr-spec-change/SKILL.md:123 | "The Budget section's headline number(s) MUST equal the computed sum of the itemized per-item estimates above — paste the arithmetic, never restated by hand." | none |
| dr-spec-change-31 | .claude/skills/dr-spec-change/SKILL.md:131 | "Anti-invention pass: re-read SPEC.md and delete anything that does not trace to an R or C number." | none |
| dr-spec-change-32 | .claude/skills/dr-spec-change/SKILL.md:132 | "If it felt necessary, it is either an assumption (record it) or scope creep (PARKED.md)." | none |
| dr-spec-change-33 | .claude/skills/dr-spec-change/SKILL.md:134 | "Rubric pass — the last act before committing." | none |
| dr-spec-change-34 | .claude/skills/dr-spec-change/SKILL.md:135 | "Re-read the finished SPEC.md as a REVIEWER, not the author; any 'no' routes back to that step before commit." | none |
| dr-spec-change-35 | .claude/skills/dr-spec-change/SKILL.md:145 | "Record the outcome as one line in SPEC.md ('Rubric: n/n yes')." | none |
| dr-spec-change-36 | .claude/skills/dr-spec-change/SKILL.md:190 | "SPEC.md committed and pushed; every R number appears in some item..." | none |
| dr-spec-change-37 | .claude/skills/dr-spec-change/SKILL.md:193 | "The rubric pass ran and its line is in SPEC.md..." | none |
| dr-spec-change-38 | .claude/skills/dr-spec-change/SKILL.md:195 | "If 'Questions for operator' is non-empty: stopped and asked." | none |

### dr-validate-change/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-validate-change-1 | .claude/skills/dr-validate-change/SKILL.md:10 | "You do not fix anything — a failure routes back to re-planning with evidence, which is cheaper than a hidden patch that invalidates the checklist's audit trail." | none |
| dr-validate-change-2 | .claude/skills/dr-validate-change/SKILL.md:16 | "Re-read REQUEST.md, SPEC.md, CHECKLIST.md in full." | none |
| dr-validate-change-3 | .claude/skills/dr-validate-change/SKILL.md:19 | "Run EVERY acceptance check in SPEC.md, in item order, even ones a checklist step already ran." | none |
| dr-validate-change-4 | .claude/skills/dr-validate-change/SKILL.md:21 | "Paste each real output." | none |
| dr-validate-change-5 | .claude/skills/dr-validate-change/SKILL.md:22 | "Run the regression ring: the full gate (`pytest tests/ -q -n 4`) must end **0 failed**." | none |
| dr-validate-change-6 | .claude/skills/dr-validate-change/SKILL.md:24 | "A failure you caused is a FAIL verdict; a pre-existing failure you can prove pre-dates the change...is recorded as such and does not block, but goes to PARKED.md." | none |
| dr-validate-change-7 | .claude/skills/dr-validate-change/SKILL.md:27 | "Behavior-preservation spot-check: if the change touched a reader or validator...prior verdicts must be unchanged except where SPEC.md says otherwise." | none |
| dr-validate-change-8 | .claude/skills/dr-validate-change/SKILL.md:31 | "**Frozen-surface diff — paste it, empty or explained:**" | S5 (source sub-numbers this "4a2") |
| dr-validate-change-9 | .claude/skills/dr-validate-change/SKILL.md:38 | "Empty output is the expected result and is pasted as proof." | S5 |
| dr-validate-change-10 | .claude/skills/dr-validate-change/SKILL.md:39 | "Non-empty output is a FAIL unless REQUEST.md quotes the operator approving that exact surface..." | S5 |
| dr-validate-change-11 | .claude/skills/dr-validate-change/SKILL.md:43 | "**Packaging-surface check.**..." | S5 (source sub-numbers this "4a3"), S3 (dup cluster: wheel-smoke-pins) |
| dr-validate-change-12 | .claude/skills/dr-validate-change/SKILL.md:48 | "The smokes pin expected sets and hashes; a surface change whose commit did not update those pins is a FAIL." | S5 |
| dr-validate-change-13 | .claude/skills/dr-validate-change/SKILL.md:49 | "If the surface did not move, write 'packaging surface untouched — smoke not owed': the skip must be a recorded decision, not an omission." | S5 |
| dr-validate-change-14 | .claude/skills/dr-validate-change/SKILL.md:53 | "**Map validation — the documentation half of the gate:**" | S5 (source sub-numbers this "4b") |
| dr-validate-change-15 | .claude/skills/dr-validate-change/SKILL.md:61 | "A failing check is a FAIL verdict exactly like a failing test." | S5 |
| dr-validate-change-16 | .claude/skills/dr-validate-change/SKILL.md:64 | "`--stale` is advisory, but every entry it lists must be either updated or explicitly dismissed in VALIDATION.md with the reason." | S5 |
| dr-validate-change-17 | .claude/skills/dr-validate-change/SKILL.md:67 | "Confirm too that behaviour the change ADDED is covered by at least one new map check." | S5, S3 (dup cluster: new-check-required) |
| dr-validate-change-18 | .claude/skills/dr-validate-change/SKILL.md:69 | "A change with no new check has documented nothing falsifiable." | S5 |
| dr-validate-change-19 | .claude/skills/dr-validate-change/SKILL.md:70 | "And if the change added a typed-record OBSERVABLE...confirm a sweep probe for it exists or is specced as its own follow-up commit." | S5 |
| dr-validate-change-20 | .claude/skills/dr-validate-change/SKILL.md:74 | "Requirement sweep: for every R in REQUEST.md, one line...An R with neither is a FAIL." | none |
| dr-validate-change-21 | .claude/skills/dr-validate-change/SKILL.md:76 | "the work is incomplete no matter how green the gate is" | none |
| dr-validate-change-22 | .claude/skills/dr-validate-change/SKILL.md:78 | "Assumption audit: list SPEC.md's assumptions A1..An in VALIDATION.md so the delivery surfaces them to the operator." | none |
| dr-validate-change-23 | .claude/skills/dr-validate-change/SKILL.md:110 | "VALIDATION.md committed and pushed, every acceptance check run with pasted output, every R swept." | none |
| dr-validate-change-24 | .claude/skills/dr-validate-change/SKILL.md:112 | "No file other than VALIDATION.md (and PARKED.md) modified." | W3 |
| dr-validate-change-25 | .claude/skills/dr-validate-change/SKILL.md:113 | "A map document that needs updating is a FAIL routed back to `dr-execute-step`, not something validation fixes in passing." | none |

### dr-verify-outcome/SKILL.md

| ID | file:line | sentence | flags |
|---|---|---|---|
| dr-verify-outcome-1 | .claude/skills/dr-verify-outcome/SKILL.md:9 | "You verify; you do not patch." | none |
| dr-verify-outcome-2 | .claude/skills/dr-verify-outcome/SKILL.md:10 | "Any new code change belongs to a fresh cycle through the orchestrator." | none |
| dr-verify-outcome-3 | .claude/skills/dr-verify-outcome/SKILL.md:15 | "**Criterion command.** Run GOAL.md's success command verbatim. Paste output." | none |
| dr-verify-outcome-4 | .claude/skills/dr-verify-outcome/SKILL.md:17 | "**Historical roots.** If the fix changed a reader/validator, re-run `verify_root`...the target violations must disappear, everything else must be unchanged." | none |
| dr-verify-outcome-5 | .claude/skills/dr-verify-outcome/SKILL.md:20 | "List remaining violations by class — do not summarize them away." | W3 |
| dr-verify-outcome-6 | .claude/skills/dr-verify-outcome/SKILL.md:23 | "**Live run (only if GOAL.md demands live proof).** At most ONE attempt, fully guarded" | none |
| dr-verify-outcome-7 | .claude/skills/dr-verify-outcome/SKILL.md:24 | "Preflight: env file present, `deepreason` importable, run identity free (retire + commit rename first if occupied)." | S3 (dup cluster: root-retirement) |
| dr-verify-outcome-8 | .claude/skills/dr-verify-outcome/SKILL.md:26 | "Launch detached from the ladder's own directory: `setsid nohup ./<ladder>.sh & disown`." | S3 (dup cluster: detached-launch) |
| dr-verify-outcome-9 | .claude/skills/dr-verify-outcome/SKILL.md:28 | "Arm rollback insurance: the snapshot loop...and a monitor on `progress.jsonl`...alerting on both success AND failure signatures." | S3 (dup cluster: detached-launch) |
| dr-verify-outcome-10 | .claude/skills/dr-verify-outcome/SKILL.md:32 | "Judge only typed outcomes: run state, stop_reason, audit JSON, `verify_root`, FINDINGS.md." | S3 (dup cluster: typed-outcomes-only) |
| dr-verify-outcome-11 | .claude/skills/dr-verify-outcome/SKILL.md:33 | "Model prose is not verification." | none |
| dr-verify-outcome-12 | .claude/skills/dr-verify-outcome/SKILL.md:37 | "A live attempt that never reaches the fixed path is INCONCLUSIVE for that path — say so; the offline regression remains the proof of correctness." | none |
| dr-verify-outcome-13 | .claude/skills/dr-verify-outcome/SKILL.md:39 | "Do not burn repeated live attempts chasing a stochastic path: one relaunch maximum, then record the residue." | W3 |
| dr-verify-outcome-14 | .claude/skills/dr-verify-outcome/SKILL.md:54 | "Append a dated segment to the experiment's RESULTS.md: what was observed, what was fixed, what the record now shows, and the honest residue." | none |
| dr-verify-outcome-15 | .claude/skills/dr-verify-outcome/SKILL.md:56 | "'Accepted does not mean true'; never claim more than the record shows." | none |
| dr-verify-outcome-16 | .claude/skills/dr-verify-outcome/SKILL.md:58 | "**Errata check — mandatory, before VERIFY.md is committed.** ... If yes, the `docs/ERRATA.md` entry lands in the SAME commit as VERIFY.md." | S3 (dup cluster: errata-checkpoint) |
| dr-verify-outcome-17 | .claude/skills/dr-verify-outcome/SKILL.md:63 | "If no, state 'errata: none' explicitly in VERIFY.md's Errata line." | S3 (dup cluster: errata-checkpoint) |
| dr-verify-outcome-18 | .claude/skills/dr-verify-outcome/SKILL.md:66 | "Commit and push everything; confirm `git status` is clean and the branch head is on the remote." | none |
| dr-verify-outcome-19 | .claude/skills/dr-verify-outcome/SKILL.md:68 | "Report: verdict, evidence pointers, PARKED.md contents as candidate next tranches." | none |
| dr-verify-outcome-20 | .claude/skills/dr-verify-outcome/SKILL.md:71 | "On FAIL: append the failure evidence to DIAGNOSIS.md, commit, and return to the orchestrator (route: dr-diagnose)." | none |
| dr-verify-outcome-21 | .claude/skills/dr-verify-outcome/SKILL.md:72 | "Never patch from inside this skill." | none |

### Cross-file duplication clusters (S3)

Ten clusters account for nearly every S3 flag above — the same procedure
or prohibition, stated in full (not delegated) in multiple files:

1. **Map preflight** (4 copies in full: README, deepreason-orchestrator,
   dr-change-orchestrator, dr-drive-harness; a 5th, dr-plan-steps,
   restates it as "scope from the map before planning steps"). Biggest
   cluster; a strong MERGE signal for Phase B — one canonical statement
   (dr-drive-harness, the designated driving-manual authority) with the
   other four pointing at it.
2. **Environment/session preflight** (git log/status/pip
   install/env-file check): full copies in deepreason-orchestrator AND
   dr-drive-harness; dr-change-orchestrator already delegates correctly
   ("load `dr-drive-harness`") — the asymmetry itself is a finding.
3. **Commit-and-push-every-phase-boundary**: README, deepreason-
   orchestrator, dr-change-orchestrator, dr-drive-harness, dr-plan-steps
   (5 restatements of the same sentence).
4. **Root retirement** (`git mv run-<id> ...`, commit rename first):
   deepreason-orchestrator, dr-drive-harness, dr-implement-fix,
   dr-verify-outcome (4 copies).
5. **Credential handling** (env gitignored, never commit): deepreason-
   orchestrator, dr-drive-harness, dr-change-orchestrator,
   dr-implement-fix (4 copies).
6. **Detached-launch + monitor** (`setsid nohup ... & disown`, arm
   snapshot loop): dr-drive-harness, dr-verify-outcome (2 full copies).
7. **Judge-only-typed-outcomes**: dr-drive-harness, dr-verify-outcome (2
   copies).
8. **Stop-format** ("decision in ONE sentence, options priced,
   recommendation"): dr-change-orchestrator, dr-drive-harness,
   dr-execute-step (3 copies).
9. **Map-moves-same-commit / new-check-required / Verified-at-honesty**:
   each restated independently in dr-execute-step, dr-implement-fix,
   dr-plan-steps, dr-validate-change (the general map-obligations
   procedure duplicated per-phase rather than stated once and cited).
10. **Errata-checkpoint** ("did this tranche find a wrong claim...errata:
    none"): dr-deliver-change, dr-verify-outcome (near-identical
    paragraph in the two family-terminal skills).

Two files model the GOOD pattern instead (cite the canonical location,
don't restate it): dr-implement-fix-5 and dr-spec-change-20 both point at
"`dr-execute-step`'s Durable tests, checks, and probes rules" rather than
repeating them. Phase B's router/GATE design should extend that pattern
to clusters 1-10 above.

### Cross-cutting flag totals (informational)

- W1 (cannot fail): ~8 rows, mostly single-clause aphorisms ("You do not
  freelance", "Plan against that") rather than the file's operational
  content — low density relative to file size, not a systemic problem.
- W3 (ungated negation): ~30 rows. Most are gated (an outlet or
  enforcing mechanism appears in the same sentence or the same section)
  and are marked "none" above; genuine ungated negations cluster in
  deepreason-orchestrator/dr-change-orchestrator's terse "Never X"
  prohibition lists and in dr-drive-harness's process-hygiene bullets.
- W5 (incident story as prose): concentrated almost entirely in
  dr-drive-harness (6 rows) and dr-execute-step (4 rows) — both already
  carry the mechanized GATE beside the story (diff_budget.py,
  blast_radius.py, the recursive wall-clock scrub), so W5 here is "delete
  the story, keep the citation" rather than "the GATE is missing."
- S1 (loop control in a worker skill): zero confirmed rows after
  correction — the one candidate (dr-execute-step-4) does not qualify;
  no worker file was found embedding "then pick the next phase" routing
  logic. This is a genuine negative result, not an omission.
- S5 (bolted-on / sub-lettered): concentrated in dr-deliver-change (3b,
  3c), dr-plan-steps (4b, 4c), dr-validate-change (4a2, 4a3, 4b), and
  dr-spec-change (an un-lettered but visibly appended "one more
  guardrail" clause) — four files where a later rule was inserted into
  an already-numbered procedure rather than the procedure being
  renumbered, exactly the authoring-skills S5 pattern.

## Evidence binding

Per authoring-skills E1: "A skill with no bound evidence is a DELETE
candidate; overlapping skills are MERGE candidates." Per R6/the operator's
OPERATOR OVERRIDE, this pass cites only ALREADY-COMMITTED sources —
`docs/ERRATA.md` (E1-E23), `docs/ERRATA_EXECUTOR.md` (X1-X13, XE1,
X5-E), and CLAUDE.md's own "Hard-won invariants" — no fresh trials were
run. Two incidents the operator named in the OPERATOR OVERRIDE (wheel-
smoke pins left behind by the all-configs window; the judge-seat run
compiling inert authority settings) were searched for
(`grep -rl` across `experiments/` and `docs/`) and are NOT independently
findable as a specific ledgered entry — consistent with REQUEST.md's own
"PARKED BY DESIGN: the full repo sweep/smoke re-pin audit (next tranche,
operator-ordered)". They are cited below as operator-asserted-but-not-
yet-ledgered, never invented as a false match to an existing entry.

Family-1 (defect) tranches have actually run 17 times
(`find experiments -maxdepth 2 -name GOAL.md | wc -l` = 17); the
family's own errata coverage is thinner than Family 2's, which the
X-series (`docs/ERRATA_EXECUTOR.md`) was purpose-built to observe — this
asymmetry is itself a finding, not a gap in this census.

| Skill | Evidence | Signal |
|---|---|---|
| `README.md` | No ERRATA-class finding about its own content; X1 shows an INDEX's absence from a checkout causes misrouting (value of *some* index existing). But readme-3/4/5/6 (Rule extraction) are near-verbatim duplicates of content stated in full elsewhere (map-preflight and commit-every-boundary clusters). | MERGE candidate — thin distinct content once clusters 1/3 are deduplicated; Phase B decides whether it survives as a pure pointer page. |
| `authoring-skills/SKILL.md` | This tranche's own binding authority (REQUEST AUTHORITY quote); its rules mirror empirically observed patterns — G6 (mutation-prove) mirrors X8's golden-test catch; G1/X2 (proof required, mechanical stop) mirrors X3/X5-E/X6/X9's repeated validation-FAIL-catches-self-blessed-claims pattern. | KEEP — out of delete/merge consideration by construction (this tranche applies it, does not revise its content). |
| `deepreason-orchestrator/SKILL.md` | Family 1 has run 17 times; E6 (misdiagnosed root cause corrected via record-first diagnosis, `experiments/2026-08-03-fix-attached-evidence-integrity`) and E16 (crash mechanism refuted, broader true cause found, `experiments/2026-08-08-fix-l1-continue-resumable-crash`) both show the record-first discipline this router enforces catching real misattributions. | KEEP, evidenced. |
| `dr-ask-the-right-question/SKILL.md` | X11 — caught a false premise in the MONITOR's own authorization ("BridgeConfig's current defaults are the dead ones") before a line of code was written, via the dominance-test fork-and-ask procedure this skill defines. | KEEP, strongly evidenced (the one entry recorded "against the infrastructure's author"). |
| `dr-capture-request/SKILL.md` | E21 — Amendment 10's "and" reading, later corrected by Amendment 11, was only traceable because the verbatim ledger ("REQUEST.md's own R26 entry stands unedited, verbatim, per its append-only ledger rule") preserved both readings for comparison. | KEEP, evidenced. |
| `dr-change-orchestrator/SKILL.md` | The single most-exercised skill in the set: the entire rung program (X2-X13, X5-E, XE1) ran under this router 2026-08-03 through 2026-08-11, with the FAIL-loop firing and self-correcting at least four separate times (X3, X5-E, X6, X9). | KEEP, most heavily evidenced skill in the set. |
| `dr-deliver-change/SKILL.md` | The 2026-08-11 errata-checkpoint compliance audit checked 4 closed deliveries and found exactly ONE violation (missing Errata section, `experiments/2026-08-09-change-judge-evidence-review/DELIVERY.md`) — the mandatory-errata-check clause (S5-flagged "3c") is shown catching a real omission. | KEEP, evidenced. |
| `dr-diagnose/SKILL.md` | E6 and E16 (both cited above) are BOTH dr-diagnose outputs being corrected/vindicated by record-first re-diagnosis; CLAUDE.md's own turmite/jolt "read the blob before theorizing" hard-won invariant predates and matches this skill's Traps-first procedure. | KEEP, evidenced. |
| `dr-drive-harness/SKILL.md` | XE1 — *skipping* this skill's own session-preflight step (reading CLAUDE.md/RESULTS.md/ERRATA.md at session start) is the RECORDED PROXIMATE CAUSE of an unauthorized frozen-surface commit; the incident report is itself the argument for keeping the preflight rule, not for deleting the skill. | KEEP — evidenced by a documented failure-to-follow, which argues for the rule's necessity, not its removal. |
| `dr-execute-step/SKILL.md` | Three separate, specific, self-cited incidents: X8 (frozen-surface leak caught by golden tests + full gate); the diff_budget miss ("193 insertions landed against a <=150 ceiling with no stop, V1 tranche 2026-08-05", quoted verbatim in-file); the 2026-08-09 "frozen-surface stop did not hold" entry, which the file's own text names as the direct design premise of its blast_radius.py drift-check paragraph. | KEEP, most heavily self-evidenced single procedure in the set. |
| `dr-explain-to-operator/SKILL.md` | No ERRATA-class corrected-incident found (communication style is not errata-tracked material). Evidence class differs from the others: a direct, repeated, verbatim operator mandate (CLAUDE.md 2026-08-06, extended 2026-08-08 — operator's own words: "It needs to be used during every intermediary output... Keep it for every last output"), itself a committed, dated instruction. | KEEP-by-direct-mandate — flagged as a distinct evidence class from KEEP-by-corrected-incident; not a DELETE candidate (E1's bar is about SKILL efficacy, not about overriding a standing operator law), but Phase B should not claim ERRATA-class evidence for it that does not exist. |
| `dr-implement-fix/SKILL.md` | The same diff_budget miss ("193 insertions against <=150, V1 tranche 2026-08-05") is cited verbatim in this file too; no specific ERRATA entry names a dr-implement-fix-caused defect, but the "fix readers, never writers" and "map moves same commit" rules it enforces are exactly what E6's fix and X8's Traps-entry-in-same-commit pattern show working. | KEEP, evidenced (shared incident with dr-execute-step; mechanism matches E6/X8). |
| `dr-plan-steps/SKILL.md` | Cited directly by dr-spec-change's own text: "rung 4's prediction was too narrow; rung 5's spec predicted nothing and missed a test pinning 'exactly one backend'... The full gate caught both, three commits later than the census would have" — the rung-4/5 miss that motivated the mandatory blast-radius census this skill also requires (dr-plan-steps-9). The "trailing documentation step gets dropped" claim (S5/W5-flagged) matches E9/E11's pattern of map documentation drifting when left as an afterthought. | KEEP, evidenced. |
| `dr-propose-fix/SKILL.md` | No direct ERRATA citation of a dr-propose-fix output, but its two DeepReason-specific design rules are exactly what E6 (fix readers, not writers — "the READER was wrong and was fixed... `verify_root` on the unchanged bytes returns zero violations") and X9 (frozen surfaces need a flag: validation FAILED a technically-correct-but-unauthorized touch) show working in practice. | KEEP, evidenced indirectly via the mechanism it prescribes. |
| `dr-reproduce/SKILL.md` | E6's "four-artifact proof" DIAGNOSIS/REPRO pairing; the "NEVER reproduce by launching a live provider run" rule is directly what E15 warns against conflating (a live-run absence read as "stochastic miss" when the record showed a structurally dead path, not a probability). | KEEP, moderately evidenced. |
| `dr-set-goal/SKILL.md` | Weakest Family-1 evidence binding found: no specific ERRATA-class corrected failure names a dr-set-goal output. 17 Family-1 tranches have used it operationally, but no committed correction demonstrates a failure it prevented. | KEEP — flagged as the thinnest-evidenced surviving skill; not a DELETE candidate under E1's letter (no failures found is different from "the skill demonstrably fails"), but Phase B should not overstate its evidence base. |
| `dr-spec-change/SKILL.md` | Names its own motivating incidents in its own text: the 2026-08-09 "frozen-surface stop did not hold" entry (surface-3 words-before-touch breach) and `experiments/2026-08-10-change-blast-radius-analysis/REQUEST.md` as the design premise of its mandatory blast-radius sections; shares the rung-4/5 census miss with dr-plan-steps. | KEEP, very strongly evidenced — self-documenting. |
| `dr-validate-change/SKILL.md` | Four separate FAIL-loop catches across different defect classes: X3 (map-header consistency gap), X5-E (invented env-var name — a content transcription error), X6 (same), X9 (frozen-surface governance despite total technical correctness). | KEEP, the most heavily and diversely evidenced skill in the set alongside dr-change-orchestrator. |
| `dr-verify-outcome/SKILL.md` | The 2026-08-11 errata-checkpoint audit explicitly found: "No VERIFY.md (Family 1) tranches closed in this window... the dr-verify-outcome half of the checkpoint rule has not yet been exercised by a real tranche since it landed." Its errata-checkpoint clause is a direct twin of dr-deliver-change's (exercised, found one violation) but is itself UNTESTED. | KEEP — flagged as carrying one specific untested clause (the errata checkpoint), a genuine finding for the record rather than a merge/delete signal. |

### Summary signal for Phase B

No skill has ZERO bound evidence, so none is an automatic DELETE
candidate under E1's literal bar. The actionable signal from this
census is overwhelmingly MERGE, concentrated in the ten S3 clusters
above (Rule extraction) rather than in whole-file redundancy — most
files carry both duplicated boilerplate (map preflight, env preflight,
commit-every-boundary, root retirement, credentials, detached-launch,
typed-outcomes-only, stop-format, map-obligations, errata-checkpoint)
AND non-duplicated, evidenced, file-specific content. `README.md` is the
one file whose OWN distinctive content is thin enough after
deduplication to be a genuine MERGE-into-nothing (pure pointer page)
candidate. Two evidence-class flags carry into Phase B rather than
being resolved here: `dr-explain-to-operator` is KEEP-by-direct-mandate
(not KEEP-by-corrected-incident, a different justification the design
should state honestly), and `dr-verify-outcome`'s errata-checkpoint
clause is untested (KEEP, but the corresponding GATE has not yet been
observed catching anything the way dr-deliver-change's has).
