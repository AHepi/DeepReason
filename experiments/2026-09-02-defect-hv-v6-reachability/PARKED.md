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

---

## P6 — promote `v6_transactional_phase_call` out of `informal/trial.py`

WHAT: the shared v6 dispatch helper is generalised IN PLACE in
`src/deepreason/informal/trial.py` (three keyword parameters, a public alias),
because `informal/` and `measures/` are both owned by `DR-SUB-evaluation` so hv
crosses no seam to import it. The nine follow-up phases live in `rules/`,
`scratch/` and `informal/audits.py`, so the first of those that is converted
from OUTSIDE `DR-SUB-evaluation` needs the helper in a neutral home —
`src/deepreason/workflow/`, which the seam says owns "by what recorded authority
any of it may touch a provider". That is a 212-line pure relocation and belongs
in its own commit where a reviewer can verify by diffing that nothing moved but
the lines.

```
EXECUTOR WINDOW — REFACTOR TRANCHE: move v6_transactional_phase_call to the
workflow plane
=========================================================================
Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal (class: regression-risk -- nothing
is broken; this is a relocation that must prove it changed nothing).

THE MOVE: src/deepreason/informal/trial.py:61-272 defines
`_v6_transactional_trial_call`, aliased public as `v6_transactional_phase_call`
by experiments/2026-09-02-defect-hv-v6-reachability/. It is fully parameterised
(task_payload_schema, trigger_prefix, reason_prefix) and has two consumers:
trial.py's own five call sites and measures/hv.py. Move it verbatim to
src/deepreason/workflow/phase_dispatch.py and leave a re-export in trial.py so
no caller changes.

GOAL (for dr-set-goal to bound): the function's body is byte-identical after the
move. Falsifiable offline: a test comparing inspect.getsource of the moved
function against the pre-move text committed as a fixture in the tranche
directory; plus the full gate at 0 failed with no test edited.

WHY NOT SOONER: mixing a 212-line relocation with a behavioural change makes the
behavioural change unreviewable. That was the explicit reason this was parked.

READ FIRST: docs/map/SEAM-scheduler-x-workflow.md (its check counts
`deepreason.workflow` occurrences in scheduler.py and will move),
docs/map/SUB-workflow.md, docs/map/SUB-evaluation.md. The map moves in the same
commit.

OUT OF SCOPE: any change to the helper's behaviour or parameters; converting any
phase.
```

---

## P7 — CLOSED 2026-09-02 by operator ruling, not parked

**Status: DELIVERED in this tranche.** The stop was put to the operator with
both roads priced; they ruled Road A, verbatim: *"It used to be on. And it's
absolutely necessary. So switch it on. And you can test whether it works as
intended"*. `hv-floor` is converted, and the obligation the ruling carried — test
that it WORKS, not merely that it dispatches — is discharged by four offline
verdict tests (FAIL refutes and mints one warrant; PASS records the estimate and
leaves the target ACCEPTED; zero samples OVERRUN rather than passing vacuously;
no status moves on an artifact carrying no `hv-floor` criterion) plus a live
check against glm-5.2 that reached both verdicts with `verify_root` clean.

The correction the operator's first sentence makes is the one worth keeping:
`hv-floor` **used to be on**. It dispatched on every pre-v6 run and stopped only
because the gate's `schema_version` escape went dead under operations parity,
while `rules/spawn.py` kept pinning its criterion onto every connection problem.
So the tranche's own framing — that switching it on introduces new refutation —
was wrong; it RESTORES evaluation of criteria that were pinned and never
checked. The original parked prompt is kept below, struck through, because the
reasoning it contains is the reasoning the ruling overturned and a later reader
should be able to see both.

~~Original park (superseded):~~ convert `hv-floor` to v6 transactional dispatch


WHAT: `experiments/2026-09-02-defect-hv-v6-reachability/` FIX.md §7 recommended
Road B — convert `hv-spot-check` only — because `run_hv_floor` is not a ranking
measure: on `hv < hv_min` it calls `register_fail_warrant` and REFUTES its
target, and `rules/spawn.py:150-172` pins an `hv-floor` criterion onto every
connection problem the harness mints. Converting it therefore changes refutation
outcomes on ordinary runs, which the tranche brief made an explicit STOP AND ASK
and which no offline instrument can adjudicate. Priced from the record: on
`2026-08-12-live-grounded-extension-expansion/run`, 53 connection problems and
95 distinct artifacts had their `hv-floor` criterion deferred.

THE CODE CHANGE IS ONE TABLE ROW. `LEGACY_PHASE_CONTRACTS["hv-floor"].dispatch`
goes from `"unconverted"` to `"v6_transactional"`, and `run_hv_floor` passes the
self-detected manifest to `_sample_edits` exactly as `hv_spot_check` already
does. The evidence question is the whole tranche.

```
EXECUTOR WINDOW — RUN-AND-DECIDE TRANCHE: should a v6 run's pinned `hv-floor`
criterion be evaluated again?
=========================================================================
Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal.

THE SITUATION: `run_hv_floor` (src/deepreason/measures/hv.py:267) evaluates the
`hv-floor` criterion that `rules/spawn.py:150-172` pins onto every connection
problem, and on hv < hv_min it mints a demonstrative fail warrant -- it REFUTES.
Since RunManifest v6 became the only run path, the deferral gate has suppressed
that evaluation on every run; experiments/2026-09-02-defect-hv-v6-reachability/
made the gate configuration-driven but left this one phase `unconverted` on
purpose, because turning it back on changes what gets refuted and no offline
instrument can say whether the resulting refutations are sound.

Today the deferred criterion is COMPLETELY INERT: an `hv-floor` commitment is
not registry-evaluable, so `crit_program` skips it, and `pareto_scores`'
coverage denominator does not count it. A pinned criterion currently costs
nothing and proves nothing. That is the argument FOR turning it on.

GOAL (for dr-set-goal to bound): produce evidence on which the operator can rule.
Flip the one table row, then run a SHORT live run (or an offline soak on a shape
that spawns connection problems) that actually produces some hv-floor FAIL
warrants, and read them: are the refuted relations genuinely poor, or is the
floor refuting sound work? Record the verdict either way -- "the criterion
refutes soundly" and "the criterion over-refutes" are both complete outcomes,
and so is "no artifact reached the floor, inconclusive".

STOP AND ASK BEFORE MAKING THE FLIP PERMANENT: the operator decides whether
reinstated refutations are wanted. Present the sampled warrants, not a summary.

READ FIRST: experiments/2026-09-02-defect-hv-v6-reachability/FIX.md section 7
(the pricing and the two roads) and docs/map/SUB-evaluation.md's Traps entry on
zero-sample vacuous passes -- `run_hv_floor` returns OVERRUN on no edits
precisely so a floor is never passed from no evidence.

OUT OF SCOPE: the gate, the registry, the helper, the other nine phases -- all
delivered or parked separately.
```
