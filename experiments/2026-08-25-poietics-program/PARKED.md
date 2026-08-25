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

---

## P4 — the results surface counts import-role records as survivors

**FIXED 2026-08-25** — `experiments/2026-08-25-fix-import-role-survivors/`.
The reading this entry asked to separate was settled by the record, not by
wording: all 24 members register at log seqs 5-40 against a log whose first
LLM-bearing event is seq 85. The entry stands unedited below.

**What.** P-R1's terminal result reports 82 survivors. 24 of them are
IMPORT-role admission records — sections of the operator's attached record,
admitted as artifacts at seed and never removed from the survivor set. Of
the 34 survivors passing this tranche's mechanism criterion, 8 are imported
record sections rather than conjectures.

**Why it is a finding and not a preference.** CLAUDE.md states as a
hard-won invariant, in the list whose violations were "real, recorded
defects": *"import-role admission records never count as 'survivors'."*
The results surface counts them.

**Measured, from the committed root:**

    all survivors                     82   = 58 conjecturer + 24 import
    survivors passing the criterion   34   = 26 conjecturer +  8 import

**Consequence, and its limit.** No milestone in this tranche turns on it —
M1 needed one conjecture survivor passing the criterion and got 26. But any
run binding a non-empty dossier will report a survivor count inflated by the
size of that dossier, and "82 survivors" reads as 82 positions when it is
58. The inflation scales with the evidence attached, which means it grows
precisely as attached-evidence runs become more common.

**Not fixed here:** the survivor set is computed in `src/`, and R15 bounds
this tranche to no `src/` or `tests/` change.

**Ready-to-send prompt:**

> Route through `deepreason-orchestrator` (a defect, not a change). Goal:
> establish whether the terminal result's survivor set should exclude
> IMPORT-role admission records, per CLAUDE.md's invariant "import-role
> admission records never count as 'survivors'", and fix it if so.
>
> Diagnose from the typed record BEFORE reading code. The fixture is
> committed and needs no live run:
> `experiments/2026-08-25-poietics-program/run` — 82 survivors, 24 of them
> IMPORT-role, reproducible with:
>
>     from deepreason.harness import Harness
>     h = Harness('<root>', read_only=True)
>     survivors = json.load(open('<root>/run-result.json'))['survivors']
>     # count by h.state.artifacts[a].provenance.role
>
> Two readings to separate before proposing anything, because they lead to
> different fixes. Either the invariant governs every survivor surface and
> the result payload is wrong; or the invariant governs only the reach and
> carrier measures where it was originally recorded, and the defect is that
> CLAUDE.md states it unqualified. Check the tranche that recorded it before
> deciding — the wrong reading here changes committed roots' meaning, which
> is the adjudication-x-authority seam's stated failure mode.
>
> If the fix changes the survivor count, note that committed roots' reported
> numbers move. Under the 2026-08-14 operator law old roots owe the future
> nothing, so that is permitted; say it in the tranche rather than
> discovering it in review.

---

## P5 — the judge ensemble was paid for and never ran

**What.** P-R1 was configured with a two-seat cross-family judge ensemble
(`qwen3.5:397b`, `glm-5.2`) at the operator's explicit instruction. It was
compiled, it passed the qualification battery, and it recorded **zero calls**
across twelve cycles: no defended trial ran, none was declined, none was
blocked by a guard.

**Why it is worth a finding.** A judge rules inside a defended trial, and no
criticism sustained to one. So the run's 419 acceptances are acceptances
under the legacy criticism path, not adjudicated verdicts — and nothing in
this run is evidence about cross-family judging, which was the whole point
of the operator's correction from a solo configuration.

**STRENGTHENED 2026-08-25, after the tranche closed.** This is not a
property of P-R1's configuration. A census of every committed root in
`experiments/` that reports the field returns **judge calls 0, adjudication
ran: no, in every one** - reach-rich, all four epoch-3 attempts, Rung 7's
live gate, and P-R1. No defended trial has ever run in this repository.

    0  ran=no  2026-08-25-poietics-program
    0  ran=no  2026-08-24-change-rung7-wounds-falls-succession
    0  ran=no  2026-08-22-change-epoch3-second-lineage  (and attempts 2, 3, phase1)

That moves the finding from "this run's ensemble bought nothing" to "the
adjudication path has no live evidence of ever executing". Every claim in
this repository about judge behaviour under live conditions rests on
offline tests, and the operator's standing caution about judges - that they
"prosecute without any discernable discrimination" - has never been
testable here, because they have never prosecuted anything.

**Open question this tranche cannot answer:** whether no criticism has ever
DESERVED a trial, or whether something in the path prevents entry
regardless of merit. Those have opposite remedies, and the census cannot
separate them - but it does establish that the question has never been
answered live, which the single-run finding did not.

**Ready-to-send prompt:**

> Route through `deepreason-orchestrator`. Goal: establish why zero defended
> trials ran in `experiments/2026-08-25-poietics-program/run` despite
> `ENGAGED_CRITICISM_AUTHORITY: defended_trial`, `JUDGE_SEATS_ENABLED: true`,
> `ADJUDICATION_STATUS_AUTHORITY_ENABLED: true`, a qualified two-seat
> cross-family judge ensemble, 207 Crit events and 126 critic calls.
>
> Diagnose from the typed record first. The committed root is the fixture;
> `results.txt` reports adjudication ran: no, judge calls 0, trials declined
> none, trials blocked none — note that "declined none" and "blocked none"
> means the trial path was never ENTERED, not that cases were tried and
> lost. Find where a criticism becomes a trial candidate and what predicate
> it failed.
>
> Separate the two readings before proposing a fix: (a) no criticism
> sustained, which is correct behaviour and the finding is only that the
> ensemble's cost bought nothing; or (b) a configuration or gate prevents
> entry regardless of merit, which is a defect. Consult the judge-evidence
> review tranche before designing anything that leans on judges
> (`experiments/2026-08-09-change-judge-evidence-review/`), per CLAUDE.md.
