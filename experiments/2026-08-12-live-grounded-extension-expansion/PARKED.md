# PARKED.md — grounded-extension-expansion, third launch attempt

## P1: Schools currently share one model each for conjecture and criticism (no per-school model diversity)

Raised by the operator mid-run, 2026-08-13. Not a defect in this run:
`run-config.yaml`'s own header comments explicitly requested "each seat
bound to the seat's existing model (no new model diversity introduced)"
— this was the operator's own prior design choice for this exact run,
correctly executed by `build_manifest.py`'s
`route_bound_school_execution_policy()` call with no `seat_map`. Parked
here rather than acted on because the run is live: CLAUDE.md's
cross-routing rule is "a change wished for mid-defect is PARKED, not
implemented," and the same discipline applies to a change wished for
mid-run — the live root, and any budget already spent reaching its
current state, must not be touched.

**What the harness already supports (verified against code this
session, not assumed):** `SchoolExecutionPolicyV1` (`route_bound` mode)
and `CriticismPolicyV1` both accept a `seat_map: school_id -> (seat,
endpoint_id)` argument (`src/deepreason/v6_policy.py:
route_bound_school_execution_policy`, `engaged_criticism_policy`) that
assigns each school a genuinely different route. Their
`require_distinct_models`/`require_distinct_families` fields (both
`False` in this run) can be set `True` so the manifest's own validator
enforces the distinctness, not just a convention.

**Why this run didn't use it (three separate reasons, not one):**

1. **Experimental cleanliness.** This run's target question is about
   the grounded-extension semantics themselves, not about which model
   makes a better conjecturer or critic. Schools already vary by
   *stance* (8 curated rhetorical postures — adversary, skeptic, etc.,
   `docs/map/CON-schools.md`). Adding model diversity on top, in a run
   with no plan to separate the two effects statistically, would
   confound any observed difference between schools: an interesting
   proposal from school-2 could be "the adversary stance found
   something" or "the model behind school-2 happens to be stronger,"
   and this run's design cannot tell which.
2. **Cost.** Every additional distinct route bound into a role adds its
   own qualification-battery pair (`cli/doctor.py`'s
   `production_contract_pairs` is exact-route × exact-contract) — more
   routes means more qualification time and provider spend, for no
   evidence gain toward the actual research question.
3. **Judge independence.** The two non-conjecturer/non-critic models in
   this run's roster (`qwen3.5:397b`, `mistral-large-3:675b`) are
   reserved for the judge ensemble specifically so a defended trial's
   verdict comes from a model family that never produced the content
   under trial (`informal/trial.py`'s cross-family gate; `judge` is one
   of the two roles the schools mechanism refuses to route at all —
   `docs/map/CON-schools.md`, "exactly two roles may be school-routed").
   Reusing either judge model as a school's conjecturer or critic would
   put that same model family on both sides of some future trial:
   generating content in one school and, in its judge seat, ruling on a
   trial that content is party to. That is a real independence question,
   not a hypothetical one, and it would need its own design decision
   before being introduced — not a default.

**Ready-to-send prompt for a future change tranche (not this window):**

> Change grounded-extension-expansion (or a successor run)'s school
> routing so each of the 4 schools gets a distinct conjecturer model
> and/or distinct critic model, using
> `route_bound_school_execution_policy`'s `seat_map` and
> `engaged_criticism_policy`'s `seat_map`, with
> `require_distinct_models=True`. Decide first whether the new per-school
> models reuse the existing 4-model roster (reassigned — accepting the
> judge-independence question in PARKED.md P1) or introduce new pinned
> tags (accepting the added qualification cost, and the same
> reproducibility-hazard bookkeeping `PREREG.md`'s catalog-metadata table
> already carries), and pre-register which of the two before compiling.
