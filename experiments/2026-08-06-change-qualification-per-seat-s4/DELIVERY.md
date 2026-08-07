# Delivered: qualification per seat — Rung S4 of role-seat separation

Branch: `claude/seat-census-rung-s1-7gphj9` @ `c7098554` (pushed, tree clean)

## What changed

`deepreason qualify` now walks the distinct bound provider profiles a
home's seats declare — one full battery each, cached by its own subject
digest — in addition to its existing combination-qualify pass (the
heterogeneous manifest, qualified as one subject, unchanged since Rung
S3). `deepreason status` now reports readiness per seat as well as the
one aggregate readiness it always reported. A run whose seat combination
has never been qualified still refuses typed (`QUALIFICATION_NOT_CONFIGURED`),
exactly as it already did — that refusal needed zero new code, only a
pinning test, because a live measurement (M6) proved it already worked.

The delivered design, Option 2b, is smaller than either option this
rung's SPEC originally weighed. A required measurement (M5) proved that
a heterogeneous manifest's qualification battery dispatches every case
to exactly its own role's bound endpoint — zero cross-contamination,
including across schema-repair retries — which is what makes qualifying
the whole combination as one subject legitimate rather than merely
convenient. That measurement, now a committed regression test, is what
let this rung add a per-profile loop for `status` granularity without
touching `preparation.py`, `qualification.py`'s digest/report functions,
`cli/doctor.py`, or any frozen surface.

Changed: `src/deepreason/cli/main.py` (`_cmd_qualify` extracted into
`_qualify_one_profile`, called once for the combination and once per
distinct bound profile; `_cmd_status` extended with a per-seat section),
`src/deepreason/readiness.py` (`get_seat_readiness`/`SeatReadinessV1`
added; `get_readiness`'s existing body extracted into a shared
`_readiness_fields` helper, otherwise untouched). New test file
`tests/test_qualification_per_seat.py` (7 tests) plus 2 tests added to
`tests/test_run_preparation_service.py`. Map documents `docs/map/
CON-seats.md` and `docs/map/SUB-application.md` updated with new prose
and runnable checks for this behaviour.

A single-profile home (no `--seat` flags) is byte-identical to before
this rung at every layer checked: the per-profile loop has exactly one
iteration (the unchanged combination call itself), `deepreason qualify
--json`/`deepreason status --json` output diffs empty against captures
taken before this rung's code landed, and the 45-committed-run-root
sweep is byte-identical before/after.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "qualify walks the distinct bound profiles — one full battery each, each cached by its own subject digest" | done | commit `68b5b69b`, VALIDATION S2 |
| R2 | "S2's SM7 is the evidence this is already sound" | done | commit `68b5b69b` — zero lines touched in `qualification.py`, VALIDATION S2/S9 diff |
| R3 | "status reports readiness per seat" | done | commits `7ef63b01`, `1da24da7`, VALIDATION S3/S4 |
| R4 | "a run with any unqualified seat refuses with a typed reason, at selection time" | done | already-existing code, measured (SPEC.md M6) and pinned by commit `f33ffa3d`, VALIDATION S5 |
| R5 | "never qualify a profile inside a manifest that mixes it with other seats' different bindings" | done-with-assumption, per R11's amendment | superseded to "PERMITTED once measured dispatch-correct" by R11 (operator's own words); measurement M5 run and PASSES, commit `0d86b5c5`; the per-profile loop itself still honors R5's original form for every UNIFORM pass (`seat_bindings=None`) |
| R6 | "single-profile homes must hit the existing cache exactly as today" | done | commits `68b5b69b`, `1da24da7`, VALIDATION S2/S6 (byte-identical diffs) |
| R7 | "a two-profile home qualifies both and refuses typed when one battery is absent" | done | commits `68b5b69b`, `f33ffa3d`, VALIDATION S5 |
| R8 | "full gate 0 failed" | done | VALIDATION full-gate section — `1 failed, 3366 passed, 7 skipped`, the 1 an independently-reconfirmed pre-existing failure (P1) |
| R9 | "sweep byte-identical" | done | commit `bb52a71c`, VALIDATION S8 |
| R10 | "One rung only — no S5 record-stamping work" | done | VALIDATION S9 — no `RunManifest`/`Config` schema change anywhere in the diff; `PARKED.md` defers Rung S4b explicitly, Rung S5 not started |
| R11 | operator's amendment: measure dispatch-correctness first, branch scope on the real outcome | done | SPEC.md revision 2's M5 (measurement run, PASSES) and the delivered Option 2b scope, branched on that real result per the operator's own rule |
| R12 | "S3's mixed-qualify defect analysis stands recorded" | done | SPEC.md revision 2 retains M1-M4 verbatim, unsoftened, under "The finding this rung's design actually rests on" |

All 12 requirements done. None deferred, none not-done.

## Assumptions the operator may override

A1: "the rung-6/fingerprint gating shape" = lazy, checked-at-use gating
— moot for this rung's actual delta (M6 showed the check already
exists and fires at the right time); kept for the record.
A2: "distinct bound profiles" = default + every profile named by
`load_seat_bindings()`'s raw entries, deduped by `profile_digest`.
A3: the qualification-completeness check lives in
`RunPreparationService.prepare` — confirmed, required zero new code
there (M6), only a pinning test.
A4: the per-profile loop excludes a bound profile whose digest equals
the default's own, to avoid re-running the same battery under two
labels; override toward always listing it is a display-only change.

## Map delta

changed: `docs/map/CON-seats.md` (added `readiness.py` to `Owns:`, new
prose on `get_seat_readiness` answering a different question than
launch readiness, new `check:` line), `docs/map/SUB-application.md`
(new "Where to change what" row for the per-profile qualify loop and
per-seat status, extended existing aggregated `check:` line)
created: none
new checks: 2 (825 total map checks, up from 824 before this tranche)
left stale: `REC-change-a-seam.md` (`Owns: docs/map/`, the entire
directory — structurally always shows staleness after any map edit
whatsoever, including this fix's own commits; pre-existing, 51 commits
stale before this tranche began, not owed to this change). 20 other
documents remain in `docs_verify --stale`'s advisory list, all with
commits that predate this tranche (`d6b8dea9`) — unrelated prior-tranche
staleness, unaffected by this work.

## Parked (not done, not promised)

**Rung S4b** — per-role provenance qualification (Option 1 from SPEC.md
revision 1): qualify each distinct profile once, let any manifest that
mixes already-qualified profiles launch without a fresh combination
battery. Real cost optimization (fewer batteries as operators reshuffle
seat bindings), NOT required for correctness — this rung's M5/M6
measurements already prove combination-subject qualification is
correct, not merely convenient. Genuine frozen-surface-5 contact when
built (`project_qualification_report` and all 5
`require_v6_production_qualification` call sites would need to accept a
report synthesized from N independent single-profile qualifications).
Ready-to-send prompt: *"Rung S4b via `dr-change-orchestrator`: per-role
provenance qualification, per `experiments/
2026-08-06-change-qualification-per-seat-s4/PARKED.md`'s S4b entry and
SPEC.md revision 1's Option 1 design sketch. This is real
frozen-surface-5 contact — `dr-spec-change` must produce the
frozen-surface contact forecast and stop for approval before any code
lands."*

**P1** — pre-existing full-gate failure, not caused by any Rung S1-S4
tranche: `tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`
fails on root `run-a518e33a75507207633f864ba6a864b1` (2
`module_fingerprints` stamps where the test expects exactly 1). Fully
diagnosed in Rung S1's `PARKED.md` (root cause, reproduce steps,
two candidate fix shapes) and re-confirmed unrelated by every
subsequent rung (S2 made no code change; S3 and this rung both show
empty `git log` on the failing test's dependency files). Ready-to-send
prompt: *"`deepreason-orchestrator`, `dr-set-goal`: `tests/
test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`
fails on a continued root carrying 2 `module_fingerprints` stamps where
the test expects exactly 1 — diagnosed in `experiments/
2026-08-06-change-seat-census-s1/PARKED.md`'s P3 entry. Determine
whether the continuation path over-emits the stamp or the test's
'exactly one' assumption is wrong for a continued run, before choosing
a fix."*

recommended next: none from this queue requires action — both parked
items are real but neither blocks anything live. If the operator wants
multi-model launches to get CHEAPER (not just correct) as seat bindings
reshuffle often, Rung S4b is the one with headroom; otherwise the
program's own next named rung is S5 (seats in the typed record),
explicitly out of scope here per R10 and not started.

---

This closes Rung S4. The role-seat separation program
(`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md`) has now delivered S1
(census), S2 (binding design), S3 (the binding, wired), and S4
(qualification per seat). Remaining named work is Rung S4b (parked
above) and Rung S5 (seats in the typed record) — neither begins without
explicit operator instruction, per this program's "one rung only"
discipline observed at every step so far.
