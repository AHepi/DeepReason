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
from typing import Any, Mapping, Sequence

from deepreason.llm.endpoints import DEFAULT_TIMEOUT_S
from deepreason.run_manifest import (
    Route,
    RunManifest,
    SchoolRoleBindingV1,
    infer_model_family,
)


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
        "context_window_tokens",
        "context_window",
        "max_context_tokens",
        "prompt_token_limit",
    }
)

# Values of these contract fields are data rather than control objects.  A
# counterexample can legitimately contain an application input whose key is
# e.g. ``status``; the surrounding role object remains firewall-checked.
_OPAQUE_DATA_FIELDS = frozenset({"counterexample"})


class RouteFirewallError(RuntimeError):
    """A runtime endpoint no longer matches its compiled lease."""


class SchoolRouteResolutionError(RouteFirewallError):
    """A v4 school assignment cannot resolve to its manifest-owned seat."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class JudgeEnsemblePolicyError(RuntimeError):
    """A rubric trial has no valid frozen cross-family judge ensemble."""

    code = "SECOND_JUDGE_FAMILY_REQUIRED"
    pointer = "/roles/judge"

    def __init__(self) -> None:
        super().__init__(
            f"{self.code} at {self.pointer}: rubric trials require at least "
            "two frozen judge seats from distinct route families"
        )


class JudgeSchoolEnsemblePolicyError(RuntimeError):
    """A rubric trial has no valid frozen cross-school judge ensemble.

    Distinct from ``JudgeEnsemblePolicyError`` so a stop is attributable to the
    gate that produced it: the two are never both in force for one run.
    """

    code = "SECOND_JUDGE_SCHOOL_REQUIRED"
    pointer = "/criticism_policy/bindings"

    def __init__(self) -> None:
        super().__init__(
            f"{self.code} at {self.pointer}: single-family rubric trials require "
            "at least two frozen judge seats bound to distinct schools"
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
        # production knobs. ``max_tokens`` and ``timeout_s`` are absent from
        # this equality set: they are bounded process-health controls which
        # the deterministic controller may tune and log as policy artifacts.
        # They do not permit route, model, reasoning, temperature, or
        # output-mode substitution. ``max_tokens`` is not unbounded, though —
        # a route declaring qualified capacity binds it as a CEILING below.
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
            "context_window_tokens": route.context_window_tokens,
        }
        for attr, wanted in optional.items():
            if hasattr(endpoint, attr) and getattr(endpoint, attr) != wanted:
                raise RouteFirewallError(
                    f"ROUTE_LEASE_MISMATCH role={self.role!r} seat={self.seat} "
                    f"field={attr} expected={wanted!r} "
                    f"actual={getattr(endpoint, attr)!r}"
                )
        # Qualified capacity binds the completion side of the envelope as well
        # as the total, but binds it as a ceiling rather than an identity: a
        # cap AT OR BELOW the leased allowance stays inside what qualification
        # certified, while a cap above it escapes. An equality here would make
        # the controller's own lawful settling of a wasteful cap terminal
        # mid-run, which is not a stricter guarantee but a different one.
        # Legacy routes declare no allowance and retain unbounded
        # controller-owned tuning.
        if route.context_window_tokens is not None and route.max_tokens is not None:
            cap = getattr(endpoint, "max_tokens", None)
            if cap is not None and cap > route.max_tokens:
                raise RouteFirewallError(
                    f"ROUTE_LEASE_MISMATCH role={self.role!r} seat={self.seat} "
                    f"field=max_tokens expected<={route.max_tokens!r} "
                    f"actual={cap!r}"
                )


def _lease_families(leases: Mapping[str, tuple[EndpointLease, ...]]) -> set[str]:
    """Every non-blank route family across every leased seat, folded.

    Family comes only from immutable leases, never from runtime endpoints or
    model output; blank families are dropped so an unset field cannot masquerade
    as a distinct one.
    """

    return {
        lease.route.family.strip().casefold()
        for seats in leases.values()
        for lease in seats
        if lease.route.family.strip()
    }


def is_single_family_run(leases: Mapping[str, tuple[EndpointLease, ...]]) -> bool:
    """True when exactly one model family serves the whole run.

    A cross-family judge ensemble is unobtainable here by construction, so this
    is the only condition under which cross-SCHOOL independence may stand in
    for cross-FAMILY independence.  An empty lease set is not single-family: it
    is no family at all, and must not unlock a substitute guarantee.
    """

    return len(_lease_families(leases)) == 1


def _lease_models(leases: Mapping[str, tuple[EndpointLease, ...]]) -> set[str]:
    """Every non-blank model identity across every leased seat, folded.

    Identity is (provider, model_id): the same model string served by two
    providers is two deployments, and treating them as one would claim a
    sameness nothing here has checked.
    """

    return {
        f"{lease.route.provider.strip().casefold()}:"
        f"{lease.route.model_id.strip().casefold()}"
        for seats in leases.values()
        for lease in seats
        if lease.route.model_id.strip()
    }


def is_single_model_run(leases: Mapping[str, tuple[EndpointLease, ...]]) -> bool:
    """True when one model occupies every position in the run.

    Strictly narrower than ``is_single_family_run``: two different models of
    one family are one family and two models. Narrower is the safe direction —
    this predicate unlocks a substitute for an independence guarantee, so it
    must not fire on a run that has more independence available than it thinks.
    An empty lease set is not one model; it is no model at all.
    """

    return len(_lease_models(leases)) == 1


def require_cross_family_judge_ensemble(
    leases: Mapping[str, tuple[EndpointLease, ...]],
) -> tuple[EndpointLease, ...]:
    """Validate the normative judge ensemble before any rubric model call.

    Route family comes only from immutable leases. Runtime endpoints, model
    output, and convenience ensemble counts cannot redefine this boundary.

    Accepts EITHER cross-family diversity OR a structural same-model
    substitute (adjudication-judge-seats-optins tranche, Amendment 9/R24,
    2026-08-10): >=2 judge seats that are ALL the exact same
    (provider, model_id) -- narrower than same-FAMILY, so two different
    models of one family (e.g. two distinct Gemma checkpoints) still do
    NOT satisfy this and still raise. The substitute relies on the judge
    pack's content-blindness guarantee (never discloses author/model/
    school identity, pinned by tests/test_judge_ensemble_boundary.py::
    test_judge_pack_never_names_an_author_school_or_model) rather than
    model diversity -- reachable only via the manifest-compile CLI's
    `--blind-same-model-judges` lever (SPEC's Road C finding: no
    operator-facing surface could construct this shape before it), so an
    ordinary run can never land here by accident.
    """

    seats = tuple(leases.get("judge", ()))
    families = {
        lease.route.family.strip().casefold()
        for lease in seats
        if lease.route.family.strip()
    }
    models = {
        f"{lease.route.provider.strip().casefold()}:"
        f"{lease.route.model_id.strip().casefold()}"
        for lease in seats
        if lease.route.model_id.strip()
    }
    if len(seats) < 2:
        raise JudgeEnsemblePolicyError()
    if len(families) < 2 and len(models) != 1:
        raise JudgeEnsemblePolicyError()
    return seats


def require_cross_school_judge_ensemble(
    leases: Mapping[str, tuple[EndpointLease, ...]],
    bindings: Sequence[SchoolRoleBindingV1],
) -> tuple[EndpointLease, ...]:
    """Validate the substitute judge ensemble available to a single-family run.

    Cross-family independence is unobtainable when one family serves the whole
    run, so distinctness is carried by SCHOOL instead. This is a sibling of
    ``require_cross_family_judge_ensemble``, never a relaxation of it: the two
    seats and the frozen-lease requirement are unchanged, and only the
    dimension along which the seats must differ moves.

    School is not a property of a route -- two schools may share one -- so it
    comes only from manifest-owned bindings, which is the same immutability
    guarantee the family check gets from the lease. A binding whose endpoint
    identity disagrees with the seat it names is not counted: coverage that
    cannot be verified is absence, not coverage.
    """

    seats = tuple(leases.get("judge", ()))
    by_seat = {lease.seat: lease for lease in seats}
    schools = {
        binding.school_id
        for binding in bindings
        if binding.role == "judge"
        and binding.seat in by_seat
        and binding.endpoint_id == by_seat[binding.seat].route.endpoint_id
    }
    if len(seats) < 2 or len(schools) < 2:
        raise JudgeSchoolEnsemblePolicyError()
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
        context_window_tokens=getattr(endpoint, "context_window_tokens", None),
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


def resolve_school_role_lease(
    manifest: RunManifest,
    leases: Mapping[str, tuple[EndpointLease, ...]],
    *,
    school_id: str,
    role: str,
    default_seat: int = 0,
) -> EndpointLease:
    """Resolve one school call without consulting semantic/model content.

    Historical manifests and v4 conjecturer ``conditioning_only`` preserve
    the existing role-default seat. Conjecturer ``route_bound`` and optional
    v4 foreign criticism use only their validated manifest bindings. In all
    cases the runtime lease is rechecked against the exact manifest route
    before provider dispatch.
    """

    if not school_id:
        raise SchoolRouteResolutionError(
            "SCHOOL_ROUTE_SCHOOL_REQUIRED", "school_id cannot be empty"
        )
    policy = None
    criticism_policy = None
    if manifest.schema_version in {4, 5, 6}:
        control = manifest.control_plane_policy
        if control is None:
            raise SchoolRouteResolutionError(
                "SCHOOL_ROUTE_POLICY_MISSING",
                "v4 manifest has no control-plane school policy",
            )
        if role == "conjecturer":
            policy = control.school_execution
        elif role == "argumentative_critic":
            criticism_policy = manifest.criticism_policy
            if criticism_policy is None:
                raise SchoolRouteResolutionError(
                    "SCHOOL_ROUTE_CRITICISM_POLICY_MISSING",
                    "school-routed argumentative criticism requires a v4 criticism policy",
                )
        else:
            raise SchoolRouteResolutionError(
                "SCHOOL_ROUTE_ROLE_UNSUPPORTED",
                f"school routing does not support role {role!r}",
            )
        try:
            engine_data = json.loads(manifest.engine_config_json)
        except (TypeError, json.JSONDecodeError) as error:
            raise SchoolRouteResolutionError(
                "SCHOOL_ROUTE_ENGINE_CONFIG_INVALID",
                "manifest engine configuration is not canonical JSON",
            ) from error
        school_count = engine_data.get("N_SCHOOLS")
        if isinstance(school_count, bool) or not isinstance(school_count, int):
            raise SchoolRouteResolutionError(
                "SCHOOL_ROUTE_SCHOOL_COUNT_INVALID",
                "manifest N_SCHOOLS is not an integer",
            )
        if school_id not in {f"school-{index}" for index in range(school_count)}:
            raise SchoolRouteResolutionError(
                "SCHOOL_ROUTE_SCHOOL_UNKNOWN",
                f"school {school_id!r} is outside the manifest roster",
            )

    seat = default_seat
    binding = None
    if criticism_policy is not None:
        matches = tuple(
            item
            for item in criticism_policy.bindings
            if item.school_id == school_id and item.role == role
        )
        if not matches:
            raise SchoolRouteResolutionError(
                "SCHOOL_ROUTE_BINDING_MISSING",
                f"no binding for {school_id}/{role}",
            )
        if len(matches) != 1:
            raise SchoolRouteResolutionError(
                "SCHOOL_ROUTE_BINDING_AMBIGUOUS",
                f"multiple bindings for {school_id}/{role}",
            )
        binding = matches[0]
        seat = binding.seat
    elif policy is not None and policy.mode == "route_bound":
        matches = tuple(
            item
            for item in policy.bindings
            if item.school_id == school_id and item.role == role
        )
        if not matches:
            raise SchoolRouteResolutionError(
                "SCHOOL_ROUTE_BINDING_MISSING",
                f"no binding for {school_id}/{role}",
            )
        if len(matches) != 1:
            raise SchoolRouteResolutionError(
                "SCHOOL_ROUTE_BINDING_AMBIGUOUS",
                f"multiple bindings for {school_id}/{role}",
            )
        binding = matches[0]
        seat = binding.seat

    try:
        lease = select_lease(leases, role, seat)
        manifest_route = manifest.roles[role][seat]
    except (KeyError, IndexError) as error:
        raise SchoolRouteResolutionError(
            "SCHOOL_ROUTE_SEAT_UNAVAILABLE",
            f"no frozen runtime lease for {role}[{seat}]",
        ) from error
    if lease.route != manifest_route:
        raise SchoolRouteResolutionError(
            "SCHOOL_ROUTE_LEASE_MISMATCH",
            f"runtime lease for {role}[{seat}] differs from the manifest route",
        )
    if binding is not None and binding.endpoint_id != lease.route.endpoint_id:
        raise SchoolRouteResolutionError(
            "SCHOOL_ROUTE_ENDPOINT_MISMATCH",
            "binding endpoint identity differs from the selected lease",
        )
    return lease
