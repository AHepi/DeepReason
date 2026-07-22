"""Application-boundary provider profiles with no credential values.

Resolution is deliberately outside :mod:`deepreason.config`.  The core
configuration loader remains pure; operator-facing callers explicitly choose
one profile using the closed precedence implemented here.
"""

from __future__ import annotations

import math
import os
import re
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    field_validator,
    model_validator,
)

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.run_manifest import validate_route_base_url


PROFILE_ENV = "DEEPREASON_PROFILE"
PROFILE_FILENAME = "provider.yaml"
PROFILE_SCHEMA = "deepreason-provider-profile.v1"
_PROFILE_ID_DOMAIN = b"deepreason.provider-profile.v1\x00"
_MAX_PROFILE_BYTES = 64 * 1024
_ENV_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DIGEST = r"^[0-9a-f]{64}$"


class ProviderProfileError(ValueError):
    """Stable, redacted application-boundary profile failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class ProviderProfileV1(BaseModel):
    """One exact secret-free provider/model/transport identity."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        serialize_by_alias=True,
        hide_input_in_errors=True,
    )

    schema_: Literal["deepreason-provider-profile.v1"] = Field(
        PROFILE_SCHEMA, alias="schema"
    )
    profile_digest: str = Field(pattern=_DIGEST)
    provider: str = Field(min_length=1, max_length=128)
    endpoint: str = Field(min_length=1, max_length=4_096)
    model_id: str = Field(min_length=1, max_length=1_024)
    model_revision: str | None = Field(default=None, max_length=1_024)
    family: str = Field(min_length=1, max_length=256)
    context_window_tokens: StrictInt = Field(gt=0)
    maximum_completion_tokens: StrictInt = Field(gt=0)
    credential_env: str = Field(min_length=1, max_length=256)
    model_profile: Literal["compact", "standard", "frontier"] = "standard"
    reasoning: str | StrictInt | None = None
    output_mode: Literal["json_object", "text"] = "json_object"
    output_mechanism: Literal[
        "native_json_schema", "grammar", "json_text"
    ] = "json_text"
    temperature: StrictFloat | None = None
    timeout_s: StrictInt = Field(default=120, gt=0)
    logprobs: bool = False

    @field_validator(
        "provider", "endpoint", "model_id", "model_revision", "family"
    )
    @classmethod
    def _bounded_nonblank_text(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("profile text fields must be nonblank")
        if value is not None and any(not character.isprintable() for character in value):
            raise ValueError("profile text fields must not contain control characters")
        return value

    @field_validator("endpoint")
    @classmethod
    def _secret_free_endpoint(cls, value: str) -> str:
        return validate_route_base_url(value)

    @field_validator("credential_env")
    @classmethod
    def _credential_reference_is_an_environment_name(cls, value: str) -> str:
        if _ENV_IDENTIFIER.fullmatch(value) is None:
            raise ValueError(
                "credential_env must be a POSIX environment-variable name"
            )
        return value

    @field_validator("temperature")
    @classmethod
    def _finite_temperature(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("temperature must be finite")
        return value

    @model_validator(mode="after")
    def _finite_capacity_and_identity(self):
        if self.context_window_tokens <= self.maximum_completion_tokens:
            raise ValueError(
                "context_window_tokens must exceed maximum_completion_tokens"
            )
        expected = self.identity_digest(self.identity_payload())
        if self.profile_digest != expected:
            raise ValueError("provider profile digest does not match its payload")
        return self

    @staticmethod
    def identity_digest(payload: Mapping[str, Any]) -> str:
        return sha256_hex(_PROFILE_ID_DOMAIN + canonical_json(dict(payload)))

    def identity_payload(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json", by_alias=True, exclude={"profile_digest"}
        )

    @classmethod
    def create(cls, **values: Any) -> "ProviderProfileV1":
        values = dict(values)
        values.pop("profile_digest", None)
        provisional = cls.model_construct(profile_digest="0" * 64, **values)
        payload = provisional.model_dump(
            mode="json",
            by_alias=True,
            exclude={"profile_digest"},
            warnings=False,
        )
        return cls(profile_digest=cls.identity_digest(payload), **values)

    @property
    def endpoint_id(self) -> str:
        return f"provider-profile-{self.profile_digest[:24]}"

    def endpoint_spec(self) -> dict[str, Any]:
        """Return the strict Config role-seat form without reading a secret."""

        return {
            "endpoint_id": self.endpoint_id,
            "endpoint": self.endpoint,
            "model": self.model_id,
            "model_revision": self.model_revision,
            "family": self.family,
            "provider": self.provider,
            "reasoning": self.reasoning,
            "max_tokens": self.maximum_completion_tokens,
            "context_window_tokens": self.context_window_tokens,
            "api_key_env": self.credential_env,
            "model_profile": self.model_profile,
            "json_mode": self.output_mode == "json_object",
            "output_mode": self.output_mode,
            "output_mechanism": self.output_mechanism,
            "temperature": self.temperature,
            "timeout_s": self.timeout_s,
            "logprobs": self.logprobs,
        }


class ResolvedProviderProfileV1(BaseModel):
    """A typed profile together with the winning application source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile: ProviderProfileV1
    source: Literal["explicit", "environment", "setup"]
    path: str = Field(min_length=1, max_length=4_096)


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ProviderProfileError(
                "PROVIDER_PROFILE_MALFORMED",
                "provider profile contains a duplicate field",
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _read_profile(path: Path) -> bytes:
    try:
        observed = path.lstat()
    except FileNotFoundError as error:
        raise ProviderProfileError(
            "PROVIDER_PROFILE_MISSING", "selected provider profile is absent"
        ) from error
    except OSError as error:
        raise ProviderProfileError(
            "PROVIDER_PROFILE_UNAVAILABLE",
            "selected provider profile cannot be inspected safely",
        ) from error
    if (
        not stat.S_ISREG(observed.st_mode)
        or stat.S_ISLNK(observed.st_mode)
        or not 1 <= observed.st_size <= _MAX_PROFILE_BYTES
    ):
        raise ProviderProfileError(
            "PROVIDER_PROFILE_UNSAFE",
            "selected provider profile must be a bounded regular file",
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or opened.st_size != observed.st_size:
                raise ProviderProfileError(
                    "PROVIDER_PROFILE_UNSAFE",
                    "selected provider profile changed while opening",
                )
            payload = stream.read(_MAX_PROFILE_BYTES + 1)
        current = path.lstat()
    except ProviderProfileError:
        raise
    except OSError as error:
        raise ProviderProfileError(
            "PROVIDER_PROFILE_UNAVAILABLE",
            "selected provider profile cannot be read safely",
        ) from error
    if (
        len(payload) != opened.st_size
        or len(payload) > _MAX_PROFILE_BYTES
        or not stat.S_ISREG(current.st_mode)
        or current.st_size != opened.st_size
        or (
            opened.st_ino
            and current.st_ino
            and (opened.st_dev, opened.st_ino)
            != (current.st_dev, current.st_ino)
        )
    ):
        raise ProviderProfileError(
            "PROVIDER_PROFILE_UNSAFE",
            "selected provider profile changed while being read",
        )
    return payload


def load_provider_profile(path: Path | str) -> ProviderProfileV1:
    """Load one strict profile without echoing malformed input values."""

    try:
        decoded = yaml.load(_read_profile(Path(path)), Loader=_UniqueKeyLoader)
        if not isinstance(decoded, dict):
            raise ValueError
        return ProviderProfileV1.model_validate(decoded)
    except ProviderProfileError:
        raise
    except (UnicodeError, yaml.YAMLError, ValueError, TypeError):
        raise ProviderProfileError(
            "PROVIDER_PROFILE_MALFORMED",
            "selected provider profile is not a valid secret-free profile",
        ) from None


def provider_state_dir(
    *,
    home: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    environment = os.environ if environ is None else environ
    configured = str(environment.get("DEEPREASON_HOME", "")).strip()
    if configured:
        return Path(configured)
    return Path(home) / ".deepreason" if home is not None else Path.home() / ".deepreason"


def setup_provider_profile_path(
    *,
    home: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    return provider_state_dir(home=home, environ=environ) / PROFILE_FILENAME


def resolve_provider_profile(
    explicit_path: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | str | None = None,
) -> ResolvedProviderProfileV1:
    """Resolve exactly explicit path, DEEPREASON_PROFILE, then setup profile."""

    environment = os.environ if environ is None else environ
    if explicit_path is not None:
        path = Path(explicit_path)
        source = "explicit"
    elif PROFILE_ENV in environment:
        raw = str(environment.get(PROFILE_ENV, ""))
        if not raw.strip():
            raise ProviderProfileError(
                "PROVIDER_PROFILE_PATH_INVALID",
                f"{PROFILE_ENV} must name a provider profile",
            )
        path = Path(raw)
        source = "environment"
    else:
        path = setup_provider_profile_path(home=home, environ=environment)
        source = "setup"
    return ResolvedProviderProfileV1(
        profile=load_provider_profile(path),
        source=source,
        path=str(path),
    )


def credential_present(
    profile: ProviderProfileV1,
    *,
    environ: Mapping[str, str] | None = None,
) -> bool:
    environment = os.environ if environ is None else environ
    value = environment.get(profile.credential_env)
    return isinstance(value, str) and bool(value.strip())


def write_provider_profile(
    profile: ProviderProfileV1,
    target: Path | str,
) -> Path:
    """Write a setup profile atomically; the model cannot contain a key."""

    profile = ProviderProfileV1.model_validate(profile)
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        profile.model_dump(mode="json", by_alias=True),
        sort_keys=True,
        allow_unicode=True,
    ).encode("utf-8")
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return path


__all__ = [
    "PROFILE_ENV",
    "PROFILE_FILENAME",
    "ProviderProfileError",
    "ProviderProfileV1",
    "ResolvedProviderProfileV1",
    "credential_present",
    "load_provider_profile",
    "provider_state_dir",
    "resolve_provider_profile",
    "setup_provider_profile_path",
    "write_provider_profile",
]
