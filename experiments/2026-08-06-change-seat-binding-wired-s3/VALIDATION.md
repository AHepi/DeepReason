# Validation for: the binding, wired — Rung S3 of role-seat separation

## Acceptance checks

S1 (R1): `--seat` accepted on `deepreason setup`.
```
$ deepreason setup --help | grep -A1 "\-\-seat"
                        [--reasoning REASONING] [--seat GROUP=PATH]
  --seat GROUP=PATH     bind an existing provider profile file to a role group
                        (conjecture, coder, scratch, simulation); repeatable,
                        default (no --seat) leaves every role on the profile
                        above
```
**PASS**

S2 (R1, R8, R9): `seat_bindings.py` parse/write/load + conflict
refusal.
```
$ python -m pytest tests/test_seat_bindings.py -q
12 passed in 0.27s
```
**PASS**

S3 (R2, R10): `resolve_seat_bindings` conflict detection (folded into
the same 12-test run above, including the A8-generalized
scratch/conjecture case). **PASS**

S4 (R2, R3, R10): `_config_for_profile` generalization.
```
$ python -m pytest tests/test_reusable_qualification.py -q -k config_for_profile
2 passed, 31 deselected in 0.18s
```
Full file: 33/33 passing (31 pre-existing + 2 new) — MUST NOT MOVE
confirmed for the pre-existing 31. **PASS**

S5 (R2, R4): threading through `build_preparation_manifest`,
`qualification_subject_manifest`/`_cmd_qualify`,
`RunPreparationService.prepare`.
```
$ python -m pytest tests/test_run_preparation_service.py -q -k seat
2 passed, 9 deselected in 8.69s
```
Full file: 11/11 passing (9 pre-existing + 2 new). **PASS**

S6 (R5): full gate — see "Full gate" section below. **PASS**

S7 (R6): sweep byte-identical.
```
$ diff experiments/2026-08-06-change-seat-binding-wired-s3/sweep-before.txt experiments/2026-08-06-change-seat-binding-wired-s3/sweep-after.txt
(empty, exit 0)
```
45 roots both sides. **PASS**

S8 (R7, A6): two-`MockEndpoint` routing proof.
```
$ python -m pytest tests/test_seat_bindings.py -q -k routing
1 passed, 11 deselected in 2.43s
```
Asserts `LLMCall.model` (the typed attempt record) matches each seat's
own `MockEndpoint`, not internal adapter state. **PASS**

S9 (map maintenance): `docs/map/CON-seats.md` updated in the same
commit as `_config_for_profile`'s generalization (commit `a4e93037`).
See "Map" section below for the full `docs_verify` battery. **PASS**

S10 (R11): no later rung begun.
```
$ grep -rn "qualification.per.seat\|SeatBindingPlanV1\|route_seat.*binding" src/deepreason/seat_bindings.py src/deepreason/preparation.py src/deepreason/run_manifest.py
(no output — src/ clean)
```
(First attempt at this check also searched the tranche's own `*.md`
files, which of course mention "qualification per seat" — as an
explicit OUT-OF-SCOPE item in REQUEST.md/SPEC.md, not an
implementation; caught the false claim of "no output" before
finalizing and re-scoped the check to `src/` only, where it belongs.)
No S4-shaped (`SeatBindingPlanV1`, a manifest-level binding record) or
S5-shaped code landed; `PARKED.md` records only pre-existing and
self-caught-and-fixed items, nothing deferred toward S4/S5.
**PASS**

## Full gate

```
$ pytest tests/ -q -n 4
1 failed, 3357 passed, 7 skipped in 473.17s (0:07:53)
FAILED tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after
```
Independently re-verified unrelated (not merely re-trusting
CHECKLIST.md step 20's own reasoning):
```
$ git log --oneline b4327cc6..HEAD -- src/deepreason/harness.py src/deepreason/module_events.py tests/test_module_fingerprints.py
(no output)
```
This tranche's entire commit range (`b4327cc6`..`HEAD`) never touches
any file the failing test imports or exercises. The failure is the
IDENTICAL one already root-caused as P3 in
`experiments/2026-08-06-change-seat-census-s1/PARKED.md` (a continued
root, `run-a518e33a75507207633f864ba6a864b1`, now carries 2
`module_fingerprints` payloads where the test expects 1) — not
re-diagnosed here, only re-confirmed as out of this tranche's blast
radius. 3357 passed (up from S1's validated 3339 — the ~18 tests this
tranche added: 12 in `test_seat_bindings.py`, 2 in
`test_reusable_qualification.py`, 2 in `test_cli_setup_seats.py`, 2 in
`test_run_preparation_service.py`). **Gate: PASS (pre-existing
failure, confirmed unrelated, already parked)**

## Record-behavior preservation

n/a for `verify_root` re-runs specifically (this tranche never touches
a reader/validator of the append-only record — frozen-surface diff
below is empty). The sweep (S7 above) is the applicable instrument
here and is byte-identical.

## Frozen-surface diff (mechanical tripwire)

```
$ git diff --stat b4327cc6..HEAD -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py src/deepreason/run_manifest.py src/deepreason/qualification.py
(empty)
```
**PASS** — matches SPEC.md's forecast exactly (none expected, none
found).

## Packaging-surface check

```
$ git diff --stat b4327cc6..HEAD -- pyproject.toml
(empty)
$ git diff --stat b4327cc6..HEAD --name-only | grep -E "mcp_server|entry.point|wheel"
(no output)
```
`deepreason setup` gained a new optional argparse flag on an EXISTING
subcommand — no new console entry point, no MCP tool/schema change, no
wheel-layout change. **Packaging surface untouched — smoke not owed.**

## Map

```
$ python tools/docs_verify.py
docs_verify [full]: 52 documents, 824 checks, 4 workers
docs_verify: 0 failed
```
**PASS**
```
$ python tools/docs_verify.py --audit
docs_verify --audit: 0 finding(s)
```
**PASS**
```
$ python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 52 document(s)
```
**PASS**
```
$ python tools/docs_verify.py --coverage
docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 0 finding(s)
```
0 findings — the 16 "no Sweep: header" notices are pre-existing
advisory state across the whole map, none newly introduced by this
tranche (`CON-seats.md` is a `CON-`, not `SEAM-`, document; not in
this list). **PASS**

**`--stale`** (advisory; every entry this tranche's commits appear in,
judged):
- `CON-seats.md` (2 commits since its own `e9007ad1` stamp: the
  `_config_for_profile` generalization commit itself, plus step 15's
  later `preparation.py` threading) — **dismissed, content still
  accurate.** Step 15 only added callers that RESOLVE and PASS
  `seat_bindings` through; it does not change the mechanism
  `CON-seats.md` documents (seat_bindings overrides specific roles,
  resolved before `Config` is built). All of `CON-seats.md`'s own
  checks still pass (confirmed above). Not re-stamping `Verified-at`
  here — this phase may not edit map documents (exit criteria).
- `SUB-application.md` (2 commits: the `--seat` CLI wiring) —
  **dismissed.** Its content names `setup_wizard`/`apply_setup`/etc.
  as existing functions; it makes no claim about `setup`'s exhaustive
  flag list that a new additive flag would contradict. All of its own
  checks still pass.
- `CON-authority.md` (8 commits, 2 attributable to this tranche),
  `CON-run-identity.md` (3 commits, 2 attributable) — **dismissed as
  unrelated.** Both dual-own `preparation.py` (SCHEMA.md's normal
  shared-ownership pattern); this tranche's edits there only add an
  optional `seat_bindings` parameter to config/manifest-building
  functions, touching neither authority/status semantics nor run-id
  digesting (frozen-surface diff above confirms `run_manifest.py`
  itself is untouched).
- `REC-change-a-seam.md` (51 commits, 2 attributable) — **dismissed as
  pre-existing broad staleness**, not attributable to this tranche
  specifically (49 of 51 commits predate it).
- The remaining ~19 entries (`SEAM-*`, `SUB-harness.md`,
  `SUB-manifest.md`, `SUB-ontology.md`, `SUB-periphery.md`,
  `SUB-scheduler.md`, `SUB-verification.md`,
  `CON-scheduler-ranking.md`) list ONLY pre-tranche commits (rung-3/4
  school-population and module-fingerprint work) — **not this
  tranche's concern**, pre-existing at tranche start.

New checks added by this change: 2 (`CON-seats.md`'s
`seat_bindings and role in seat_bindings` check and its
`SEAT_BINDING_ROLE_CONFLICT` check, both added in commit `a4e93037`).

Record observables added vs. sweep probes: none — this tranche adds no
new typed-record field/observable (S2's approved design, 2a: no new
`Config`/`RunManifest` field). The sweep (S7) covers exactly what it
covered before; nothing new for a probe to miss.

Wheel smoke: packaging surface untouched — smoke not owed (see above).

## Requirement sweep

R1: demonstrated by S1 (`--seat` flag exists and is wired).
R2: demonstrated by S4/S5 (`_config_for_profile`/
`build_preparation_manifest` generalized per SM1/SM2).
R3: demonstrated by S4's default-identical test and S7's byte-identical
sweep.
R4: demonstrated by S3/S5 (`resolve_seat_bindings`, threaded to where
leases are built).
R5: demonstrated by "Full gate" section (0 failed net of the
pre-existing, confirmed-unrelated P3).
R6: demonstrated by S7 (sweep byte-identical).
R7: demonstrated by S8 (two-`MockEndpoint` routing proof from
`LLMCall`).
R8: demonstrated by S2's `simulation` alias test.
R9: demonstrated by S2/S3's `SEAT_BINDING_ROLE_CONFLICT` tests
(both the named simulation/conjecture pair and the A8-generalized
scratch/conjecture case).
R10: demonstrated by S10 (no S4/S5-shaped content found).
R11: demonstrated by S10.

Every requirement demonstrated; none deferred.

## Assumptions carried

A1: "coder" = `{property_designer}`.
A2: "scratch" = `{conjecturer, synthesizer, summarizer}`.
A3: "conjecture"/"simulation" = `{conjecturer, variator}`, simulation
a true alias.
A4: the `experimenter`-template call site (CENSUS.md M20) is NOT
independently controllable by "coder" — named limitation, not fixed.
A5: `setup_wizard`/`apply_setup` untouched; `--seat` handled entirely
in `cli/main.py`'s dispatch.
A6: R7's "unit run" read as a pytest unit test with `MockEndpoint`,
not a live CLI subprocess.
A7: `--seat GROUP=PATH`, repeated, confirmed.
A8: the conflict-refusal mechanism generalizes beyond R9's named pair
to the scratch/conjecture overlap this tranche's spec discovered.

## Verdict: PASS
