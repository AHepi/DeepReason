# PARKED — found during the wheel-smoke reason-stage tranche, deliberately not fixed here

Cross-routing law (CLAUDE.md): a change wished for mid-defect is PARKED, not
implemented. One tranche, one goal. Each entry is written for its future
runner and should cost the operator a paste, not an authoring session.

---

## P1 — `docs/map/` owns nothing under `scripts/`, and that has now caused the same defect twice

**What.** The two wheel smokes (`scripts/wheel_smoke.py`,
`scripts/wheel_operational_smoke.py`) are named in `CLAUDE.md` and
`dr-drive-harness` §4 as the third verification instrument, the one NO gate
runs — but no map document owns them, so nothing routes a reader from a
`src/` change to the assertion that change just invalidated.
`docs/map/SUB-application.md`'s Traps already records this happening once
(`2d4ca2e1` moved `budget_exhausted` into `RESUMABLE_STOP_REASONS` while the
smoke asserted the opposite; surfaced 2026-08-05, three defects later). This
tranche is the second occurrence, same shape: `a476c564f` (2026-08-15) made
`verification.completion_satisfied` unreachable on the public reason path
while `_assert_resumable_terminal` still demanded it, and it took six days
and two tranches to attribute.

Deliberately not fixed here: creating a map document for a directory the map
currently excludes is a scoping decision about what the map covers, not a
defect repair, and inventing it as a side effect of a one-function fix is
exactly the silent scope growth the workflow exists to prevent. The
recurrence note added to `SUB-application.md` in this tranche records the
pattern; it does not close it.

**Ready-to-send prompt:**

```
Change tranche: give docs/map/ coverage of the wheel smokes, so a src/
change that invalidates one of their assertions is routable from the map.
Route through dr-change-orchestrator (dr-capture-request -> dr-spec-change ->
dr-plan-steps -> dr-execute-step -> dr-validate-change -> dr-deliver-change).

SETUP: git fetch origin main && git checkout -B claude/map-covers-the-smokes
origin/main; pip install -e . --break-system-packages -q; pip install pytest
pytest-xdist jsonschema --break-system-packages -q. Use `python -m pytest`,
never bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
dr-explain-to-operator. Read docs/map/SCHEMA.md before writing any map
document.

EVIDENCE ALREADY ESTABLISHED (do not re-derive; cite it):
Twice now a src/ change has moved a property only scripts/ asserted, and no
document pointed at it.
 (1) 2d4ca2e1 moved `budget_exhausted` into RESUMABLE_STOP_REASONS while
     wheel_operational_smoke.py had a whole stage asserting the opposite;
     surfaced 2026-08-05 in experiments/2026-08-05-fix-continue-run-rejection,
     only after three other defects in front of that stage were cleared.
 (2) a476c564f (2026-08-15) added Scheduler._premise_rent_step, whose
     unconditional per-cycle deferral makes verification.completion_satisfied
     unreachable on the public reason path, while
     _assert_resumable_terminal still demanded it. Fixed 2026-08-21 in
     experiments/2026-08-21-fix-wheel-smoke-reason-stage/; the intervening
     tranche misread it as a flake (docs/ERRATA.md E34).
Both are recorded in docs/map/SUB-application.md's Traps, in the entry
beginning "That decision changed a property an out-of-map instrument
asserted".

THE QUESTION TO SETTLE FIRST, with the operator, before writing anything:
what SHAPE should this coverage take? The map's five kinds are SUB- (a
package), CON- (a cross-cutting concept), SEAM- (how two meet), INV- (an
invariant) and REC- (a recipe). The smokes are none of them cleanly: they
are an out-of-tree instrument over the INSTALLED wheel. Three candidate
roads, priced:
  A. INV-public-surface-pins.md -- an invariant document listing every
     property the smokes pin (console entry points, MCP tool set + schema
     sha, wheel layout, the terminal assertions) with a `check:` per pin
     that fails when the pin and the code disagree. Cheapest; keeps
     docs/map/ free of a package that is not a package.
  B. SUB-smokes.md -- treat scripts/ as a subsystem with Owns: lines.
     Costs a precedent: docs/map/ currently owns only src/.
  C. Extend each affected SUB- document with a "What the smokes pin here"
     section. Most local, least discoverable.
Recommendation: A. The recurring failure is not "nobody documented
scripts/", it is "nobody could tell that changing a stop reason's meaning
would break an assertion", and an INV- with executable checks is the
artifact that fails when that happens.

END STATE: the map routes a reader from a changed property to the smoke
assertion that depends on it; `python tools/docs_verify.py` stays at
baseline (3 pre-existing CON-run-identity.md shallow-clone failures) with
the new checks passing; `python tools/docs_verify.py --audit` does not
refuse any new check as unfailable; both smokes still exit 0.
```

---

## P2 — `_premise_rent_step` skips its FREE half when the variator is uncontracted

**What.** NOT ESTABLISHED AS A DEFECT — recorded as a question, not a
finding, because this tranche did not test it and must not be read as having
done so. `Scheduler._premise_rent_step` (`scheduler/scheduler.py:2313-2343`)
has two branches. With no variator seat at all it runs
`premise_rent_sweep(harness, decided=...)` — the free half — and its own
docstring says why: "a solo run that cannot take the second reading must say
so rather than pass the premise silently". With a variator seat that has no
v6 behavioral contract it defers and returns, running NEITHER half. The
sibling sites behave the same way (`_lazy_hv`, `vision-criticism`,
`hv-floor`), so this is the house pattern rather than an oversight, and the
whole-step skip may well be the deliberate reading: half-adjudicating a
premise records a verdict the second reading never supported.

The question a future tranche would settle from the record: does a run with a
seated-but-uncontracted variator silently pass premises that a run with NO
variator seat would have recorded a typed abstention for? If yes, the two
no-variator cases disagree about what the record says, and the deferral
marker discloses the phase but not the premises. If no, this entry closes
with a Traps line saying so.

Deliberately not chased here: it is a second, independent cause (dr-diagnose
"If you find a SECOND independent cause, put it in PARKED.md and continue
with the primary"), it is in the harness rather than the instrument, and the
tranche goal was explicitly scoped to name one side and fix that side.

**Ready-to-send prompt:**

```
Diagnosis-only tranche (may end at DIAGNOSIS.md with no fix): does
Scheduler._premise_rent_step silently skip premise adjudication when the
variator seat exists but holds no v6 behavioral contract?
Route through deepreason-orchestrator (dr-set-goal -> dr-diagnose ->
dr-reproduce; STOP after dr-propose-fix and report -- do not implement
without operator direction, because the harness here is behaving as three
design records describe and changing it changes bytes written to every
future record).

SETUP: git fetch origin main && git checkout -B claude/premise-rent-skip
origin/main; pip install -e . --break-system-packages -q; pip install pytest
pytest-xdist jsonschema --break-system-packages -q. Use `python -m pytest`,
never bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
dr-explain-to-operator.

EVIDENCE ALREADY ESTABLISHED (do not re-derive; cite it):
- scheduler/scheduler.py:2313-2343. Branch 1 (`not
  self.adapter.has_role("variator")`) runs `premise_rent_sweep(harness,
  decided=self._premise_decided)` and returns. Branch 2
  (`_defer_untransactional_v6_phase("premise-demarcation-variation",
  "variator", "premise-rent")` returning True) returns having run nothing.
- A v6 manifest grants the variator a behavioral contract only under
  `criticism_policy.authority == "defended_trial"`
  (run_manifest.py::_route_seat_behavioral_contract_assignments, the
  `_defended_trial_authorized` gate), and the public `deepreason reason`
  path sets no criticism_policy at all, so branch 2 is what every ordinary
  run takes: confirmed on run-e9d4bb16796b8aa4b560c632b33d6500's manifest
  (`criticism_policy: null`, one variator seat), marker at log seq 34.
- Committed evidence for that root:
  experiments/2026-08-21-fix-wheel-smoke-reason-stage/evidence/.

FIRST MOVE, record before code: find a committed root that took branch 1
and one that took branch 2, and compare what each recorded for its filed
premises. `premise_rent_sweep`'s typed abstention is the thing to look for
in branch 1's record and to show absent in branch 2's. If no branch-1 root
exists in the repository, say so and build the comparison offline instead
of guessing.

DO NOT widen this into a fix for the deferral mechanism itself. The
deferral is the operator's all-configurations-allowed law working as
designed (disclose typed, never die). The question is only whether the
DISCLOSURE covers what it needs to cover.
```
