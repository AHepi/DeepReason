# Parked — found during the repair-vocabulary tranche, NOT worked here

One tranche, one goal. Each entry is written for its future runner: what it
is, and a ready-to-send prompt.

---

## PK1 — `scripts/wheel_operational_smoke.py` fails at `continuation_resume` on main

**What.** `python -u scripts/wheel_operational_smoke.py` exits 1 with
`{"stage": "continuation_resume", "failure_kind": "assertion_failed",
"schema": "deepreason-wheel-operational-failure-v4"}` and every
lifecycle/progress field `"not_observed"`. Measured on THIS tranche's tree and
then again on a clean checkout of `main` (2a5e984c8) with the tranche's work
stashed: **identical stage and failure kind on both**, so it is not this
tranche's. `python scripts/wheel_smoke.py` — the other smoke, which pins the
public surface — passes.

This matters more than a red script usually would: CLAUDE.md says NO gate runs
the wheel smokes, so a failure here is invisible to `pytest tests/ -q` and can
sit unnoticed indefinitely. Nothing in the tranche's cone touches the resume
path; the only edit to that file was an additive `RawResponse` marker plus one
handler branch that no existing response reaches.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect).

Goal, one sentence: find why the installed-wheel operational smoke fails at
its continuation_resume stage on main, and either fix the defect it is
reporting or fix the smoke if the smoke is what is wrong.

Evidence:
  python -u scripts/wheel_operational_smoke.py   -> exit 1
  Failure blob (stage continuation_resume, failure_kind assertion_failed,
  schema deepreason-wheel-operational-failure-v4); every lifecycle and
  progress field reads "not_observed", so the assertion fires before the
  resumed run is observed at all -- read the assertion, not the blob's
  zeros, first.
  Reproduced on main 2a5e984c8 with all other work stashed, so it is not
  the repair-vocabulary tranche's:
      experiments/2026-08-28-defect-repair-vocabulary/VERIFY.md, "Pre-existing
      failures confirmed not mine"
  python scripts/wheel_smoke.py -> passes (public surface is intact)

Note before scoping: no gate runs either wheel smoke (CLAUDE.md, "Build and
test"), so start by finding WHEN this went red -- git log -S on the
continuation_resume assertion, or bisect the script against recent commits
touching application/ or the terminalization phases. A regression that no
gate can see is worth dating before it is fixed, because the answer decides
whether the fix is one commit or a whole lifecycle question.

End state: the smoke passes, or its assertion is corrected with the reason
recorded; if the smoke was right, the defect it found is fixed with a
regression test that a GATE runs, not only the smoke.
```

---

## PK2 — the `repairs` fact in `cycle_soak.py` was over-claiming, and the same shape may be elsewhere

**What.** FIXED here for D1, but recorded because the pattern is general.
`scripts/cycle_soak.py::_attempt_facts` computed `repairs` as the number of
provider attempts with `attempt_index > 0`, and the D1-seat-contract seam
reported `covered` on that count. That is not the same fact as "a repair task
was written and read back": the tranche measured a soak reporting
`covered` / `repairs: 1` whose root contained exactly one
`repair.semantic-task.v1` preparation in the harmless mode, and zero in the
mode that kills runs. This tranche added `repair_payloads` and `repair_modes`,
read from the preparations, so D1's verdict can no longer rest on an attempt
index alone.

The parked question is whether the OTHER three seams (D2 route-lease, D3
budget-auth, D4 reservation-bound) decide `covered` on proxies of the same
kind. All four use `reached_by` object counts, which prove an object EXISTS,
not that the seam's own failure mode was exercised. A soak that reports
covered where it is only reachable is the failure mode CLAUDE.md already names
for this instrument: "an instrument that soaks the wrong shape is worse than
no instrument, because it reports green."

**Ready-to-send prompt:**

```
Route: dr-audit-orchestrator (read-only) or deepreason-orchestrator (defect)
depending on what the first pass finds.

Goal, one sentence: decide, for each of cycle_soak.py's four seams, whether
its "covered" disposition is evidence that the seam's recorded death shape
was exercised, or only that the seam's code was reached.

Evidence:
  scripts/cycle_soak.py SEAMS / assess_seams / _attempt_facts
  experiments/2026-08-28-defect-repair-vocabulary/REPRO.md -- the measured
      case: D1 reported "covered" with repairs: 1, over a root whose single
      repair payload was mode "patch"; the mode that killed the technique
      run's epoch 5 was still unreachable offline. Fixed for D1 in that
      tranche by adding repair_payloads/repair_modes and an unparseable
      induction kind; D2/D3/D4 were not examined.
  experiments/2026-08-23-change-cycle-soak-instrument/RESULTS.md -- states
      which of the four 2026-08-22 deaths are DEMONSTRATED and which are
      only ASSERTED. Read this before treating any green as coverage.

For each seam, answer with a command: what would have to be induced offline
for its recorded death to actually occur, and does the instrument have a way
to induce it? Where it does not, add the induction the way D1's was added
(a kind on the existing inducer, never a second stub) or say plainly that
the seam is reach-only and mark its disposition so.

End state: no seam reports "covered" on a proxy; each either exercises its
own failure mode offline or says it cannot, in the report the launch reads.
```
