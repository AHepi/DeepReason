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
    RunManifestError,
    bind_run_manifest,
    compile_run_manifest,
    load_run_manifest,
)
from deepreason.seat_bindings import (
    resolve_criticism_seats,
    resolve_school_seats,
    resolve_seat_bindings,
    resolve_seat_bindings_by_group,
)
from deepreason.seat_events import SeatBindingsEventPayloadV1, SeatBindingV1
from deepreason.v6_policy import (
    POLICY_PRESET_ID,
    configured_criticism_policy,
    engaged_bridge_source,
    engaged_control_plane_policy_v3,
    engaged_inquiry_capability_policy,
    engaged_policy_digest,
    engaged_scratchpad_source,
    engaged_simulation_toolchain,
    route_bound_school_execution_policy,
)
from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem


PREPARATION_RECORD_NAME = "run-preparation.json"
# Written only when at least one --seat group is bound (Rung S5); a
# default home's prepared root never gets this file at all.
SEAT_BINDINGS_SNAPSHOT_NAME = "seat-bindings.json"
PREPARATION_SCHEMA = "deepreason-run-preparation.v1"
_REQUEST_DOMAIN = b"deepreason.run-preparation-request.v1\x00"
_RECORD_DOMAIN = b"deepreason.run-preparation-record.v1\x00"
_QUESTION_DOMAIN = b"deepreason.question.v1\x00"
_CONFIG_DOMAIN = b"deepreason.run-preparation-config.v1\x00"
_DIGEST = r"^[0-9a-f]{64}$"
_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAX_RECORD_BYTES = 128 * 1024
PUBLIC_DEFAULT_CYCLES = 6
PUBLIC_DEFAULT_TOKEN_BUDGET = 100_000
PUBLIC_MAX_CYCLES = 12
_QUALIFICATION_QUESTION = "DeepReason reusable V6 qualification subject"
_QUALIFICATION_COMPILED_AT = "2000-01-01T00:00:00Z"


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
    budget: RunBudgetIntentV1 = RunBudgetIntentV1(
        cycles=PUBLIC_DEFAULT_CYCLES,
        token_budget=PUBLIC_DEFAULT_TOKEN_BUDGET,
    )
    profile_path: str | None = Field(default=None, min_length=1, max_length=4_096)
    # The operator's run configuration. Absent, preparation compiles from the
    # provider profile alone, byte-identical to before this field existed.
    config_path: str | None = Field(default=None, min_length=1, max_length=4_096)
    managed_run_id: str | None = Field(default=None, min_length=1, max_length=128)
    # An admitted-dossier digest binds attached evidence into the run
    # identity; absent, preparation mints the empty question-only dossier.
    dossier_digest: str | None = Field(default=None, pattern=_DIGEST)

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

    @model_validator(mode="after")
    def _public_budget_is_finite_and_bounded(self):
        if (
            not isinstance(self.budget.cycles, int)
            or self.budget.cycles > PUBLIC_MAX_CYCLES
            or not isinstance(self.budget.token_budget, int)
            or self.budget.token_budget < 1
        ):
            raise ValueError(
                "public budget must be finite and within the fixed V6 policy "
                f"ceiling: cycles <= {PUBLIC_MAX_CYCLES} and token budget "
                f">= 1 (requested cycles={self.budget.cycles}, "
                f"token_budget={self.budget.token_budget})"
            )
        return self


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
    policy_preset_id: Literal["deepreason.v6.engaged.v1"] = POLICY_PRESET_ID
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


def _load_operator_config(config_path: str | None) -> Config | None:
    """Load the operator's configuration, or None when none was named.

    A file that does not parse into the configuration model is not a
    configuration at all (all-configurations law, 2026-08-12: parse/shape
    errors stay refused), so it is a typed refusal at the boundary rather
    than a traceback out of yaml.
    """

    if config_path is None:
        return None
    from deepreason.config import load as load_config

    try:
        return load_config(Path(config_path))
    except (OSError, ValueError) as error:
        raise RunPreparationError(
            "CONFIG_PROFILE_INVALID",
            f"configuration profile could not be loaded: {error}",
        ) from error


def _request_digest(
    request: RunPreparationRequestV1,
    profile: ProviderProfileV1,
    config: Config | None = None,
) -> str:
    payload = {
        "schema": "deepreason-run-preparation-request-identity.v1",
        "question": request.question,
        "budget": request.budget.model_dump(mode="json", by_alias=True),
        "provider_profile_digest": profile.profile_digest,
        "policy_preset_id": POLICY_PRESET_ID,
        "policy_preset_digest": engaged_policy_digest(),
    }
    if request.dossier_digest is not None:
        # Only dossier-bearing requests carry the key, so question-only
        # request digests remain byte-identical to their historical values.
        payload["dossier_digest"] = request.dossier_digest
    if config is not None:
        # Same conditional discipline as dossier_digest above. The digest is
        # over the config's VALUES, not the file's bytes, so reformatting a
        # YAML profile does not mint a second run of the same question.
        payload["config_digest"] = sha256_hex(
            _CONFIG_DOMAIN
            + canonical_json(config.model_dump(mode="json", by_alias=True))
        )
    return sha256_hex(_REQUEST_DOMAIN + canonical_json(payload))


def _school_seat_route_ensemble(
    profile: ProviderProfileV1,
    school_seats: Mapping[str, ProviderProfileV1] | None,
) -> tuple[list, dict[str, tuple[int, str]]]:
    """Extend one role's route into a route ensemble for a school-seat opt-in
    (S2d/R5, Amendment 11/R27, 2026-08-10) -- role-agnostic: the caller picks
    which role's route list this becomes (`conjecturer` for Step 44's
    conjecture-side `--school-seat`, `argumentative_critic` for Step 44b's
    criticism-side `--criticism-seat`); both levers need the identical
    seat-allocation shape, only the destination role differs.

    Seat 0 is always the default broadcast profile. Each DISTINCT profile
    named in `school_seats` gets one additional seat (schools sharing the
    same profile share a seat -- deduplicated by endpoint_id, in first-
    seen order for determinism). Returns the route-spec list (for
    `Config.roles[<role>]`) and a `school_id -> (seat, endpoint_id)` map so
    the caller's policy builder can bind each school to the seat that
    actually carries its route -- `SchoolRoleBindingV1` resolves against
    `manifest.roles[<role>][seat]`, not a bare endpoint_id string, so both
    must agree with what this function built.
    """

    default_spec = profile.endpoint_spec()
    routes = [dict(default_spec)]
    seat_by_endpoint_id: dict[str, int] = {profile.endpoint_id: 0}
    seat_map: dict[str, tuple[int, str]] = {}
    for school_id, seat_profile in (school_seats or {}).items():
        endpoint_id = seat_profile.endpoint_id
        if endpoint_id not in seat_by_endpoint_id:
            seat_by_endpoint_id[endpoint_id] = len(routes)
            routes.append(dict(seat_profile.endpoint_spec()))
        seat_map[school_id] = (seat_by_endpoint_id[endpoint_id], endpoint_id)
    return routes, seat_map


def _config_for_profile(
    profile: ProviderProfileV1,
    *,
    base: Config | None = None,
    seat_bindings: Mapping[str, ProviderProfileV1] | None = None,
    school_seats: Mapping[str, ProviderProfileV1] | None = None,
    criticism_seats: Mapping[str, ProviderProfileV1] | None = None,
    channels_disabled: tuple[str, ...] = (),
) -> Config:
    endpoint = profile.endpoint_spec()
    # seat_bindings overrides specific roles onto a DIFFERENT profile's
    # endpoint (Rung S3, role-seat separation); every other role keeps the
    # one broadcast endpoint, exactly as before seat bindings existed.
    roles = {
        role: dict(
            seat_bindings[role].endpoint_spec()
            if seat_bindings and role in seat_bindings
            else endpoint
        )
        for role in V3_CANONICAL_ROLES
    }
    if school_seats:
        conjecturer_routes, _seat_map = _school_seat_route_ensemble(
            profile, school_seats
        )
        roles["conjecturer"] = conjecturer_routes
    if criticism_seats:
        critic_routes, _seat_map = _school_seat_route_ensemble(
            profile, criticism_seats
        )
        roles["argumentative_critic"] = critic_routes
    # The seven values the HOST owns on this path, whatever the operator's
    # configuration says: the provider profile holds the credential and the
    # endpoint, and the seat-binding mechanism owns per-role divergence, so a
    # configuration file may never redirect a managed run to another endpoint.
    owned = dict(
        engine_profile="full",
        model_profile=profile.model_profile,
        scratchpad=engaged_scratchpad_source(),
        # The grounded two-stage bridge rides the same single endpoint: the
        # frozen summarizer and thesis routes below satisfy its validator.
        bridge=engaged_bridge_source(),
        # The public preset keeps the semantic scratch channel on the
        # deterministic hashing embedder: no optional neural dependency may
        # decide public manifest identity.
        EMBEDDER_MODEL=None,
        # Evidence channels this preparation turns off, by declared id. Empty
        # is the default and means all three protected channels are live: the
        # setting names WHICH channels are off, never whether channels exist.
        CHANNELS_DISABLED=tuple(channels_disabled),
        roles=roles,
    )
    if base is None:
        return Config(**owned)
    data = base.model_dump(mode="python")
    data.update(owned)
    # model_validate, never model_copy: model_copy skips revalidation and
    # leaves the typed submodels (scratchpad, bridge) as bare dicts, which
    # moves the serialized bytes -- and therefore the qualification subject
    # digest -- for a configuration that asked for nothing.
    return Config.model_validate(data)


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


def _records_for_admitted_dossier(
    question: str,
    stored,
) -> tuple[Any, RunInputManifestV2, ReasoningWorkloadSpec]:
    """Bind one stored admission dossier into the question's run identity."""

    question_hash = _question_digest(question)
    problem_id = f"question-{question_hash[:32]}"
    if stored.problem_ref != problem_id:
        raise RunPreparationError(
            "ADMISSION_PROBLEM_MISMATCH",
            "the stored dossier was admitted for a different question; "
            "re-run deepreason admit with this exact question as --problem",
        )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id=problem_id,
            description=question,
            criteria=(),
        ),
        evidence_dossier_digest=stored.dossier_digest,
        brain_snapshot_digest=None,
    )
    workload = ReasoningWorkloadSpec(
        problem=WorkloadProblem(id=problem_id, description=question),
        criteria=(),
        sources=(),
    )
    return stored, run_input, workload


def build_preparation_manifest(
    profile: ProviderProfileV1,
    *,
    question: str,
    compiled_at: str,
    run_input_digest: str | None = None,
    attached_evidence: bool = False,
    config: Config | None = None,
    seat_bindings: Mapping[str, ProviderProfileV1] | None = None,
    school_seats: Mapping[str, ProviderProfileV1] | None = None,
    criticism_seats: Mapping[str, ProviderProfileV1] | None = None,
    channels_disabled: tuple[str, ...] = (),
):
    """Build the in-memory V6 manifest used by qualification and preparation.

    ``attached_evidence`` opts the manifest into the fixed finite
    attached-evidence envelope; question-only preparation (and the
    question-neutral qualification subject) keeps the historical disabled
    policy byte-identical. ``seat_bindings`` overrides specific roles onto
    a different profile (Rung S3); omitted, every role uses ``profile``,
    byte-identical to before seat bindings existed. ``school_seats`` maps
    ``school_id -> ProviderProfileV1`` for schools bound to a distinct
    CONJECTURE-side route (Part E, S2d/R5, Amendment 11/R27, 2026-08-10 --
    a school is a conjecture-side tool; this never touches criticism
    routing); requires ``Config.SCHOOL_SEATS_ENABLED``, checked here as
    defense-in-depth alongside the CLI's own gate. ``criticism_seats`` is
    the fully independent CRITICISM-side counterpart (S2d/R27, Step 44b,
    SPEC.md addendum S18): maps ``school_id -> ProviderProfileV1`` for one
    or more schools whose ``argumentative_critic`` binding should diverge
    from the shared default route; requires BOTH
    ``Config.SCHOOL_SEATS_ENABLED`` and ``Config.LEGACY_CRITICISM_ENABLED
    is False`` (criticism must already be school-routed before a
    per-school distinct route is meaningful) -- refuses typed, not
    silently, when either prerequisite is missing. ``config`` is the
    OPERATOR's loaded configuration; every field it sets is either carried
    into the compiled manifest or disclosed by the compiler as a typed
    ``ENGINE_CONFIG_FIELD_NOT_CARRIED`` notice, except the seven the host
    owns (``_config_for_profile``'s ``owned``). Omitted, the manifest is
    byte-identical to before configuration reached this path.
    """

    if run_input_digest is None:
        _dossier, run_input, _workload = _records_for_question(question)
        run_input_digest = run_input.run_input_digest
    config = _config_for_profile(
        profile,
        base=config,
        seat_bindings=seat_bindings,
        school_seats=school_seats,
        criticism_seats=criticism_seats,
        channels_disabled=channels_disabled,
    )
    if (school_seats or criticism_seats) and not config.SCHOOL_SEATS_ENABLED:
        raise RunManifestError(
            "SCHOOL_SEATS_DISABLED",
            "school_seats/criticism_seats requires Config.SCHOOL_SEATS_ENABLED",
            "/control_plane_policy/school_execution",
        )
    if criticism_seats and config.LEGACY_CRITICISM_ENABLED:
        raise RunManifestError(
            "CRITICISM_SEATS_REQUIRE_SCHOOL_ROUTED_CRITICISM",
            "criticism_seats requires Config.LEGACY_CRITICISM_ENABLED is False",
            "/criticism_policy",
        )
    control_plane_policy = engaged_control_plane_policy_v3()
    if school_seats:
        _routes, seat_map = _school_seat_route_ensemble(profile, school_seats)
        control_plane_policy = control_plane_policy.model_copy(
            update={
                "school_execution": route_bound_school_execution_policy(
                    profile.endpoint_id, seat_map=seat_map
                )
            }
        )
    criticism_seat_map = None
    if criticism_seats:
        _routes, criticism_seat_map = _school_seat_route_ensemble(
            profile, criticism_seats
        )
    return compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=compiled_at,
        control_plane_policy=control_plane_policy,
        criticism_policy=configured_criticism_policy(
            config,
            profile.endpoint_id,
            seat_map=criticism_seat_map,
        ),
        # The channel registry decides which evidence channels this manifest
        # compiles ON, from the SAME config every other setting here comes
        # from -- so turning one off is an ordinary setting on the one run
        # path, not a second door.
        inquiry_capability_policy=engaged_inquiry_capability_policy(
            attached_evidence=attached_evidence, config=config
        ),
        run_input_digest=run_input_digest,
        # The one frozen simulation toolchain is derived from the executing
        # interpreter at preparation time so the wheel stays portable across
        # end-user machines; the entry matches the engaged simulation policy
        # (local declarative by default, container when the operator opts
        # into the contained runner).
        toolchains=(engaged_simulation_toolchain(),),
    )


def qualification_subject_manifest(
    profile: ProviderProfileV1,
    *,
    attached_evidence: bool = False,
    config: Config | None = None,
    seat_bindings: Mapping[str, ProviderProfileV1] | None = None,
):
    """Return a stable per-profile manifest whose reusable subject is question-neutral.

    ``attached_evidence`` warms the subject that ``reason --attach`` runs
    bind (the fixed attached-evidence envelope); the default subject stays
    byte-identical to the historical question-only preset. ``seat_bindings``
    is threaded straight through (Rung S3); omitted, unchanged. ``config``
    is the operator's configuration, threaded through the SAME door
    ``prepare`` uses: the battery this warms must be the battery a run of
    that configuration needs, or a configuration that compiles is a
    configuration no operation can qualify.
    """

    return build_preparation_manifest(
        profile,
        question=_QUALIFICATION_QUESTION,
        compiled_at=_QUALIFICATION_COMPILED_AT,
        attached_evidence=attached_evidence,
        config=config,
        seat_bindings=seat_bindings,
    )


def resolve_managed_run_root(
    managed_run_id: str,
    *,
    runs_dir: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | str | None = None,
) -> Path:
    """Resolve an opaque managed ID from its durable record, never from a path."""

    if _RUN_ID.fullmatch(managed_run_id) is None:
        raise RunPreparationError(
            "MANAGED_RUN_ID_INVALID", "managed run id has an invalid form"
        )
    state = provider_state_dir(home=home, environ=environ)
    base = Path(runs_dir) if runs_dir is not None else state / "runs"
    root = base / managed_run_id
    if not root.is_dir() or root.is_symlink():
        raise RunPreparationError(
            "MANAGED_RUN_NOT_FOUND", "managed run id does not identify a run"
        )
    record = load_preparation_record(root)
    if record.managed_run_id != managed_run_id or root.name != managed_run_id:
        raise RunPreparationError(
            "MANAGED_RUN_IDENTITY_MISMATCH", "managed run identity is inconsistent"
        )
    return root


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

        operator_config = _load_operator_config(request.config_path)
        request_digest = _request_digest(request, profile, config=operator_config)
        managed_id = request.managed_run_id or f"run-{request_digest[:32]}"
        source_contents: dict[str, bytes] = {}
        if request.dossier_digest is not None:
            from deepreason.admission.store import AdmissionStore, AdmissionStoreError

            store = AdmissionStore()
            try:
                stored = store.load(request.dossier_digest)
                source_contents = store.source_bytes(stored)
            except AdmissionStoreError as error:
                raise RunPreparationError(error.code, str(error)) from error
            dossier, run_input, workload = _records_for_admitted_dossier(
                request.question, stored
            )
        else:
            dossier, run_input, workload = _records_for_question(request.question)
        seat_bindings = resolve_seat_bindings(environ=self._environ, home=self._home)
        seat_bindings_by_group = resolve_seat_bindings_by_group(
            environ=self._environ, home=self._home
        )
        school_seats = resolve_school_seats(environ=self._environ, home=self._home)
        criticism_seats = resolve_criticism_seats(environ=self._environ, home=self._home)
        seat_bindings_payload = (
            SeatBindingsEventPayloadV1.of(
                [
                    SeatBindingV1.of(group, seat_bindings_by_group[group])
                    for group in sorted(seat_bindings_by_group)
                ]
            )
            if seat_bindings_by_group
            else None
        )
        manifest = build_preparation_manifest(
            profile,
            question=request.question,
            compiled_at=_compiled_at(self._clock),
            run_input_digest=run_input.run_input_digest,
            attached_evidence=request.dossier_digest is not None,
            config=operator_config,
            seat_bindings=seat_bindings or None,
            school_seats=school_seats or None,
            criticism_seats=criticism_seats or None,
        )
        try:
            bundle = resolve_completed_qualification(
                manifest,
                profile,
                cache_dir=self._cache_dir,
                executor=self._executor,
            )
        except ValueError as error:
            if (
                request.dossier_digest is not None
                and getattr(error, "code", "") == "QUALIFICATION_NOT_CONFIGURED"
            ):
                raise RunPreparationError(
                    "QUALIFICATION_NOT_CONFIGURED",
                    "attached-evidence runs bind their own frozen evidence "
                    "envelope, which is a distinct qualification subject; "
                    "run `deepreason qualify --attached-evidence` first",
                ) from error
            raise
        report = project_qualification_report(bundle, manifest, profile)
        subject_digest = qualification_subject_digest(manifest, profile)
        root = self._runs_dir / managed_id
        if root.exists():
            return self._load_existing(
                root=root,
                request=request,
                request_digest=request_digest,
                resolved=resolved,
                expected_bundle_digest=bundle.bundle_digest,
            )
        record = RunPreparationRecordV1.create(
            managed_run_id=managed_id,
            request_digest=request_digest,
            question_digest=_question_digest(request.question),
            problem_id=run_input.problem.id,
            budget=request.budget,
            provider_profile_digest=profile.profile_digest,
            policy_preset_digest=engaged_policy_digest(),
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
                    expected_bundle_digest=bundle.bundle_digest,
                )
            temporary = self._runs_dir / (
                f".{managed_id}.preparing.{uuid.uuid4().hex}"
            )
            try:
                if source_contents:
                    from deepreason.storage.blobs import BlobStore

                    staged = BlobStore(temporary / "blobs")
                    for body in source_contents.values():
                        staged.put(body)
                bind_run_input(run_input, dossier, temporary)
                bind_run_manifest(manifest, temporary)
                policy = manifest.production_qualification_policy
                assert policy is not None
                write_production_contract_report(
                    report, temporary / policy.report_filename
                )
                _write_preparation_record(record, temporary)
                if seat_bindings_payload is not None:
                    (temporary / SEAT_BINDINGS_SNAPSHOT_NAME).write_bytes(
                        seat_bindings_payload.model_dump_json(by_alias=True).encode(
                            "utf-8"
                        )
                        + b"\n"
                    )
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
        expected_bundle_digest: str,
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
        if record.qualification_bundle_digest != expected_bundle_digest:
            raise RunPreparationError(
                "PREPARATION_QUALIFICATION_BUNDLE_MISMATCH",
                "managed run qualification differs from the completed cache",
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
    "PUBLIC_DEFAULT_CYCLES",
    "PUBLIC_DEFAULT_TOKEN_BUDGET",
    "PUBLIC_MAX_CYCLES",
    "SEAT_BINDINGS_SNAPSHOT_NAME",
    "PreparedRunV1",
    "RunPreparationError",
    "RunPreparationRecordV1",
    "RunPreparationRequestV1",
    "RunPreparationService",
    "build_preparation_manifest",
    "load_preparation_record",
    "qualification_subject_manifest",
    "resolve_managed_run_root",
]
