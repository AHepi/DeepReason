#!/usr/bin/env python3
"""Offline domain, safety, and resume primitives for the full-judge matrix."""
from __future__ import annotations
import argparse, contextlib, fcntl, hashlib, itertools, json, os, re, struct
import subprocess, sys, tempfile, threading, unicodedata
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

SEAT_SCHEMA = "deepreason.full-judge-seat-case.v1"
STRUCTURAL_SCHEMA = "deepreason.full-judge-structural-case.v1"
FULL_CROSS_DOMAIN_SCHEMA = "deepreason.full-cross-judge-domain.v1"
FULL_CROSS_CASE_SCHEMA = "deepreason.full-cross-judge-case.v1"
FORBIDDEN_REASONING = frozenset({"high", "max", "xhigh"})
RESULT_FIELDS = ("case_id", "status", "code", "message", "stage",
                 "exception_type", "pointer", "dispatch_history")
_CALL_SLOTS = threading.BoundedSemaphore(3)
_CALL_COUNTER_LOCK = threading.Lock()
_CALL_COUNTER = {"active": 0, "peak": 0}


def compile_run_manifest(*args, **kwargs):
    """Patchable experiment seam around the shipped manifest compiler."""
    from deepreason.run_manifest import compile_run_manifest as shipped_compile

    return shipped_compile(*args, **kwargs)


class MatrixRefusal(RuntimeError):
    """Typed campaign refusal whose stable code is present in ``str(exc)``."""
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}" if message else code)
def canonical_json(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
def _sha256_id(payload: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(payload)).hexdigest()
def load_domain(path: str | os.PathLike[str]) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        domain = json.load(handle)
    if domain.get("schema") != "deepreason.full-judge-matrix-domain.v1":
        raise MatrixRefusal("DOMAIN_SCHEMA_UNSUPPORTED")
    return domain
def seat_counts(model_count: int) -> dict[str, int]:
    if isinstance(model_count, bool) or model_count < 1:
        raise MatrixRefusal("EMPTY_MODEL_CATALOG")
    return {
        "judge_pairs": model_count**2,
        "core_courts": model_count**3,
        "no_variator": model_count**4,
        "with_variator": model_count**5,
        "total": model_count**4 + model_count**5,
    }
def transport_counts(model_count: int) -> dict[str, int]:
    per_model = 3 * 2 * 3 * 4 * 3 * (1 + 5)
    return {"per_model": per_model, "total": model_count * per_model}
def domain_counts(domain: Mapping[str, Any]) -> dict[str, int]:
    model_count = len(domain["fixture_catalog"])
    seat = seat_counts(model_count)["total"]
    transport = transport_counts(model_count)["total"]
    return {"seat": seat, "transport": transport, "combined": seat + transport}


_FULL_CROSS_LITERAL_AXES = {
    "judge_count": {2, 3},
    "split_protocol": {"auto", "on", "off"},
    "model_profile_per_seat": {"compact", "standard", "frontier"},
    "output_mode_per_seat": {"text", "json_object"},
    "output_mechanism_per_seat": {"native_json_schema", "grammar", "json_text"},
    "paraphrase_count_with_variator": {-1, 0, 1, 2, 3},
}
_FULL_CROSS_REASONING = (
    {"kind": "string", "value": "none"},
    {"kind": "string", "value": "low"},
    {"kind": "string", "value": "medium"},
    {"kind": "integer", "value": 2_000},
)


def _full_cross_axis(axes: Mapping[str, Any], name: str) -> list[Any]:
    values = axes.get(name)
    if not isinstance(values, list) or not values:
        raise MatrixRefusal("FULL_CROSS_DOMAIN_INVALID", f"{name} must be nonempty")
    encoded = [canonical_json(value) for value in values]
    if len(set(encoded)) != len(encoded):
        raise MatrixRefusal("FULL_CROSS_DOMAIN_INVALID", f"{name} contains duplicates")
    return values


def _validate_full_cross_domain(domain: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(domain, Mapping) or domain.get("schema") != FULL_CROSS_DOMAIN_SCHEMA:
        raise MatrixRefusal("FULL_CROSS_DOMAIN_SCHEMA_UNSUPPORTED")
    axes = domain.get("finite_axes")
    if not isinstance(axes, Mapping):
        raise MatrixRefusal("FULL_CROSS_DOMAIN_INVALID", "finite_axes is absent")
    for name, allowed in _FULL_CROSS_LITERAL_AXES.items():
        values = _full_cross_axis(axes, name)
        if any(isinstance(value, bool) or value not in allowed for value in values):
            raise MatrixRefusal("FULL_CROSS_DOMAIN_INVALID", f"{name} left its frozen domain")
    reasoning = _full_cross_axis(axes, "reasoning_per_seat")
    if any(
        not isinstance(value, Mapping)
        or set(value) != {"kind", "value"}
        or not any(value == registered for registered in _FULL_CROSS_REASONING)
        for value in reasoning
    ):
        raise MatrixRefusal(
            "FULL_CROSS_DOMAIN_INVALID", "reasoning_per_seat left its typed frozen domain"
        )
    if axes.get("paraphrase_count_without_variator", object()) is not None:
        raise MatrixRefusal(
            "FULL_CROSS_DOMAIN_INVALID",
            "paraphrase_count_without_variator must be null",
        )
    return axes


def load_full_cross_domain(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Load the frozen full-cross document without normalizing its ordering."""
    with Path(path).open(encoding="utf-8") as handle:
        domain = json.load(handle)
    _validate_full_cross_domain(domain)
    return domain


def full_cross_seat_tuple_count(domain: Mapping[str, Any], *, model_count: int) -> int:
    """Return ``S`` using Python's arbitrary-precision integer arithmetic."""
    axes = _validate_full_cross_domain(domain)
    if isinstance(model_count, bool) or not isinstance(model_count, int) or model_count < 1:
        raise MatrixRefusal("EMPTY_MODEL_CATALOG")
    return model_count * (
        len(axes["model_profile_per_seat"])
        * len(axes["output_mode_per_seat"])
        * len(axes["output_mechanism_per_seat"])
        * len(axes["reasoning_per_seat"])
    )


def full_cross_counts(domain: Mapping[str, Any], *, model_count: int) -> dict[str, int]:
    """Return exact per-topology and union cardinalities for this literal domain."""
    axes = _validate_full_cross_domain(domain)
    seat_tuples = full_cross_seat_tuple_count(domain, model_count=model_count)
    split_count = len(axes["split_protocol"])
    paraphrase_count = len(axes["paraphrase_count_with_variator"])
    result = {"seat_tuples": seat_tuples}
    total = 0
    for judge_count in axes["judge_count"]:
        count = (
            split_count * seat_tuples ** (2 + judge_count)
            + split_count * paraphrase_count * seat_tuples ** (3 + judge_count)
        )
        result[f"judge_count_{judge_count}"] = count
        total += count
    result["total"] = total
    return result


def _full_cross_models(model_ids: Iterable[str]) -> list[str]:
    models = freeze_catalog(model_ids)["model_ids"]
    if not models:
        raise MatrixRefusal("EMPTY_MODEL_CATALOG")
    return models


def _require_full_cross_authority(
    domain: Mapping[str, Any], criticism_authority: Any
) -> None:
    integrity = domain.get("request_integrity")
    if (
        criticism_authority != "defended_trial"
        or not isinstance(integrity, Mapping)
        or integrity.get("criticism_authority") != "defended_trial"
    ):
        raise MatrixRefusal("FULL_CROSS_REQUIRES_DEFENDED_TRIAL")


def _validate_full_cross_catalog_digest(catalog_sha256: Any) -> None:
    if (
        not isinstance(catalog_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", catalog_sha256) is None
    ):
        raise MatrixRefusal("FULL_CROSS_CATALOG_DIGEST_INVALID")


def _full_cross_tuple_axes(
    axes: Mapping[str, Any], models: Sequence[str]
) -> tuple[Sequence[Any], ...]:
    return (
        models,
        axes["model_profile_per_seat"],
        axes["output_mode_per_seat"],
        axes["output_mechanism_per_seat"],
        axes["reasoning_per_seat"],
    )


def _decode_mixed_radix(index: int, radices: Sequence[int]) -> list[int]:
    digits = [0] * len(radices)
    for position in range(len(radices) - 1, -1, -1):
        index, digits[position] = divmod(index, radices[position])
    if index:
        raise MatrixRefusal("FULL_CROSS_ORDINAL_OUT_OF_RANGE")
    return digits


def _encode_mixed_radix(digits: Sequence[int], radices: Sequence[int]) -> int:
    value = 0
    for digit, radix in zip(digits, radices):
        value = value * radix + digit
    return value


def _full_cross_seat_at(
    axes: Mapping[str, Any], models: Sequence[str], tuple_index: int, role: str
) -> dict[str, Any]:
    tuple_axes = _full_cross_tuple_axes(axes, models)
    digits = _decode_mixed_radix(tuple_index, [len(axis) for axis in tuple_axes])
    values = [axis[digit] for axis, digit in zip(tuple_axes, digits)]
    reasoning = values[4]
    return {
        "role": role,
        "model_id": values[0],
        "model_profile": values[1],
        "output_mode": values[2],
        "output_mechanism": values[3],
        "reasoning": {"kind": reasoning["kind"], "value": reasoning["value"]},
    }


def _full_cross_roles(judge_count: int, with_variator: bool) -> list[str]:
    roles = ["critic", "defender", *(f"judge:{seat}" for seat in range(judge_count))]
    if with_variator:
        roles.append("variator")
    return roles


def _full_cross_component(
    axes: Mapping[str, Any], seat_tuple_count: int, ordinal: int
) -> tuple[int, bool, int]:
    split_count = len(axes["split_protocol"])
    paraphrase_count = len(axes["paraphrase_count_with_variator"])
    remaining = ordinal
    for judge_count in axes["judge_count"]:
        for with_variator in (False, True):
            role_count = 2 + judge_count + int(with_variator)
            multiplier = split_count * (paraphrase_count if with_variator else 1)
            size = multiplier * seat_tuple_count**role_count
            if remaining < size:
                return judge_count, with_variator, remaining
            remaining -= size
    raise MatrixRefusal("FULL_CROSS_ORDINAL_OUT_OF_RANGE")


def full_cross_case_at(
    domain: Mapping[str, Any],
    model_ids: Iterable[str],
    ordinal: int,
    *,
    catalog_sha256: str,
    criticism_authority: str | None,
) -> dict[str, Any]:
    """Decode one case directly; no earlier case is generated or inspected."""
    axes = _validate_full_cross_domain(domain)
    _require_full_cross_authority(domain, criticism_authority)
    models = _full_cross_models(model_ids)
    counts = full_cross_counts(domain, model_count=len(models))
    if (
        isinstance(ordinal, bool)
        or not isinstance(ordinal, int)
        or ordinal < 0
        or ordinal >= counts["total"]
    ):
        raise MatrixRefusal("FULL_CROSS_ORDINAL_OUT_OF_RANGE")
    _validate_full_cross_catalog_digest(catalog_sha256)

    judge_count, with_variator, local = _full_cross_component(
        axes, counts["seat_tuples"], ordinal
    )
    roles = _full_cross_roles(judge_count, with_variator)
    assignment_count = counts["seat_tuples"] ** len(roles)
    if with_variator:
        per_split = len(axes["paraphrase_count_with_variator"]) * assignment_count
        split_index, local = divmod(local, per_split)
        paraphrase_index, assignment_index = divmod(local, assignment_count)
        paraphrase_count = axes["paraphrase_count_with_variator"][paraphrase_index]
    else:
        split_index, assignment_index = divmod(local, assignment_count)
        paraphrase_count = None
    tuple_indices = _decode_mixed_radix(
        assignment_index, [counts["seat_tuples"]] * len(roles)
    )
    identity = {
        "schema": FULL_CROSS_CASE_SCHEMA,
        "catalog_sha256": catalog_sha256,
        "judge_count": judge_count,
        "split_protocol": axes["split_protocol"][split_index],
        "paraphrase_count": paraphrase_count,
        "seats": [
            _full_cross_seat_at(axes, models, tuple_index, role)
            for role, tuple_index in zip(roles, tuple_indices)
        ],
    }
    return {
        **identity,
        "ordinal": ordinal,
        "case_id": _sha256_id(identity),
        "criticism_authority": "defended_trial",
    }


def _full_cross_axis_index(axis: Sequence[Any], value: Any, field: str) -> int:
    for index, candidate in enumerate(axis):
        if canonical_json(candidate) == canonical_json(value):
            return index
    raise MatrixRefusal("FULL_CROSS_CASE_INVALID", f"{field} left its frozen axis")


def _full_cross_seat_ordinal(
    axes: Mapping[str, Any], models: Sequence[str], seat: Mapping[str, Any]
) -> int:
    expected = {
        "role", "model_id", "model_profile", "output_mode", "output_mechanism", "reasoning"
    }
    if not isinstance(seat, Mapping) or set(seat) != expected:
        raise MatrixRefusal("FULL_CROSS_CASE_INVALID", "seat schema mismatch")
    tuple_axes = _full_cross_tuple_axes(axes, models)
    fields = ("model_id", "model_profile", "output_mode", "output_mechanism", "reasoning")
    digits = [
        _full_cross_axis_index(axis, seat[field], field)
        for axis, field in zip(tuple_axes, fields)
    ]
    return _encode_mixed_radix(digits, [len(axis) for axis in tuple_axes])


def full_cross_case_ordinal(
    domain: Mapping[str, Any], model_ids: Iterable[str], row: Mapping[str, Any]
) -> int:
    """Encode a case directly back to its stable mixed-radix ordinal."""
    axes = _validate_full_cross_domain(domain)
    if not isinstance(row, Mapping):
        raise MatrixRefusal("FULL_CROSS_CASE_INVALID")
    _require_full_cross_authority(domain, row.get("criticism_authority"))
    if row.get("schema") != FULL_CROSS_CASE_SCHEMA:
        raise MatrixRefusal("FULL_CROSS_CASE_SCHEMA_UNSUPPORTED")
    models = _full_cross_models(model_ids)
    judge_count = row.get("judge_count")
    judge_index = _full_cross_axis_index(axes["judge_count"], judge_count, "judge_count")
    seats = row.get("seats")
    if not isinstance(seats, list):
        raise MatrixRefusal("FULL_CROSS_CASE_INVALID", "seats must be a list")
    no_variator_roles = _full_cross_roles(judge_count, False)
    with_variator = len(seats) == len(no_variator_roles) + 1
    roles = _full_cross_roles(judge_count, with_variator)
    if (
        len(seats) != len(roles)
        or any(not isinstance(seat, Mapping) for seat in seats)
        or [seat.get("role") for seat in seats] != roles
    ):
        raise MatrixRefusal("FULL_CROSS_CASE_INVALID", "seat roles or order mismatch")
    paraphrase = row.get("paraphrase_count")
    if with_variator:
        paraphrase_index = _full_cross_axis_index(
            axes["paraphrase_count_with_variator"], paraphrase, "paraphrase_count"
        )
    elif paraphrase is None:
        paraphrase_index = 0
    else:
        raise MatrixRefusal("FULL_CROSS_CASE_INVALID", "unexpected paraphrase_count")
    split_index = _full_cross_axis_index(
        axes["split_protocol"], row.get("split_protocol"), "split_protocol"
    )
    seat_tuple_count = full_cross_seat_tuple_count(domain, model_count=len(models))
    seat_ordinals = [_full_cross_seat_ordinal(axes, models, seat) for seat in seats]
    assignment_ordinal = _encode_mixed_radix(
        seat_ordinals, [seat_tuple_count] * len(seats)
    )

    ordinal = 0
    split_count = len(axes["split_protocol"])
    paraphrase_axis_count = len(axes["paraphrase_count_with_variator"])
    for prior_judge_count in axes["judge_count"][:judge_index]:
        ordinal += split_count * seat_tuple_count ** (2 + prior_judge_count)
        ordinal += (
            split_count
            * paraphrase_axis_count
            * seat_tuple_count ** (3 + prior_judge_count)
        )
    no_variator_assignments = seat_tuple_count ** (2 + judge_count)
    if with_variator:
        ordinal += split_count * no_variator_assignments
        assignment_count = seat_tuple_count ** (3 + judge_count)
        ordinal += (
            (split_index * paraphrase_axis_count + paraphrase_index) * assignment_count
            + assignment_ordinal
        )
    else:
        ordinal += split_index * no_variator_assignments + assignment_ordinal

    identity = {
        key: row.get(key)
        for key in (
            "schema", "catalog_sha256", "judge_count", "split_protocol",
            "paraphrase_count", "seats",
        )
    }
    _validate_full_cross_catalog_digest(identity["catalog_sha256"])
    if row.get("case_id") != _sha256_id(identity):
        raise MatrixRefusal("FULL_CROSS_CASE_ID_MISMATCH")
    if "ordinal" in row and row["ordinal"] != ordinal:
        raise MatrixRefusal("FULL_CROSS_CASE_ORDINAL_MISMATCH")
    return ordinal


def iter_full_cross_cases(
    domain: Mapping[str, Any],
    model_ids: Iterable[str],
    *,
    catalog_sha256: str,
    criticism_authority: str | None,
    start_ordinal: int = 0,
    stop_ordinal: int | None = None,
) -> Iterator[dict[str, Any]]:
    """Lazily enumerate exactly the requested ordinal interval via direct lookup."""
    _validate_full_cross_domain(domain)
    _require_full_cross_authority(domain, criticism_authority)
    models = list(model_ids)
    accepted_count = len(_full_cross_models(models))
    total = full_cross_counts(domain, model_count=accepted_count)["total"]
    stop = total if stop_ordinal is None else stop_ordinal
    for name, value in (("start_ordinal", start_ordinal), ("stop_ordinal", stop)):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= total:
            raise MatrixRefusal("FULL_CROSS_ORDINAL_OUT_OF_RANGE", name)
    if stop < start_ordinal:
        raise MatrixRefusal("FULL_CROSS_ORDINAL_RANGE_INVALID")
    for ordinal in range(start_ordinal, stop):
        yield full_cross_case_at(
            domain,
            models,
            ordinal,
            catalog_sha256=catalog_sha256,
            criticism_authority=criticism_authority,
        )
def normalize_model_id(model_id: str) -> str:
    if not isinstance(model_id, str):
        raise MatrixRefusal("MODEL_ID_NOT_STRING")
    folded = unicodedata.normalize("NFKC", model_id).casefold()
    return re.sub(r"[^a-z0-9]", "", folded)
def _ordered_raw_ids(model_ids: Iterable[str]) -> list[str]:
    raw = list(model_ids)
    if any(not isinstance(item, str) or not item for item in raw):
        raise MatrixRefusal("MODEL_ID_INVALID")
    if len(set(raw)) != len(raw):
        raise MatrixRefusal("DUPLICATE_RAW_MODEL_ID")
    return sorted(raw, key=lambda item: item.encode("utf-8"))
def freeze_catalog(model_ids: Iterable[str]) -> dict[str, Any]:
    accepted: list[str] = []
    excluded: list[dict[str, str]] = []
    for model_id in _ordered_raw_ids(model_ids):
        if "kimik3" in normalize_model_id(model_id):
            excluded.append({"model_id": model_id, "code": "KIMI_K3_FORBIDDEN"})
        else:
            accepted.append(model_id)
    return {
        "model_ids": accepted,
        "excluded": excluded,
        "catalog_sha256": hashlib.sha256(canonical_json(accepted)).hexdigest(),
    }


def freeze_authenticated_catalog(response: Mapping[str, Any]) -> dict[str, Any]:
    """Freeze every authenticated catalog id except the typed Kimi-K3 ban."""
    if not isinstance(response, Mapping) or not isinstance(response.get("data"), list):
        raise MatrixRefusal("CATALOG_RESPONSE_INVALID", "data must be a list")
    model_ids: list[str] = []
    for index, entry in enumerate(response["data"]):
        if not isinstance(entry, Mapping) or set(entry).isdisjoint({"id"}):
            raise MatrixRefusal("CATALOG_RESPONSE_INVALID", f"data[{index}].id absent")
        model_ids.append(entry["id"])
    return freeze_catalog(model_ids)


@dataclass(frozen=True)
class LiveEndpointBinding:
    """One registered seat and its credential-bearing in-memory endpoint."""

    role: str
    model_profile: str
    endpoint: Any


class BoundedLiveEndpoint:
    """Keep an endpoint's whole retrying completion under the global ceiling."""

    def __init__(self, endpoint: Any) -> None:
        self._endpoint = endpoint

    def __getattr__(self, name: str) -> Any:
        return getattr(self._endpoint, name)

    def complete(self, *args: Any, **kwargs: Any) -> Any:
        secret = getattr(self._endpoint, "api_key", None)
        try:
            with _live_call_slot():
                result = self._endpoint.complete(*args, **kwargs)
        except Exception as error:
            if isinstance(secret, str) and secret and secret in str(error):
                raise MatrixRefusal(
                    "SECRET_BEARING_PROVIDER_RESPONSE_WITHHELD"
                ) from None
            raise
        trace = getattr(self._endpoint, "last_reasoning_trace", None)
        for value in (result, trace):
            if (
                isinstance(secret, str) and secret
                and isinstance(value, str) and secret in value
            ):
                raise MatrixRefusal(
                    "SECRET_BEARING_PROVIDER_RESPONSE_WITHHELD"
                )
        return result


class RecordedLiveEndpoint:
    """Record the exact logical seat dispatch before entering its call gate."""

    def __init__(self, endpoint: Any, label: str, history: list[str]) -> None:
        self._endpoint = endpoint
        self._label = label
        self._history = history

    def __getattr__(self, name: str) -> Any:
        return getattr(self._endpoint, name)

    def complete(self, *args: Any, **kwargs: Any) -> Any:
        self._history.append(self._label)
        return self._endpoint.complete(*args, **kwargs)


@contextlib.contextmanager
def _live_call_slot() -> Iterator[None]:
    """Account for one whole provider call under the campaign-wide ceiling."""
    with _CALL_SLOTS:
        with _CALL_COUNTER_LOCK:
            _CALL_COUNTER["active"] += 1
            _CALL_COUNTER["peak"] = max(
                _CALL_COUNTER["peak"], _CALL_COUNTER["active"]
            )
        try:
            yield
        finally:
            with _CALL_COUNTER_LOCK:
                _CALL_COUNTER["active"] -= 1


def live_call_counts(*, reset_peak: bool = False) -> dict[str, int]:
    """Return concurrency evidence without exposing endpoint or credential state."""
    with _CALL_COUNTER_LOCK:
        snapshot = dict(_CALL_COUNTER)
        if reset_peak:
            _CALL_COUNTER["peak"] = _CALL_COUNTER["active"]
    return snapshot


def _live_reasoning_value(reasoning: Any) -> str | int:
    if (
        not isinstance(reasoning, Mapping)
        or set(reasoning) != {"kind", "value"}
        or not any(reasoning == registered for registered in _FULL_CROSS_REASONING)
    ):
        raise MatrixRefusal("FORBIDDEN_REASONING_EFFORT")
    return reasoning["value"]


def build_live_endpoint(
    seat: Mapping[str, Any], *, criticism_authority: str | None,
    environ: Mapping[str, str] | None = None,
) -> LiveEndpointBinding:
    """Construct one exact Ollama seat after all pre-dispatch integrity checks."""
    from deepreason.llm.endpoints import OpenAICompatEndpoint
    from deepreason.run_manifest import infer_model_family

    if criticism_authority != "defended_trial":
        raise MatrixRefusal("LIVE_REQUIRES_DEFENDED_TRIAL")
    required = {
        "role", "model_id", "model_profile", "output_mode",
        "output_mechanism", "reasoning",
    }
    if not isinstance(seat, Mapping) or set(seat) != required:
        raise MatrixRefusal("LIVE_SEAT_INVALID")
    role = seat["role"]
    profile = seat["model_profile"]
    mode = seat["output_mode"]
    mechanism = seat["output_mechanism"]
    if not isinstance(role, str) or not role:
        raise MatrixRefusal("LIVE_SEAT_INVALID", "role")
    if profile not in {"compact", "standard", "frontier"}:
        raise MatrixRefusal("LIVE_SEAT_INVALID", "model_profile")
    if mode not in {"text", "json_object"}:
        raise MatrixRefusal("LIVE_SEAT_INVALID", "output_mode")
    if mechanism not in {"native_json_schema", "grammar", "json_text"}:
        raise MatrixRefusal("LIVE_SEAT_INVALID", "output_mechanism")
    reasoning = _live_reasoning_value(seat["reasoning"])
    body = build_provider_body(seat["model_id"], reasoning)
    source = os.environ if environ is None else environ
    secret = source.get("OLLAMA_API_KEY")
    if not isinstance(secret, str) or not secret:
        raise MatrixRefusal("OLLAMA_API_KEY_MISSING")
    endpoint = OpenAICompatEndpoint(
        "https://ollama.com/v1", body["model"], api_key=secret,
        timeout_s=300, max_tokens=8_192, json_mode=mode == "json_object",
        reasoning=reasoning, provider="ollama", output_mechanism=mechanism,
    )
    endpoint.endpoint_id = "https://ollama.com/v1"
    endpoint.family = infer_model_family(body["model"], "ollama")
    endpoint.model_revision = None
    endpoint.context_window_tokens = 131_072
    return LiveEndpointBinding(
        role=role, model_profile=profile, endpoint=BoundedLiveEndpoint(endpoint)
    )


_TRACE_KEYS = ("reasoning", "reasoning_content", "thinking")


def reasoning_probe_receipt(
    *, model_id: str, requested_reasoning: str, message: Mapping[str, Any],
    secret: str | None = None,
) -> dict[str, Any]:
    """Record probe structure and trace metadata without persisting trace text."""
    validate_provider_body({
        "model": model_id, "reasoning_effort": requested_reasoning,
    })
    if requested_reasoning not in {"none", "low", "medium"}:
        raise MatrixRefusal("PROBE_REASONING_NOT_REGISTERED")
    if not isinstance(message, Mapping):
        raise MatrixRefusal("PROBE_MESSAGE_INVALID")
    encoded_message = canonical_json(message)
    if secret and secret.encode("utf-8") in encoded_message:
        raise MatrixRefusal("SECRET_BEARING_PROVIDER_RESPONSE_WITHHELD")
    content = message.get("content")
    try:
        parsed = json.loads(content) if isinstance(content, str) else None
        parser_outcome = "valid" if isinstance(content, str) else "invalid"
    except (TypeError, ValueError):
        parsed, parser_outcome = None, "invalid"
    schema_outcome = (
        "valid" if parser_outcome == "valid" and parsed == {"ok": True}
        else "invalid" if parser_outcome == "valid" else "not_run"
    )
    traces: dict[str, dict[str, Any]] = {}
    for key in _TRACE_KEYS:
        value = message.get(key)
        present = key in message and value is not None
        encoded = (
            value.encode("utf-8") if isinstance(value, str)
            else canonical_json(value) if present else b""
        )
        traces[key] = {
            "present": present,
            "byte_count": len(encoded) if present else 0,
            "sha256": hashlib.sha256(encoded).hexdigest() if present else None,
        }
    return {
        "model_id": model_id,
        "requested_reasoning": requested_reasoning,
        "status": (
            "probe_usable" if parser_outcome == schema_outcome == "valid"
            else "provider_indeterminate"
        ),
        "message_keys": sorted(message, key=lambda key: str(key).encode("utf-8")),
        "parser_outcome": parser_outcome,
        "schema_outcome": schema_outcome,
        "trace_fields": traces,
    }
def _seat_case(catalog_sha256: str, critic: str, defender: str, judge0: str,
               judge1: str, variator: str | None, prefix: str) -> dict[str, Any]:
    fields = {"schema": SEAT_SCHEMA, "catalog_sha256": catalog_sha256,
              "critic": critic, "defender": defender, "judge0": judge0,
              "judge1": judge1, "variator": variator}
    return {**fields, "case_id": _sha256_id(fields), "prefix": prefix}
def iter_seat_cases(model_ids: Iterable[str], *, catalog_sha256: str
                    ) -> Iterator[dict[str, Any]]:
    models = freeze_catalog(model_ids)["model_ids"]
    if not models:
        raise MatrixRefusal("EMPTY_MODEL_CATALOG")
    anchor = models[0]
    seen: set[str] = set()
    plans = (
        ("judge_pairs", ((anchor, anchor, j0, j1, None) for j0, j1 in itertools.product(models, repeat=2))),
        ("core_courts", ((anchor, d, j0, j1, None) for d, j0, j1 in itertools.product(models, repeat=3))),
        ("no_variator", ((*parts, None) for parts in itertools.product(models, repeat=4))),
        ("with_variator", itertools.product(models, repeat=5)),
    )
    for prefix, assignments in plans:
        for assignment in assignments:
            row = _seat_case(catalog_sha256, *assignment, prefix)
            if prefix == "with_variator":
                yield row
                continue
            if row["case_id"] not in seen:
                seen.add(row["case_id"])
                yield row
def structural_case_ids(domain: Mapping[str, Any]) -> list[str]:
    case_ids: list[str] = []
    for group in domain["structural_domains"]:
        assignments: Iterable[Any]
        if group["combination"] == "cartesian":
            axes = group["axes"]
            keys = list(axes)
            assignments = (
                dict(zip(keys, values))
                for values in itertools.product(*(axes[key] for key in keys))
            )
        elif group["combination"] == "enumerated_cases":
            assignments = (
                value if isinstance(value, dict) else {"case": value}
                for value in group["cases"]
            )
        else:
            raise MatrixRefusal("STRUCTURAL_COMBINATION_UNSUPPORTED", group["name"])
        before = len(case_ids)
        for assignment in assignments:
            case_ids.append(_sha256_id({"schema": STRUCTURAL_SCHEMA,
                                        "group": group["name"],
                                        "assignment": assignment}))
        if len(case_ids) - before != group["expected_count"]:
            raise MatrixRefusal("STRUCTURAL_COUNT_MISMATCH", group["name"])
    return case_ids
def length_prefixed_set_digest(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values, key=lambda item: item.encode("utf-8")):
        encoded = value.encode("utf-8")
        digest.update(struct.pack(">I", len(encoded)))
        digest.update(encoded)
    return digest.hexdigest()
def validate_provider_body(body: Mapping[str, Any]) -> None:
    model_id = body.get("model")
    if not isinstance(model_id, str) or not model_id:
        raise MatrixRefusal("MODEL_ID_INVALID")
    if "kimik3" in normalize_model_id(model_id):
        raise MatrixRefusal("KIMI_K3_FORBIDDEN")
    if "reasoning_effort" not in body or body["reasoning_effort"] is None:
        raise MatrixRefusal("REASONING_EFFORT_REQUIRED")
    effort = body["reasoning_effort"]
    if isinstance(effort, str) and effort.strip().casefold() in FORBIDDEN_REASONING:
        raise MatrixRefusal("FORBIDDEN_REASONING_EFFORT")
    if isinstance(effort, int) and not isinstance(effort, bool) and effort > 2_000:
        raise MatrixRefusal("FORBIDDEN_REASONING_EFFORT")
def build_provider_body(model_id: str, reasoning: str | int | None) -> dict[str, Any]:
    if reasoning is None:
        raise MatrixRefusal("REASONING_EFFORT_REQUIRED")
    if isinstance(reasoning, bool) or not isinstance(reasoning, (str, int)):
        raise MatrixRefusal("REASONING_EFFORT_INVALID")
    if isinstance(reasoning, int):
        effort = "low" if reasoning <= 2_000 else "high"
    else:
        effort = reasoning
    body = {"model": model_id, "reasoning_effort": effort}
    validate_provider_body(body)
    return body
def guarded_complete(config_authority: str, manifest: Mapping[str, Any],
                     body: Mapping[str, Any],
                     complete: Callable[[Mapping[str, Any]], Any]) -> Any:
    contracts = manifest.get("trial_contracts")
    required = ("defender[0]", "judge[0]", "judge[1]")
    authorized = (
        config_authority == "defended_trial"
        and manifest.get("authority") == "defended_trial"
        and isinstance(contracts, Mapping)
        and all(contracts.get(seat) for seat in required)
    )
    if not authorized:
        raise MatrixRefusal("DEFENDED_TRIAL_NOT_AUTHORIZED")
    validate_provider_body(body)
    with _live_call_slot():
        return complete(body)
def run_bounded(tasks: Sequence[Callable[[], Any]], *, workers: int = 3) -> list[Any]:
    worker_count = min(3, max(1, workers))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        return list(pool.map(lambda task: task(), tasks))
@contextlib.contextmanager
def coordinator_lock(path: str | os.PathLike[str]) -> Iterator[None]:
    lock_path = Path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise MatrixRefusal("COORDINATOR_ALREADY_RUNNING") from exc
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
def safe_result_bytes(result: Mapping[str, Any], *, secret: str | None = None) -> bytes:
    safe = {field: result[field] for field in RESULT_FIELDS if field in result}
    proposed = canonical_json(safe)
    if secret and secret.encode("utf-8") in proposed:
        proposed = canonical_json({"case_id": str(result.get("case_id", "withheld")),
            "status": "unexpected_error", "code": "SECRET_BEARING_DIAGNOSTIC_WITHHELD",
            "message": "Diagnostic withheld because it contained credential bytes."})
    return proposed


_LIVE_RESULT_FIELDS = (
    "case_id", "ordinal", "status", "catalog_sha256", "domain_sha256",
    "branch_commit", "case_payload", "criticism_authority",
    "request_body_sha256", "dispatch_extent", "outcome_code",
    "variator_reachability", "full_dispatch_reached",
)
_BOUNDARY_FIELDS = ("stage", "exception_type", "code", "pointer", "message")
_RESPONSE_METADATA_FIELDS = (
    "message_keys", "parser_outcome", "schema_outcome", "fallback_events",
    "finish_reason", "usage",
)
_LIVE_SUBRESULT_FIELDS = (
    "status", "dispatch_extent", "outcome_code", "parser_outcome",
    "schema_outcome",
)


def _safe_response_metadata(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    safe = {
        field: value[field]
        for field in _RESPONSE_METADATA_FIELDS
        if field in value
    }
    traces = value.get("trace_fields")
    if isinstance(traces, Mapping):
        safe["trace_fields"] = {
            key: {
                field: metadata[field]
                for field in ("present", "byte_count", "sha256")
                if field in metadata
            }
            for key, metadata in traces.items()
            if key in _TRACE_KEYS and isinstance(metadata, Mapping)
        }
    return safe


def _safe_live_subresult(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    safe = {
        field: value[field] for field in _LIVE_SUBRESULT_FIELDS if field in value
    }
    boundary = value.get("first_boundary")
    if isinstance(boundary, Mapping):
        safe["first_boundary"] = {
            field: boundary[field]
            for field in _BOUNDARY_FIELDS
            if field in boundary
        }
    return safe


def safe_live_result_bytes(
    result: Mapping[str, Any], *, secret: str | None = None
) -> bytes:
    """Serialize only registered live evidence and scan the proposed bytes."""
    if not isinstance(result, Mapping):
        raise MatrixRefusal("LIVE_RESULT_INVALID")
    safe = {
        field: result[field]
        for field in _LIVE_RESULT_FIELDS
        if field in result
    }
    boundary = result.get("first_boundary")
    if isinstance(boundary, Mapping):
        safe["first_boundary"] = {
            field: boundary[field] for field in _BOUNDARY_FIELDS if field in boundary
        }
    response_metadata = _safe_response_metadata(result.get("response_metadata"))
    if response_metadata is not None:
        safe["response_metadata"] = response_metadata
    for field in ("critic_compatibility", "fixed_case_court_reachability"):
        subresult = _safe_live_subresult(result.get(field))
        if subresult is not None:
            safe[field] = subresult
    proposed = canonical_json(safe)
    if secret and secret.encode("utf-8") in proposed:
        proposed = canonical_json({
            "case_id": str(result.get("case_id", "withheld")),
            "ordinal": result.get("ordinal"),
            "status": "unexpected_error",
            "code": "SECRET_BEARING_DIAGNOSTIC_WITHHELD",
            "message": "Diagnostic withheld because it contained credential bytes.",
        })
    return proposed


def classify_live_result(
    *, error: Exception | None = None, outcome_code: str | None = None,
    stage: str, dispatch_extent: Sequence[str],
    provider_dependent: bool = False,
) -> dict[str, Any]:
    """Keep the first shipped or provider boundary as a typed terminal fact."""
    if (error is None) == (outcome_code is None):
        raise MatrixRefusal("LIVE_RESULT_CLASSIFICATION_INVALID")
    extent = list(dispatch_extent)
    if error is None:
        return {
            "status": "trial_outcome", "outcome_code": outcome_code,
            "dispatch_extent": extent, "first_boundary": None,
        }
    boundary = {
        "stage": stage,
        "exception_type": type(error).__name__,
        "code": getattr(error, "code", type(error).__name__),
        "pointer": getattr(error, "pointer", None),
        "message": str(error),
    }
    return {
        "status": (
            "provider_indeterminate" if provider_dependent
            else "configuration_refused"
        ),
        "dispatch_extent": extent,
        "first_boundary": boundary,
    }


def _require_hex(value: Any, length: int, code: str) -> str:
    if not isinstance(value, str) or re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is None:
        raise MatrixRefusal(code)
    return value


def build_live_case_receipt(
    row: Mapping[str, Any], *, domain_sha256: str, branch_commit: str,
    request_body: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind one terminal subject to exact identity and a non-reversible body digest."""
    if not isinstance(row, Mapping) or row.get("schema") != FULL_CROSS_CASE_SCHEMA:
        raise MatrixRefusal("FULL_CROSS_CASE_SCHEMA_UNSUPPORTED")
    if row.get("criticism_authority") != "defended_trial":
        raise MatrixRefusal("LIVE_REQUIRES_DEFENDED_TRIAL")
    identity_keys = (
        "schema", "catalog_sha256", "judge_count", "split_protocol",
        "paraphrase_count", "seats",
    )
    if any(key not in row for key in identity_keys):
        raise MatrixRefusal("FULL_CROSS_CASE_INVALID")
    identity = {key: row[key] for key in identity_keys}
    if row.get("case_id") != _sha256_id(identity):
        raise MatrixRefusal("FULL_CROSS_CASE_ID_MISMATCH")
    ordinal = row.get("ordinal")
    if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
        raise MatrixRefusal("FULL_CROSS_CASE_ORDINAL_OUT_OF_RANGE")
    _validate_full_cross_catalog_digest(row.get("catalog_sha256"))
    _require_hex(domain_sha256, 64, "FULL_CROSS_DOMAIN_DIGEST_INVALID")
    _require_hex(branch_commit, 40, "BRANCH_COMMIT_INVALID")
    if not isinstance(request_body, Mapping):
        raise MatrixRefusal("LIVE_REQUEST_BODY_INVALID")
    validate_provider_body(request_body)
    return {
        "case_id": row["case_id"],
        "ordinal": ordinal,
        "case_payload": identity,
        "catalog_sha256": row["catalog_sha256"],
        "domain_sha256": domain_sha256,
        "branch_commit": branch_commit,
        "request_body_sha256": hashlib.sha256(canonical_json(request_body)).hexdigest(),
        "criticism_authority": "defended_trial",
    }


def next_pending_full_cross_case(
    domain: Mapping[str, Any], model_ids: Iterable[str], *,
    terminal_receipts: Iterable[Mapping[str, Any]], start_ordinal: int,
    catalog_sha256: str, criticism_authority: str | None,
) -> dict[str, Any] | None:
    """Validate immutable receipts and directly return the first ordinal gap."""
    axes = _validate_full_cross_domain(domain)
    _require_full_cross_authority(domain, criticism_authority)
    models = _full_cross_models(model_ids)
    total = full_cross_counts(domain, model_count=len(models))["total"]
    if (
        isinstance(start_ordinal, bool) or not isinstance(start_ordinal, int)
        or not 0 <= start_ordinal <= total
    ):
        raise MatrixRefusal("FULL_CROSS_ORDINAL_OUT_OF_RANGE")
    seen: set[int] = set()
    for receipt in terminal_receipts:
        if not isinstance(receipt, Mapping):
            raise MatrixRefusal("FULL_CROSS_RECEIPT_INVALID")
        ordinal = receipt.get("ordinal")
        if (
            isinstance(ordinal, bool) or not isinstance(ordinal, int)
            or not 0 <= ordinal < total
        ):
            raise MatrixRefusal("FULL_CROSS_RECEIPT_ORDINAL_INVALID")
        if ordinal in seen:
            raise MatrixRefusal("FULL_CROSS_RECEIPT_DUPLICATE")
        expected = full_cross_case_at(
            domain, models, ordinal, catalog_sha256=catalog_sha256,
            criticism_authority=criticism_authority,
        )
        if receipt.get("case_id") != expected["case_id"]:
            raise MatrixRefusal("FULL_CROSS_RECEIPT_ID_MISMATCH")
        seen.add(ordinal)
    ordinal = start_ordinal
    while ordinal in seen:
        ordinal += 1
    if ordinal == total:
        return None
    return full_cross_case_at(
        domain, models, ordinal, catalog_sha256=catalog_sha256,
        criticism_authority=criticism_authority,
    )
def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temp_path.unlink(missing_ok=True)
def atomic_terminal_write(path: str | os.PathLike[str], result: Mapping[str, Any],
                          *, secret: str | None = None) -> None:
    target = Path(path)
    if target.exists():
        raise MatrixRefusal("TERMINAL_RESULT_IMMUTABLE")
    _atomic_bytes(target, safe_result_bytes(result, secret=secret))
def prepare_attempt(root: str | os.PathLike[str], *, domain_sha256: str,
                    catalog_sha256: str) -> Path:
    attempt_root = Path(root)
    attempt_root.mkdir(parents=True, exist_ok=True)
    binding_path = attempt_root / "binding.json"
    binding = {"domain_sha256": domain_sha256, "catalog_sha256": catalog_sha256}
    if binding_path.exists():
        previous = json.loads(binding_path.read_text(encoding="utf-8"))
        if previous.get("domain_sha256") != domain_sha256:
            raise MatrixRefusal("DOMAIN_DIGEST_MISMATCH")
        if previous.get("catalog_sha256") != catalog_sha256:
            raise MatrixRefusal("CATALOG_DIGEST_MISMATCH")
    else:
        _atomic_bytes(binding_path, canonical_json(binding))
    attempts = sorted(
        (path for path in attempt_root.glob("attempt-[0-9][0-9][0-9][0-9]") if path.is_dir()),
        key=lambda path: path.name,
    )
    if attempts and not (attempts[-1] / "INTERRUPTED.json").exists():
        raise MatrixRefusal("ATTEMPT_ALREADY_ACTIVE")
    next_path = attempt_root / f"attempt-{len(attempts) + 1:04d}"
    next_path.mkdir()
    _atomic_bytes(next_path / "attempt.json", canonical_json({**binding, "status": "active"}))
    return next_path
def mark_interrupted(attempt: str | os.PathLike[str]) -> None:
    atomic_terminal_write(
        Path(attempt) / "INTERRUPTED.json",
        {"status": "interrupted", "message": "Attempt retained unchanged; resume rotates."},
    )


_COURT_STAMP = "2026-09-01T00:00:00Z"
_COURT_CASE = "The proposal omits the boundary condition required by its own mechanism."
_COURT_DEFENCE = "The boundary condition is enforced by the mechanism."
_COURT_POINT = "boundary condition"
_BASELINE_PROFILE = "standard"
_BASELINE_OUTPUT_MODE = "json_object"
_BASELINE_OUTPUT_MECHANISM = "json_text"
_BASELINE_REASONING = {"kind": "string", "value": "low"}


def _baseline_live_seats(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    identity_keys = (
        "schema", "catalog_sha256", "critic", "defender", "judge0",
        "judge1", "variator",
    )
    if not isinstance(row, Mapping) or row.get("schema") != SEAT_SCHEMA:
        raise MatrixRefusal("SEAT_CASE_SCHEMA_UNSUPPORTED")
    identity = {key: row.get(key) for key in identity_keys}
    if row.get("case_id") != _sha256_id(identity):
        raise MatrixRefusal("SEAT_CASE_ID_MISMATCH")
    _validate_full_cross_catalog_digest(row.get("catalog_sha256"))
    assignments = [
        ("critic", row.get("critic")),
        ("defender", row.get("defender")),
        ("judge:0", row.get("judge0")),
        ("judge:1", row.get("judge1")),
    ]
    if row.get("variator") is not None:
        assignments.append(("variator", row["variator"]))
    seats = []
    for role, model_id in assignments:
        validate_provider_body({"model": model_id, "reasoning_effort": "low"})
        seats.append({
            "role": role,
            "model_id": model_id,
            "model_profile": _BASELINE_PROFILE,
            "output_mode": _BASELINE_OUTPUT_MODE,
            "output_mechanism": _BASELINE_OUTPUT_MECHANISM,
            "reasoning": dict(_BASELINE_REASONING),
        })
    return seats


def _live_endpoint_id(role: str) -> str:
    return "ollama-" + role.replace(":", "-")


def _live_route_spec(seat: Mapping[str, Any], endpoint_id: str) -> dict[str, Any]:
    from deepreason.run_manifest import infer_model_family

    reasoning = _live_reasoning_value(seat["reasoning"])
    validate_provider_body({
        "model": seat["model_id"], "reasoning_effort": reasoning,
    })
    return {
        "endpoint_id": endpoint_id,
        "endpoint": "https://ollama.com/v1",
        "model": seat["model_id"],
        "provider": "ollama",
        "family": infer_model_family(seat["model_id"], "ollama"),
        "model_profile": seat["model_profile"],
        "reasoning": reasoning,
        "max_tokens": 8_192,
        "context_window_tokens": 131_072,
        "output_mode": seat["output_mode"],
        "output_mechanism": seat["output_mechanism"],
        "timeout_s": 300,
        "api_key_env": "OLLAMA_API_KEY",
    }


def compile_live_court(
    seats: Sequence[Mapping[str, Any]], *, split_protocol: str,
    paraphrase_count: int | None, run_input_digest: str,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Compile exact live seats and construct their in-memory endpoints."""
    from deepreason.config import Config
    from deepreason.v6_policy import (
        conservative_control_plane_policy_v3,
        engaged_criticism_policy,
    )

    source = os.environ if environ is None else environ
    if split_protocol not in {"auto", "on", "off"}:
        raise MatrixRefusal("LIVE_SPLIT_PROTOCOL_INVALID")
    _require_hex(run_input_digest, 64, "LIVE_INPUT_DIGEST_INVALID")
    labels = [seat.get("role") for seat in seats]
    judge_count = sum(
        isinstance(label, str) and label.startswith("judge:") for label in labels
    )
    expected = _full_cross_roles(judge_count, "variator" in labels)
    if labels != expected or judge_count not in {2, 3}:
        raise MatrixRefusal("LIVE_SEAT_ORDER_INVALID")

    route_specs: dict[str, list[dict[str, Any]]] = {}
    live_endpoints: dict[str, list[tuple[str, Any]]] = {}
    for seat in seats:
        label = seat["role"]
        role = "argumentative_critic" if label == "critic" else (
            "judge" if label.startswith("judge:") else label
        )
        endpoint_id = _live_endpoint_id(label)
        spec = _live_route_spec(seat, endpoint_id)
        route_specs.setdefault(role, []).append(spec)
        binding = build_live_endpoint(
            seat, criticism_authority="defended_trial", environ=source,
        )
        binding.endpoint.endpoint_id = endpoint_id
        live_endpoints.setdefault(role, []).append((label, binding.endpoint))

    critic_spec = route_specs["argumentative_critic"][0]
    conjecturer_spec = {
        **critic_spec,
        "endpoint_id": _live_endpoint_id("conjecturer"),
    }
    config_roles = {"conjecturer": [conjecturer_spec], **route_specs}
    config = Config(
        N_SCHOOLS=2,
        RETRY_MAX=0,
        VS_K=1,
        FUZZ_N=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        RECRIT_STANDING=False,
        NEAR_DUP_EPS=None,
        TRIAL_PARAPHRASE_N=(2 if paraphrase_count is None else paraphrase_count),
        SPLIT_BUDGET_SEAT_PROTOCOL=split_protocol,
        ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ENGAGED_CRITICISM_AUTHORITY="defended_trial",
        LEGACY_CRITICISM_ENABLED=False,
        JUDGE_SEATS_ENABLED=True,
        model_profile="standard",
        roles=config_roles,
    )
    policy = engaged_criticism_policy(
        critic_spec["endpoint_id"],
        authority="defended_trial",
        school_count=config.N_SCHOOLS,
    )
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=_COURT_STAMP,
        control_plane_policy=conservative_control_plane_policy_v3(),
        criticism_policy=policy,
        run_input_digest=run_input_digest,
    )
    if (
        config.ENGAGED_CRITICISM_AUTHORITY != "defended_trial"
        or manifest.criticism_policy is None
        or manifest.criticism_policy.authority != "defended_trial"
    ):
        raise MatrixRefusal("LIVE_REQUIRES_DEFENDED_TRIAL")
    grants = {
        (entry.role, entry.seat): tuple(entry.contracts)
        for entry in manifest.route_seat_behavioral_capability_plan.entries
    }
    required = [
        ("defender", 0),
        *(("judge", index) for index in range(judge_count)),
    ]
    if "variator" in route_specs:
        required.append(("variator", 0))
    if any(not grants.get(key) for key in required):
        raise MatrixRefusal("DEFENDED_TRIAL_NOT_AUTHORIZED")
    return {
        "config": config,
        "manifest": manifest,
        "live_endpoints": live_endpoints,
    }


def _baseline_live_case_receipt(
    row: Mapping[str, Any], *, domain_sha256: str, branch_commit: str,
) -> dict[str, Any]:
    seats = _baseline_live_seats(row)
    _require_hex(domain_sha256, 64, "MATRIX_DOMAIN_DIGEST_INVALID")
    _require_hex(branch_commit, 40, "BRANCH_COMMIT_INVALID")
    identity_keys = (
        "schema", "catalog_sha256", "critic", "defender", "judge0",
        "judge1", "variator",
    )
    request_definition = {
        seat["role"]: {
            **build_provider_body(seat["model_id"], "low"),
            "model_profile": seat["model_profile"],
            "output_mode": seat["output_mode"],
            "output_mechanism": seat["output_mechanism"],
            "split_protocol": "off",
            "max_tokens": 8_192,
            "context_window_tokens": 131_072,
            "timeout_s": 300,
        }
        for seat in seats
    }
    return {
        "case_id": row["case_id"],
        "case_payload": {key: row.get(key) for key in identity_keys},
        "catalog_sha256": row["catalog_sha256"],
        "domain_sha256": domain_sha256,
        "branch_commit": branch_commit,
        "request_body_sha256": hashlib.sha256(
            canonical_json(request_definition)
        ).hexdigest(),
        "criticism_authority": "defended_trial",
    }


def _recorded_live_endpoint_table(
    live_endpoints: Mapping[str, Sequence[tuple[str, Any]]],
    history: list[str],
) -> dict[str, Any]:
    table: dict[str, Any] = {}
    for role, entries in live_endpoints.items():
        recorded = [
            RecordedLiveEndpoint(endpoint, label, history)
            for label, endpoint in entries
        ]
        table[role] = recorded if len(recorded) > 1 else recorded[0]
    return table


def _ensure_exception_is_secret_free(error: Exception, secret: str) -> None:
    if secret and secret in str(error):
        raise MatrixRefusal("SECRET_BEARING_DIAGNOSTIC_WITHHELD") from None


def _critic_compatibility(
    harness: Any, endpoint: Any, *, model_profile: str,
    history: list[str], secret: str,
) -> dict[str, Any]:
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.budget import TokenMeter
    from deepreason.llm.contracts import ArgumentativeCriticOutput

    start = len(history)
    adapter = LLMAdapter(
        {"argumentative_critic": endpoint},
        harness.blobs,
        retry_max=0,
        model_profile=model_profile,
        meter=TokenMeter(None),
    )
    try:
        adapter.call(
            "argumentative_critic",
            "TARGET:\nA mechanism whose validity depends on an explicit "
            "boundary condition. State whether the proposed omission is an "
            "attack and give the case.",
            ArgumentativeCriticOutput,
        )
    except Exception as error:
        _ensure_exception_is_secret_free(error, secret)
        return classify_live_result(
            error=error,
            stage="critic",
            dispatch_extent=history[start:],
            provider_dependent=len(history) > start,
        )
    return {
        "status": "mechanically_compatible",
        "dispatch_extent": history[start:],
        "parser_outcome": "valid",
        "schema_outcome": "valid",
        "first_boundary": None,
    }


def run_live_seat_case(
    row: Mapping[str, Any], home: str | os.PathLike[str], *, secret: str,
    domain_sha256: str, branch_commit: str,
) -> dict[str, Any]:
    """Run one baseline fixed-case court without letting critic prose gate it."""
    from deepreason.harness import Harness
    from deepreason.informal.trial import run_argument_trial_from_case
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.budget import TokenMeter
    from deepreason.llm.firewall import leases_from_manifest
    from deepreason.ontology import Problem, ProblemProvenance, Provenance

    receipt = _baseline_live_case_receipt(
        row, domain_sha256=domain_sha256, branch_commit=branch_commit,
    )
    seats = _baseline_live_seats(row)
    root = Path(home)
    if root.exists():
        raise MatrixRefusal("LIVE_CASE_HOME_NOT_FRESH")
    built = compile_live_court(
        seats,
        split_protocol="off",
        paraphrase_count=(2 if row.get("variator") is not None else None),
        run_input_digest=row["case_id"].split(":", 1)[1],
        environ={"OLLAMA_API_KEY": secret},
    )
    config, manifest = built["config"], built["manifest"]
    root.mkdir(parents=True)
    harness = Harness(root / "run")
    _bind_court_classification(harness, manifest)
    harness.register_problem(Problem(
        id="pi-live-full-judge-court",
        description="exercise one live defended court",
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    target = harness.create_artifact(
        "A mechanism whose validity depends on an explicit boundary condition.",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    history: list[str] = []
    endpoints = _recorded_live_endpoint_table(built["live_endpoints"], history)
    critic_profile = next(
        seat["model_profile"] for seat in seats if seat["role"] == "critic"
    )
    critic = _critic_compatibility(
        harness,
        endpoints["argumentative_critic"],
        model_profile=critic_profile,
        history=history,
        secret=secret,
    )
    adapter = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=config.RETRY_MAX,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
        split_budget_mode=config.SPLIT_BUDGET_SEAT_PROTOCOL,
        split_extraction_tokens=config.SPLIT_BUDGET_EXTRACTION_TOKENS,
        meter=TokenMeter(None),
    )
    trial_start = len(history)
    try:
        adapter.bind_v6_authority(harness, manifest)
        diagnostics: list[dict[str, Any]] = []
        run_argument_trial_from_case(
            harness,
            adapter,
            config,
            target.id,
            _COURT_CASE,
            authority="status",
            critic_school_id="school-1",
            diagnostics=diagnostics,
        )
        fixed = classify_live_result(
            outcome_code=_court_outcome(harness, target.id),
            stage="trial",
            dispatch_extent=history[trial_start:],
        )
    except Exception as error:
        if isinstance(error, MatrixRefusal) and error.code.startswith("SECRET_BEARING_"):
            raise
        _ensure_exception_is_secret_free(error, secret)
        fixed = classify_live_result(
            error=error,
            stage=(history[-1] if len(history) > trial_start else "trial_preflight"),
            dispatch_extent=history[trial_start:],
            provider_dependent=len(history) > trial_start,
        )
    required = ["critic", "defender", "judge:0", "judge:1"]
    if row.get("variator") is not None:
        required.append("variator")
    result = {
        **receipt,
        **fixed,
        "dispatch_extent": list(history),
        "critic_compatibility": critic,
        "fixed_case_court_reachability": fixed,
        "full_dispatch_reached": all(stage in history for stage in required),
        "variator_reachability": (
            "not_configured" if row.get("variator") is None
            else "exercised" if "variator" in history
            else "not_exercised_by_outcome"
        ),
    }
    return result


def _court_route(endpoint_id: str, role: str, seat: int = 0) -> dict[str, Any]:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": f"offline-{role}-{seat}",
        "provider": "mock",
        "family": f"offline-{role}-{seat}",
        "max_tokens": 256,
        "context_window_tokens": 262_144,
    }


def compile_stubbed_court(*, judge_count: int,
                          with_variator: bool = False,
                          paraphrase_count: int = 2) -> dict[str, Any]:
    """Compile one explicit defended court through the shipped v6 compiler."""
    from deepreason.config import Config
    from deepreason.v6_policy import (
        conservative_control_plane_policy_v3,
        engaged_criticism_policy,
    )

    if isinstance(judge_count, bool) or judge_count < 1:
        raise MatrixRefusal("JUDGE_COUNT_INVALID")
    roles: dict[str, Any] = {
        "conjecturer": [_court_route("court-conjecturer", "conjecturer")],
        "argumentative_critic": [_court_route("court-critic", "critic")],
        "defender": [_court_route("court-defender", "defender")],
        "judge": [
            _court_route(f"court-judge-{seat}", "judge", seat)
            for seat in range(judge_count)
        ],
    }
    if with_variator:
        roles["variator"] = [_court_route("court-variator", "variator")]
    config = Config(
        N_SCHOOLS=2,
        RETRY_MAX=0,
        VS_K=1,
        FUZZ_N=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        RECRIT_STANDING=False,
        NEAR_DUP_EPS=None,
        TRIAL_PARAPHRASE_N=paraphrase_count,
        ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ENGAGED_CRITICISM_AUTHORITY="defended_trial",
        LEGACY_CRITICISM_ENABLED=False,
        JUDGE_SEATS_ENABLED=True,
        roles=roles,
    )
    policy = engaged_criticism_policy(
        "court-critic", authority="defended_trial", school_count=config.N_SCHOOLS
    )
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=_COURT_STAMP,
        control_plane_policy=conservative_control_plane_policy_v3(),
        criticism_policy=policy,
        run_input_digest="f" * 64,
    )
    return {"config": config, "manifest": manifest}


def _managed_profile(*, distinct: bool = False):
    from deepreason.provider_profile import ProviderProfileV1

    suffix = "distinct" if distinct else "baseline"
    return ProviderProfileV1.create(
        provider="openai",
        endpoint=f"https://{suffix}.example.test/v1",
        model_id=f"managed-{suffix}",
        model_revision="fixture-1",
        family=f"managed-family-{suffix}",
        context_window_tokens=131_072,
        maximum_completion_tokens=4_096,
        credential_env=f"DEEPREASON_MANAGED_{suffix.upper()}_TEST_KEY",
    )


def classify_managed_path(*, diverse_nonjudge: bool) -> dict[str, Any]:
    """Exercise and report the managed builder's first shipped trial boundary.

    The attack is obtained through a real adapter call owned by this
    compatibility fixture.  The shipped managed manifest is then bound and
    exercised from that precomputed case, matching the production hand-off
    between criticism and ``run_argument_trial_from_case``.
    """
    from deepreason.config import Config
    from deepreason.harness import Harness
    from deepreason.informal.trial import run_argument_trial_from_case
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.contracts import ArgumentativeCriticOutput
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.llm.firewall import JudgeEnsemblePolicyError, leases_from_manifest
    from deepreason.ontology import Provenance
    from deepreason.preparation import build_preparation_manifest

    base = _managed_profile()
    config = Config(
        ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ENGAGED_CRITICISM_AUTHORITY="defended_trial",
        LEGACY_CRITICISM_ENABLED=False,
        JUDGE_SEATS_ENABLED=True,
    )
    bindings = {"conjecturer": _managed_profile(distinct=True)} if diverse_nonjudge else None
    manifest = build_preparation_manifest(
        base,
        question="Where does the managed defended court first stop?",
        compiled_at=_COURT_STAMP,
        config=config,
        seat_bindings=bindings,
    )
    with tempfile.TemporaryDirectory(prefix="deepreason-managed-court-") as directory:
        harness = Harness(Path(directory) / "run")
        target = harness.create_artifact(
            "A mechanism with an explicit boundary.",
            provenance=Provenance(role="conjecturer", school="school-0"),
        )
        dispatch_history: list[str] = []
        critic_route = manifest.roles["argumentative_critic"][0]
        critic_endpoint = MockEndpoint(
            lambda _prompt: (
                dispatch_history.append("critic")
                or json.dumps({"attack": True, "case": _COURT_CASE})
            ),
            name=critic_route.base_url, model=critic_route.model_id,
            max_tokens=critic_route.max_tokens,
        )
        critic_output, _critic_call = LLMAdapter(
            {"argumentative_critic": critic_endpoint}, harness.blobs, retry_max=0,
        ).call("argumentative_critic", "TARGET:\nA mechanism with an explicit boundary.",
               ArgumentativeCriticOutput)
        route = manifest.roles["judge"][0]
        defender_route = manifest.roles["defender"][0]
        adapter = LLMAdapter(
            {
                "defender": MockEndpoint(
                    lambda _prompt: json.dumps({"answer": _COURT_DEFENCE}),
                    name=defender_route.base_url, model=defender_route.model_id,
                    max_tokens=defender_route.max_tokens,
                ),
                "judge": MockEndpoint(
                    lambda _prompt: json.dumps({
                        "verdict": "fail", "decisive_point": "boundary"
                    }),
                    name=route.base_url, model=route.model_id, max_tokens=route.max_tokens,
                ),
            },
            harness.blobs,
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
            transaction_authority_required=True,
        )
        _bind_court_classification(harness, manifest)
        adapter.bind_v6_authority(harness, manifest)
        diagnostics: list[dict[str, Any]] = []
        try:
            run_argument_trial_from_case(
                harness, adapter, config, target.id, critic_output.case,
                authority="status", critic_school_id="school-1",
                diagnostics=diagnostics,
            )
            code = diagnostics[-1]["declined"]
        except JudgeEnsemblePolicyError as error:
            code = error.code
    return {
        "construction": "managed_preparation",
        "status": "configuration_refused",
        "stage": "trial_preflight",
        "code": code,
        "dispatch_history": dispatch_history,
    }


def _bind_court_classification(harness, manifest) -> None:
    from deepreason.cli.doctor import ProductionContractCaseResultV1, run_production_contract_doctor

    def admitted(_manifest, _pair, index):
        return ProductionContractCaseResultV1(
            case_id=f"case-{index + 1:03d}", first_pass_valid=True,
            eventual_valid=True, repair_count=0, semantic_admission=True,
        )

    harness.bind_model_classification(
        manifest, run_production_contract_doctor(manifest, case_executor=admitted)
    )


def _court_endpoint(route, calls: list[str], label: Callable[[int], str], response: str):
    from deepreason.llm.endpoints import MockEndpoint

    count = 0
    def respond(_prompt: str) -> str:
        nonlocal count
        calls.append(label(count))
        count += 1
        return response
    return MockEndpoint(
        respond, name=route.base_url, model=route.model_id, max_tokens=route.max_tokens
    )


def _court_dispatch_extent(harness) -> list[str]:
    """Read successful court dispatches from shipped durable workflow work."""
    extent: list[str] = []
    for work in harness.workflow_state.transaction_work.values():
        provider = work.provider_attempts.get(work.preparation.attempt_index)
        if provider is None or provider.outcome != "provider_result":
            continue
        role = work.preparation.route_lease.role
        payload = work.preparation.task_payload_value
        if role == "argumentative_critic" and payload.get("schema") == "criticism.semantic-task.v1":
            extent.append("critic")
        elif payload.get("schema") == "defended-trial-step.v1":
            extent.append(str(payload["step"]))
    return extent


def _court_outcome(harness, target_id: str) -> str:
    """Read a semantic trial result from committed measures or target state."""
    for event in reversed(list(harness.log.read())):
        inputs = list(event.inputs)
        if len(inputs) >= 3 and inputs[:2] == ["trial-declined", target_id]:
            return str(inputs[2])
        if len(inputs) >= 2 and inputs[1] == target_id and str(inputs[0]).startswith("trial-blocked:"):
            return str(inputs[0])
    status = harness.state.status.get(target_id)
    if status is not None and status.value == "refuted":
        return "case-sustained"
    raise MatrixRefusal("COURT_OUTCOME_UNRECORDED")


def run_stubbed_court(home: str | os.PathLike[str], *, judge_count: int,
                      returned_paraphrases: Sequence[str] | None,
                      judge_verdict: str = "fail") -> dict[str, Any]:
    """Drive one shipped scheduler cycle and retain its typed court boundary."""
    from deepreason.harness import Harness
    from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError
    from deepreason.llm.budget import TokenMeter
    from deepreason.llm.firewall import (
        JudgeEnsemblePolicyError,
        JudgeSchoolEnsemblePolicyError,
        SchoolRouteResolutionError,
        leases_from_manifest,
    )
    from deepreason.ontology import Problem, ProblemProvenance, Provenance
    from deepreason.rules.warrants import formally_backed
    from deepreason.run_manifest import RunManifestError
    from deepreason.scheduler.scheduler import Scheduler
    from deepreason.workflow.transaction import WorkBudgetDenied

    root = Path(home)
    if root.exists():
        raise MatrixRefusal("COURT_HOME_NOT_FRESH")
    paraphrases = None if returned_paraphrases is None else tuple(returned_paraphrases)
    built = compile_stubbed_court(
        judge_count=judge_count, with_variator=paraphrases is not None,
        paraphrase_count=len(paraphrases or ()),
    )
    config, manifest = built["config"], built["manifest"]
    root.mkdir(parents=True)
    calls: list[str] = []
    harness = Harness(root / "run")
    _bind_court_classification(harness, manifest)
    harness.register_problem(Problem(
        id="pi-full-judge-court", description="exercise one defended court",
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    target = harness.create_artifact(
        "A mechanism whose validity depends on an explicit boundary condition.",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    target_formally_backed = formally_backed(harness, target.id)
    routes = manifest.roles
    critic_response = json.dumps({
        "cases": [{"target_alias": "SRC_001", "attack": True, "case": _COURT_CASE}]
    })
    endpoints: dict[str, Any] = {
        "conjecturer": _court_endpoint(
            routes["conjecturer"][0], calls, lambda _n: "conjecturer",
            json.dumps({"candidates": [{
                "content": "A mechanism whose validity depends on an explicit boundary condition.",
                "typicality": 0.5,
            }]}),
        ),
        "argumentative_critic": [_court_endpoint(
            routes["argumentative_critic"][0], calls, lambda _n: "critic", critic_response,
        )],
        "defender": [_court_endpoint(
            routes["defender"][0], calls, lambda _n: "defender",
            json.dumps({"answer": _COURT_DEFENCE}),
        )],
        "judge": [
            _court_endpoint(
                route, calls,
                lambda n, seat=seat: (
                    f"judge:{seat}" if n == 0 else f"judge:paraphrase:{n - 1}:{seat}"
                ),
                json.dumps({"verdict": judge_verdict, "decisive_point": _COURT_POINT}),
            )
            for seat, route in enumerate(routes["judge"])
        ],
    }
    if paraphrases is not None:
        endpoints["variator"] = [_court_endpoint(
            routes["variator"][0], calls, lambda _n: "variator",
            json.dumps({"edits": [{"content": text} for text in paraphrases]}),
        )]
    adapter = LLMAdapter(
        endpoints, harness.blobs, retry_max=0, model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest), transaction_authority_required=True,
        meter=TokenMeter(1_000_000),
    )
    typed_refusals = (
        RunManifestError, SchoolRouteResolutionError, JudgeEnsemblePolicyError,
        JudgeSchoolEnsemblePolicyError, WorkflowAuthorizationError, WorkBudgetDenied,
    )
    first_refusal = None
    try:
        Scheduler(harness, adapter, config, workload_profile="text",
                  run_manifest=manifest).step()
    except typed_refusals as error:
        first_refusal = {
            "stage": "trial_preflight",
            "code": getattr(error, "code", type(error).__name__),
            "message": str(error),
            "exception_type": type(error).__name__,
        }
    callback_extent = [
        call for call in calls
        if call == "critic" or call == "defender" or call == "variator"
        or call.startswith("judge:")
    ]
    extent = _court_dispatch_extent(harness)
    if callback_extent != extent:
        raise MatrixRefusal(
            "DISPATCH_RECEIPT_MISMATCH",
            f"callback={callback_extent!r}; workflow={extent!r}",
        )
    if first_refusal is not None:
        return {
            "status": "configuration_refused", "first_refusal": first_refusal,
            "dispatch_extent": extent, "target_formally_backed": target_formally_backed,
        }
    outcome = _court_outcome(harness, target.id)
    return {
        "status": "trial_outcome", "outcome_code": outcome, "first_refusal": None,
        "dispatch_extent": extent, "target_formally_backed": target_formally_backed,
        "variator_reachability": (
            "not_exercised_by_outcome" if outcome == "defence-sustained" and paraphrases is not None
            else "exercised" if paraphrases is not None else "not_configured"
        ),
    }


def persist_response_receipts(root: str | os.PathLike[str], prose: str, *,
                              parser_outcome: str, schema_outcome: str,
                              fallback_events: Sequence[str]) -> dict[str, Any]:
    """Persist human prose independently from its mechanical parse receipt."""
    target = Path(root)
    prose_bytes = prose.encode("utf-8")
    blob_ref = "response-prose.txt"
    _atomic_bytes(target / blob_ref, prose_bytes)
    prose_receipt = {
        "blob_ref": blob_ref, "byte_count": len(prose_bytes),
        "sha256": hashlib.sha256(prose_bytes).hexdigest(),
    }
    parser_receipt = {
        "parser_outcome": parser_outcome, "schema_outcome": schema_outcome,
        "fallback_events": list(fallback_events), "structured_value": None,
    }
    _atomic_bytes(target / "prose-receipt.json", canonical_json(prose_receipt))
    _atomic_bytes(target / "parser-receipt.json", canonical_json(parser_receipt))
    return {"prose_receipt": prose_receipt, "parser_receipt": parser_receipt}


def install_soak_case() -> tuple[Any, Any]:
    """Register this experiment's defended-court case in the shipped soak.

    The committed driver remains byte-unchanged.  Its in-memory case registry
    is the intended extension seam for a launch-specific configuration whose
    root construction delegates to this experiment's ``soak_builder``.
    """
    tranche = Path(__file__).resolve().parent
    repo = tranche.parents[1]
    scripts = repo / "scripts"
    scripts_text = str(scripts)
    if scripts_text not in sys.path:
        sys.path.insert(0, scripts_text)

    import cycle_soak

    case = cycle_soak.SoakCase(
        id="judge-matrix",
        description=(
            "the full judge-matrix launch shape: a defended two-judge "
            "cross-family court with critic, defender, variator, four "
            "schools, and attached evidence"
        ),
        config_path=(
            repo
            / "experiments"
            / "2026-08-12-live-grounded-extension-expansion"
            / "run-config.yaml"
        ),
        builder="soak_builder",
        attached_evidence=True,
        default_cycles=8,
        builder_dir=tranche,
        delegates_to_builder=True,
    )
    cycle_soak.CASES[case.id] = case
    return cycle_soak, case


def _run_soak() -> int:
    cycle_soak, case = install_soak_case()
    result = cycle_soak.main(
        ["--case", case.id, "--cycles", str(case.default_cycles)]
    )
    verdict = "PASS" if result == 0 else "FAIL"
    print(
        f"SOAK_VERDICT={verdict} CASE={case.id} "
        f"CYCLES={case.default_cycles}"
    )
    return result


def _enumerate_fixture() -> None:
    domain = load_domain(Path(__file__).with_name("MATRIX_DOMAIN.json"))
    model_count = len(domain["fixture_catalog"])
    counts = seat_counts(model_count)
    print(
        f"CATALOG_MODELS={model_count} JUDGE_PAIRS={counts['judge_pairs']} "
        f"CORE_COURTS={counts['core_courts']} NO_VARIATOR={counts['no_variator']} "
        f"WITH_VARIATOR={counts['with_variator']} TOTAL={counts['total']}"
    )


def _enumerate_full_cross_fixture() -> None:
    tranche = Path(__file__).parent
    domain = load_full_cross_domain(tranche / "FULL_CROSS_DOMAIN.json")
    catalog_domain = load_domain(tranche / "MATRIX_DOMAIN.json")
    model_count = len(freeze_catalog(
        entry["model_id"] for entry in catalog_domain["fixture_catalog"]
    )["model_ids"])
    counts = full_cross_counts(domain, model_count=model_count)
    print(
        f"FULL_CROSS SEAT_TUPLES={counts['seat_tuples']} "
        f"JUDGE_2={counts['judge_count_2']} JUDGE_3={counts['judge_count_3']} "
        f"TOTAL={counts['total']}"
    )


def _run_structural() -> int:
    domain = load_domain(Path(__file__).with_name("MATRIX_DOMAIN.json"))
    expected = sum(group["expected_count"] for group in domain["structural_domains"])
    terminal_ids = structural_case_ids(domain)
    unique = set(terminal_ids)
    duplicate = len(terminal_ids) - len(unique)
    missing = max(0, expected - len(unique))
    extra = max(0, len(unique) - expected)
    print(
        f"STRUCTURAL_EXPECTED={expected} STRUCTURAL_TERMINAL={len(unique)} "
        f"DUPLICATE={duplicate} MISSING={missing}"
    )
    return int(bool(duplicate or missing or extra))


def _run_catalog() -> int:
    import urllib.error
    import urllib.request

    secret = os.environ.get("OLLAMA_API_KEY")
    if not secret:
        raise MatrixRefusal("OLLAMA_API_KEY_MISSING")
    request = urllib.request.Request(
        "https://ollama.com/v1/models",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {secret}",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            provider_payload = json.load(response)
    except urllib.error.HTTPError as error:
        raise MatrixRefusal("CATALOG_HTTP_ERROR", f"status={error.code}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise MatrixRefusal("CATALOG_TRANSPORT_ERROR", type(error).__name__) from None
    frozen = freeze_authenticated_catalog(provider_payload)
    document = {
        "schema": "deepreason.ollama-authenticated-catalog.v1",
        "source": "https://ollama.com/v1/models",
        **frozen,
    }
    payload = canonical_json(document)
    if secret.encode("utf-8") in payload:
        raise MatrixRefusal("SECRET_BEARING_DIAGNOSTIC_WITHHELD")
    target = Path(__file__).with_name("CATALOG.json")
    if target.exists() and target.read_bytes() != payload:
        raise MatrixRefusal("CATALOG_SNAPSHOT_IMMUTABLE")
    if not target.exists():
        _atomic_bytes(target, payload)
    print(
        f"CATALOG_MODELS={len(frozen['model_ids'])} "
        f"EXCLUDED={len(frozen['excluded'])} "
        f"CATALOG_SHA256={frozen['catalog_sha256']}"
    )
    return 0


_PROBE_SETTINGS = ("none", "low", "medium")
_PROBE_SCHEMA = "deepreason.ollama-reasoning-probes.v1"


def _probe_error_row(
    model_id: str, requested_reasoning: str, *, code: str,
    exception_type: str | None = None, http_status: int | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "model_id": model_id,
        "requested_reasoning": requested_reasoning,
        "wire_reasoning": requested_reasoning,
        "status": "provider_indeterminate",
        "code": code,
    }
    if exception_type:
        row["exception_type"] = exception_type
    if http_status is not None:
        row["http_status"] = http_status
    return row


def _build_probe_plan(
    model_id: str, requested_reasoning: str, secret: str,
) -> dict[str, Any]:
    binding = build_live_endpoint(
        {
            "role": "probe",
            "model_id": model_id,
            "model_profile": "standard",
            "output_mode": "json_object",
            "output_mechanism": "native_json_schema",
            "reasoning": {"kind": "string", "value": requested_reasoning},
        },
        criticism_authority="defended_trial",
        environ={"OLLAMA_API_KEY": secret},
    )
    endpoint = binding.endpoint
    response_schema = {
        "type": "object",
        "properties": {"ok": {"type": "boolean", "const": True}},
        "required": ["ok"],
        "additionalProperties": False,
    }
    body = endpoint.build_body(
        "Return exactly the JSON object {\"ok\":true}.",
        response_schema=response_schema,
        output_mechanism="native_json_schema",
        max_tokens=128,
    )
    validate_provider_body(body)
    wire_reasoning = body.get("reasoning_effort")
    if wire_reasoning != requested_reasoning:
        raise MatrixRefusal("PROBE_WIRE_REASONING_MISMATCH")
    body_bytes = canonical_json(body)
    if secret.encode("utf-8") in body_bytes:
        raise MatrixRefusal("SECRET_BEARING_REQUEST_WITHHELD")
    return {
        "model_id": model_id,
        "requested_reasoning": requested_reasoning,
        "wire_reasoning": wire_reasoning,
        "url": endpoint.name.rstrip("/") + "/chat/completions",
        "timeout": endpoint.timeout_s,
        "body": body_bytes,
    }


def _run_probe_plan(plan: Mapping[str, Any], secret: str) -> dict[str, Any]:
    import urllib.error
    import urllib.request

    model_id = plan["model_id"]
    requested = plan["requested_reasoning"]
    request = urllib.request.Request(
        plan["url"], data=plan["body"],
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {secret}",
        },
        method="POST",
    )
    try:
        with _live_call_slot():
            with urllib.request.urlopen(request, timeout=plan["timeout"]) as response:
                response_bytes = response.read()
    except urllib.error.HTTPError as error:
        return _probe_error_row(
            model_id, requested, code="PROBE_HTTP_ERROR",
            exception_type=type(error).__name__, http_status=error.code,
        )
    except Exception as error:
        return _probe_error_row(
            model_id, requested, code="PROBE_TRANSPORT_ERROR",
            exception_type=type(error).__name__,
        )
    if secret.encode("utf-8") in response_bytes:
        return _probe_error_row(
            model_id, requested,
            code="SECRET_BEARING_PROVIDER_RESPONSE_WITHHELD",
        )
    try:
        response_payload = json.loads(response_bytes)
        if not isinstance(response_payload, Mapping):
            raise MatrixRefusal("PROBE_RESPONSE_INVALID")
        choices = response_payload.get("choices")
        choice = choices[0] if isinstance(choices, list) and choices else None
        message = choice.get("message") if isinstance(choice, Mapping) else None
        if not isinstance(message, Mapping):
            raise MatrixRefusal("PROBE_MESSAGE_INVALID")
        receipt = reasoning_probe_receipt(
            model_id=model_id, requested_reasoning=requested,
            message=message, secret=secret,
        )
    except MatrixRefusal as error:
        return _probe_error_row(model_id, requested, code=error.code)
    except (TypeError, ValueError, UnicodeError) as error:
        return _probe_error_row(
            model_id, requested, code="PROBE_RESPONSE_INVALID",
            exception_type=type(error).__name__,
        )
    receipt["wire_reasoning"] = plan["wire_reasoning"]
    return receipt


def _probe_summary(
    document: Mapping[str, Any], model_ids: Sequence[str], secret: str,
) -> dict[str, int]:
    payload = canonical_json(document)
    if secret.encode("utf-8") in payload:
        raise MatrixRefusal("SECRET_BEARING_DIAGNOSTIC_WITHHELD")
    if (
        document.get("schema") != _PROBE_SCHEMA
        or document.get("catalog_sha256")
        != hashlib.sha256(canonical_json(model_ids)).hexdigest()
    ):
        raise MatrixRefusal("PROBE_EVIDENCE_BINDING_MISMATCH")
    rows = document.get("rows")
    expected_pairs = [
        (model_id, setting)
        for model_id in model_ids
        for setting in _PROBE_SETTINGS
    ]
    if not isinstance(rows, list) or [
        (row.get("model_id"), row.get("requested_reasoning"))
        for row in rows if isinstance(row, Mapping)
    ] != expected_pairs:
        raise MatrixRefusal("PROBE_TERMINAL_SET_MISMATCH")
    terminal = sum(
        row.get("status") in {"probe_usable", "provider_indeterminate"}
        for row in rows
    )
    forbidden = sum(
        str(row.get("wire_reasoning", "")).strip().casefold()
        in FORBIDDEN_REASONING
        for row in rows
    )
    leaks = sum(
        str(row.get("code", "")).startswith("SECRET_BEARING_")
        for row in rows
    )
    peak = document.get("peak_in_flight")
    if (
        terminal != len(expected_pairs)
        or isinstance(peak, bool) or not isinstance(peak, int)
        or not 0 <= peak <= 3
    ):
        raise MatrixRefusal("PROBE_EVIDENCE_INVALID")
    return {
        "expected": len(expected_pairs),
        "terminal": terminal,
        "usable": sum(row.get("status") == "probe_usable" for row in rows),
        "provider_indeterminate": sum(
            row.get("status") == "provider_indeterminate" for row in rows
        ),
        "peak": peak,
        "forbidden": forbidden,
        "leaks": leaks,
    }


def _run_probe() -> int:
    secret = os.environ.get("OLLAMA_API_KEY")
    if not secret:
        raise MatrixRefusal("OLLAMA_API_KEY_MISSING")
    tranche = Path(__file__).resolve().parent
    catalog_bytes = (tranche / "CATALOG.json").read_bytes()
    if secret.encode("utf-8") in catalog_bytes:
        raise MatrixRefusal("SECRET_BEARING_DIAGNOSTIC_WITHHELD")
    catalog = json.loads(catalog_bytes)
    model_ids = catalog.get("model_ids")
    if (
        catalog.get("schema") != "deepreason.ollama-authenticated-catalog.v1"
        or not isinstance(model_ids, list)
        or freeze_catalog(model_ids)["model_ids"] != model_ids
        or hashlib.sha256(canonical_json(model_ids)).hexdigest()
        != catalog.get("catalog_sha256")
    ):
        raise MatrixRefusal("CATALOG_SNAPSHOT_INVALID")
    target = tranche / "proof" / "reasoning-probes.json"
    with coordinator_lock("/tmp/deepreason-ollama-full-judge-seat-matrix.lock"):
        if target.exists():
            target_bytes = target.read_bytes()
            if secret.encode("utf-8") in target_bytes:
                raise MatrixRefusal("SECRET_BEARING_DIAGNOSTIC_WITHHELD")
            document = json.loads(target_bytes)
        else:
            plans = [
                _build_probe_plan(model_id, setting, secret)
                for model_id in model_ids
                for setting in _PROBE_SETTINGS
            ]
            live_call_counts(reset_peak=True)
            rows = run_bounded(
                [lambda plan=plan: _run_probe_plan(plan, secret) for plan in plans],
                workers=3,
            )
            counts = live_call_counts()
            document = {
                "schema": _PROBE_SCHEMA,
                "catalog_sha256": catalog["catalog_sha256"],
                "requested_reasoning": list(_PROBE_SETTINGS),
                "expected": len(plans),
                "terminal": len(rows),
                "peak_in_flight": counts["peak"],
                "rows": rows,
            }
            payload = canonical_json(document)
            if secret.encode("utf-8") in payload:
                raise MatrixRefusal("SECRET_BEARING_DIAGNOSTIC_WITHHELD")
            _atomic_bytes(target, payload)
        summary = _probe_summary(document, model_ids, secret)
    print(
        f"PROBE_EXPECTED={summary['expected']} "
        f"PROBE_TERMINAL={summary['terminal']} "
        f"PROBE_USABLE={summary['usable']} "
        f"PROVIDER_INDETERMINATE={summary['provider_indeterminate']} "
        f"PEAK_IN_FLIGHT={summary['peak']} PEAK_IN_FLIGHT<=3 "
        f"FORBIDDEN_REASONING={summary['forbidden']} "
        f"SECRET_LEAK={summary['leaks']}"
    )
    return int(bool(summary["forbidden"] or summary["leaks"]))


_LIVE_TERMINAL_STATUSES = {
    "configuration_refused", "trial_outcome", "provider_indeterminate",
    "unexpected_error",
}
_THROUGH_PREFIXES = {
    "judge-pairs": ("judge_pairs",),
    "core-courts": ("judge_pairs", "core_courts"),
    "no-variator": ("judge_pairs", "core_courts", "no_variator"),
    "seat-only": (
        "judge_pairs", "core_courts", "no_variator", "with_variator",
    ),
}


def _live_source_commit(repo: Path) -> str:
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=repo, text=True,
    ).strip()
    if branch != "codex/live-full-judge-seat-matrix-20260901":
        raise MatrixRefusal("LIVE_BRANCH_ISOLATION_VIOLATION")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo,
        text=True,
    )
    if dirty:
        raise MatrixRefusal("LIVE_SOURCE_NOT_COMMITTED")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True,
    ).strip()
    return _require_hex(commit, 40, "BRANCH_COMMIT_INVALID")


def _attempt_is_quarantined(attempt: Path) -> bool:
    integrity_stop = attempt / "INTEGRITY_STOP.json"
    if not integrity_stop.exists():
        return False
    try:
        stop = json.loads(integrity_stop.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as error:
        raise MatrixRefusal(
            "LIVE_INTEGRITY_STOP_CORRUPT", integrity_stop.name,
        ) from error
    if (
        not isinstance(stop, Mapping)
        or stop.get("schema") != "deepreason.live_attempt_integrity_stop.v1"
        or stop.get("status") != "quarantined"
        or stop.get("result_disposition") != "preserved_excluded"
    ):
        raise MatrixRefusal("LIVE_INTEGRITY_STOP_CORRUPT", integrity_stop.name)
    return True


def _load_live_terminals(
    root: Path, *, domain_sha256: str, catalog_sha256: str,
    secret: str | None,
) -> dict[str, dict[str, Any]]:
    terminals: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("attempt-*/results/*.json")):
        if _attempt_is_quarantined(path.parents[1]):
            continue
        payload = path.read_bytes()
        if secret and secret.encode("utf-8") in payload:
            raise MatrixRefusal("SECRET_BEARING_DIAGNOSTIC_WITHHELD")
        try:
            row = json.loads(payload)
        except (ValueError, UnicodeError) as error:
            raise MatrixRefusal("LIVE_RESULT_CORRUPT", path.name) from error
        case_payload = row.get("case_payload") if isinstance(row, Mapping) else None
        if (
            not isinstance(row, Mapping)
            or row.get("status") not in _LIVE_TERMINAL_STATUSES
            or row.get("domain_sha256") != domain_sha256
            or row.get("catalog_sha256") != catalog_sha256
            or not isinstance(case_payload, Mapping)
            or case_payload.get("schema") != SEAT_SCHEMA
            or row.get("case_id") != _sha256_id(case_payload)
        ):
            raise MatrixRefusal("LIVE_RESULT_CORRUPT", path.name)
        case_id = row["case_id"]
        if case_id in terminals:
            raise MatrixRefusal("LIVE_RESULT_DUPLICATE", case_id)
        terminals[case_id] = dict(row)
    return terminals


def _load_full_cross_terminals(
    root: Path, *, domain: Mapping[str, Any], model_ids: Sequence[str],
    domain_sha256: str, catalog_sha256: str, secret: str | None = None,
) -> dict[int, dict[str, Any]]:
    """Load exact full-cross receipts without walking any uncompleted prefix."""
    _require_hex(domain_sha256, 64, "FULL_CROSS_DOMAIN_DIGEST_INVALID")
    _validate_full_cross_catalog_digest(catalog_sha256)
    result_paths = sorted(root.glob("attempt-*/results/*.json"))
    binding_path = root / "binding.json"
    if binding_path.exists():
        try:
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as error:
            raise MatrixRefusal("FULL_CROSS_BINDING_CORRUPT") from error
        if not isinstance(binding, Mapping):
            raise MatrixRefusal("FULL_CROSS_BINDING_CORRUPT")
        if binding.get("domain_sha256") != domain_sha256:
            raise MatrixRefusal("DOMAIN_DIGEST_MISMATCH")
        if binding.get("catalog_sha256") != catalog_sha256:
            raise MatrixRefusal("CATALOG_DIGEST_MISMATCH")
    elif result_paths:
        raise MatrixRefusal("FULL_CROSS_BINDING_MISSING")

    terminals: dict[int, dict[str, Any]] = {}
    case_ids: set[str] = set()
    for path in result_paths:
        if _attempt_is_quarantined(path.parents[1]):
            continue
        payload = path.read_bytes()
        if secret and secret.encode("utf-8") in payload:
            raise MatrixRefusal("SECRET_BEARING_DIAGNOSTIC_WITHHELD")
        try:
            row = json.loads(payload)
        except (ValueError, UnicodeError) as error:
            raise MatrixRefusal("FULL_CROSS_RESULT_CORRUPT", path.name) from error
        case_payload = row.get("case_payload") if isinstance(row, Mapping) else None
        ordinal = row.get("ordinal") if isinstance(row, Mapping) else None
        if (
            not isinstance(row, Mapping)
            or row.get("status") not in _LIVE_TERMINAL_STATUSES
            or row.get("domain_sha256") != domain_sha256
            or row.get("catalog_sha256") != catalog_sha256
            or not isinstance(case_payload, Mapping)
            or case_payload.get("schema") != FULL_CROSS_CASE_SCHEMA
            or not isinstance(ordinal, int)
            or isinstance(ordinal, bool)
        ):
            raise MatrixRefusal("FULL_CROSS_RESULT_CORRUPT", path.name)
        try:
            expected = full_cross_case_at(
                domain,
                model_ids,
                ordinal,
                catalog_sha256=catalog_sha256,
                criticism_authority="defended_trial",
            )
        except MatrixRefusal as error:
            raise MatrixRefusal("FULL_CROSS_RESULT_CORRUPT", path.name) from error
        case_id = row.get("case_id")
        if (
            dict(case_payload) != expected
            or case_id != expected["case_id"]
            or path.name != f"{case_id.removeprefix('sha256:')}.json"
        ):
            raise MatrixRefusal("FULL_CROSS_RESULT_CORRUPT", path.name)
        if ordinal in terminals or case_id in case_ids:
            raise MatrixRefusal("FULL_CROSS_RESULT_DUPLICATE", str(ordinal))
        terminals[ordinal] = dict(row)
        case_ids.add(case_id)
    return terminals


def full_cross_resume_summary(
    domain: Mapping[str, Any], model_ids: Sequence[str], *,
    catalog_sha256: str, terminals: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    """Summarize exact set completion and identify the first missing ordinal."""
    models = _full_cross_models(model_ids)
    expected = full_cross_counts(domain, model_count=len(models))["total"]
    ordinals = set(terminals)
    if any(
        isinstance(ordinal, bool)
        or not isinstance(ordinal, int)
        or not 0 <= ordinal < expected
        for ordinal in ordinals
    ):
        raise MatrixRefusal("FULL_CROSS_RESULT_ORDINAL_INVALID")
    terminal = len(ordinals)
    if terminal > expected:
        raise MatrixRefusal("FULL_CROSS_RESULT_COUNT_INVALID")
    next_ordinal = 0
    while next_ordinal in ordinals:
        next_ordinal += 1
    next_case = None
    if next_ordinal < expected:
        next_case = full_cross_case_at(
            domain,
            models,
            next_ordinal,
            catalog_sha256=catalog_sha256,
            criticism_authority="defended_trial",
        )
    return {
        "expected": expected,
        "terminal": terminal,
        "possible": sum(
            row.get("status") == "trial_outcome"
            and row.get("full_dispatch_reached") is True
            for row in terminals.values()
        ),
        "impossible": sum(
            row.get("status") == "configuration_refused"
            for row in terminals.values()
        ),
        "provider_indeterminate": sum(
            row.get("status") == "provider_indeterminate"
            for row in terminals.values()
        ),
        "unexpected_error": sum(
            row.get("status") == "unexpected_error"
            for row in terminals.values()
        ),
        "interrupted": 0,
        "pending": expected - terminal,
        "next_ordinal": next_ordinal if next_case is not None else None,
        "next_case_id": next_case["case_id"] if next_case is not None else None,
    }


def _unexpected_live_result(
    receipt: Mapping[str, Any], error: Exception,
) -> dict[str, Any]:
    return {
        **receipt,
        "status": "unexpected_error",
        "dispatch_extent": [],
        "first_boundary": {
            "stage": "driver",
            "exception_type": type(error).__name__,
            "code": getattr(error, "code", type(error).__name__),
            "pointer": getattr(error, "pointer", None),
            "message": str(error),
        },
        "full_dispatch_reached": False,
        "variator_reachability": "not_reached",
    }


def _run_and_persist_live_case(
    row: Mapping[str, Any], *, attempt: Path, secret: str,
    domain_sha256: str, branch_commit: str,
) -> dict[str, Any]:
    digest = row["case_id"].split(":", 1)[1]
    result_path = attempt / "results" / f"{digest}.json"
    if result_path.exists():
        raise MatrixRefusal("TERMINAL_RESULT_IMMUTABLE")
    receipt = _baseline_live_case_receipt(
        row, domain_sha256=domain_sha256, branch_commit=branch_commit,
    )
    try:
        result = run_live_seat_case(
            row,
            attempt / "cases" / digest,
            secret=secret,
            domain_sha256=domain_sha256,
            branch_commit=branch_commit,
        )
    except MatrixRefusal as error:
        if error.code in {
            "SECRET_BEARING_DIAGNOSTIC_WITHHELD",
            "SECRET_BEARING_PROVIDER_RESPONSE_WITHHELD",
            "KIMI_K3_FORBIDDEN",
            "FORBIDDEN_REASONING_EFFORT",
            "OLLAMA_API_KEY_MISSING",
            "LIVE_CASE_HOME_NOT_FRESH",
        }:
            raise
        result = {
            **receipt,
            **classify_live_result(
                error=error, stage="compile", dispatch_extent=[],
                provider_dependent=False,
            ),
            "full_dispatch_reached": False,
            "variator_reachability": "not_reached",
        }
    except ValueError as error:
        _ensure_exception_is_secret_free(error, secret)
        result = {
            **receipt,
            **classify_live_result(
                error=error, stage="compile", dispatch_extent=[],
                provider_dependent=False,
            ),
            "full_dispatch_reached": False,
            "variator_reachability": "not_reached",
        }
    except Exception as error:
        _ensure_exception_is_secret_free(error, secret)
        result = _unexpected_live_result(receipt, error)
    payload = safe_live_result_bytes(result, secret=secret)
    persisted = json.loads(payload)
    if persisted.get("code") == "SECRET_BEARING_DIAGNOSTIC_WITHHELD":
        _atomic_bytes(result_path, payload)
        raise MatrixRefusal("SECRET_BEARING_DIAGNOSTIC_WITHHELD")
    _atomic_bytes(result_path, payload)
    return persisted


def _live_scope_count(model_count: int, through: str | None) -> int:
    counts = seat_counts(model_count)
    return {
        "judge-pairs": counts["judge_pairs"],
        "core-courts": counts["core_courts"],
        "no-variator": counts["no_variator"],
        "seat-only": counts["total"],
        None: counts["total"],
    }[through]


def _iter_live_scope(
    model_ids: Sequence[str], *, catalog_sha256: str, through: str | None,
) -> Iterator[dict[str, Any]]:
    allowed = _THROUGH_PREFIXES.get(through)
    for row in iter_seat_cases(model_ids, catalog_sha256=catalog_sha256):
        if allowed is not None and row["prefix"] not in allowed:
            return
        yield row


def _run_summary() -> int:
    tranche = Path(__file__).resolve().parent
    catalog = json.loads((tranche / "CATALOG.json").read_text(encoding="utf-8"))
    model_ids = catalog.get("model_ids")
    if (
        catalog.get("schema") != "deepreason.ollama-authenticated-catalog.v1"
        or not isinstance(model_ids, list)
        or freeze_catalog(model_ids)["model_ids"] != model_ids
        or hashlib.sha256(canonical_json(model_ids)).hexdigest()
        != catalog.get("catalog_sha256")
    ):
        raise MatrixRefusal("CATALOG_SNAPSHOT_INVALID")

    seat_domain_path = tranche / "MATRIX_DOMAIN.json"
    seat_domain_sha256 = hashlib.sha256(seat_domain_path.read_bytes()).hexdigest()
    load_domain(seat_domain_path)
    seat_terminals = _load_live_terminals(
        tranche / "home/live-seat-matrix",
        domain_sha256=seat_domain_sha256,
        catalog_sha256=catalog["catalog_sha256"],
        secret=None,
    )
    anchor = model_ids[0]
    projection_predicates = {
        "judge-pairs": lambda row: (
            row.get("critic") == anchor
            and row.get("defender") == anchor
            and row.get("variator") is None
        ),
        "core-courts": lambda row: (
            row.get("critic") == anchor and row.get("variator") is None
        ),
        "no-variator": lambda row: row.get("variator") is None,
        "seat-only": lambda row: True,
    }
    for name, predicate in projection_predicates.items():
        expected = _live_scope_count(len(model_ids), name)
        terminal = sum(
            predicate(row["case_payload"]) for row in seat_terminals.values()
        )
        print(
            f"PROJECTION={name} EXPECTED={expected} TERMINAL={terminal} "
            f"PENDING={expected - terminal}"
        )

    full_cross_path = tranche / "FULL_CROSS_DOMAIN.json"
    full_cross_bytes = full_cross_path.read_bytes()
    full_cross_domain = load_full_cross_domain(full_cross_path)
    full_cross_terminals = _load_full_cross_terminals(
        tranche / "home/live-full-cross",
        domain=full_cross_domain,
        model_ids=model_ids,
        domain_sha256=hashlib.sha256(full_cross_bytes).hexdigest(),
        catalog_sha256=catalog["catalog_sha256"],
    )
    summary = full_cross_resume_summary(
        full_cross_domain,
        model_ids,
        catalog_sha256=catalog["catalog_sha256"],
        terminals=full_cross_terminals,
    )
    next_ordinal = (
        str(summary["next_ordinal"])
        if summary["next_ordinal"] is not None else "none"
    )
    next_case_id = summary["next_case_id"] or "none"
    print(
        f"EXPECTED={summary['expected']} TERMINAL={summary['terminal']} "
        f"POSSIBLE={summary['possible']} IMPOSSIBLE={summary['impossible']} "
        f"PROVIDER_INDETERMINATE={summary['provider_indeterminate']} "
        f"UNEXPECTED_ERROR={summary['unexpected_error']} "
        f"INTERRUPTED={summary['interrupted']} PENDING={summary['pending']} "
        f"NEXT_ORDINAL={next_ordinal} NEXT_CASE_ID={next_case_id} "
        "PEAK_IN_FLIGHT<=3 SCOPE=full-cross"
    )
    return 0


def _run_live(*, limit: int | None, workers: int, through: str | None) -> int:
    if limit is not None and (isinstance(limit, bool) or limit < 1):
        raise MatrixRefusal("LIVE_LIMIT_INVALID")
    if isinstance(workers, bool) or not 1 <= workers <= 3:
        raise MatrixRefusal("LIVE_WORKERS_INVALID")
    secret = os.environ.get("OLLAMA_API_KEY")
    if not secret:
        raise MatrixRefusal("OLLAMA_API_KEY_MISSING")
    tranche = Path(__file__).resolve().parent
    repo = tranche.parents[1]
    catalog_bytes = (tranche / "CATALOG.json").read_bytes()
    if secret.encode("utf-8") in catalog_bytes:
        raise MatrixRefusal("SECRET_BEARING_DIAGNOSTIC_WITHHELD")
    catalog = json.loads(catalog_bytes)
    model_ids = catalog.get("model_ids")
    if (
        catalog.get("schema") != "deepreason.ollama-authenticated-catalog.v1"
        or not isinstance(model_ids, list)
        or freeze_catalog(model_ids)["model_ids"] != model_ids
        or hashlib.sha256(canonical_json(model_ids)).hexdigest()
        != catalog.get("catalog_sha256")
    ):
        raise MatrixRefusal("CATALOG_SNAPSHOT_INVALID")
    domain_bytes = (tranche / "MATRIX_DOMAIN.json").read_bytes()
    domain_sha256 = hashlib.sha256(domain_bytes).hexdigest()
    load_domain(tranche / "MATRIX_DOMAIN.json")
    branch_commit = _live_source_commit(repo)
    root = tranche / "home" / "live-seat-matrix"
    expected = _live_scope_count(len(model_ids), through)

    with coordinator_lock("/tmp/deepreason-ollama-full-judge-seat-matrix.lock"):
        terminals = _load_live_terminals(
            root,
            domain_sha256=domain_sha256,
            catalog_sha256=catalog["catalog_sha256"],
            secret=secret,
        )
        selected: list[dict[str, Any]] = []
        scope_ids: set[str] | None = set() if through is not None else None
        for row in _iter_live_scope(
            model_ids,
            catalog_sha256=catalog["catalog_sha256"],
            through=through,
        ):
            if scope_ids is not None:
                scope_ids.add(row["case_id"])
            if row["case_id"] in terminals:
                continue
            if limit is None or len(selected) < limit:
                selected.append(row)
            if limit is not None and len(selected) == limit and through is None:
                break
        live_call_counts(reset_peak=True)
        completed: list[dict[str, Any]] = []
        if selected:
            attempt = prepare_attempt(
                root,
                domain_sha256=domain_sha256,
                catalog_sha256=catalog["catalog_sha256"],
            )
            try:
                completed = run_bounded(
                    [
                        lambda row=row: _run_and_persist_live_case(
                            row,
                            attempt=attempt,
                            secret=secret,
                            domain_sha256=domain_sha256,
                            branch_commit=branch_commit,
                        )
                        for row in selected
                    ],
                    workers=workers,
                )
            finally:
                if not (attempt / "INTERRUPTED.json").exists():
                    mark_interrupted(attempt)
        terminals = _load_live_terminals(
            root,
            domain_sha256=domain_sha256,
            catalog_sha256=catalog["catalog_sha256"],
            secret=secret,
        )
        scoped = (
            [terminals[case_id] for case_id in scope_ids if case_id in terminals]
            if scope_ids is not None else list(terminals.values())
        )
        counts = live_call_counts()
    status_counts = {
        status: sum(row.get("status") == status for row in scoped)
        for status in _LIVE_TERMINAL_STATUSES
    }
    possible = sum(
        row.get("status") == "trial_outcome" and row.get("full_dispatch_reached")
        for row in scoped
    )
    print(
        f"LIVE_EXPECTED={expected} LIVE_TERMINAL={len(scoped)} "
        f"POSSIBLE={possible} "
        f"CONFIGURATION_REFUSED={status_counts['configuration_refused']} "
        f"PROVIDER_INDETERMINATE={status_counts['provider_indeterminate']} "
        f"UNEXPECTED_ERROR={status_counts['unexpected_error']} "
        f"PENDING={expected - len(scoped)} "
        f"PEAK_IN_FLIGHT={counts['peak']} PEAK_IN_FLIGHT<=3"
    )
    if completed:
        first = completed[0]
        print(
            f"FIRST_CASE={first['case_id']} STATUS={first['status']} "
            f"DISPATCH_EXTENT={','.join(first.get('dispatch_extent', [])) or 'none'}"
        )
    return int(bool(status_counts["unexpected_error"] or counts["peak"] > 3))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    enumerate_parser = subparsers.add_parser("enumerate")
    enumerate_parser.add_argument("--fixture-catalog", action="store_true", required=True)
    full_cross_parser = subparsers.add_parser("full-cross-enumerate")
    full_cross_parser.add_argument("--fixture-catalog", action="store_true", required=True)
    subparsers.add_parser("soak")
    subparsers.add_parser("structural")
    subparsers.add_parser("catalog")
    subparsers.add_parser("probe")
    subparsers.add_parser("summarize")
    live_parser = subparsers.add_parser("live")
    live_parser.add_argument("--limit", type=int)
    live_parser.add_argument("--workers", type=int, default=3)
    live_parser.add_argument("--through", choices=tuple(_THROUGH_PREFIXES))
    args = parser.parse_args(argv)
    if args.command == "enumerate" and args.fixture_catalog:
        _enumerate_fixture()
    elif args.command == "full-cross-enumerate" and args.fixture_catalog:
        _enumerate_full_cross_fixture()
    elif args.command == "soak":
        return _run_soak()
    elif args.command == "structural":
        return _run_structural()
    elif args.command == "catalog":
        return _run_catalog()
    elif args.command == "probe":
        return _run_probe()
    elif args.command == "summarize":
        return _run_summary()
    elif args.command == "live":
        return _run_live(
            limit=args.limit, workers=args.workers, through=args.through,
        )
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
