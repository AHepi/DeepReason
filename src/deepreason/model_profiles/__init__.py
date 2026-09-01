"""The model-profile registry -- the ONLY legal import surface for per-model facts.

A model's settings are a document a human wrote, not a constant the harness
carries.  Everything a consumer may know about a model comes through the names
re-exported here; reaching past them into ``document`` or ``registry`` is the
bypass ``tests/test_model_profile_registry.py`` exists to catch
(`DR-CON-model-profiles`, the 2026-08-26 modularity law: "enforced" means a
check that can fail).
"""

from deepreason.model_profiles.document import (
    FENCE_INFO,
    SCHEMA_ID,
    ModelProfileError,
    ModelProfileV1,
    ReasoningFactsV1,
    parse_document,
)
from deepreason.model_profiles.registry import (
    MODEL_PROFILE_REGISTRY_VERSION,
    PROFILES_DIRNAME,
    installed,
    profiles_root,
    register,
    registry_fingerprint,
    resolve,
    unregister,
)

__all__ = [
    "FENCE_INFO",
    "MODEL_PROFILE_REGISTRY_VERSION",
    "ModelProfileError",
    "ModelProfileV1",
    "ReasoningFactsV1",
    "PROFILES_DIRNAME",
    "SCHEMA_ID",
    "installed",
    "parse_document",
    "profiles_root",
    "register",
    "registry_fingerprint",
    "resolve",
    "unregister",
]
