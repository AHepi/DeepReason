# VERDICT: (a) — zero is correct for these roots

Reach never fires on any current-version root, and the census says that is
the RIGHT answer, not a suppressed one. No reader is wrong in the direction
the operator worried about and no threshold is suppressing a hit: the
coverage gate rejected 0 pairs, the structural filter rejected 0 pairs, and
every one of the 585 096 rejections at the verdict gate is a genuine
content-level `fail` over artifact bytes that resolve (3 528 / 3 528
non-empty).

The reason is sharper than the hypothesis the brief offered. It is NOT that
"the problems really do carry only structural criteria" — `E2
non-qualifying` is zero, so the structural filter is not what rejects
anything. It is that the corpus's ENTIRE qualifying vocabulary is two FORM
gates (`relation-form@578e42df713e`, `reasoning-envelope-wf`), and an
artifact satisfies a form gate exactly when it was built carrying it. Reach
asks for a criterion that is novel to the artifact AND passed by it; over
96 roots and 6 650 artifact-criterion observations, that cell is empty.

So there is no substantive foreign battery in this corpus for anything to
survive — and the Bronze Age discipline is not what is holding reach back.
Something weaker is: nothing has ever asked these runs' problems a
machine-checkable question about their own subject.

## What Rung 5 needs before its gate can be honest

Rung 5 nominates a promotion problem from "reach events for one subject
spanning >= K_frame distinct problem lineages". On this evidence that
nomination can never fire on any existing root, so Rung 5 cannot gate on the
committed corpus. It needs a REACH-RICH root generated live. From the
census, that run must contain all five of:

1. **Subject-substantive criteria.** At least one criterion per problem that
   is machine-evaluable AND asks about the problem's subject, not its form:
   an `exec_oracle` / `property_oracle` / `dataset_oracle` commitment, or an
   operator-authored `predicate:` over subject content. Zero of these appear
   on any problem in any in-scope root today, so the run has to introduce
   them deliberately (the reasoning-workload seed path,
   `workloads/text.py::seed_reasoning_workload`, is where a run's own
   criteria enter).
2. **Criteria the conjecturer is not told to satisfy.** The measured killer
   is that carrying implies passing. A criterion minted per-problem from the
   problem's subject, and absent from the candidate's own compiled battery,
   is what makes the novelty condition satisfiable at all. A criterion the
   spawn prompt teaches the model to satisfy will always be carried, hence
   never novel.
3. **Coverage headroom.** The foreign problem needs qualifying / total
   criteria >= 0.5. Auto-spawned CONNECTION problems sit at 0.33
   (`hv_floor` + `lineage_ref` + one qualifying gate) and can therefore only
   ever be PROVISIONAL — so the reach-rich run's problems must carry at
   least as many substantive criteria as auto-attached structural ones.
4. **Two or more genuinely overlapping subjects.** Reach is cross-problem
   survival: the run needs at least two problems whose subject matter
   overlaps enough that one problem's answer could survive the other's
   battery, plus a third for `K_frame >= 3` if Rung 5 pins K_frame above 2.
5. **Distinct problem LINEAGES.** Nomination counts lineages, not problems.
   Problems spawned from one artifact's neighbourhood share a lineage, so
   the run must seed independent problems rather than rely on the
   connection/integration spawn cascade to manufacture them.

A cheaper intermediate is available and worth pricing: a run satisfying
(1)-(3) but only two overlapping subjects would produce the first non-zero
`reach_set` event in the project's post-discipline history and turn the
mechanism from unexercised into exercised, without yet proving nomination.
That is the smallest live evidence that would let Rung 5's design proceed on
something other than a mechanism no root has ever run.

## What was NOT done, deliberately

No threshold was lowered, no program was removed from
`_STRUCTURAL_PROGRAMS`, no criterion was reclassified. The Bronze Age
postmortem is why the strictness exists, and the census shows the strictness
is not the cause; loosening it would manufacture hits from form gates, which
is exactly the defect the discipline exists to prevent. Two findings that
would move in the OPPOSITE direction — the substantive/structural boundary
being too PERMISSIVE — are parked, not fixed: see `PARKED.md` P1 and P2.
