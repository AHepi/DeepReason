"""The single configuration boundary for DeepReason (spec §15).

``Config`` owns every default and validates every knob. YAML files are partial
profiles: they contain only deliberate differences from the built-in schema.
Profile-driven entry points load here and build role endpoints through
``deepreason.llm.adapter.build_adapter``; general-purpose scripts must not
carry private copies of role caps, reasoning policy, or model-selection logic.
Pre-registered experiment arms may still instantiate ``Config`` directly so
their manipulated conditions remain explicit in the experiment source.

Knobs whose spec start value is "tune" default to ``None`` and must be set
before the phases that consume them.
"""

import math
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.authority import TextAuthorityMode


_ENV_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class EndpointSpec(BaseModel):
    """Validated shape of one role endpoint while preserving dict consumers."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    # ``endpoint_id`` and ``family`` are setup-time identities used by the
    # compiled RunManifest.  They are never model-visible and contain no
    # credential.  Omitting them keeps legacy profiles valid: compilation
    # derives stable values from endpoint/provider/model.
    endpoint_id: str | None = None
    endpoint: str | None = None
    model: str | None = None
    model_revision: str | None = None
    family: str | None = None
    temperature: float | None = None
    api_key_env: str | None = None
    provider: str | None = None
    # Setup-time presentation authority for this exact endpoint assignment.
    # Runtime model output cannot alter it; v6 compilation freezes it into the
    # route-seat presentation plan.
    model_profile: Literal["compact", "standard", "frontier"] | None = None
    reasoning: str | int | None = None
    max_tokens: int | None = Field(default=None, gt=0)
    # Total prompt-plus-completion capacity declared by the route owner.
    # ``None`` is legacy/unqualified capacity, not an infinite window.
    context_window_tokens: int | None = Field(default=None, gt=0)
    json_mode: bool = False
    output_mode: Literal["json_object", "text"] | None = None
    # Compile-time transport choice. Runtime calls never probe/fall back.
    output_mechanism: Literal["native_json_schema", "grammar", "json_text"] | None = None
    logprobs: bool = False
    # Transport read timeout (seconds) for one completion attempt. None keeps
    # the endpoint default. Slow hosted open-model endpoints need headroom:
    # a run was killed by ~110s+ generations against a fixed 120s wait.
    timeout_s: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _qualified_context_window_has_finite_completion_allowance(self):
        if self.context_window_tokens is None:
            return self
        if self.max_tokens is None:
            raise ValueError(
                "context_window_tokens requires a finite max_tokens allowance"
            )
        if self.context_window_tokens <= self.max_tokens:
            raise ValueError("context_window_tokens must be greater than max_tokens")
        return self

    @field_validator("api_key_env")
    @classmethod
    def _credential_reference_is_an_env_name(cls, value: str | None) -> str | None:
        if value is not None and not _ENV_IDENTIFIER.fullmatch(value):
            raise ValueError("api_key_env must be a POSIX environment-variable name")
        return value


class ImportPolicy(BaseModel):
    """One typed policy boundary for project-local browser dependencies.

    Runtime packages are never Python dependencies or repository dependencies.
    These limits are frozen into each resolved import record, so changing the
    defaults affects future resolutions only and cannot rewrite an old run.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    discovery_beyond_catalog: bool = False
    permitted_registries: list[str] = Field(
        default_factory=lambda: ["https://registry.npmjs.org"]
    )
    exact_versions_required: bool = True
    lifecycle_scripts_forbidden: bool = True
    max_direct_dependencies: int = Field(default=4, ge=0)
    max_transitive_dependencies: int = Field(default=64, ge=0)
    max_javascript_bytes: int = Field(default=250_000, ge=0)
    max_css_bytes: int = Field(default=80_000, ge=0)
    permitted_licenses: list[str] = Field(default_factory=lambda: [
        "MIT", "Apache-2.0", "0BSD", "BSD-2-Clause", "BSD-3-Clause", "ISC",
        "Unlicense",
    ])
    allow_gsap_license: bool = False
    # One is normal; two is the hard ceiling for a manifest that explicitly
    # proves non-overlapping ownership and compatibility.
    max_core_animation_engines: int = Field(default=2, ge=0)
    max_scroll_coordinators: int = Field(default=1, ge=0)
    max_webgl_canvases: int = Field(default=1, ge=0)
    max_pixel_ratio: float = Field(default=2.0, gt=0)
    # Both references are effective run inputs. The catalog contains metadata
    # only; the exact builder package is resolved and archived with the run.
    catalog_ref: str = Field(default="runtime-web-catalog-v1", min_length=1)
    builder_toolchain_ref: str = Field(default="esbuild@0.28.1", min_length=1)

    @field_validator("permitted_registries")
    @classmethod
    def _https_registries(cls, value):
        if not value:
            raise ValueError("at least one permitted registry is required")
        for registry in value:
            if not registry.startswith("https://"):
                raise ValueError(f"registry must use https: {registry!r}")
        return value

    @field_validator("builder_toolchain_ref")
    @classmethod
    def _exact_builder(cls, value):
        name, marker, version = value.rpartition("@")
        if (not marker or not name or not version
                or any(c in version for c in "*^~<>= ")
                or re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version) is None):
            raise ValueError("builder_toolchain_ref must be an exact package@version")
        return value


class ScratchpadConfig(BaseModel):
    """Typed source policy for the advisory scratch workspace.

    These are setup inputs.  RunManifest compilation resolves profile-specific
    ceilings and the complete channel policy before any scratch model call.
    None of these values has formal-ontology or adjudicative authority.
    """

    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, hide_input_in_errors=True
    )

    enabled: bool = False
    max_blocks_per_pack: int = Field(default=24, gt=0, le=1_000)
    # Zero guides is an explicit, legal request for a block-only context.
    max_guides_per_pack: int = Field(default=4, ge=0, le=100)
    semantic_retrieval: bool = True
    keyword_retrieval: bool = True
    coverage_enabled: bool = True
    coverage_slot_every_n_packs: int = Field(default=4, gt=0, le=100_000)
    exploratory_fraction: float = Field(default=0.10, ge=0.0, le=1.0)
    underexposed_fraction: float = Field(default=0.15, ge=0.0, le=1.0)
    dormant_after_events: int = Field(default=200, ge=0)
    similarity_top_k: int = Field(default=12, gt=0, le=10_000)
    similarity_threshold: float | None = None
    guide_max_open_threads: int = Field(default=8, ge=0, le=256)
    guide_max_entry_points: int = Field(default=8, ge=0, le=256)

    # These names match ScratchAuthoringService's deliberately narrow role
    # surface.  They are content-authoring bindings, never route selectors
    # supplied by scratch text.
    block_role: Literal["conjecturer", "synthesizer"] = "conjecturer"
    link_role: Literal["synthesizer"] = "synthesizer"
    guide_role: Literal["summarizer"] = "summarizer"

    @field_validator("similarity_threshold")
    @classmethod
    def _finite_similarity_threshold(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("similarity_threshold must be finite")
        return value

    @model_validator(mode="after")
    def _reserved_attention_fractions_fit(self):
        if self.exploratory_fraction + self.underexposed_fraction > 1.0:
            raise ValueError("reserved scratch attention fractions must not exceed one")
        return self


class BridgeConfig(BaseModel):
    """Typed source policy for legacy or grounded final-output construction."""

    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, hide_input_in_errors=True
    )

    mode: Literal["legacy_thesis", "grounded_two_stage"] = "legacy_thesis"
    allow_partial: bool = True
    allow_abstention: bool = True
    require_claim_ledger: bool = True
    require_claim_uses: bool = True
    grounding_review: bool = True
    # The shared schema-repair kernel exposes at most two correction turns.
    max_schema_repair_attempts: int = Field(default=2, ge=0, le=2)
    # GroundingRepairService has a separate global semantic-call ceiling of 8.
    max_grounding_repair_attempts: int = Field(default=4, ge=0, le=8)
    # This tranche defines one reviewer stream.  A larger ensemble would need
    # a separately specified deterministic aggregation rule.
    reviewer_seats: int = Field(default=1, ge=1, le=1)
    # Grounding review itself is bounded to at most 128 spans.
    output_section_limit: int = Field(default=32, gt=0, le=128)
    # Stage-B formatting identity.  This is deliberately not a model profile
    # or a route selector; it feeds CompositionRequestV1.formatting_profile.
    target_profile: str = Field(
        default="plain",
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$",
    )

    ledger_role: Literal["summarizer"] = "summarizer"
    composer_role: Literal["thesis", "summarizer"] = "thesis"
    reviewer_role: Literal["judge", "grounding_reviewer"] = "judge"

    @model_validator(mode="after")
    def _grounded_mode_preserves_valid_unresolved_results(self):
        if self.mode != "grounded_two_stage":
            return self
        required = {
            "allow_partial": self.allow_partial,
            "allow_abstention": self.allow_abstention,
            "require_claim_ledger": self.require_claim_ledger,
            "require_claim_uses": self.require_claim_uses,
        }
        disabled = [name for name, enabled in required.items() if not enabled]
        if disabled:
            raise ValueError(
                "grounded_two_stage requires unresolved-success-safe settings: "
                + ", ".join(disabled)
            )
        return self


class Config(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, hide_input_in_errors=True
    )

    # Orthogonal process profiles. engine_profile selects the available
    # deterministic harness surface; model_profile changes only packs, wire
    # contracts, batching and repair presentation. Neither is ontology data.
    engine_profile: Literal["mini", "full"] = "full"
    model_profile: Literal["compact", "standard", "frontier"] = "standard"
    scratchpad: ScratchpadConfig = Field(default_factory=ScratchpadConfig)
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)

    # Unification (§7)
    FLOOR: int = 1
    K: int = 4
    INTEGRATION_BUDGET_SHARE: float = 0.30
    HV_MIN: float | None = None
    HV_K: int = 8
    # Informal domains (§10)
    PRECEDENT_K: int = 4
    TRIAL_PARAPHRASE_N: int = 2
    JUDGE_ERR_MAX: float | None = None
    AUDIT_PERIOD: int = 30
    USER_RULINGS_BUDGET: int = 2
    HOLDOUT_SHARE: float = 0.2
    # Capture control (§11)
    N_SCHOOLS: int = 4
    STANCE_DECAY: float | None = None  # lineage size at which stance weight hits 0 (None => 20)
    XEXAM_SHARE: float = 0.15
    RESEED_DIST_MIN: float | None = None
    # Embedder-AGNOSTIC school-convergence firing path (detection.raw_flags):
    # school_convergence also fires when inter_school_dist_ratio (min inter-
    # school centroid distance / mean within-stream pairwise distance) drops
    # below this. RESEED_DIST_MIN is an ABSOLUTE distance and must be calibrated
    # to the embedder (the HashingEmbedder runs hot, ~0.6-0.9, so the shipped
    # 0.15 can never fire); this ratio is scale-free (~1.0 = as separated as the
    # stream, ->0 = converged). Default 0.3: conservative (fires only on strong
    # convergence), safe under any embedder including the hashing default —
    # a live run shipped with every convergence tripwire silently off. None
    # disables; calibrate against views/basin.embedder_calibration to tighten.
    RESEED_RATIO_MAX: float | None = 0.3
    # Refuted-attractor orbiting floor (basin study, docs/BASIN_REPORT.md):
    # gate blocks per CAPTURE_W event window before the ladder rotates the
    # orbiting school's stance. Healthy runs measured exactly 0; orbiting
    # runs ~7 per 20 events. Default ON — zero false fires across every
    # committed root. None disables.
    GATE_ORBIT_MIN: int | None = 5
    NEAR_DUP_EPS: float | None = None
    VS_K: int = 6
    # Conjecture-pack shaping (attention only, never status). Defaults
    # reproduce prior behavior exactly; the basin study manipulates them.
    NEIGHBOURHOOD_N: int = 8  # exemplars shown per conj pack (0 = blind)
    COMPLEMENT_ALWAYS: bool = False  # force the §11.4 complement directive every cycle
    PARETO_AXES: list[str] = Field(default_factory=lambda: ["hv", "reach", "coverage"])
    # Grounding-ratio alarm line (spec §11.3): the grounding-decay brake
    # fires when windowed λ drops below this. Default 0.3 (the live-run
    # profile's value): program-heavy runs peg spec-λ at 1.0 and never trip
    # it, so the default only bites where it should — rubric-heavy runs
    # drifting away from exogenous anchors. None disables (explicit
    # replay/experiment configurations only).
    LAMBDA_FLOOR: float | None = 0.3
    # Opt-in: drive the grounding-decay brake off the stricter evidence_lambda
    # (fraction of observation_valued claims actually covered by external
    # evidence) instead of the spec lambda (which counts internal well-
    # formedness program checks as grounding, so it pegs at 1.0 on
    # program-heavy runs and the brake never fires). Default False preserves
    # spec §11.3 semantics and the §11.8 experiment; evidence_lambda is always
    # reported as a diagnostic regardless. Only bites when the run makes
    # empirical claims — a pure design problem reads N/A and never trips it.
    GROUNDING_USE_EVIDENCE_LAMBDA: bool = False
    CAPTURE_W: int = 20
    # Adjudication-ritual thresholds (§11.3; empirical per family/domain, §17)
    ATTACK_ENTROPY_FLOOR: float = 0.2
    CRIT_DEBT_CEILING: float = 0.5
    MIN_ATTACKS_FOR_RITUAL: int = 5
    # Reach (Def 3.7 as amended): a foreign problem's qualifying
    # (substantive, evaluable) criteria must cover at least this fraction of
    # its TOTAL criteria for a full reach hit (which registers addressing and
    # can raise explanation debt); below it the hit is provisional - logged,
    # grounding nothing. Guards against reach minted from thin or unguarded
    # batteries (rubric-heavy problems stay provisional until their guarded
    # procedures put survivals on the record).
    REACH_COVERAGE_MIN: float = 0.5
    # Research (§12)
    RESEARCH_PERIOD: int = 5  # cycles between research fetches (standing exogenous schedule)
    # Research service mode (§12; research/backends.py:build_service):
    #   "agent" (default)  — the operating agent retrieves; the harness
    #                        exposes ops.research_docket and accepts
    #                        ops.submit_evidence. Research is ACTIVE.
    #   "static:<file>"    — deterministic local fixture backend (curated
    #                        offline evidence; NOT local RAG — no indexing).
    #   "ask-user"         — attended human retrieval (see RESEARCH_ATTENDED).
    #   null               — research deliberately DISABLED (tests, explicit
    #                        offline runs, the pre-registered lambda=0 arm).
    #                        Logged as research-off when requests go unmet.
    # Invalid values fail loudly at startup. Do not mutate this mid-run out
    # of band: a backend-policy change affects scheduling and must be part
    # of the replayable run history (use separate runs/configs).
    RESEARCH_BACKEND: str | None = "agent"
    # Attended vs unattended is explicit and replay-visible: only an
    # attended run may surface ask-user questions synchronously; unattended
    # runs never block — requests stay visible in the docket.
    RESEARCH_ATTENDED: bool = False
    # Internal-retrieval futility bounds (attention only, never status):
    # cycles between attempts per problem, and the per-strategy attempt cap
    # after which internal fetching pauses (research-fetch-exhausted). The
    # agent channel can still cover an exhausted problem at any time.
    RESEARCH_COOLDOWN: int = Field(default=3, ge=0)
    RESEARCH_ATTEMPTS_MAX: int = Field(default=5, gt=0)
    # Budget triage (§14; attention only, never status)
    ARG_CRIT_PER_CYCLE: int | None = None      # cap argumentative-critic TARGETS per cycle
    RUBRIC_TRIALS_PER_ARTIFACT: int | None = None  # cap rubric trials per artifact per cycle
    # Batch criticism (docs/TOKEN_ECONOMY.md angle 3): up to this many
    # admitted targets share ONE argumentative-critic call; warrants remain
    # per-target. None = one call per target (legacy behavior).
    CRIT_BATCH_K: int | None = None
    # Criticism authority (bronze postrun repair, RC1): what a prose-only
    # argumentative case may do to a NON-execution-backed target.
    #   observe_only   - the case registers as scrutiny evidence (critic-role
    #                    artifact, no warrant) plus a Measure; no status change.
    #   trial_required - the case goes to the defended cross-family trial;
    #                    only a guard-accepted sustained ruling mints the
    #                    ARGUMENTATIVE warrant.
    #   legacy_direct  - pre-repair behavior: the critic's self-authored
    #                    validity node certifies the case. Explicit opt-in for
    #                    replay of old roots and pre-registered experiments.
    # Demonstrative outcomes (counterexamples, program/verifier failures)
    # remain status-changing under every mode.
    ARGUMENTATIVE_AUTHORITY: Literal[
        "observe_only", "trial_required", "legacy_direct"
    ] = "observe_only"
    # LLM-mediated text adjudication has its own policy surface.  A status
    # mode is prospective only: schema-v2 text manifests preflight it against
    # CALIBRATION_RECEIPT before any endpoint is built.  observe_only records
    # scrutiny/comparison data without creating a warrant or attack edge.
    TEXT_RUBRIC_AUTHORITY: TextAuthorityMode = TextAuthorityMode.OBSERVE_ONLY
    PAIRWISE_AUTHORITY: TextAuthorityMode = TextAuthorityMode.OBSERVE_ONLY
    INFRASTRUCTURE_REVIEW_AUTHORITY: TextAuthorityMode = TextAuthorityMode.OBSERVE_ONLY
    # Immutable reference to the calibration receipt that authorizes a
    # calibrated text-status mode. The manifest stores this source config
    # field; preflight fails closed when a status mode omits the reference.
    CALIBRATION_RECEIPT: str | None = None
    # Default text runs do not spend judge tokens on rubric trials.  Setting a
    # positive budget opts into bounded advisory trials only while the rubric
    # authority remains observe_only.
    ADVISORY_TRIALS_PER_CYCLE: int = Field(default=0, ge=0)
    # Counterexample feedback retries (§3 execution supremacy): when an attack
    # on an execution-backed target fails to ground (missing / gate-rejected /
    # property-held counterexample), re-ask the critic up to this many times
    # WITH the deterministic rejection reason echoed back — the gate's verdict
    # is information the one-shot caller otherwise never sees. 0 disables.
    CX_RETRY_MAX: int = 1
    # Standing re-criticism (§14 attention only): unused ARG_CRIT_PER_CYCLE
    # slots sweep ACCEPTED artifacts with no warrant on record (round-robin,
    # execution-oracle carriers first). Off = legacy behavior, where an
    # artifact is only criticized in the cycle it was admitted and anything
    # accepted early is never attacked again (accepted-by-neglect).
    RECRIT_STANDING: bool = True
    # Deterministic fuzz criticism (§3): inputs enumerated per property-oracle
    # commitment carrying a generator (def gen(k), pure in k). The harness
    # experiments mechanically — sandboxed executions, zero LLM calls, replay-
    # stable. 0 disables.
    FUZZ_N: int = 64
    # Experiment design (rules/experiment.py): every this-many cycles, ask the
    # EXPERIMENTER (conjecturer endpoint, experimenter template) to propose
    # def gen(k) input generators for a property oracle that has fewer than
    # GEN_MAX accepted ones. Proposals are adjudicated mechanically
    # (generator_wf: compile/yield/novelty) — no judge. 0 disables.
    GEN_PROPOSE_PERIOD: int = 5
    GEN_MAX: int = 3
    # Proposed properties (rules/experiment.py): every this-many cycles, ask
    # the property_designer role to conjecture correctness properties the
    # problem statement demands but the current checker does not enforce.
    # Adjudication: checker_wf (mechanical non-vacuity) + cross-family
    # relevance trial (unanimity) + population wipeout guard at use time +
    # the source-artifact att closure (refute the property => its verdicts
    # collapse). Requires the property_designer AND judge roles. 0 disables.
    PROP_PROPOSE_PERIOD: int = 7
    PROP_MAX: int = 3
    # Discrimination futility backoff (§14 attention only; the run-3
    # starvation: an order-swap-deadlocked pairwise trial stayed 'unsolved'
    # and won unsolved-first selection 18 times while the root problem got
    # one conjecturer call). Each attempt starts a cooldown; after the cap
    # the problem is paused permanently — recorded as unresolved, never
    # retried into starvation. None = unlimited attempts (legacy).
    DISC_ATTEMPTS_MAX: int | None = 3
    DISC_COOLDOWN: int = 4
    # Lazy HV spot-checks ask the variator for K whole-content edits in one
    # JSON reply; on app-sized artifacts (multi-KB HTML) that reliably blows
    # the completion window (observed live: 9 dropped variator calls in one
    # run, all length-limit). Artifacts whose content exceeds this many chars
    # are skipped by _lazy_hv (attention-only machinery — skipping estimates
    # is legal; skipping criticism would not be), logged once as
    # hv-skip-oversize. None disables the gate.
    HV_CONTENT_MAX_CHARS: int | None = 8000
    # Browser oracle (rules/act.py): app candidates carrying browser
    # commitments are rendered + driven in headless Chromium, at most this
    # many NEW runs per cycle (each is one exogenous evidence registration;
    # re-runs never happen — pending() guards). 0 disables.
    BROWSER_PER_CYCLE: int = 1
    # Vision criticism (rules/vision.py): targets with recorded screenshots
    # get one vision-critic look each, at most this many calls per cycle.
    # Requires the vision_critic role. 0 disables.
    VISION_CRIT_PER_CYCLE: int = 1
    # The ratchet: an active property older than this many EVENTS is promoted
    # — it may then refute without population support (the standard holds the
    # line even when every current candidate fails it). Promotion is trust,
    # never finality: the source-artifact closure still collapses a promoted
    # property's verdicts if it is ever refuted. 0 disables promotion.
    PROP_PROBATION_EVENTS: int = 80
    # Focus lock (attention only): when set, the scheduler works ONLY this
    # problem — used by controlled experiments to eliminate side-problem
    # dilution (spawn triggers still record problems; they are just unworked).
    FOCUS_PROBLEM: str | None = None
    # Family lock (attention only): when set, selection is restricted to the
    # named problem's transitive FAMILY — the problem plus everything spawned
    # from it or from artifacts addressing it (successors, discriminations,
    # lineage problems). Unlike FOCUS_PROBLEM, in-family successor iteration
    # keeps working. Used by staged pipelines (easy.make: plan -> design ->
    # build) so one stage's leftovers cannot out-age the next stage's seed
    # under the liveness queue. FOCUS_PROBLEM takes precedence when both set.
    FOCUS_FAMILY: str | None = None
    # Level-2 diversity injection always-on (llm/specs.py); the stagnation
    # ladder can also switch it on reactively (§11.4).
    SPEC_INJECTION: bool = False
    # Self-calibration liveness queue (docs/CONTROLLER_SPEC.md): replaces
    # unsolved-first rotation with aging priority (age x unsolvedness) so no
    # registered problem starves. Attention only, never status. Default ON
    # since the ground-truth run-3 starvation: under unsolved-first, a SOLVED
    # root problem is never selected while ANY unsolved spawn exists, so the
    # very process that could overturn its survivor is starved by that
    # survivor's own acceptance. False = legacy unsolved-first.
    LIVENESS_QUEUE: bool = True
    # Self-calibration controller (docs/CONTROLLER_SPEC.md, controller.py):
    # process-signal-driven live tuning of generator knobs inside safe
    # envelopes. Default ON for every run built through ops.run_scheduler —
    # a live run shipped without it (it was reachable only via a research
    # script flag) and the loop could not heal its own transport failures.
    # False = no controller (controlled experiments, replay of old roots).
    CONTROLLER: bool = True
    # Embedder (§9, §11.5): default is the neural model (E0.1,
    # experiments/results/e01_embedder_recalibration_report.json: hashing
    # novelty rankings demoted to unverified; contamination 1.0/1.0). Set to
    # None for the zero-dependency HashingEmbedder (lexical geometry) —
    # controlled experiments and replay of old roots. Requires the optional
    # dependency group (pip install 'deepreason[embed]'); first use fetches
    # ~0.5 GB of ONNX weights. If the backend is unavailable at run start
    # the scheduler falls back to hashing and records `embedder-fallback`
    # on the log, so offline installs keep working. EVERY distance threshold
    # (NEAR_DUP_EPS, RESEED_DIST_MIN, atlas radii) is scale-specific:
    # recalibrate via `deepreason calibrate` (views/basin.threshold_calibration)
    # before trusting a config on a new embedder — the adjudicated record in
    # runs/embedder_design refuted every blind distribution-mapping shortcut.
    EMBEDDER_MODEL: str | None = "nomic-ai/nomic-embed-text-v1.5"
    # "fallback" (interactive default): unavailable backend degrades to
    # hashing with an embedder-fallback measure. "error" (evidence mode):
    # the run fails BEFORE the first model call rather than silently
    # swapping the geometry instrument.
    EMBEDDER_FAILURE_POLICY: Literal["fallback", "error"] = "fallback"
    # Chunked website builds (manifest.py, easy.py): components are bounded
    # fragments composed by the deterministic assembler. CHUNK_MAX_CHARS is
    # the default per-fragment size commitment (a manifest entry may set a
    # tighter own bound); WEBSITE_CHUNKED False falls back to the legacy
    # one-giant-page build — an explicit compatibility option, kept for
    # replaying old roots, never a way to skip capture machinery.
    CHUNK_MAX_CHARS: int = 4000
    WEBSITE_CHUNKED: bool = True
    # Runtime project imports (imports.py): one nested, typed policy. Keeping
    # this under a single field prevents package-security and byte-budget
    # controls from drifting into unrelated controller/transport settings.
    IMPORT_POLICY: ImportPolicy = Field(default_factory=ImportPolicy)
    # LLM adapter (§9)
    PACK_TOKEN_BUDGET: int = 2500
    RETRY_MAX: int = 2
    roles: dict[
        str,
        dict[str, Any] | list[dict[str, Any]] | None,
    ] = Field(default_factory=dict)

    @field_validator("roles")
    @classmethod
    def _validate_roles(cls, value):
        for role, configured in value.items():
            if configured is None:
                continue
            seats = configured if isinstance(configured, list) else [configured]
            if not seats:
                raise ValueError(f"role {role!r} has an empty endpoint ensemble")
            for index, seat in enumerate(seats):
                try:
                    EndpointSpec.model_validate(seat)
                except ValueError as error:
                    raise ValueError(
                        f"invalid endpoint for role {role!r} seat {index}: {error}"
                    ) from error
        return value


def load(path: Path | None = None) -> Config:
    """Load a partial YAML profile over the canonical typed defaults.

    With no path, no file-system lookup occurs: installed packages, the CLI,
    MCP, tests, and scripts all receive exactly ``Config()``.
    """
    if path is None:
        return Config()
    data = yaml.safe_load(Path(path).read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"config profile must be a mapping: {path}")
    return Config.model_validate(data)


def parse_overrides(items: Iterable[str]) -> dict[str, Any]:
    """Parse repeatable ``KEY=YAML_VALUE`` command-line overrides."""
    parsed: dict[str, Any] = {}
    for item in items:
        key, separator, raw = item.partition("=")
        if not separator or not key.strip():
            raise ValueError(f"invalid config override {item!r}; expected KEY=VALUE")
        parsed[key.strip()] = parse_value(raw)
    return parsed


def parse_value(raw: str) -> Any:
    """Parse one command-line value with the profile's YAML scalar rules."""
    return yaml.safe_load(raw)


def apply_overrides(config: Config, values: Mapping[str, Any]) -> Config:
    """Return a revalidated config with top-level or dotted-path overrides.

    Dotted role paths such as ``roles.conjecturer.reasoning`` and indexed
    ensemble paths such as ``roles.judge.1.model`` use the same validation as
    a YAML profile. Unknown paths fail loudly instead of becoming inert knobs.
    """
    data = config.model_dump(mode="python")
    for path, value in values.items():
        parts = path.split(".")
        cursor: Any = data
        for part in parts[:-1]:
            if isinstance(cursor, list):
                try:
                    index = int(part)
                except ValueError as error:
                    raise ValueError(f"config path {path!r}: {part!r} is not a list index") from error
                if index < 0 or index >= len(cursor):
                    raise ValueError(f"unknown config path: {path}")
                cursor = cursor[index]
            elif isinstance(cursor, dict) and part in cursor:
                cursor = cursor[part]
            elif parts[0] == "roles" and cursor is data["roles"]:
                cursor[part] = {}
                cursor = cursor[part]
            else:
                raise ValueError(f"unknown config path: {path}")
        leaf = parts[-1]
        if isinstance(cursor, list):
            try:
                index = int(leaf)
            except ValueError as error:
                raise ValueError(f"config path {path!r}: {leaf!r} is not a list index") from error
            if index < 0 or index >= len(cursor):
                raise ValueError(f"unknown config path: {path}")
            cursor[index] = value
        elif isinstance(cursor, dict) and (
            leaf in cursor
            or (parts[0] == "roles" and leaf in EndpointSpec.model_fields)
            or (parts[0] == "roles" and cursor is data["roles"])
        ):
            cursor[leaf] = value
        else:
            raise ValueError(f"unknown config path: {path}")
    return Config.model_validate(data)


def role_api_key_envs(
    config: Config,
    roles: Iterable[str] | None = None,
) -> set[str]:
    """Environment-variable names referenced by selected enabled roles."""
    names: set[str] = set()
    selected = config.roles.values() if roles is None else (
        config.roles.get(role) for role in roles
    )
    for configured in selected:
        seats = configured if isinstance(configured, list) else [configured]
        for seat in seats:
            if isinstance(seat, dict) and seat.get("endpoint") and seat.get("api_key_env"):
                names.add(str(seat["api_key_env"]))
    return names
