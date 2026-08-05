# Parked — noticed during the P1 tranche, not done

## P1a — `docs/ERRATA.md` E5 misidentifies which roots are the no-manifest three

E5 says: "The three no-manifest calibration roots under
`runs/jolt_positive_headroom_v3_1/` are outside its glob."

Measured at `8122b0e3`, by direct manifest load over every git-tracked
root:

    raising      runs/jolt_positive_headroom_v3_1/calibration/20260701
    raising      runs/jolt_positive_headroom_v3_1/calibration/20260702
    raising      runs/jolt_positive_headroom_v3_1/calibration/20260703
    no-manifest  experiments/bronze_flat_2026-07-13/deepseek-v4-pro
    no-manifest  experiments/bronze_flat_2026-07-13/kimi-k2_6
    no-manifest  experiments/bronze_flat_2026-07-13/qwen3_5_397b

The `runs/` calibration roots RAISE; they are not the no-manifest
three. The no-manifest three are `bronze_flat`, and they are INSIDE
`root_sweep.py`'s `experiments/` glob rather than outside it.

E5's headline finding is unaffected — the 45-root baseline is not
reproducible from the committed tree, and `root_sweep.py` does scan
`experiments/` only — so this is a wrong supporting sentence inside a
correct entry, not a wrong entry. Per `docs/ERRATA.md`'s own rule
("Entries are appended, never rewritten — if a correction itself proves
wrong, that is a new entry"), the disposition is a NEW entry, not an
edit to E5.

Not done here because `docs/ERRATA.md` is outside this tranche's
declared scope (GOAL.md names three paths, and the ledger is not one).
The prose this tranche rewrites around both census checks states the
measured truth and does not repeat the false association, so nothing
this tranche ships depends on E5.

Suggested disposition: a one-entry append to `docs/ERRATA.md`, cheap,
any tranche.

## P1b — the workflow gap that let this reach a delivered tranche

Carried from
`experiments/2026-08-04-change-rung7-authority-as-declared-policy/PARKED.md`
P1: `dr-deliver-change` takes its final measurement BEFORE the
live-evidence commits that a tranche's own later phases make, so a
tranche can invalidate its own proof line without any instrument
noticing. Rung 5's `DELIVERY.md` claims "full gate 3338 passed / 0
failed" and "`docs_verify` 0 failed", both true at `7fdff121` and both
false from `f6d41bff` — inside its own post-delivery segments.

This tranche fixes the readers, which removes the symptom. It does not
close the gap: a future tranche that commits a root after its final
measurement will still ship a stale proof line, just about something
else. Candidate fixes, none chosen here: require `DELIVERY.md` proof
lines to name the commit they were measured at; or add a
delivery-phase step that re-runs the gate after the last evidence
commit.

Suggested disposition: a change tranche against
`.claude/skills/dr-deliver-change/SKILL.md`.

## P1c — P7 remains parked and untouched

The `round-robin` A/B arm root still carries one `attempt-validity`
`verify_root` violation. Confirmed still present while ruling out the
"bad evidence" hypothesis in DIAGNOSIS.md. Not this tranche's goal, not
investigated, not fixed.

## P1d — QUEUED, not parked: the smoke-instrument tranche

Operator instruction received mid-tranche (2026-08-05), recorded here so
it is not lost and NOT absorbed into this goal:

> Defect tranche via deepreason-orchestrator: scripts/wheel_smoke.py is
> red, bisectable to 4940b5f7 (2026-07-28). The pyproject packaging is
> correct — the smoke's entry-point reader wrongly treats the custom
> deepreason.admission.adapters group as console scripts. Fix the
> reader; then run BOTH smokes to completion (wheel_smoke and
> wheel_operational_smoke) and update any other stale pins they surface
> — the MCP tool set and schema sha haven't been verified since
> 2026-07-26. Evidence and analysis in
> experiments/2026-08-05-change-smoke-instrument-visibility/.

Its own tranche, started after this one reaches VERIFY.md. Two things
checked on receipt:

- `4940b5f7` exists and matches the description ("Ship the first-party
  EPUB adapter under the identical §3a contract"); both
  `scripts/wheel_smoke.py` and `scripts/wheel_operational_smoke.py`
  exist.
- **`experiments/2026-08-05-change-smoke-instrument-visibility/` did not
  exist when the instruction arrived — CORRECTED: it does now.** It was
  absent at `7e0a2ea5` and arrived via `20f2c8d1`, pushed by the
  monitoring session (`claude/handover-defect-audit-33pv3d`) and merged
  into this branch at the reproduce-phase boundary. It holds
  `REQUEST.md`, `SPEC.md`, `DELIVERY.md`. Nothing was wrong with the
  operator's pointer; this session simply read the tree before the push
  landed. Recorded rather than silently deleted, because "the evidence
  is missing" and "the evidence arrived late" lead to different next
  actions and the difference is worth one sentence.

The same merge changed the rules this session operates under, mid-
tranche: `20f2c8d1` adds the wheel smokes to `CLAUDE.md` as a THIRD
instrument that no gate runs, and adds a step to `dr-implement-fix`
requiring `python scripts/wheel_smoke.py` when a fix's change sites
touch the packaging surface (pyproject entry points, CLI commands, MCP
tools/schema, wheel layout). **Checked against this tranche: it does
not apply.** FIX.md's change sites are `tests/test_module_fingerprints.py`
and two `docs/map/` documents — no packaging surface — so the smoke ring
is not owed here. It IS owed by the queued P1d tranche, which is
entirely about that surface.

Sequencing note, not a preference: it is worth finishing this tranche
first because the smoke tranche must measure against a tree whose gate
is green. While the four P1 instruments are red, any new breakage the
smokes surface cannot be distinguished from the inherited kind — the
exact cost recorded in
`experiments/2026-08-04-change-rung7-authority-as-declared-policy/DELIVERY.md`.
