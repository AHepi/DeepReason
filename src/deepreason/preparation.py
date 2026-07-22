"""Idempotent question-to-bound-V6 preparation with no provider dispatch."""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from deepreason.application.models import RunBudgetIntentV1
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.cli.doctor import (
    load_production_contract_report,
    validate_production_contract_qualification,
    write_production_contract_report,
)
from deepreason.config import Config
from deepreason.evidence.models import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
)
from deepreason.evidence.state import (
    bind_run_input,
    load_evidence_dossier,
    load_run_input,
    verify_run_input,
)
from deepreason.locking import ProcessLock
from deepreason.provider_profile import (
    ProviderProfileError,
    ProviderProfileV1,
    ResolvedProviderProfileV1,
    credential_present,
    provider_state_dir,
    resolve_provider_profile,
)
from deepreason.qualification import (
    QualificationExecutor,
    project_qualification_report,
    qualification_subject_digest,
    resolve_completed_qualification,
)
from deepreason.run_manifest import (
    MANIFEST_NAME,
    V3_CANONICAL_ROLES,
    bind_run_manifest,
    compile_run_manifest,
    load_run_manifest,
)
from deepreason.v6_policy import (
    POLICY_PRESET_ID,
    conservative_control_plane_policy_v3,
    conservative_policy_digest,
)
from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem


PREPARATION_RECORD_NAME = "run-preparation.json"
PREPARATION_SCHEMA = "deepreason-run-preparation.v1"
_REQUEST_DOMAIN = b"deepreason.run-preparation-request.v1\x00"
_RECORD_DOMAIN = b"deepreason.run-preparation-record.v1\x00"
_QUESTION_DOMAIN = b"deepreason.question.v1\x00"
_DIGEST = r"^[0-9a-f]{64}$"
_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAX_RECORD_BYTES = 128 * 1024


class RunPreparationError(ValueError):
    """Stable, secret-free failure from the managed preparation boundary."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class RunPreparationRequestV1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        populate_by_name=True,
        serialize_by_alias=True,
        hide_input_in_errors=True,
    )

    schema_: Literal["deepreason-run-preparation-request.v1"] = Field(
        "deepreason-run-preparation-request.v1", alias="schema"
    )
    question: str = Field(min_length=1, max_length=262_144)
    budget: RunBudgetIntentV1
    profile_path: str | None = Field(default=None, min_length=1, max_length=4_096)
    managed_run_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("question")
    @classmethod
    def _question_is_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must be nonblank")
        return value

    @field_validator("profile_path")
    @classmethod
    def _path_has_no_nul(cls, value: str | None) -> str | None:
        if value is not None and "\x00" in value:
            raise ValueError("provider profile path cannot contain NUL")
        return value

    @field_validator("managed_run_id")
    @classmethod
    def _run_id_is_safe(cls, value: str | None) -> str | None:
        if value is not None and _RUN_ID.fullmatch(value) is None:
            raise ValueError("managed_run_id contains unsafe characters")
        return value


class RunPreparationRecordV1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    schema_: Literal["deepreason-run-preparation.v1"] = Field(
        PREPARATION_SCHEMA, alias="schema"
    )
    record_digest: str = Field(pattern=_DIGEST)
    managed_run_id: str = Field(min_length=1, max_length=128)
    request_digest: str = Field(pattern=_DIGEST)
    question_digest: str = Field(pattern=_DIGEST)
    problem_id: str = Field(min_length=1, max_length=512)
    budget: RunBudgetIntentV1
    provider_profile_digest: str = Field(pattern=_DIGEST)
    policy_preset_id: Literal["deepreason.v6.conservative.v1"] = POLICY_PRESET_ID
    policy_preset_digest: str = Field(pattern=_DIGEST)
    qualification_subject_digest: str = Field(pattern=_DIGEST)
    qualification_bundle_digest: str = Field(pattern=_DIGEST)
    qualification_report_sha256: str = Field(pattern=_DIGEST)
    dossier_digest: str = Field(pattern=_DIGEST)
    run_input_digest: str = Field(pattern=_DIGEST)
    run_manifest_sha256: str = Field(pattern=_DIGEST)
    compiled_at: str = Field(min_length=1, max_length=128)

    def identity_payload(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json", by_alias=True, exclude={"record_digest"}
        )

    @classmethod
    def create(cls, **values: Any) -> "RunPreparationRecordV1":
        provisional = cls.model_construct(record_digest="0" * 64, **values)
        payload = provisional.model_dump(
            mode="json", by_alias=True, exclude={"record_digest"}
        )
        return cls(
            record_digest=sha256_hex(_RECORD_DOMAIN + canonical_json(payload)),
            **values,
        )

    @model_validator(mode="after")
    def _identity_matches(self):
        expected = sha256_hex(_RECORD_DOMAIN + canonical_json(self.identity_payload()))
        if self.record_digest != expected:
            raise ValueError("preparation record digest is inconsistent")
        if _RUN_ID.fullmatch(self.managed_run_id) is None:
            raise ValueError("preparation record has an unsafe managed run id")
        return self


class PreparedRunV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_: Literal["deepreason-prepared-run.v1"] = Field(
        "deepreason-prepared-run.v1", alias="schema"
    )
    root: str
    managed_run_id: str
    run_manifest_ref: str
    manifest_digest: str = Field(pattern=_DIGEST)
    run_input_digest: str = Field(pattern=_DIGEST)
    qualification_subject_digest: str = Field(pattern=_DIGEST)
    profile_source: Literal["explicit", "environment", "setup"]
    credential_present: Literal[True] = True
    workload: ReasoningWorkloadSpec
    budget: RunBudgetIntentV1


def _question_digest(question: str) -> str:
    return sha256_hex(_QUESTION_DOMAIN + question.encode("utf-8"))


def _qualification_report_sha256(report) -> str:
    payload = canonical_json(
        report.model_dump(mode="json", by_alias=True, exclude_none=True)
    ) + b"\n"
    return sha256_hex(payload)


def _request_digest(
    request: RunPreparationRequestV1,
    profile: ProviderProfileV1,
) -> str:
    payload = {
        "schema": "deepreason-run-preparation-request-identity.v1",
        "question": request.question,
        "budget": request.budget.model_dump(mode="json", by_alias=True),
        "provider_profile_digest": profile.profile_digest,
        "policy_preset_id": POLICY_PRESET_ID,
        "policy_preset_digest": conservative_policy_digest(),
    }
    return sha256_hex(_REQUEST_DOMAIN + canonical_json(payload))


def _config_for_profile(profile: ProviderProfileV1) -> Config:
    endpoint = profile.endpoint_spec()
    return Config(
        engine_profile="full",
        model_profile=profile.model_profile,
        roles={role: dict(endpoint) for role in V3_CANONICAL_ROLES},
    )


def _records_for_question(
    question: str,
) -> tuple[EvidenceDossierV1, RunInputManifestV2, ReasoningWorkloadSpec]:
    question_hash = _question_digest(question)
    problem_id = f"question-{question_hash[:32]}"
    provenance = AttachedSourceProvenanceV1(
        supplied_by="deepreason.bootstrap",
        acquisition_method="question-only preparation",
        note="No attached evidence was supplied.",
    )
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=provenance,
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id=problem_id,
            description=question,
            criteria=(),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
        brain_snapshot_digest=None,
    )
    workload = ReasoningWorkloadSpec(
        problem=WorkloadProblem(id=problem_id, description=question),
        criteria=(),
        sources=(),
    )
    return dossier, run_input, workload


def _compiled_at(clock: Callable[[], datetime]) -> str:
    value = clock()
    if value.tzinfo is None:
        raise RunPreparationError(
            "PREPARATION_CLOCK_INVALID", "preparation clock must include a timezone"
        )
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_record(path: Path) -> bytes:
    try:
        observed = path.lstat()
    except FileNotFoundError as error:
        raise RunPreparationError(
            "PREPARATION_ROOT_UNMANAGED",
            "existing run root has no complete managed preparation record",
        ) from error
    except OSError as error:
        raise RunPreparationError(
            "PREPARATION_RECORD_UNAVAILABLE",
            "managed preparation record cannot be inspected safely",
        ) from error
    if (
        not stat.S_ISREG(observed.st_mode)
        or stat.S_ISLNK(observed.st_mode)
        or not 1 <= observed.st_size <= _MAX_RECORD_BYTES
    ):
        raise RunPreparationError(
            "PREPARATION_RECORD_UNSAFE",
            "managed preparation record must be a bounded regular file",
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            payload = stream.read(_MAX_RECORD_BYTES + 1)
        current = path.lstat()
    except OSError as error:
        raise RunPreparationError(
            "PREPARATION_RECORD_UNAVAILABLE",
            "managed preparation record cannot be read safely",
        ) from error
    if (
        not stat.S_ISREG(opened.st_mode)
        or len(payload) != opened.st_size
        or len(payload) > _MAX_RECORD_BYTES
        or not stat.S_ISREG(current.st_mode)
        or current.st_size != opened.st_size
        or (
            opened.st_ino
            and current.st_ino
            and (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino)
        )
    ):
        raise RunPreparationError(
            "PREPARATION_RECORD_UNSAFE",
            "managed preparation record changed while being read",
        )
    return payload


def load_preparation_record(root: Path | str) -> RunPreparationRecordV1:
    path = Path(root) / PREPARATION_RECORD_NAME
    try:
        payload = _read_record(path)
        decoded = json.loads(payload)
        record = RunPreparationRecordV1.model_validate(decoded)
    except RunPreparationError:
        raise
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        RecursionError,
        ValidationError,
        TypeError,
    ):
        raise RunPreparationError(
            "PREPARATION_RECORD_INVALID",
            "managed preparation record is invalid",
        ) from None
    canonical = canonical_json(record.model_dump(mode="json", by_alias=True)) + b"\n"
    if payload != canonical:
        raise RunPreparationError(
            "PREPARATION_RECORD_NONCANONICAL",
            "managed preparation record is not in canonical form",
        )
    return record


def _write_preparation_record(record: RunPreparationRecordV1, root: Path) -> None:
    path = root / PREPARATION_RECORD_NAME
    payload = canonical_json(record.model_dump(mode="json", by_alias=True)) + b"\n"
    path.write_bytes(payload)


class RunPreparationService:
    """Own profile resolution, reusable qualification, and immutable V6 binding."""

    def __init__(
        self,
        *,
        runs_dir: Path | str | None = None,
        qualification_cache_dir: Path | str | None = None,
        environ: Mapping[str, str] | None = None,
        home: Path | str | None = None,
        qualification_executor: QualificationExecutor | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._environ = os.environ if environ is None else environ
        state = provider_state_dir(home=home, environ=self._environ)
        self._runs_dir = Path(runs_dir) if runs_dir is not None else state / "runs"
        self._cache_dir = (
            Path(qualification_cache_dir)
            if qualification_cache_dir is not None
            else state / "qualification-cache"
        )
        self._home = home
        self._executor = qualification_executor
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def prepare(
        self,
        request: RunPreparationRequestV1 | Mapping[str, Any],
    ) -> PreparedRunV1:
        request = RunPreparationRequestV1.model_validate(request)
        try:
            resolved = resolve_provider_profile(
                request.profile_path,
                environ=self._environ,
                home=self._home,
            )
        except ProviderProfileError:
            raise
        profile = resolved.profile
        if not credential_present(profile, environ=self._environ):
            raise RunPreparationError(
                "PROVIDER_CREDENTIAL_MISSING",
                f"credential environment variable {profile.credential_env} is absent",
            )

        request_digest = _request_digest(request, profile)
        managed_id = request.managed_run_id or f"run-{request_digest[:32]}"
        root = self._runs_dir / managed_id
        if root.exists():
            return self._load_existing(
                root=root,
                request=request,
                request_digest=request_digest,
                resolved=resolved,
            )

        dossier, run_input, workload = _records_for_question(request.question)
        manifest = compile_run_manifest(
            _config_for_profile(profile),
            schema_version=6,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=_compiled_at(self._clock),
            control_plane_policy=conservative_control_plane_policy_v3(),
            run_input_digest=run_input.run_input_digest,
        )
        bundle = resolve_completed_qualification(
            manifest,
            profile,
            cache_dir=self._cache_dir,
            executor=self._executor,
        )
        report = project_qualification_report(bundle, manifest, profile)
        subject_digest = qualification_subject_digest(manifest, profile)
        record = RunPreparationRecordV1.create(
            managed_run_id=managed_id,
            request_digest=request_digest,
            question_digest=_question_digest(request.question),
            problem_id=run_input.problem.id,
            budget=request.budget,
            provider_profile_digest=profile.profile_digest,
            policy_preset_digest=conservative_policy_digest(),
            qualification_subject_digest=subject_digest,
            qualification_bundle_digest=bundle.bundle_digest,
            qualification_report_sha256=_qualification_report_sha256(report),
            dossier_digest=dossier.dossier_digest,
            run_input_digest=run_input.run_input_digest,
            run_manifest_sha256=manifest.sha256,
            compiled_at=manifest.compiled_at,
        )

        self._runs_dir.mkdir(parents=True, exist_ok=True)
        preparation_lock = self._runs_dir / f".{managed_id}.preparation.lock"
        with ProcessLock(
            preparation_lock,
            owner="run-preparation",
            blocking=True,
        ):
            if root.exists():
                return self._load_existing(
                    root=root,
                    request=request,
                    request_digest=request_digest,
                    resolved=resolved,
                )
            temporary = self._runs_dir / (
                f".{managed_id}.preparing.{uuid.uuid4().hex}"
            )
            try:
                bind_run_input(run_input, dossier, temporary)
                bind_run_manifest(manifest, temporary)
                policy = manifest.production_qualification_policy
                assert policy is not None
                write_production_contract_report(
                    report, temporary / policy.report_filename
                )
                _write_preparation_record(record, temporary)
                temporary.rename(root)
            except Exception:
                if temporary.exists():
                    shutil.rmtree(temporary)
                raise
        return self._result(
            root=root,
            record=record,
            resolved=resolved,
            workload=workload,
            budget=request.budget,
        )

    def _load_existing(
        self,
        *,
        root: Path,
        request: RunPreparationRequestV1,
        request_digest: str,
        resolved: ResolvedProviderProfileV1,
    ) -> PreparedRunV1:
        if not root.is_dir() or root.is_symlink():
            raise RunPreparationError(
                "PREPARATION_ROOT_UNSAFE",
                "managed run identity does not name a regular directory",
            )
        record = load_preparation_record(root)
        if record.request_digest != request_digest:
            raise RunPreparationError(
                "PREPARATION_INPUT_CONFLICT",
                "managed run identity is already bound to different preparation input",
            )
        if record.managed_run_id != root.name:
            raise RunPreparationError(
                "PREPARATION_IDENTITY_MISMATCH",
                "managed preparation record does not match its run-root identity",
            )
        if record.question_digest != _question_digest(request.question):
            raise RunPreparationError(
                "PREPARATION_INPUT_CONFLICT",
                "managed run identity is already bound to another question",
            )
        if record.provider_profile_digest != resolved.profile.profile_digest:
            raise RunPreparationError(
                "PREPARATION_PROFILE_CONFLICT",
                "managed run identity is already bound to another provider profile",
            )
        run_input = load_run_input(root)
        if not isinstance(run_input, RunInputManifestV2):
            raise RunPreparationError(
                "PREPARATION_RUN_INPUT_V2_REQUIRED",
                "managed V6 preparation requires RunInputManifestV2",
            )
        dossier = load_evidence_dossier(root)
        verified = verify_run_input(root)
        manifest = load_run_manifest(root / MANIFEST_NAME)
        if (
            run_input.problem.description != request.question
            or run_input.problem.id != record.problem_id
            or run_input.evidence_dossier_digest != dossier.dossier_digest
            or dossier.problem_ref != record.problem_id
            or verified["run_input_digest"] != record.run_input_digest
            or dossier.dossier_digest != record.dossier_digest
            or manifest.schema_version != 6
            or manifest.run_input_digest != record.run_input_digest
            or manifest.sha256 != record.run_manifest_sha256
            or manifest.compiled_at != record.compiled_at
        ):
            raise RunPreparationError(
                "PREPARATION_BINDING_MISMATCH",
                "managed preparation artifacts do not match their immutable record",
            )
        policy = manifest.production_qualification_policy
        if policy is None:
            raise RunPreparationError(
                "PREPARATION_QUALIFICATION_POLICY_REQUIRED",
                "managed manifest lacks production qualification authority",
            )
        report = load_production_contract_report(root / policy.report_filename)
        validate_production_contract_qualification(report, manifest)
        if record.qualification_report_sha256 != _qualification_report_sha256(report):
            raise RunPreparationError(
                "PREPARATION_QUALIFICATION_PROJECTION_MISMATCH",
                "managed qualification projection differs from its immutable record",
            )
        if (
            record.qualification_subject_digest
            != qualification_subject_digest(manifest, resolved.profile)
        ):
            raise RunPreparationError(
                "PREPARATION_QUALIFICATION_SUBJECT_MISMATCH",
                "managed qualification does not match current behavior authority",
            )
        workload = ReasoningWorkloadSpec(
            problem=WorkloadProblem(
                id=run_input.problem.id,
                description=run_input.problem.description,
            ),
            criteria=(),
            sources=(),
        )
        return self._result(
            root=root,
            record=record,
            resolved=resolved,
            workload=workload,
            budget=request.budget,
        )

    @staticmethod
    def _result(
        *,
        root: Path,
        record: RunPreparationRecordV1,
        resolved: ResolvedProviderProfileV1,
        workload: ReasoningWorkloadSpec,
        budget: RunBudgetIntentV1,
    ) -> PreparedRunV1:
        return PreparedRunV1(
            root=str(root),
            managed_run_id=record.managed_run_id,
            run_manifest_ref=str(root / MANIFEST_NAME),
            manifest_digest=record.run_manifest_sha256,
            run_input_digest=record.run_input_digest,
            qualification_subject_digest=record.qualification_subject_digest,
            profile_source=resolved.source,
            credential_present=True,
            workload=workload,
            budget=budget,
        )


__all__ = [
    "PREPARATION_RECORD_NAME",
    "PreparedRunV1",
    "RunPreparationError",
    "RunPreparationRecordV1",
    "RunPreparationRequestV1",
    "RunPreparationService",
    "load_preparation_record",
]
