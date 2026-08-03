---
name: dr-ask-the-right-question
description: Question discipline for working DeepReason - route every question to the cheapest authority (record, then framework, then operator), translate the operator's shorthand into typed obligations, and frame uncertainty as falsifiable forks. Load whenever an operator message is ambiguous or short, whenever any workflow phase says "stop and ask", whenever evidence contradicts your expectation, and at the start of any session run by a model that has not worked this repo before.
---

# Ask the right question

The two workflow families tell you what to PRODUCE. This skill tells you
what to ASK, of whom, in what order — the reasoning that happens between an
operator message and the first phase artifact. Working here fails in two
ways: asking nothing (you invent facts and build on them) or asking the
operator everything (their attention is the scarcest budget in the system).
Both are the same mistake — a question routed to the wrong authority.

## 1. The three authorities, in cost order

Every question has a cheapest competent authority. Ascend only when the
cheaper one genuinely cannot answer.

| Authority | Answers questions like | Cost |
|---|---|---|
| THE RECORD — `log.jsonl`, `objects/`, typed verdicts, blobs, instruments (`verify_root`, `tools/root_sweep.py`, `tools/docs_verify.py`, the gate) | what happened; which value was rejected; do two instruments agree; did anything move | a command |
| THE FRAMEWORK — CLAUDE.md, `docs/map/` (Traps first), `docs/ERRATA.md`, the tranche ledgers (REQUEST/GOAL/PARKED), prior DELIVERY reconciliations | what is frozen; what has gone wrong here before; what did the operator already rule; where does X live | a file read |
| THE OPERATOR | genuine forks the record and framework underdetermine; frozen-surface approval; taste on user-facing shape | the scarcest budget there is |

Two rules that are always in force:

- **Cite the instrument with the number.** Two instruments can both be
  right and disagree: the root census is 45 by direct manifest load over
  `git ls-files` and 42 rows by `root_sweep.py`, which scans `experiments/`
  only. A number without its instrument is not a fact yet
  (`docs/ERRATA.md` E5, E8; `DR-INV-frozen-surfaces`, "The root sweep").
- **Model prose is never evidence.** Yours included. If your answer to a
  record-question does not end in a command output or a file path, you have
  not asked the record yet.

## 2. Reading the operator

The operator writes tersely and expects the repo's context to carry the
rest. Each row is a real committed exchange — look it up when unsure.

| The operator says | It means | Not | Committed evidence |
|---|---|---|---|
| "Do it" / "go ahead" after you stated a plan | approval of EXACTLY that plan | a new vague instruction; license to widen | FIX.md, `experiments/2026-08-03-fix-attached-evidence-integrity` ("operator approval on the stated plan: 'Do it.'") |
| "…as you go" ("fix documentation as you go") | a STANDING grant — but you must bound it in the tranche ledger and park the rest | permission to survey and rewrite everything | that tranche's GOAL.md, "Documentation (operator-granted scope addition)" |
| "are you using X?" about your process | a prompt: check honestly, answer plainly, and apply X now — the honest "no" is expected and useful | an accusation to deflect, or a yes/no to answer without checking | REPRO.md map-finding section of the same tranche (the answer "not until now" surfaced a missing seam) |
| "start an errata please" (artifact named, shape unstated) | derive the shape from repo conventions (honest ledger, append-only, evidence pointers) and build it; say what you assumed | a reason to ask what an errata is | `docs/ERRATA.md` header block |
| an apparent typo or wrong name ("Claude.me") | resolve by repo context and proceed; note the resolution in one clause | a blocker; a thing to ask about | CLAUDE.md is the only near-match in the tree |
| a new instruction mid-tranche | APPEND to REQUEST.md verbatim, reconcile through dr-spec-change | something to absorb silently into the current step | dr-change-orchestrator, "The ledger rule" |

The general rule behind every row: the operator's words are AUTHORITY, so
treat them the way the harness treats a record — quote them verbatim into
the ledger, then interpret them in writing where the interpretation can be
reviewed (REQUEST.md quotes; SPEC.md interprets). If you find yourself
paraphrasing the operator from memory, you have already lost the thread.

## 3. Ask the record first

Before any theory about a failure or a surprise, in order:

1. **Which instrument produced this?** Name it. A verdict without an
   instrument is hearsay (section 1).
2. **What does the typed artifact say verbatim?** `run-status.json` state
   and stop_reason; the violation's `check` and `detail`; the blob under
   `blobs/` with the rejected value. Both cycle-0 deaths in this repo's
   history were misattributed by readers who theorized before opening the
   diagnostic blob (CLAUDE.md, hard-won invariants; `DR-SUB-capabilities`
   Traps, jolt `run-b4d6dfda`).
3. **Do two instruments agree?** rc codes, `verify_root`, the audit JSON,
   the report layer. Agreement is signal; disagreement is a finding about
   an INSTRUMENT, not yet about the system (ERRATA E8: a fix's predicted
   verdict flip appeared in `verify_root` but not in the sweep, because
   the sweep also binds the stored terminal summary — frozen evidence).
4. **Has this gone wrong here before?** The covering map document's Traps
   section, then `docs/ERRATA.md`. A recurrence is the cheapest diagnosis
   available.
5. **What would falsify my current reading?** If nothing could, it is not
   a reading, it is a mood.

## 4. Derive before asking

(Absorbed from `dr-decide-or-ask`, kw8imd lineage, commit 86f1248e —
credited, superseded here.) Before composing ANY question to the operator,
derive their answer from what they have already said: this tranche's
verbatim words, CLAUDE.md's standing rules, prior rulings in DELIVERY
reconciliations and RESULTS conventions. This operator's recorded values:
smallest correct change; fix readers, never invalidate committed records;
no frozen surface without explicit approval; honesty over polish —
negative results recorded as negative; a reachable defect is fixed or
parked, never shipped silently.

**The dominance test:** would every reasonable operator holding those
values choose the same option? Then the fork is false — decide, act, and
record one line: "Decided without asking (dominant under your recorded
values): <choice> — override any time."

**What earns a question:** options that survive the dominance test AND
change real stakes — frozen-surface or irreversible action, >2x effort
divergence between defensible readings, a conflict WITHIN the operator's
own words, or taste on user-facing shape. Batch every such fork into ONE
question set per tranche; lead with your recommendation and its
one-sentence reason; state each option's consequence in the operator's
terms (risk, cost to them, honesty of the record), including the
do-nothing consequence when it leaves something reachable-broken.

## 5. Frame forks falsifiably

When you are genuinely uncertain between two readings, do not pick one and
build — and do not ask yet either. Write BOTH readings as alternatives the
record can decide between, each with the evidence that would prove it, the
way the attached-evidence tranche's GOAL.md framed W ("the writer breached;
the finding is correct; the root stays invalid") against R ("the reader
over-demands; the finding is spurious") before any code was read. Then
collect the deciding evidence. The fork that survives IS your diagnosis;
the fork that died is your "Ruled out" section. A goal written this way is
decidable under either outcome, which is what makes it a goal rather than
a hope (`experiments/2026-08-03-fix-attached-evidence-integrity/GOAL.md`,
DIAGNOSIS.md).

## 6. The wrong-question table

Questions this repo has already paid for asking — or paid for not asking.
Each cites the committed scar.

| Wrong question | Right question | Scar |
|---|---|---|
| "Which schema rule failed?" (theorizing at cycle-0) | "What does the diagnostic blob say verbatim?" | CLAUDE.md hard-won invariants: both cycle-0 deaths misattributed on first reading |
| "Is the count 42 or 45?" | "Which instrument, over which scope, produced each count?" | ERRATA E3/E5: both were true; the census check went stale asserting one of them |
| "Why is this root invalid?" (accepting the finding's prose) | "Does the artifact the finding names actually exist in the state?" | ERRATA E6: the detail text named as missing an artifact present at seq 4 |
| "Which artifact mentions the source record?" (shape as identity) | "Which artifact carries the discriminator only the trusted writer can stamp?" | `DR-SUB-verification` Traps: a mention-shaped predicate selected ordinary citations |
| "Can I reuse this passing check?" | "Can this check FAIL, and on whose machine?" | ERRATA E7: four map checks passed only on the machine whose gitignored roots they opened |
| "Should I ask the operator which option they prefer?" | "Do the operator's recorded values already decide this?" | Section 4; a false fork spends the budget the whole system is designed to conserve |

**Exit criterion.**
Before you send any question upward or act on any assumption: every
question you almost asked is either answered-with-a-command (record),
answered-with-a-citation (framework), decided-and-recorded (dominant), or
sitting in ONE batched question set with a recommendation. Zero questions
whose answer a reader of CLAUDE.md, the map's Traps, and this tranche's
ledger could have given without you.
