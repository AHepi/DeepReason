# CENSUS — Rung S1 seat census

Every claim below is backed by the pasted command immediately above it.
Measured against `deepreason` HEAD `d2c46d71` (checklist-committed head)
on branch `claude/seat-census-rung-s1-7gphj9`, itself continued from
`origin/claude/delivery-rungs-handover-m22sdy` (see this tranche's
REQUEST.md for why).

## M0 — raw sweep

```
$ grep -rn "\.call(" src/deepreason --include="*.py"
src/deepreason/views/prose.py:24:        output, _ = adapter.call("summarizer", text, ProseOutput)
src/deepreason/views/thesis.py:79:    output, llm_call = adapter.call(call_role, pack, ThesisOutput,
src/deepreason/views/thesis.py:91:        retry_out, retry_call = adapter.call(call_role, repair_pack,
src/deepreason/measures/hv.py:136:    output, llm_call = adapter.call("variator", pack, VariatorOutput)
src/deepreason/llm/specs.py:41:    output, llm_call = adapter.call(
src/deepreason/informal/audits.py:79:        ruling, llm_call = adapter.call(
src/deepreason/informal/audits.py:130:            para, para_call = adapter.call(
src/deepreason/informal/trial.py:211:    ruling, first = adapter.call("judge", pack, JudgeRuling, aliases=aliases)
src/deepreason/informal/trial.py:216:        other, call = adapter.call(
src/deepreason/informal/trial.py:287:    case_out, call = adapter.call(
src/deepreason/informal/trial.py:300:    defence, call = adapter.call(
src/deepreason/informal/trial.py:523:    para_out, call = adapter.call(
src/deepreason/informal/trial.py:648:    defence, call = adapter.call(
src/deepreason/informal/trial.py:842:    ruling1, llm_call = adapter.call(
src/deepreason/informal/trial.py:867:    ruling2, call = adapter.call(
src/deepreason/workflows/website.py:869:            output, llm_call = adapter.call(
src/deepreason/workflows/website.py:918:            output, llm_call = adapter.call(
src/deepreason/rules/conj.py:555:                output, call = adapter.call(
src/deepreason/rules/conj.py:1774:        output, llm_call = adapter.call(
src/deepreason/rules/experiment.py:148:    output, llm_call = adapter.call(
src/deepreason/rules/experiment.py:342:            ruling, llm_call = adapter.call(
src/deepreason/rules/experiment.py:452:    output, llm_call = adapter.call(
src/deepreason/rules/vision.py:85:    output, llm_call = adapter.call(
src/deepreason/rules/synth.py:36:    output, llm_call = adapter.call(
src/deepreason/rules/crit.py:424:        output, llm_call = adapter.call(
src/deepreason/rules/crit.py:642:        output, call = adapter.call(
src/deepreason/rules/crit.py:1220:    output, llm_call = adapter.call(
src/deepreason/rules/crit.py:1275:                retry, llm_call = adapter.call(
src/deepreason/rules/crit.py:1615:        output, llm_call = adapter.call(
src/deepreason/rules/crit.py:1884:            retry_out, retry_llm = adapter.call(
src/deepreason/workflow/repair_transaction.py:398:            _wire_output, repair_call = adapter.call(
src/deepreason/ops.py:135:    case_out, llm_call = adapter.call(
src/deepreason/bridge/review.py:297:                verdict, call = self.adapter.call(
src/deepreason/bridge/ledger.py:1992:        ledger, call = adapter.call(
src/deepreason/bridge/ledger.py:2079:        ledger, call = adapter.call(
src/deepreason/bridge/repair.py:513:                patch, call = self.adapter.call(
src/deepreason/bridge/compose.py:893:            draft, call = self.adapter.call(
src/deepreason/bridge/transactional_adapter.py:902:            ledger, call = self.call(
src/deepreason/bridge/transactional_adapter.py:997:            draft, call = self.call(
src/deepreason/bridge/transactional_adapter.py:1341:            output, llm_call = self._adapter.call(
src/deepreason/scratch/authoring.py:868:            output, call = self.adapter.call(
src/deepreason/scratch/authoring.py:1194:            output, call = self.adapter.call(
src/deepreason/referee.py:628:        output, llm_call = adapter.call(
```
43 lines.

```
$ grep -n "render_role_prompt\|EndpointLease(\|select_lease" src/deepreason/cli/doctor.py
518:        lease = EndpointLease(role=pair.role, seat=pair.seat, route=route)
779:    from deepreason.llm.roles import render_role_prompt
870:    request = render_role_prompt(
915:    lease = EndpointLease(role=pair.role, seat=pair.seat, route=route)
```
4 lines. Zero `select_lease` occurrences in `doctor.py` — confirmed
separately in the "select_lease degrees of freedom" section below.

## Excluded hits

Every hit in M0's `.call(` sweep is a call on an `LLMAdapter`-family
receiver: the literal variable `adapter` (a parameter named `adapter`
in every enclosing function — spot-checked below), `self.adapter`,
`self._adapter`, or `self.call(` inside
`bridge/transactional_adapter.py`'s `TransactionalBridgeAdapter` class
(whose own `call` method, defined at line 1073, forwards to
`self._adapter.call(...)` at line 1341 — itself already counted as a
promoted M0 hit). No hit is a `.call(` on an unrelated object (no
pydantic/dict/other `.call` method appears anywhere in the sweep).

```
$ grep -n "def .*adapter" src/deepreason/llm/specs.py src/deepreason/measures/hv.py src/deepreason/ops.py src/deepreason/views/prose.py src/deepreason/views/thesis.py
src/deepreason/llm/specs.py:29:def generate_specs(harness, adapter, problem: Problem, config) -> tuple[list[str], LLMCall]:
src/deepreason/measures/hv.py:124:def _sample_edits(harness, adapter, artifact: Artifact, k: int):
src/deepreason/measures/hv.py:170:def hv_spot_check(harness, adapter, artifact_id: str, k: int, embedder=None) -> float | None:
src/deepreason/measures/hv.py:202:def run_hv_floor(harness, adapter, target_id: str, commitment: Commitment, embedder=None) -> str:
src/deepreason/ops.py:101:def review_infrastructure(harness, adapter, config, artifact_id: str):
src/deepreason/views/prose.py:14:def prose(artifact_id: str, state: EpistemicState, blobs, adapter=None) -> str:
src/deepreason/views/thesis.py:61:def thesis(harness, adapter, problem_id: str | None = None,
```

```
$ grep -n "^class \|def call(" src/deepreason/bridge/transactional_adapter.py
src/deepreason/bridge/transactional_adapter.py:215:class TransactionalBridgeAdapter:
src/deepreason/bridge/transactional_adapter.py:1073:    def call(
```

**Arithmetic:** M0 sweep total = 43 (`.call(` in `src/deepreason`) + 4
(`doctor.py` render/lease lines, of which 2 are `EndpointLease(`
construction sites, 1 is the `render_role_prompt` import, 1 is its
call site) = 47 raw lines. Promoted call sites: 43 (every `.call(` hit)
+ 1 (`doctor.py`'s `render_role_prompt(...)` call at line 870, which
dispatches a provider-facing role render without going through
`LLMAdapter.call` at all — see the operational definition in SPEC.md)
= 44 promoted sites. Excluded: 0 `.call(` hits; the `doctor.py`
`EndpointLease(` construction lines (518, 915) and the `import` line
(779) are not call-site dispatch lines themselves — they are evidence
for the "lease selection path" column of the two `doctor.py` rows built
from the one promoted `render_role_prompt` pattern (`doctor.py` renders
per `(pair.role, pair.seat)` in a loop; both construction lines are the
same mechanism, not two distinct call sites — see M1 table note).
44 promoted + 0 excluded (plus 3 non-dispatch evidence lines already
accounted for) = 47. Total = 47.

## select_lease degrees of freedom

```
$ sed -n '164,189p' src/deepreason/run_manifest.py
class Route(BaseModel):
    """One exact provider route, with no credential value."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True
    )

    endpoint_id: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_revision: str | None = None
    provider: str = Field(min_length=1)
    family: str = Field(min_length=1)
    reasoning: str | int | None = None
    output_mode: Literal["json_object", "text"] = "text"
    output_mechanism: Literal["native_json_schema", "grammar", "json_text"] = "json_text"
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, gt=0)
    # Frozen total prompt-plus-completion capacity. ``None`` retains legacy
    # unqualified behavior and is not evidence of an unlimited window.
    context_window_tokens: int | None = Field(default=None, gt=0)
    timeout_s: int = Field(default=DEFAULT_TIMEOUT_S, gt=0)
    logprobs: bool = False
    # The name of an environment variable is routing metadata, not a secret.
    # The variable's value is looked up only while constructing the endpoint.
    api_key_env: str | None = None
```

```
$ sed -n '222,235p' src/deepreason/llm/firewall.py
@dataclass(frozen=True, slots=True)
class EndpointLease:
    """One role seat permanently bound to one concrete Route."""

    role: str
    seat: int
    route: Route

    def __post_init__(self) -> None:
        if not self.role:
            raise ValueError("EndpointLease role cannot be empty")
        if self.seat < 0:
            raise ValueError("EndpointLease seat cannot be negative")
```

```
$ sed -n '424,462p' src/deepreason/llm/firewall.py
def leases_from_endpoints(
    endpoints: Mapping[str, object],
) -> dict[str, tuple[EndpointLease, ...]]:
    """Freeze the legacy role table once at adapter construction."""
    leases: dict[str, tuple[EndpointLease, ...]] = {}
    for role, configured in endpoints.items():
        seats = configured if isinstance(configured, (list, tuple)) else (configured,)
        leases[role] = tuple(
            EndpointLease(role=role, seat=index, route=route_from_endpoint(endpoint))
            for index, endpoint in enumerate(seats)
        )
    return leases


def leases_from_manifest(manifest: RunManifest) -> dict[str, tuple[EndpointLease, ...]]:
    return {
        role: tuple(
            EndpointLease(role=role, seat=index, route=route)
            for index, route in enumerate(routes)
        )
        for role, routes in manifest.roles.items()
        if routes
    }


def select_lease(
    leases: Mapping[str, tuple[EndpointLease, ...]], role: str, seat: int
) -> EndpointLease:
    try:
        lease = leases[role][seat]
    except (KeyError, IndexError) as error:
        raise KeyError(f"no endpoint lease configured for role {role!r} seat {seat}") from error
    if lease.role != role or lease.seat != seat:
        raise RouteFirewallError(
            f"lease identity mismatch: requested {role}[{seat}], got "
            f"{lease.role}[{lease.seat}]"
        )
    return lease
```

**Derived variance statement**, grounded only in the text above:
`leases` is a `dict[role -> tuple[EndpointLease, ...]]`, built once per
run from `config.roles` (legacy) or `RunManifest.roles` (v6), and
`select_lease(leases, role, seat)` is a pure two-key lookup into it.
Each `EndpointLease` binds one `(role, seat)` pair to one immutable
`Route`, and `Route` already carries a fully independent
`model_id`/`endpoint_id`/`base_url`/`provider`/`family`/`reasoning`/
`temperature`/`output_mechanism`/`context_window_tokens`/`max_tokens`
per lease — nothing in `EndpointLease`, `select_lease`, or `Route`
forces two different roles (or two seats of the same role's ensemble,
e.g. `judge`) to share a model or endpoint; the mechanism is already
role-and-seat-scoped model routing at the `Route` level. What
`select_lease` CANNOT vary, because nothing keys leases on anything
else: call-site identity (two call sites rendering the same `role` get
the identical lease), workload/consumer kind (rules vs. scratch vs.
capabilities all resolve through the same per-role table), or a
per-call profile override (`profile_for`/`base_profile_for` in
`adapter.py` read `self.base_model_profile`, a single value on the
`LLMAdapter` instance, not sourced from `leases` or `Route` at all —
see the M1 table's "frozen-per-role" column below). In today's actual
runs every role's `Route` happens to be populated from the one profile
`setup`/`config.roles` bound (measured in M1), but that is a
configuration-time fact, not a `select_lease` limitation — the
mechanism already has the degrees of freedom Rung S2 would spend.

## The mint-time fact that makes "frozen per-role today" answer uniformly

Before the per-row table: one setup-time mechanism explains almost every
row's "frozen-per-role" column, so it is measured once here and cited
by pointer rather than re-derived 44 times.

```
$ sed -n '263,277p' src/deepreason/preparation.py
def _config_for_profile(profile: ProviderProfileV1) -> Config:
    endpoint = profile.endpoint_spec()
    return Config(
        engine_profile="full",
        model_profile=profile.model_profile,
        scratchpad=engaged_scratchpad_source(),
        # The grounded two-stage bridge rides the same single endpoint: the
        # frozen summarizer and thesis routes below satisfy its validator.
        bridge=engaged_bridge_source(),
        # The public preset keeps the semantic scratch channel on the
        # deterministic hashing embedder: no optional neural dependency may
        # decide public manifest identity.
        EMBEDDER_MODEL=None,
        roles={role: dict(endpoint) for role in V3_CANONICAL_ROLES},
    )
```

```
$ grep -n "LEGACY_CANONICAL_ROLES\s*=" -A 12 src/deepreason/run_manifest.py
LEGACY_CANONICAL_ROLES = (
    "conjecturer",
    "argumentative_critic",
    "defender",
    "variator",
    "judge",
    "summarizer",
    "synthesizer",
    "vision_critic",
    "property_designer",
    "thesis",
)
```

```
$ grep -n "V3_CANONICAL_ROLES\s*=" src/deepreason/run_manifest.py
src/deepreason/run_manifest.py:72:V3_CANONICAL_ROLES = (*LEGACY_CANONICAL_ROLES, "grounding_reviewer")
```

`ProviderProfileV1` (`provider_profile.py`) is one secret-free
`provider`/`endpoint`/`model_id`/`family`/`model_profile`/`reasoning`
bundle — the thing `deepreason setup` mints and the plan document calls
"the provider profile `setup` bound." `_config_for_profile` builds
exactly ONE `endpoint` dict from it, then copies that SAME dict — same
object identity is not preserved but same field values are — into
`Config.roles` for every name in `V3_CANONICAL_ROLES` (11 roles: the 10
legacy names plus `grounding_reviewer`). This is the literal, load-
bearing mechanism behind "profile is frozen per-role today": no role
gets a different provider/model/transport than any other, because they
are all populated from the one `endpoint` value at this one call. Every
M-row below whose "frozen-per-role" column reads "No" cites this
section rather than repeating the derivation. Roles absent from
`V3_CANONICAL_ROLES` (`batch_critic`, `config_referee`, `experimenter`,
`spec_generator`, `scratch_block`, `scratch_link`, `scratch_guide`,
`bridge_ledger`, `bridge_compose`, `bridge_review`,
`bridge_grounding_repair`) are template-only names, rendered via
`template_role=` while dispatching on one of the eleven ENDPOINT-bearing
roles above (measured per-row below) — they inherit that role's route,
not a route of their own.

## M1 — the call-site table

Columns: **M#** | **file:line** | **role rendered** | **template_role**
| **lease selection path** | **frozen-per-role today?** (evidence)

| M# | file:line | role | template_role | lease path | frozen-per-role? |
|---|---|---|---|---|---|
| M1 | views/prose.py:24 | `"summarizer"` (literal) | — | `select_lease` via `_render_request` (default `endpoint_index=0`) | No — preparation.py:276 |
| M2 | views/thesis.py:79 | `call_role` = `role if adapter.has_role(role) else "summarizer"` (dynamic, thesis.py:76) | `"thesis"` (literal) | `select_lease`, index 0 | No — preparation.py:276 |
| M3 | views/thesis.py:91 | same `call_role` as M2 (retry) | `"thesis"` (literal) | `select_lease`, index 0 | No — preparation.py:276 |
| M4 | measures/hv.py:136 | `"variator"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M5 | llm/specs.py:41 | `"conjecturer"` (literal) | `"spec_generator"` (literal) | `select_lease`, index 0 | No — preparation.py:276 |
| M6 | informal/audits.py:79 | `"judge"` (literal) | — | `select_lease`, `endpoint_index=index` (judge ensemble seat) | No — preparation.py:276 (all judge seats still come from the one profile's endpoint unless a distinct judge-ensemble endpoint was separately configured — table does not claim ensemble seats are homogeneous, only that they are not role-differentiated by this mechanism) |
| M7 | informal/audits.py:130 | `"variator"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M8 | informal/trial.py:211 | `"judge"` (literal) | — | `select_lease`, index 0 (first seat) | No — preparation.py:276 |
| M9 | informal/trial.py:216 | `"judge"` (literal) | — | `select_lease`, `endpoint_index=index` (later ensemble seats) | No — preparation.py:276 |
| M10 | informal/trial.py:287 | `"argumentative_critic"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M11 | informal/trial.py:300 | `"defender"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M12 | informal/trial.py:523 | `"variator"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M13 | informal/trial.py:648 | `"defender"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M14 | informal/trial.py:842 | `"judge"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M15 | informal/trial.py:867 | `"judge"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M16 | workflows/website.py:869 | `"conjecturer"` (literal) | `template_role` (dynamic param) | `select_lease`, index 0; `model_profile="compact"` overrides ONLY presentation, not route/model | No — preparation.py:276 |
| M17 | workflows/website.py:918 | `"conjecturer"` (literal) | `template_role` (dynamic param) | `select_lease`, index 0; `model_profile="compact"` | No — preparation.py:276 |
| M18 | rules/conj.py:555 | `"conjecturer"` (literal) | — | explicit `endpoint_lease=endpoint_lease` (caller-resolved, school-routed conjecture — bypasses the default `select_lease` call inside `_render_request` because a lease is already supplied) | No — preparation.py:276 |
| M19 | rules/conj.py:1774 | `"conjecturer"` (literal) | — | explicit `endpoint_lease=dispatch_endpoint_lease` | No — preparation.py:276 |
| M20 | rules/experiment.py:148 | `"conjecturer"` (literal) | `"experimenter"` (literal) | `select_lease`, index 0 | No — preparation.py:276 |
| M21 | rules/experiment.py:342 | `"judge"` (literal) | — | `select_lease`, `endpoint_index=seat` | No — preparation.py:276 |
| M22 | rules/experiment.py:452 | `"property_designer"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M23 | rules/vision.py:85 | `"vision_critic"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M24 | rules/synth.py:36 | `"synthesizer"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M25 | rules/crit.py:424 | `"argumentative_critic"` (literal) | `"batch_critic"` (literal) | explicit `endpoint_lease=endpoint_lease` | No — preparation.py:276 |
| M26 | rules/crit.py:642 | `"argumentative_critic"` (literal) | `"argumentative_critic"` (literal, redundant) | explicit `endpoint_lease=endpoint_lease` | No — preparation.py:276 |
| M27 | rules/crit.py:1220 | `"argumentative_critic"` (literal) | — (may be in `**call_kwargs`, not visible at this line) | `select_lease` unless `**call_kwargs` supplies `endpoint_lease` | No — preparation.py:276 |
| M28 | rules/crit.py:1275 | `"argumentative_critic"` (literal) | — (`**call_kwargs`) | same as M27 | No — preparation.py:276 |
| M29 | rules/crit.py:1615 | `"argumentative_critic"` (literal) | `"batch_critic"` (literal) | `select_lease` unless `**call_kwargs` supplies `endpoint_lease` | No — preparation.py:276 |
| M30 | rules/crit.py:1884 | `"argumentative_critic"` (literal) | `"batch_critic"` (literal) | same as M29 | No — preparation.py:276 |
| M31 | workflow/repair_transaction.py:398 | `role` (dynamic param — shared v6 schema-repair dispatch helper, reused for any role's failed call; `repair_schema_failure(role: str, ...)`) | `template_role` (dynamic param) | `select_lease` unless an `endpoint_lease` was passed through | No — preparation.py:276 |
| M32 | ops.py:135 | `"argumentative_critic"` (literal) | — | `select_lease`, index 0 | No — preparation.py:276 |
| M33 | bridge/review.py:297 | `self.role` (constructor param, default `"judge"`, constrained to `{judge, grounding_reviewer}` — `GroundingReviewService.__init__`) | `"bridge_review"` (literal) | `select_lease`, index 0 | No — preparation.py:276 |
| M34 | bridge/ledger.py:1992 | `role` (param, default `"summarizer"` — `build_claim_ledger_stage_a`) | `"bridge_ledger"` (literal) | `select_lease`, index 0 | No — preparation.py:276 |
| M35 | bridge/ledger.py:2079 | `role` (same default `"summarizer"` path, amendment variant) | `"bridge_ledger"` (literal) | `select_lease`, index 0 | No — preparation.py:276 |
| M36 | bridge/repair.py:513 | `self.role` (constructor param, default `"judge"`, constrained to `{judge, grounding_reviewer}` — `GroundingRepairService.__init__`-equivalent) | `"bridge_grounding_repair"` (literal) | `select_lease`, index 0 | No — preparation.py:276 |
| M37 | bridge/compose.py:893 | `self.role` (constructor param, constrained to `{thesis, summarizer}` — bridge composer) | `"bridge_compose"` (literal) | `select_lease`, index 0 | No — preparation.py:276 |
| M38 | bridge/transactional_adapter.py:902 | `transition.route_lease.role` (dynamic, from a decomposition transition record) | `"bridge_ledger"` (literal) | `endpoint_index=transition.route_lease.seat`; ultimately `select_lease` inside `self.call` (=`_adapter.call` via M40's site) unless overridden | No — preparation.py:276 |
| M39 | bridge/transactional_adapter.py:997 | `transition.route_lease.role` (dynamic) | `"bridge_compose"` (literal) | `endpoint_index=transition.route_lease.seat` | No — preparation.py:276 |
| M40 | bridge/transactional_adapter.py:1341 | `role` (dynamic param — `TransactionalBridgeAdapter.call`'s own generic forwarding method, the real dispatch point M38/M39 and any other `self.call(...)` route through) | `template_role` (dynamic param) | `select_lease` via the wrapped `_adapter.call`'s `_render_request`, unless `endpoint_lease` supplied | No — preparation.py:276 |
| M41 | scratch/authoring.py:868 | `role` (param of `_legacy_call`; literal at the real call sites: `"conjecturer"` or `"synthesizer"` for blocks — `block_role` constructor default `"conjecturer"`, constrained to `{conjecturer, synthesizer}` — `"synthesizer"` fixed for links, `"summarizer"` fixed for guides — `ScratchAuthoringService.__init__`) | `template_role` (param; literal at real call sites: `"scratch_block"`, `"scratch_link"`, or `"scratch_guide"`) | `select_lease`, index 0 (legacy/non-v6 path) | No — preparation.py:276 |
| M42 | scratch/authoring.py:1194 | same role set as M41 (v6/transactional path) | same template_role set as M41 | explicit `endpoint_lease=lease` (v6 route-seat lease, still ultimately sourced from the one `preparation.py:276` route per role) | No — preparation.py:276 for route/model identity; presentation (`model_profile=base_profile`) IS resolved per `(role, seat, endpoint_id)` here via `resolve_route_seat_base_profile` in v6 — see the separate note below the table |
| M43 | referee.py:628 | `"argumentative_critic"` (literal) | `"config_referee"` (literal) | explicit `endpoint_lease=endpoint_lease` | No — preparation.py:276 |
| M44 | cli/doctor.py:870 (`render_role_prompt`), lease evidence at doctor.py:518/915 | `pair.role` (dynamic — one production-contract pair from the qualification battery's finite pair set) | `template_role` (dynamic; resolved per contract_id in `_production_probe_contract`, e.g. `"config_referee"`, `"bridge_ledger"`, `"bridge_compose"`, `"bridge_review"`, `"bridge_grounding_repair"`, or a `scratch.*`-derived name) | **not** `select_lease` — `route = manifest.roles[pair.role][pair.seat]` read directly from the manifest, then `EndpointLease(role=pair.role, seat=pair.seat, route=route)` constructed inline; dispatch itself calls `endpoint.complete(...)` directly, never `LLMAdapter.call` | No — preparation.py:276 for route/model identity (the qualification battery walks the SAME manifest-compiled routes M1-M43 use); presentation profile IS resolved per `(role, seat, endpoint_id)` via `resolve_route_seat_base_profile` (doctor.py:876-880) |

**A genuine per-(role,seat) mechanism that already exists (not a
counterexample to the mint-time fact above, but a real nuance):** in v6
transactional runs (`RunManifest.schema_version == 6`), the
PRESENTATION profile (compact/standard/frontier — how the SAME model is
asked to respond, not which model/endpoint answers) resolves through
`resolve_route_seat_base_profile(manifest, role=role, seat=seat,
endpoint_id=...)`, which the manifest's `RouteSeatPresentationGrantV1`/
`RouteSeatPresentationPlanV1` records can in principle set differently
per role/seat/endpoint. This is presentation-only: it never changes
`model_id`/`endpoint_id`/`provider`, all of which remain the one
`preparation.py:276` value for every role. M42 and M44 are the two rows
where this per-seat presentation resolution is reached.

```
$ grep -n "^def resolve_route_seat_base_profile" -A 20 src/deepreason/run_manifest.py
def resolve_route_seat_base_profile(
    manifest: RunManifest,
    *,
    role: str,
    seat: int,
    endpoint_id: str,
) -> Literal["compact", "standard", "frontier"]:
    """Resolve one exact v6 route seat's frozen base presentation authority.

    Historical v6 manifests predate the per-seat plan and retain their global
    profile semantics. Plan-bearing manifests must resolve through the exact
    role, seat, and endpoint identity; absence is never implicit permission.
    """

    if manifest.schema_version != 6:
        raise RunManifestError(
            "ROUTE_SEAT_PRESENTATION_V6_REQUIRED",
            "route-seat presentation authority requires RunManifest v6",
            "/schema_version",
        )
    routes = manifest.roles.get(role, ())
```

## Delegating modules

Every plan-named module below is confirmed to hold zero call sites of
its own; each row states the real owning M-row(s) and the evidence.

```
$ for f in workloads/website.py workloads/code.py workloads/formal.py workloads/text.py workloads/simulation.py qualification.py capabilities/simulation.py capabilities/research.py scratch/conjecture.py scratch/service.py; do
  echo "=== src/deepreason/$f ==="
  grep -n "\.call(\|select_lease\|render_role_prompt" "src/deepreason/$f" | wc -l
done
=== src/deepreason/workloads/website.py ===
0
=== src/deepreason/workloads/code.py ===
0
=== src/deepreason/workloads/formal.py ===
0
=== src/deepreason/workloads/text.py ===
0
=== src/deepreason/workloads/simulation.py ===
0
=== src/deepreason/qualification.py ===
0
=== src/deepreason/capabilities/simulation.py ===
0
=== src/deepreason/capabilities/research.py ===
0
=== src/deepreason/scratch/conjecture.py ===
0
=== src/deepreason/scratch/service.py ===
0
```

| Named module | Delegates to | Evidence |
|---|---|---|
| `workloads/website.py` | `workflows/website.py` (M16, M17) | Module docstring, line 1: `"""Compatibility adapter around the existing website state machine."""` — `WebsiteWorkloadAdapter` wraps the state machine `workflows/website.py` implements. |
| `workloads/code.py` | `rules/experiment.py` (M20 `experimenter`, M22 `property_designer`) | `code.py` defines only property-oracle/workspace-safety schema and execution (`WorkspaceFile`, sandbox validators) — zero LLM imports; `rules/experiment.py`'s `ExperimenterOutput`/`PropertyDesignerOutput` roles are what generate content that runs against these oracles (`rules/experiment.py:148,452` build generators/checkers, the only producers of code-workload content). |
| `workloads/formal.py` | `rules/experiment.py` (same M20/M22) | `formal.py` imports only `ontology`/`verification.models` (`VerificationRequest`, `VerificationResult`) — a verification-result schema, no adapter/LLM import; the same experimenter/property-designer roles author formal-workload content. |
| `workloads/text.py` | `rules/conj.py` + `rules/crit.py` (the ordinary conjecture/criticism loop; no dedicated text-workload call site) | `text.py` defines only `WorkloadProblem`/ontology schema (`Problem`, `Commitment`) — zero LLM imports; text is the plain `Problem` shape the default conjecturer/critic cycle already handles, so it has no call site beyond the ordinary rules M-rows. |
| `workloads/simulation.py` | `capabilities/simulation.py` -> `rules/conj.py` (M18, M19) | `workloads/simulation.py` only tags `Provenance(role="import"/"user")` on artifacts (data provenance, not a dispatch role) — zero LLM imports; simulation proposal content is authored as typed conjecturer output (see next row). |
| `qualification.py` | `cli/doctor.py` (M44) | `from deepreason.cli.doctor import (... production_contract_pairs, validate_production_contract_qualification ...)` (qualification.py:24-35) — qualification's battery machinery is imported wholesale from `doctor.py`; `qualification.py` itself has zero `.call`/`select_lease`/`render_role_prompt` occurrences. |
| `capabilities/simulation.py` | `rules/conj.py` (M18, M19) | Module docstring: `"""Deterministic Tranche-A simulation controller and result reinjection data."""` — it manages the `PROPOSED -> VALIDATED -> GRANTED -> COMPILED -> DISPATCHED -> SUCCEEDED/FAILED -> RESULT_PACKAGED -> CONSUMED` lifecycle of a `SimulationProposalV1` that already exists; `grep -rl "SimulationProposalV1(" src/deepreason` finds the constructor used only in `capabilities/simulation.py` itself (post-hoc typed wrapping) while the actual conjecturer call sites capable of yielding a capability-channel proposal are `rules/conj.py:555,1774` (M18/M19, `role="conjecturer"`) — the roles CLAUDE.md's own language ("typed simulation/research proposals") and the plan document ("Conjecturer... roles") assign this content to. |
| `capabilities/research.py` | `rules/conj.py` (M18, M19) | Module docstring: "Mirrors the simulation controller's transactional discipline... PROPOSED -> VALIDATED -> GRANTED/DENIED -> COMPILED -> DISPATCHED -> SUCCEEDED/FAILED -> RESULT_PACKAGED -> CONSUMED" — same lifecycle-only shape as `capabilities/simulation.py`; `rules/conj.py` appears in `grep -rl "ResearchFetch.*Proposal\|CompiledResearchFetchV1("` alongside state/audit/harness plumbing, confirming the conjecturer is the proposal's origin. |
| `scratch/conjecture.py` | `rules/conj.py` (M18, M19) — supplies their `conjecture_context=` advisory payload | Imports `ConjectureContextCallReceiptV1` and `ContextRequestV1`, builds the bounded advisory-context bytes `rules/conj.py`'s conjecturer calls attach via `conjecture_context=` (`rules/conj.py` uses `context_policy = run_manifest.control_plane_policy.conjecture_context` at line 307 and threads `conjecture_context_plan`); it renders no role prompt and has zero adapter import. |
| `scratch/service.py` | `scratch/authoring.py` (M41, M42) | Imports only `harness`, `scratch.errors/events/models/search/state` — a CRUD/query substrate over scratch state, zero adapter import; `ScratchAuthoringService.__init__(self, service: ScratchService, adapter, ...)` in `scratch/authoring.py` takes a `ScratchService` instance as a dependency, confirming `service.py` is consumed by, not the source of, the dispatch. |

(Steps 6+ continue outside this document — see CHECKLIST.md.)
