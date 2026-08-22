"""Semantics-preserving JSON normalization and bounded local repair helpers.

This module is deliberately transport-only.  It never selects a route,
changes policy, or manufactures a substantive field.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from deepreason.canonical import canonical_json, sha256_hex


class OutputMechanism(StrEnum):
    NATIVE_JSON_SCHEMA = "native_json_schema"
    GRAMMAR = "grammar"
    JSON_TEXT = "json_text"


class SchemaRepairError(RuntimeError):
    """Bounded schema repair failed; ``spend`` carries attempted usage."""

    def __init__(self, message: str, spend=None) -> None:
        super().__init__(message)
        self.spend = spend


class RepairScopeViolation(ValueError):
    """A parseable repair changed JSON outside its authorized subtree."""

    code = "REPAIR_SCOPE_VIOLATION"

    def __init__(self, pointer: str, repair_scope: str) -> None:
        self.pointer = pointer
        self.repair_scope = repair_scope
        scope = repair_scope or "/"
        super().__init__(
            f"repair changed JSON outside authorized subtree {scope}: "
            f"{pointer or '/'}"
        )


class UnrepairableDiagnosticError(ValueError):
    """The validator did not identify a finite model-editable location."""

    code = "REPAIR_DIAGNOSTIC_UNREPAIRABLE"


class SchemaExhaustedError(SchemaRepairError):
    """The v6 contract exhausted its finite local-repair authority."""

    code = "schema_exhausted"

    def __init__(self, message: str = "bounded schema repair was exhausted", spend=None):
        super().__init__(message, spend=spend)


# Container names a model has used to wrap the single patch object it was
# asked for.  None of them is a RepairPatchV1 field and the model forbids
# extra fields, so a dict whose sole key is one of these can never itself be
# a valid patch: unwrapping cannot lose information.  Record-driven — every
# name here appears in a recorded response, none is added speculatively
# (run-40e713b30a147dfc, epoch 1).
_PATCH_CONTAINER_KEYS = frozenset(
    {"repair.patch.v1", "patch", "patches", "operations"}
)

# Field names a model has used for RepairPatchV1's own fields.  Renaming is
# lossless only while the real field is absent, which the caller checks.
_PATCH_FIELD_SYNONYMS = {"operation": "op", "pointer": "path"}


def _unwrap_patch_container(value):
    """Strip one list-of-one and one known container key, in either order."""

    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
        value = value[0]
    if isinstance(value, dict) and len(value) == 1:
        key = next(iter(value))
        if key in _PATCH_CONTAINER_KEYS:
            inner = value[key]
            if isinstance(inner, list) and len(inner) == 1 and isinstance(inner[0], dict):
                inner = inner[0]
            if isinstance(inner, dict):
                value = inner
    return value


def _drop_envelope_echoes(value, envelope):
    """Remove only bytes the harness itself put in the dispatched envelope.

    Exact equality is the whole safety argument: a key whose value differs
    from what was sent is the model's own and survives, so a wrong ``schema``
    literal or a mismatched baseline still fails validation as before.
    """

    if not isinstance(value, dict):
        return value
    echoes = {"schema": "repair.patch.v1"}
    if envelope is not None:
        echoes["contract"] = envelope.contract
        echoes["baseline_sha256"] = envelope.baseline_sha256
    dropped = {
        key: item
        for key, item in value.items()
        if not (key in echoes and item == echoes[key])
    }
    return dropped if len(dropped) != len(value) else value


def _rename_patch_field_synonyms(value):
    """Rename a synonym onto its RepairPatchV1 field when that field is absent."""

    if not isinstance(value, dict):
        return value
    renames = {
        source: target
        for source, target in _PATCH_FIELD_SYNONYMS.items()
        if source in value and target not in value
    }
    if "operation" in renames and value["operation"] not in {"add", "remove", "replace"}:
        del renames["operation"]
    if "pointer" in renames and not (
        isinstance(value["pointer"], str) and value["pointer"]
    ):
        del renames["pointer"]
    if not renames:
        return value
    return {renames.get(key, key): item for key, item in value.items()}


def tolerant_patch_value(value, envelope=None):
    """Strip lossless transport packaging from a patch payload.

    Observed live: models answer patch turns with the patch wrapped in a
    container key (the schema name from the prompt, or ``patch`` /
    ``patches`` / ``operations``), sometimes inside a single-element array;
    with the envelope's own ``contract`` / ``baseline_sha256`` echoed back
    alongside the patch; and with RFC-6902 fields spelled ``operation`` or
    ``pointer``.  Each of those is lossless and unambiguous, the same
    tolerance class as narrated code fences, and each discarded response
    still consumed one of the contract's finite repair grants — the epoch-1
    conjecturer seat exhausted itself holding a correct final patch
    (run-40e713b30a147dfc; experiments/2026-08-22-fix-repair-patch-transport).

    What is NOT absorbed: anything requiring the harness to supply a value
    the model did not give.  ``{"op": "replace", "old": …, "new": …}`` has no
    ``value`` and stays a typed rejection, because reading ``new`` as
    ``value`` would be an inference about intent rather than a rename.

    ``envelope`` is the dispatched :class:`RepairDiagnosticEnvelopeV2`.  Both
    boundaries that call this must pass the same one, so a patch the session
    applies is never re-rejected at admission.  Without it the echo rule is
    inert and every other tolerance is unchanged.
    """

    value = _unwrap_patch_container(value)
    value = _drop_envelope_echoes(value, envelope)
    # The echo drop can leave a lone container key behind, e.g. the recorded
    # {"contract": …, "operations": [ … ], "schema": …}.
    value = _unwrap_patch_container(value)
    return _rename_patch_field_synonyms(value)


class RepairPatchV1(BaseModel):
    """One RFC-6902-shaped edit at one explicitly authorized JSON pointer.

    This is intentionally not a general patch document: every provider turn
    can propose exactly one operation, and ``value`` is absent for ``remove``
    while remaining required (including an explicit JSON null) for the other
    two operations.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    schema_: Literal["repair.patch.v1"] = Field(
        "repair.patch.v1", alias="schema"
    )
    op: Literal["add", "remove", "replace"]
    path: str
    value: Any = None

    @field_validator("path")
    @classmethod
    def _non_root_canonical_pointer(cls, value: str) -> str:
        _validate_json_pointer(value, allow_root=False)
        return value

    @model_validator(mode="after")
    def _operation_has_exact_fields(self):
        value_supplied = "value" in self.model_fields_set
        if self.op == "remove" and value_supplied:
            raise ValueError("remove patch must omit value")
        if self.op != "remove" and not value_supplied:
            raise ValueError(f"{self.op} patch requires value")
        return self


class RepairDiagnosticV2(BaseModel):
    """One field-level contract failure in a v6 repair envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    path: str
    code: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=500)
    received: Any = None
    allowed: str = Field(default="", max_length=2_048)
    # Handle-aware guidance, populated only for reference-field failures so
    # a repair can pick a legal handle (or a legal omission) instead of
    # regex-guessing new invalid handles.  Absent fields serialize away.
    rejected_handle: str | None = Field(default=None, max_length=128)
    observed_handle_kind: str | None = Field(default=None, max_length=64)
    required_handle_kinds: tuple[str, ...] | None = Field(
        default=None, max_length=16
    )
    legal_handles: tuple[str, ...] | None = Field(default=None, max_length=64)
    omission_or_unknown_legal: bool | None = None
    instruction: str | None = Field(default=None, max_length=500)

    @field_validator("path")
    @classmethod
    def _canonical_pointer(cls, value: str) -> str:
        _validate_json_pointer(value, allow_root=True)
        return value


class FrozenSubtreeHashV1(BaseModel):
    """Digest of a maximal valid subtree that no authorized patch may edit."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("path")
    @classmethod
    def _canonical_pointer(cls, value: str) -> str:
        _validate_json_pointer(value, allow_root=True)
        return value


class RepairDiagnosticEnvelopeV2(BaseModel):
    """Finite repair authority bound to one exact parseable baseline."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    schema_: Literal["repair.diagnostic-envelope.v2"] = Field(
        "repair.diagnostic-envelope.v2", alias="schema"
    )
    contract: str = Field(min_length=1, max_length=256)
    baseline_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    diagnostics: tuple[RepairDiagnosticV2, ...] = Field(
        min_length=1, max_length=64
    )
    authorized_pointers: tuple[str, ...] = Field(min_length=1, max_length=64)
    frozen_subtree_hashes: tuple[FrozenSubtreeHashV1, ...] = Field(
        default=(), max_length=4_096
    )

    @field_validator("authorized_pointers")
    @classmethod
    def _finite_non_root_pointers(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for pointer in value:
            _validate_json_pointer(pointer, allow_root=False)
        if tuple(sorted(set(value))) != value:
            raise ValueError("authorized pointers must be sorted and unique")
        return value

    @field_validator("frozen_subtree_hashes")
    @classmethod
    def _ordered_frozen_hashes(
        cls, value: tuple[FrozenSubtreeHashV1, ...]
    ) -> tuple[FrozenSubtreeHashV1, ...]:
        paths = tuple(item.path for item in value)
        if tuple(sorted(set(paths))) != paths:
            raise ValueError("frozen subtree hashes must be sorted and unique")
        return value


def select_output_mechanism(capabilities) -> OutputMechanism:
    """Choose once in priority order; the caller freezes the result."""
    if bool(getattr(capabilities, "native_json_schema", False)):
        return OutputMechanism.NATIVE_JSON_SCHEMA
    if bool(getattr(capabilities, "grammar", False)):
        return OutputMechanism.GRAMMAR
    return OutputMechanism.JSON_TEXT


class RepairDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: str
    path: str
    error: str
    received: Any = None
    allowed: str = ""
    repair_scope: str
    skeleton: Any = None
    rejected_handle: str | None = None
    observed_handle_kind: str | None = None
    required_handle_kinds: tuple[str, ...] | None = None
    legal_handles: tuple[str, ...] | None = None
    omission_or_unknown_legal: bool | None = None
    instruction: str | None = None


@dataclass(frozen=True)
class ParsedJSON:
    text: str
    value: Any


@dataclass(frozen=True)
class RepairTurn:
    """One deterministic turn in the bounded structured-output protocol.

    The transport owns the actual provider request and accounting.  This
    value owns only the request text, response schema, and repair location,
    so both DeepReason and MiniReason can execute the same protocol without
    sharing endpoint, meter, or event-log implementations.
    """

    attempt: int
    request: str
    response_schema: dict[str, Any]
    repair_scope: str = ""
    validation_path: str = ""


_FENCE = re.compile(
    r"\A\s*```(?:json|JSON)?[ \t]*\r?\n(?P<body>.*)\r?\n```\s*\Z",
    re.DOTALL,
)

_FENCED_BLOCK = re.compile(
    r"```(?:json|JSON)?[ \t]*\r?\n(?P<body>.*?)\r?\n[ \t]*```",
    re.DOTALL,
)


def strip_json_fence(raw: str) -> str:
    """Remove one surrounding markdown fence and nothing inside it."""
    match = _FENCE.match(raw)
    return match.group("body") if match else raw.strip()


def _contains_json_value(segment: str) -> bool:
    """True when prose around a fence itself carries a complete JSON value."""

    decoder = json.JSONDecoder()
    stripped = segment.strip()
    if stripped:
        try:
            _, end = decoder.raw_decode(stripped)
        except json.JSONDecodeError:
            pass
        else:
            if not stripped[end:].strip():
                return True
    for start, char in enumerate(segment):
        if char not in "{[":
            continue
        try:
            decoder.raw_decode(segment, start)
        except json.JSONDecodeError:
            continue
        return True
    return False


def _sole_fenced_json_value(text: str) -> ParsedJSON | None:
    """Extract the one fenced JSON value when nothing competes with it.

    Live providers wrap the actual value in one markdown fence between
    explanation prose ("Here's the corrected JSON ... ```json {...} ``` ...").
    The fence is authoritative only when it is unambiguous: exactly one
    well-formed fenced block, whose body is exactly one complete JSON value,
    with no complete JSON value anywhere in the surrounding text.  Two fenced
    blocks, a fence plus a bare top-level value elsewhere, or surrounding
    content that itself parses as JSON all stay rejected.
    """

    if text.count("```") != 2:
        return None
    blocks = tuple(_FENCED_BLOCK.finditer(text))
    if len(blocks) != 1:
        return None
    body = blocks[0].group("body").strip()
    decoder = json.JSONDecoder()
    try:
        value, end = decoder.raw_decode(body)
    except json.JSONDecodeError:
        return None
    if body[end:].strip():
        return None
    outside = text[: blocks[0].start()] + text[blocks[0].end() :]
    if _contains_json_value(outside):
        return None
    return ParsedJSON(body[:end], value)


def parse_one_json_value(raw: str) -> ParsedJSON:
    """Extract one complete top-level JSON value without coercion.

    Provider prose around a value and one surrounding markdown fence are
    transport wrappers.  Keys, enum values, arrays, and scalar types are
    preserved exactly.
    """
    if not isinstance(raw, str):
        raise ValueError("JSON response must be text")
    text = strip_json_fence(raw)
    decoder = json.JSONDecoder()

    # Prefer the complete value at the first non-whitespace character.
    stripped = text.lstrip()
    offset = len(text) - len(stripped)
    try:
        value, end = decoder.raw_decode(stripped)
        if stripped[end:].strip():
            raise ValueError("multiple top-level JSON values or trailing content")
        return ParsedJSON(stripped[:end], value)
    except json.JSONDecodeError:
        pass

    # A provider may prefix prose. Role contracts are objects/arrays, so find
    # the first complete structured value. This cannot invent or coerce data.
    trailing_content = False
    for start, char in enumerate(text):
        if char not in "{[":
            continue
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            continue
        if text[end:].strip():
            trailing_content = True
            break
        return ParsedJSON(text[start:end], value)

    # Prose may also follow the value.  That is a transport wrapper only when
    # one markdown fence unambiguously marks which value is authoritative.
    fenced = _sole_fenced_json_value(text)
    if fenced is not None:
        return fenced
    if trailing_content:
        raise ValueError("multiple top-level JSON values or trailing content")
    raise ValueError(f"no complete top-level JSON value at offset {offset}")


def _pointer_token(value: Any) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def json_pointer(loc: tuple[Any, ...] | list[Any]) -> str:
    return "" if not loc else "/" + "/".join(_pointer_token(part) for part in loc)


def _unescape_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def pointer_parts(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON Pointer {pointer!r}")
    return [_unescape_pointer_token(p) for p in pointer[1:].split("/")]


def _validate_json_pointer(pointer: str, *, allow_root: bool) -> None:
    if not isinstance(pointer, str):
        raise ValueError("JSON Pointer must be text")
    if pointer == "":
        if allow_root:
            return
        raise ValueError("a patch may not replace the parseable root object")
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON Pointer {pointer!r}")
    for token in pointer[1:].split("/"):
        for match in re.finditer(r"~", token):
            following = token[match.start() + 1 : match.start() + 2]
            if following not in {"0", "1"}:
                raise ValueError(f"invalid JSON Pointer escape in {pointer!r}")
    if json_pointer(pointer_parts(pointer)) != pointer:
        raise ValueError(f"non-canonical JSON Pointer {pointer!r}")


def pointer_get(value: Any, pointer: str) -> Any:
    current = value
    for part in pointer_parts(pointer):
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as exc:
                raise ValueError(f"unknown list path {pointer!r}") from exc
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise ValueError(f"unknown object path {pointer!r}")
    return current


def _subtree_hash(value: Any) -> str:
    return sha256_hex(canonical_json(value))


def _frozen_subtree_hashes(
    baseline: Any,
    authorized_pointers: tuple[str, ...],
) -> tuple[FrozenSubtreeHashV1, ...]:
    """Hash maximal unaffected object subtrees for an auditable state fence.

    List siblings are deliberately not addressed by index: an authorized
    removal would shift their JSON Pointers even though their values were not
    edited. Object siblings and fields of the selected list item remain
    frozen, which is sufficient because the deterministic patch applicator
    itself can perform only the one requested operation.
    """

    authorized_parts = tuple(tuple(pointer_parts(item)) for item in authorized_pointers)
    frozen: list[FrozenSubtreeHashV1] = []

    def related(prefix: tuple[str, ...], candidate: tuple[str, ...]) -> bool:
        return candidate[: len(prefix)] == prefix

    def visit(current: Any, parts: tuple[str, ...]) -> None:
        if parts in authorized_parts:
            return
        relevant = tuple(item for item in authorized_parts if related(parts, item))
        if not relevant:
            frozen.append(
                FrozenSubtreeHashV1(
                    path=json_pointer(parts),
                    sha256=_subtree_hash(current),
                )
            )
            return
        if isinstance(current, dict):
            for key in sorted(current):
                child_parts = (*parts, str(key))
                if any(related(child_parts, item) for item in relevant):
                    visit(current[key], child_parts)
                else:
                    frozen.append(
                        FrozenSubtreeHashV1(
                            path=json_pointer(child_parts),
                            sha256=_subtree_hash(current[key]),
                        )
                    )
        elif isinstance(current, list):
            # Follow only authorized list elements. Hashing other indices
            # would make a legitimate remove operation appear to rewrite them.
            selected: set[int] = set()
            for item in relevant:
                if len(item) <= len(parts):
                    continue
                try:
                    selected.add(int(item[len(parts)]))
                except ValueError:
                    continue
            for index in sorted(selected):
                if 0 <= index < len(current):
                    visit(current[index], (*parts, str(index)))

    visit(baseline, ())
    return tuple(sorted(frozen, key=lambda item: item.path))


def _verify_repair_envelope_baseline(
    baseline: Any,
    envelope: RepairDiagnosticEnvelopeV2,
) -> None:
    if _subtree_hash(baseline) != envelope.baseline_sha256:
        raise RepairScopeViolation("", "stale-baseline")
    for frozen in envelope.frozen_subtree_hashes:
        try:
            value = pointer_get(baseline, frozen.path)
        except ValueError as exc:
            raise RepairScopeViolation(frozen.path, "frozen-subtree") from exc
        if _subtree_hash(value) != frozen.sha256:
            raise RepairScopeViolation(frozen.path, "frozen-subtree")


def _patch_parent(value: Any, pointer: str) -> tuple[Any, str]:
    parts = pointer_parts(pointer)
    if not parts:
        raise ValueError("a patch may not replace the parseable root object")
    return pointer_get(value, json_pointer(parts[:-1])), parts[-1]


def apply_repair_patch(
    baseline: Any,
    patch: RepairPatchV1,
    envelope: RepairDiagnosticEnvelopeV2,
) -> Any:
    """Apply exactly one authorized edit and verify every frozen subtree."""

    _verify_repair_envelope_baseline(baseline, envelope)
    if patch.path not in envelope.authorized_pointers:
        raise RepairScopeViolation(patch.path, "|".join(envelope.authorized_pointers))

    candidate = copy.deepcopy(baseline)
    parent, final = _patch_parent(candidate, patch.path)
    value_supplied = "value" in patch.model_fields_set
    if isinstance(parent, dict):
        exists = final in parent
        if patch.op == "add":
            if exists:
                raise ValueError("add patch target already exists")
            parent[final] = copy.deepcopy(patch.value)
        elif patch.op == "replace":
            if not exists:
                raise ValueError("replace patch target does not exist")
            parent[final] = copy.deepcopy(patch.value)
        else:
            if not exists:
                raise ValueError("remove patch target does not exist")
            del parent[final]
    elif isinstance(parent, list):
        if final == "-":
            if patch.op != "add":
                raise ValueError("only add may use the list append pointer")
            parent.append(copy.deepcopy(patch.value))
        else:
            try:
                index = int(final)
            except ValueError as exc:
                raise ValueError(f"non-integer list path {patch.path!r}") from exc
            if index < 0:
                raise ValueError(f"negative list path {patch.path!r}")
            if patch.op == "add":
                if index > len(parent):
                    raise ValueError(f"unknown list path {patch.path!r}")
                parent.insert(index, copy.deepcopy(patch.value))
            elif index >= len(parent):
                raise ValueError(f"unknown list path {patch.path!r}")
            elif patch.op == "replace":
                parent[index] = copy.deepcopy(patch.value)
            else:
                del parent[index]
    else:
        raise ValueError(f"path parent is not a container: {patch.path!r}")

    # The model cannot smuggle a value into remove through a manually-created
    # instance. Pydantic enforces this too; retaining the check here makes the
    # applicator independently safe at its public boundary.
    if patch.op == "remove" and value_supplied:
        raise ValueError("remove patch must omit value")
    for frozen in envelope.frozen_subtree_hashes:
        try:
            value = pointer_get(candidate, frozen.path)
        except ValueError as exc:
            raise RepairScopeViolation(frozen.path, patch.path) from exc
        if _subtree_hash(value) != frozen.sha256:
            raise RepairScopeViolation(frozen.path, patch.path)
    return candidate


def merge_subtree(value: Any, pointer: str, replacement: Any) -> Any:
    """Return a copied JSON value with exactly one subtree replaced."""
    if pointer == "":
        return copy.deepcopy(replacement)
    merged = copy.deepcopy(value)
    parts = pointer_parts(pointer)
    parent_pointer = json_pointer(parts[:-1])
    parent = pointer_get(merged, parent_pointer)
    final = parts[-1]
    if isinstance(parent, list):
        try:
            index = int(final)
        except ValueError as exc:
            raise ValueError(f"non-integer list path {pointer!r}") from exc
        if index < 0 or index >= len(parent):
            raise ValueError(f"unknown list path {pointer!r}")
        parent[index] = copy.deepcopy(replacement)
    elif isinstance(parent, dict):
        # Missing required fields may be supplied; unknown placement is
        # subsequently rejected by whole-object validation.
        parent[final] = copy.deepcopy(replacement)
    else:
        raise ValueError(f"path parent is not a container: {pointer!r}")
    return merged


_MISSING = object()


def _json_differences(
    baseline: Any,
    candidate: Any,
    loc: tuple[Any, ...] = (),
) -> list[str]:
    """Return deterministic, type-sensitive JSON pointers that changed."""

    if baseline is _MISSING or candidate is _MISSING:
        return [json_pointer(loc)]
    if type(baseline) is not type(candidate):
        return [json_pointer(loc)]
    if isinstance(baseline, dict):
        changed: list[str] = []
        for key in sorted(set(baseline) | set(candidate)):
            changed.extend(
                _json_differences(
                    baseline.get(key, _MISSING),
                    candidate.get(key, _MISSING),
                    (*loc, key),
                )
            )
        return changed
    if isinstance(baseline, list):
        changed = []
        for index in range(max(len(baseline), len(candidate))):
            changed.extend(
                _json_differences(
                    baseline[index] if index < len(baseline) else _MISSING,
                    candidate[index] if index < len(candidate) else _MISSING,
                    (*loc, index),
                )
            )
        return changed
    return [] if baseline == candidate else [json_pointer(loc)]


def enforce_repair_subtree(
    baseline: Any,
    candidate: Any,
    authorized_subtree_pointer: str,
) -> None:
    """Reject any parseable repair diff outside its authorized JSON pointer.

    Root replacement is intentionally not treated as broad semantic authority:
    callers invoke this only when a parseable baseline exists, so a root-scoped
    repair may preserve that baseline but may not rewrite it.  Syntax recovery
    from an unparseable response bypasses this check because there is no
    narrower value against which a deterministic diff can be computed.
    """

    differences = _json_differences(baseline, candidate)
    if not differences:
        return
    scope = authorized_subtree_pointer
    if scope:
        allowed_prefix = scope + "/"
        outside = next(
            (
                pointer
                for pointer in differences
                if pointer != scope and not pointer.startswith(allowed_prefix)
            ),
            None,
        )
        if outside is None:
            return
    else:
        outside = differences[0]
    raise RepairScopeViolation(outside, scope)


def _resolve_schema_node(node: Any, root: dict, *, array: bool) -> dict:
    """Resolve refs and nullable unions for one pointer traversal step."""

    current = node
    seen: set[str] = set()
    while isinstance(current, dict) and "$ref" in current:
        ref = str(current["$ref"])
        if ref in seen:
            return {}
        seen.add(ref)
        resolved: Any = root
        for part in ref.lstrip("#/").split("/"):
            resolved = resolved.get(part, {}) if isinstance(resolved, dict) else {}
        current = resolved
    if not isinstance(current, dict):
        return {}
    choices = current.get("anyOf") or current.get("oneOf") or ()
    if choices:
        if array:
            current = next(
                (
                    choice
                    for choice in choices
                    if isinstance(choice, dict)
                    and (choice.get("type") == "array" or "items" in choice)
                ),
                current,
            )
        else:
            current = next(
                (
                    choice
                    for choice in choices
                    if isinstance(choice, dict)
                    and (
                        choice.get("type") == "object"
                        or "properties" in choice
                        or "$ref" in choice
                    )
                ),
                current,
            )
        if current is not node:
            return _resolve_schema_node(current, root, array=array)
    return current


def _schema_at(schema: dict, loc: tuple[Any, ...]) -> dict:
    current: Any = schema
    for part in loc:
        if isinstance(part, int):
            current = _resolve_schema_node(current, schema, array=True)
            current = current.get("items", {})
        else:
            current = _resolve_schema_node(current, schema, array=False)
            current = current.get("properties", {}).get(str(part), {})
    current = _resolve_schema_node(current, schema, array=False)
    return current if isinstance(current, dict) else {}


def schema_at_pointer(schema: dict, pointer: str) -> dict:
    parts: list[Any] = []
    for part in pointer_parts(pointer):
        parts.append(int(part) if part.isdigit() else part)
    return _schema_at(schema, tuple(parts))


def minimal_skeleton(schema: dict, _root: dict | None = None) -> Any:
    """Create a syntax example from schema metadata, not task content."""
    root = schema if _root is None else _root
    if "$ref" in schema:
        current: Any = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            current = current.get(part, {}) if isinstance(current, dict) else {}
        if current is schema or not isinstance(current, dict):
            return None
        return minimal_skeleton(current, root)
    if "const" in schema:
        return schema["const"]
    if schema.get("enum"):
        return schema["enum"][0]
    any_of = schema.get("anyOf") or schema.get("oneOf")
    if any_of:
        branch = next((b for b in any_of if b.get("type") != "null"), any_of[0])
        return minimal_skeleton(branch, root)
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        required = set(schema.get("required") or ())
        return {
            key: minimal_skeleton(child, root)
            for key, child in schema.get("properties", {}).items()
            if key in required
        }
    if kind == "array":
        count = max(0, int(schema.get("minItems", 0)))
        return [minimal_skeleton(schema.get("items", {}), root) for _ in range(count)]
    if kind == "string":
        return "x" if int(schema.get("minLength", 0)) else ""
    if kind in {"integer", "number"}:
        return schema.get("minimum", 0)
    if kind == "boolean":
        return False
    return None


_SCRATCH_REFERENCE_HANDLE = re.compile(r"^(?:SCR|NEW)_[0-9]{3,}$")
_SCRATCH_SCALAR_REFERENCE_POINTER = re.compile(
    r"^/scratch_proposal/(?:links/[0-9]+/(?:from_ref|to_ref)"
    r"|revisions/[0-9]+/target_alias)$"
)
_SCRATCH_ARRAY_REFERENCE_POINTER = re.compile(
    r"^/scratch_proposal/(?:unresolved_questions/[0-9]+/related_refs"
    r"|cluster_suggestions/[0-9]+/member_refs)(?:/[0-9]+)?$"
)
_MAX_DIAGNOSTIC_LEGAL_HANDLES = 32


def _scratch_handle_kind(handle: str) -> str:
    if handle.startswith("SCR_"):
        return "scratch_block_handle"
    if handle.startswith("NEW_"):
        return "new_block_key"
    return "unknown"


def _handle_fields_from_error(error: Exception) -> dict[str, Any]:
    """Mirror a reference error's handle attributes into diagnostic fields.

    Reference errors that carry no handle state (or plain validation errors)
    contribute nothing; fields stay absent rather than inventing guidance.
    """

    rejected = getattr(error, "rejected_handle", None)
    observed = getattr(error, "observed_kind", None)
    required = tuple(getattr(error, "required_kinds", ()))
    legal = tuple(getattr(error, "legal_handles", ()))
    omission = getattr(error, "omission_allowed", None)
    return {
        "rejected_handle": rejected if isinstance(rejected, str) else None,
        "observed_handle_kind": observed if isinstance(observed, str) else None,
        "required_handle_kinds": required or None,
        "legal_handles": legal[:_MAX_DIAGNOSTIC_LEGAL_HANDLES] or None,
        "omission_or_unknown_legal": None if omission is None else bool(omission),
    }


def _scratch_reference_guidance(
    error: Exception,
    pointer: str,
    received: Any,
) -> dict[str, Any] | None:
    """Handle-aware guidance for one scratch-proposal reference failure.

    The v6 wire contract attaches its durable legal-handle state
    (``scratch_reference_context``: the visible SCR catalog plus the
    proposal's own NEW keys) to the validation error it re-raises.  Validity
    is decided entirely by the validators that raised ``error``; this only
    completes the diagnostic so a repair can use a legal handle or a legal
    omission instead of regex-guessing new invalid handles.
    """

    context = getattr(error, "scratch_reference_context", None)
    if not isinstance(context, dict):
        return None
    array_field = bool(_SCRATCH_ARRAY_REFERENCE_POINTER.fullmatch(pointer))
    scalar_field = bool(_SCRATCH_SCALAR_REFERENCE_POINTER.fullmatch(pointer))
    proposal_root = pointer == "/scratch_proposal"
    if not (array_field or scalar_field or proposal_root):
        return None
    new_keys = tuple(
        key for key in context.get("new_block_keys", ()) if isinstance(key, str)
    )
    scratch_handles = tuple(
        key for key in context.get("scratch_handles", ()) if isinstance(key, str)
    )
    revision_target = pointer.endswith("/target_alias")
    legal = scratch_handles if revision_target else (*new_keys, *scratch_handles)
    legal = tuple(dict.fromkeys(legal))[:_MAX_DIAGNOSTIC_LEGAL_HANDLES]
    required = (
        ("scratch_block_handle",)
        if revision_target
        else ("new_block_key", "scratch_block_handle")
    )
    rejected: str | None = None
    items = tuple(received) if isinstance(received, (list, tuple)) else (received,)
    for item in items:
        if not isinstance(item, str):
            continue
        if _SCRATCH_REFERENCE_HANDLE.fullmatch(item) is None or (
            item.startswith("NEW_") and item not in new_keys
        ):
            rejected = item[:128]
            break
    omission_legal = bool(array_field or proposal_root)
    if legal:
        instruction = "Use only a listed legal handle for this reference field."
    else:
        instruction = (
            "No legal handle exists for this reference field; do not invent one."
        )
    if omission_legal:
        instruction += (
            " Omission is legal: a remove operation at this path, or a replace "
            "that drops the offending entry, is a valid repair; never invent a "
            "handle to fill an optional reference."
        )
    return {
        "rejected_handle": rejected,
        "observed_handle_kind": (
            None if rejected is None else _scratch_handle_kind(rejected)
        ),
        "required_handle_kinds": required,
        "legal_handles": legal,
        "omission_or_unknown_legal": omission_legal,
        "instruction": instruction,
    }


def diagnostic_from_error(
    contract: str,
    error: Exception,
    schema: dict,
) -> RepairDiagnostic:
    if getattr(error, "code", "") == "REPAIR_SCOPE_VIOLATION":
        pointer = str(getattr(error, "pointer", ""))
        repair_scope = str(getattr(error, "repair_scope", ""))
        child_schema = (
            schema_at_pointer(schema, repair_scope) if repair_scope else schema
        )
        return RepairDiagnostic(
            contract=contract,
            path=pointer,
            error="repair changed JSON outside its authorized subtree",
            received=None,
            allowed=f"changes only at {repair_scope or '/'}",
            repair_scope=repair_scope,
            skeleton=minimal_skeleton(child_schema, schema),
        )
    if getattr(error, "code", "") == "MODEL_CONTROL_FIELD_FORBIDDEN":
        pointer = str(getattr(error, "pointer", ""))
        return RepairDiagnostic(
            contract=contract,
            path=pointer,
            error="MODEL_CONTROL_FIELD_FORBIDDEN",
            received=None,
            allowed="declared response-schema fields only",
            repair_scope=pointer,
            skeleton=None,
        )
    if getattr(error, "code", "") == "BRIDGE_COMPOSITION_INVALID":
        pointer = str(getattr(error, "pointer", ""))
        repair_scope = str(getattr(error, "repair_scope", pointer))
        child_schema = (
            schema_at_pointer(schema, repair_scope) if repair_scope else schema
        )
        allowed = "valid bridge rendering for the bound claim class"
        allowed_detail = getattr(error, "allowed_detail", None)
        if isinstance(allowed_detail, str) and allowed_detail.strip():
            allowed = f"{allowed_detail}; {allowed}"[:2_048]
        instruction = getattr(error, "instruction", None)
        return RepairDiagnostic(
            contract=contract,
            path=pointer,
            error=str(error)[:300],
            received=None,
            allowed=allowed,
            repair_scope=repair_scope,
            skeleton=minimal_skeleton(child_schema, schema),
            instruction=(
                instruction[:500]
                if isinstance(instruction, str) and instruction.strip()
                else None
            ),
        )
    reference_code = getattr(error, "code", "")
    if reference_code in {
        "SCRATCH_WIRE_REFERENCE_INVALID",
        "BRIDGE_WIRE_REFERENCE_INVALID",
    }:
        pointer = str(getattr(error, "pointer", ""))
        repair_scope = str(getattr(error, "repair_scope", pointer))
        child_schema = (
            schema_at_pointer(schema, repair_scope) if repair_scope else schema
        )
        rejected_handle = getattr(error, "rejected_handle", None)
        is_bridge_reference = reference_code == "BRIDGE_WIRE_REFERENCE_INVALID"
        if is_bridge_reference:
            required_kinds = tuple(getattr(error, "required_kinds", ()))
            legal_handles = tuple(getattr(error, "legal_handles", ()))
            omission_allowed = bool(getattr(error, "omission_allowed", False))
            allowed = (
                f"one of {list(legal_handles)!r}"
                if legal_handles
                else "no supplied handle is legal for this field"
            )
            instruction = "Use only a listed handle for this field."
            if omission_allowed:
                instruction += (
                    " Omission, unknown, or an uncovered requirement is legal; "
                    "do not invent evidence."
                )
        else:
            # Scratch reference errors carry the same handle attributes when
            # their raiser knows the legal set; absent attributes stay absent
            # instead of degrading to a bare pattern diagnostic.
            required_kinds = tuple(getattr(error, "required_kinds", ())) or None
            legal_handles = (
                tuple(getattr(error, "legal_handles", ()))[
                    :_MAX_DIAGNOSTIC_LEGAL_HANDLES
                ]
                or None
            )
            omission = getattr(error, "omission_allowed", None)
            omission_allowed = None if omission is None else bool(omission)
            if legal_handles:
                allowed = f"one of {list(legal_handles)!r}"
                instruction = "Use only a listed legal handle for this field."
                if omission_allowed:
                    instruction += (
                        " Omission is legal: removing the optional reference is "
                        "a valid repair; do not invent handles."
                    )
            else:
                allowed = "one supplied call-local handle or rendered-list index"
                instruction = None
        return RepairDiagnostic(
            contract=contract,
            path=pointer,
            error=reference_code,
            received=rejected_handle,
            allowed=allowed,
            repair_scope=repair_scope,
            skeleton=minimal_skeleton(child_schema, schema),
            rejected_handle=rejected_handle,
            observed_handle_kind=getattr(error, "observed_kind", None),
            required_handle_kinds=required_kinds,
            legal_handles=legal_handles,
            omission_or_unknown_legal=omission_allowed,
            instruction=instruction,
        )
    if isinstance(error, ValidationError) and error.errors():
        detail = error.errors(include_url=False)[0]
        loc = tuple(detail.get("loc") or ())
        path = json_pointer(loc)
        error_type = str(detail.get("type") or "validation_error")
        # An extra field is removed only by repairing its containing object.
        scope_loc = loc[:-1] if error_type == "extra_forbidden" else loc
        child_schema = _schema_at(schema, scope_loc)
        allowed_bits = []
        for key in ("type", "enum", "const", "pattern", "minimum", "maximum"):
            if key in child_schema:
                allowed_bits.append(f"{key}={child_schema[key]!r}")
        guidance = _scratch_reference_guidance(error, path, detail.get("input"))
        return RepairDiagnostic(
            contract=contract,
            path=path,
            error=str(detail.get("msg") or error_type),
            received=detail.get("input"),
            allowed=", ".join(allowed_bits),
            repair_scope=json_pointer(scope_loc),
            skeleton=minimal_skeleton(child_schema),
            **(guidance or {}),
        )
    return RepairDiagnostic(
        contract=contract,
        path="",
        error=str(error)[:300],
        received=None,
        allowed="complete JSON value",
        repair_scope="",
        skeleton=minimal_skeleton(schema),
        **_handle_fields_from_error(error),
    )


def _received_for_diagnostic(value: Any) -> Any:
    try:
        canonical_json(value)
    except (TypeError, ValueError):
        return repr(value)[:300]
    return value


def _allowed_at_pointer(schema: dict[str, Any], pointer: str) -> str:
    child = schema_at_pointer(schema, pointer) if pointer else schema
    allowed_bits: list[str] = []
    for key in (
        "type",
        "enum",
        "const",
        "pattern",
        "minimum",
        "maximum",
        "minItems",
        "maxItems",
    ):
        if key in child:
            allowed_bits.append(f"{key}={child[key]!r}")
    return ", ".join(allowed_bits)


def diagnostic_envelope_from_error(
    *,
    contract: str,
    error: Exception,
    schema: dict[str, Any],
    baseline: Any,
    root_authorized_pointers: tuple[str, ...] = (),
) -> RepairDiagnosticEnvelopeV2:
    """Compile field failures into exact, finite v6 patch authority.

    Pydantic locations become exact edit pointers. A model-level/root failure
    is not silently widened: its validator or caller must supply an explicit
    finite set of non-root pointers or the response is unrepairable.
    """

    explicit = tuple(sorted(set(root_authorized_pointers)))
    for pointer in explicit:
        _validate_json_pointer(pointer, allow_root=False)

    diagnostics: list[RepairDiagnosticV2] = []
    authorized: set[str] = set()
    if isinstance(error, ValidationError) and error.errors():
        for detail in error.errors(include_url=False):
            loc = tuple(
                part
                for part in (detail.get("loc") or ())
                if part not in {"__root__", "root"}
            )
            pointer = json_pointer(loc)
            code = str(detail.get("type") or "validation_error")
            if pointer:
                pointers = (pointer,)
            else:
                pointers = explicit
            if not pointers:
                raise UnrepairableDiagnosticError(
                    "object-wide validation error requires explicit authorized pointers"
                )
            authorized.update(pointers)
            operation = (
                "remove"
                if code == "extra_forbidden"
                else "add"
                if code == "missing"
                else "replace"
            )
            guidance = _scratch_reference_guidance(
                error, pointer, detail.get("input")
            )
            diagnostics.append(
                RepairDiagnosticV2(
                    path=pointer,
                    code=code,
                    message=str(detail.get("msg") or code)[:500],
                    received=_received_for_diagnostic(detail.get("input")),
                    allowed=(
                        f"operation={operation}"
                        + (
                            "; " + _allowed_at_pointer(schema, pointer)
                            if pointer and _allowed_at_pointer(schema, pointer)
                            else ""
                        )
                    ),
                    **(guidance or {}),
                )
            )
    else:
        supplied = tuple(getattr(error, "authorized_pointers", ())) or explicit
        pointer = str(
            getattr(error, "pointer", "")
            or getattr(error, "repair_scope", "")
        )
        pointers = tuple(sorted(set(supplied or ((pointer,) if pointer else ()))))
        if not pointers:
            raise UnrepairableDiagnosticError(
                "object-wide validation error requires explicit authorized pointers"
            )
        for item in pointers:
            _validate_json_pointer(item, allow_root=False)
        authorized.update(pointers)
        handle_fields = _handle_fields_from_error(error)
        if handle_fields["legal_handles"]:
            instruction = "Use only a listed legal handle for this field."
            if handle_fields["omission_or_unknown_legal"]:
                instruction += (
                    " Omission is legal: removing the optional reference is a "
                    "valid repair; do not invent handles."
                )
            handle_fields["instruction"] = instruction
        explicit_instruction = getattr(error, "instruction", None)
        if isinstance(explicit_instruction, str) and explicit_instruction.strip():
            handle_fields["instruction"] = explicit_instruction[:500]
        allowed = "; ".join(
            filter(None, (_allowed_at_pointer(schema, item) for item in pointers))
        )
        allowed_detail = getattr(error, "allowed_detail", None)
        if isinstance(allowed_detail, str) and allowed_detail.strip():
            allowed = (
                f"{allowed_detail}; {allowed}" if allowed else allowed_detail
            )[:2_048]
        diagnostics.append(
            RepairDiagnosticV2(
                path=pointer,
                code=str(getattr(error, "code", "validation_error"))[:128],
                message=(str(error).strip() or "contract validation failed")[:500],
                received=None,
                allowed=allowed,
                **handle_fields,
            )
        )

    ordered = tuple(sorted(authorized))
    return RepairDiagnosticEnvelopeV2(
        contract=contract,
        baseline_sha256=_subtree_hash(baseline),
        diagnostics=tuple(diagnostics),
        authorized_pointers=ordered,
        frozen_subtree_hashes=_frozen_subtree_hashes(baseline, ordered),
    )


def repair_patch_response_schema(
    envelope: RepairDiagnosticEnvelopeV2,
) -> dict[str, Any]:
    """Closed provider schema for one patch at one envelope-authorized path."""

    def branch(operation: Literal["add", "remove", "replace"]) -> dict[str, Any]:
        properties: dict[str, Any] = {
            "schema": {"const": "repair.patch.v1", "type": "string"},
            "op": {"const": operation, "type": "string"},
            "path": {
                "enum": list(envelope.authorized_pointers),
                "type": "string",
            },
        }
        required = ["schema", "op", "path"]
        if operation != "remove":
            properties["value"] = {}
            required.append("value")
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": required,
        }

    return {"oneOf": [branch("add"), branch("remove"), branch("replace")]}


def patch_repair_prompt(
    baseline: Any,
    envelope: RepairDiagnosticEnvelopeV2,
) -> str:
    """Render one v6 patch request without reopening valid subtrees."""

    payload = envelope.model_dump(mode="json", by_alias=True, exclude_none=True)
    return (
        "Return exactly one repair.patch.v1 JSON object. Choose one authorized "
        "path and one add, remove, or replace operation. Do not return the "
        "surrounding object. Frozen subtree hashes are immutable. If several "
        "diagnostics are listed, repair only one now; separate later attempts "
        "will address the remaining diagnostics.\n\n"
        f"CURRENT JSON:\n{json.dumps(baseline, sort_keys=True, ensure_ascii=False)}\n\n"
        "DIAGNOSTIC ENVELOPE:\n"
        f"{json.dumps(payload, sort_keys=True, ensure_ascii=False)}"
    )


def whole_object_repair_prompt(
    invalid_json: str,
    diagnostic: RepairDiagnostic,
) -> str:
    """Attempt 1: reduced validation feedback, no operational vocabulary."""
    payload = diagnostic.model_dump(exclude_none=True)
    return (
        "The JSON value below is invalid for this output contract. Correct only "
        "the reported contract error and preserve every unrelated value. Return "
        "ONLY the complete corrected JSON value.\n\n"
        f"INVALID JSON:\n{invalid_json}\n\n"
        f"DIAGNOSTIC:\n{json.dumps(payload, sort_keys=True, ensure_ascii=False)}"
    )


def subtree_repair_prompt(
    invalid_value: Any,
    diagnostic: RepairDiagnostic,
) -> str:
    """Attempt 2: ask for only the smallest invalid field/subtree."""
    payload = diagnostic.model_dump(exclude_none=True)
    return (
        f"Repair only the JSON value at {diagnostic.repair_scope or '/'} for the "
        "contract error below. Return ONLY the replacement JSON value for that "
        "field or subtree, not the surrounding object.\n\n"
        f"CURRENT JSON:\n{json.dumps(invalid_value, ensure_ascii=False)}\n\n"
        f"DIAGNOSTIC:\n{json.dumps(payload, sort_keys=True, ensure_ascii=False)}"
    )


@dataclass(frozen=True)
class V6RepairTurn:
    """One initial, syntax-retry, or patch-only v6 provider request."""

    attempt: int
    request: str
    response_schema: dict[str, Any]
    mode: Literal["initial", "whole_object_syntax", "patch"]
    diagnostic_envelope: RepairDiagnosticEnvelopeV2 | None = None
    authorized_pointers: tuple[str, ...] = ()
    repair_scope: str = ""
    validation_path: str = ""


# A v6 patch edits exactly one authorized pointer, so a turn with several
# independent field failures needs one repair per pointer.  Four covers the
# multi-pointer failures observed live (four handle-pattern mistakes in one
# conjecturer.turn.v6 output) while staying finite; each contract's manifest
# grant sets the actual, usually smaller, ceiling.
V6_PATCH_REPAIR_CEILING = 4


class V6PatchRepairSession:
    """Initial call plus a finite run of independent, exact JSON patch repairs.

    A parseable response is never regenerated wholesale. The sole complete
    object retry is available only when no JSON baseline could be parsed; as
    soon as a baseline exists, every remaining turn returns one
    :class:`RepairPatchV1` and the harness applies it deterministically.  The
    manifest grant supplies ``retry_max``; :data:`V6_PATCH_REPAIR_CEILING`
    bounds it here.
    """

    def __init__(
        self,
        *,
        contract: str,
        schema: dict[str, Any],
        initial_request: str,
        retry_max: int = 2,
        root_authorized_pointers: tuple[str, ...] = (),
    ) -> None:
        self.contract = contract
        self.schema = copy.deepcopy(schema)
        self.initial_request = initial_request
        self.max_attempt = min(max(0, int(retry_max)), V6_PATCH_REPAIR_CEILING)
        self.root_authorized_pointers = tuple(
            sorted(set(root_authorized_pointers))
        )
        for pointer in self.root_authorized_pointers:
            _validate_json_pointer(pointer, allow_root=False)
        self.invalid_text = ""
        self.invalid_value: Any = None
        self.invalid_value_parseable = False
        self.diagnostic_envelope: RepairDiagnosticEnvelopeV2 | None = None
        self.syntax_diagnostic: RepairDiagnostic | None = None
        self.last_error: Exception | None = None
        self.whole_object_retry_used = False
        self._pending_candidate: Any = _MISSING
        # Digests of every rejected candidate, to catch a repair that cycles.
        self._rejected_digests: dict[str, int] = {}
        self.oscillation: str = ""

    @property
    def attempt_count(self) -> int:
        return self.max_attempt + 1

    def turn(self, attempt: int) -> V6RepairTurn:
        if attempt < 0 or attempt > self.max_attempt:
            raise IndexError(
                f"repair attempt {attempt} outside bounded range 0..{self.max_attempt}"
            )
        if attempt == 0:
            return V6RepairTurn(
                attempt=attempt,
                request=self.initial_request,
                response_schema=self.schema,
                mode="initial",
            )
        if self.invalid_value_parseable:
            if self.diagnostic_envelope is None:
                raise UnrepairableDiagnosticError(
                    "parseable invalid response has no finite repair envelope"
                )
            envelope = self.diagnostic_envelope
            first_path = envelope.diagnostics[0].path
            return V6RepairTurn(
                attempt=attempt,
                request=patch_repair_prompt(self.invalid_value, envelope),
                response_schema=repair_patch_response_schema(envelope),
                mode="patch",
                diagnostic_envelope=envelope,
                authorized_pointers=envelope.authorized_pointers,
                repair_scope=(
                    envelope.authorized_pointers[0]
                    if len(envelope.authorized_pointers) == 1
                    else ""
                ),
                validation_path=first_path,
            )
        if self.whole_object_retry_used:
            raise SchemaExhaustedError(
                "schema_exhausted: syntax retry did not produce a parseable baseline"
            )
        if self.syntax_diagnostic is None:
            raise RuntimeError("repair requested before a validation failure")
        self.whole_object_retry_used = True
        return V6RepairTurn(
            attempt=attempt,
            request=whole_object_repair_prompt(
                self.invalid_text,
                self.syntax_diagnostic,
            ),
            response_schema=self.schema,
            mode="whole_object_syntax",
            validation_path=self.syntax_diagnostic.path,
        )

    def candidate_from_raw(self, turn: V6RepairTurn, raw: str) -> Any:
        """Parse a response and apply a patch without accepting it semantically."""

        self._pending_candidate = _MISSING
        if turn.mode in {"initial", "whole_object_syntax"}:
            parsed = parse_one_json_value(raw)
            self.invalid_text = parsed.text
            self._pending_candidate = parsed.value
            return parsed.value
        if not self.invalid_value_parseable or turn.diagnostic_envelope is None:
            raise UnrepairableDiagnosticError("patch turn has no parseable baseline")
        patch_value = tolerant_patch_value(
            parse_one_json_value(raw).value,
            turn.diagnostic_envelope,
        )
        patch = RepairPatchV1.model_validate(patch_value)
        candidate = apply_repair_patch(
            self.invalid_value,
            patch,
            turn.diagnostic_envelope,
        )
        self._pending_candidate = candidate
        return candidate

    def note_invalid(
        self,
        turn: V6RepairTurn,
        raw: str,
        error: Exception,
        *,
        truncated: bool = False,
    ) -> RepairDiagnosticEnvelopeV2 | RepairDiagnostic:
        """Record rejection and compile the next finite repair authority."""

        self.last_error = error
        candidate_ready = self._pending_candidate is not _MISSING
        if candidate_ready:
            self.invalid_value = copy.deepcopy(self._pending_candidate)
            self.invalid_value_parseable = True
            self.invalid_text = json.dumps(
                self.invalid_value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        elif turn.mode in {"initial", "whole_object_syntax"}:
            try:
                parsed = parse_one_json_value(raw)
            except ValueError:
                self.invalid_text = raw
                self.invalid_value_parseable = False
            else:
                self.invalid_text = parsed.text
                self.invalid_value = parsed.value
                self.invalid_value_parseable = True
                candidate_ready = True

        if self.invalid_value_parseable and candidate_ready:
            self._note_repeated_state(turn)
            envelope = diagnostic_envelope_from_error(
                contract=self.contract,
                error=error,
                schema=self.schema,
                baseline=self.invalid_value,
                root_authorized_pointers=self.root_authorized_pointers,
            )
            if truncated:
                first = envelope.diagnostics[0]
                shortened = first.model_copy(
                    update={
                        "message": (
                            "output hit the length limit; make the authorized value "
                            "more compact: " + first.message
                        )[:500]
                    }
                )
                envelope = envelope.model_copy(
                    update={"diagnostics": (shortened, *envelope.diagnostics[1:])}
                )
            self.diagnostic_envelope = envelope
            return envelope

        if turn.mode == "patch" and self.diagnostic_envelope is not None:
            # Invalid patch syntax/scope consumes the attempt but cannot widen
            # or replace the already-bound baseline authority.
            return self.diagnostic_envelope

        diagnostic = diagnostic_from_error(self.contract, error, self.schema)
        if truncated:
            diagnostic = diagnostic.model_copy(
                update={
                    "error": (
                        "output hit the length limit and did not contain one complete "
                        "JSON value: " + diagnostic.error
                    )[:500]
                }
            )
        self.syntax_diagnostic = diagnostic
        return diagnostic

    def _note_repeated_state(self, turn: V6RepairTurn) -> None:
        """Record a rejected candidate and detect a repair that has cycled.

        Observed live (run-bc3e8797b3e0609eddb324299c8257bd): a scratch link's
        `to_ref` had NO legal value — the response declared one new block, so
        every target was either that block (a self-link) or an undeclared key.
        The model alternated between the two invalid values across four
        attempts, because each diagnostic names only the violation of the state
        the document is currently in, so patching away the reported violation
        lands it in the other one. The budget drained and the seat exhausted
        its smallest authorized contract, discarding an answer it had already
        written.

        Detection RECORDS the loop; it deliberately does not cut the attempts
        short. A repeated state is evidence of non-convergence, not proof of
        it, and `test_doctor_two_ceiling_allows_second_required_repair` is the
        standing counterexample: a no-op patch reproduces the rejected document
        and the NEXT attempt removes the offending field and succeeds. Stopping
        on the repeat would forfeit a granted repair that demonstrably works.

        What the loop costs is legibility, and that is what this buys back. On
        exhaustion the recorded reason now names the repeat and its pointer
        instead of echoing whichever validation error happened to come last, so
        `run-bc3e8797b3e0609eddb324299c8257bd` would have said the authorized
        value was unsatisfiable rather than leaving that to be reconstructed
        from blobs.

        The detection guesses nothing: the equality is exact, over the
        canonical form of the whole candidate, so a repair converging through
        distinct states is never flagged.
        """

        digest = hashlib.sha256(
            json.dumps(
                self.invalid_value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        first_seen = self._rejected_digests.get(digest)
        if first_seen is None:
            self._rejected_digests[digest] = turn.attempt
            return
        pointer = turn.validation_path or (
            turn.authorized_pointers[0] if turn.authorized_pointers else ""
        )
        self.oscillation = (
            "repair_oscillation: attempt "
            f"{turn.attempt} restored the candidate already rejected at attempt "
            f"{first_seen}"
            + (f" while repairing {pointer}" if pointer else "")
            + "; the authorized value is likely unsatisfiable by patching"
        )

    def exhaustion_error(self, *, spend=None) -> SchemaExhaustedError:
        message = str(self.last_error).strip() if self.last_error is not None else ""
        # A detected loop is the more useful cause than whichever validation
        # error happened to come last, so it leads; the last error is kept
        # after it rather than replaced.
        if self.oscillation:
            message = f"{self.oscillation}; last error: {message}" if message else self.oscillation
        return SchemaExhaustedError(
            "schema_exhausted"
            + (f": {message[:500]}" if message else ""),
            spend=spend,
        )


class BoundedRepairSession:
    """State machine for W4's initial + whole-object + subtree protocol.

    This class deliberately performs no I/O and has no endpoint, routing,
    logging, or budget authority.  A caller asks for the next :class:`RepairTurn`,
    sends that exact request on its already-frozen route, obtains a candidate
    with :meth:`candidate_from_raw`, and either accepts it or records the
    validation failure with :meth:`note_invalid`.  The same object can
    therefore drive DeepReason's ``LLMAdapter`` and MiniReason's small call
    loop while each engine retains its own durable event representation.
    """

    def __init__(
        self,
        *,
        contract: str,
        schema: dict[str, Any],
        initial_request: str,
        retry_max: int = 2,
        enforce_scope: bool = False,
    ) -> None:
        self.contract = contract
        self.schema = schema
        self.initial_request = initial_request
        # RETRY_MAX is a ceiling.  The normative transport exposes exactly
        # two repair forms and never opens a fourth provider call.
        self.max_attempt = min(max(0, int(retry_max)), 2)
        # Historical v1-v3 transports keep their original whole-object
        # correction behavior. The migrated active/v2 boundaries opt into
        # immutable subtree enforcement when their authority contract can
        # durably account for it.
        self.enforce_scope = bool(enforce_scope)
        self.diagnostic: RepairDiagnostic | None = None
        self.invalid_text = ""
        self.invalid_value: Any = None
        self.invalid_value_parseable = False
        self.last_error: Exception | None = None

    @property
    def attempt_count(self) -> int:
        """Maximum provider completions this session may consume."""

        return self.max_attempt + 1

    def turn(self, attempt: int) -> RepairTurn:
        """Return the exact request and constrained schema for ``attempt``."""

        if attempt < 0 or attempt > self.max_attempt:
            raise IndexError(
                f"repair attempt {attempt} outside bounded range 0..{self.max_attempt}"
            )
        if attempt == 0:
            return RepairTurn(
                attempt=attempt,
                request=self.initial_request,
                response_schema=self.schema,
            )
        if self.diagnostic is None:
            raise RuntimeError("repair requested before a validation failure")
        if attempt == 1:
            return RepairTurn(
                attempt=attempt,
                request=whole_object_repair_prompt(
                    self.invalid_text,
                    self.diagnostic,
                ),
                response_schema=self.schema,
                repair_scope=self.diagnostic.repair_scope,
                validation_path=self.diagnostic.path,
            )

        scope = self.diagnostic.repair_scope
        try:
            current = pointer_get(self.invalid_value, scope)
        except (TypeError, ValueError):
            # A missing required OBJECT field is precisely the local value we
            # need: keep its pointer, render CURRENT JSON as null, and let
            # merge_subtree insert the returned value. Reset to root only when
            # the parent path is unavailable or cannot accept that field.
            parts = pointer_parts(scope)
            try:
                parent = pointer_get(
                    self.invalid_value,
                    json_pointer(parts[:-1]),
                )
            except (TypeError, ValueError):
                parent = None
            if parts and isinstance(parent, dict):
                current = None
            else:
                scope = ""
                current = self.invalid_value
        if scope != self.diagnostic.repair_scope:
            self.diagnostic = self.diagnostic.model_copy(
                update={"repair_scope": scope}
            )
        return RepairTurn(
            attempt=attempt,
            request=subtree_repair_prompt(current, self.diagnostic),
            response_schema=schema_at_pointer(self.schema, scope) or {},
            repair_scope=scope,
            validation_path=self.diagnostic.path,
        )

    def candidate_from_raw(self, turn: RepairTurn, raw: str) -> Any:
        """Parse ``raw`` and deterministically apply a subtree replacement."""

        parsed = parse_one_json_value(raw)
        if turn.attempt == 0:
            # Keep the normalized text solely for the next model-facing
            # repair request; the caller separately stores the exact raw.
            self.invalid_text = parsed.text
            self.invalid_value = parsed.value
            self.invalid_value_parseable = True
            return parsed.value
        if turn.attempt == 1:
            if self.enforce_scope and self.invalid_value_parseable:
                enforce_repair_subtree(
                    self.invalid_value,
                    parsed.value,
                    turn.repair_scope,
                )
            self.invalid_text = parsed.text
            self.invalid_value = parsed.value
            self.invalid_value_parseable = True
            return parsed.value
        candidate = merge_subtree(
            self.invalid_value,
            turn.repair_scope,
            parsed.value,
        )
        if self.enforce_scope and self.invalid_value_parseable:
            enforce_repair_subtree(
                self.invalid_value,
                candidate,
                turn.repair_scope,
            )
        return candidate

    def note_invalid(
        self,
        turn: RepairTurn,
        raw: str,
        error: Exception,
        *,
        truncated: bool = False,
    ) -> RepairDiagnostic:
        """Record one failed validation and return its reduced diagnostic."""

        self.last_error = error
        diagnostic = diagnostic_from_error(self.contract, error, self.schema)
        if turn.attempt < 2 and not isinstance(error, RepairScopeViolation):
            # ``candidate_from_raw`` normally captured this.  Reparse here so
            # normalization failures still retain their exact text for the
            # whole-object repair while never inventing a JSON value.
            try:
                parsed = parse_one_json_value(raw)
                self.invalid_text = parsed.text
                self.invalid_value = parsed.value
                self.invalid_value_parseable = True
            except ValueError:
                self.invalid_text = raw
        if truncated:
            message = (
                "your output hit the length limit and was CUT OFF mid-JSON. "
                "Respond MORE COMPACTLY: fewer/shorter items, terse strings, "
                "same schema. Original error: " + diagnostic.error
            )[:500]
            diagnostic = diagnostic.model_copy(update={"error": message})
        self.diagnostic = diagnostic
        return diagnostic

    def note_control_invalid(
        self,
        error: Exception,
        sanitized_value: Any,
    ) -> RepairDiagnostic:
        """Record a control-field failure without reflecting it in a pack.

        The returned diagnostic is the exact process/audit diagnostic.  The
        session retains a separate root-scoped, vocabulary-neutral diagnostic
        and sanitized value for the next model-facing repair turn.  Neither is
        eligible for validation or canonical compilation.
        """
        self.last_error = error
        logged_diagnostic = diagnostic_from_error(
            self.contract,
            error,
            self.schema,
        )
        self.invalid_value = copy.deepcopy(sanitized_value)
        self.invalid_value_parseable = True
        self.invalid_text = json.dumps(
            sanitized_value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        self.diagnostic = RepairDiagnostic(
            contract=self.contract,
            path="",
            error="response contains a field outside the declared schema",
            received=None,
            allowed="declared response-schema fields only",
            repair_scope="",
            skeleton=minimal_skeleton(self.schema),
        )
        return logged_diagnostic
