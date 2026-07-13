"""Model-facing presentation profiles.

Profiles tune only rendering and transport.  No value in this module is an
ontology field or an input to normative adjudication.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from deepreason.llm.capabilities import ModelCapabilities


class ModelProfile(StrEnum):
    COMPACT = "compact"
    STANDARD = "standard"
    FRONTIER = "frontier"


@dataclass(frozen=True)
class ProfileSpec:
    name: ModelProfile
    pack_tokens_min: int
    pack_tokens_max: int
    max_meaningful_nesting: int
    # Compact fixes VS_K=4. None means preserve the existing configured value.
    vs_k: int | None
    default_concurrency: int
    website_design_mode: str
    direct_contracts: bool
    batching: bool
    parallel_calls: bool
    examples: int

    def pack_budget(self, requested: int | None = None) -> int:
        """Return a finite presentation target.

        An explicit target belongs to the pack profile and may exceed this
        model profile's preset when the frozen route supports it.
        """
        if requested is None:
            return self.pack_tokens_max
        if int(requested) <= 0:
            raise ValueError("pack target must be positive")
        return int(requested)


PROFILES: dict[ModelProfile, ProfileSpec] = {
    ModelProfile.COMPACT: ProfileSpec(
        name=ModelProfile.COMPACT,
        pack_tokens_min=700,
        pack_tokens_max=1200,
        max_meaningful_nesting=2,
        vs_k=4,
        default_concurrency=1,
        website_design_mode="skeleton_first",
        direct_contracts=False,
        batching=False,
        parallel_calls=False,
        examples=1,
    ),
    ModelProfile.STANDARD: ProfileSpec(
        name=ModelProfile.STANDARD,
        pack_tokens_min=1500,
        pack_tokens_max=2500,
        max_meaningful_nesting=4,
        vs_k=None,
        default_concurrency=1,
        website_design_mode="direct_then_skeleton",
        direct_contracts=True,
        batching=True,
        parallel_calls=False,
        examples=1,
    ),
    ModelProfile.FRONTIER: ProfileSpec(
        name=ModelProfile.FRONTIER,
        pack_tokens_min=1500,
        pack_tokens_max=3000,
        max_meaningful_nesting=8,
        vs_k=None,
        default_concurrency=4,
        website_design_mode="direct",
        direct_contracts=True,
        batching=True,
        parallel_calls=True,
        examples=2,
    ),
}


def get_profile(profile: str | ModelProfile | ProfileSpec | None) -> ProfileSpec:
    if isinstance(profile, ProfileSpec):
        return profile
    try:
        name = ModelProfile(profile or ModelProfile.STANDARD)
    except ValueError as exc:
        allowed = ", ".join(p.value for p in ModelProfile)
        raise ValueError(f"unknown model profile {profile!r}; expected {allowed}") from exc
    return PROFILES[name]


def select_profile(capabilities: ModelCapabilities) -> ProfileSpec:
    """Deterministically select a default from measured transport behavior."""
    if (
        capabilities.nested_object_reliability < 0.9
        or capabilities.array_reliability < 0.9
        or capabilities.enum_adherence < 0.9
        or capabilities.long_context_retention < 0.9
    ):
        return PROFILES[ModelProfile.COMPACT]
    if (
        capabilities.native_json_schema
        and capabilities.repair_reliability >= 0.9
        and capabilities.max_reliable_output_tokens >= 3000
    ):
        return PROFILES[ModelProfile.FRONTIER]
    return PROFILES[ModelProfile.STANDARD]


def clip_pack(
    pack: str,
    profile: str | ModelProfile | ProfileSpec,
    requested: int | None = None,
) -> str:
    """A deterministic approximate-token clip for already-rendered packs."""
    spec = get_profile(profile)
    return pack[: spec.pack_budget(requested) * 4]


def apply_profile_to_config(config, profile: str | ModelProfile | ProfileSpec):
    """Return Config with only model-facing process defaults applied.

    This never changes commitments, guards, adjudication, status, or any
    ontology value. Standard/frontier preserve the user's Verbalized Sampling
    count; only compact has the plan-mandated VS_K=4.
    """
    spec = get_profile(profile)
    updates = {
        # Legacy Config has no separate explicit pack-profile field. Preserve
        # its measured preset; reasoning-first PackIR accepts an explicit
        # larger target without mutating this compatibility path.
        "PACK_TOKEN_BUDGET": spec.pack_budget()
    }
    if spec.name == ModelProfile.COMPACT:
        updates.update(VS_K=4, CRIT_BATCH_K=None)
    return config.model_copy(update=updates)
