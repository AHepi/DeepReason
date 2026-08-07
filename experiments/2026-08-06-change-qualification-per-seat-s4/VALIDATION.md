# Validation for: qualification per seat — Rung S4 of role-seat separation

## Acceptance checks

S1: `python -m pytest tests/test_qualification_per_seat.py -q -k dispatch_purity`
-> `1 passed, 6 deselected in 0.30s` : PASS
`python -m pytest tests/test_qualification_per_seat.py -q -k mutation`
-> `1 passed, 6 deselected in 0.29s` (mutation-companion, proves the
main assertion is not vacuous) : PASS

S2: `python -m pytest tests/test_qualification_per_seat.py -q -k single_profile`
-> `2 passed, 5 deselected in 7.37s` (single-profile-home byte-identity,
both the qualify-payload test and the status test match this filter)
: PASS
`python -m pytest tests/test_qualification_per_seat.py -q -k two_profile`
-> `1 passed, 6 deselected in 7.57s` (two-distinct-profile home: per-
profile loop qualifies both, combination call still qualifies the
combination, three distinct outcomes) : PASS

S3: `python -m pytest tests/test_qualification_per_seat.py -q -k seat_readiness`
-> `1 passed, 6 deselected in 7.38s` (two bound groups -> 2
`SeatReadinessV1` entries, correct per-profile state, independent of
combination-qualify status) : PASS

S4: `python -m pytest tests/test_qualification_per_seat.py -q -k status`
-> `2 passed, 5 deselected in 4.19s` (single-profile status byte-
identical; two-seat status names both seats) : PASS

S5: `python -m pytest tests/test_run_preparation_service.py -q -k combination`
-> `2 passed, 11 deselected in 5.55s` (unqualified combination refuses
typed `QUALIFICATION_NOT_CONFIGURED`; qualified combination succeeds,
committed manifest roles reflect both profiles) : PASS

S6: `diff before-qualify.json after-qualify.json` -> `QUALIFY_DIFF_EMPTY`
`diff before-status.json after-status.json` -> `STATUS_DIFF_EMPTY`
: PASS

S7: full gate — see below : PASS (net of pre-existing P1/P3)

S8: sweep — see below : PASS

S9: `git diff --stat d6b8dea9~1..HEAD -- src/deepreason/run_manifest.py src/deepreason/config.py`
-> (empty). `git diff --stat d6b8dea9~1..HEAD -- src/ tests/`:
```
 src/deepreason/cli/main.py            | 410 +++++++++++++++++++++-------------
 src/deepreason/readiness.py           | 178 ++++++++++-----
 tests/test_qualification_per_seat.py  | 375 +++++++++++++++++++++++++++++++
 tests/test_run_preparation_service.py |  63 ++++++
```
No schema file touched; only `cli/main.py`/`readiness.py` function
bodies and two test files. PARKED.md records Rung S4b. : PASS

## Full gate

Ran fresh at CHECKLIST step 21 (commit `2905c12e` is the last commit;
`git diff --stat HEAD~1..HEAD -- src/ tests/` from that commit is
empty, so the result still holds at current HEAD):
`1 failed, 3366 passed, 7 skipped in 631.89s (0:10:31)`.
The 1 failure is `tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`,
the SAME pre-existing failure recorded as P3 in Rung S1's PARKED.md and
P1 in Rung S3's PARKED.md (root `run-a518e33a75507207633f864ba6a864b1`
carries 2 `module_fingerprints` stamps). Re-confirmed unrelated to this
tranche fresh:
```
$ git log --oneline d6b8dea9~1..HEAD -- src/deepreason/harness.py src/deepreason/module_events.py tests/test_module_fingerprints.py
(no output)
```
Verdict: PASS (net of the independently-reconfirmed pre-existing
failure, per R8's own "net of" language and this program's established
convention).

## Record-behavior preservation

n/a — this tranche touches qualification/status/readiness ORCHESTRATION
(`cli/main.py`, `readiness.py`), not a reader or validator of the
append-only record. No `RunManifest`/`Config`/`verify_root` code
changed (S9). Not applicable; no spot-check owed.

## Frozen-surface diff

```
$ git diff --stat d6b8dea9~1..HEAD -- \
  src/deepreason/capabilities/state.py src/deepreason/harness.py \
  src/deepreason/invariants.py src/deepreason/run_manifest.py \
  src/deepreason/qualification.py
(no output)
```
Empty — zero frozen-surface contact, exactly as SPEC.md's forecast
("None," measured via M5/M6) predicted.

## Packaging-surface check

`cli/main.py`'s CLI surface (`_cmd_qualify`, `_cmd_status`) and
`readiness.py` changed, but neither the MCP tool set, `pyproject.toml`,
nor the wheel layout moved:
```
$ git diff d6b8dea9~1..HEAD -- src/deepreason/mcp_server.py pyproject.toml
(no output)
$ grep -c "get_readiness\|get_seat_readiness" src/deepreason/mcp_server.py
8   # all 8 are get_readiness; get_seat_readiness is never referenced
```
`get_readiness`/`ReadinessV1`/the MCP `get_readiness` tool are
confirmed untouched. `--seat`/`qualify`/`status` are pre-existing CLI
entry points (added in Rungs S3/pre-existing); no NEW console entry
point, MCP tool, or wheel-layout change. Packaging surface untouched —
smoke not owed.

## Map

docs_verify: `52 documents, 824 checks, 4 workers` / `0 failed` : PASS
docs_verify --audit: `0 finding(s)` : PASS
docs_verify --links: `0 dangling reference(s), 52 document(s)` : PASS
docs_verify --coverage: `6 seam(s) swept, 16 without a Sweep: header,
0 finding(s)` — the 16 are pre-existing (unrelated seams: adjudication,
bridge, evaluation, harness-verification, llm-manifest/rules/workflow,
ontology-rules, rules-workflow, scheduler-rules/workflow,
schools-scheduler, scratch-workflow); none touch this tranche's files
: PASS (advisory-clean for this tranche)
docs_verify --stale: `24 document(s) worth re-reading`. Of these, ONE
is caused by this tranche and is a real, unaddressed finding:

```
SUB-application.md: 4 commit(s) to owned files since a65e8578
    1da24da7 Rung S4 step 15-16: _cmd_status's per-seat readiness section
    68b5b69b Rung S4 step 8-10: _cmd_qualify's additive per-profile loop
    9d28d47a step 15: thread seat_bindings through prepare and qualify
```
`68b5b69b`/`1da24da7` are THIS tranche's own commits (verified: both
appear in `git log --oneline d6b8dea9~1..HEAD`); `9d28d47a` predates
this tranche (Rung S3). `SUB-application.md` owns `src/deepreason/cli/`
(the `Owns:` glob), which covers `cli/main.py` — the file this
tranche's `_qualify_one_profile` extraction and `_cmd_status`'s
per-seat section both live in. `SUB-application.md`'s current text
(re-read in full) contains ZERO mention of `_cmd_qualify`,
`_cmd_status`, per-seat qualification, or per-seat readiness. Grepping
`CON-seats.md` and `SUB-manifest.md` (the other two map documents named
in SPEC.md's own Map preflight line) for the new symbols this rung
introduced also comes back empty:
```
$ grep -n "get_seat_readiness\|SeatReadinessV1\|_qualify_one_profile\|_readiness_fields" docs/map/CON-seats.md docs/map/SUB-manifest.md docs/map/SUB-application.md
(no output)
```
**Not dismissed** — this is real: behaviour this rung ADDED (the
per-profile qualify loop, `get_seat_readiness`/`SeatReadinessV1`, the
per-seat status section) has ZERO falsifiable map coverage anywhere.
Per dr-validate-change's own rule ("a change with no new [map] check
has documented nothing falsifiable") and CLAUDE.md's "the map moves in
the SAME COMMIT as the code" rule, this is a genuine gap CHECKLIST.md
never planned a step for (re-read in full: no step among the 23
touches `docs/map/`). All other 23 `--stale` entries are pre-existing,
caused by OTHER tranches' commits, unrelated to any file this rung
touched (`cli/main.py`, `readiness.py`) — dismissed as out of scope.

new checks added by this change: **none** — this is the FAIL detail.
record observables added vs sweep probes: n/a — no new typed-record
field/observable added (S9: no `RunManifest`/`Config` schema change);
`SeatReadinessV1`/the qualify per-seat payload are CLI/facade-layer
projections, not append-only-record fields, so the 45-root sweep
(S8, PASS) is the correct and sufficient probe for this tranche's
actual record-adjacent surface (none).
wheel smoke: packaging surface untouched — smoke not owed.

## Requirement sweep

R1: demonstrated by S2's acceptance output (`_qualify_one_profile`
loop, single/two-profile tests).
R2: demonstrated by S2 — `qualification_subject_digest`/
`qualification_subject_payload` unchanged (git diff shows zero lines
touched in `qualification.py`).
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
re-confirmed unrelated).
R9: demonstrated by S8, the 45-root sweep diff (empty).
R10: demonstrated by S9 — no S5 (record-stamping) work anywhere in this
tranche's diff; PARKED.md defers Rung S4b explicitly.
R11: demonstrated by SPEC.md's M5 (the required dispatch-correctness
measurement, run, PASSES) and the delivered Option 2b scope branching
on that real outcome, not an assumed one.
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

## Verdict: FAIL

FAIL detail: the map validation battery (`docs_verify --stale`)
surfaces a real, unaddressed finding: `SUB-application.md` (one of the
three map documents SPEC.md's own "Map preflight" line named in scope)
is stale specifically because of this tranche's own commits (`68b5b69b`,
`1da24da7`) touching `cli/main.py`'s owned surface, and NEITHER
`SUB-application.md` NOR `CON-seats.md` NOR `SUB-manifest.md` gained
any new prose or `check:` line for the behaviour this rung actually
added — the per-profile qualify loop (`_qualify_one_profile`), per-seat
readiness (`get_seat_readiness`/`SeatReadinessV1`), or `_cmd_status`'s
per-seat section. CHECKLIST.md (re-read in full for this validation
pass) never planned a map-update step for any of S2/S3/S4's items,
violating `dr-plan-steps`' own rule 4c ("plan the map update as part of
the step that changes behaviour, never as a trailing step") and
CLAUDE.md's "the map moves in the SAME COMMIT as the code" rule. Every
other check in this document is a genuine PASS; this is the sole
blocker. Routing back to `dr-plan-steps` to add the missing map-update
step(s) (documenting the S2/S3/S4 mechanism in the appropriate map
document(s), with a new runnable `check:`), then `dr-execute-step`,
then re-run this validation phase.
