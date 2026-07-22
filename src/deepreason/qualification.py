"""Reusable, completed-only qualification evidence for V6 preparation.

The existing production doctor qualifies one exact RunManifest.  This module
defines the narrower reusable subject by removing only per-run input identity
and compile time, caches sanitized completed case outcomes, and projects those
outcomes back into the existing exact-manifest report.  Runtime validation
therefore remains the authority for every prepared run.
"""

from __future__ import annotations

import json
import os
import stat
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.cli.doctor import (
    PRODUCTION_CASES_PER_PAIR,
    PRODUCTION_EVENTUAL_VALID_MINIMUM,
    ProductionContractCaseResultV1,
    ProductionContractDoctorReportV1,
    ProductionContractDoctorSummaryV1,
    ProductionContractPairReportV1,
    ProductionContractPairV1,
    derive_route_seat_model_classification,
    production_contract_pairs,
    validate_production_contract_qualification,
)
from deepreason.provider_profile import ProviderProfileV1
from deepreason.run_manifest import RunManifest
from deepreason.v6_policy import POLICY_PRESET_ID, conservative_policy_digest
from deepreason.v6_policy import conservative_control_plane_policy_v3


QUALIFICATION_CACHE_SCHEMA = "deepreason-reusable-qualification.v1"
_SUBJECT_DOMAIN = b"deepreason.qualification-subject.v1\x00"
_PAIR_DOMAIN = b"deepreason.qualification-pair-subject.v1\x00"
_BUNDLE_DOMAIN = b"deepreason.reusable-qualification.v1\x00"
_DIGEST = r"^[0-9a-f]{64}$"
_ROUTE_DIGEST = r"^[0-9a-f]{64}$"
_MAX_CACHE_BYTES = 16 * 1024 * 1024


class QualificationError(ValueError):
    """Stable qualification failure with no provider response content."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class ReusableQualificationPairV1(BaseModel):
    """Sanitized outcomes for one manifest-independent route/contract pair."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pair_subject_digest: str = Field(pattern=_DIGEST)
    contract_id: str = Field(min_length=1, max_length=128)
    role: str = Field(min_length=1, max_length=64)
    seat: StrictInt = Field(ge=0, le=1_023)
    endpoint_id: str = Field(min_length=1, max_length=256)
    route_sha256: str = Field(pattern=_ROUTE_DIGEST)
    model_id: str = Field(min_length=1, max_length=1_024)
    model_revision: str | None = Field(default=None, max_length=1_024)
    provider: str = Field(min_length=1, max_length=128)
    family: str = Field(min_length=1, max_length=256)
    output_mechanism: Literal[
        "native_json_schema", "grammar", "json_text"
    ]
    cases: tuple[ProductionContractCaseResultV1, ...] = Field(
        min_length=PRODUCTION_CASES_PER_PAIR,
        max_length=PRODUCTION_CASES_PER_PAIR,
    )

    def pair_payload(self) -> dict:
        return self.model_dump(
            mode="json",
            exclude={"pair_subject_digest", "cases"},
        )

    @model_validator(mode="after")
    def _identity_and_completed_cases(self):
        if self.pair_subject_digest != _pair_subject_digest(self.pair_payload()):
            raise ValueError("qualification pair subject digest is inconsistent")
        expected_ids = tuple(
            f"case-{index:03d}" for index in range(1, PRODUCTION_CASES_PER_PAIR + 1)
        )
        if tuple(case.case_id for case in self.cases) != expected_ids:
            raise ValueError("qualification pair does not contain one completed case set")
        eventual = sum(case.eventual_valid for case in self.cases)
        if (
            eventual < PRODUCTION_EVENTUAL_VALID_MINIMUM
            or sum(case.alias_failures for case in self.cases)
            or sum(case.scope_violations for case in self.cases)
            or sum(case.semantic_admission for case in self.cases) != eventual
        ):
            raise ValueError(
                "qualification pair does not contain a completed qualified case set"
            )
        return self


class ReusableQualificationBundleV1(BaseModel):
    """One atomic, completed qualification bundle suitable for reuse."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    schema_: Literal["deepreason-reusable-qualification.v1"] = Field(
        QUALIFICATION_CACHE_SCHEMA, alias="schema"
    )
    status: Literal["complete"] = "complete"
    bundle_digest: str = Field(pattern=_DIGEST)
    subject_digest: str = Field(pattern=_DIGEST)
    provider_profile_digest: str = Field(pattern=_DIGEST)
    policy_preset_id: Literal["deepreason.v6.conservative.v1"] = POLICY_PRESET_ID
    policy_preset_digest: str = Field(pattern=_DIGEST)
    pairs: tuple[ReusableQualificationPairV1, ...] = Field(min_length=1)

    def identity_payload(self) -> dict:
        return self.model_dump(
            mode="json", by_alias=True, exclude={"bundle_digest"}
        )

    @classmethod
    def create(cls, **values) -> "ReusableQualificationBundleV1":
        provisional = cls.model_construct(bundle_digest="0" * 64, **values)
        payload = provisional.model_dump(
            mode="json", by_alias=True, exclude={"bundle_digest"}
        )
        return cls(
            bundle_digest=sha256_hex(_BUNDLE_DOMAIN + canonical_json(payload)),
            **values,
        )

    @model_validator(mode="after")
    def _identity_and_inventory(self):
        expected = sha256_hex(_BUNDLE_DOMAIN + canonical_json(self.identity_payload()))
        if self.bundle_digest != expected:
            raise ValueError("qualification bundle digest is inconsistent")
        keys = tuple(item.pair_subject_digest for item in self.pairs)
        if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
            raise ValueError("qualification pairs must be unique and canonically sorted")
        return self


QualificationExecutor = Callable[[RunManifest], ProductionContractDoctorReportV1]


def production_qualification_maximum_provider_calls(manifest: RunManifest) -> int:
    """Return the frozen worst-case call count before qualification dispatch."""

    from deepreason.cli.doctor import _contract_schema_repair_grant

    return sum(
        PRODUCTION_CASES_PER_PAIR
        * _contract_schema_repair_grant(manifest, pair).maximum_provider_calls
        for pair in production_contract_pairs(manifest)
    )


def default_qualification_executor(
    manifest: RunManifest,
) -> ProductionContractDoctorReportV1:
    """Run the production doctor; callers must invoke this explicitly."""

    from deepreason.cli.doctor import run_production_contract_doctor

    return run_production_contract_doctor(manifest)


def _pair_payload(pair: ProductionContractPairV1) -> dict:
    return pair.model_dump(mode="json", exclude={"pair_id"})


def _pair_subject_digest(payload: dict) -> str:
    return sha256_hex(_PAIR_DOMAIN + canonical_json(payload))


def qualification_subject_payload(
    manifest: RunManifest,
    profile: ProviderProfileV1,
) -> dict:
    """Return the closed behavior subject, excluding only per-run identity."""

    if manifest.schema_version != 6:
        raise QualificationError(
            "QUALIFICATION_V6_REQUIRED",
            "reusable production qualification accepts only RunManifest schema 6",
        )
    if manifest.control_plane_policy != conservative_control_plane_policy_v3():
        raise QualificationError(
            "QUALIFICATION_POLICY_PRESET_MISMATCH",
            "reusable qualification requires the repository-owned V6 policy preset",
        )
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
        "policy_preset_digest": conservative_policy_digest(),
        "manifest_behavior": behavior,
        "pair_inventory": pairs,
    }


def qualification_subject_digest(
    manifest: RunManifest,
    profile: ProviderProfileV1,
) -> str:
    return sha256_hex(
        _SUBJECT_DOMAIN + canonical_json(qualification_subject_payload(manifest, profile))
    )


def qualification_cache_path(cache_dir: Path | str, subject_digest: str) -> Path:
    if len(subject_digest) != 64 or any(
        character not in "0123456789abcdef" for character in subject_digest
    ):
        raise QualificationError(
            "QUALIFICATION_SUBJECT_INVALID", "qualification subject digest is invalid"
        )
    return Path(cache_dir) / f"{subject_digest}.json"


def _read_cache(path: Path) -> bytes:
    try:
        observed = path.lstat()
    except FileNotFoundError as error:
        raise QualificationError(
            "QUALIFICATION_NOT_CONFIGURED",
            "no completed reusable qualification exists for this exact subject",
        ) from error
    except OSError as error:
        raise QualificationError(
            "QUALIFICATION_CACHE_UNAVAILABLE",
            "qualification cache cannot be inspected safely",
        ) from error
    if (
        not stat.S_ISREG(observed.st_mode)
        or stat.S_ISLNK(observed.st_mode)
        or not 1 <= observed.st_size <= _MAX_CACHE_BYTES
    ):
        raise QualificationError(
            "QUALIFICATION_CACHE_UNSAFE",
            "qualification cache entry must be a bounded regular file",
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            payload = stream.read(_MAX_CACHE_BYTES + 1)
        current = path.lstat()
    except OSError as error:
        raise QualificationError(
            "QUALIFICATION_CACHE_UNAVAILABLE",
            "qualification cache cannot be read safely",
        ) from error
    if (
        not stat.S_ISREG(opened.st_mode)
        or len(payload) != opened.st_size
        or len(payload) > _MAX_CACHE_BYTES
        or not stat.S_ISREG(current.st_mode)
        or current.st_size != opened.st_size
        or (
            opened.st_ino
            and current.st_ino
            and (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino)
        )
    ):
        raise QualificationError(
            "QUALIFICATION_CACHE_UNSAFE",
            "qualification cache entry changed while being read",
        )
    return payload


class _DuplicateCacheKey(ValueError):
    pass


def load_completed_qualification(
    cache_dir: Path | str,
    subject_digest: str,
) -> ReusableQualificationBundleV1:
    path = qualification_cache_path(cache_dir, subject_digest)

    def reject_duplicates(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise _DuplicateCacheKey
            value[key] = item
        return value

    try:
        payload = _read_cache(path)
        decoded = json.loads(payload, object_pairs_hook=reject_duplicates)
        if isinstance(decoded, dict) and decoded.get("status") != "complete":
            raise QualificationError(
                "QUALIFICATION_INCOMPLETE",
                "incomplete qualification evidence is never reusable",
            )
        bundle = ReusableQualificationBundleV1.model_validate(decoded)
    except QualificationError:
        raise
    except (
        _DuplicateCacheKey,
        json.JSONDecodeError,
        UnicodeDecodeError,
        RecursionError,
        ValidationError,
        TypeError,
    ):
        raise QualificationError(
            "QUALIFICATION_CACHE_INVALID",
            "qualification cache entry is invalid or incomplete",
        ) from None
    canonical = canonical_json(
        bundle.model_dump(mode="json", by_alias=True)
    ) + b"\n"
    if payload != canonical:
        raise QualificationError(
            "QUALIFICATION_CACHE_NONCANONICAL",
            "qualification cache entry is not in canonical form",
        )
    if bundle.subject_digest != subject_digest:
        raise QualificationError(
            "QUALIFICATION_SUBJECT_MISMATCH",
            "qualification cache entry belongs to another behavior subject",
        )
    return bundle


def write_completed_qualification(
    bundle: ReusableQualificationBundleV1,
    cache_dir: Path | str,
) -> Path:
    bundle = ReusableQualificationBundleV1.model_validate(bundle)
    path = qualification_cache_path(cache_dir, bundle.subject_digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(bundle.model_dump(mode="json", by_alias=True)) + b"\n"
    temporary = path.with_name(
        f".{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}"
    )
    try:
        temporary.write_bytes(payload)
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError:
            existing = load_completed_qualification(path.parent, bundle.subject_digest)
            if existing != bundle:
                raise QualificationError(
                    "QUALIFICATION_CACHE_CONFLICT",
                    "different completed evidence already exists for this subject",
                ) from None
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return path


def _reusable_pair(report: ProductionContractPairReportV1) -> ReusableQualificationPairV1:
    payload = _pair_payload(report.pair)
    return ReusableQualificationPairV1(
        pair_subject_digest=_pair_subject_digest(payload),
        cases=report.cases,
        **payload,
    )


def completed_bundle_from_report(
    report: ProductionContractDoctorReportV1,
    manifest: RunManifest,
    profile: ProviderProfileV1,
) -> ReusableQualificationBundleV1:
    validate_production_contract_qualification(report, manifest)
    subject_digest = qualification_subject_digest(manifest, profile)
    pairs = tuple(
        sorted(
            (_reusable_pair(item) for item in report.pairs),
            key=lambda item: item.pair_subject_digest,
        )
    )
    return ReusableQualificationBundleV1.create(
        subject_digest=subject_digest,
        provider_profile_digest=profile.profile_digest,
        policy_preset_digest=conservative_policy_digest(),
        pairs=pairs,
    )


def _pair_report(
    pair: ProductionContractPairV1,
    cases: tuple[ProductionContractCaseResultV1, ...],
) -> ProductionContractPairReportV1:
    eventual = sum(item.eventual_valid for item in cases)
    aliases = sum(item.alias_failures for item in cases)
    scopes = sum(item.scope_violations for item in cases)
    admissions = sum(item.semantic_admission for item in cases)
    return ProductionContractPairReportV1(
        pair=pair,
        cases=cases,
        first_pass_valid_count=sum(item.first_pass_valid for item in cases),
        eventual_valid_count=eventual,
        repair_count=sum(item.repair_count for item in cases),
        alias_failures=aliases,
        scope_violations=scopes,
        semantic_admission_count=admissions,
        qualified=bool(
            len(cases) == PRODUCTION_CASES_PER_PAIR
            and eventual >= PRODUCTION_EVENTUAL_VALID_MINIMUM
            and aliases == 0
            and scopes == 0
            and admissions == eventual
        ),
    )


def project_qualification_report(
    bundle: ReusableQualificationBundleV1,
    manifest: RunManifest,
    profile: ProviderProfileV1,
) -> ProductionContractDoctorReportV1:
    """Bind reusable sanitized cases to one exact manifest and validate it."""

    subject_digest = qualification_subject_digest(manifest, profile)
    if bundle.subject_digest != subject_digest:
        raise QualificationError(
            "QUALIFICATION_SUBJECT_MISMATCH",
            "completed qualification evidence does not cover this exact behavior subject",
        )
    if bundle.provider_profile_digest != profile.profile_digest:
        raise QualificationError(
            "QUALIFICATION_PROFILE_MISMATCH",
            "completed qualification evidence belongs to another provider profile",
        )
    cached = {item.pair_subject_digest: item for item in bundle.pairs}
    reports = []
    for pair in production_contract_pairs(manifest):
        key = _pair_subject_digest(_pair_payload(pair))
        item = cached.pop(key, None)
        if item is None or item.pair_payload() != _pair_payload(pair):
            raise QualificationError(
                "QUALIFICATION_PAIR_INVENTORY_MISMATCH",
                "completed qualification pair inventory differs from the manifest",
            )
        reports.append(_pair_report(pair, item.cases))
    if cached:
        raise QualificationError(
            "QUALIFICATION_PAIR_INVENTORY_MISMATCH",
            "completed qualification contains foreign route/contract pairs",
        )
    pair_reports = tuple(reports)
    summary = ProductionContractDoctorSummaryV1(
        pair_count=len(pair_reports),
        case_count=sum(len(item.cases) for item in pair_reports),
        first_pass_valid_count=sum(item.first_pass_valid_count for item in pair_reports),
        eventual_valid_count=sum(item.eventual_valid_count for item in pair_reports),
        repair_count=sum(item.repair_count for item in pair_reports),
        alias_failures=sum(item.alias_failures for item in pair_reports),
        scope_violations=sum(item.scope_violations for item in pair_reports),
        semantic_admission_count=sum(item.semantic_admission_count for item in pair_reports),
        qualified_pair_count=sum(item.qualified for item in pair_reports),
        qualified=all(item.qualified for item in pair_reports),
    )
    classification = derive_route_seat_model_classification(
        manifest, pairs=pair_reports, summary=summary
    )
    report = ProductionContractDoctorReportV1(
        run_manifest_sha256=manifest.sha256,
        pairs=pair_reports,
        summary=summary,
        route_seat_model_classification=classification,
    )
    return validate_production_contract_qualification(report, manifest)


def resolve_completed_qualification(
    manifest: RunManifest,
    profile: ProviderProfileV1,
    *,
    cache_dir: Path | str,
    executor: QualificationExecutor | None = None,
) -> ReusableQualificationBundleV1:
    """Load completed evidence, or execute only through an injected interface."""

    subject_digest = qualification_subject_digest(manifest, profile)
    try:
        return load_completed_qualification(cache_dir, subject_digest)
    except QualificationError as error:
        if error.code != "QUALIFICATION_NOT_CONFIGURED" or executor is None:
            raise
    try:
        executed = executor(manifest)
    except Exception:
        raise QualificationError(
            "QUALIFICATION_EXECUTION_FAILED",
            "injected qualification execution did not complete successfully",
        ) from None
    try:
        report = ProductionContractDoctorReportV1.model_validate(executed)
    except (ValidationError, TypeError):
        raise QualificationError(
            "QUALIFICATION_EXECUTION_INVALID",
            "injected qualification execution returned invalid sanitized evidence",
        ) from None
    bundle = completed_bundle_from_report(report, manifest, profile)
    write_completed_qualification(bundle, cache_dir)
    return bundle


__all__ = [
    "QUALIFICATION_CACHE_SCHEMA",
    "QualificationError",
    "QualificationExecutor",
    "ReusableQualificationBundleV1",
    "ReusableQualificationPairV1",
    "completed_bundle_from_report",
    "default_qualification_executor",
    "load_completed_qualification",
    "project_qualification_report",
    "production_qualification_maximum_provider_calls",
    "qualification_cache_path",
    "qualification_subject_digest",
    "qualification_subject_payload",
    "resolve_completed_qualification",
    "write_completed_qualification",
]
