"""Verified, support-inert cross-run skill retrieval and test adoption."""

from deepreason.skills.adoption import (
    CapsuleDependenceError,
    adopt_commitments,
    capsule_ref,
    import_capsule,
    validate_capsule_refs,
)
from deepreason.skills.distill import distill_capsule, distill_lesson
from deepreason.skills.metrics import skill_metrics
from deepreason.skills.models import (
    AdoptionEvaluation,
    AdoptionResult,
    CapsuleDraft,
    DependencyLink,
    LessonMemory,
    PackageCoordinate,
    PassedCommitmentDefinition,
    RankedSkill,
    RawEmbedding,
    RevoicedSkill,
    SchoolSkillSlice,
    SkillCapsule,
    SkillCatalogEntry,
    SkillLibrarySnapshot,
    SkillMetrics,
    SkillRetrievalReceipt,
    ToolchainCoordinate,
    VerifiedDistillationSource,
)
from deepreason.skills.retrieve import render_school_slice, replay_retrieval, retrieve_skills
from deepreason.skills.revoice import RevoiceOverlapError, revoice_capsule
from deepreason.skills.snapshot import snapshot_library
from deepreason.skills.validate import DistillationSourceError, validate_distillation_source

__all__ = [
    "AdoptionEvaluation",
    "AdoptionResult",
    "CapsuleDependenceError",
    "CapsuleDraft",
    "DependencyLink",
    "DistillationSourceError",
    "LessonMemory",
    "PackageCoordinate",
    "PassedCommitmentDefinition",
    "RankedSkill",
    "RawEmbedding",
    "RevoiceOverlapError",
    "RevoicedSkill",
    "SchoolSkillSlice",
    "SkillCapsule",
    "SkillCatalogEntry",
    "SkillLibrarySnapshot",
    "SkillMetrics",
    "SkillRetrievalReceipt",
    "ToolchainCoordinate",
    "VerifiedDistillationSource",
    "adopt_commitments",
    "capsule_ref",
    "distill_capsule",
    "distill_lesson",
    "import_capsule",
    "render_school_slice",
    "replay_retrieval",
    "retrieve_skills",
    "revoice_capsule",
    "skill_metrics",
    "snapshot_library",
    "validate_capsule_refs",
    "validate_distillation_source",
]
