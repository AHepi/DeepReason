"""Compile source configuration into a frozen, replayable run manifest.

YAML and command-line options are setup inputs.  Runtime model calls consume
only the concrete routes in :class:`RunManifest`: ``auto`` sentinels are
resolved once, before the first call, and credentials never enter the file.
The manifest is deliberately process metadata; it has no place in the
artifact ontology or adjudication graph.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.llm.endpoints import DEFAULT_TIMEOUT_S, resolve_model
from deepreason.llm.providers import infer_provider


SCHEMA_VERSION = 1
LATEST_SCHEMA_VERSION = 2
MANIFEST_NAME = "run-manifest.json"
MANIFEST_HASH_NAME = "run-manifest.sha256"
_UNRESOLVED_MODELS = {"auto", "auto-alt"}

# Configured endpoint roles. Auxiliary prompt templates such as
# ``batch_critic`` and ``experimenter`` reuse one of these seats and are not
# independently routable roles.
CANONICAL_ROLES = (
    "conjecturer",
    "argumentative_critic",
    "defender",
    "variator",
    "judge",
    "summarizer",
    "synthesizer",
    "vision_critic",
    "property_designer",
    "thesis",
)


class RunManifestError(ValueError):
    """Stable preflight/manifest error suitable for CLI and MCP callers."""

    def __init__(self, code: str, message: str, pointer: str = "") -> None:
        self.code = code
        self.pointer = pointer
        location = f" at {pointer}" if pointer else ""
        super().__init__(f"{code}{location}: {message}")


class RouteSecretError(RuntimeError):
    """A route URL contains credential material that must not be persisted.

    This deliberately does not inherit from ``ValueError``: Pydantic includes
    rejected input values in ordinary validation errors, which would echo the
    very credential this boundary is meant to keep out of logs and manifests.
    """

    code = "ROUTE_URL_CREDENTIAL_FORBIDDEN"
    pointer = "/base_url"

    def __init__(self) -> None:
        super().__init__(
            f"{self.code} at {self.pointer}: route URL must not contain credentials"
        )


def validate_route_base_url(value: str) -> str:
    """Reject credential-bearing URLs without placing their values in errors."""
    try:
        parsed = urlsplit(value)
    except ValueError:
        # General URL syntax belongs to the endpoint implementation.  This
        # check has one narrow job: prevent secrets entering canonical data.
        return value
    if parsed.username is not None or parsed.password is not None:
        raise RouteSecretError()
    # API base URLs are origin/path identifiers. Queries and fragments are not
    # routing identity and are common credential carriers, so accepting any
    # would leave a value-pattern loophole in the no-secrets invariant.
    if parsed.query or parsed.fragment:
        raise RouteSecretError()
    return value


class _FrozenDict(dict):
    """A JSON-serializable dict whose contents cannot change after compile."""

    @staticmethod
    def _blocked(*_args, **_kwargs):
        raise TypeError("RunManifest roles are immutable")

    __setitem__ = _blocked
    __delitem__ = _blocked
    clear = _blocked
    pop = _blocked
    popitem = _blocked
    setdefault = _blocked
    update = _blocked


class Route(BaseModel):
    """One exact provider route, with no credential value."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True
    )

    endpoint_id: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_revision: str | None = None
    provider: str = Field(min_length=1)
    family: str = Field(min_length=1)
    reasoning: str | int | None = None
    output_mode: Literal["json_object", "text"] = "text"
    output_mechanism: Literal["native_json_schema", "grammar", "json_text"] = "json_text"
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, gt=0)
    timeout_s: int = Field(default=DEFAULT_TIMEOUT_S, gt=0)
    logprobs: bool = False
    # The name of an environment variable is routing metadata, not a secret.
    # The variable's value is looked up only while constructing the endpoint.
    api_key_env: str | None = None

    @field_validator("base_url")
    @classmethod
    def _secret_free_url(cls, value: str) -> str:
        return validate_route_base_url(value)

    @field_validator("api_key_env")
    @classmethod
    def _credential_reference_is_an_env_name(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError("api_key_env must be a POSIX environment-variable name")
        return value

    @field_validator("model_id")
    @classmethod
    def _concrete_model(cls, value: str) -> str:
        if value in _UNRESOLVED_MODELS:
            raise ValueError("production routes cannot contain auto or auto-alt")
        return value

    def endpoint_spec(self) -> dict[str, Any]:
        """Return the legacy Config role-table shape for this frozen route."""
        return {
            "endpoint_id": self.endpoint_id,
            "endpoint": self.base_url,
            "model": self.model_id,
            "model_revision": self.model_revision,
            "provider": self.provider,
            "family": self.family,
            "reasoning": self.reasoning,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout_s": self.timeout_s,
            "json_mode": self.output_mode == "json_object",
            "output_mechanism": self.output_mechanism,
            "logprobs": self.logprobs,
            "api_key_env": self.api_key_env,
        }


class ToolchainEntry(BaseModel):
    """Resolved, secret-free verifier/program toolchain coordinates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    runner: Literal["local", "container"]
    executable: str = Field(min_length=1)
    version_output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    lock_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    network: Literal[False] = False
    environment: dict[str, str] = Field(default_factory=dict)
    allowed_programs: tuple[str, ...] = ()

    @field_validator("executable")
    @classmethod
    def _resolved_executable(cls, value: str) -> str:
        if value.strip().casefold() in {
            "auto",
            "unresolved",
            "<resolved path or image digest>",
        }:
            raise ValueError("toolchain executable must be resolved before use")
        return value

    @field_validator("environment", mode="after")
    @classmethod
    def _secret_free_environment(cls, value: dict[str, str]):
        secret_markers = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")
        if any(marker in key.upper() for key in value for marker in secret_markers):
            raise ValueError("toolchain environment cannot contain credential fields")
        return _FrozenDict(dict(value))


class RunManifest(BaseModel):
    """Canonical, immutable routing and presentation plan for one run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1, 2] = SCHEMA_VERSION
    engine_profile: Literal["mini", "full"] = "full"
    model_profile: Literal["compact", "standard", "frontier"] = "standard"
    workload_profile: Literal["text", "code", "formal", "website"] | None = None
    roles: dict[str, tuple[Route, ...]]
    rubric_policy: Literal["forbid", "require_cross_family"] = "require_cross_family"
    provider_fallback: Literal[False] = False
    concurrency: int = Field(default=1, ge=1)
    pack_profile: str = Field(min_length=1)
    output_profile: str = Field(min_length=1)
    toolchains: tuple[ToolchainEntry, ...] = ()
    budget_policy: dict[str, Any] = Field(default_factory=dict)
    stop_policy: dict[str, Any] = Field(default_factory=dict)
    memory_policy: dict[str, Any] = Field(default_factory=dict)
    source_config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    compiled_at: str = Field(min_length=1)
    # Canonical full engine configuration without a role table.  Runtime
    # reconstruction injects routes solely from ``roles``, so a decoy provider
    # in the source file is observationally irrelevant after compilation.
    engine_config_json: str = Field(min_length=2, repr=False)

    @field_validator("roles", mode="after")
    @classmethod
    def _freeze_roles(cls, value: dict[str, tuple[Route, ...]]):
        return _FrozenDict({role: tuple(routes) for role, routes in value.items()})

    @field_validator("budget_policy", "stop_policy", "memory_policy", mode="after")
    @classmethod
    def _freeze_policies(cls, value: dict[str, Any]):
        return _FrozenDict(json.loads(json.dumps(value)))

    @field_validator("compiled_at")
    @classmethod
    def _valid_timestamp(cls, value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("compiled_at must be an ISO-8601 timestamp") from error
        if parsed.tzinfo is None:
            raise ValueError("compiled_at must include a timezone")
        return value

    @model_validator(mode="after")
    def _production_routes_are_concrete(self):
        if self.schema_version == 1:
            if self.workload_profile is not None or self.toolchains:
                raise ValueError("v1 manifest cannot carry v2 workload/toolchain fields")
            if self.budget_policy or self.stop_policy or self.memory_policy:
                raise ValueError("v1 manifest cannot carry v2 process policies")
        elif self.workload_profile is None:
            raise ValueError("v2 manifest requires workload_profile")
        for role, routes in self.roles.items():
            for index, route in enumerate(routes):
                if route.model_id in _UNRESOLVED_MODELS:
                    raise ValueError(
                        f"roles.{role}.{index}.model_id is unresolved: {route.model_id}"
                    )
        if self.rubric_policy == "require_cross_family":
            families = {
                route.family.strip().casefold()
                for route in self.roles.get("judge", ())
                if route.family.strip()
            }
            if len(families) < 2:
                raise ValueError(
                    "SECOND_JUDGE_FAMILY_REQUIRED: require_cross_family needs "
                    "at least two distinct judge families"
                )
        return self

    def canonical_bytes(self) -> bytes:
        payload = self.model_dump(mode="json")
        if self.schema_version == 1:
            # Preserve the exact canonical v1 byte and hash contract.  The v2
            # fields did not exist and must not appear as serialized defaults.
            for field in (
                "workload_profile",
                "toolchains",
                "budget_policy",
                "stop_policy",
                "memory_policy",
            ):
                payload.pop(field, None)
        return _canonical_json(payload)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _source_config_data(config) -> dict[str, Any]:
    if hasattr(config, "model_dump"):
        return config.model_dump(mode="json")
    if not isinstance(config, dict):
        raise TypeError("config must be a deepreason.config.Config or mapping")
    return json.loads(json.dumps(config))


def source_config_hash(config) -> str:
    """Hash the complete effective source configuration, including roles."""
    return hashlib.sha256(_canonical_json(_source_config_data(config))).hexdigest()


def infer_model_family(model_id: str, provider: str) -> str:
    """Deterministic setup-time family inference, overridable in Config.

    Family is normative for judge ensembles, so unknown identifiers are kept
    distinct by their stable provider/model stem rather than guessed into a
    known family.
    """
    lowered = model_id.lower()
    known = (
        ("deepseek", "deepseek"),
        ("gemma", "gemma"),
        ("claude", "claude"),
        ("qwen", "qwen"),
        ("llama", "llama"),
        ("mistral", "mistral"),
        ("mixtral", "mistral"),
        ("gpt", "openai-gpt"),
        ("o1", "openai-o"),
        ("o3", "openai-o"),
        ("o4", "openai-o"),
    )
    for marker, family in known:
        if marker in lowered:
            return family
    stem = lowered.rsplit("/", 1)[-1].split(":", 1)[0].split("-", 1)[0]
    return f"{provider}:{stem or 'unknown'}"


def _endpoint_identifier(spec: dict[str, Any], provider: str) -> str:
    explicit = str(spec.get("endpoint_id") or "").strip()
    if explicit:
        return explicit
    base_url = str(spec.get("endpoint") or "").rstrip("/")
    digest = hashlib.sha256(base_url.encode()).hexdigest()[:16]
    return f"{provider}:{digest}"


def _route_from_spec(
    spec: dict[str, Any], *, forced_model: str | None = None, capability_cache=None
) -> Route:
    base_url = str(spec.get("endpoint") or "").strip()
    if not base_url:
        raise RunManifestError("ENDPOINT_REQUIRED", "route has no endpoint")
    try:
        validate_route_base_url(base_url)
    except RouteSecretError as error:
        raise RunManifestError(error.code, "route URL must not contain credentials", "/base_url") from error
    provider = str(spec.get("provider") or infer_provider(base_url))
    model = forced_model if forced_model is not None else str(spec.get("model") or "")
    if not model:
        raise RunManifestError("MODEL_REQUIRED", "route has no model")
    api_key_env = str(spec.get("api_key_env") or "") or None
    api_key = os.environ.get(api_key_env) if api_key_env else None
    resolved = resolve_model(model, base_url, api_key)
    if resolved in _UNRESOLVED_MODELS or not resolved:
        raise RunManifestError(
            "UNRESOLVED_MODEL", f"could not resolve concrete model from {model!r}"
        )
    family = str(spec.get("family") or infer_model_family(resolved, provider))
    output_mode = spec.get("output_mode")
    if output_mode is None:
        output_mode = "json_object" if spec.get("json_mode") else "text"
    mechanism = spec.get("output_mechanism")
    if mechanism is None and capability_cache is not None:
        capabilities = capability_cache.get(
            provider, base_url, resolved, str(spec.get("model_revision") or "")
        )
        if capabilities is not None:
            from deepreason.llm.repair import select_output_mechanism

            mechanism = select_output_mechanism(capabilities).value
    return Route(
        endpoint_id=_endpoint_identifier(spec, provider),
        base_url=base_url,
        model_id=resolved,
        model_revision=str(spec.get("model_revision") or "") or None,
        provider=provider,
        family=family,
        reasoning=spec.get("reasoning"),
        output_mode=output_mode,
        # A capability probe or explicit source profile may select a stronger
        # transport. In its absence strict JSON text is the only honest fixed
        # choice; runtime calls must not probe or fall back.
        output_mechanism=mechanism or "json_text",
        temperature=spec.get("temperature"),
        max_tokens=spec.get("max_tokens"),
        timeout_s=spec.get("timeout_s") or DEFAULT_TIMEOUT_S,
        logprobs=bool(spec.get("logprobs", False)),
        api_key_env=api_key_env,
    )


def _configured_seats(config_data: dict[str, Any]):
    for role, configured in (config_data.get("roles") or {}).items():
        if configured is None:
            continue
        seats = configured if isinstance(configured, list) else [configured]
        for index, spec in enumerate(seats):
            if isinstance(spec, dict) and spec.get("endpoint"):
                yield role, index, spec


def _select_single_model_seed(
    config_data: dict[str, Any], model_id: str
) -> dict[str, Any]:
    seats = list(_configured_seats(config_data))
    exact = [
        entry for entry in seats
        if entry[0] in CANONICAL_ROLES and entry[2].get("model") == model_id
    ]
    if exact:
        # Distinct creative caps/temperatures on roles do not name different
        # provider routes; single-model mode deliberately copies the chosen
        # seed's complete settings to every role. Multiple origins, endpoint
        # identities, credential references, revisions, providers, or
        # families are genuinely ambiguous and must fail closed.
        identities = set()
        for _role, _index, spec in exact:
            route = _route_from_spec(spec, forced_model=model_id)
            identities.add((
                route.endpoint_id,
                route.base_url,
                route.model_id,
                route.model_revision,
                route.provider,
                route.family,
                route.api_key_env,
            ))
        if len(identities) > 1:
            raise RunManifestError(
                "SINGLE_MODEL_ROUTE_AMBIGUOUS",
                "the requested model is bound to multiple distinct configured "
                "routes; make the route unique before compiling",
                "/roles",
            )
        exact.sort(key=lambda item: (item[0] != "conjecturer", item[0], item[1]))
        return exact[0][2]
    raise RunManifestError(
        "SINGLE_MODEL_ROUTE_REQUIRED",
        f"no configured endpoint is explicitly bound to model {model_id!r}; "
        "add one concrete route before compiling",
        "/roles",
    )


def _select_second_judge_spec(
    config_data: dict[str, Any], selector: str, primary_family: str,
    capability_cache=None,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for _role, _index, spec in _configured_seats(config_data):
        provider = str(spec.get("provider") or infer_provider(str(spec.get("endpoint") or "")))
        model = str(spec.get("model") or "")
        family = str(spec.get("family") or (
            infer_model_family(model, provider) if model not in _UNRESOLVED_MODELS else ""
        ))
        endpoint_id = _endpoint_identifier(spec, provider)
        if selector in {family, endpoint_id, model, str(spec.get("endpoint") or "")}:
            matches.append(spec)
    if not matches:
        raise RunManifestError(
            "SECOND_JUDGE_ROUTE_NOT_FOUND",
            f"no configured route matches judge-family selector {selector!r}",
            "/roles/judge",
        )
    route = _route_from_spec(matches[0], capability_cache=capability_cache)
    if route.family == primary_family:
        raise RunManifestError(
            "SECOND_JUDGE_FAMILY_REQUIRED",
            f"second judge route is still family {primary_family!r}",
            "/roles/judge",
        )
    return matches[0]


def compile_run_manifest(
    config,
    *,
    engine_profile: Literal["mini", "full"] | None = None,
    model_profile: Literal["compact", "standard", "frontier"] | None = None,
    single_model: str | None = None,
    judge_family: str | None = None,
    rubric_policy: Literal["forbid", "require_cross_family"] = "require_cross_family",
    concurrency: int | None = None,
    compiled_at: str | None = None,
    capability_cache=None,
    schema_version: Literal[1, 2] = SCHEMA_VERSION,
    workload_profile: Literal["text", "code", "formal", "website"] | None = None,
    pack_profile: str | None = None,
    output_profile: str | None = None,
    toolchains: tuple[ToolchainEntry, ...] = (),
    budget_policy: dict[str, Any] | None = None,
    stop_policy: dict[str, Any] | None = None,
    memory_policy: dict[str, Any] | None = None,
) -> RunManifest:
    """Resolve and freeze the role matrix before any role-model call.

    In single-model mode only the route explicitly carrying ``single_model``
    is consulted. Other provider entries are not discovered or used.
    """
    explicit_config_profile = (
        "model_profile" in getattr(config, "model_fields_set", set())
        if not isinstance(config, dict)
        else "model_profile" in config
    )
    data = _source_config_data(config)
    if schema_version == 2 and workload_profile is None:
        raise RunManifestError(
            "WORKLOAD_PROFILE_REQUIRED",
            "schema v2 requires a text, code, formal, or website workload profile",
            "/workload_profile",
        )
    # This must precede route resolution: a rejected authority policy cannot
    # spend an endpoint/model-discovery call merely to learn that it is unsafe.
    _preflight_text_authority(config, schema_version, workload_profile)
    engine_profile = engine_profile or data.get("engine_profile") or "full"
    if model_profile is None:
        model_profile = data.get("model_profile") or "standard"
        # A doctor result recommends presentation only. It may select the
        # default profile, never a route or an epistemic policy, and an
        # explicit config/CLI profile always wins.
        if capability_cache is not None and not explicit_config_profile:
            try:
                seed = (
                    _select_single_model_seed(data, single_model)
                    if single_model
                    else next(
                        spec for role, _index, spec in _configured_seats(data)
                        if role in CANONICAL_ROLES
                    )
                )
            except (RunManifestError, StopIteration):
                seed = None
            if seed is not None:
                base_url = str(seed.get("endpoint") or "")
                provider = str(seed.get("provider") or infer_provider(base_url))
                model_id = single_model or str(seed.get("model") or "")
                if model_id not in _UNRESOLVED_MODELS:
                    capabilities = capability_cache.get(
                        provider, base_url, model_id,
                        str(seed.get("model_revision") or ""),
                    )
                    if capabilities is not None:
                        from deepreason.llm.profiles import select_profile

                        model_profile = select_profile(capabilities).name.value
    configured_roles = {
        role for role, _index, _spec in _configured_seats(data)
        if role in CANONICAL_ROLES
    }
    role_names = CANONICAL_ROLES
    roles: dict[str, tuple[Route, ...]] = {role: () for role in role_names}

    if single_model:
        if single_model in _UNRESOLVED_MODELS:
            raise RunManifestError(
                "SINGLE_MODEL_MUST_BE_CONCRETE", "--single-model cannot be auto or auto-alt"
            )
        seed = _select_single_model_seed(data, single_model)
        exact = _route_from_spec(
            seed, forced_model=single_model, capability_cache=capability_cache
        )
        for role in configured_roles:
            # One exact route is copied to every active role. Ensembles are
            # not inferred from another provider or model.
            roles[role] = (exact,)
        if "judge" in configured_roles and judge_family:
            second_spec = _select_second_judge_spec(
                data, judge_family, exact.family, capability_cache=capability_cache
            )
            roles["judge"] = (
                exact, _route_from_spec(second_spec, capability_cache=capability_cache)
            )
    else:
        grouped: dict[str, list[Route]] = {role: [] for role in role_names}
        for role, _index, spec in _configured_seats(data):
            if role not in CANONICAL_ROLES:
                continue
            grouped.setdefault(role, []).append(
                _route_from_spec(spec, capability_cache=capability_cache)
            )
        roles = {role: tuple(grouped.get(role, ())) for role in role_names}

    if rubric_policy == "require_cross_family":
        families = {
            route.family.strip().casefold()
            for route in roles.get("judge", ())
            if route.family.strip()
        }
        if len(families) < 2:
            raise RunManifestError(
                "SECOND_JUDGE_FAMILY_REQUIRED",
                "rubric workloads require at least two frozen judge families; "
                "supply --judge-family or use --rubric-policy forbid only for "
                "program/predicate workloads",
                "/roles/judge",
            )

    if concurrency is None:
        from deepreason.llm.profiles import get_profile

        concurrency = get_profile(model_profile).default_concurrency
    if concurrency < 1:
        raise RunManifestError("INVALID_CONCURRENCY", "concurrency must be at least 1")

    engine_config = dict(data)
    engine_config["roles"] = {}
    stamp = compiled_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    default_pack_profiles = {
        "text": "reasoning.text.v1",
        "code": "reasoning.code.v1",
        "formal": "reasoning.formal.v1",
        "website": "website.v1",
    }
    return RunManifest(
        schema_version=schema_version,
        engine_profile=engine_profile,
        model_profile=model_profile,
        workload_profile=workload_profile,
        roles=roles,
        rubric_policy=rubric_policy,
        concurrency=concurrency,
        pack_profile=(
            pack_profile
            or (default_pack_profiles[workload_profile] if workload_profile else model_profile)
        ),
        output_profile=(
            output_profile
            or ("compact.v2" if schema_version == 2 and model_profile == "compact" else model_profile)
        ),
        toolchains=toolchains,
        budget_policy=budget_policy or {},
        stop_policy=stop_policy or {},
        memory_policy=memory_policy or {},
        source_config_hash=source_config_hash(data),
        compiled_at=stamp,
        engine_config_json=_canonical_json(engine_config).decode("utf-8"),
    )


def write_run_manifest(manifest: RunManifest, path: Path | str) -> tuple[Path, Path]:
    """Atomically write canonical bytes and a sibling SHA-256 file.

    This is the explicit export operation used by ``config compile``.  A run
    root must use :func:`bind_run_manifest`, whose first-writer semantics are
    deliberately stricter.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(target, manifest.canonical_bytes())
    digest_path = target.with_suffix(target.suffix + ".sha256")
    _atomic_write(digest_path, (manifest.sha256 + "\n").encode("utf-8"))
    return target, digest_path


def _atomic_write(target: Path, payload: bytes) -> None:
    """Replace ``target`` with one complete, fsynced payload."""
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        # Persist the directory entry as well as the file contents so a
        # reported successful bind survives a host crash.
        directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


@contextmanager
def _run_manifest_lock(root: Path):
    """Serialize bind/check across processes sharing a run root."""
    import fcntl

    lock_path = root / ".run-manifest.lock"
    with lock_path.open("a+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def bind_run_manifest(manifest: RunManifest, root: Path | str) -> tuple[Path, Path]:
    """Bind exactly one immutable manifest to a run root.

    The first caller writes canonical bytes atomically.  Later callers are
    idempotent only when their canonical manifest is byte-for-byte identical;
    a resume can therefore never replace routing, profile, policy, or even
    compile-time identity.  The filesystem lock makes that guarantee hold for
    concurrent processes as well as threads.
    """
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    target = root_path / MANIFEST_NAME
    fixed_hash = root_path / MANIFEST_HASH_NAME
    payload = manifest.canonical_bytes()
    digest_payload = (manifest.sha256 + "\n").encode("utf-8")

    with _run_manifest_lock(root_path):
        if target.exists():
            existing = target.read_bytes()
            if existing != payload:
                existing_hash = hashlib.sha256(existing).hexdigest()
                raise RunManifestError(
                    "RUN_MANIFEST_CONFLICT",
                    "run root is already bound to a different manifest "
                    f"({existing_hash} != {manifest.sha256})",
                    f"/{MANIFEST_NAME}",
                )
            # Validate every sidecar that load_run_manifest could select. A
            # missing fixed-name sidecar is safe to recover because the
            # canonical target bytes already match the requested manifest.
            sidecars = (
                target.with_suffix(target.suffix + ".sha256"),
                fixed_hash,
            )
            for sidecar in sidecars:
                if not sidecar.exists():
                    continue
                words = sidecar.read_text(encoding="utf-8").strip().split()
                expected = words[0] if words else ""
                if expected != manifest.sha256:
                    raise RunManifestError(
                        "MANIFEST_HASH_MISMATCH",
                        f"expected {expected or '<empty>'}, computed {manifest.sha256}",
                    )
            if not fixed_hash.exists():
                _atomic_write(fixed_hash, digest_payload)
            return target, fixed_hash

        # A surviving sidecar is also a binding record (for example after an
        # interrupted/manual target removal). Never let a later caller claim
        # that root for different canonical bytes.
        for sidecar in (
            target.with_suffix(target.suffix + ".sha256"),
            fixed_hash,
        ):
            if not sidecar.exists():
                continue
            words = sidecar.read_text(encoding="utf-8").strip().split()
            expected = words[0] if words else ""
            if expected != manifest.sha256:
                raise RunManifestError(
                    "RUN_MANIFEST_CONFLICT",
                    "run root already records a different manifest digest "
                    f"({expected or '<empty>'} != {manifest.sha256})",
                    f"/{sidecar.name}",
                )
        _atomic_write(target, payload)
        if not fixed_hash.exists():
            _atomic_write(fixed_hash, digest_payload)
    return target, fixed_hash


def persist_run_manifest(manifest: RunManifest, root: Path | str) -> tuple[Path, Path]:
    """Backward-compatible name for conflict-safe run-root binding."""
    return bind_run_manifest(manifest, root)


def load_run_manifest(path: Path | str, *, verify_hash: bool = True) -> RunManifest:
    target = Path(path)
    raw = target.read_bytes()
    try:
        manifest = RunManifest.model_validate_json(raw)
    except ValueError as error:
        raise RunManifestError("INVALID_RUN_MANIFEST", str(error)) from error
    if verify_hash:
        candidates = [
            target.with_suffix(target.suffix + ".sha256"),
            target.parent / MANIFEST_HASH_NAME,
        ]
        # Every recognized sidecar is an integrity record. Accepting the
        # first match would let a stale/conflicting second record hide behind
        # candidate ordering and make verification depend on filename choice.
        for sidecar in candidates:
            if not sidecar.exists():
                continue
            words = sidecar.read_text(encoding="utf-8").strip().split()
            expected = words[0] if words else ""
            if expected != manifest.sha256:
                raise RunManifestError(
                    "MANIFEST_HASH_MISMATCH",
                    f"expected {expected or '<empty>'}, computed {manifest.sha256}",
                    f"/{sidecar.name}",
                )
    return manifest


def config_from_run_manifest(manifest: RunManifest):
    """Reconstruct Config with routes sourced only from the manifest."""
    from deepreason.config import Config
    from deepreason.llm.profiles import apply_profile_to_config

    try:
        data = json.loads(manifest.engine_config_json)
    except json.JSONDecodeError as error:
        raise RunManifestError("INVALID_ENGINE_CONFIG", str(error)) from error
    data["roles"] = {
        role: (
            [route.endpoint_spec() for route in routes]
            if len(routes) > 1
            else routes[0].endpoint_spec()
        )
        for role, routes in manifest.roles.items()
        if routes
    }
    data["engine_profile"] = manifest.engine_profile
    data["model_profile"] = manifest.model_profile
    return apply_profile_to_config(Config.model_validate(data), manifest.model_profile)


def materialize_run_config(manifest: RunManifest, root: Path | str) -> Path:
    """Write a harness-readable Config generated solely from frozen routes."""
    path = Path(root) / ".run-manifest-config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    config = config_from_run_manifest(manifest)
    _atomic_write(path, _canonical_json(config.model_dump(mode="json")))
    return path


def role_matrix(manifest: RunManifest) -> list[dict[str, Any]]:
    """Exact resolved role matrix for dry-run and inspection surfaces."""
    return [
        {
            "role": role,
            "seat": index,
            "endpoint_id": route.endpoint_id,
            "base_url": route.base_url,
            "model_id": route.model_id,
            "provider": route.provider,
            "family": route.family,
            "reasoning": route.reasoning,
            "output_mode": route.output_mode,
            "output_mechanism": route.output_mechanism,
            "temperature": route.temperature,
        }
        for role, routes in manifest.roles.items()
        for index, route in enumerate(routes)
    ]


def render_role_matrix(manifest: RunManifest) -> str:
    rows = role_matrix(manifest)
    if not rows:
        return "(no active model routes)"
    return "\n".join(
        f"{row['role']}[{row['seat']}]  endpoint={row['endpoint_id']}  "
        f"model={row['model_id']}  provider={row['provider']}  "
        f"family={row['family']}  output={row['output_mode']}  "
        f"mechanism={row['output_mechanism']}  "
        f"reasoning={row['reasoning']}  temperature={row['temperature']}"
        for row in rows
    )


def payload_has_rubric(payload: dict[str, Any]) -> bool:
    if payload.get("standard"):
        return True
    return any(
        str(commitment.get("eval") or "").startswith("rubric:")
        for commitment in (payload.get("commitments") or [])
        if isinstance(commitment, dict)
    )


def _preflight_text_authority(
    config,
    schema_version: int,
    workload_profile: str | None,
) -> None:
    """Fail closed before any endpoint exists for text status authority."""

    if schema_version != 2 or workload_profile != "text":
        return
    from deepreason.authority import text_status_authority_issues

    issues = text_status_authority_issues(config, workload_profile)
    if issues:
        issue = issues[0]
        raise RunManifestError(issue.code, issue.message, issue.pointer)


def preflight_payload(manifest: RunManifest, payload: dict[str, Any]) -> None:
    """Reject workload/manifest policy conflicts before the first call."""
    if payload_has_rubric(payload) and manifest.rubric_policy == "forbid":
        raise RunManifestError(
            "RUBRIC_INPUT_FORBIDDEN",
            "this run manifest permits program and predicate evaluation only",
            "/standard",
        )
    if payload_has_rubric(payload):
        families = {route.family for route in manifest.roles.get("judge", ())}
        if len(families) < 2:
            raise RunManifestError(
                "SECOND_JUDGE_FAMILY_REQUIRED",
                "rubric input requires two distinct frozen judge families",
                "/roles/judge",
            )


def preflight_harness(manifest: RunManifest, harness, config) -> None:
    """Reject materialized workload/policy conflicts before an endpoint call.

    Payload preflight cannot see criteria that reference commitments already
    present in a resumed root, nor scheduler features that can introduce a
    rubric trial later.  This check operates on the replayed canonical state
    and the frozen engine config, while remaining purely read-only.
    """
    _preflight_text_authority(
        config,
        manifest.schema_version,
        manifest.workload_profile,
    )
    if manifest.schema_version == 2 and manifest.workload_profile == "text":
        # The policy that authorizes a status-changing text judgement is part
        # of the frozen manifest, not a knob a caller may replace between
        # manifest compilation and adapter construction. Reconstruct through
        # Config so older manifests with newly introduced fields retain their
        # safe defaults during replay.
        from deepreason.authority import authority_policy_snapshot

        frozen_config = config_from_run_manifest(manifest)
        if (
            authority_policy_snapshot(config)
            != authority_policy_snapshot(frozen_config)
        ):
            raise RunManifestError(
                "TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH",
                "runtime text authority policy differs from the frozen manifest",
                "/engine_config",
            )
    active_commitments = {
        commitment_id: harness.commitments[commitment_id]
        for problem in harness.state.problems.values()
        for commitment_id in problem.criteria
        if commitment_id in harness.commitments
    }
    if manifest.rubric_policy == "forbid":
        if any(
            commitment.eval.startswith("rubric:")
            for commitment in active_commitments.values()
        ):
            raise RunManifestError(
                "RUBRIC_INPUT_FORBIDDEN",
                "this materialized run contains an active rubric criterion",
                "/problems/*/criteria",
            )

        # Property admission contains a normative cross-family relevance
        # trial. A program:property_wf criterion is program-evaluable, but an
        # enabled proposal path can still reach judges later in the run.
        from deepreason.oracle import PROPERTY_PROGRAM

        property_path_enabled = (
            int(getattr(config, "PROP_PROPOSE_PERIOD", 0)) > 0
            and int(getattr(config, "FUZZ_N", 0)) > 0
            and bool(manifest.roles.get("property_designer"))
            and bool(manifest.roles.get("judge"))
        )
        if property_path_enabled and any(
            commitment.eval == f"program:{PROPERTY_PROGRAM}"
            for commitment in active_commitments.values()
        ):
            raise RunManifestError(
                "PROPERTY_RUBRIC_TRIAL_FORBIDDEN",
                "property proposals require the frozen cross-family judge "
                "ensemble; disable PROP_PROPOSE_PERIOD explicitly or compile "
                "a require_cross_family manifest",
                "/engine_config/PROP_PROPOSE_PERIOD",
            )
