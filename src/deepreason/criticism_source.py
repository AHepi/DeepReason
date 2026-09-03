from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

CONTRIBUTION_ONLY_EXPLANATION = (
    "This source can add criticism. It cannot change status, rank, admission, "
    "or candidate visibility, and it cannot remove candidates. The run selects "
    "observation or defended trial separately."
)

_CONTRACT = ConfigDict(extra="forbid", frozen=True, strict=True)
_DIGEST_PATTERN = r"^[0-9a-f]{64}$"


class CriticismSourceManifestV1(BaseModel):
    model_config = _CONTRACT
    schema_version: Literal[1] = 1
    source_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    authority_ceiling: Literal["contribution_only"] = "contribution_only"

    @property
    def sha256(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class CriticismTargetV1(BaseModel):
    model_config = _CONTRACT
    target_id: str = Field(min_length=1)
    content: str
    codec: str = Field(default="text/plain", min_length=1)


class CriticismContributionV1(BaseModel):
    model_config = _CONTRACT
    content: str
    codec: str = Field(default="text/plain", min_length=1)


class CriticismInvocationResultV1(BaseModel):
    model_config = _CONTRACT
    source_id: str
    outcome: Literal["completed", "declined", "unavailable", "error"]
    manifest_digest: str | None = Field(default=None, pattern=_DIGEST_PATTERN)
    contributions: tuple[CriticismContributionV1, ...] = ()
    detail: str | None = None


class CriticismSourceDescriptionV1(BaseModel):
    model_config = _CONTRACT
    source_id: str
    version: str
    summary: str
    manifest_digest: str = Field(pattern=_DIGEST_PATTERN)
    authority_explanation: str


class CriticismSource(Protocol):
    manifest: CriticismSourceManifestV1

    def contribute(self, target: CriticismTargetV1) -> object:
        ...


class CriticismSourceRegistry:
    __slots__ = ("_rows",)

    def __init__(self, sources: Iterable[CriticismSource] = ()) -> None:
        registered: dict[str, tuple[CriticismSourceManifestV1, CriticismSource]] = {}
        for source in sources:
            raw = source.manifest
            material = raw.model_dump(mode="python") if isinstance(raw, BaseModel) else raw
            manifest = CriticismSourceManifestV1.model_validate(material)
            if manifest.source_id in registered:
                raise ValueError(f"CRITICISM_SOURCE_DUPLICATE:{manifest.source_id}")
            registered[manifest.source_id] = (manifest, source)
        self._rows = MappingProxyType(dict(sorted(registered.items())))

    @property
    def manifests(self) -> tuple[CriticismSourceManifestV1, ...]:
        return tuple(row[0] for row in self._rows.values())

    def resolve(self, source_id: str) -> tuple[CriticismSourceManifestV1, CriticismSource] | None:
        return self._rows.get(source_id)


def _contribution(value: object) -> CriticismContributionV1:
    material = value.model_dump(mode="python") if isinstance(value, BaseModel) else value
    return CriticismContributionV1.model_validate(material)


def invoke_criticism_source(
    registry: CriticismSourceRegistry,
    source_id: str,
    target: CriticismTargetV1,
) -> CriticismInvocationResultV1:
    resolved = registry.resolve(source_id)
    if resolved is None:
        return CriticismInvocationResultV1(
            source_id=source_id, outcome="unavailable", detail="CRITICISM_SOURCE_UNAVAILABLE")
    manifest, source = resolved
    try:
        raw = source.contribute(target)
    except Exception:
        return CriticismInvocationResultV1(
            source_id=source_id, outcome="error", manifest_digest=manifest.sha256,
            detail="CRITICISM_SOURCE_EXECUTION_ERROR")
    try:
        if isinstance(raw, (str, bytes)):
            raise TypeError
        values = () if raw is None else ((raw,) if isinstance(raw, (BaseModel, Mapping))
                                         else tuple(raw))  # type: ignore[arg-type]
        contributions = tuple(_contribution(value) for value in values)
    except Exception:
        return CriticismInvocationResultV1(
            source_id=source_id, outcome="error", manifest_digest=manifest.sha256,
            detail="CRITICISM_SOURCE_OUTPUT_INVALID")
    return CriticismInvocationResultV1(
        source_id=source_id, outcome="completed" if contributions else "declined",
        manifest_digest=manifest.sha256, contributions=contributions)


def describe_criticism_sources(registry: CriticismSourceRegistry
                               ) -> tuple[CriticismSourceDescriptionV1, ...]:
    return tuple(
        CriticismSourceDescriptionV1(
            source_id=row.source_id, version=row.version, summary=row.summary,
            manifest_digest=row.sha256,
            authority_explanation=CONTRIBUTION_ONLY_EXPLANATION)
        for row in registry.manifests
    )
