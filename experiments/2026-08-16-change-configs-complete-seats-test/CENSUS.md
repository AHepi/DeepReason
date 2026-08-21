# CENSUS — every all-configs-allowed denial site, final state

Satisfies REQUEST.md **R8**. This file is **Part B's declared input**: the
"configuration shape now admitted" column is the attack list Part B draws
from (R11).

Derived by running `census_probe.py` before and after the conversion
(`census-before.txt`, `census-after.txt`), both committed beside this file.

## Summary

| | count |
|---|---|
| Sites that refused or crashed on the tranche base | **21** (A1–A21) |
| Converted by this tranche | **21** |
| Already converted by an intervening tranche (`already-done`) | **1** (A22) |
| Deliberately left refusing, re-parked for an operator decision | **1** (A23) |
| Distinct notice CODES now emitted where a refusal used to fire | **20** |

The 20 codes: `V4_SCHOOL_ROLE_UNSUPPORTED`, `V4_SCHOOL_BINDING_INCOMPLETE`,
`V4_SCHOOL_SHARED_SEAT_FORBIDDEN`, `V4_SCHOOL_DISTINCT_MODEL_REQUIRED`,
`V4_SCHOOL_DISTINCT_FAMILY_REQUIRED`, `CRITICISM_ACTIVE_CONJECTURE_REQUIRED`,
`V4_CRITICISM_ACTIVE_REQUIRED`, `V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE`,
`V4_CRITICISM_ROLE_UNSUPPORTED`, `V4_CRITICISM_BINDING_INCOMPLETE`,
`V4_CRITICISM_SHARED_SEAT_FORBIDDEN`, `V4_CRITICISM_DEFENDER_REQUIRED`,
`V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED`, `V5_CAPABILITY_PROFILE_MISMATCH`,
`V6_CAPABILITY_PROFILE_MISMATCH`, `RUBRIC_INPUT_FORBIDDEN`,
`SECOND_JUDGE_FAMILY_REQUIRED`, `PROPERTY_RUBRIC_TRIAL_FORBIDDEN`,
`SCRATCH_EMBEDDER_MODEL_UNRESOLVED`, `V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED`
— plus one NEW code, `V6_CONTRACT_DECOMPOSITION_ROUTE_REQUIRED`, minted for
a site that had no typed refusal at all (it crashed with a bare `IndexError`).

Two sites resolve WITHOUT a notice, because the surface they live on carries
no manifest and therefore no `compile_notices` sink; the resolved value is
the disclosure, exactly as the 2026-08-12 tranche left `INTAKE_SEAT_CONFLICT`:
`ScratchpadConfig`'s attention fractions (clamped) and `IntakeFormV1.cycles`
(clamped). `_compile_scratch_policy` DOES emit
`SCRATCH_RESERVED_ATTENTION_FRACTIONS_EXCEED_ONE` when the manifest is
compiled from an unclamped source.

## The table

Legend for **Part B**: ✔ = this shape touches seat binding, school routing,
criticism policy, judge roles, or scratch, and is therefore on Part B's
attack list.

| # | Site | Old outcome (base `5f648ebc9`) | New outcome | Configuration shape now admitted | Resolution (R4) | Point-of-use guard | Part B |
|---|---|---|---|---|---|---|---|
| A1 | `_validate_v4_control_plane_policy` | refused `V4_SCHOOL_ROLE_UNSUPPORTED` | compiles + notice | a school binding naming a role other than `conjecturer` | none needed | `SCHOOL_ROUTE_ROLE_UNSUPPORTED` (typed) | ✔ B1 |
| A2 | same | refused `V4_SCHOOL_BINDING_INCOMPLETE` | compiles + notice | `N_SCHOOLS=k` with fewer/more school→conjecturer bindings than `k` | none needed | `SCHOOL_ROUTE_BINDING_MISSING` (typed) | ✔ B2 |
| A3 | same | refused `V4_SCHOOL_SHARED_SEAT_FORBIDDEN` | compiles + notice | `allow_shared=False` **and** two bindings on one seat | **bindings win**; `resolution` names the shared seats | both schools resolve to the SAME lease | ✔ B3 |
| A4 | same | refused `V4_SCHOOL_DISTINCT_MODEL_REQUIRED` | compiles + notice | `require_distinct_models=True` with two bound schools on one model | **bindings win**; `resolution` names the shared model | — | ✔ B4 |
| A5 | same | refused `V4_SCHOOL_DISTINCT_FAMILY_REQUIRED` | compiles + notice | `require_distinct_families=True` with two bound schools on one family | **bindings win**; `resolution` names the shared family | `require_cross_family_judge_ensemble` still refuses a single-family judge matrix | ✔ B4 |
| A6 | `compile_run_manifest` | refused `CRITICISM_ACTIVE_CONJECTURE_REQUIRED` | compiles + notice | a `criticism_policy` under a control mode that never dispatches criticism | none needed | no criticism transaction is ever created | ✔ B5 |
| A7 | `_validate_v4_criticism_policy` | refused `V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE` | compiles + notice | `minimum_foreign_school_coverage > N_SCHOOLS-1` | **none invented** — the field is `ge=1`, so a clamp to zero is unrepresentable; the notice states the arithmetic | `V4_CRITICISM_FOREIGN_COVERAGE_UNSATISFIED` (typed) | ✔ |
| A8 | same | refused `V4_CRITICISM_ROLE_UNSUPPORTED` | compiles + notice | a criticism binding naming a role other than `argumentative_critic` | none needed | `SCHOOL_ROUTE_ROLE_UNSUPPORTED` (typed) | ✔ B6 |
| A9 | same | refused `V4_CRITICISM_BINDING_INCOMPLETE` | compiles + notice | criticism bindings not covering the school roster exactly | none needed | `SCHOOL_ROUTE_BINDING_MISSING`, and `SCHOOL_ROUTE_CRITIC_ROLE_MISSING` when no critic seat exists at all | ✔ |
| A10 | same | refused `V4_CRITICISM_SHARED_SEAT_FORBIDDEN` | compiles + notice | `allow_shared=False` with two critic bindings on one seat | **bindings win** | one lease serves both schools | ✔ B3 |
| A11 | same | refused `V4_CRITICISM_DEFENDER_REQUIRED` | compiles + notice | `authority="defended_trial"` with no `defender` route | none needed | `informal/trial.py` `_block("no-defender-role")` — a typed logged no-op, zero warrants | ✔ B7 |
| A12 | same (2 raises) | refused `V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED` | compiles + notice | `defended_trial` with <2 judge seats, or 2+ seats sharing a family without being the same model | none needed | `JudgeEnsemblePolicyError` before any judge call | ✔ B8 |
| A13 | `_validate_v5_capability_policy` | refused `V5_CAPABILITY_PROFILE_MISMATCH` | compiles + notice | inquiry `capability_profile` ≠ control-plane profile at schema 5 | **control plane wins**; the inquiry policy is rewritten and the overwrite is the `resolution` | — | |
| A14 | `_validate_v6_capability_policy` | refused `V6_CAPABILITY_PROFILE_MISMATCH` | compiles + notice | same at schema 6 | **control plane wins** | — | |
| A15 | `preflight_payload` | refused `RUBRIC_INPUT_FORBIDDEN` | returns notice | a rubric standard/criterion under `rubric_policy="forbid"` | **none — the payload is NOT mutated**; preflight is read-only over the operator's input | `Harness._validate_warrant` §2/§3: a rubric-derived warrant with no conforming trial transcript is refused (FROZEN surface) | ✔ B9 |
| A16 | same | refused `SECOND_JUDGE_FAMILY_REQUIRED` | returns notice | rubric input with <2 frozen judge families | none needed | `require_cross_family_judge_ensemble` (typed) | ✔ B10 |
| A17 | `preflight_harness` | refused `PROPERTY_RUBRIC_TRIAL_FORBIDDEN` | returns notice | property-proposal path enabled alongside a `program:property_oracle` criterion under `forbid` | none needed | the property path's judge call is ensemble-gated | ✔ B11 |
| A17b | `preflight_harness` | refused `RUBRIC_INPUT_FORBIDDEN` | returns notice | a resumed root whose materialized criteria contain a `rubric:` eval under `forbid` | none needed | `_validate_warrant`, as A15 | ✔ B9 |
| A18 | `_compile_scratch_policy` | refused `SCRATCH_EMBEDDER_MODEL_UNRESOLVED` | compiles + notice | `semantic_retrieval` on with an unresolved `EMBEDDER_MODEL` | **falls back to `deterministic_hashing`**, model dropped to `None` | — (the fallback is implemented, not deferred) | ✔ B12 |
| A19 | `ScratchpadConfig` + its `ScratchPolicy` mirror | refused "reserved scratch attention fractions must not exceed one" | compiles, clamped | `exploratory_fraction + underexposed_fraction > 1.0` | **proportional clamp** to sum exactly 1.0, ratio preserved; BOTH mirrors move together | — | ✔ B12 |
| A20 | `IntakeFormV1._cycles_within_ceiling` | refused `INTAKE_CYCLES_CEILING_EXCEEDED` | compiles, clamped | `cycles > PUBLIC_MAX_CYCLES` | **clamp to the ceiling** | — | |
| A21 | `_compile_route_seat_contract_decomposition_plan` **and** `_route_seat_behavioral_contract_assignments` | **crashed untyped** (`IndexError`) | compiles + notices | a grounded-bridge v6 manifest whose bridge stage roles carry no frozen route | **grant omitted from the plan**, disclosed per skipped grant | `resolve_route_seat_contract_decomposition` / `resolve_route_seat_behavioral_capability` refuse typed with no fallback | ✔ B13 |
| A22 | `_preflight_text_authority` | already converted 2026-08-13 | **already-done** | text-status-authority issues under a `text` workload | falls back to `OBSERVE_ONLY` | — | |
| A23 | `runtime/launch_policy.py::require_v6_launch_allowed` | refuses `V6_LAUNCH_DISABLED` | **STAYS** | — | — | — | |

## What deliberately still refuses (R5's boundary)

Not a gap; the law's own carve-out. Pinned from the other side by
`tests/test_all_configs_allowed_remainder.py`:

- **Shape / parse errors.** `V4_SCHOOL_COUNT_INVALID`,
  `V4_ENGINE_CONFIG_INVALID`, `V4_SCHOOL_BINDING_DUPLICATE`,
  `V4_CRITICISM_BINDING_DUPLICATE`,
  `SCRATCH_EMBEDDER_FAILURE_POLICY_INVALID`, every single-field
  regex/format/finiteness check in `config.py`, `IntakeFormV1`'s `Field(gt=0)`
  bounds. These are not configurations.
- **Dangling references.** `V4_SCHOOL_UNKNOWN`, `V4_SCHOOL_ROLE_UNKNOWN`,
  `V4_SCHOOL_SEAT_OUT_OF_RANGE`, `V4_CRITICISM_SCHOOL_UNKNOWN`,
  `V4_CRITICISM_SEAT_OUT_OF_RANGE`, `SECOND_JUDGE_ROUTE_NOT_FOUND`. There is
  nothing to disclose: the named thing does not exist.
- **Frozen-record protection.** `V4_SCHOOL_ENDPOINT_MISMATCH`,
  `V4_CRITICISM_ENDPOINT_MISMATCH`,
  `TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH`,
  `V6_ROUTE_SEAT_PRESENTATION_PLAN_MISMATCH`, every digest/immutability check.
- **Not-yet-implemented capabilities.** `V5/V6_FORMALIZATION_UNAVAILABLE`,
  `V5/V6_RESEARCH_UNAVAILABLE`, `V6_CONFIG_REFEREE_CRITIC_SEAT_REQUIRED`,
  `V5/V6_SIMULATION_TOOLCHAIN_UNSAFE`, `V5_SIMULATION_TOOLCHAIN_REQUIRED`.
  Converting these trades a typed compile refusal for an untyped runtime
  crash, which is the opposite of what the law asks for.
- **Version-completeness checks.** `V5/V6_CAPABILITY_POLICY_REQUIRED`,
  `V5_ACTIVE_INQUIRY_REQUIRED`, `V6_TRANSACTIONAL_INQUIRY_REQUIRED`,
  `V6_COMPILE_INPUTS_REQUIRED`, `RUN_INPUT_DIGEST_REQUIRED`. A missing
  required part, not a refused combination.
- **Runtime/dispatch.** Every `resolve_route_seat_*` resolver,
  `PROVIDER_CREDENTIAL_MISSING`, `REASONING_MUST_BE_DISABLED`,
  qualification confirmation. These ARE the point-of-use surface the law
  requires to keep existing.
- **The v6 launch kill switch** (A23), re-parked — see `PARKED.md` P1.
