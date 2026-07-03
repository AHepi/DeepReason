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
    NEAR_DUP_EPS: float | None = None
    VS_K: int = 6
    PARETO_AXES: list[str] = Field(default_factory=lambda: ["hv", "reach", "coverage"])
    LAMBDA_FLOOR: float | None = None
    CAPTURE_W: int = 20
    # Adjudication-ritual thresholds (§11.3; empirical per family/domain, §17)
    ATTACK_ENTROPY_FLOOR: float = 0.2
    CRIT_DEBT_CEILING: float = 0.5
    MIN_ATTACKS_FOR_RITUAL: int = 5
    # LLM adapter (§9)
    PACK_TOKEN_BUDGET: int = 2500
    RETRY_MAX: int = 2
    roles: dict = Field(default_factory=dict)


def load(path: Path | None = None) -> Config:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "default.yaml"
    with open(path) as f:
        return Config.model_validate(yaml.safe_load(f) or {})
