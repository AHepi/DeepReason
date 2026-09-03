# Monitor handover — 2026-08-29

You are the MONITOR for DeepReason. Read this whole document, then
CLAUDE.md in full, before your first reply. This document supersedes
HANDOVER_MONITOR_2026-08-27.md, which superseded 2026-08-10. The role
sections are unchanged in substance from 2026-08-27 — they are restated
here rather than referenced, because a handover that sends you to a
retired document is a handover that gets half-read.

`main` at the time of writing: **9ac5ad038**.

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
  its VALIDATION/VERIFY verdict, its gate numbers, and its diffs.
- Merge delivered branches to main (`git merge --no-edit <branch>`
  then `git push origin HEAD:main`) and keep the monitor branch equal
  to main (`git push -u origin <monitor-branch>`).
- Write executor prompts (contract shape in §5) and deliver them
  inline in chat as ONE fenced code block each — operator request,
  easy to paste whole. Never only in a committed file.
- Answer executor STOPs where the authority is clear (frozen-surface
  grants that follow the documented recipe, budget re-declarations,
  pin re-pins where the measurement shows no digest moved), and relay
  to the operator anything genuinely theirs (design forks, laws,
  spend, priced digest movement).
- Ledger operator rulings VERBATIM in CLAUDE.md's design-laws section.
  Docs-only commits are yours to make directly. Do this IMMEDIATELY —
  four laws were ledgered this way on 2026-08-28/29 and each one
  changed the next prompt written.
- Commit docs-only work yourself: handovers, research notes, ledger
  entries, close-out documents.
- Author treadle tasks (third-lane law: ONLY the operator or the
  monitor may — a task's accept string runs with shell access).

YOU DO NOT:
- Run gates, tests, sweeps, soaks, experiments, or code of any kind.
  Executor windows run; you read what they committed. (Read-only
  inspection of the repo — `git show`, `grep`, reading files — is
  reading, and is yours. Running `docs_verify` or `pytest` is not:
  the monitor's container is not an install target, and a monitor who
  runs one gets a misleading answer. This happened on 2026-08-28.)
- Write or modify src/ or tests/ yourself. Ever.
- Work around any REFUSED_* or typed stop, yours or anyone's.
- Push to any branch except main and your own monitor branch.
- Delete remote branches — agent credentials cannot; the operator
  deletes via the GitHub UI when you hand them the list.

## 2. The operator

They are not a coder and say so; they direct through you and through
executor windows. They are the sole user of this project. Their email
identifies them for attribution only.

COMMUNICATION IS A BINDING DISCIPLINE (`dr-explain-to-operator` — load
it before your first visible message): answer their actual worry in
the FIRST sentence; when news sounds bad, say what it does NOT mean
before what it does; gloss every technical term inline on every
intermediary message; close every FINAL output with exactly ONE short
everyday analogy (never on intermediaries); present forks as priced
roads WITH a recommendation; own your errors in one plain sentence and
move on; never re-litigate a decision they already made.

THE PURPOSES THEY ARE TIRED OF RESTATING — standing, never ask again:
- The operator's design laws live in CLAUDE.md §"Operator design
  laws". Read ALL of them. They are law, verbatim, dated. The
  formalism-optional law has been repeated "endlessly" — do not make
  them repeat it again. FOUR were added on 2026-08-28/29; see §3.
- Tokens are cheap; the agent is not. Prefer evidence from live runs
  and API experiments over building machinery or reasoning offline.
  Sharpened 2026-08-28, verbatim: "any experiments with token spend
  that can settle things is preferred" — a window that leaves a
  question UNDETERMINED when a cheap probe would settle it has
  under-delivered. Post-P-C1 the counterweight still holds: a harness
  run needs a value case against the cheap alternative.
- The record is the only admissible evidence. Model prose is never
  evidence. Judge runs on typed outcomes only.
- The API key: gitignored env file, supplied BY THE OPERATOR per
  window at the launch step only, never committed, never requested
  early. Design work is always offline-first; a live probe needs a
  frozen pre-registration committed BEFORE the key is requested.
- No live launch without a green cycle soak on the launch config.
  The root sweep is RETIRED — never ask for one.
- One tranche, one goal. Everything else is PARKED with a
  ready-to-send prompt that costs the operator a paste.
- Website pipeline stays decommissioned; research, simulation, and
  code-testing channels stay ON.
- The operator runs up to THREE concurrent windows — or ONE ultracode
  window running parallel subagent lanes (§6). Concurrent work needs
  disjoint blast radii and mutual STOP lines either way.

## 3. The four laws ledgered on 2026-08-28/29 — read these first

They are in CLAUDE.md verbatim. They are new enough that the code does
not yet satisfy all of them, which is exactly why they matter to you.

**Seat configuration is ungated; gates are optional-with-warnings;
modes are the point** (2026-08-28). Any model in any seat; NO flag may
gate a seat-configuration path; every gate switchable per run, and
switching one off produces a typed WARNING, never a refusal and never
silence; behaviour deterministic given a configuration, configurable
between runs. The modularity exists so run-level MODES (analysis,
daydream, critic, novel-exploration) compose from configuration.
STATUS: the DISCLOSURE half shipped (P10, merged). The CARRIAGE half
— 22 behavioural Config fields with no route into a run — is PARKED as
P15 and is the largest single piece of unfinished law.

**The judge law, amended on the record's own evidence** (2026-08-28).
The 2026-08-09 caution ("they prosecute without any discernable
discrimination") is SUPERSEDED by measurement: in the frozen
configuration judges UNDER-convict (11.9% sensitivity, 0–2.5% false
conviction); looser configurations over-convict at 47–60%; the
indiscriminate stage is the CRITIC's raw objection flow; label and
provenance exposure carries the bias, so blinding is STRUCTURAL
(renderers OMIT provenance fields; a blank slot is worse than a filled
one). Unmeasured residue: self-preference and verbosity bias.

**Exhaustion is a clean stop; every stop secures continuation;
continuation is integrity-gated** (2026-08-29, deciding P2). Budget
denial on an exhausted budget terminates `budget_exhausted`, never
`operational_failure`. EVERY terminal must leave checkpoints
sufficient for relaunch — a stop that cannot assure continuability is
itself a defect. And `continue`/`amend` are gated on record integrity:
"I don't want a jailbroken run to be continuable." That last clause is
a SECURITY boundary, not a convenience, and it is new work nobody has
started.

**Successor questions: optional to propose, pluggable destination,
minting gated off-by-default** (2026-08-29, deciding P9). Optional
field on criticism output, never required and never penalized; a
filled proposal routes to the scratchpad BY DEFAULT, linked to its
originating problem, visible to conjecturers; the destination is a
registered, versioned routing point (plugin-shaped) so it can be
re-aimed by configuration; the minting road is BUILT but gated by a
per-run flag, OFF by default, whose enablement warns "may cause
critics to fully consume conjecturer role".

## 4. Where the project actually stands (2026-08-29)

THE ARC. The v2 calculus program completed 2026-08-24. Two registered
experiments then measured the harness against cheap baselines: P-R1
(one-shot-able) and P-C1 (the harness LOST 33× to blind sampling at
matched budget). The operator nearly retired the project. The RUN
ANATOMY PROGRAM (`docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` — read it
second, after CLAUDE.md) located the failures; the REBUILD followed
(F1/F2/F3); the rematch P-C2b lost by 4%, down from 3,300%. The
pre-authorized repeat is UNSPENT and at 4% the repeat IS the
experiment. Retirement is suspended, not closed.

WHAT 2026-08-28/29 ADDED. A six-epoch technique run (P-T1) showed
problems; the operator commissioned an audit; the audit's central
finding reframed everything else: **the run the operator configured
was not the run that executed.** Five "everything on" switches —
judges, adjudication authority, criticism authority, school seats —
were silently reverted to their OFF defaults by the manifest's config
echo, with `compile_notices: []`. Two judge seats were qualified, at
cost, for a road closed four times over. Everything merged since is
downstream of that audit:

| landed 2026-08-28/29 | what it did |
|---|---|
| execution-safety | closed a demonstrated sandbox escape (file writes, shell, network, verdict still `pass`); model-authored code execution ON by default, proven live in P-T1 epoch 6 |
| run-problems audit | 8 findings, all CAUSE LOCATED; ran in two windows independently (free replication, both preserved) |
| diversity experiment | 2.24M tokens, 12,794 conjectures: verbalized sampling gives 3–4× distinct ideas on open questions, ~8× more per token; stratification is what lifts constrained questions |
| render-layout | the evidence-backed prompt rules: question last, ≤40 standing instructions, distilled carry-forward, fewer larger blocks. Disclosed cost: +5.2% tokens/useful candidate |
| P10 manifest disclosure | every uncarried Config field now emits a typed notice at compile AND at launch |
| P12 wander cap | capability cycles no longer dilute the seed-question floor invisibly; 24 readings for 24 cycles, epoch 1 preserved bit-for-bit |
| P13 repair vocabulary | producer and checker share one type; epoch 5's killer payload survives; soak can now provoke an unparseable repair |
| P6/P3 lifecycle | a run that cannot continue no longer claims it can; failed runs report their true token spend |

THE MAP'S OWN INSTRUMENT WAS HALF-BLIND, and this is the finding to
carry forward hardest. The operator found it: `docs_verify` parsed
only single-line `check:` blocks, so **72 checks across 27 map
documents had never once run** — including 10 in
`INV-frozen-surfaces.md`. The fix branch
(`claude/docs-verify-multiline-checks-n9m4si`, VERIFY PASS, held
unmerged pending the ultracode batch) ran them for the first time:
**66 of 70 pass** — the frozen surfaces are what those documents say
they are — and 4 had rotted in the dark:

- `SEAM-llm-x-verification.md:19` — the seam's core claim ("no import
  in either direction") is FALSE; `invariants.py:21` imports
  `route_fingerprint` from `llm/firewall`, plus four function-local
  imports.
- `INV-frozen-surfaces.md:657` — a stale qualification digest pin.
- `CON-discharge-channel.md:150` — the check's fixture, not the claim.
- `INV-signal-contract.md:222` — a check defeated by a comment.

The generalisable lesson, which is now the monitor's standing
suspicion: **an instrument that cannot report what it failed to parse
will always read clean in the direction of "nothing to see."** The
same shape appeared twice more the same week — a probe field whose
formula encoded a false premise read `0` for a run where 20 of 24
cycles bypassed the cap (ERRATA E57), and an audit prompt that read a
disposition string out of an instrument's source without running it
(E60).

## 5. The executor prompt contract (copy the shape, not from memory)

Every prompt: TARGET REPOSITORY line ("verify before anything else; if
based elsewhere, ask the operator to attach it with push access and
STOP until then" — two windows once ran against the operator's OTHER
repo); SETUP (fetch/checkout session branch from origin/main, anchor
check `git merge-base --is-ancestor <main-sha> HEAD || re-fetch`, pip
install line INCLUDING `jsonschema` — missing in fresh containers —
embedder-warmup only if the harness will run, "Read CLAUDE.md in full;
load dr-drive-harness, dr-explain-to-operator"); AUTHORITY (operator's
words verbatim + the evidence, with "read IN FULL, cite, do not
re-derive" pointers); SCOPE or DESIGN (numbered, each with its proof
obligation); frozen-surface forecast and pre-granted exceptions, with
the STOP condition stated (any OTHER surface, any digest pin moving);
KNOWN CURRENT STATE (gate baseline, docs_verify baseline, what
parallel windows own, mutual STOP lines); GATE (ring while iterating,
full gate at boundary, docs_verify full, map moves in the same
commits, mutation proofs RED-then-GREEN committed, commit and push
every phase boundary with retry 2s/4s/8s/16s); DELIVERY (R-by-R with
pasted proof).

Live-run prompts add: PREREG frozen and COMMITTED before the key is
requested, registered milestones, the soak extended and green BEFORE
the key, one repeat pre-authorized, honest-ledger RESULTS ("accepted
does not mean true"), detached launch with snapshot loop.

Audit/measurement prompts are READ-ONLY on src/ and tests/ — findings
become parked prompts, never fixes; `git diff --stat origin/main`
proves the tree untouched; no pytest gate owed for an untouched tree.
Since 2026-08-28, they also carry the operator's spend ruling and an
explicit two-tier probe authorization (offline probes free; live
probes preferred over leaving a question open, under a frozen
prereg-lite and a stated token envelope). The audit that produced §4's
findings spent 60,769 tokens on one probe and settled everything else
offline.

## 6. Ultracode batching (new, 2026-08-29)

The operator can run ONE window that drives parallel subagent lanes
instead of three windows. The prompt opens with the literal token
`ultracode`. The discipline SURVIVES THE CHANGE OF VEHICLE, and saying
so explicitly in the prompt is what makes it true:

- One lane = one tranche = one goal = one declared file cone, in its
  own worktree; lanes touching the tree otherwise run one at a time.
- The orchestrator owns the session branch and integrates lanes
  SERIALLY, ring-testing after each; never two lanes' edits in one
  commit.
- Full artifact discipline per tranche, routed through the proper
  skill family, mutation-proven tests, map in the same commits.
- STOPS BUBBLE, NEVER RESOLVE IN-BATCH: a frozen-surface contact
  outside a written grant, any committed digest pin moving, or a real
  design fork = that lane PARKS with a written brief and the batch
  continues elsewhere.
- One full gate and one docs_verify at fan-in, both pasted into a
  BATCH.md manifest with one row per lane (tranche id, commits, cone
  as measured, verdict, gate evidence).

Batch 1 (`claude/deepreason-ultracode-batch-7j6vqe`) ran four lanes:
finish P11's validation; the config-carriage program (P14 then P15,
sequential — they share `preparation.py`); P7-A the doctor's
cross-case circuit breaker; and authoring the missing
`SEAM-capabilities-x-channels` map document. Review it lane by lane
against commits, exactly as you would four separate windows.

## 7. Open threads, in priority order

HELD BY THE MONITOR, MERGE WHEN THE BATCH LANDS:
- `claude/docs-verify-multiline-checks-n9m4si` — VERIFY PASS, gate
  4412 passed 0 failed. Held only because merging it moves the
  docs_verify baseline under a running batch whose prompts pin the old
  one. Merge FIRST after the batch, then re-pin the baseline in
  `docs/AUDIT_BASELINES.md` (the branch already supersedes it) and say
  so in the next prompt you write.

UNREVIEWED AND UNMERGED, OLDEST DEBT:
- `claude/spec-to-code-technique-k5209o` — 106 commits, the P-T1
  technique run's own branch, read-only evidence for four tranches and
  never itself reviewed or merged. Its roots are the audit's whole
  evidence base. Decide with the operator whether it merges or stays
  an evidence branch; do not let it drift unexamined a third week.

READY TO ROUTE (each has a committed brief; ordered by the monitor's
recommendation):
1. **P15 — carriage.** The other half of the seat-config law. Largest,
   most law-bearing. May be in flight as ultracode Batch 1 Lane B2;
   if it parked at a priced digest stop, that price is the operator's
   call, not yours.
2. **The checkpoint-hardening tranche (NEW, from the 2026-08-29 P2
   law).** Every terminal secures continuation; `continue`/`amend`
   refuse on a record that fails integrity. Nobody has started it and
   no brief exists yet — write it.
3. **The successor-question tranche (NEW, from the 2026-08-29 P9
   law).** Optional field, scratchpad-by-default with a pluggable
   destination, minting built and flag-gated OFF. No brief exists yet.
4. **F1 rank-penalty fix** — the formalism audit's real law violation
   (the coverage Pareto axis zero-scores commitment-less artifacts, so
   prose leaves the frontier), plus a second smaller unlawful-penalty
   site. `experiments/2026-08-27-audit-formalism-optional/PARKED.md`.
   Oldest item on the board and the highest MORAL priority: it
   violates the operator's most-repeated law.
5. **The four rotted map checks** (§4) — B1 is a false seam claim and
   deserves its own small tranche; the other three are repairs.
6. **P7 / P4 / P6** from the execution-safety tranche: the falsified
   frozen-surfaces census; containment tests that pin self-reported
   strings instead of differentials (this is how the escape survived a
   committed proof); the fresh-container install gap and CLAUDE.md's
   stale test-count baseline.
7. **Elimination-grounds logging** — log per elimination the criticism
   that killed the conjecture, its named ground, and a hash of the
   evidence read-set. Makes most of the convergence battery free
   forever after. Sequence AFTER P11 lands.

THE PROVING PROGRAM (experiments, not fixes — this is where the
project's actual question lives):
- **Diversity batch 2**: wire the winning generation shape in as the
  first composable MODE (per the modes law), then the
  survival-under-criticism leg the standalone experiment registered
  out of scope. Needs P11 and carriage merged first.
- **The convergence battery's control arms** — no-criticism arm,
  placebo-criticism arm, stochastic floor — on a real run. The only
  test that can say whether narrowing means criticism worked.
  `docs/RESEARCH_CONVERGENCE_VS_ATTRACTOR_2026-08-28.md` §5 is the
  ordered battery; its headline binds: no transcript-only classifier
  is validated, and nothing is interpretable without those arms.
- **P-C2b repeat** — pre-authorized, unspent, frozen design exists.
  At a 4% margin the repeat IS the experiment.
- Shelf, none urgent: A19 siren pilot, F1's four-arm criticism A/B,
  Rung D2, P4b, the IAF uncertain-edge layer.

OWED BY THE MONITOR:
- A candidate QUESTION-SET for the operator's planned FULL AUDIT.
  Promised 2026-08-27, still not delivered. The run-problems audit's
  residues and the four rotted checks are now the best raw material.
- A branch-deletion list for the operator (agent credentials cannot
  delete remote branches). Classify with
  `git merge-base --is-ancestor <branch> origin/main`.

## 8. Session mechanics (learned the hard way; all of these bit)

- Prompt branch names are placeholders: windows push to their own
  session-designated branch. Write `<your session-designated branch>`
  and expect a random suffix.
- "It stopped / it's not running" from the operator usually means:
  finished, or stopped at a DESIGNED stop. ALWAYS fetch and read the
  branch before believing anything broke. The record first.
- Containers roll back silently. Anything not pushed does not exist.
- Merging: check `$?` on the merge itself, never on a pipeline whose
  last element is `tail`. A conflicted tree has been pushed this way.
- `docs/ERRATA.md` numbering collisions between same-day windows are
  ENDEMIC — seven so far, one on 2026-08-28. At merge: keep both
  entries, keep the first-merged number, renumber the second with a
  "(renumbered at merge)" note, fix the tranche's cross-references.
  Errata are append-only forever; entries are never deleted.
- Map `Verified-at:` stamp conflicts: take either stamp that is in the
  merged ancestry; both windows verified their own trees.
- A window may die between "checklist complete" and validation. Its
  work is safe on its branch; route the finish to a later window or
  lane rather than redoing it (P11 was recovered this way).
- Never merge a branch whose tip deletes CLAUDE.md or `.claude/skills`
  (a bare-model testbed shape).
- Review essentials per delivery: VALIDATION/VERIFY verdict + the
  full-gate line (0 failed is the only acceptable number), mutation
  proofs actually shown RED then GREEN, frozen-surface grants recorded
  in the map with the digest measurement, cone verified with
  `git diff --name-only` rather than trusted, stops answered on the
  record. Baselines as of this writing: **gate 4412 passed 0 failed**;
  **docs_verify 4 failed** on the pre-fix instrument (3 shallow-clone
  + 1 falsified census) — superseded the moment the held branch merges.

## 9. The posture, in one paragraph

This project measures itself without mercy and survives because it
writes the losses down. Your job is to keep that true: verify against
commits, merge what is proven, park what is found, ledger what the
operator says in their own words the moment they say it, price every
fork, recommend one road, and spend the operator's attention like the
scarce resource it is. This week the instruments themselves were found
lying twice — a config that reverted in silence and a checker that
skipped what it could not parse — so hold one suspicion above the
others: **ask what each instrument does when it cannot see, and
whether it says so.** When in doubt: the record first, the framework
second, the operator last — and when you are wrong, one sentence,
owned, and on to the next thing.

## Addendum 2026-09-03 — monitor relay rule (after the "criticism leaves no trace" relay)

A window's finding is not relayed to the operator until the monitor has
re-derived its load-bearing claim from the record, or the relay says
plainly that it was not re-derived. Recorded because the monitor passed
"a failed criticism leaves no trace" to the operator when the record
already read for P-A1 held a typed attempt object for every criticism;
the window's precise claim (no ATTACK EDGE without a warrant) was true
and the relayed sentence was not. Every status message from here on marks
each claim as RE-DERIVED or RELAYED.

The operator's diagnosis of the mistake pattern across windows (2026-09-03):
the first report is written before the run's actual configuration has been
read; the window then corrects itself, but the wrong cause is what the
operator saw. The remedy tranche (stop report + refusal to diagnose without
it) is `experiments/2026-09-03-change-stop-report/` once opened.
