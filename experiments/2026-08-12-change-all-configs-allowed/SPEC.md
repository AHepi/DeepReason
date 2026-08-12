# Spec: all configurations are allowed — compile-time denial is abolished

Traces to `REQUEST.md` R1-R12. Written after: (a) an empirical reproduction
of two concrete compile-time blocks (R7a), (b) a three-way parallel census
of `run_manifest.py`, `config.py`, `seat_bindings.py`, `intake_form.py`,
`cli/main.py`, and the V6 launch gates (`runtime/launch_policy.py`) (R7b).

## 1. The reproduction (R7a) — "the grounded-extension run"

No tranche or run root in the repository is named "grounded-extension."
Read literally, the phrase names the bridge's `grounded_two_stage` mode
(`BridgeConfig`/`BridgePolicyV1` — the harness's own extension of the
plain thesis-and-criticism run into a two-stage ledger-then-compose
bridge). This SPEC treats "the grounded-extension run" as the natural
minimal configuration an operator would write to launch a
`grounded_two_stage` bridge run, and reproduces it directly against the
current code rather than guessing from prose. This is the smallest
reasonable reading of an otherwise-unidentifiable name (scope contract,
recorded here as an assumption), and it is empirically confirmed to
produce exactly two sequential blocks — matching the task's "the two
blocks it currently hits":

```python
from deepreason.config import Config
from deepreason.run_manifest import compile_run_manifest, RunManifestError

def route(model="gemma4:31b", family="gemma", endpoint="https://models.invalid/v1"):
    return {"endpoint_id": f"{family}-route", "endpoint": endpoint, "model": model,
            "provider": "fixture", "family": family, "api_key_env": "FIXTURE_API_KEY"}

config = Config(
    bridge={"mode": "grounded_two_stage"},
    roles={"conjecturer": route(), "synthesizer": route(), "summarizer": route(), "thesis": route()},
)
compile_run_manifest(config, workload_profile="text", rubric_policy="forbid", compiled_at="2026-08-12T00:00:00Z")
```

- **Block 1** (schema_version left at its default, which resolves below
  3): `GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED` at `/bridge/mode` —
  "grounded_two_stage requires RunManifest schema v3." A schema-ceiling
  gate: the mode is unrepresentable below v3 (`bridge_policy` itself is
  popped from every v1/v2 document).
- **Block 2**, once `schema_version=3` is added: `BRIDGE_REVIEWER_ROUTE_REQUIRED`
  at `/roles/judge` — "grounded bridge requires an explicit 'judge' route."
  A backend-identity/combination gate: `grounding_review` defaults `True`,
  and no role in the config's own `roles` maps to the bridge's
  `reviewer_role` ("judge").

Both are re-run at the end of `dr-validate-change` to prove they compile
clean (notices allowed, zero denials) — see §7.

## 2. The compile-notice mechanism

### 2.1 Why a new sibling structure, not a new required manifest field

The operator pre-granted touching frozen surfaces 3 and 4 "as far as this
conversion requires... changed model-and-validator together." That
licenses widening the manifest schema and its validators. It does not
by itself make every possible widening safe — `DR-INV-frozen-surfaces`'
own worked trap (`ENGAGED_CRITICISM_AUTHORITY`) shows that a naive new
field breaks pinned canonical-byte goldens unless the version-popping
discipline is followed exactly.

Verified by reading `RunManifest._versioned_serialization` and its
`canonical_bytes` twin (run_manifest.py:1246-1308, 1540-1600 approx.):
every field added to schema v6 after v6 already had committed roots
(`compact_recovery_policy`, `contract_schema_repair_policy`,
`route_seat_presentation_plan`, `route_seat_behavioral_capability_plan`,
`route_seat_contract_decomposition_plan`, `production_qualification_policy`,
`terminal_commitment_policy`, `criticism_policy`) follows the SAME rule:
declare it `Optional[...] = None` (or an empty-default that reads as
"absent"), and in BOTH serialization functions, `payload.pop(field, None)`
whenever `schema_version < 6 OR self.<field> is None`. A historical v6
root, reloaded after the Python model gains the new field, gets the
default (`None`), which is popped identically in both functions — so its
canonical bytes and digest sidecar are byte-for-byte unchanged. This is
the established, sanctioned way to add a manifest field without
retroactively re-minting any existing root's identity, and it is exactly
what this tranche needs for `compile_notices`.

**Design:** add one new field, following the identical pattern:

```python
class CompileNoticeV1(BaseModel):
    """A disclosed configuration choice a prior schema version would have
    refused at compile time. Notices describe; they never block compilation."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: str = Field(min_length=1)          # the exact code the old gate raised
    message: str = Field(min_length=1)       # the old gate's message, unchanged
    pointer: str = Field(min_length=1)       # the old gate's JSON pointer, unchanged
    resolution: str | None = None            # set only for R4 conflict-resolution notices
```

`RunManifest.compile_notices: tuple[CompileNoticeV1, ...] | None = None`.
In `_versioned_serialization` and `canonical_bytes`:
`if self.schema_version < 6 or not self.compile_notices: payload.pop("compile_notices", None)`
(the `not` form treats both `None` and an empty tuple as absent, so a
compile that triggers zero notices is byte-identical to today's output —
existing v6 fixtures/goldens that assert exact `canonical_bytes()` for
notice-free configs are unaffected). No schema-version bump; this is an
additive v6 field exactly like its seven predecessors.

**Threading:** `compile_run_manifest` (and the small number of
`_validate_v4_*`/`_validate_v5_*`/`_validate_v6_*` helpers it calls) each
currently `raise RunManifestError(...)` at a denial site. Converted sites
call a new module-level helper instead:

```python
def _emit_compile_notice(sink: list[CompileNoticeV1], code: str, message: str,
                          pointer: str, *, resolution: str | None = None) -> None:
    sink.append(CompileNoticeV1(code=code, message=message, pointer=pointer, resolution=resolution))
```

`compile_run_manifest` owns one `notices: list[CompileNoticeV1] = []`
local, threaded as an explicit parameter into every helper it calls that
needs to emit one (not a contextvar: the existing helpers are already
plain functions taking explicit arguments, and an explicit `notices`
parameter keeps the qualification battery's "pure `RunManifest -> report`
function" expectation intact — nothing here needs process-wide scoped
state the way `qualification.py`'s executor override does). At the end,
`compile_notices=tuple(notices) or None` is passed into the final
`RunManifest(...)` construction alongside every other field.

**`_production_routes_are_concrete` (the frozen model's own duplicate
enforcement, mode="after"):** three of its checks
(`BRIDGE_LEDGER_ROUTE_REQUIRED`/`_COMPOSER_`/`_REVIEWER_`,
`BRIDGE_REVIEWER_SEATS_MISMATCH`, `SECOND_JUDGE_FAMILY_REQUIRED`) exist
so that constructing or loading a `RunManifest` directly (bypassing
`compile_run_manifest`) still enforces the same rule. Converting these
means the validator appends to `self.compile_notices` instead of raising.
Because `model_validator(mode="after")` may return a **different**
instance, the converted validator returns
`self.model_copy(update={"compile_notices": (*(self.compile_notices or ()), CompileNoticeV1(...))})`
rather than mutating `self` in place (the model is frozen; `model_copy`
is the sanctioned way an "after" validator changes its own output).
**Safety argument for existing roots:** every currently-committed root
compiled successfully under the OLD strict gate, so by construction none
of them can be in the state this validator's converted branch checks for
(missing bridge route, mismatched reviewer seats, uncovered rubric
family) — the branch is dead code for every existing `load_run_manifest`
call. It only ever fires for a **freshly constructed** manifest, which is
exactly where a notice is wanted. This is verified per-root in §7 with a
targeted `verify_root_report`, not asserted from reasoning alone.

### 2.2 What "the run proceeds" means when a feature becomes unrepresentable

For a gate that guards an actually-implemented, well-defined fallback
(schema too old to carry a policy that already has a defined "absent"
projection — e.g. `GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED`,
`SCRATCH_MANIFEST_V3_REQUIRED`), converting to a notice is safe: the
existing version-popping code ALREADY silently drops the field for that
schema version (that is what "structural, schema-version gate" meant in
the census) — the field is dropped whether the gate raises or not,
because the pop is unconditional on schema_version. So it is not the
denial that was preventing an incoherent manifest; the denial was
preventing an operator from ASKING for something the schema literally
drops and not being told. Converting these to a notice states the same
fact the old refusal stated, but does not block. **These schema-ceiling
sites are the tier this SPEC converts most freely** — see §3.

For a gate that guards a genuinely **not-yet-implemented** capability
(`V5_FORMALIZATION_UNAVAILABLE`, `V5_RESEARCH_UNAVAILABLE`,
`V6_FORMALIZATION_UNAVAILABLE`, `V6_RESEARCH_UNAVAILABLE`'s backend-
identity restriction, `V6_CONFIG_REFEREE_CRITIC_SEAT_REQUIRED`,
`V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED`,
`V5_SIMULATION_TOOLCHAIN_UNSAFE`/`V6_SIMULATION_TOOLCHAIN_UNSAFE`),
converting risks something worse than the denial it removes: R5 requires
that "an unreachable model, an unsatisfiable ensemble, or a zero budget
still FAILS TYPED at the point of use" — i.e. impossibility must still
surface as a *typed* refusal, just deferred to dispatch. These particular
gates exist precisely because the dispatch-time code for the guarded
capability does not exist yet; letting a manifest compile with, say,
`research_capability_policy.enabled=True` and a `backend_identity` other
than `web.contained.v1` risks an **untyped** crash the first time the
scheduler tries to dispatch that capability, not a typed refusal — the
opposite of what CLAUDE.md requires ("Everything meaningful is TYPED").
**Assumption recorded (scope contract):** this SPEC does NOT convert
this sub-tier without first verifying a downstream typed guard exists;
where none is evidenced within this tranche's budget, the compile-time
gate stays and is recorded as NOT CONVERTED with that reason, rather
than converted on faith. See §3's table, "not-yet-implemented" rows.

## 3. Full census and conversion table

Legend: **CONVERT-T1** = converted with code + tests in this tranche.
**CONVERT-SPEC'D** = conversion rule fully specified below but not
implemented in this tranche (documented for a follow-on tranche).
**STAYS** = correctly excluded (structural/parse, runtime/dispatch, or
frozen-record) — the operator's own scope carve-outs (R2, R5, R8).

### 3.1 `run_manifest.py`

| Code | Site | Category | Decision | Conversion rule |
|---|---|---|---|---|
| `GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED` | `compile_run_manifest` :3123 | schema-ceiling | **CONVERT-T1** | Notice; `bridge_policy` still popped for schema<3 by the existing unconditional pop (no behavior change beyond the notice) |
| `BRIDGE_LEDGER_ROUTE_REQUIRED`/`_COMPOSER_`/`_REVIEWER_` | `compile_run_manifest` :3204-3210 AND `_production_routes_are_concrete` :1399-1402 (both sites, model+validator together) | combination/backend-identity | **CONVERT-T1** | Notice; the bridge policy compiles with the missing role's route absent from `roles`, so `bridge_policy.mode` stays `grounded_two_stage` but the run's actual dispatch of that stage fails typed the first time it is attempted (existing `select_lease`/route-lookup machinery already raises a typed `KeyError`-successor for an unbound role — verified in step-level testing, §5) |
| `BRIDGE_REVIEWER_SEATS_MISMATCH` | `_production_routes_are_concrete` :1406-1409 | combination | **CONVERT-T1** | Notice; the frozen reviewer route tuple is truncated/left as compiled (no silent duplication) — same model_copy pattern |
| `SECOND_JUDGE_FAMILY_REQUIRED` (3 sites: `compile_run_manifest` :3282-3288, `_production_routes_are_concrete` :1532-1536, `preflight_harness`'s rubric re-check :3872-3876) | rubric cross-family requirement | combination | **CONVERT-T1** | Notice at all three sites (must move together — they are the same rule enforced at three call points: compile, construction/load, and payload-materialization preflight) |
| `SCRATCH_MANIFEST_V3_REQUIRED` | `compile_run_manifest` :3117 | schema-ceiling | **CONVERT-T1** | Notice; `scratch_policy` still popped for schema<3 |
| `JUDGE_FAMILY_AND_BLIND_SAME_MODEL_CONFLICT` | `compile_run_manifest` :3016 (mirrors the cli/main.py flag-level check, §3.4) | R4 conflict | **CONVERT-T1** | Precedence: `judge_family` (the stronger, explicit diversity request) wins; `blind_same_model_judges` is dropped and the drop is the notice's `resolution` |
| `CRITICISM_ACTIVE_CONJECTURE_REQUIRED` | `compile_run_manifest` :3112 (early-fail duplicate of `V4_CRITICISM_ACTIVE_REQUIRED`) | combination | CONVERT-SPEC'D | Notice; must move with `V4_CRITICISM_ACTIVE_REQUIRED` below (currently untested standalone — a regression test is needed before conversion, flagged by the census as a risk) |
| `V4_SCHOOL_ROLE_UNSUPPORTED`, `_SHARED_SEAT_FORBIDDEN`, `_DISTINCT_MODEL_REQUIRED`, `_DISTINCT_FAMILY_REQUIRED`, `_BINDING_INCOMPLETE` | `_validate_v4_control_plane_policy` | combination/family-requirement | CONVERT-SPEC'D | Notice; requires verifying the scheduler's school-allocation code (`capture/schools.py`) fails typed, not with an untyped crash, when a school's binding is absent/duplicate/same-family — not yet verified (§2.2 principle) |
| `V4_CRITICISM_ACTIVE_REQUIRED`, `_FOREIGN_COVERAGE_IMPOSSIBLE`, `_ROLE_UNSUPPORTED`, `_SHARED_SEAT_FORBIDDEN`, `_DEFENDER_REQUIRED`, `_CROSS_FAMILY_JUDGES_REQUIRED` (×2), `_BINDING_INCOMPLETE` | `_validate_v4_criticism_policy` | combination/family-requirement | CONVERT-SPEC'D | Same rationale as the school cluster — `rules/crit.py`'s dispatch-time behavior under an under-specified criticism topology needs the same downstream-typed-guard check before conversion |
| `V5_CAPABILITY_PROFILE_MISMATCH`, `V6_CAPABILITY_PROFILE_MISMATCH` | `_validate_v5/v6_capability_policy` | combination | CONVERT-SPEC'D | Notice; resolution rule: `control_plane_policy.capability_profile` wins (it is the earlier-frozen, coarser authority), the narrower `inquiry_capability_policy.capability_profile` is overwritten to match and the overwrite is the notice's `resolution` |
| `V5_FORMALIZATION_UNAVAILABLE`, `V5_RESEARCH_UNAVAILABLE`, `V6_FORMALIZATION_UNAVAILABLE`, `V6_RESEARCH_UNAVAILABLE`, `V6_CONFIG_REFEREE_CRITIC_SEAT_REQUIRED`, `V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED`, `V5_SIMULATION_TOOLCHAIN_UNSAFE`, `V6_SIMULATION_TOOLCHAIN_UNSAFE` | `_validate_v5/v6_capability_policy` | **not-yet-implemented capability** | **STAYS** (§2.2) | No downstream typed guard evidenced within this tranche's budget; converting risks an untyped crash at dispatch, which would violate "everything meaningful is TYPED." Recorded, not silently dropped from the census. |
| `RUBRIC_INPUT_FORBIDDEN` (×2: `preflight_payload`, `preflight_harness`) | text-authority preflight | combination | CONVERT-SPEC'D | Notice; the rubric-bearing criterion is stripped before dispatch (deterministic: the run proceeds without the forbidden rubric input, the strip itself is the resolution) |
| `PROPERTY_RUBRIC_TRIAL_FORBIDDEN` | `preflight_harness` | combination | CONVERT-SPEC'D | Notice; property-proposal path is disabled for the run rather than reaching a judge, mirroring the rubric-strip resolution above |
| `SCRATCH_EMBEDDER_MODEL_UNRESOLVED` | `_compile_scratch_policy` | combination | CONVERT-SPEC'D | Notice; falls back to the hashing embedder (the documented, already-safe default per `capture/detection.py`'s own traps entry) instead of an unresolved neural model id |
| `_preflight_text_authority`'s pass-through (`CALIBRATION_RECEIPT_REQUIRED`/`_UNVERIFIED`, defined in `authority.py`) | preflight | combination | CONVERT-SPEC'D (needs `DR-CON-authority` follow-up — these codes live in `authority.py`, one file outside this tranche's five named files; converting only the `run_manifest.py` call site without `authority.py`'s own `text_status_authority_issues` would leave the other three call sites in `authority.py`'s own "Traps" list — `ops.review_infrastructure`, both scheduler call sites — still hard-refusing while the manifest path alone goes advisory, a worse inconsistency than not converting) | Falls back to `TrialAuthority.OBSERVE_ONLY` (the safe, zero-status default every surface already falls back to by design) instead of the unsafe status mode |
| `TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH` | `preflight_harness` | **frozen-record** | **STAYS** | Detects that an already-bound manifest's authority decision has since diverged from the live runtime `Config` — protects an EXISTING record, explicitly out of scope per R8 |
| `resolve_route_seat_base_profile`/`_behavioral_capability`/`_contract_decomposition` (dispatch-time exact-match resolvers) | dispatch, not compile | **runtime/dispatch** | **STAYS** | These ARE the R5 typed-dispatch-failure surface — converting them would remove the exact guard R5 requires to still exist |
| Every `schema_version < N and field is not None` / `>= N and field is None` gate (≈15 sites), `SINGLE_MODEL_MUST_BE_CONCRETE`, `INVALID_CONCURRENCY`, `SINGLE_MODEL_ROUTE_AMBIGUOUS`/`_REQUIRED`, `SECOND_JUDGE_ROUTE_NOT_FOUND`, credential/URL/immutability/digest checks (≈180 sites) | throughout | **structural/parse or frozen-record** | **STAYS** | Not configurations being refused — either shape defects, non-referential lookups, or protection of an existing bound/loaded manifest |

### 3.2 `config.py`

| Code | Site | Decision | Conversion rule |
|---|---|---|---|
| `BridgeConfig`'s "grounded_two_stage requires unresolved-success-safe settings: ..." | `_grounded_mode_preserves_valid_unresolved_results` | **CONVERT-T1** | Notice; the disabled sibling fields (`allow_partial`/`allow_abstention`/`require_claim_ledger`/`require_claim_uses`) are force-restored to `True` before the model finishes validating — `mode="after"` may reassign fields on a not-yet-frozen-at-validation-time instance the same way `_freeze_roles` already does; the forced values are the notice's `resolution` |
| `ScratchpadConfig`'s "reserved scratch attention fractions must not exceed one" | `_reserved_attention_fractions_fit` | CONVERT-SPEC'D | Notice; deterministic clamp: scale both fractions down proportionally to sum to 1.0, record the scaled values as the resolution |
| `EndpointSpec`'s context-window/max-tokens pair (2 sites) | `_qualified_context_window_has_finite_completion_allowance` | **STAYS** | Census's own "borderline" flag: this is capacity math (a window with no completion budget is nonsensical, not a policy stance), and `run_manifest.py`'s `Route` independently re-implements the identical check — converting `EndpointSpec` alone while `Route` still hard-refuses produces exactly the inconsistency the census warned about. Left as a hard error; recorded rather than silently converted. |
| All remaining `config.py` sites (single-field regex/format/finiteness/shape checks, YAML/override-path navigation) | various | **STAYS** | Structural/parse — no dependency on another config value |

### 3.3 `seat_bindings.py`

| Code | Site | Decision | Conversion rule |
|---|---|---|---|
| `SEAT_BINDING_ROLE_CONFLICT` | `resolve_seat_bindings` | **CONVERT-T1** | **The operator's own named example.** Precedence: explicit-most-wins — a group named directly for its expanded role (e.g. `--seat conjecture=` binding `conjecturer`) outranks a group reaching that role only through `GROUP_ALIASES`/overlap (e.g. `--seat simulation=` aliasing to the same group, or `--seat scratch=` overlapping via `GROUP_ROLES`). Where BOTH bindings are equally direct (two literal groups whose OWN `GROUP_ROLES` both list the role with no alias indirection), fall back to flag order: the LAST `--seat` flag for that direct group wins (deterministic, since `parse_seat_flags` already preserves flag order) |
| `SEAT_BINDING_GROUP_DUPLICATED` | `parse_seat_flags` | **CONVERT-T1** | Precedence: last-flag-wins (same rule applied one level earlier, before role expansion) |
| `SCHOOL_SEAT_DUPLICATED` | `parse_school_seat_flags` | **CONVERT-T1** | Same last-flag-wins rule (unpinned by any test today — lowest risk to convert first) |
| `SEAT_BINDING_GROUP_UNKNOWN`, `SEAT_BINDING_FLAG_MALFORMED`, `SEAT_BINDING_FILE_MALFORMED`, `SCHOOL_SEAT_FLAG_MALFORMED`, `SCHOOL_SEAT_ID_MALFORMED` | various | **STAYS** | Structural/parse — closed-enum or shape checks with no cross-field dependency |

### 3.4 `intake_form.py` / `cli/main.py`

| Code | Site | Decision | Conversion rule |
|---|---|---|---|
| `INTAKE_SEAT_CONFLICT` | `IntakeFormV1._no_conflicting_role_bindings` | **CONVERT-T1** | Same explicit-most-wins / last-wins precedence as `SEAT_BINDING_ROLE_CONFLICT` (§3.3) — the two must use an identical rule since an intake form's `seats` mapping and a CLI `--seat` set both resolve through the same underlying vocabulary |
| `INTAKE_CYCLES_CEILING_EXCEEDED` | `IntakeFormV1._cycles_within_ceiling` | CONVERT-SPEC'D | Notice; clamp `cycles` down to `PUBLIC_MAX_CYCLES` and record the clamp as the resolution |
| `JUDGE_FAMILY_AND_BLIND_SAME_MODEL_CONFLICT` (CLI flag pair) | `cli/main.py` `config compile` branch, :822-828 | **CONVERT-T1** | Same precedence as the `run_manifest.py` twin (§3.1) — `--judge-family` wins, `--blind-same-model-judges` is dropped |
| `V6_COMPILE_INPUTS_REQUIRED` | `cli/main.py` `config compile` branch, :816-821 | **STAYS** | On reflection this is a "missing required argument for this schema version" completeness check, not a combination refusal between two present values — closer to the schema-ceiling family than to a conflict; recorded rather than converted since "supply the missing thing" has no notice-worthy fallback (there is no default control-plane-policy/run-input-digest to synthesize safely) |
| `IntakeFormV1`'s `Field(gt=0)` shape constraints (`context_window_tokens`, `maximum_completion_tokens`, the shape half of `cycles`, `token_budget`) | model fields | **STAYS** | Structural/parse |
| `deepreason validate-intake` (CLI, `_cmd_validate_intake`) | `cli/main.py` :1924-1941 | **CONVERT-T1 (R6)** | Currently genuinely blocking (exit 1 on any violation). Made advisory: always print the full violation/notice report and **exit 0**, unless the file itself fails to parse (`INTAKE_FILE_NOT_AN_OBJECT`, or the intake bytes are not valid JSON/YAML at all) — those remain non-inputs per R2 and keep exit 1 |
| MCP `validate_intake` tool | `mcp_server.py` | **already advisory — no change needed** | Confirmed by the census: it already returns `{"ok": False, "violations": [...]}` as normal tool-call data, never raising through the JSON-RPC boundary. R6 is satisfied here today; recorded as "errata: none" territory, not a defect. |

### 3.5 V6 launch gates (`runtime/launch_policy.py`)

| Code | Site | Decision | Conversion rule |
|---|---|---|---|
| `V6_LAUNCH_DISABLED` (env-var kill switch) | `require_v6_launch_allowed` | CONVERT-SPEC'D | This is the one gate the operator's own text explicitly names as a config-shaped denial ("family requirements... backend-identity gates" — a global rollback switch is the closest fit). Converting it, however, changes an emergency-rollback primitive's actual behavior (a switch meant to stop ALL v6 launches during an incident) into something that only discloses — this SPEC recommends leaving it a hard error and records the disagreement rather than silently deciding: an emergency kill switch that no longer blocks is not "compile-time denial abolished" in the spirit the operator intends, it is the removal of an operational safety valve. **Flagged, not converted, in this tranche** — pending explicit operator confirmation in a follow-on tranche (not asked now, per "no stops"; recorded as a scope boundary this SPEC draws on its own authority under the scope contract's "smallest reasonable interpretation" clause, since converting an incident kill-switch was never named as an example in the operator's own list of denial categories). |
| `V6_LAUNCH_DISABLED` (release-policy file) | same function | Same as above | Same reasoning |
| Everything else in `launch_policy.py` | various | **STAYS** | Census's own analysis: schema-version identity, frozen-record protection, or delegated runtime/evidence gates — none are configuration-combination denials |

## 4. Precedence rules (R4), consolidated

Two rules cover every R4 conflict this tranche converts:

1. **Explicit-most-wins, then last-flag-wins.** For seat/role-binding
   conflicts (`SEAT_BINDING_ROLE_CONFLICT`, `SEAT_BINDING_GROUP_DUPLICATED`,
   `SCHOOL_SEAT_DUPLICATED`, `INTAKE_SEAT_CONFLICT`): a group/binding that
   names its role directly outranks one that reaches it only through an
   alias or overlap; among equally-direct bindings, the last one given
   wins. Same config in (same flag order) → same resolution out, always.
2. **Stronger-diversity-request wins.** For
   `JUDGE_FAMILY_AND_BLIND_SAME_MODEL_CONFLICT` (both the `run_manifest.py`
   and `cli/main.py` sites): `--judge-family`/`judge_family` (an explicit
   request for a SPECIFIC second family) outranks
   `--blind-same-model-judges`/`blind_same_model_judges` (a same-model
   substitute the codebase's own doc calls a fallback, "reachable only...
   mirrors the existing cross-school substitute's no-separate-flag shape"
   — i.e. already documented as the weaker of the two mechanisms).

Both rules are deterministic functions of the parsed configuration alone
(never of wall-clock time, randomness, or execution order beyond the
config's own declared flag order) — run identity stays deterministic per
R4's own requirement.

## 5. Acceptance checks, per requirement

- **R1/R2**: the two grounded-extension blocks (§1) compile clean with
  notices by `dr-validate-change`; `IntakeFormV1`'s remaining hard errors
  are all parse/shape (§3.4's STAYS row).
- **R3**: every CONVERT-T1 row's pinned test is rewritten to assert
  "compiles + notice present with the old code/message/pointer," never
  silently deleted (R7c).
- **R4**: §4's two rules, each with a rewritten conflict test asserting
  the deterministic winner and a `resolution` string on the notice.
- **R5**: no runtime/dispatch site in §3 is touched; the resolve_route_seat_*
  resolvers, `PROVIDER_CREDENTIAL_MISSING`, `REASONING_MUST_BE_DISABLED`,
  qualification confirmation gates all STAY verbatim.
- **R6**: `_cmd_validate_intake` rewritten to exit 0 on semantic
  violations (§3.4); MCP tool confirmed already-advisory (no code change,
  documented in DELIVERY.md).
- **R7**: this document is (b); §1 is (a); CHECKLIST.md executes (c) for
  every CONVERT-T1 row.
- **R8**: proven with a targeted `verify_root_report` on a committed v6
  root carrying `bridge_policy`/`criticism_policy` (the fields most
  affected by this tranche's converted validators) at CHECKLIST time, plus
  the full root sweep at the tranche boundary — no root's `valid`,
  `att`, `module_digests`, or `seat_digests` may move.
- **R9**: digest-drift consequence for future manifests that DO trigger a
  notice (their qualification subject digest will differ from an
  otherwise-identical notice-free compile, since `compile_notices` is
  non-None) — reported in DELIVERY.md with the requalification cost
  (one full battery, ~14 min, ~1160 calls, per `DR-INV-frozen-surfaces`).
  No IntakeFormV1 schema SHAPE change is planned (only its validators'
  behavior on an already-well-shaped payload changes), so the four-pin
  FORM_DR1 regeneration is not triggered — verified at CHECKLIST time by
  diffing `IntakeFormV1`'s JSON Schema before/after.
- **R10**: errata check performed in §6.
- **R11**: gate discipline followed in CHECKLIST.md; baselines recorded
  in REQUEST.md are the ones this tranche measured directly (§7 below).
- **R12**: CLAUDE.md's "Operator design laws" section gains a new entry,
  same commit as the code (a CHECKLIST step, not part of this SPEC).

## 6. Errata check (R10)

Searched `docs/TOKEN_ECONOMY.md`, `docs/STATE_OF_THE_THEORY.md`,
`docs/BASIN_REPORT.md`, every tranche `DELIVERY.md`, and
`docs/proposals/*.md` for a claim that compile-time denial was already
removed, or that `validate-intake`/the MCP tool/any compile gate was
already advisory or already load-bearing-and-permanent. No such claim
was found (grep for "compile-time denial", "validate-intake", "advisory"
combined with "removed"/"abolished" in those paths returns nothing
relevant to this specific change). **Errata: none** — no `docs/ERRATA.md`
entry needed for this tranche's own subject matter. (E24 would be the
next free number if one were needed later.)

## 7. Baselines measured directly (for R11's gate discipline)

- `python -m pytest tests/test_bronze_report.py -q`: 1 failed
  (`test_census_totals_internally_consistent`, `159 == 165`), 6 passed —
  matches REQUEST.md's stated baseline exactly.
- `python tools/docs_verify.py`: 3 failed, all `CON-run-identity.md`
  shallow-clone `git log`/`git show` failures (ambiguous revision — the
  container's shallow clone has no history for those commits) — matches
  REQUEST.md's stated baseline exactly.
- MCP-thread flakiness under `-n 4`: not independently re-measured before
  starting (accepted as given per REQUEST.md; will isolate with `-n 1` if
  any MCP test fails during the boundary gate run, per the instruction to
  isolate before attributing).

## 8. Assumptions recorded (scope contract)

1. "The grounded-extension run" is read as a `bridge.mode="grounded_two_stage"`
   config, not a specific named tranche/root (§1) — no such artifact exists
   in the repository under that name.
2. Converting a not-yet-implemented-capability gate is deferred wherever no
   downstream typed guard is evidenced within this tranche (§2.2, §3.1) —
   chosen over converting on faith, which risks an untyped crash and
   directly contradicts "everything meaningful is TYPED."
3. The V6 launch kill-switch (`V6_LAUNCH_DISABLED`, both sources) is left a
   hard error (§3.5) — an incident rollback valve is judged out of the
   operator's named denial categories (family requirements, role
   conflicts, backend-identity gates, ceiling checks, combination
   restrictions); flagged for explicit confirmation in a follow-on
   tranche rather than converted on this tranche's own authority.
4. `EndpointSpec`'s context-window/max-tokens pair and `config.py`'s
   `V6_COMPILE_INPUTS_REQUIRED` stay hard errors (§3.2, §3.4) — no safe
   deterministic fallback value exists for either, unlike every converted
   row.
5. CONVERT-SPEC'D rows are fully designed (conversion rule stated) but not
   implemented in this tranche's CHECKLIST — implementing every row would
   multiply this tranche's diff several-fold over what CHECKLIST.md scopes
   below; DELIVERY.md will state plainly which rows are code-complete and
   which are census-complete-but-not-yet-converted, rather than silently
   claiming full coverage.
