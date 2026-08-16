# SPEC — Part A: finish the conversion. Part B: pin the seats/evidence law.

Traces to `REQUEST.md` R1–R26. Written after the fresh census (R2,
`census-before.txt`, reproduced by `census_probe.py`) and after the
downstream-typed-guard verification §2 records.

Map ids in scope: `DR-SUB-manifest`, `DR-CON-schools`,
`DR-CON-criticism-source`, `DR-CON-seats`, `DR-CON-authority`,
`DR-SUB-scratch`, `DR-SEAM-manifest-x-schools`,
`DR-SEAM-adjudication-x-authority`, `DR-INV-frozen-surfaces`.

---

## 1. The fresh census (R2) — pasted proof

`python experiments/2026-08-16-change-configs-complete-seats-test/census_probe.py`
run against the tranche base (`5f648ebc9`), output verbatim in
`census-before.txt`:

```
A1 V4_SCHOOL_ROLE_UNSUPPORTED                                  | REFUSES              | ValidationError: V4_SCHOOL_ROLE_UNSUPPORTED
A2 V4_SCHOOL_BINDING_INCOMPLETE                                | REFUSES              | ValidationError: V4_SCHOOL_BINDING_INCOMPLETE
A3 V4_SCHOOL_SHARED_SEAT_FORBIDDEN                             | REFUSES              | ValidationError: V4_SCHOOL_SHARED_SEAT_FORBIDDEN
A4 V4_SCHOOL_DISTINCT_MODEL_REQUIRED                           | REFUSES              | ValidationError: V4_SCHOOL_DISTINCT_MODEL_REQUIRED
A5 V4_SCHOOL_DISTINCT_FAMILY_REQUIRED                          | REFUSES              | ValidationError: V4_SCHOOL_DISTINCT_FAMILY_REQUIRED
A6 CRITICISM_ACTIVE_CONJECTURE_REQUIRED (compile_run_manifest) | REFUSES              | RunManifestError: CRITICISM_ACTIVE_CONJECTURE_REQUIRED
A7 V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE                    | REFUSES              | ValidationError: V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE
A8 V4_CRITICISM_ROLE_UNSUPPORTED                               | REFUSES              | ValidationError: V4_CRITICISM_ROLE_UNSUPPORTED
A9 V4_CRITICISM_BINDING_INCOMPLETE                             | REFUSES              | ValidationError: V4_CRITICISM_BINDING_INCOMPLETE
A10 V4_CRITICISM_SHARED_SEAT_FORBIDDEN                         | REFUSES              | ValidationError: V4_CRITICISM_SHARED_SEAT_FORBIDDEN
A11 V4_CRITICISM_DEFENDER_REQUIRED                             | REFUSES              | ValidationError: V4_CRITICISM_DEFENDER_REQUIRED
A12 V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED                  | REFUSES              | ValidationError: V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED
A13 V5_CAPABILITY_PROFILE_MISMATCH                             | REFUSES              | ValidationError: V5_CAPABILITY_PROFILE_MISMATCH
A14 V6_CAPABILITY_PROFILE_MISMATCH                             | REFUSES              | ValidationError: V6_CAPABILITY_PROFILE_MISMATCH
A15 RUBRIC_INPUT_FORBIDDEN (preflight_payload)                 | REFUSES              | RunManifestError: RUBRIC_INPUT_FORBIDDEN
A16 SECOND_JUDGE_FAMILY_REQUIRED (preflight_payload)           | REFUSES              | RunManifestError: SECOND_JUDGE_FAMILY_REQUIRED
A17 PROPERTY_RUBRIC_TRIAL_FORBIDDEN (preflight_harness)        | COMPILES (no notice) | 'raises_PROPERTY_RUBRIC_TRIAL_FORBIDDEN=True'
A17b RUBRIC_INPUT_FORBIDDEN (preflight_harness)                | COMPILES (no notice) | 'raise_count=3'
A18 SCRATCH_EMBEDDER_MODEL_UNRESOLVED                          | REFUSES              | RunManifestError: SCRATCH_EMBEDDER_MODEL_UNRESOLVED
A19 ScratchpadConfig reserved attention fractions              | REFUSES              | ValidationError: 1 validation error for Config scratchpad Value error, reserved scratch attention fractions must not exceed one
A20 INTAKE_CYCLES_CEILING_EXCEEDED                             | REFUSES              | ValidationError: INTAKE_CYCLES_CEILING_EXCEEDED
A21 V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED                      | CRASHES UNTYPED      | IndexError: tuple index out of range
A22 already-done? CALIBRATION_RECEIPT_* (_preflight_text_authority) | COMPILES (no notice) | 'raises=False'
A23 already-done? V6_LAUNCH_DISABLED (runtime/launch_policy.py) | COMPILES (no notice) | 'raises=True'
```

Reading of the three non-obvious rows:

- **A17 / A17b** are source inspections, not construction probes:
  `preflight_harness` already RETURNS `tuple[CompileNoticeV1, ...]`
  (the 2026-08-13 text-authority conversion gave it the return channel)
  but still carries 3 `raise RunManifestError` statements, of which two
  (`RUBRIC_INPUT_FORBIDDEN`, `PROPERTY_RUBRIC_TRIAL_FORBIDDEN`) are this
  tranche's; the third (`TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH`) is a
  frozen-record protection that STAYS. Their construction probes are the
  two pinned tests enumerated in §5.
- **A21 is the finding of this census.** The park (P2) predicted the
  grounded-bridge v6 shape would hit a typed
  `V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED`. It does not. It reaches
  `_compile_route_seat_contract_decomposition_plan`
  (`run_manifest.py:1781`, `route = manifest.roles[role][0]`) FIRST and
  dies with a bare `IndexError`. This is an **untyped compile-time
  crash** — neither a compile (the law's requirement) nor a typed
  refusal (CLAUDE.md's requirement). It is directly caused by the
  delivering tranche's own conversion of `BRIDGE_*_ROUTE_REQUIRED` to a
  notice: compilation now proceeds past the missing route and into an
  unguarded index. It is in Part A's scope and is fixed here, not parked.
- **A23 STAYS** (`V6_LAUNCH_DISABLED`). See §4.3.

**Site count: 21 of the parked remainder still refuse or crash on
current main (A1–A21). 1 is `already-done` (A22). 1 stays by recorded
decision pending an operator answer (A23).**

## 2. The §2.2 precondition, discharged (P1(a)'s explicit blocker)

The delivering tranche refused to convert the v4 school/criticism cluster
until someone verified the downstream fails TYPED rather than with an
untyped crash. That verification is done, by reading the dispatch code:

| Compile-time gate being converted | Downstream typed guard at the point of use | Evidence |
|---|---|---|
| `V4_SCHOOL_BINDING_INCOMPLETE`, `V4_CRITICISM_BINDING_INCOMPLETE` | `SchoolRouteResolutionError("SCHOOL_ROUTE_BINDING_MISSING")` | `llm/firewall.py:576`, `:556` |
| `V4_SCHOOL_ROLE_UNSUPPORTED`, `V4_CRITICISM_ROLE_UNSUPPORTED` | `SchoolRouteResolutionError("SCHOOL_ROUTE_ROLE_UNSUPPORTED")` | `llm/firewall.py:526` |
| any binding whose seat has no lease | `SchoolRouteResolutionError("SCHOOL_ROUTE_SEAT_UNAVAILABLE")` — wraps the `KeyError`/`IndexError` explicitly | `llm/firewall.py:588-594` |
| `V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE` | `ValueError("V4_CRITICISM_FOREIGN_COVERAGE_UNSATISFIED")` | `workflow/criticism.py:358` |
| `V4_CRITICISM_DEFENDER_REQUIRED` | `_block(harness, "no-defender-role", ...)` — a logged typed no-op, explicitly "not a mid-run KeyError crash" | `informal/trial.py:503-506`, `:894-896` |
| `V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED` (×2) | `JudgeEnsemblePolicyError` from `require_cross_family_judge_ensemble` | `llm/firewall.py:376-379`, called at `informal/trial.py:510` |
| `V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED` | `RunManifestError` from `resolve_route_seat_behavioral_capability` — "without fallback" | `run_manifest.py:2206-2231` |
| the A21 decomposition grant | `RunManifestError("V6_CONTRACT_DECOMPOSITION_AUTHORITY_REQUIRED")` from `resolve_route_seat_contract_decomposition` | `run_manifest.py:1842-1859` |
| `RUBRIC_INPUT_FORBIDDEN` (both sites), `PROPERTY_RUBRIC_TRIAL_FORBIDDEN` | `Harness._validate_warrant`'s §2/§3 guard: a warrant on a `rubric:` commitment without a CONFORMING TRIAL TRANSCRIPT raises `WellFormednessError` — unbypassable, and on a FROZEN surface | `harness.py:1979-1993` |
| `SCRATCH_EMBEDDER_MODEL_UNRESOLVED` | none needed — the resolution is the already-implemented `deterministic_hashing` backend, not a deferral | `run_manifest.py:2594-2596` |

**One gap found, and closed here.** `scheduler.py:1320` raises a BARE
`RuntimeError("manifest foreign criticism has no runtime critic role")`.
Converting `V4_CRITICISM_BINDING_INCOMPLETE` makes that line newly
reachable (today, a criticism policy with no critic route cannot compile,
because every binding's seat must index into `critic_routes`). An untyped
runtime crash is exactly what §2.2 forbids converting into, and the
all-configurations law itself says an unsatisfiable ensemble "still fails
TYPED at the point of use". This SPEC therefore types that one line —
`SchoolRouteResolutionError("SCHOOL_ROUTE_CRITIC_ROLE_MISSING", ...)`,
which is a `RouteFirewallError`, which is a `RuntimeError`, so every
existing catcher still catches it and no behavior other than the code
changes. This is not a runtime-behavior change under R6; it is giving an
existing failure a type.

## 3. The mechanism (unchanged from main — R3)

No new machinery. Everything converted uses what the delivering tranche
already built and this tranche does not touch:

- `CompileNoticeV1(code, message, pointer, resolution=None)`
  (`run_manifest.py:1167`) — frozen, `extra="forbid"`.
- `RunManifest.compile_notices: tuple[CompileNoticeV1, ...] | None`
  (`:1233`), popped from both serializations when `schema_version < 6 or
  not compile_notices` (`:1319`, `:1643`) — so a notice-free compile is
  byte-identical to today.
- `_emit_compile_notice(sink, ...)` for free-function sites that own a
  `notices` list (`compile_run_manifest`, `preflight_*`).
- `_emit_deduped(code, message, pointer)` + `object.__setattr__` inside
  `_production_routes_are_concrete` for model-validator sites, keyed on
  `(code, pointer)` so a `model_validate` round trip cannot double-record
  (`:1342-1352`, `:1586-1589`).

**Threading for the v4/v5/v6 helper validators.** `_validate_v4_control_plane_policy`,
`_validate_v4_criticism_policy`, `_validate_v5_capability_policy` and
`_validate_v6_capability_policy` are called from INSIDE
`_production_routes_are_concrete` (`run_manifest.py:1462-1506`), where
`_emit_deduped` is already in lexical scope. Each gains one keyword-only
parameter `emit` with a default that raises on absence-of-sink misuse:

```python
def _validate_v4_control_plane_policy(manifest, *, emit) -> None: ...
```

No contextvar, no global; the existing call sites pass `emit=_emit_deduped`.
`emit` gains an optional `resolution=` keyword (a one-line widening of
`_emit_deduped`, which currently constructs `CompileNoticeV1` without it)
so R4 resolutions are recordable from a validator.

## 4. Conversion table (R1, R3, R4, R5, R6)

Legend: **CONVERT** = becomes a notice in this tranche. **STAYS** =
structural/parse, dangling reference, frozen-record protection, or
runtime/dispatch (the R5/R6 surface). **ALREADY-DONE** = converted by an
intervening tranche; not re-converted (R2).

### 4.1 `run_manifest.py` — `_validate_v4_control_plane_policy` (school topology)

| Code | Decision | Configuration shape now admitted | Resolution rule (R4) |
|---|---|---|---|
| `V4_SCHOOL_ROLE_UNSUPPORTED` | CONVERT | a school binding naming a role other than `conjecturer` | none needed — no two config values contradict; the binding is retained verbatim in the frozen policy and resolves typed at dispatch (`SCHOOL_ROUTE_ROLE_UNSUPPORTED`) |
| `V4_SCHOOL_BINDING_INCOMPLETE` | CONVERT | `N_SCHOOLS=k` with fewer (or extra) school→conjecturer bindings than `k` | none needed — partial coverage is a config, not a contradiction; `SCHOOL_ROUTE_BINDING_MISSING` fires typed for an unbound school |
| `V4_SCHOOL_SHARED_SEAT_FORBIDDEN` | CONVERT | `allow_shared=False` together with two bindings on one seat | **R4 conflict. Bindings win.** The per-school bindings are the explicit, enumerated statement; `allow_shared` is the coarse switch. The bindings are kept as declared and the notice's `resolution` records `allow_shared=false overridden by explicit bindings; seats shared: <role[seat] list>` |
| `V4_SCHOOL_DISTINCT_MODEL_REQUIRED` | CONVERT | `require_distinct_models=True` with two bound schools on one model identity | **R4 conflict. Bindings win**, same rule and same `resolution` shape (`shared model: <identity>`) |
| `V4_SCHOOL_DISTINCT_FAMILY_REQUIRED` | CONVERT | `require_distinct_families=True` with two bound schools on one family | **R4 conflict. Bindings win** (`shared family: <family>`) |
| `V4_SCHOOL_COUNT_INVALID`, `V4_ENGINE_CONFIG_INVALID` | STAYS | — | shape/parse: `N_SCHOOLS` is not an integer, engine config is not JSON. Not configurations (R5) |
| `V4_SCHOOL_UNKNOWN`, `V4_SCHOOL_ROLE_UNKNOWN`, `V4_SCHOOL_SEAT_OUT_OF_RANGE` | STAYS | — | dangling references — the same class as `SECOND_JUDGE_ROUTE_NOT_FOUND`, which the delivering census already classed STAYS. Nothing to disclose: the named thing does not exist |
| `V4_SCHOOL_BINDING_DUPLICATE` | STAYS | — | shape: `SchoolExecutionPolicyV1._canonical_bindings` already refuses an unsorted/duplicated tuple at model level |
| `V4_SCHOOL_ENDPOINT_MISMATCH` | STAYS | — | frozen-record identity: the binding's `endpoint_id` disagreeing with the frozen seat is a corrupted record, not a policy choice (R8/frozen-surface carve-out) |

### 4.2 `run_manifest.py` — `_validate_v4_criticism_policy` + its compile twin

| Code | Decision | Configuration shape now admitted | Resolution rule (R4) |
|---|---|---|---|
| `CRITICISM_ACTIVE_CONJECTURE_REQUIRED` (`compile_run_manifest`) | CONVERT | a `criticism_policy` under a control mode that is neither `active_conjecture` nor `active_inquiry` | none needed — the criticism policy is compiled as given; a control mode that never dispatches foreign criticism simply never reaches it |
| `V4_CRITICISM_ACTIVE_REQUIRED` (validator twin) | CONVERT | same shape, reached through direct construction / `model_validate` | same |
| `V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE` | CONVERT | `minimum_foreign_school_coverage > max(0, N_SCHOOLS-1)` | none — the field is `ge=1`, so clamping to 0 is unrepresentable; the declared coverage is kept and `V4_CRITICISM_FOREIGN_COVERAGE_UNSATISFIED` fires typed at the point of use. The notice states the arithmetic (`coverage=k exceeds N_SCHOOLS-1=j`) |
| `V4_CRITICISM_ROLE_UNSUPPORTED` | CONVERT | a criticism binding naming a role other than `argumentative_critic` | none — typed at dispatch |
| `V4_CRITICISM_BINDING_INCOMPLETE` | CONVERT | criticism bindings not covering exactly the school roster | none — typed at dispatch |
| `V4_CRITICISM_SHARED_SEAT_FORBIDDEN` | CONVERT | `allow_shared=False` with two critic bindings on one seat | **R4 conflict. Bindings win**, identical rule to §4.1 |
| `V4_CRITICISM_DEFENDER_REQUIRED` | CONVERT | `authority="defended_trial"` with no `defender` route | none — `informal/trial.py` declines typed (`no-defender-role`) |
| `V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED` (both raises) | CONVERT | `authority="defended_trial"` with <2 judge seats, or 2+ seats sharing a family without being the exact same model | none — `JudgeEnsemblePolicyError` fires typed before any judge call |
| `V4_CRITICISM_BINDING_DUPLICATE`, `V4_CRITICISM_SCHOOL_UNKNOWN`, `V4_CRITICISM_SEAT_OUT_OF_RANGE`, `V4_CRITICISM_ENDPOINT_MISMATCH` | STAYS | — | shape / dangling reference / frozen-record identity, exactly as §4.1's mirrors |

### 4.3 `run_manifest.py` — v5/v6 capability profile, scratch, v6 plans

| Code | Decision | Configuration shape now admitted | Resolution rule (R4) |
|---|---|---|---|
| `V5_CAPABILITY_PROFILE_MISMATCH` | CONVERT | an `inquiry_capability_policy` whose `capability_profile` differs from the control plane's | **R4 conflict. Control plane wins** (it is the coarser, earlier-frozen authority — the delivering SPEC's own stated rule). The inquiry policy is replaced by `policy.model_copy(update={"capability_profile": control.capability_profile})` and the notice's `resolution` records `capability_profile overwritten <was> -> <now>` |
| `V6_CAPABILITY_PROFILE_MISMATCH` | CONVERT | same at schema 6 | same rule |
| `V5_FORMALIZATION_UNAVAILABLE`, `V5_RESEARCH_UNAVAILABLE`, `V6_FORMALIZATION_UNAVAILABLE`, `V6_RESEARCH_UNAVAILABLE`, `V6_CONFIG_REFEREE_CRITIC_SEAT_REQUIRED`, `V5/V6_SIMULATION_TOOLCHAIN_UNSAFE`, `V5_SIMULATION_TOOLCHAIN_REQUIRED` | STAYS | — | not-yet-implemented capability, §2.2 of the delivering SPEC. Re-checked here: no downstream typed guard was found for enabling a capability whose dispatch code does not exist. Converting would trade a typed compile refusal for an untyped runtime crash — the opposite of the law's own "still fails typed at the point of use". Recorded, not silently dropped |
| `V5_CAPABILITY_POLICY_REQUIRED`, `V6_CAPABILITY_POLICY_REQUIRED`, `V5_ACTIVE_INQUIRY_REQUIRED`, `V6_TRANSACTIONAL_INQUIRY_REQUIRED` | STAYS | — | completeness checks for a schema version (a missing required part, not a refused combination) — the same family as `V6_COMPILE_INPUTS_REQUIRED`, which the delivering census already classed STAYS |
| `SCRATCH_EMBEDDER_MODEL_UNRESOLVED` | CONVERT | `semantic_retrieval` on with `EMBEDDER_MODEL` set to an unresolved placeholder | **deterministic fallback.** `embedder_backend` becomes `deterministic_hashing` and `embedder_model` becomes `None` — the already-safe documented default. Notice `resolution`: `embedder falls back to deterministic hashing` |
| `SCRATCH_EMBEDDER_FAILURE_POLICY_INVALID` | STAYS | — | closed-enum shape check |
| `V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED` (`_route_seat_behavioral_contract_assignments`) | CONVERT | a v6 manifest whose behavioral contract assignment names a role/seat with no frozen route | **deterministic skip.** The grant is omitted from the plan; the notice names the contract and the missing `role[seat]`. `resolve_route_seat_behavioral_capability` then refuses typed at dispatch |
| `_compile_route_seat_contract_decomposition_plan`'s `manifest.roles[role][0]` (A21, currently `IndexError`) | CONVERT | the same shape, one step earlier | **deterministic skip**, identical rule; the notice uses code `V6_CONTRACT_DECOMPOSITION_ROUTE_REQUIRED` (a NEW code — the site had none, because it was never a typed refusal) |
| `V6_ROUTE_SEAT_PRESENTATION_PLAN_MISMATCH` and the remaining `schema_version < N` field gates | STAYS | — | frozen-record protection and structural version gates; the delivering census's ≈180-site STAYS block, unchanged |
| `TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH` | STAYS | — | protects an already-bound record (R8) |
| `CALIBRATION_RECEIPT_REQUIRED` / `_UNVERIFIED` | **ALREADY-DONE** | — | converted 2026-08-13; `_preflight_text_authority` contains no `raise` (census A22) |

### 4.4 `run_manifest.py` — the two preflight functions

| Code | Decision | Configuration shape now admitted | Resolution rule (R4) |
|---|---|---|---|
| `RUBRIC_INPUT_FORBIDDEN` (`preflight_payload`) | CONVERT | a payload carrying a rubric standard/criterion under `rubric_policy="forbid"` | none — **the payload is NOT mutated.** Preflight is read-only over the operator's input; silently stripping a criterion would change what the run is about. The law's own point-of-use guard is `Harness._validate_warrant`: a rubric-derived warrant without a conforming trial transcript is refused on a frozen surface |
| `SECOND_JUDGE_FAMILY_REQUIRED` (`preflight_payload`) | CONVERT | rubric input with fewer than two frozen judge families | none — `require_cross_family_judge_ensemble` refuses typed before any judge call |
| `RUBRIC_INPUT_FORBIDDEN` (`preflight_harness`) | CONVERT | a resumed root whose materialized criteria contain a `rubric:` eval under `forbid` | same as above |
| `PROPERTY_RUBRIC_TRIAL_FORBIDDEN` (`preflight_harness`) | CONVERT | property-proposal path enabled alongside a `program:property_oracle` criterion under `forbid` | none — the property path's own judge call is gated by the same typed ensemble guard |

**Signature change (P1(c)'s stated blocker).** `preflight_payload`
currently returns `None`, so it has no channel for a notice. It gains
`-> tuple[CompileNoticeV1, ...]`, exactly mirroring `preflight_harness`,
which already returns notices. The manifest it receives is frozen and is
NOT modified. Every caller is updated in the same commit; callers that
ignore the return value keep compiling unchanged.

### 4.5 `config.py` and `intake_form.py`

| Site | Decision | Configuration shape now admitted | Resolution rule (R4) |
|---|---|---|---|
| `ScratchpadConfig._reserved_attention_fractions_fit` (`config.py:187`) | CONVERT | `exploratory_fraction + underexposed_fraction > 1.0` | **deterministic proportional clamp**: both fractions multiplied by `1.0 / (e + u)`, so they sum to exactly 1.0 and their ratio is preserved. Applied in a `mode="before"` validator so the constructed model already holds the normalized pair |
| `ScratchPolicy._resolved_policy_is_consistent`'s mirror of the same rule (`run_manifest.py:357`) | CONVERT | same | **the same clamp, by the same shared helper.** Moving one side and not the other is exactly the inconsistency the delivering census warned about for `EndpointSpec`/`Route`; both move together. `_compile_scratch_policy` emits the notice (it owns the sink), with `resolution` recording `<e>,<u> -> <e'>,<u'>` |
| `IntakeFormV1._cycles_within_ceiling` | CONVERT | `cycles > PUBLIC_MAX_CYCLES` | **deterministic clamp** to `PUBLIC_MAX_CYCLES`. `IntakeFormV1` has no manifest and no notice sink; the clamp is the disclosure, mirroring how the delivering tranche left `INTAKE_SEAT_CONFLICT` (validator returns a resolved value, `error_catalog.py`'s entry rewritten to describe the new behavior). **R18 check:** the ceiling lives only in the validator, not in a `Field` constraint, so `IntakeFormV1.model_json_schema()` must not move — this is verified by diffing the schema before/after, and the four pins are touched only if it does |
| `EndpointSpec`'s context-window/max-tokens pair | STAYS | — | capacity arithmetic, and `Route` re-implements it; the delivering SPEC's assumption 4, re-affirmed |
| every remaining `config.py` regex/format/finiteness/shape check | STAYS | — | structural/parse (R5) |

### 4.6 `runtime/launch_policy.py`

| Site | Decision |
|---|---|
| `V6_LAUNCH_DISABLED` (env kill switch, release-policy file) | **STAYS — re-parked, needs an operator answer.** The delivering tranche's P3 recorded this as genuinely undecidable without the operator: an incident rollback valve that no longer blocks is not "compile-time denial abolished", it is the removal of an operational safety valve, and the operator's own list of denial categories (family requirements, role conflicts, backend-identity gates, ceiling checks, combination restrictions) does not name it. R26 says no stops, so this tranche does not stop to ask; it records the same decision the delivering tranche made, re-parks it in `PARKED.md`, and does not convert on its own authority |

### 4.7 Seat-binding notices (the delivering tranche's P4)

Out of Part A's scope, and re-parked. The three seat-binding conflicts
are **already converted** (`SEAT_BINDING_ROLE_CONFLICT`,
`SEAT_BINDING_GROUP_DUPLICATED`, `SCHOOL_SEAT_DUPLICATED` resolve
deterministically and no longer refuse) — R2 rows them `already-done`.
What P4 asks for is not a denial conversion but notice THREADING from
`seat_bindings.py` through `preparation.py`, whose blast radius the
delivering tranche explicitly declined to measure. Re-parked with that
reason.

## 5. Tests pinning an old refusal, enumerated BEFORE any is touched (R7)

Derived by grepping every converted code across `tests/`. Each row states
what the test asserts today and what it asserts after.

| # | Test | Today | After |
|---|---|---|---|
| T1 | `tests/test_run_manifest_v4.py::test_route_bound_fails_closed_when_one_school_binding_is_missing` | `pytest.raises(..., match="V4_SCHOOL_BINDING_INCOMPLETE\|...")` | compiles; `compile_notices` contains `V4_SCHOOL_BINDING_INCOMPLETE`. Renamed `..._discloses_a_missing_school_binding` |
| T2 | `tests/test_run_manifest_v4.py::test_route_bound_rejects_invalid_binding_topology[V4_SCHOOL_SHARED_SEAT_FORBIDDEN]` | one parametrize case raising | that case moves OUT of the parametrize list into its own test asserting compile + notice + `resolution`. The other four cases (`V4_SCHOOL_UNKNOWN`, `V4_SCHOOL_ROLE_UNKNOWN`, `V4_SCHOOL_ENDPOINT_MISMATCH`, `V4_SCHOOL_BINDING_DUPLICATE`) STAY raising — they are §4.1 STAYS rows |
| T3 | `tests/test_run_manifest.py::test_rubric_forbid_rejects_rubric_input_before_runtime` | `preflight_payload` raises `RUBRIC_INPUT_FORBIDDEN` | returns a notice tuple containing `RUBRIC_INPUT_FORBIDDEN`; renamed `..._discloses_rubric_input_before_runtime` |
| T4 | `tests/test_run_manifest.py::test_materialized_rubric_reference_is_preflighted_on_resume` | `preflight_harness` raises `RUBRIC_INPUT_FORBIDDEN` | returns a notice tuple containing it |
| T5 | `tests/test_run_manifest.py::test_property_proposal_rubric_path_fails_before_any_model_call` | raises `PROPERTY_RUBRIC_TRIAL_FORBIDDEN` | returns a notice tuple containing it; renamed `..._is_disclosed_before_any_model_call` |
| T6 | `tests/test_intake_form.py::test_cycles_over_ceiling_raises` | `ValidationError` naming `INTAKE_CYCLES_CEILING_EXCEEDED` | `IntakeFormV1(cycles=PUBLIC_MAX_CYCLES+1).cycles == PUBLIC_MAX_CYCLES`; renamed `test_cycles_over_ceiling_clamps` |
| T7 | `tests/test_error_catalog.py` | asserts `INTAKE_CYCLES_CEILING_EXCEEDED` is a real, catalogued code | unchanged as an assertion; the CATALOG ENTRY's prose is rewritten to describe the clamp, exactly as `INTAKE_SEAT_CONFLICT`'s was |

**Tests that must NOT move** (they pin the runtime guards R6 protects,
and Part B leans on them): `tests/test_judge_ensemble_boundary.py:142`,
`tests/test_prose_refutation_boundaries.py:440,883,1383` (all
`JudgeEnsemblePolicyError`), and `tests/test_manifest_integration.py:87`
(already asserting a notice). `tests/test_v6_nonconjecture_recovery.py`
and `tests/test_v6_manifest_defended_trial.py` name the v4 criticism codes
only in prose comments explaining why their fixtures are shaped as they
are; their assertions do not touch them, so their comments are updated
and nothing else.

**New tests** (not flips): one per converted site that had NO pinning
test — A1, A4, A5, A6/A7/A8/A9/A10/A11/A12, A13, A14, A16, A18, A19, A21
— gathered in `tests/test_all_configs_allowed_remainder.py`, each
asserting compile + the expected notice code (+ `resolution` where §4
states one).

## 6. Part B — the adversarial seats/evidence test (R9–R16)

Runs only after Part A's full gate is green (R9).

**File:** `tests/test_seats_evidence_law.py`. Module docstring names the
law verbatim and this tranche (R10).

**The mechanism the law actually rests on**, located during §2's
downstream sweep and the thing the test asserts against (R13):

1. `Harness._validate_warrant` (`harness.py:1979`) — a warrant on a
   `rubric:` commitment MUST carry a `trace_ref` resolving to a
   `conforming_transcript`; otherwise `WellFormednessError`. This is the
   unbypassable "prose cannot become evidence without the trial" rule.
   It sits on a FROZEN surface, so the test may only read it.
2. `require_cross_family_judge_ensemble` / `require_cross_school_judge_ensemble`
   (`llm/firewall.py`) — the judge ensemble is validated from IMMUTABLE
   LEASES before any judge call; `JudgeEnsemblePolicyError` otherwise.
3. `informal/trial.py`'s `_block`/`_decline` — a missing critic, defender
   or judge role produces a typed logged no-op, never a warrant.
4. `resolve_school_route` (`llm/firewall.py:495+`) — a seat may only be
   reached through a manifest-frozen binding; nine typed refusal codes.
5. `scratch` is declared `advisory_non_grounding` — scratch-authored
   content is not admissible as grounding.

**Attack list (R11).** Every census shape from §4 that touches seat
binding, school routing, criticism policy, judge roles, or scratch —
each must COMPILE (Part A's promise) and then be shown NOT to yield
evidence status:

| # | Attack (the configuration a seat could hide behind) | Census row | Assertion |
|---|---|---|---|
| B1 | school binding naming a non-conjecturer role | A1 | compiles; `resolve_school_route` refuses typed |
| B2 | incomplete school binding roster | A2 | compiles; `SCHOOL_ROUTE_BINDING_MISSING` typed |
| B3 | two schools sharing one seat under `allow_shared=False` | A3 | compiles; both resolve to the SAME lease — one seat cannot masquerade as two independent critics |
| B4 | `require_distinct_families` overridden by bindings | A5 | compiles; `require_cross_family_judge_ensemble` still refuses a single-family judge matrix |
| B5 | criticism policy under a control mode that never dispatches criticism | A6 | compiles; no criticism transaction is recorded, and no warrant appears |
| B6 | criticism binding naming a non-critic role | A8 | compiles; typed refusal at dispatch |
| B7 | `defended_trial` with no defender route | A11 | compiles; trial `_block`s with `no-defender-role`; zero warrants, zero attack edges |
| B8 | `defended_trial` with a single-family judge matrix | A12 | compiles; `JudgeEnsemblePolicyError` before any judge call |
| B9 | rubric payload under `rubric_policy="forbid"` | A15 | compiles; preflight returns a NOTICE — and a rubric-derived warrant without a conforming transcript is still refused by `_validate_warrant` |
| B10 | rubric input with one judge family | A16 | compiles; notice; ensemble guard still refuses |
| B11 | property-proposal rubric path under `forbid` | A17 | compiles; notice; the judge call is still ensemble-gated |
| B12 | scratch enabled with clamped attention fractions | A19 | compiles; the scratch policy stays `advisory_non_grounding` — a scratch block cannot become a warrant's validity node |
| B13 | v6 behavioral grant for an unbound seat | A21 | compiles with a notice; `resolve_route_seat_behavioral_capability` refuses typed — no ungranted seat may act |
| B14 | seat-binding role conflict resolved by precedence (the already-done row) | §4.7 | the resolved winner is a GENERATION seat binding only; the criticism seat file is separate and unaffected |
| B15 | previously-constructible shape from `proof/goal-L2.txt`: `criticism-seat-bindings.yaml` present/absent vs `resolve_criticism_seats` | audit L2 | a generation-side seat binding cannot supply a criticism seat |

Cases B1–B15 assert TYPED RECORD facts only: `harness.state.warrants`,
attack edges, `WellFormednessError`, `SchoolRouteResolutionError`,
`JudgeEnsemblePolicyError`, trial `_block`/`_decline` diagnostics, and
`compile_notices`. No model output is read (R13).

**Mutation proof (R14).** In a scratch copy of the tree (never the
repo), `Harness._validate_warrant`'s rubric branch is disabled, the file
is run, and the run recorded RED; the copy is discarded and the same file
re-run GREEN against the real tree. Both outputs are pasted into
`VALIDATION.md`.

**Real violations (R16).** Any case that exposes a genuine current hole
becomes an `xfail(strict=True)` with a pointer to a new `PARKED.md` entry
carrying a ready-to-send `deepreason-orchestrator` prompt. It is not
fixed here.

## 7. Acceptance checks, per requirement

- **R1/R2**: `census_probe.py` re-run after Part A — every A1–A21 row
  reads `COMPILES+NOTICE` except the STAYS rows §4 names; A22/A23 rows
  unchanged. `census-after.txt` committed beside `census-before.txt`.
- **R3**: every converted row's notice carries the OLD code, message and
  pointer unchanged.
- **R4**: §4's resolution rules, each with a test asserting the
  deterministic winner AND the `resolution` string.
- **R5**: §4's STAYS rows re-probed and still refusing.
- **R6**: no dispatch-time resolver is weakened; the single
  `scheduler.py:1320` change gives an existing failure a type and is
  argued in §2.
- **R7**: §5's table, executed row by row in `CHECKLIST.md`.
- **R8**: `CENSUS.md`, generated from the post-conversion probe.
- **R9–R16**: §6.
- **R18**: `IntakeFormV1.model_json_schema()` diffed before/after; the
  four pins move only if it moves.
- **R20**: `compile_notices` being non-`None` changes a manifest's
  canonical bytes and therefore its qualification subject digest — but
  ONLY for a configuration that previously could not compile at all.
  Every previously-compilable configuration is byte-identical (the
  `not self.compile_notices` pop). Reported in `DELIVERY.md`, not a stop.
- **R21/R22/R23/R24**: `CHECKLIST.md`.

## 8. Baselines measured directly (R21)

Measured on the tranche base before any edit; recorded in
`CHECKLIST.md` step 0 and re-compared at the boundary.

## 9. Assumptions recorded (scope contract)

1. **A21's untyped `IndexError` is in scope, not parked.** It is the
   exact configuration P2 named, at the exact site P1(c)/P2 asked to be
   investigated, and leaving it would ship a conversion whose own
   configuration crashes untyped. Cross-routing parks defects that are
   NOT the tranche's subject; this one is.
2. **`scheduler.py:1320` is typed, not parked**, for the reason §2 gives:
   the conversion makes it newly reachable, and shipping a newly-reachable
   untyped crash violates the very principle (§2.2) that gated this work.
3. **Rubric payloads are disclosed, not stripped.** The delivering SPEC
   proposed stripping; this SPEC does not, because preflight is read-only
   over the operator's own input and because the frozen
   `_validate_warrant` guard already makes the strip unnecessary. Recorded
   as a deliberate departure from the delivering SPEC's stated rule.
4. **`V6_LAUNCH_DISABLED` stays** (§4.6), re-parked rather than converted
   or asked about, because R26 forbids a stop.
5. **P4 is not a denial conversion** (§4.7) and is re-parked.
