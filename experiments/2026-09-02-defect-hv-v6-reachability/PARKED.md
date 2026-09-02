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

---

## P5 — the behavioural grant is minted only under a `defended_trial` criticism policy

WHAT: `run_manifest.py:2059-2065` mints the `defender`/`judge`/`variator`
behavioural-contract grants only when
`manifest.criticism_policy.authority == "defended_trial"`. Measured across the
committed corpus: of 50 v6 roots, exactly 4 hold a `variator` grant, and all
four are `defended_trial`; every other root — including all five committed
cycle-soak cases — has `criticism_policy` absent or `observe_only`, so its
`variator[0]` grant list is empty. After
`experiments/2026-09-02-defect-hv-v6-reachability/` makes the gate consult the
grant, `hv` is reachable by configuration, but ONLY through that one policy
shape. Whether that minting condition is itself too narrow is a question about
the minting rule, not about the gate, so it is not this tranche's to answer.

WHY IT MAY BE A DEFECT AND NOT A DESIGN: the operator's solo-run law
(2026-08-09, verbatim: "A solo run with everything on should be an option.
That's what solo run option should always have been. However, turning on judges
at all should be done with caution... I would prefer to do without") says
sole-model operation may never be structurally locked out of any harness
capability. `hv` is a ranking measure with no judge in it — `run_hv_floor` and
`hv_spot_check` call the `variator` role and nothing else. If reaching it
requires a criticism policy that also arms judge seats, then a run that declines
judges has been locked out of an unrelated capability, which is the shape that
law forbids. That is an argument, not a verdict: the record has to settle
whether a `defended_trial` policy actually forces judge participation.

```
EXECUTOR WINDOW — DEFECT-OR-DESIGN TRANCHE (may end at DIAGNOSIS.md): can a
solo run with no judges reach `hv`?
=========================================================================
Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal.

THE OBSERVATION, FROM THE RECORD: `run_manifest.py:2059-2065` mints the
variator behavioural-contract grant only when
`criticism_policy.authority == "defended_trial"`, and the same condition mints
the defender and judge grants. Across 50 committed v6 roots, exactly 4 hold a
variator grant and all 4 are defended_trial (census reproducible with
`python experiments/2026-09-02-defect-hv-v6-reachability/repro_record.py`).
Since experiments/2026-09-02-defect-hv-v6-reachability/ made the dispatch gate
consult that grant, the grant is now what decides whether `hv` measures at all.

THE LAW AT STAKE: the solo-run law (2026-08-09) and the ungated-seats law
(2026-08-28, operator verbatim: "no limits to what model you place where...
Gates are always optional: with warnings"). `hv` invokes the variator role and
no judge. If a run that declines judges cannot reach it, an unrelated
capability has been gated on a judge-bearing policy.

GOAL (for dr-set-goal to bound): establish whether a v6 configuration with
JUDGE_SEATS_ENABLED false (or no judge seats at all) can hold a
`variator.direct.v1` grant. Falsifiable offline: compile such a manifest and
print its variator grant list. If it is non-empty, there is NO defect -- record
that verdict and stop; "nothing is broken" is a complete outcome. If it is
empty, the defect is that grant minting couples an ungated capability to a
judge-bearing policy, and the fix is in the minting rule.

STOP AND ASK BEFORE IMPLEMENTING: `run_manifest.py` is FROZEN SURFACE 4
(manifest schemas and validators). Changing what the manifest MINTS is a writer
change, not a reader fix, and the asymmetry in
docs/map/INV-frozen-surfaces.md is explicit about which of those is permitted.
Request the grant in FIX.md BEFORE a line of code, with the writer/reader
question argued and the qualification-battery consequence measured -- adding a
contract to a seat ADDS A PAIR to the production-contract battery
(cli/doctor.py:385-420), which is frozen surface 5. Expect this to be a
PRICED STOP, and price it rather than route around it.

OUT OF SCOPE: the dispatch gate (fixed); the nine other gated phases; the
frontier sort.
```
