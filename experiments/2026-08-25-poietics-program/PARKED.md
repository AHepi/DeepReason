# PARKED — found in this tranche, deliberately not fixed here

One tranche, one goal (CLAUDE.md cross-routing). Each item below is a
finding, not a task for this tranche, and each carries a ready-to-send
prompt so the follow-up costs a paste rather than an authoring session.

---

## P1 — the cycle soak cannot catch a launch-time workload mismatch

**What.** P-R1's first launch was refused by
`cli/main.py::_require_v6_workload_match` with `RUN_INPUT_MISMATCH`, AFTER
the qualification battery had been paid for. `python -u
scripts/cycle_soak.py --case pr1` had returned exit 0 (clean) on the same
configuration minutes earlier.

**Why the bench missed it, precisely.** The soak drives
`TextRunApplicationService` directly — it is written to soak the run path,
and it does. But `_require_v6_workload_match` does not live on that path. It
lives in the CLI shell that `deepreason run --run-manifest --problem` runs
BEFORE entering the service, and it compares three things the soak never
constructs a disagreement between: `problem.json`'s problem id, its
criteria, and **its `sources` list against the bound dossier's source ids**.
The soak's own `build_root` binds an EMPTY dossier for every non-delegating
case, so `sources: []` matches trivially and the predicate is vacuous there.

This is the soak's own stated limit turning up in a new place. Its docstring
says it exists because `wheel_operational_smoke` "never renders this
configuration's SHAPE". The soak renders the shape and drives the cycles —
and still does not render the LAUNCH, because the launch is a CLI shell over
the path it drives.

**Why it matters beyond this tranche.** Any future case that binds a
non-empty dossier at seed inherits the same blind spot, and the cost is not
small: a refused launch after a paid battery, which for a new subject digest
is ~14 minutes and ~1160 calls.

**Not fixed here** because R11 authorises extending the case table, and R15
bounds this tranche to no `src/` or `tests/` change. Adding a launch-shell
stage to the soak is a change to the instrument's scope, which is its own
tranche.

**Ready-to-send prompt:**

> Route through `dr-change-orchestrator`. Goal: `scripts/cycle_soak.py`
> should refuse a case whose `problem.json` and bound dossier disagree,
> because today it cannot see that class at all and a live launch paid a
> full qualification battery to discover one
> (`experiments/2026-08-25-poietics-program/`, attempt 1, retired as
> `refused-attempt1-manifest-1b31f0065687bd24`, typed cause
> `RUN_INPUT_MISMATCH at /run-input.json`).
>
> The gap: `_require_v6_workload_match` lives in `cli/main.py` and runs in
> the `deepreason run --run-manifest --problem` shell, BEFORE
> `TextRunApplicationService`, which is what the soak drives. Every
> non-delegating soak case binds an empty dossier, so the predicate is
> vacuous on the bench.
>
> Smallest correct change is probably a launch-contract stage in the soak
> that calls the CLI's own predicate (imported, never copied) against the
> built root, so the soak fails where the launch would. Prove it can FAIL
> before trusting it: plant `sources: []` against a non-empty dossier and
> require the stage to refuse — that mutation proof already exists in
> `experiments/2026-08-25-poietics-program/` and can be lifted.
>
> Note the tranche-local remedy already shipped and should NOT be
> duplicated: `build_manifest_pr1.py::_assert_workload_matches` runs the
> same check at build time. The question for that tranche is whether every
> builder should have to remember to, or whether the bench should enforce it.

---

## P2 — `deepreason results` cannot describe a root whose run never started

**What.** The retired root carries a bound manifest, run input, dossier and
completed qualification, and no log. `milestone_census.py` crashed on the
missing `log.jsonl` before it was hardened here (fixed in-tranche: it now
reports `record_present: false` and UNMET-by-absence).

**Why it matters.** A refused-at-launch root is a real and reachable state,
and the retrieval surface CLAUDE.md names as "the ONE retrieval surface"
should be able to say what it is rather than erroring. Worth checking
whether `deepreason results` handles it; this tranche did not test that.

**Not fixed here:** `src/` is out of bounds (R15).

**Ready-to-send prompt:**

> Route through `deepreason-orchestrator` (this is a defect, not a change).
> Goal: establish what `deepreason results` does with a root that was
> refused before its Harness existed, using
> `experiments/2026-08-25-poietics-program/refused-attempt1-manifest-1b31f0065687bd24`
> as the fixture — it is committed and has exactly that shape.
>
> Diagnose from the typed record first. If `results` errors rather than
> reporting a typed absence, that contradicts its own documented contract
> ("absent facts print as typed absences, never omitted", CLAUDE.md /
> `dr-drive-harness` §2), and the fix belongs in the results surface, not in
> every caller.

---

## P3 — `report/14` never satisfies P-R1's own confound criterion

**What.** Measured by `preflight_criteria.py`:
`record/report/14_CORRECTIONS_AND_WITHDRAWN_CLAIMS.md` scores **0/3** on
this tranche's criteria, including `poietics-confound@v1`, despite being the
record's own catalogue of everything it got wrong.

**Why it is not a defect of the criteria.** §14 lists corrections
concretely — a specific withdrawn figure, a specific mechanism — without
using the record's generalising limit vocabulary ("one repository", "not
established", "untested"), which is concentrated in §15. So the leakage
census is telling the truth about both documents.

**Why it is worth recording anyway.** M3 asks critics to cite §14 against a
conjecture leaning on a withdrawn number. A future run that tried to select
§14 by criterion match rather than by citation would never find it. M3 as
registered does not do that — it matches on the source id — so P-R1 is
unaffected. Recorded so a later program does not invent the shortcut.

**Ready-to-send prompt:** none. This is a note for whoever designs P-R2's
criteria, and belongs in that design, not in a fix.
