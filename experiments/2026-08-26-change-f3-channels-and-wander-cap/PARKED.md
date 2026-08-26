<!-- DR-TRANCHE-F3 -->
# Parked — found in this tranche, deliberately not done here

The cross-routing rule: a defect found mid-change is PARKED, not fixed; a change
wished for mid-defect is PARKED, not implemented. Each entry is written for its
future runner at park time — one line of WHAT, then a ready-to-send prompt.

---

## P1 — the code-testing channel has no off-switch

**What.** `channels.CHANNEL_DECLARATIONS["code-testing"]` declares
`enforcement="unconditional"`: the channel is on, always, and no configuration
turns it off. Research and simulation both have real toggles. R4's "turning one
OFF remains a lawful configuration" is therefore delivered for two of three.

**Why it was parked and not improvised.** The channel's only live entry points
are the commitment compilers in `workloads/text.py::draft_countercondition_commitments`
and `informal/skeleton.py::forbidden_commitment`, whose commitment ids are
CONTENT-ADDRESSED digests over the compiled shape. Gating there would change
what a record CONTAINS rather than what a run may reach for — evidence-side
surgery, which the tranche instruction excluded in its own words ("this is
config defaults, not path surgery"). The two constructors that look like the
obvious gate (`oracle.exec_oracle_commitment`, `candidate_checker_commitment`)
have NO production call site at all, so gating them would gate nothing a live
run reaches (SPEC.md M3, and `tools/blast_radius.py`'s own "2 declared
symbol(s) already have no live call path today").

**Prompt, ready to send:**

```
Change tranche: give the code-testing evidence channel a real off-switch.
Route through dr-change-orchestrator.

AUTHORITY: operator 2026-08-14, "Code testing, simulation, scratch pad and
research backends need to stay live"; and the all-configurations law — every
channel's OFF state must be a lawful configuration. F3 delivered toggles for
research and simulation and PARKED this one
(experiments/2026-08-26-change-f3-channels-and-wander-cap/PARKED.md P1).

START FROM: docs/map/INV-evidence-channels.md — the registry, the row that
reads enforcement="unconditional", and the trap that says why. Then
DR-SEAM-evaluation-x-ontology and DR-SUB-evaluation.

THE PROBLEM, stated: the channel's live entry points are
workloads/text.py::draft_countercondition_commitments and
informal/skeleton.py::forbidden_commitment. Their commitment ids are
content-addressed digests over {case, eval, observation_valued, checker_spec},
so refusing to compile one changes what the record contains. The operator's
own law says seats change how content is GENERATED, never what counts as
EVIDENCE — so design the switch on the GENERATION side (the harness stops
OFFERING an executable commitment) and prove that an already-recorded
commitment still evaluates byte-identically on replay.

GATE PROVES: with the channel on, every committed root's verdicts are
unchanged (a targeted regression on a fixture, not a sweep); with it off, no
executable commitment is compiled and the run still reaches its typed
terminal; the channel registry's `enforcement` row stops saying
"unconditional" and its map check moves with the code.

BLAST RADIUS WARNING, measured: 33 test assertions across eleven files name
property_oracle_commitment alone. Read SPEC.md's blast-radius census in the F3
tranche before scoping.
```

---

## P2 — `_completion_cap`'s repair of the 47 has no live instance yet

**What.** Phase A wired the allocation controller's decisions to the dispatch
envelope, and the regression proves it offline. No LIVE run has yet recorded a
controller decision reaching a provider call, so the fix is proven but not
witnessed — the same status W5 gave the E43 lease ceiling ("proven offline,
never fired live").

**Why it was parked.** This tranche's gate is offline by instruction (R14–R17).
Live evidence is a separately budgeted question and needs a ladder.

**Prompt, ready to send:**

```
Evidence-generation tranche: witness the allocation controller steering a live
run. Route through deepreason-orchestrator (dr-set-goal first).

AUTHORITY: operator, "Ollama API tokens are cheap, you are not... Creating
evidence from live runs is preferred if it means less work."

WHAT IS ALREADY TRUE, offline: F3 Phase A changed Adapter._completion_cap to
book the seat's SETTLED cap bounded by the route ceiling, and
tests/test_controller_reaches_the_wire.py drives a narrowing series and
asserts every applied knob equals the booked envelope. Before it, W7 measured
47 decisions and 0 reaching the wire across the whole committed population.

WHAT IS NOT: no committed root shows a dispatch whose attempt_trace.max_tokens
is a controller-settled value. W5's census is the instrument — re-run it after
the run and expect the `wire` column to stop reading `no` in all 47.

GATE PROVES: one live ladder run long enough for the controller to settle a
seat (it needs MIN_SAMPLES calls per instance and CLEAN_WINDOWS of spotless
signal); its log carries at least one attempt whose max_tokens equals a policy
artifact's applied knob; verify_root passes on the root. Judge only typed
outcomes.

READ FIRST: docs/map/SEAM-llm-x-scheduler.md, the third-link section and the
trap beneath it.
```

---

## P3 — the wander cap has no live instance either

**What.** The floor holds against an aggressive self-spawner offline, and the
label differential is mutation-proven. No live run has engaged it.

**Why it was parked.** Same reason as P2, and the two share a ladder: a run long
enough to settle a seat is a run long enough to spawn a lineage.

**Prompt, ready to send:**

```
Evidence-generation tranche: witness the wander cap engaging on a live run.
Route through deepreason-orchestrator (dr-set-goal first). Can share a ladder
with P2 above — one long run answers both.

AUTHORITY: W6's post-mortem is the motivating measurement (41.2% of 702 789
tokens on a self-spawned problem about the run's own critic); F3 shipped the
floor as wander.LINEAGE_POLICIES["wander-cap.v1"], default
SEED_PROBLEM_BUDGET_FLOOR=0.5.

GATE PROVES: the run's log carries allocation.seed-lineage-share.v1 readings
every cycle; if the throttle engages it carries exactly one
allocation.wander-throttled.v1 per engagement plus an
allocation.wander-cap.v1 policy artifact; the seeded lineage's share of worked
cycles ends at or above the floor. A run that never engages the throttle is an
INCONCLUSIVE result for the cap, not a negative one — say so, and do not
re-run hunting for an engagement.

WORTH MEASURING WHILE THERE: re-run W6's pc1_postmortem.py cut on the new root
and compare the seed-question share against ARM H's 53.2%.
```

---

## P4 — 79 signals in the registry are still silent

**What.** W5's census found 79 of 111 declared names never emitted in any
committed root. F3 closed the four `allocation.*` phantoms and the tranche's
own two; the rest are untouched.

**Why it was parked.** R13 named the four `allocation.POLICY_SIGNALS` phantoms
and the policy this tranche ships. The other 75 are a different worklist and
several describe paths no committed run has taken, which is not the same defect.

**Prompt, ready to send:**

```
Audit tranche: dispose of the remaining declared-but-silent signals. Route
through dr-audit-orchestrator (the docs-drift dimension), findings only.

START FROM:
experiments/2026-08-26-run-anatomy-program/W5-signals-controller/DECLARED_VS_EMITTED.md,
"Declared but SILENT everywhere (79)". F3 closed six of them
(allocation.seat-truncation/seat-repair/policy-authorized/policy-contested and
the two lineage signals) and left 73-75 depending on how you count the two it
added.

FOR EACH remaining name, decide ONE of three and say which: (a) it has an emit
site and no committed run took that path — leave it, name the path; (b) it has
NO emit site and the consumption is real — that is a phantom, and the F3
precedent is to EMIT at the point the consumer acts on the reading, never to
strike; (c) it has no emit site and no consumer — strike it, with the reason.

ALSO: W5 found the reverse gap, and it is bigger — eight tags emitted 18 151
times that the registry never declared, because tests/test_signals.py scans
only for `record_measure(inputs=[<literal>...])` heads. That is a completeness
hole in the enforcement, not a missing row, and it may be the more valuable
finding.
```
