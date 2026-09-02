#!/usr/bin/env python3
"""Offline domain, safety, and resume primitives for the full-judge matrix."""
from __future__ import annotations
import argparse, contextlib, fcntl, hashlib, itertools, json, os, re, struct
import sys, tempfile, threading, unicodedata
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
        with _CALL_SLOTS:
            with _CALL_COUNTER_LOCK:
                _CALL_COUNTER["active"] += 1
                _CALL_COUNTER["peak"] = max(
                    _CALL_COUNTER["peak"], _CALL_COUNTER["active"]
                )
            try:
                return self._endpoint.complete(*args, **kwargs)
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
    *, model_id: str, requested_reasoning: str, message: Mapping[str, Any]
) -> dict[str, Any]:
    """Record probe structure and trace metadata without persisting trace text."""
    validate_provider_body({
        "model": model_id, "reasoning_effort": requested_reasoning,
    })
    if requested_reasoning not in {"none", "low", "medium"}:
        raise MatrixRefusal("PROBE_REASONING_NOT_REGISTERED")
    if not isinstance(message, Mapping):
        raise MatrixRefusal("PROBE_MESSAGE_INVALID")
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
        encoded = value.encode("utf-8") if isinstance(value, str) else b""
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
    with _CALL_SLOTS:
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    enumerate_parser = subparsers.add_parser("enumerate")
    enumerate_parser.add_argument("--fixture-catalog", action="store_true", required=True)
    full_cross_parser = subparsers.add_parser("full-cross-enumerate")
    full_cross_parser.add_argument("--fixture-catalog", action="store_true", required=True)
    subparsers.add_parser("soak")
    args = parser.parse_args(argv)
    if args.command == "enumerate" and args.fixture_catalog:
        _enumerate_fixture()
    elif args.command == "full-cross-enumerate" and args.fixture_catalog:
        _enumerate_full_cross_fixture()
    elif args.command == "soak":
        return _run_soak()
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
