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
    # Focus lock (attention only): when set, the scheduler works ONLY this
    # problem — used by controlled experiments to eliminate side-problem
    # dilution (spawn triggers still record problems; they are just unworked).
    FOCUS_PROBLEM: str | None = None
    # Level-2 diversity injection always-on (llm/specs.py); the stagnation
    # ladder can also switch it on reactively (§11.4).
    SPEC_INJECTION: bool = False
    # Self-calibration liveness queue (docs/CONTROLLER_SPEC.md): replaces
    # unsolved-first rotation with aging priority (age x unsolvedness) so no
    # registered problem starves. Attention only, never status.
    LIVENESS_QUEUE: bool = False
    # LLM adapter (§9)
    PACK_TOKEN_BUDGET: int = 2500
    RETRY_MAX: int = 2
    roles: dict = Field(default_factory=dict)


def load(path: Path | None = None) -> Config:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "default.yaml"
    with open(path) as f:
        return Config.model_validate(yaml.safe_load(f) or {})
