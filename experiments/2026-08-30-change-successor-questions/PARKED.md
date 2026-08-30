# Parked — successor questions (lane B, ultracode batch 2)

Parked at the SPEC boundary, 2026-08-30, before any implementation code exists.
Five entries. Four are operator DECISIONS that block or shape work already
specified (`SPEC.md` §Questions for operator); one is a genuine future tranche.

A STOP is a phase boundary: this file and the two artifacts beside it were
committed and pushed at the moment the parks were made, not when the answers
arrive (`experiments/2026-08-29-ultracode-batch-2/SETUP.md`, and batch 1's
recorded loss).

---

## P9B-1 .. P9B-5 — the operator decision block

WHAT: five questions the implementer may not decide. Q1 and Q5 BLOCK spec items
outright (S14, S15, S19, S24); Q3 makes S9 and S13 provisional; Q2 and Q4 change
what gets built, not whether. Full reasoning, both roads and a recommendation
for each are in `SPEC.md`; the block below is the shortest answerable form.

```
DeepReason — successor questions (P9 law, 2026-08-29). SPEC.md is committed on
branch claude/b2-lane-B at experiments/2026-08-30-change-successor-questions/.
No implementation code exists yet. Five decisions, each answerable in a word:

Q1 FROZEN SURFACE 4 — GRANT? Two new Config fields need two unconditional
   four-space data.pop lines in run_manifest.py::_versioned_source_config_data
   (insertions only, 25 -> 27, nothing else in the file). Without them the
   qualification subject digest moves and ~40 tests go red. You have called this
   line "the documented recipe"; this is the written request the discipline
   requires. GRANT / REFUSE.

Q2 WHERE THE WARNING IS PRINTED. Enabling the minting flag must emit your words
   "may cause critics to fully consume conjecturer role".
   Road A: on the compile-notice stream the CLI already prints to stderr —
           costs ONE MORE LINE inside run_manifest.py (a second frozen contact).
   Road B: declared on the destination registry (outside run_manifest.py) and
           recorded on the run's own append-only record — zero extra frozen
           contact, but today's CLI does not print it.
   Recommended: B, plus A only if you widen Q1's grant by that one line. A / B / BOTH.

Q3 MAY CRITICISM WRITE TO THE WORKSHOP? SEAM-rules-x-scratch says "Never widen
   the criticism side to close the asymmetry ... Overturning it is an operator's
   call". Your P9 law is that call, but it does not say which half survives.
   Road A: rules/crit.py dispatches the route directly (~20 lines, matches the
           shipped premise-channel precedent, but is a workaround of that rule's
           letter and needs this lane's cone widened).
   Road B: a reader OUTSIDE rules/ walks what the criticism already recorded and
           routes it; crit.py takes a zero-line diff, the asymmetry survives
           as written (~60 lines, more failure modes).
   Recommended: B. A / B.

Q4 HOW STRONG IS "never outrank the seed"? A minted successor loses a rank TIE
   to your seed question by construction, in both selection modes, today, with
   no code change. It can still out-AGE a seed that has already been worked,
   because the age term precedes the seed term.
   Recommended: take the tie guarantee now; park strict domination as its own
   tranche against a pinned scheduler socket. TIE / STRICT.

Q5 CONFIRM THIS SUPERSESSION SENTENCE (it rewrites a tripwire founded on your
   2026-08-15 ruling): "The P9 law of 2026-08-29 supersedes the 2026-08-15
   decommissioning ruling FOR THE SUCCESSOR TRIGGER ALONE — one producer,
   outside rules/, gated by a per-run flag defaulting OFF — while the website
   development pipeline itself stays decommissioned." CONFIRM / AMEND.
```

---

## P9B-6 — strict domination of the seed question over minted problems

WHAT: `Scheduler._select_problem`'s rank key gives the seed question the
tie-break but not strict priority; a freshly minted problem that has never been
worked can outrank a seed that has. This tranche proves the tie half (S18) and
does not touch the scheduler. Only becomes work if Q4 answers STRICT.

Ready-to-send prompt for its future runner:

```
Route: deepreason-orchestrator (class: regression-risk — proposal only, stop
after FIX.md unless the operator says otherwise).

One goal: decide, and if the operator wants it, implement, whether the
operator's SEED question should STRICTLY dominate every spawned or minted
problem in Scheduler._select_problem, rather than only winning rank TIES.

Evidence pointers, all committed:
- src/deepreason/scheduler/scheduler.py, the LIVENESS_QUEUE rank tuple: first
  term is -(age * weight), second is `p.provenance.trigger != SpawnTrigger.SEED`.
  A never-worked problem is maximally aged, so the seed term never decides.
- The round-robin pool's key puts the seed term FIRST, so the two modes do not
  hold the same guarantee in the same strength.
- docs/map/CON-scheduler-ranking.md pins the promise with a two-occurrence grep;
  tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero
  is the regression. Both must stay green or move deliberately.
- The existing mitigation is the wander cap — a CANDIDACY gate under
  Config.SEED_PROBLEM_BUDGET_FLOOR, not a rank term (F3, 2026-08-26).
- The motivating history: selfstudy run-9175f0ec spent a whole 200k-call budget
  inside a connection problem that won cycle 0, while the operator's own
  question terminated budget_denied having made zero provider calls.
- experiments/2026-08-30-change-successor-questions/SPEC.md Q4 states both
  readings and why this was not decided in that tranche.

End state: FIX.md naming which of the two sort keys changes, what the new term
is, which of the two map checks and which regression must be re-derived, and a
measurement showing the change does not starve non-seed problems entirely.
```
