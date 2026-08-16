# CHECKLIST — Part A then Part B

State: S0 done; S1–S13 pending.

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

PROOF-S0: (pasted at execution)

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

- [ ] S1

## S2 — convert the v4 school topology cluster (§4.1)

Five codes: `V4_SCHOOL_ROLE_UNSUPPORTED`, `V4_SCHOOL_BINDING_INCOMPLETE`,
`V4_SCHOOL_SHARED_SEAT_FORBIDDEN`, `V4_SCHOOL_DISTINCT_MODEL_REQUIRED`,
`V4_SCHOOL_DISTINCT_FAMILY_REQUIRED`. The nine STAYS rows in §4.1 keep
raising, untouched.

Flip T1 and split T2 per §5.

Done-criterion: census probe rows A1–A5 read `COMPILES+NOTICE` with the
old codes; `python -m pytest tests/test_run_manifest_v4.py -q` green.

- [ ] S2

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

- [ ] S3

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

- [ ] S4

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

- [ ] S5

## S6 — convert the scratch embedder fallback and the attention-fraction clamp (§4.3, §4.5)

`SCRATCH_EMBEDDER_MODEL_UNRESOLVED` → hashing fallback + notice.
Shared proportional clamp helper applied at BOTH mirrors
(`config.py:187`, `run_manifest.py:357`), notice emitted by
`_compile_scratch_policy`.

Done-criterion: census rows A18–A19 converted; a clamped pair sums to
exactly 1.0 with its ratio preserved; `python -m pytest
tests/test_config_scratch_bridge.py tests/test_run_manifest_scratch_bridge.py
tests/test_scratch*.py -q` green.

- [ ] S6

## S7 — convert the intake cycles ceiling (§4.5) and check R18

`INTAKE_CYCLES_CEILING_EXCEEDED` → clamp to `PUBLIC_MAX_CYCLES`;
`error_catalog.py`'s entry rewritten. Flip T6, T7.

Done-criterion: census row A20 clamps; **and** a before/after diff of
`IntakeFormV1.model_json_schema()` is EMPTY (if non-empty, the four R18
pins + FORM_DR1 move in this same step); `python -m pytest
tests/test_intake_form.py tests/test_error_catalog.py tests/test_mcp.py
tests/test_mcp_help.py -q` green.

- [ ] S7

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

- [ ] S8

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

- [ ] S9

---

## Part B (starts only after S9 is green — R9)

## S10 — write `tests/test_seats_evidence_law.py` (R10–R13, R15)

Attack cases B1–B15 from SPEC §6. Docstring names the law verbatim and
this tranche. No pytest marks beyond `xfail` where R16 applies.

Done-criterion: `python -m pytest tests/test_seats_evidence_law.py -q`
green (or green-with-declared-xfail), and every assertion reads a typed
record object, never model output — proven by `grep -n` showing no
assertion on generated text.

- [ ] S10

## S11 — mutation proof (R14)

Disable `Harness._validate_warrant`'s rubric branch in a SCRATCH COPY of
the tree, run the new file, record RED; discard the copy; re-run against
the real tree, record GREEN.

Done-criterion: both runs pasted, RED then GREEN, with the exact mutation
diff shown.

- [ ] S11

## S12 — park anything Part B exposed (R16)

Any attack case that found a REAL hole: `xfail(strict=True)` + a
`PARKED.md` entry with a ready-to-send `deepreason-orchestrator` prompt.
If none, say so explicitly.

Done-criterion: `PARKED.md` written (P1 = `V6_LAUNCH_DISABLED` decision,
P2 = seat-binding notice threading, plus any Part B finding), and every
`xfail` in the new file points at a `PARKED.md` id.

- [ ] S12

## S13 — tranche boundary: full gate, wheel smokes, validation

Done-criterion: full gate 0 failed; `docs_verify` at baseline;
`python scripts/wheel_smoke.py` exit 0; `python -u
scripts/wheel_operational_smoke.py` exit 0 OR failing only at its
`reason` stage with "terminal verification is incomplete" (the parked
pre-existing flake). `VALIDATION.md` written.

- [ ] S13
