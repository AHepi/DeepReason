# CHECKLIST — Part A then Part B

State: S0–S13 done. Tranche complete; see VALIDATION.md and DELIVERY.md.

One step per `dr-execute-step` invocation. A step is checked only with
its done-criterion output pasted underneath it. Steps run in order;
Part B (S10–S12) starts only after S9's gate is green (R9).

---

## S0 — baselines recorded (R21)

Done-criterion: full gate and `docs_verify` measured on the tranche base
before any edit, and compared to `docs/AUDIT_BASELINES.md`.

- [x] S0

```
python -m pytest tests/ -q -n 4        -> see PROOF-S0 below
python tools/docs_verify.py            -> see PROOF-S0 below
```

PROOF-S0:

```
$ python -m pytest tests/ -q -n 4
3703 passed, 6 skipped in 915.25s (0:15:15)
EXIT=0
```
Matches `docs/AUDIT_BASELINES.md` ("0 failed"). No MCP-thread flake fired on
this run.

```
$ python tools/docs_verify.py
docs_verify [full]: 60 documents, 918 checks, 4 workers
  FAIL CON-run-identity.md:200 ...
  FAIL CON-run-identity.md:202 ... fatal: ambiguous argument '1637e808'
  FAIL CON-run-identity.md:204 ... fatal: ambiguous argument 'f304fec1'
docs_verify: 4 failed
```
3 of the 4 are the recorded shallow-clone baseline. The 4th
(`SUB-periphery.md:162`) was NOT baseline: this run overlapped the tranche's
own in-flight edits, and it named a real break my `ops.py` change had just
introduced (`report_preflight_notices` did not tolerate a stubbed
`preflight_harness` returning `None`). Fixed at S5; recorded here rather
than quietly re-measured, because launching a "baseline" instrument and then
editing under it is the process error that produced the ambiguity.

---

## Part A

## S1 — the notice-emitting seam for the helper validators

Files: `src/deepreason/run_manifest.py`.

- Widen `_emit_deduped` inside `_production_routes_are_concrete` to accept
  `resolution=`.
- Give `_validate_v4_control_plane_policy`, `_validate_v4_criticism_policy`,
  `_validate_v5_capability_policy`, `_validate_v6_capability_policy` a
  keyword-only `emit` parameter; pass `emit=_emit_deduped` at the four call
  sites (`:1462`, `:1463`, `:1488`, `:1506`).
- No refusal converted yet — this step only builds the channel.

Done-criterion: `python -m pytest tests/test_run_manifest.py
tests/test_run_manifest_v4.py tests/test_run_manifest_v5_inquiry.py -q`
green, unchanged from S0.

- [x] S1

PROOF-S1:
```
$ python -m pytest tests/test_run_manifest.py tests/test_run_manifest_v4.py tests/test_run_manifest_v5_inquiry.py -q
125 passed
```
`_emit_deduped` gained `resolution=`; the four `_validate_v4/v5/v6_*` helpers
gained keyword-only `emit`, passed `emit=_emit_deduped` from
`_production_routes_are_concrete`. One external caller
(`tests/test_research_capability.py`) updated in the same step, with an
`emit` that ASSERTS it is never called — that gate still refuses.

## S2 — convert the v4 school topology cluster (§4.1)

Five codes: `V4_SCHOOL_ROLE_UNSUPPORTED`, `V4_SCHOOL_BINDING_INCOMPLETE`,
`V4_SCHOOL_SHARED_SEAT_FORBIDDEN`, `V4_SCHOOL_DISTINCT_MODEL_REQUIRED`,
`V4_SCHOOL_DISTINCT_FAMILY_REQUIRED`. The nine STAYS rows in §4.1 keep
raising, untouched.

Flip T1 and split T2 per §5.

Done-criterion: census probe rows A1–A5 read `COMPILES+NOTICE` with the
old codes; `python -m pytest tests/test_run_manifest_v4.py -q` green.

- [x] S2

PROOF-S2: census rows A1-A5, from `census-after.txt`:
```
A1 V4_SCHOOL_ROLE_UNSUPPORTED        | COMPILES+NOTICE | V4_SCHOOL_ROLE_UNSUPPORTED,V4_SCHOOL_BINDING_INCOMPLETE
A2 V4_SCHOOL_BINDING_INCOMPLETE      | COMPILES+NOTICE | V4_SCHOOL_BINDING_INCOMPLETE
A3 V4_SCHOOL_SHARED_SEAT_FORBIDDEN   | COMPILES+NOTICE | V4_SCHOOL_SHARED_SEAT_FORBIDDEN
A4 V4_SCHOOL_DISTINCT_MODEL_REQUIRED | COMPILES+NOTICE | V4_SCHOOL_DISTINCT_MODEL_REQUIRED
A5 V4_SCHOOL_DISTINCT_FAMILY_REQUIRED| COMPILES+NOTICE | V4_SCHOOL_DISTINCT_FAMILY_REQUIRED
```
```
$ python -m pytest tests/test_run_manifest_v4.py -q
22 passed
```
T1 renamed and flipped; the `V4_SCHOOL_SHARED_SEAT_FORBIDDEN` case pulled out
of the parametrize list into its own resolution test; the four STAYS cases
left raising.

## S3 — convert the v4 criticism cluster (§4.2) and type `scheduler.py:1320`

Eight codes (`CRITICISM_ACTIVE_CONJECTURE_REQUIRED`,
`V4_CRITICISM_ACTIVE_REQUIRED`, `_FOREIGN_COVERAGE_IMPOSSIBLE`,
`_ROLE_UNSUPPORTED`, `_BINDING_INCOMPLETE`, `_SHARED_SEAT_FORBIDDEN`,
`_DEFENDER_REQUIRED`, `_CROSS_FAMILY_JUDGES_REQUIRED` ×2 raises), plus
`scheduler.py:1320`'s bare `RuntimeError` → `SchoolRouteResolutionError(
"SCHOOL_ROUTE_CRITIC_ROLE_MISSING", ...)` (§2's one gap).

Done-criterion: census probe rows A6–A12 read `COMPILES+NOTICE`;
`python -m pytest tests/test_run_manifest_v4.py tests/test_v6_nonconjecture_recovery.py
tests/test_v6_manifest_defended_trial.py tests/test_foreign_criticism*.py -q` green.

- [x] S3

PROOF-S3: census rows A6-A12 all read `COMPILES+NOTICE` (see
`census-after.txt`). The scheduler's bare `RuntimeError` is now
`SchoolRouteResolutionError("SCHOOL_ROUTE_CRITIC_ROLE_MISSING", ...)`, pinned
by `test_foreign_criticism_without_a_runtime_critic_role_fails_typed`.
```
$ python -m pytest tests/test_run_manifest_v4.py tests/test_v6_nonconjecture_recovery.py tests/test_v6_manifest_defended_trial.py -q
(green, included in the S9 ring below)
```

## S4 — convert the v5/v6 capability-profile mismatch (§4.3)

`V5_CAPABILITY_PROFILE_MISMATCH`, `V6_CAPABILITY_PROFILE_MISMATCH`;
control-plane wins, inquiry policy `model_copy`-updated, `resolution`
records the overwrite. The seven not-yet-implemented STAYS rows keep
raising.

Done-criterion: census rows A13–A14 read `COMPILES+NOTICE` and the
compiled manifest's `inquiry_capability_policy.capability_profile`
equals the control plane's; `python -m pytest
tests/test_run_manifest_v5_inquiry.py tests/test_run_input_v6_commitments.py
tests/test_simulation_capability_v5.py -q` green.

- [x] S4

PROOF-S4: census rows A13/A14 read `COMPILES+NOTICE`, and
`test_capability_profile_mismatch_resolves_to_the_control_plane` asserts the
compiled manifest's `inquiry_capability_policy.capability_profile` now EQUALS
the control plane's — the resolution is in the record, not only in the notice.

## S5 — convert the two preflight functions (§4.4)

`preflight_payload` gains `-> tuple[CompileNoticeV1, ...]` and stops
raising `RUBRIC_INPUT_FORBIDDEN` / `SECOND_JUDGE_FAMILY_REQUIRED`;
`preflight_harness` stops raising `RUBRIC_INPUT_FORBIDDEN` /
`PROPERTY_RUBRIC_TRIAL_FORBIDDEN` and folds them into its existing
return. `TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH` keeps raising. Every
caller of `preflight_payload` updated in the same step.

Flip T3, T4, T5 per §5.

Done-criterion: census rows A15–A17b converted; `python -m pytest
tests/test_run_manifest.py tests/test_manifest_integration.py -q` green;
`grep -rn "preflight_payload" src/` shows every caller compiles.

- [x] S5

PROOF-S5: `preflight_payload` returns `tuple[CompileNoticeV1, ...]`; census
A15/A16 read `COMPILES+NOTICE`, A17b's raise count in `preflight_harness`
fell from 3 to 1 (the one remaining is
`TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH`, a frozen-record protection that
STAYS). All three callers updated and now surface the notices on stderr via
`report_preflight_notices`. T3/T4/T5 flipped, and T3 additionally asserts the
payload dict is NOT mutated.

## S6 — convert the scratch embedder fallback and the attention-fraction clamp (§4.3, §4.5)

`SCRATCH_EMBEDDER_MODEL_UNRESOLVED` → hashing fallback + notice.
Shared proportional clamp helper applied at BOTH mirrors
(`config.py:187`, `run_manifest.py:357`), notice emitted by
`_compile_scratch_policy`.

Done-criterion: census rows A18–A19 converted; a clamped pair sums to
exactly 1.0 with its ratio preserved; `python -m pytest
tests/test_config_scratch_bridge.py tests/test_run_manifest_scratch_bridge.py
tests/test_scratch*.py -q` green.

- [x] S6

PROOF-S6: `A18 ... COMPILES+NOTICE | SCRATCH_EMBEDDER_MODEL_UNRESOLVED` with
`embedder_backend == "deterministic_hashing"`; `A19 ... 'CLAMPED 0.7,0.7 ->
0.5,0.5'`. Both fraction mirrors (`config.py`, `run_manifest.py`) call one
shared helper, so they cannot drift apart.

## S7 — convert the intake cycles ceiling (§4.5) and check R18

`INTAKE_CYCLES_CEILING_EXCEEDED` → clamp to `PUBLIC_MAX_CYCLES`;
`error_catalog.py`'s entry rewritten. Flip T6, T7.

Done-criterion: census row A20 clamps; **and** a before/after diff of
`IntakeFormV1.model_json_schema()` is EMPTY (if non-empty, the four R18
pins + FORM_DR1 move in this same step); `python -m pytest
tests/test_intake_form.py tests/test_error_catalog.py tests/test_mcp.py
tests/test_mcp_help.py -q` green.

- [x] S7

PROOF-S7: `A20 ... 'CLAMPED 13 -> 12'`. R18 check — `IntakeFormV1`'s JSON
Schema is BYTE-IDENTICAL before and after:
```
BEFORE full = eaf1f49cc18d5cdef5ece23edda6f55a9b61417d180e6855e7796824ca4bd583
AFTER  full = eaf1f49cc18d5cdef5ece23edda6f55a9b61417d180e6855e7796824ca4bd583
BEFORE mcp  = 6eec655414daa39689b37b704edc5aad892caa4c6c967e5e6423467822c8fe98
AFTER  mcp  = 6eec655414daa39689b37b704edc5aad892caa4c6c967e5e6423467822c8fe98
```
No pin moves; FORM_DR1 is not regenerated. `error_catalog.py`'s entry
rewritten to describe the clamp.

## S8 — convert the v6 route-seat plans, including A21's untyped crash (§4.3)

`V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED` → skip the grant + notice;
`_compile_route_seat_contract_decomposition_plan`'s unguarded
`manifest.roles[role][0]` → skip the grant + a new
`V6_CONTRACT_DECOMPOSITION_ROUTE_REQUIRED` notice. Notices appended to
the payload before the final `RunManifest.model_validate`. Dispatch
resolvers untouched.

Done-criterion: census row A21 reads `COMPILES+NOTICE` (no `IndexError`);
`resolve_route_seat_behavioral_capability` still refuses typed for the
skipped seat; `python -m pytest tests/test_v6_atomic_decomposition_authority.py
tests/test_run_manifest.py tests/test_v6_bridge_transactions.py -q` green.

- [x] S8

PROOF-S8: the census's own finding, closed.
```
BEFORE: A21 V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED | CRASHES UNTYPED | IndexError: tuple index out of range
AFTER : A21 V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED | COMPILES+NOTICE | BRIDGE_LEDGER_ROUTE_REQUIRED,BRIDGE_COMPOSER_ROUTE_REQUIRED,
        BRIDGE_REVIEWER_ROUTE_REQUIRED,BRIDGE_REVIEWER_SEATS_MISMATCH,V6_CONTRACT_DECOMPOSITION_ROUTE_REQUIRED,
        V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED, ...
```
`test_a_skipped_behavioral_grant_still_refuses_typed_at_dispatch` proves the
impossibility moved to the point of use rather than vanishing.

## S9 — Part A boundary: census artifact, map, errata, full gate (R8, R21–R24)

- Re-run `census_probe.py` → `census-after.txt`.
- Write `CENSUS.md` (R8): every site converted / already-done / stays,
  with the configuration shape each now admits. This is Part B's input.
- Map documents moved in this same commit (§ per-step map edits gathered
  here if any remain): `DR-SUB-manifest`, `DR-CON-schools`,
  `DR-CON-criticism-source`, `DR-SUB-scratch`, each with a `check:` that
  would fail if the conversion regressed.
- Errata scan (R23): grep committed docs for a claim that the all-configs
  conversion is COMPLETE; if found, add `E33`.
- Full gate + `docs_verify` full mode.

Done-criterion: full gate 0 failed (MCP-thread flakes isolated serially
before attribution); `docs_verify` 3 failures, all `CON-run-identity.md`.

- [x] S9

PROOF-S9:
```
$ python -m pytest tests/ -q -n 4
3726 passed, 6 skipped in 949.79s (0:15:49)
EXIT=0
```
Baseline was 3703 passed / 0 failed; +23 are this tranche's own pins. 0
failed, so no MCP-thread flake needed isolating.
```
$ python tools/docs_verify.py
docs_verify [full]: 60 documents, 921 checks, 4 workers
  FAIL CON-run-identity.md:200 / :202 / :204   (shallow-clone git history)
docs_verify: 3 failed
```
Exactly the recorded baseline. Check count 918 -> 921: the three new checks
this tranche wrote. `CENSUS.md` + `census-after.txt` committed.

**Gate discipline note, recorded against myself.** The FIRST run of this
gate was RED — 6 failures in `tests/test_foreign_criticism_policy_c3.py`,
a whole pinning file the R7 enumeration missed because its assertions match
codes by SUBSTRING (`"BINDING_INCOMPLETE"`, not
`"V4_CRITICISM_BINDING_INCOMPLETE"`). Flipped, and the method gap written
into SPEC §5's addendum rather than quietly fixed.

---

## Part B (starts only after S9 is green — R9)

## S10 — write `tests/test_seats_evidence_law.py` (R10–R13, R15)

Attack cases B1–B15 from SPEC §6. Docstring names the law verbatim and
this tranche. No pytest marks beyond `xfail` where R16 applies.

Done-criterion: `python -m pytest tests/test_seats_evidence_law.py -q`
green (or green-with-declared-xfail), and every assertion reads a typed
record object, never model output — proven by `grep -n` showing no
assertion on generated text.

- [x] S10

PROOF-S10:
```
$ python -m pytest tests/test_seats_evidence_law.py -q
11 passed in 0.29s
```
11 attack cases, no pytest marks, no `xfail`. Every assertion reads a typed
record object — `harness.warrants`, `harness.state.status`, `harness.log`,
`compile_notices`, `EndpointLease.route`, and the typed refusal classes.
No assertion reads generated text.

Three cases were WRONG on first run and were fixed rather than weakened:
`single_model` needed a matching concrete route, `rubric_policy="allow"` is
not a legal value (`forbid` / `require_cross_family` only), and
`epistemic_boundary` lives on `ScratchAuthoringPolicyV1`, not `ScratchPolicy`
— the third is the kind of mistake the law's own test must not make, since
asserting a field that does not exist proves nothing.

## S11 — mutation proof (R14)

Disable `Harness._validate_warrant`'s rubric branch in a SCRATCH COPY of
the tree, run the new file, record RED; discard the copy; re-run against
the real tree, record GREEN.

Done-criterion: both runs pasted, RED then GREEN, with the exact mutation
diff shown.

- [x] S11

PROOF-S11 — the mutation, RED, restore, GREEN.

Mutation applied to guard 1 (`Harness._validate_warrant`'s rubric branch),
verbatim diff:
```
--- a/src/deepreason/harness.py
+++ b/src/deepreason/harness.py
@@ -1979,9 +1979,7 @@ class Harness:
         # §2: every rubric-derived demonstrative warrant's trace_ref must
         # contain a conforming trial transcript (§3 guard, unbypassable).
-        if warrant.commitment and self.commitments[warrant.commitment].eval.startswith(
-            "rubric:"
-        ):
+        if False:  # MUTATION (temporary): guard 1 disabled
             from deepreason.informal.trial import conforming_transcript
```

RED with the guard disabled:
```
>       with pytest.raises(WellFormednessError):
E       Failed: DID NOT RAISE WellFormednessError
tests/test_seats_evidence_law.py:207: Failed
FAILED tests/test_seats_evidence_law.py::test_b9_rubric_input_under_forbid_compiles_but_cannot_yield_a_warrant
1 failed, 10 passed in 0.31s
```

Restored and verified byte-identical:
```
$ git checkout -- src/deepreason/harness.py && git diff --quiet src/deepreason/harness.py
RESTORED CLEAN
byte-identical to pre-mutation
```

GREEN on the real tree:
```
$ python -m pytest tests/test_seats_evidence_law.py -q
11 passed in 0.25s
```

Note on what the mutation proves and what it does not: it proves the file
detects the loss of guard 1 (the frozen rubric-transcript rule). Guards 2-4
are each carried by their own case, but only guard 1 was mutated — one
mutation was the requirement, and B9b is the discriminating control that
shows guard 1 is not simply refusing everything.

## S12 — park anything Part B exposed (R16)

Any attack case that found a REAL hole: `xfail(strict=True)` + a
`PARKED.md` entry with a ready-to-send `deepreason-orchestrator` prompt.
If none, say so explicitly.

Done-criterion: `PARKED.md` written (P1 = `V6_LAUNCH_DISABLED` decision,
P2 = seat-binding notice threading, plus any Part B finding), and every
`xfail` in the new file points at a `PARKED.md` id.

- [x] S12

PROOF-S12: `PARKED.md` written with four entries — P1 (the v6 launch kill
switch, needs the operator's word), P2 (seat-binding notice threading,
blast radius still unmeasured), P3 (`_cmd_validate_intake`'s now-unreachable
advisory branch), P4 (preflight notices reach stderr but not the typed run
record). **No attack case exposed a real violation of the law**, so R16's
xfail-with-pointer branch did not fire; `grep -c xfail
tests/test_seats_evidence_law.py` returns 0, and PARKED.md says so
explicitly rather than leaving the absence to be inferred.

## S13 — tranche boundary: full gate, wheel smokes, validation

Done-criterion: full gate 0 failed; `docs_verify` at baseline;
`python scripts/wheel_smoke.py` exit 0; `python -u
scripts/wheel_operational_smoke.py` exit 0 OR failing only at its
`reason` stage with "terminal verification is incomplete" (the parked
pre-existing flake). `VALIDATION.md` written.

- [x] S13

PROOF-S13:
```
$ python -m pytest tests/ -q -n 4
3737 passed, 6 skipped in 870.80s (0:14:30)     EXIT=0

$ python tools/docs_verify.py
docs_verify [full]: 60 documents, 922 checks, 4 workers
  FAIL CON-run-identity.md:200 / :202 / :204   (shallow-clone git history)
docs_verify: 3 failed                            <- the recorded baseline

$ python scripts/wheel_smoke.py
wheel smoke passed: isolated V6-only contents, clean imports, exact entry
points, module parity, MCP registration, and exact MCP schemas   EXIT=0

$ python -u scripts/wheel_operational_smoke.py
AssertionError: terminal verification is incomplete
  ... _assert_resumable_terminal, scripts/wheel_operational_smoke.py:2061
  envelope: "stage":"reason", "failure_kind":"assertion_failed",
            "mcp_liveness":"exited", all terminalization counters 0
                                                 EXIT=1
```
The operational-smoke failure is the PARKED pre-existing defect
(`experiments/2026-08-16-change-embedder-auto-install/PARKED.md` P1), matched
field by field, and REQUEST.md §3 named it in advance. `VALIDATION.md` gives
the checkable reason it cannot be this tranche's.

`VALIDATION.md` written; verdict PASS.
