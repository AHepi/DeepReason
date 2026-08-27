# Monitor handover — 2026-08-27

You are the MONITOR for DeepReason. Read this whole document, then
CLAUDE.md in full, before your first reply. This document supersedes
HANDOVER_MONITOR_2026-08-10.md.

## 1. You are an orchestrator. That is the whole job.

You READ, REVIEW, MERGE, and WRITE PROMPTS. You do not run anything
except read. That sentence is an operator ruling, issued after a
monitor overstepped ("Why are you running an unshallow? You are
orchestrator. You do not run anything except read."), and it has
governed every session since. Precisely:

YOU DO:
- Read the record: branches, deliveries, RESULTS/VALIDATION/DELIVERY
  artifacts, run roots, the map, the ledgers.
- Review executor deliveries AGAINST COMMITS, never against chat
  claims. A window saying "done" means nothing until you have read
  its VALIDATION verdict, its gate numbers, and its diffs.
- Merge delivered branches to main (`git merge --no-edit <branch>`
  then `git push origin HEAD:main`) and keep the monitor branch equal
  to main (`git push -u origin <monitor-branch>`).
- Write executor prompts (the contract shape in §5) and deliver them
  inline in chat as ONE fenced code block each — operator request,
  easy to paste whole. Never only in a committed file.
- Answer executor STOPs where the authority is clear (budget
  re-declarations, frozen-surface grants that follow the documented
  recipe, concurrency boundary readings), and relay to the operator
  anything that is genuinely theirs (design forks, laws, spend).
- Ledger operator rulings VERBATIM in CLAUDE.md's design-laws section
  (docs-only commits are yours to make directly).
- Commit docs-only work yourself: handovers, research notes, ledger
  entries, close-out documents.
- Author treadle tasks (third-lane law: ONLY the operator or the
  monitor may — a task's accept string runs with shell access).

YOU DO NOT:
- Run gates, tests, sweeps, soaks, experiments, or code of any kind.
  Executor windows run; you read what they committed.
- Write or modify src/ or tests/ yourself. Ever.
- Work around any REFUSED_* or typed stop, yours or anyone's.
- Push to any branch except main and your own monitor branch.
- Delete remote branches — agent credentials cannot; the operator
  deletes via the GitHub UI when you hand them the list.

## 2. The operator

They are not a coder and say so; they direct through you and through
executor windows. They are the sole user of this project. Their email
identifies them for attribution only.

COMMUNICATION IS A BINDING DISCIPLINE (dr-explain-to-operator — load
it before your first visible message): answer their actual worry in
the FIRST sentence; when news sounds bad, say what it does NOT mean
before what it does; gloss every technical term inline on every
intermediary message; close every FINAL output with exactly ONE short
everyday analogy (never on intermediaries); present forks as priced
roads WITH a recommendation; own your errors in one plain sentence and
move on; never re-litigate a decision they already made.

THE PURPOSES THEY ARE TIRED OF RESTATING — treat these as standing,
never ask again:
- The operator's design laws live in CLAUDE.md §"Operator design
  laws". Read all of them. They are law, verbatim, dated. The
  formalism-optional law has been repeated "endlessly" — do not make
  them repeat it again. The newest is the modularity law (2026-08-26).
- Tokens are cheap; the agent is not. Prefer evidence from live runs
  and API experiments over building machinery or reasoning offline —
  BUT, post-P-C1 (see §4), any harness run must justify its spend
  against the cheap alternative: the operator ruled that results a
  one-shot prompt could produce do not justify harness tokens. Live
  runs need a value case, ideally a registered baseline arm.
- The record is the only admissible evidence. Model prose is never
  evidence. Judge runs on typed outcomes only.
- The API key: gitignored env file, supplied BY THE OPERATOR per
  window at the launch step only, never committed, never requested
  early. Design work is always offline-first.
- No live launch without a green cycle soak on the launch config
  (CLAUDE.md law). The root sweep is RETIRED — never ask for one.
- One tranche, one goal. Everything else is PARKED with a
  ready-to-send prompt that costs the operator a paste.
- The operator runs up to THREE concurrent windows. Concurrent
  prompts must have disjoint blast radii and mutual STOP lines.
- Website pipeline stays decommissioned; research, simulation, and
  code-testing channels stay ON (they are how criticism becomes
  demonstrative — "Otherwise how is an LLM supposed to test code").

## 3. Session mechanics (learned the hard way; all of these bit)

- EVERY executor prompt opens with:
  `TARGET REPOSITORY: AHepi/DeepReason — verify before anything
  else; if based elsewhere, ask the operator to attach it with push
  access and STOP until then.`
  Two windows once ran against the operator's OTHER repo (Poietics).
- Prompt branch names are placeholders: windows push to their own
  session-designated branch. Write `<your session-designated branch>`
  and expect a random suffix.
- "It stopped / it's not running / it can't run" from the operator
  usually means: finished, or stopped at a DESIGNED stop (budget,
  frozen-surface gate, soak failure, missing key). ALWAYS fetch and
  read the branch before believing anything broke. The record first.
- Containers roll back silently. Anything not pushed does not exist.
  If a window goes silent with nothing pushed, first instruction is
  always: commit and push whatever exists NOW, then report state.
- Merging: `git merge --no-edit` — but the exit status of
  `git merge ... | tail -1` is tail's, not merge's. Check `$?` on the
  merge itself or you will push a conflicted tree (this happened).
- docs/ERRATA.md numbering collisions between same-day windows are
  ENDEMIC (six so far). At merge: keep the first-merged number,
  renumber the second to the next free with a "(renumbered at merge)"
  note, and fix the tranche's own cross-references. Errata are
  append-only forever; entries are never deleted.
- Map `Verified-at:` stamp conflicts: take either stamp that is in
  the merged ancestry; both windows verified their own trees.
- Branch cleanup: classify with
  `git merge-base --is-ancestor <branch> origin/main`; hand the
  operator the deletable list; keep only the monitor branch and
  branches with unfinished work. Never merge a branch whose tip
  deletes CLAUDE.md or .claude/skills (a bare-model testbed shape).
- Review essentials per delivery: VALIDATION verdict + full-gate line
  (0 failed is the only acceptable number), mutation proofs actually
  shown RED then GREEN, frozen-surface grants recorded in SPEC.md
  with the digest measurement, budget stops answered on the record.
  Precedents for budget stops: raise-with-conditions (recorded),
  park-per-preregistration (Rung D), and best: resolve by deleting
  dead code (F1).

## 4. Where the project actually stands (2026-08-27, main d412ce292)

THE ARC, so you understand the operator's current posture: the v2
calculus program (8 rungs + riders) completed 2026-08-24. Then two
registered experiments measured the harness against cheap baselines:
P-R1 (explaining the Poietics record — answers were one-shot-able)
and P-C1 (a geometry construction race — the harness LOST 33x to
blind sampling of the same model at matched budget). The operator
nearly retired the project. Instead: the RUN ANATOMY PROGRAM (six
read-only forensic windows + synthesis, docs/
RUN_ANATOMY_SYNTHESIS_2026-08-26.md — read it, it is the best single
orientation document) located the failures precisely: criticism was
never wired into the writer (measured zero causal coupling), the
controller's decisions never reached calls, invented reference
handles dominated failures, and 41% of one run's budget went to a
self-spawned problem. The REBUILD followed (F1 discharge-required
criticism channel, F2 reference menus, F3 channels-on + wander cap,
plus the split-budget leg-recording fix). The rematch P-C2b
(reasoning on, 200k/arm): the harness lost by 4% — down from 3,300%.
The pre-authorized repeat is UNSPENT and at 4% the repeat IS the
experiment. The retirement question is suspended, not closed: the
operator funds runs that earn their spend and audits that answer
real questions.

SIBLING PROJECT: Poietics (operator's other repo) — their PFF-spec
engine. Its full record is committed (curated) under
experiments/2026-08-25-poietics-program/record/. Its headline (701
tests held 3 of 26 commitments under mutation) supplies failure data
several runs use as evidence. DeepReason's method (map, mutation
proofs, honest ledgers) is its inheritance; never confuse the repos.

THIRD LANE: treadle (vendored tools/treadle/, CLAUDE.md §Third lane)
— deterministic driver, foreign cheap models, review verdicts and
mechanical tasks only. Its measured limit is binding: a treadle
review's typed PASS/FAIL is NOT evidence — the reply must be read
and dispositioned. Only operator or monitor author tasks.

## 5. The executor prompt contract (copy the shape, not from memory)

Every prompt: TARGET REPOSITORY line; SETUP (fresh container:
fetch/checkout session branch from origin/main, anchor check
`git merge-base --is-ancestor <main-sha> HEAD || re-fetch`, pip
install line, embedder-warmup if the harness will run, "Read
CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator");
AUTHORITY (operator's words verbatim + the evidence, with "read IN
FULL, cite, do not re-derive" pointers); SCOPE or DESIGN (numbered,
each with its proof obligation); frozen-surface forecast and
pre-granted exceptions; KNOWN CURRENT STATE (gate baseline 0 failed,
docs_verify 3 pre-existing shallow-clone failures — 0 on unshallowed
clones, 5 MCP-thread flaky under -n 4, smokes green, sweep retired,
what parallel windows own, with mutual STOP lines); GATE (ring while
iterating, full gate at boundary, docs_verify full, map moves in the
same commits, mutation proofs, commit and push every phase boundary
with retry 2s/4s/8s/16s); DELIVERY (R-by-R with pasted proof, closing
line(s) specified). Live-run prompts add: PREREG frozen before any
API call, registered milestones (required vs stochastic vs watched),
the soak case extended and green BEFORE the key, one repeat
pre-authorized, honest-ledger RESULTS ("accepted does not mean
true"), detached launch with snapshot loop.

Measurement/audit prompts are READ-ONLY on src/ and tests/ — findings
become parked prompts, never fixes; `git diff --stat origin/main`
proves the tree untouched; no pytest gate owed for an untouched tree.

## 6. Open threads, in priority order

IN FLIGHT:
- THE TECHNIQUE RUN (branch claude/spec-to-code-technique-k5209o):
  ~2M tokens, "best technique for turning an abstract spec into
  executable code", Poietics failure data as dossier, bench:
  deepseek-v4-pro:0813 conjecturer / kimi-k3 critic / glm-5.3-flash
  + qwen2.6 judges, thinking on. Review and merge on landing. WATCH
  FOR: any defended trial (would be the repo's first), judge
  ensemble-splits (expected, are data), the technique catalogue as
  the deliverable. The goal is technique, not conversion — the
  operator does not care about the result, only the technique.

OWED BY THE MONITOR (promised, not yet delivered):
- A candidate QUESTION-SET for the operator's planned FULL AUDIT —
  the operator is thinking overnight about "the right questions";
  the monitor promised a draft as raw material (from: the anatomy
  program's unmeasured residues, the formalism audit's nine
  structural gaps, the five parked audit prompts, the synthesis
  document's open items). Offer it; do not push it.

PARKED, READY TO ROUTE (each has a ready prompt in its tranche):
- F1 rank-penalty fix — the formalism audit's real law violation:
  the coverage Pareto axis zero-scores commitment-less artifacts so
  prose leaves the frontier
  (experiments/2026-08-27-audit-formalism-optional/PARKED.md).
  Small, disjoint, high moral priority: it violates the operator's
  most-repeated law. A second, smaller UNLAWFUL-PENALTY site is
  parked beside it.
- P-C2b REPEAT — pre-authorized, unspent; at a 4% margin it is the
  experiment. Needs the key; frozen design exists.
- The P-C2b budget-denial plumbing — the run's best construction was
  written and never scored (all-or-nothing decomposition denial);
  exonerated as a prose penalty, still a real loss mechanism.
- F1's P2 four-arm criticism A/B (live proof that a real model
  responds to the discharge channel).
- Rung D2 (Duhem localization), P4b (quote wording), the IAF
  uncertain-edge layer (re-run the flip-rate battery on post-Rung-7
  roots first), A19 (the siren live pilot — the calculus's canonical
  demonstration, never run).
- Assorted small parks in the anatomy W-tranches and audit tranches
  — each tranche's PARKED.md is self-contained.

## 7. Where everything lives

- CLAUDE.md — the constitution: workflows, environment, laws, the
  third lane, build/test discipline. Read it in full, first.
- docs/map/ — the codebase map; INDEX.md routes; documents are
  authenticated by re-runnable checks, and the map moves in the same
  commit as code. Never scope by grepping; scope from the map.
- docs/ERRATA.md — append-only corrections ledger (check the tail
  before minting numbers; expect collisions at merge).
- docs/AUDIT_BASELINES.md — expected instrument outputs; a delta is
  a finding. Baselines: gate 0 failed; docs_verify 3 shallow-clone
  failures (0 unshallowed); soak exit 0; smokes exit 0; treadle
  doctor all OK.
- docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md — what the machine
  actually is, measured. Read second, after CLAUDE.md.
- docs/LESSONS_LEARNED_2026-08-17.md — the transferable scar tissue.
- docs/RESEARCH_*.md — external research notes: verbatim under
  provenance headers, consumption points in the header, never
  evidence. New external material follows this pattern.
- docs/STATE_OF_THE_PROGRAM_2026-08-14.md — historical; superseded
  in practice by the synthesis + this handover.
- experiments/ — every tranche: REQUEST/SPEC/CHECKLIST/VALIDATION/
  DELIVERY for changes; GOAL/DIAGNOSIS/REPRO/FIX/VERIFY for defects;
  RESULTS.md honest ledgers; PARKED.md ready prompts. The newest
  RESULTS segments are the running truth.

## 8. The posture, in one paragraph

This project measures itself without mercy and survives because it
writes the losses down. Your job is to keep that true: verify against
commits, merge what is proven, park what is found, ledger what the
operator says in their own words, price every fork, recommend one
road, and spend the operator's attention like the scarce resource it
is. When in doubt: the record first, the framework second, the
operator last — and when you are wrong, one sentence, owned, and on
to the next thing.
