# Spec for: seat-binding design — Rung S2 of role-seat separation
Traces: every item cites R/C numbers. Untraceable items are bugs.

Map preflight (per `dr-change-orchestrator`, done before any design
reasoning below): `docs/map/INDEX.md` resolves this work to
`DR-CON-seats` (the concept this rung extends),
`DR-SUB-manifest` (`RunManifest` schemas/validators — frozen surface
4), `DR-SUB-llm` (`select_lease`, `EndpointLease`, `LLMAdapter`), and
`DR-INV-frozen-surfaces` (read in full before this document was
written — its five surfaces are the fixed reference frame for every
"frozen contact" verdict below). No `SEAM-*.md` names both "seats" and
"manifest" today; `DR-CON-seats`'s own `Seams:` header already points
at `DR-SEAM-llm-x-manifest`/`DR-SEAM-llm-x-rules` for the underlying
mechanism, which is where this design's actual contact (or lack of it)
must be checked against, not a new seam document (out of scope, C1).

## Measurement index (SM-numbers; cites CENSUS.md M-numbers where reused)

This section is the evidence base every later "priced"/"rejected"
claim points back to. All facts below were re-verified against the
live tree in this session (either directly or via a dedicated
read-only research pass); each SM is not an argument, it is something
that was actually run or read.

**SM1 — `Config.roles` is already typed for heterogeneous per-role
endpoints, not a single shared one.**
```
$ sed -n '530,533p' src/deepreason/config.py
    roles: dict[
        str,
        dict[str, Any] | list[dict[str, Any]] | None,
    ] = Field(default_factory=dict)
```
Nothing in this type, or in its validator (`config.py:535-551`),
requires every role's dict to be equal. `_config_for_profile`
(`preparation.py:263-277`, the ONE place every canonical role gets its
route today per `CON-seats.md`) simply happens to write the same
`dict(endpoint)` into every slot — that is a choice made at that call
site, not a constraint of the type it is populating.

**SM2 — `RunManifest.roles` and `compile_run_manifest`'s grouped
branch already build per-role-independent `Route`s; no schema or
validator change is needed for heterogeneous roles.**
```
$ sed -n '1179p' src/deepreason/run_manifest.py
    roles: dict[str, tuple[Route, ...]]
$ sed -n '3155,3167p' src/deepreason/run_manifest.py
    else:
        grouped: dict[str, list[Route]] = {role: [] for role in role_names}
        grouped_specs: dict[str, list[dict[str, Any]]] = {
            role: [] for role in role_names
        }
        for role, _index, spec in _configured_seats(data):
            if role not in role_names:
                continue
            grouped.setdefault(role, []).append(
                _route_from_spec(spec, capability_cache=capability_cache)
            )
            grouped_specs.setdefault(role, []).append(spec)
        roles = {role: tuple(grouped.get(role, ())) for role in role_names}
```
This branch resolves a `Route` (`_route_from_spec`) independently per
`(role, seat)` from whatever `Config.roles` seat-spec it is handed —
it does not assume, anywhere in this code, that two roles share a
`Route`. This is CENSUS.md's own measured mechanism (the
"select_lease degrees of freedom" section): `select_lease` already
resolves a fully independent `Route` per `(role, seat)`; SM2 shows the
COMPILE side already builds that independence too, when given
heterogeneous `Config.roles` input.

**SM3 — presentation-profile per-seat variance is not hypothetical:
it already runs, today, for a different field on the same structure.**
```
$ sed -n '2285,2297p' src/deepreason/run_manifest.py
    for seat, (route, spec) in enumerate(zip(routes, specs, strict=True)):
        explicit = spec.get("model_profile")
        entries.append(
            RouteSeatPresentationGrantV1(
                role=role,
                seat=seat,
                endpoint_id=route.endpoint_id,
                base_profile=explicit or manifest_default,
                selection_basis=(
                    "explicit_endpoint"
                    if explicit is not None
                    else "manifest_default"
                ),
            )
        )
```
`EndpointSpec.model_profile` (`config.py:50`) is an existing per-seat
override field; when set, `selection_basis="explicit_endpoint"` is a
real, exercised code path, not dead type surface. The generalization
this spec needs (a per-role-GROUP provider identity, not just a
per-seat presentation override) is the same shape one level up.

**SM4 — the ONLY place that collapses every role to one identity is
`preparation.py:263-277` (already the CENSUS.md/CON-seats.md central
finding).** Re-cited, not re-measured:
```
roles={role: dict(endpoint) for role in V3_CANONICAL_ROLES}
```
`_config_for_profile` is called from exactly two places
(`build_preparation_manifest`'s two callers: `qualification_subject_manifest`,
used by `deepreason qualify`, and `RunPreparationService.prepare`,
used by `deepreason reason`/managed-run creation — `preparation.py:387-402`,
`529-591`). `deepreason setup` (`easy.py:408-511`, dispatched from
`cli/main.py:571-592`) never calls it — `setup` only mints and writes
ONE `ProviderProfileV1` to a single fixed `provider.yaml`
(`provider_profile.py:34`, `297-302`) and stops. `_config_for_profile`
runs two levels downstream, at qualify-time or run-prepare-time, not
at `setup` time itself.

**SM5 — the new-optional-field pattern for byte-safe manifest
additions is proven, used 7 times already.**
```
$ sed -n '1198,1207p' src/deepreason/run_manifest.py
    compact_recovery_policy: CompactRecoveryPolicyV1 | None = None
    contract_schema_repair_policy: ContractSchemaRepairPolicyV1 | None = None
    route_seat_presentation_plan: RouteSeatPresentationPlanV1 | None = None
    route_seat_behavioral_capability_plan: (
        RouteSeatBehavioralCapabilityPlanV1 | None
    ) = None
    route_seat_contract_decomposition_plan: (
        RouteSeatContractDecompositionPlanV1 | None
    ) = None
    production_qualification_policy: ProductionQualificationPolicyV1 | None = None
```
Each is popped identically in `_versioned_serialization`
(`run_manifest.py:1239-1301`, e.g. lines 1273-1276) and in
`canonical_bytes()` (`run_manifest.py:1522-1577`, e.g. lines
1559-1560) whenever `schema_version < 6` or the field is `None` — so
an old manifest's `.sha256` is provably unaffected by the field's mere
existence. This is the mechanism `INV-frozen-surfaces.md`'s governing
principle ("fix READERS so old roots stay valid") already relies on
for seven other fields.

**SM6 — a NEW `Config` field, if one is added, is NOT automatically
invisible to replay — `_versioned_source_config_data` must be told
about it explicitly, and skipping this has broken the gate before.**
Per `INV-frozen-surfaces.md`'s own Traps section (quoted in full
there): `Config.ENGAGED_CRITICISM_AUTHORITY` broke
`test_v1_v2_v3_canonical_shapes_and_hashes_remain_byte_identical`
immediately, and a first fix scoped to `schema_version < 4` was itself
refuted by two more golden-hash tests failing at schema v5. The fix
had to pop the new key unconditionally, every schema version. This is
the one place a "just add a Config field, it's free" instinct is
wrong, and it is a real risk this spec's Option A must address
explicitly (see Option A pricing, Item S2).

**SM7 — the qualification subject digest already fully distinguishes
by profile identity and does not care whether the manifest it
digests has uniform or heterogeneous roles.**
```
$ sed -n '248,282p' src/deepreason/qualification.py
def qualification_subject_payload(
    manifest: RunManifest,
    profile: ProviderProfileV1,
) -> dict:
    ...
    behavior = manifest.model_dump(mode="json", by_alias=True)
    behavior.pop("compiled_at", None)
    behavior.pop("run_input_digest", None)
    pairs = tuple(
        {
            "pair_subject_digest": _pair_subject_digest(_pair_payload(pair)),
            **_pair_payload(pair),
        }
        for pair in production_contract_pairs(manifest)
    )
    return {
        "schema": "deepreason-qualification-subject.v1",
        "provider_profile": profile.identity_payload(),
        "provider_profile_digest": profile.profile_digest,
        "policy_preset_id": POLICY_PRESET_ID,
        "policy_preset_digest": engaged_policy_digest(),
        "manifest_behavior": behavior,
        "pair_inventory": pairs,
    }
```
This function takes whatever `manifest`/`profile` it is handed and
digests it whole — it contains no assumption that every role shares
one route. Qualifying profile A and profile B (bound to the same or
different roles) necessarily produces different `provider_profile`/
`provider_profile_digest`/`manifest_behavior`/`pair_inventory` values,
hence different subject digests — **qualifying A never silently
qualifies B**, confirming the plan's own claim ("each distinct profile
bound to any seat is its own qualification subject") from the digest
code itself, not merely from the plan's prose.

**SM8 — the qualification battery's case inventory is already
role/seat-tagged, so a role-scoped battery (if ever built) is a
filter, not a redesign.**
```
$ sed -n '57,88p' src/deepreason/cli/doctor.py
class ProductionContractPairV1(_DoctorRecord):
    ...
    role: str = Field(min_length=1, max_length=64)
    seat: int = Field(ge=0, le=1_023)
    endpoint_id: str = Field(min_length=1, max_length=256)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_id: str = Field(min_length=1, max_length=1_024)
    ...
```
`production_contract_pairs` (`cli/doctor.py:302-363`) builds this
tuple by walking `manifest.route_seat_behavioral_capability_plan.entries`
and pulling `route = manifest.roles[entry.role][entry.seat]` per
entry — every pair already carries its owning `(role, seat)`. Nothing
about qualifying a NARROWER set of roles requires new fields on this
type; it requires only (a) a manifest whose `roles` covers fewer role
names, and (b) filtering `production_contract_pairs`' output — both
additive, no schema change.

**SM9 (kill-risk 2) — pairs never cross-reference another role's
route; qualification is pinned to the seat it's actually testing.**
Confirmed from the same quoted loop in SM8: each `pair` is built from
exactly one `entry` (one `(role, seat, endpoint_id)`) and one `route =
manifest.roles[entry.role][entry.seat]` — there is no code path in
`production_contract_pairs` that reads a DIFFERENT role's route while
building a pair for role X. **Kill-risk 2 measured outcome: defused
by construction**, provided S3/S4 continue to qualify each distinct
bound profile against a manifest where that profile is (as today)
bound to every role the pass is meant to cover — i.e., do not attempt
a manifest that mixes "the profile under test" on some roles with
"other seats' bindings" on others for the SAME qualification pass,
which SM9 does not rule out contaminating (untested combination, not
measured, flagged as an explicit non-goal in Item S4 below).

**SM10 (kill-risk 3) — neither the token meter nor config_referee
assume single-model economics.**
```
$ sed -n '1,4p' src/deepreason/llm/budget.py
"""Token budgeting (spec §14: global budgets, generalized to the provider).

A TokenMeter is shared across all endpoints of a provider and enforces a
HARD ceiling with a locked reserve-settle protocol:
$ grep -n "model_id\|context_window\|single.model" src/deepreason/llm/budget.py
(no output)
$ grep -n "model_id\|context_window\|single.model" src/deepreason/referee.py
(no output)
```
`TokenMeter` counts raw tokens via a conservative `chars/3` estimate
before dispatch and reconciles against whatever the provider actually
reports after — "generalized to the provider" per its own docstring,
already model-agnostic, already shared across every endpoint a run
uses. `referee.py` (config_referee, the dynamic token-steering
critic) contains no reference to `model_id` or any per-model
assumption. **Kill-risk 3 measured outcome: defused.** Per-seat budget
ALLOCATION (giving conjecturer N tokens and coder M tokens
separately) is a distinct, separable feature nothing here requires —
the existing single per-run ceiling continues to be correct arithmetic
under heterogeneous models, since it sums real usage regardless of
source. Not needed for S2/S3; noted as a possible future refinement,
not a blocker (Item S8, out of scope).

**SM11 (kill-risk 1) — the manifest does NOT bind provider identity
too tightly for named profiles to stay out of it; SM1-SM3 already
demonstrate the opposite.** Restated as the kill-risk's own measured
answer: the fear was that `RunManifest`'s schema/validators would
force option (b)'s territory (a manifest-declared section) merely to
express per-role variance. SM1 (`Config.roles`' type) and SM2
(`compile_run_manifest`'s grouped branch) show per-role variance is
ALREADY expressible with zero manifest schema change — the tightness
the kill-risk worried about does not exist at this layer. **Kill-risk
1 measured outcome: defused for Option A specifically** (see Item S2);
it would be REAL for a hypothetical design that tried to express the
binding as manifest-native structure without reusing the existing
`Route`-per-seat machinery — which is exactly why Option B (Item S3)
is priced as touching frozen surface 4, on purpose, not by oversight.

**SM12 — continuation NEVER re-derives leases/routes from a live
`Config`/`ProviderProfileV1`; it is provably sourced from the
committed, hash-verified manifest alone.**
```
$ sed -n '415,431p' src/deepreason/application/text_runs.py
    def continue_run(
        self,
        intent: ContinueTextRunIntentV1,
        *,
        progress_callback: Callable[[dict], None] | None = None,
        credential_checker: Callable[[Any], list[str]] = missing_manifest_credentials,
    ) -> RunStartedV1:
        from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

        intent = ContinueTextRunIntentV1.model_validate(intent)
        root = Path(intent.root).resolve()
        manifest = load_run_manifest(root / MANIFEST_NAME)
        if (
            intent.expected_manifest_digest is not None
            and intent.expected_manifest_digest != manifest.sha256
        ):
            raise ValueError("CONTINUE_MANIFEST_MISMATCH")
$ sed -n '1459,1470p' src/deepreason/llm/adapter.py
    role_specs = (
        {
            role: (
                [route.endpoint_spec() for route in routes]
                if len(routes) > 1
                else routes[0].endpoint_spec()
            )
            for role, routes in run_manifest.roles.items()
            if routes
        }
        if run_manifest is not None
        else (config.roles or {})
    )
$ python3 -c "
import deepreason.application.models as m
print(list(m.ContinueTextRunIntentV1.model_fields.keys()))
"
['schema_', 'root', 'budget', 'expected_manifest_digest']
```
`ContinueTextRunIntentV1` has exactly 4 fields — a `schema_` version
marker, `root`, `budget`, `expected_manifest_digest` — no field through
which a live manifest or config could be injected even in principle. `build_adapter`'s
`config.roles` fallback (the `else` branch above) is only reachable
when `run_manifest is None`, and every continuation call site passes a
non-`None`, disk-loaded, hash-verified manifest. Three independent
typed refusals already guard mismatch:
`CONTINUE_MANIFEST_MISMATCH` (`text_runs.py:427-431`,
`runtime/continuation.py:372-373`), `RUN_MANIFEST_CONFLICT`
(`runtime/launch_policy.py:163-172`), and `MANIFEST_HASH_MISMATCH`
(`run_manifest.py:3645-3650`, fires on every `load_run_manifest` call
via its default `verify_hash=True`). `deepreason amend`
(`amendment/apply.py:359-554`) stages the PARENT epoch's identical
`canonical_bytes()` into the successor epoch — `parent_manifest_digest
== successor_manifest_digest` by construction (`apply.py:452-453`) —
never a re-bound manifest.

## Frozen-surface contact forecast (R8 — this is the section the spec
lives or dies on)

Per `docs/map/INV-frozen-surfaces.md`'s five named surfaces, evaluated
against the design this SPEC recommends (Option A, Item S2) and
against the rejected alternative (Option B, Item S3) so the contrast
is explicit, not assumed:

| Surface | Option A (setup-time named profiles, resolved pre-compile) | Option B (manifest-declared seat section) |
|---|---|---|
| 1. `capabilities/state.py` digests/event application | **none** — this design never touches capability proposal/work-order digesting; SM1-SM4 are entirely upstream of any capability event | **none** — same reasoning |
| 2. `harness.py` event application | **none** — no new event type, no change to append-only application order | **none** — same, a manifest field is read at compile/replay time, not applied as a log event |
| 3. Replay-validation record formats (`invariants.py`, `verification/`) | **none** — `verify_root` re-derives state from the log; nothing here changes what a seat binding IS after compile, only how many distinct `Route`s a manifest's `roles` happens to contain, which `verify_root` already tolerates (routes vary by role today, per CENSUS.md's `select_lease` measurement) | **none directly**, but a NEW typed record class (a `SeatBindingPlanV1` analog) would need its own replay-tolerant reader if any downstream verification ever inspects it — not automatic, must be built |
| 4. Manifest schemas AND validators (`run_manifest.py`) | **none** — SM1/SM2/SM3 show `Config.roles`→`RunManifest.roles`→`compile_run_manifest`'s grouped branch already accept and correctly compile heterogeneous per-role `Route`s; no new Pydantic model, no new field on `RunManifest`, no new validator | **real, by design** — a first-class "which profile bound which role-group" concept needs a new optional field (SM5's pattern makes this byte-safe for old roots) PLUS new validator cross-checks analogous to `_production_routes_are_concrete`'s existing re-derive-and-diff checks against the other three route-seat plans (`run_manifest.py:1458-1502`) — real new surface-4 code, not merely a value change |
| 5. Qualification subject digests (`qualification.py`) | **none in the digest FUNCTION** — SM7 shows `qualification_subject_payload` digests whatever manifest/profile it is given, with no assumption of uniform roles; what changes is ORCHESTRATION (how many distinct-profile manifests get qualified before a run may launch), which is Rung S4's explicitly scoped job per the plan, not S2/S3's | **none in the digest function either** — same SM7 reasoning applies regardless of binding surface, since the digest only ever sees the compiled `RunManifest` |
| Frozen-adjacent: `route_fingerprint` | **none** — untouched | **none** — untouched |
| Continuation identity (not one of the five, but load-bearing per R5) | **already enforced, zero new code** — SM12: continuation sources leases exclusively from the disk-loaded, hash-verified manifest; whatever Option A minted into `RunManifest.roles` at compile time is exactly what a later `continue` will reuse, with three existing typed refusals on any mismatch | **same** — SM12's mechanism is binding-surface-agnostic; ANY design that resolves bindings into concrete `Route`s at manifest-compile time inherits this guarantee for free, because it is the manifest-loading path that provides it, not anything specific to Option A |

**Verdict: Option A forecasts zero frozen-surface contact, and this
is a measured verdict (SM1, SM2, SM3, SM4, SM7, SM12), not an
assumption — exactly the shape rung 7's Option D forecast ("zero
frozen-surface contact... conditional on the placement decision").
Option B forecasts real, deliberate frozen-surface-4 contact** (a new
manifest field + new validator cross-checks), priced at roughly 150-300
lines by analogy to the smallest existing sibling
(`RouteSeatPresentationGrantV1`/`RouteSeatPresentationPlanV1`, ~35
lines of models plus their compile/validate call sites, scaled up
because a binding record needs a profile-identity payload the
presentation grant does not carry). Per this session's operator
instruction ("STOP: operator words required... for any
manifest/qualification contact before S3 plans anything" — REQUEST.md
C2), Option B is NOT ruled out by this spec; it is priced, and its
frozen-surface-4 contact is flagged for explicit operator sign-off
if chosen over Option A.

## Applying rung 7's placement law (R5)

Quoted verbatim from `experiments/2026-08-04-change-rung7-authority-as-declared-policy/SPEC.md`:

> "A policy consulted at MINT time is invisible to replay; a policy
> consulted at LABEL time reinterprets every recorded root. That
> single measured distinction is this spec's whole design."

Applied here: a seat binding must be resolved into a concrete `Route`
**at manifest-compile time** (mint time — the moment `Config.roles`
becomes `RunManifest.roles`, which then becomes immutable,
hash-sealed, and is the ONLY thing `select_lease`/continuation ever
reads per CENSUS.md and SM12) — never resolved lazily by a live lookup
consulted later (at call-dispatch time, or worse, re-consulted fresh
on `continue`). A hypothetical Option C — "seat bindings resolve
dynamically at call time from a live named-profile file, re-read on
every call or every continuation" — is the exact label-time mistake
the plan's own words warn against ("a continuation that silently swaps
a seat's model is the rung-7 label-time mistake wearing a new hat")
and is explicitly rejected here (Item S6), even though the plan never
named it outright, because it is the design a naive implementer would
reach for and rung 7's law rules it out on the same measured grounds
(SM5's law, SM12's continuation evidence) as it ruled out rung 7's own
label-time alternative.

Both Option A and Option B, as SPECIFIED (not as they could be
misimplemented), already satisfy this law: both resolve bindings to
concrete `Route`s at compile time, and SM12 shows continuation already
enforces "reuse exactly what was minted" regardless of which option
produced it. The law is therefore a DESIGN CONSTRAINT that both priced
options satisfy, not a discriminator between them — it discriminates
against the unnamed Option C instead.

## Items

S1 (R2, R6, R7): Price Option A — setup-time named profiles.
**Mechanism:** `deepreason setup` gains a form to bind named profiles
to role groups (exact CLI surface: `--seat conjecture=<profile-path>
--seat coder=<profile-path> --seat scratch=<profile-path> --seat
simulation=<profile-path>`, each value an explicit path resolved via
the ALREADY-EXISTING `resolve_provider_profile` explicit-path branch
(`provider_profile.py:305-333` — SM: "an operator can already
hand-maintain multiple profile YAML files at arbitrary paths and
select one via `--provider-profile`/`DEEPREASON_PROFILE`" from this
session's setup-CLI research; no new named-profile REGISTRY is
required, only accepting several such paths in one `setup` invocation
instead of one). Default (no `--seat` flags): every role group maps to
the single resolved profile — byte-identical to today's
`_config_for_profile` behavior, satisfying the plan's own default
clause verbatim.
**Where it hooks in:** `easy.setup_wizard`/CLI arg registration (to
accept the new flags and, per role-group name, resolve+persist which
profile path each group uses — persisted as a small mapping file
alongside `provider.yaml`, itself NOT manifest/replay territory);
`_config_for_profile`'s generalization (or a new sibling function next
to it) to build `Config.roles` from the resolved per-role-group
endpoints instead of one broadcast endpoint, using SM1's already-typed
heterogeneous shape; `build_preparation_manifest`'s call site to pass
the resolved mapping through. All three sit in `Config`/CLI/
`preparation.py` territory (SM1, SM2, SM4).
**Role-group -> role-name mapping:** "conjecture" = `conjecturer`,
`variator` (matches the plan's own gloss, ROLE_SEAT_SEPARATION_PLAN.md
line 37); "coder" = the roles/call sites CENSUS.md's M20/M22
(`experimenter`, `property_designer` — `rules/experiment.py`, the
call-site owner for `workloads/code.py`/`workloads/formal.py` per
CENSUS.md's Delegating-modules table) render; "scratch" = the roles
CENSUS.md's M41/M42 render (`conjecturer`/`synthesizer` for blocks,
`synthesizer` for links, `summarizer` for guides — all dispatched
through `scratch/authoring.py`'s `ScratchAuthoringService`); "simulation"
= the same conjecturer call sites as "conjecture" today (CENSUS.md
M18/M19, since capability-channel proposals are typed conjecturer
output per CENSUS.md's Delegating-modules row for
`capabilities/simulation.py`) — noting this makes "conjecture" and
"simulation" the SAME role set under the current architecture, a
real finding this spec surfaces rather than glossing: **the plan's
four named seat groups are not four disjoint role sets today**; S3
must decide whether "simulation" gets its own binding or is defined as
an alias of "conjecture" until a dedicated capability-authoring role
exists (out of scope for this SPEC to decide; flagged as Question Q1
below, since the two readings differ materially: aliasing costs zero
extra code, a dedicated distinction costs a new role/template).
**Frozen-surface contact:** none (see forecast table).
**Priced at:** roughly 80-150 changed/added lines (CLI arg parsing +
dispatch, `_config_for_profile` generalization, one small persisted
mapping format, tests) — small, no new manifest concept, no schema
migration.
accept: this pricing appears in SPEC.md with SM-cited evidence for
every "already exists" claim (SM1, SM2, SM3, SM4) and an explicit
line count estimate.

S2 (R2, R6, R7): Price Option A's ONE real risk — a NEW `Config`
field, if the persisted role-group->profile mapping needs to be
represented on `Config` itself (rather than resolved entirely before
`Config` construction, i.e. `_config_for_profile`'s generalized
sibling receiving an already-resolved `dict[role, EndpointSpec]` and
never exposing "which named profile" as a `Config` field at all).
**Two sub-options:**
  (2a) Resolve role-group->profile ENTIRELY at the CLI/setup layer,
  before any `Config` is built — `Config.roles` receives only ordinary
  per-role endpoint dicts (exactly what it already accepts today, SM1)
  with no new `Config` field naming "which named profile" produced
  them. **Zero SM6 risk** — nothing new for
  `_versioned_source_config_data` to pop, because nothing new is
  added to `Config`'s shape, only to how one of its EXISTING fields
  (`roles`) gets populated upstream.
  (2b) Add a `Config.seat_bindings: dict[str, str]`-shaped field
  (role-group -> profile name) for auditability/debugging. **Real
  SM6 risk** — `_versioned_source_config_data` (`run_manifest.py`)
  must explicitly pop it every schema version or it leaks into
  `source_config_hash`/`engine_config_json`/the compiled manifest's
  `sha256`, repeating the exact failure `INV-frozen-surfaces.md`
  already records for `ENGAGED_CRITICISM_AUTHORITY`.
**Recommendation (priced, not merely argued):** 2a. It achieves
everything Option A needs (heterogeneous `Config.roles`, SM1) with
provably zero frozen-surface-4 risk, at the cost of the operator
losing a `Config`-level audit trail of "which named profile was
selected" — which Rung S5 ("seats in the typed record") is explicitly
scoped by the plan to add as a manifest-level, replay-tolerant record
LATER, the correct rung for exactly this concern, not S2/S3.
accept: this item states which sub-option is recommended and cites
SM6 as the reason 2b is priced higher-risk, without picking 2b
silently.

S3 (R2, R6, R7): Price Option B — manifest-declared seat section, and
reject it for S3 (not for the program) with cited measurements.
**Mechanism:** a new `SeatBindingPlanV1`/`SeatBindingGrantV1` pair,
modeled on `RouteSeatPresentationGrantV1`/`RouteSeatPresentationPlanV1`
(`run_manifest.py:943-978`), added as `RunManifest.seat_binding_plan:
SeatBindingPlanV1 | None = None` (SM5's proven pattern), with a
validator cross-check analogous to `_production_routes_are_concrete`'s
existing three (`run_manifest.py:1458-1502`) re-deriving the expected
plan from `roles` and diffing.
**Frozen-surface contact:** real (forecast table, surface 4) — a new
Pydantic model, a new optional field, new pop-logic in BOTH
`_versioned_serialization` and `canonical_bytes()` (SM5's pattern,
correctly applied avoids old-root movement, but is still new code in
a frozen-surface-4 file requiring the operator sign-off
`INV-frozen-surfaces.md` demands for that surface), and new validator
cross-check code.
**What it would buy over Option A:** a first-class, manifest-native,
replay-visible statement of "this binding was an explicit operator
choice" (mirroring `RouteSeatPresentationGrantV1.selection_basis`) —
i.e., exactly Rung S5's planned deliverable, built two rungs early.
**Rejected for S3 (not cancelled) because:** (a) it duplicates work
the plan already schedules for S5 under its own name and evidence
regime (sweep probe, before/after capture — plan lines 109-117); (b)
it spends real frozen-surface-4 budget for zero additional CAPABILITY
Option A lacks — every functional requirement in REQUEST.md (binding
surface, replay validity, continuation identity, qualification
distinction) is already satisfied by Option A per SM1-SM12; (c) per
the plan's own expectation ("Expect (a) resolved at compile time with
the RESULT recorded (see S5) to win"), this spec's measurements
confirm rather than merely repeat that expectation.
accept: this item states the reject and cites which SM-numbers justify
it (SM1, SM2, SM4 for "Option A already suffices"; SM5, SM6 for
"Option B's cost is real, not merely more code").

S4 (R3): State the qualification-treatment decision for S2/S3's scope
specifically (full battery per profile now, seat-scoping deferred),
with SM7-SM9 as evidence, and name the one untested combination SM9
flags (qualifying a profile within a manifest that mixes it with
OTHER seats' already-different bindings) as an explicit non-goal for
S3/S4 to avoid without further measurement.
accept: item states the decision, cites SM7 (digest already
distinguishes by profile), SM8 (battery already role/seat-tagged, so
seat-scoping later is additive), SM9 (pairs don't cross-reference
other roles' routes, but the untested combination is named, not
silently assumed safe).

S5 (R4): State replay validity for Option A. Because Option A adds NO
new manifest field (Item S2's recommendation, 2a), there is nothing
new for a reader to find absent OR present on old roots — every
existing and future root's `RunManifest.roles` is read exactly as
CENSUS.md and `CON-seats.md` already describe it (a per-role tuple of
`Route`s, historically uniform because every historical root came from
the one-profile `_config_for_profile` broadcast, going forward
possibly heterogeneous). No absence-tolerant reader code is needed
FOR THIS RUNG — that need arises only if/when S5 (the plan's own rung)
adds a first-class binding-provenance record, at which point THAT
record (not `roles` itself) needs the absence-tolerant reader the plan
describes ("committed roots carry no seat bindings; every reader must
treat absence as single-seat run").
accept: item states why S2/S3 introduces zero new replay-reader
surface, distinct from (and not pre-empting) S5's future reader work.

S6 (R5): State and justify the continuation-identity rule, citing
SM12, and explicitly name and reject the unnamed "Option C" (dynamic
label-time re-resolution) per the placement-law section above.
accept: item states the rule is ALREADY enforced with zero new code
required for Option A (SM12), and that this is a property of WHERE
bindings resolve (compile time) rather than of Option A specifically
— true for Option B too, false for the named-and-rejected Option C.

S7 (R10): State the three kill-risk measurements and their outcomes
(SM9/SM10/SM11), each with a explicit disposition — not left as prose
worry.
accept: item states, for each of the three kill-risks quoted in
REQUEST.md, one line: which SM number measured it and what the
measured outcome was (defused / real-and-priced / escalated).

S8 (R9): Explicitly bound this tranche to S2 only — no CHECKLIST.md,
no wiring, no code. Name what is deliberately NOT decided here for the
operator to weigh in on: (a) the exact role-group -> role-name mapping
for "coder"/"scratch"/"simulation" given the "simulation" = "conjecture"
overlap finding (Item S1); (b) whether per-seat token BUDGET
allocation (distinct from the already-defused per-seat token
ACCOUNTING correctness, SM10) is ever wanted, given nothing requires
it; (c) Option A's sub-choice 2a vs 2b (recommended: 2a).
accept: item lists exactly these three as explicitly out of this
SPEC's decision, each traceable to where it was raised.

## Assumptions (operator may override)

A1: The role-group -> role-name mapping for "coder" is
`experimenter`/`property_designer` (the roles `rules/experiment.py`
renders for `workloads/code.py`/`workloads/formal.py` content, per
CENSUS.md's Delegating-modules table) — assumed as the plan's own
"execution-adjacent" gloss (ROLE_SEAT_SEPARATION_PLAN.md line 35-36)
most directly names, operator may override.
A2: "scratch" = the role set `scratch/authoring.py` actually renders
(`conjecturer`/`synthesizer` for blocks per `block_role`'s constrained
choice, `synthesizer` fixed for links, `summarizer` fixed for guides)
— assumed per CENSUS.md M41/M42's measured role set, operator may
override.
A3: Item S2 recommends sub-option 2a (resolve entirely pre-`Config`,
no new `Config` field) over 2b — assumed as the zero-SM6-risk choice;
operator may override toward 2b if a `Config`-level audit trail is
wanted before Rung S5 ships its manifest-level one.

## Questions for operator (STOP — non-empty, presenting now)

Q1: The plan names four seat groups — "conjecture", "coder",
"scratch", "simulation" — but this spec's measurement (Item S1) finds
"conjecture" and "simulation" currently render through the IDENTICAL
role set (`conjecturer`, per CENSUS.md M18/M19 — capability-channel
proposals are typed conjecturer output, there is no separate
"simulation-authoring" role in `llm/roles.py` today). This is a
MATERIAL fork, not a detail: (a) treat "simulation" as an ALIAS of
"conjecture" for S3 (zero extra role/template work, but an operator
binding `--seat simulation=X` while `--seat conjecture=Y` differ would
need a typed refusal or an explicit "last one wins" rule, since one
role cannot serve two different profiles at once); or (b) treat this
as evidence a genuinely separate capability-authoring role belongs on
the program's later roadmap (more work, not S2/S3 scope, but changes
what "the binding surface" even names). Recommend (a) for S3, since it
costs nothing now and doesn't foreclose (b) later — but this is the
operator's call, not a default to assume silently.

Q2: Item S2 recommends Option A sub-choice 2a (no new `Config` field,
zero `_versioned_source_config_data` risk) over 2b (a `Config`-level
seat-bindings field for auditability, real but small SM6 risk).
Confirm 2a, or explicitly accept 2b's risk if a pre-S5 audit trail is
wanted.

## Out of scope (explicit)

- Any code change — this tranche is SPEC only (R1).
- Rung S3's actual wiring (naming the exact new CLI flags' argparse
  shape, the persisted mapping file's exact format, tests) — S3's job,
  after operator approval of the option chosen here.
- Rung S4's qualification orchestration (`deepreason qualify` walking
  distinct bound profiles) — explicitly the plan's own S4 scope, this
  spec only confirms zero frozen-surface-5 CODE contact (SM7).
- Rung S5's binding-provenance manifest record — explicitly deferred
  by this spec's Item S2/S5 reasoning, not merely unmentioned.
- Per-seat token budget ALLOCATION (distinct from per-seat token
  ACCOUNTING, which SM10 already shows is correct today without
  change) — nothing in this design requires it; noted, not built.
- Package-level work (Rung S7) — far out of scope.

## Budget

0 lines changed under `src/` or `tests/` (DESIGN-AND-STOP, R1). This
tranche's own diff: `REQUEST.md`, `SPEC.md` only, in the tranche
directory. No `docs/map/` change (no new seam, no new concept beyond
what `CON-seats.md` already names — S1's rung already delivered that
document). Frozen surfaces touched: **none, by this tranche or by the
recommended Option A** (forecast table above) — conditional
specifically on Option A over Option B, and on sub-choice 2a over 2b,
exactly as rung 7's own spec stated its zero-contact verdict was
conditional on its placement decision, not unconditional.
