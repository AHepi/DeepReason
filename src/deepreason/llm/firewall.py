"""Non-model-controlled route and operator boundaries.

An endpoint model is a bounded ``pack -> value`` function.  It cannot choose
its route, delegate, request a tool, or turn output fields into harness
authority.  This module keeps those process constraints separate from the
epistemic ontology.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from deepreason.llm.endpoints import DEFAULT_TIMEOUT_S
from deepreason.run_manifest import Route, RunManifest, infer_model_family


FORBIDDEN_MODEL_CONTROL_FIELDS = frozenset(
    {
        "model",
        "model_id",
        "endpoint",
        "endpoint_id",
        "provider",
        "route",
        "routes",
        "tool",
        "tools",
        "command",
        "delegate",
        "delegates",
        "permission",
        "permissions",
        "spawn",
        "peer",
        "guard_policy",
        "bypass_guard",
        "bypass_guards",
        "acceptance",
        "status",
        "concurrency",
    }
)

# Values of these contract fields are data rather than control objects.  A
# counterexample can legitimately contain an application input whose key is
# e.g. ``status``; the surrounding role object remains firewall-checked.
_OPAQUE_DATA_FIELDS = frozenset({"counterexample"})


class RouteFirewallError(RuntimeError):
    """A runtime endpoint no longer matches its compiled lease."""


class JudgeEnsemblePolicyError(RuntimeError):
    """A rubric trial has no valid frozen cross-family judge ensemble."""

    code = "SECOND_JUDGE_FAMILY_REQUIRED"
    pointer = "/roles/judge"

    def __init__(self) -> None:
        super().__init__(
            f"{self.code} at {self.pointer}: rubric trials require at least "
            "two frozen judge seats from distinct route families"
        )


class ModelControlFieldError(ValueError):
    """Model JSON tried to express authority outside its role contract."""

    def __init__(self, field: str, pointer: str) -> None:
        self.code = "MODEL_CONTROL_FIELD_FORBIDDEN"
        self.field = field
        self.pointer = pointer
        super().__init__(f"{self.code} at {pointer}: field {field!r} is not role output")


def route_fingerprint(route: Route) -> str:
    """Content hash of one exact, secret-free manifest route."""
    payload = json.dumps(
        route.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _json_pointer_part(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def reject_model_control_fields(value: Any, pointer: str = "") -> None:
    """Reject routing/operator fields without executing or interpreting them."""
    if isinstance(value, dict):
        for key, child in value.items():
            name = str(key)
            child_pointer = f"{pointer}/{_json_pointer_part(name)}"
            if name.lower() in FORBIDDEN_MODEL_CONTROL_FIELDS:
                raise ModelControlFieldError(name, child_pointer)
            if name.lower() not in _OPAQUE_DATA_FIELDS:
                reject_model_control_fields(child, child_pointer)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_model_control_fields(child, f"{pointer}/{index}")


def _strings_in(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value} if value else set()
    if isinstance(value, dict):
        return set().union(*(_strings_in(child) for child in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_strings_in(child) for child in value), set())
    return set()


def _control_value_strings(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            name = str(key).lower()
            if name in FORBIDDEN_MODEL_CONTROL_FIELDS:
                found.update(_strings_in(child))
            elif name not in _OPAQUE_DATA_FIELDS:
                found.update(_control_value_strings(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_control_value_strings(child))
    return found


def _sanitize_for_repair(value: Any, sensitive_strings: set[str]) -> Any:
    if isinstance(value, dict):
        sanitized: dict[Any, Any] = {}
        for key, child in value.items():
            name = str(key).lower()
            if name in FORBIDDEN_MODEL_CONTROL_FIELDS:
                continue
            sanitized[key] = (
                _redact_strings(child, sensitive_strings)
                if name in _OPAQUE_DATA_FIELDS
                else _sanitize_for_repair(child, sensitive_strings)
            )
        return sanitized
    if isinstance(value, list):
        return [_sanitize_for_repair(child, sensitive_strings) for child in value]
    if isinstance(value, str):
        sanitized = value
        for sensitive in sorted(sensitive_strings, key=len, reverse=True):
            sanitized = sanitized.replace(sensitive, "[redacted]")
        return sanitized
    return deepcopy(value)


def _redact_strings(value: Any, sensitive_strings: set[str]) -> Any:
    if isinstance(value, dict):
        return {
            key: _redact_strings(child, sensitive_strings)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_redact_strings(child, sensitive_strings) for child in value]
    if isinstance(value, str):
        sanitized = value
        for sensitive in sorted(sensitive_strings, key=len, reverse=True):
            sanitized = sanitized.replace(sensitive, "[redacted]")
        return sanitized
    return deepcopy(value)


def sanitize_model_control_fields_for_repair(value: Any) -> Any:
    """Return a model-facing repair copy with control pairs removed.

    This is *not* output normalization and must never be compiled or
    registered. The exact raw remains in the blob log and remains invalid;
    this copy exists solely to ensure a bounded repair pack cannot reflect an
    authored route, delegation, guard, permission, or command back to a role
    model. Opaque application data follows the same exception as
    :func:`reject_model_control_fields`.
    """
    return _sanitize_for_repair(value, _control_value_strings(value))


@dataclass(frozen=True, slots=True)
class EndpointLease:
    """One role seat permanently bound to one concrete Route."""

    role: str
    seat: int
    route: Route

    def __post_init__(self) -> None:
        if not self.role:
            raise ValueError("EndpointLease role cannot be empty")
        if self.seat < 0:
            raise ValueError("EndpointLease seat cannot be negative")

    def verify(self, endpoint: object) -> None:
        """Fail closed if code mutates or substitutes the leased endpoint."""
        route = self.route
        actual = {
            "base_url": getattr(endpoint, "name", ""),
            "model_id": getattr(endpoint, "model", ""),
        }
        expected = {"base_url": route.base_url, "model_id": route.model_id}
        for field, wanted in expected.items():
            got = actual[field]
            if got != wanted:
                raise RouteFirewallError(
                    f"ROUTE_LEASE_MISMATCH role={self.role!r} seat={self.seat} "
                    f"field={field} expected={wanted!r} actual={got!r}"
                )
        # Optional endpoint attributes are checked when the endpoint exposes
        # them. This keeps MockEndpoint usable while freezing model-facing
        # production knobs. ``max_tokens`` and ``timeout_s`` are intentionally
        # absent: they are bounded process-health controls which the
        # deterministic controller may tune and log as Measure events. They
        # do not permit route, model, reasoning, temperature, or output-mode
        # substitution.
        optional = {
            "endpoint_id": route.endpoint_id,
            "family": route.family,
            "model_revision": route.model_revision,
            "provider": route.provider,
            "reasoning": route.reasoning,
            "temperature": route.temperature,
            "json_mode": route.output_mode == "json_object",
            "output_mechanism": route.output_mechanism,
            "request_logprobs": route.logprobs,
        }
        for attr, wanted in optional.items():
            if hasattr(endpoint, attr) and getattr(endpoint, attr) != wanted:
                raise RouteFirewallError(
                    f"ROUTE_LEASE_MISMATCH role={self.role!r} seat={self.seat} "
                    f"field={attr} expected={wanted!r} "
                    f"actual={getattr(endpoint, attr)!r}"
                )


def require_cross_family_judge_ensemble(
    leases: Mapping[str, tuple[EndpointLease, ...]],
) -> tuple[EndpointLease, ...]:
    """Validate the normative judge ensemble before any rubric model call.

    Route family comes only from immutable leases. Runtime endpoints, model
    output, and convenience ensemble counts cannot redefine this boundary.
    """

    seats = tuple(leases.get("judge", ()))
    families = {
        lease.route.family.strip().casefold()
        for lease in seats
        if lease.route.family.strip()
    }
    if len(seats) < 2 or len(families) < 2:
        raise JudgeEnsemblePolicyError()
    return seats


def route_from_endpoint(endpoint: object) -> Route:
    """Freeze an already-resolved legacy endpoint into a runtime lease."""
    base_url = str(getattr(endpoint, "name", ""))
    model_id = str(getattr(endpoint, "model", ""))
    if not base_url or not model_id:
        raise RouteFirewallError("endpoint must expose exact name and model")
    provider = str(getattr(endpoint, "provider", "mock"))
    family = str(
        getattr(endpoint, "family", "") or infer_model_family(model_id, provider)
    )
    endpoint_id = str(getattr(endpoint, "endpoint_id", "") or base_url)
    return Route(
        endpoint_id=endpoint_id,
        base_url=base_url,
        model_id=model_id,
        model_revision=getattr(endpoint, "model_revision", None),
        provider=provider,
        family=family,
        reasoning=getattr(endpoint, "reasoning", None),
        output_mode=("json_object" if getattr(endpoint, "json_mode", False) else "text"),
        output_mechanism=getattr(endpoint, "output_mechanism", "json_text") or "json_text",
        temperature=getattr(endpoint, "temperature", None),
        max_tokens=getattr(endpoint, "max_tokens", None),
        timeout_s=getattr(endpoint, "timeout_s", DEFAULT_TIMEOUT_S),
        logprobs=bool(getattr(endpoint, "request_logprobs", False)),
        api_key_env=None,
    )


def leases_from_endpoints(
    endpoints: Mapping[str, object],
) -> dict[str, tuple[EndpointLease, ...]]:
    """Freeze the legacy role table once at adapter construction."""
    leases: dict[str, tuple[EndpointLease, ...]] = {}
    for role, configured in endpoints.items():
        seats = configured if isinstance(configured, (list, tuple)) else (configured,)
        leases[role] = tuple(
            EndpointLease(role=role, seat=index, route=route_from_endpoint(endpoint))
            for index, endpoint in enumerate(seats)
        )
    return leases


def leases_from_manifest(manifest: RunManifest) -> dict[str, tuple[EndpointLease, ...]]:
    return {
        role: tuple(
            EndpointLease(role=role, seat=index, route=route)
            for index, route in enumerate(routes)
        )
        for role, routes in manifest.roles.items()
        if routes
    }


def select_lease(
    leases: Mapping[str, tuple[EndpointLease, ...]], role: str, seat: int
) -> EndpointLease:
    try:
        lease = leases[role][seat]
    except (KeyError, IndexError) as error:
        raise KeyError(f"no endpoint lease configured for role {role!r} seat {seat}") from error
    if lease.role != role or lease.seat != seat:
        raise RouteFirewallError(
            f"lease identity mismatch: requested {role}[{seat}], got "
            f"{lease.role}[{lease.seat}]"
        )
    return lease
