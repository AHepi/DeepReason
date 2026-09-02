# Parked — found during the hv-v6-reachability tranche, deliberately not done here

Each entry: one line of WHAT, then a ready-to-send prompt. Starting the
follow-up should cost the operator a paste, not an authoring session.

---

## P1 — the nine other model phases behind the same v6 gate

WHAT: `_defer_untransactional_v6_phase` fences eleven model phases; this tranche
converts only the two `hv` producers and writes the recipe as a `REC-` map
document. Nine remain structurally unreachable on every v6 run.

```
EXECUTOR WINDOW — DEFECT TRANCHE: convert <PHASE> to v6 transactional dispatch
=============================================================================
Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal. Commit and push at every phase
boundary on your assigned branch.

THE DEFECT: <PHASE> is one of the eleven model phases fenced behind
src/deepreason/scheduler/scheduler.py::_defer_untransactional_v6_phase, whose
whole decision was "schema_version == 6 -> defer" until
experiments/2026-09-02-defect-hv-v6-reachability/ made the gate consult the
route-seat behavioural capability plan. That tranche converted the two hv
producers only and left the recipe behind; this tranche applies it to <PHASE>.

THE RECIPE ALREADY EXISTS AND IS THE AUTHORITY: docs/map/REC-give-a-legacy-
phase-v6-transactional-dispatch.md. Follow it literally. Its steps are: add the
phase's row to the declared VERSIONED grant-id-to-phase table; route the phase's
provider call through the shared v6 transactional helper; add the soak case with
and without the grant; prove RED-then-GREEN; add the row's architecture-test
coverage; move the map in the same commit.

GOAL (for dr-set-goal to bound — ONE phase, not several): on a v6 run whose
<ROLE> seat holds <GRANT-ID>, <PHASE> dispatches through the v6 transactional
call and records its own typed output; with no grant it defers exactly as today
with the existing typed notice. Falsifiable offline: the cycle soak on the
grant-bearing shape produces >=1 <OUTPUT-EVENT> within 8 cycles (RED today,
GREEN after); the no-grant soak stays at 0 with the notice present, GREEN both
sides; mutation proofs committed.

OUT OF SCOPE: the other eight phases; the hv work already delivered; the
coverage/countercondition sort in capture/programs.py.

STOP AND ASK: any frozen-surface contact; any NEW contract id or work kind
(that is verification/, surface 3 — priced stop, grant requested in FIX.md
BEFORE code); any change that alters acceptance/refutation on a fixed stub.

VALIDATION: full gate 0 failed; python tools/docs_verify.py (full, not --fast)
in the same commit as the code.
```

The nine, with the phase-name string each passes to the gate (to be confirmed
from the call-site census in this tranche's DIAGNOSIS.md before the prompt is
sent — substitute it for `<PHASE>` above):
premise-demarcation-variation, premise-rent, paraphrase-audit-variation,
experiment-generator-authoring, rubric-trial, property-design,
property-relevance-trial, paraphrase-audit-judgment, pairwise-discrimination,
vision-criticism.

---

## P2 — coverage charges an artifact for every countercondition it declares

WHAT: with `hv` absent and `reach` empirically zero, the Pareto frontier sorts on
coverage alone, and coverage penalises an artifact for each countercondition it
declares — so 93% of P-A1's frontier and all of P-S1's were harness-minted
problems rather than the operator's seed question. This tranche gives the sort a
second axis; it does not touch the sort itself.

```
EXECUTOR WINDOW — DEFECT TRANCHE: the Pareto frontier sort charges an artifact
for declaring counterconditions
==============================================================================
Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal. Commit and push at every phase
boundary on your assigned branch.

THE DEFECT, FROM THE RECORD: on P-A1 (run 4565139800f5ca02) 93% of the Pareto
frontier, and on P-S1 (9e48a36b1dec91ee) all of it, was harness-minted problems
rather than the operator's seed question. The measured mechanism: coverage
charges an artifact for every countercondition it declares, so an artifact that
states its own defeaters ranks BELOW one that states none. The write-up is
branch claude/live-reasoning-p-a1-bv65kl,
experiments/2026-09-01-live-all-modules-p-a1/FINDINGS.md and RESULTS.md
segment 3 (read-only). The suspected site is src/deepreason/capture/programs.py.

WHY IT IS SEPARATE FROM THE hv TRANCHE: hv being unmeasurable removed the
frontier's second axis (fixed by
experiments/2026-09-02-defect-hv-v6-reachability/). That fix restores an axis;
it does not change how coverage scores an artifact. This defect is the scoring
rule itself and survives the hv fix.

WHY IT MATTERS BEYOND RANKING: CLAUDE.md's standing invariant is that the
operator's seed question always wins scheduler rank ties. A sort that
systematically ranks harness-minted problems above the seed is that invariant
losing by a different road.

GOAL (for dr-set-goal to bound): state the intended coverage semantics from the
spec series FIRST (docs/harness-spec-*.md and every amendment), then decide by
the record whether declaring a countercondition ought to reduce coverage.
Falsifiable offline: a fixture with two artifacts identical except that one
declares N counterconditions ranks them <as the spec says>, RED today if the
spec disagrees with the code.

STOP AND ASK BEFORE IMPLEMENTING: if the spec is SILENT on whether
counterconditions reduce coverage, that is a question for the operator, not an
inference. Load dr-ask-the-right-question and stop with the fork priced.

OUT OF SCOPE: hv and reach (hv fixed separately; reach's zeros are empirical);
the eleven gated phases.

VALIDATION: full gate 0 failed; docs_verify full mode in the same commit.
```

---

## P3 — `reach` is deterministic, ungated, and empirically zero

WHAT: `reach_set` is empty on the same roots as `hv_set`, but for a different
reason — `reach` is not behind the v6 gate at all, so its zeros are an empirical
fact about the runs rather than a structural lockout. Explicitly noted and NOT
touched by this tranche, per the operator's instruction.

```
EXECUTOR WINDOW — DIAGNOSTIC TRANCHE (may end at DIAGNOSIS.md): why is `reach`
zero on every committed v6 root?
==============================================================================
Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal.

THE OBSERVATION, FROM THE RECORD: experiments/2026-08-25-poietics-program/run
carries 5414 log events with zero non-empty state_diff.reach_set, alongside zero
non-empty hv_set. The hv zeros had a structural cause (the v6 dispatch gate,
fixed in experiments/2026-09-02-defect-hv-v6-reachability/). reach is NOT behind
that gate: reach_sweep is imported directly at scheduler.py:43 and dispatches
without a transaction. So reach's zeros are empirical, and the question is what
the runs actually did — a diagnosis, possibly with no defect behind it.

GOAL: establish from the record alone whether reach_sweep was ever CALLED on
these roots, and if it was, why every result was empty. A "nothing is broken"
verdict recorded in DIAGNOSIS.md is a complete and successful outcome for this
tranche — do not manufacture a fix.

OUT OF SCOPE: hv (fixed); the frontier sort; the eleven gated phases.
```

---

## P4 — the deferral marker is a signal emitted through a variable, so the registry cannot see it

WHAT: `v6-model-phase-deferred.v1` is bound to a local `marker` variable before
`record_measure` (`scheduler/scheduler.py:724`), and `tests/test_signals.py`
AST-scans only *literal* first arguments — so the one signal that stands in for
an absent transaction is neither scanned nor registered, while
`verification/report.py` reads it back. Already recorded in
`docs/map/SEAM-scheduler-x-workflow.md` Traps ("observed on 08dcdf3c ... not
fixed there or here"), re-confirmed still true this tranche. Independent of the
hv goal in both directions, so not folded in.

```
EXECUTOR WINDOW — DEFECT TRANCHE: a signal emitted through a variable is
invisible to the signal registry
=========================================================================
Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal. Commit and push at every phase
boundary on your assigned branch.

THE DEFECT: `docs/map/SEAM-scheduler-x-workflow.md`'s Traps records it and the
code still does it — `scheduler/scheduler.py:724` binds the signal name
`v6-model-phase-deferred.v1` to a local variable before passing it to
`record_measure`, and `tests/test_signals.py` scans only literal first
arguments, so `is_known("v6-model-phase-deferred.v1")` is False while
`verification/report.py` reads the marker back. The debt is visible in reports
and invisible to the registry. The trap states the generalisation: ANY signal
emitted through a variable has the same hole.

THE LAW: the signal registry is a CONTRACT (2026-08-14, operator verbatim) --
"a signal is anything declaring name, unit, producer-agnostic semantics, and a
staleness bound; new setups add signals by declaration through this typed
channel". A signal the registry cannot see has not been declared.

GOAL (for dr-set-goal to bound): make the census that decides registry
membership see signals emitted through a variable, so
is_known("v6-model-phase-deferred.v1") is True and the marker carries a
declaration. Falsifiable offline: a test that goes RED on the current tree
because the marker is unregistered, GREEN after; plus a scan-level test that
goes RED if a NEW variable-emitted signal is added without declaration -- the
class, not the instance, is the deliverable.

READ FIRST: docs/map/INV-signal-contract.md (the three layers: FROZEN change
protocol, VERSIONED registry and policy, FREE parameters) and
docs/map/REC-add-signal.md. Follow the recipe rather than improvising.

OUT OF SCOPE: the v6 dispatch gate itself (fixed by
experiments/2026-09-02-defect-hv-v6-reachability/); any change to what the
marker MEANS or when it fires.

VALIDATION: full gate 0 failed; docs_verify full mode in the same commit; the
SEAM-scheduler-x-workflow Traps entry rewritten to say when it was fixed, never
deleted.
```
