# Validation for: qualification per seat — Rung S4 of role-seat separation

Second pass. The first pass (superseded, preserved in git history at
commit `98a5bc8f`) found one FAIL: `docs_verify --stale` showed
`SUB-application.md` stale due to this tranche's own commits, and no
map document documented the behaviour this rung added. That gap was
closed via CHECKLIST.md steps 24-31 (commits `42d32ae1`, `125cc98d`).
This pass re-runs every check fresh from current HEAD.

## Acceptance checks

S1: `python -m pytest tests/test_qualification_per_seat.py -q -k dispatch_purity`
-> `1 passed, 6 deselected in 0.28s` : PASS
`python -m pytest tests/test_qualification_per_seat.py -q -k mutation`
-> `1 passed, 6 deselected in 0.26s` : PASS

S2: `python -m pytest tests/test_qualification_per_seat.py -q -k single_profile`
-> `2 passed, 5 deselected in 6.70s` : PASS
`python -m pytest tests/test_qualification_per_seat.py -q -k two_profile`
-> `1 passed, 6 deselected in 6.63s` : PASS

S3: `python -m pytest tests/test_qualification_per_seat.py -q -k seat_readiness`
-> `1 passed, 6 deselected in 3.56s` : PASS

S4: `python -m pytest tests/test_qualification_per_seat.py -q -k status`
-> `2 passed, 5 deselected in 3.57s` : PASS

S5: `python -m pytest tests/test_run_preparation_service.py -q -k combination`
-> `2 passed, 11 deselected in 5.32s` : PASS

S6: `diff before-qualify.json after-qualify.json` -> `QUALIFY_DIFF_EMPTY`
`diff before-status.json after-status.json` -> `STATUS_DIFF_EMPTY`
: PASS

S7: full gate — see below : PASS (net of pre-existing P1/P3)

S8: `diff sweep-before.txt sweep-after.txt` -> `SWEEP_DIFF_EMPTY` : PASS

S9: `git diff --stat d6b8dea9~1..HEAD -- src/deepreason/run_manifest.py src/deepreason/config.py`
-> (empty). Full tranche `src/`/`tests/` diff:
```
 src/deepreason/cli/main.py            | 410 +++++++++++++++++++++-------------
 src/deepreason/readiness.py           | 178 ++++++++++-----
 tests/test_qualification_per_seat.py  | 375 +++++++++++++++++++++++++++++++
 tests/test_run_preparation_service.py |  63 ++++++
```
No schema file touched. PARKED.md records Rung S4b. : PASS

## Full gate

Run 1 (fresh from current HEAD, `125cc98d`): `4 failed, 3363 passed,
7 skipped in 974.59s`. Beyond the known pre-existing
`test_module_fingerprints.py` failure, 3 NEW failures appeared:
`test_experiment.py::test_fuzz_kills_trap_with_a_proposed_generator`,
`test_mcp_run.py::test_start_poll_result_and_progress_notifications`,
`test_mcp_run.py::test_typed_v6_stop_can_continue_and_append`.
Investigated before accepting:
1. None of these test files, nor any file they exercise
   (`src/deepreason/mcp_server.py`, `src/deepreason/rules/
   experiment.py`), appear in this tranche's diff:
   ```
   $ git diff --stat d6b8dea9~1..HEAD -- tests/test_experiment.py tests/test_mcp_run.py src/deepreason/mcp_server.py src/deepreason/rules/experiment.py
   (no output)
   ```
2. All 3 pass when run in isolation (no `-n 4`):
   ```
   $ python -m pytest tests/test_experiment.py::test_fuzz_kills_trap_with_a_proposed_generator tests/test_mcp_run.py::test_start_poll_result_and_progress_notifications tests/test_mcp_run.py::test_typed_v6_stop_can_continue_and_append -q
   3 passed in 12.77s
   ```
3. A second full-gate re-run reproduces only the ONE known
   pre-existing failure:
   ```
   $ python -m pytest tests/ -q -n 4
   1 failed, 3366 passed, 7 skipped in 658.39s (0:10:58)
   ```
Verdict on the 3 extra failures: transient `-n 4` xdist-parallel
flakes (a fuzz test and two timing/polling-sensitive MCP-run tests —
both known-flaky shapes), not caused by this tranche. Not investigated
further or recorded in PARKED.md, since they did not reproduce and
touch nothing this tranche changed.

Accepted result: `1 failed, 3366 passed, 7 skipped` (run 2, matching
CHECKLIST step 21's original result exactly). The 1 failure is
`tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`,
the SAME pre-existing failure recorded as P3 in Rung S1's PARKED.md and
P1 in Rung S3's PARKED.md, and this tranche's own PARKED.md P1. Root
`run-a518e33a75507207633f864ba6a864b1` carries 2 `module_fingerprints`
stamps. Re-confirmed unrelated to this tranche:
```
$ git log --oneline d6b8dea9~1..HEAD -- src/deepreason/harness.py src/deepreason/module_events.py tests/test_module_fingerprints.py
(no output)
```
Verdict: PASS (net of the independently-reconfirmed pre-existing
failure).

## Record-behavior preservation

n/a — this tranche touches qualification/status/readiness ORCHESTRATION
(`cli/main.py`, `readiness.py`), not a reader or validator of the
append-only record. No `RunManifest`/`Config`/`verify_root` code
changed (S9).

## Frozen-surface diff

```
$ git diff --stat d6b8dea9~1..HEAD -- \
  src/deepreason/capabilities/state.py src/deepreason/harness.py \
  src/deepreason/invariants.py src/deepreason/run_manifest.py \
  src/deepreason/qualification.py
(no output)
```
Empty — zero frozen-surface contact, matching SPEC.md's measured
forecast.

## Packaging-surface check

```
$ git diff --stat d6b8dea9~1..HEAD -- src/deepreason/mcp_server.py pyproject.toml
(no output)
```
`get_readiness`/`ReadinessV1`/the MCP `get_readiness` tool untouched;
no new console entry point, MCP tool, or wheel-layout change.
Packaging surface untouched — smoke not owed.

## Map

docs_verify: `52 documents, 825 checks, 4 workers` / `0 failed` : PASS
docs_verify --audit: `0 finding(s)` : PASS
docs_verify --links: `0 dangling reference(s), 52 document(s)` : PASS
docs_verify --stale: `22 document(s) worth re-reading` (down from 24
before this fix). Confirmed by exact-line grep that neither
`SUB-application.md` nor `CON-seats.md` appears:
```
$ python tools/docs_verify.py --stale | grep -E "^SUB-application\.md:|^CON-seats\.md:"
(no output, exit 1)
```
The gap the first validation pass found is closed. Remaining 22
entries, each dismissed:
- `REC-change-a-seam.md` (52 commits, including this tranche's own
  `42d32ae1`): DISMISSED — its `Owns:` is literally `docs/map/`, the
  entire directory, so ANY commit that ever touches ANY map document
  (including a fix like this one) always counts against it; it was
  already 51 commits stale before this tranche began. Pre-existing
  structural condition of that document's own scope, not something
  this tranche caused in the sense `SUB-application.md`'s gap was.
- `CON-authority.md`, `CON-run-identity.md`, `CON-scheduler-ranking.md`,
  `CON-schools.md`, `INV-frozen-surfaces.md`, `SEAM-bridge-x-manifest.md`,
  `SEAM-harness-x-verification.md`, `SEAM-harness-x-workflow.md`,
  `SEAM-llm-x-manifest.md`, `SEAM-manifest-x-schools.md`,
  `SEAM-ontology-x-rules.md`, `SEAM-scheduler-x-rules.md`,
  `SEAM-scheduler-x-workflow.md`, `SEAM-schools-x-scheduler.md`,
  `SEAM-schools-x-scratch.md`, `SUB-harness.md`, `SUB-manifest.md`,
  `SUB-ontology.md`, `SUB-periphery.md`, `SUB-scheduler.md`,
  `SUB-verification.md`: DISMISSED — every listed commit predates this
  tranche (`d6b8dea9`); none is in `d6b8dea9~1..HEAD`. Pre-existing
  staleness from unrelated prior tranches, unaffected by and not owed
  to this change.

new checks added by this change: `CON-seats.md` (the shared
`_readiness_fields` extraction, `get_seat_readiness`/`SeatReadinessV1`
existence and shape) and `SUB-application.md` (`_qualify_one_profile`/
`_print_qualify_headline`/`_print_qualify_failure` existence,
`get_seat_readiness()`'s call site, 3 new pytest node ids) — 825 total
checks, up from 824 pre-tranche.
record observables added vs sweep probes: n/a — no new typed-record
field/observable (S9); `SeatReadinessV1`/the per-seat qualify payload
are CLI/facade-layer projections, not append-only-record fields, so
the 45-root sweep (S8, PASS) is the correct and sufficient probe for
this tranche's actual record-adjacent surface (none).
wheel smoke: packaging surface untouched — smoke not owed.

## Requirement sweep

R1: demonstrated by S2's acceptance output (`_qualify_one_profile`
loop, single/two-profile tests).
R2: demonstrated by S2 — `qualification_subject_digest`/
`qualification_subject_payload` unchanged (zero lines touched in
`qualification.py`).
R3: demonstrated by S3 + S4 acceptance output (`get_seat_readiness`,
`_cmd_status`'s per-seat section).
R4: demonstrated by S5 acceptance output (M6's measured, pre-existing
`prepare()` refusal, now pinned).
R5: demonstrated by S2's per-profile loop calling the shared helper
with `seat_bindings=None` for every uniform pass; the heterogeneous
COMBINATION pass is a separate, already-measured-safe call (M5),
consistent with R11's relaxation of R5's original absolute form.
R6: demonstrated by S2/S6 (single-profile byte-identity, both payload
and CLI-output level).
R7: demonstrated by S5 (two-profile home qualifies both; refuses typed
when the combination's battery is absent).
R8: demonstrated by the full-gate run above (net of pre-existing P1/P3,
re-confirmed unrelated, and net of a confirmed-transient xdist flake).
R9: demonstrated by S8, the 45-root sweep diff (empty).
R10: demonstrated by S9 — no S5 (record-stamping) work anywhere in this
tranche's diff; PARKED.md defers Rung S4b explicitly.
R11: demonstrated by SPEC.md's M5 (the required dispatch-correctness
measurement, run, PASSES) and the delivered Option 2b scope branching
on that real outcome.
R12: demonstrated by SPEC.md revision 2 retaining M1-M4 verbatim
(unsoftened) under "The finding this rung's design actually rests on".

All 12 requirements demonstrated. No deferred R.

## Assumptions carried

A1: "the rung-6/fingerprint gating shape" = lazy, checked-at-use gating
— moot for this revision's actual delta (M6 shows the check already
exists and fires at the right time); kept for the record.
A2: "distinct bound profiles" = default + every profile named by
`load_seat_bindings()`'s raw entries, deduped by `profile_digest`.
A3: the qualification-completeness check lives in
`RunPreparationService.prepare` — confirmed, requires zero new code
there (M6), only a pinning test (S5).
A4: the per-profile loop (S2) EXCLUDES a bound profile whose digest
equals the default's own, to avoid re-running the same battery under
two labels; operator may override toward always listing it.

## Verdict: PASS

Every SPEC.md acceptance check (S1-S9), the full gate (net of
pre-existing P1/P3 and a confirmed-transient xdist flake), the
frozen-surface diff (empty), the packaging-surface check (untouched),
and the full map validation battery (0 failed / 0 findings / 0
dangling / the specific `--stale` gap closed) all PASS. All 12
requirements demonstrated. No open FAIL. Ready for `dr-deliver-change`.
