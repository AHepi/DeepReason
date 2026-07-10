"""Config loading (spec §15) — single exposed knob file (config/default.yaml).

Knobs whose spec start value is "tune" load as None and must be set before
the phases that consume them.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Config(BaseModel):
    model_config = {"extra": "allow"}

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
    # stream, ->0 = converged). None (default) = disabled: opt in and calibrate
    # against views/basin.embedder_calibration before trusting it in a config.
    RESEED_RATIO_MAX: float | None = None
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
    LAMBDA_FLOOR: float | None = None
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
    # Budget triage (§14; attention only, never status)
    ARG_CRIT_PER_CYCLE: int | None = None      # cap argumentative-critic TARGETS per cycle
    RUBRIC_TRIALS_PER_ARTIFACT: int | None = None  # cap rubric trials per artifact per cycle
    # Batch criticism (docs/TOKEN_ECONOMY.md angle 3): up to this many
    # admitted targets share ONE argumentative-critic call; warrants remain
    # per-target. None = one call per target (legacy behavior).
    CRIT_BATCH_K: int | None = None
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
    # Embedder (§9, §11.5): None = HashingEmbedder (zero-dependency default,
    # lexical geometry). Set a fastembed model id to enable NeuralEmbedder —
    # verified on this repo: "BAAI/bge-small-en-v1.5" (prose margins) and
    # "jinaai/jina-embeddings-v2-base-code" (code margins); requires the
    # optional dependency group (pip install 'deepreason[embed]'). If the
    # backend is unavailable at run start the scheduler falls back to hashing
    # and records `embedder-fallback` on the log. EVERY distance threshold
    # (NEAR_DUP_EPS, RESEED_DIST_MIN, atlas radii) is scale-specific:
    # recalibrate via `deepreason calibrate` (views/basin.threshold_calibration)
    # before trusting a config on a new embedder — the adjudicated record in
    # runs/embedder_design refuted every blind distribution-mapping shortcut.
    EMBEDDER_MODEL: str | None = None
    # LLM adapter (§9)
    PACK_TOKEN_BUDGET: int = 2500
    RETRY_MAX: int = 2
    roles: dict = Field(default_factory=dict)


def load(path: Path | None = None) -> Config:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "default.yaml"
    with open(path) as f:
        return Config.model_validate(yaml.safe_load(f) or {})
