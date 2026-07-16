"""Semantics-preserving JSON normalization and bounded local repair helpers.

This module is deliberately transport-only.  It never selects a route,
changes policy, or manufactures a substantive field.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError


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


def strip_json_fence(raw: str) -> str:
    """Remove one surrounding markdown fence and nothing inside it."""
    match = _FENCE.match(raw)
    return match.group("body") if match else raw.strip()


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
    for start, char in enumerate(text):
        if char not in "{[":
            continue
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            continue
        if text[end:].strip():
            raise ValueError("multiple top-level JSON values or trailing content")
        return ParsedJSON(text[start:end], value)
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
        required_kinds = (
            tuple(getattr(error, "required_kinds", ()))
            if is_bridge_reference
            else None
        )
        legal_handles = (
            tuple(getattr(error, "legal_handles", ()))
            if is_bridge_reference
            else None
        )
        omission_allowed = (
            bool(getattr(error, "omission_allowed", False))
            if is_bridge_reference
            else None
        )
        if reference_code == "BRIDGE_WIRE_REFERENCE_INVALID":
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
        return RepairDiagnostic(
            contract=contract,
            path=path,
            error=str(detail.get("msg") or error_type),
            received=detail.get("input"),
            allowed=", ".join(allowed_bits),
            repair_scope=json_pointer(scope_loc),
            skeleton=minimal_skeleton(child_schema),
        )
    return RepairDiagnostic(
        contract=contract,
        path="",
        error=str(error)[:300],
        received=None,
        allowed="complete JSON value",
        repair_scope="",
        skeleton=minimal_skeleton(schema),
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
    ) -> None:
        self.contract = contract
        self.schema = schema
        self.initial_request = initial_request
        # RETRY_MAX is a ceiling.  The normative transport exposes exactly
        # two repair forms and never opens a fourth provider call.
        self.max_attempt = min(max(0, int(retry_max)), 2)
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
            if self.invalid_value_parseable:
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
        if self.invalid_value_parseable:
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
