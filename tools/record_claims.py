#!/usr/bin/env python3
"""Universal statements about what a run DID, tested against its record.

A claim is a universal statement over the run roots supplied. A ``never``
claim is refuted by one root where its condition holds; an ``always`` claim by
one where it does not. A claim no supplied root refutes is
``UNREFUTED_FOR_DECLARED_SCOPE``: not a proof and not a confirmation, because
the scope is exactly the roots supplied and the next root may refute it.

Every survival also carries a STANDING. A claim whose refuting condition held
on no supplied root at all -- in scope or out of it -- names a measure code, an
object kind or a status value that no record ever carried, so the records could
not have refuted it whatever the run did. That is reported as
``NOT_SHOWN_ABLE_TO_FAIL`` rather than being left for the reader to work out.

This is NOT a gate, a status, or a score. It writes nothing into any root, it
changes nothing, and it imports nothing from ``deepreason`` -- so no path
exists by which it could. It exits non-zero only when it cannot do its job.

The shape is adopted from the operator's other harness (h-EPI,
``src/creib/forge/conformance/claims.py``); the vocabulary is DeepReason's own.
``docs/CLAIMS_SCHEMA.md`` is the claims file's contract.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

SCHEMA_VERSION = "deepreason.record-claims.v1"
CLAIM_KINDS = ("never", "always")
STATUS_REFUTED = "REFUTED"
STATUS_UNREFUTED = "UNREFUTED_FOR_DECLARED_SCOPE"
STATUS_NOT_TESTED = "NOT_TESTED"
STANDING_SHOWN = "SHOWN_ABLE_TO_FAIL"
STANDING_NOT_SHOWN = "NOT_SHOWN_ABLE_TO_FAIL"

MAX_REFUTING_SHOWN = 5

# The record's own rule names, by VALUE, copied from
# `src/deepreason/ontology/event.py::Rule`. They are copied rather than
# imported because this tool must not import the harness: an import is a code
# path into the package that writes records, and the read-only guarantee is
# worth more than the coupling. `tests/test_record_claims.py` asserts the two
# lists agree, so a rule added there fails a test rather than silently making
# a claim about it unwritable.
EVENT_RULES = (
    "Conj",
    "Crit",
    "Adj",
    "Spawn",
    "Refl",
    "Register",
    "Merge",
    "Measure",
    "Reveal",
    "Reseed",
    "Scratch",
    "Bridge",
    "ConjectureTurn",
    "Control",
    "Capability",
)

CLAIM_ID = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")

SCOPE_KEYS = {
    "run_ids": "run_id",
    "root_names": "__root_name__",
    "states": "state",
    "stop_reasons": "stop_reason",
    "workloads": "workload",
}

COMPARISONS = (
    "eq",
    "ne",
    "in",
    "not_in",
    "contains",
    "present",
    "absent",
    "gt",
    "gte",
    "lt",
    "lte",
)

NON_INDUCTIVE_LIMIT = (
    "A claim no supplied record refuted is unrefuted for exactly those "
    "records. Survival is not confirmation, counts are of records and imply "
    "no ranking, and nothing here treats a survival as evidence for anything."
)

NOT_SHOWN_SENTENCE = (
    "the refuting condition held on no supplied root, in or out of scope; "
    "this check has not been shown able to fail, and the survival should be "
    "read accordingly"
)


class ClaimsError(Exception):
    """A claims file, or a root, that this tool refuses to guess about."""


# ---------------------------------------------------------------------------
# the record
# ---------------------------------------------------------------------------


class RunRecord:
    """One run root, read lazily and never written.

    Only what a claim asks for is opened: `run-status.json` always (it carries
    the root's identity and the scope fields), `log.jsonl` on the first event
    question, and one `objects/<kind>/` directory per kind a condition names.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.name = root.name
        status_path = root / "run-status.json"
        if not status_path.is_file():
            raise ClaimsError(f"{root}: no run-status.json (not a run root)")
        try:
            self.status = json.loads(status_path.read_text())
        except (OSError, ValueError) as exc:
            raise ClaimsError(f"{root}: cannot read run-status.json: {exc}") from exc
        if not isinstance(self.status, dict):
            raise ClaimsError(f"{root}: run-status.json is not an object")
        self.run_id = str(self.status.get("run_id") or root.name)
        self._events: list[dict[str, Any]] | None = None
        self._objects: dict[str, list[tuple[str, Any]]] = {}

    # -- reading ----------------------------------------------------------

    @property
    def events(self) -> list[dict[str, Any]]:
        if self._events is None:
            path = self.root / "log.jsonl"
            events: list[dict[str, Any]] = []
            if path.is_file():
                try:
                    with path.open() as handle:
                        for number, line in enumerate(handle):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                event = json.loads(line)
                            except ValueError as exc:
                                raise ClaimsError(
                                    f"{self.root}: log.jsonl line {number + 1}: {exc}"
                                ) from exc
                            if isinstance(event, dict):
                                events.append(event)
                except OSError as exc:
                    raise ClaimsError(f"{self.root}: cannot read log.jsonl: {exc}") from exc
            self._events = events
        return self._events

    def objects(self, kind: str) -> list[tuple[str, Any]]:
        """(<file stem>, <the object's `data`>) for every record of one kind.

        A kind the root does not carry is an empty list, not an error: roots
        legitimately differ in which kinds they hold, and a claim about a kind
        absent everywhere is caught by the standing, not by a crash.
        """
        if kind not in self._objects:
            directory = self.root / "objects" / kind
            found: list[tuple[str, Any]] = []
            if directory.is_dir():
                for path in sorted(directory.iterdir()):
                    if path.suffix != ".json":
                        continue
                    try:
                        raw = json.loads(path.read_text())
                    except (OSError, ValueError) as exc:
                        raise ClaimsError(f"{path}: {exc}") from exc
                    data = raw.get("data") if isinstance(raw, dict) else None
                    found.append((path.stem, data if data is not None else raw))
            self._objects[kind] = found
        return self._objects[kind]

    def scope_value(self, field: str) -> Any:
        if field == "__root_name__":
            return self.name
        return self.status.get(field)

    def describe(self) -> str:
        state = self.status.get("state")
        stop = self.status.get("stop_reason")
        return f"{self.run_id}  {self.root}  state={state} stop_reason={stop}"


# ---------------------------------------------------------------------------
# paths and operators, for the `object` predicate
# ---------------------------------------------------------------------------


def _resolve_path(value: Any, segments: Sequence[str]) -> list[Any]:
    """Every value a dotted path with `[]` list steps reaches. Missing = none."""

    if not segments:
        return [value]
    head, rest = segments[0], segments[1:]
    if head == "[]":
        if not isinstance(value, list):
            return []
        out: list[Any] = []
        for item in value:
            out.extend(_resolve_path(item, rest))
        return out
    if isinstance(value, dict) and head in value:
        return _resolve_path(value[head], rest)
    return []


def _split_path(path: str, where: str) -> tuple[str, list[str]]:
    quantifier = "any"
    if path.startswith("any:"):
        path = path[len("any:") :]
    elif path.startswith("every:"):
        quantifier = "every"
        path = path[len("every:") :]
    if not path:
        raise ClaimsError(f"{where}: empty path")
    segments: list[str] = []
    for part in path.split("."):
        while part.endswith("[]"):
            part = part[:-2]
            if not part:
                raise ClaimsError(f"{where}: path segment {path!r} is only '[]'")
            segments.append(part)
            segments.append("[]")
            part = ""
        if part:
            segments.append(part)
    if not segments:
        raise ClaimsError(f"{where}: empty path {path!r}")
    return quantifier, segments


def _compare(op: str, value: Any, expected: Any) -> bool:
    if op == "eq":
        return value == expected
    if op == "ne":
        return value != expected
    if op == "in":
        return isinstance(expected, list) and value in expected
    if op == "not_in":
        return isinstance(expected, list) and value not in expected
    if op == "contains":
        if isinstance(value, str) and isinstance(expected, str):
            return expected in value
        if isinstance(value, (list, tuple)):
            return expected in value
        return False
    if op in ("gt", "gte", "lt", "lte"):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if isinstance(expected, bool) or not isinstance(expected, (int, float)):
            return False
        return {
            "gt": value > expected,
            "gte": value >= expected,
            "lt": value < expected,
            "lte": value <= expected,
        }[op]
    raise ClaimsError(f"unknown operator {op!r}")


def _clause(clause: Any, where: str) -> Callable[[Any], bool]:
    if not isinstance(clause, list) or len(clause) != 3:
        raise ClaimsError(f"{where}: a where clause is [path, op, value], got {clause!r}")
    path, op, expected = clause
    if not isinstance(path, str):
        raise ClaimsError(f"{where}: path must be a string, got {path!r}")
    if op not in COMPARISONS:
        raise ClaimsError(f"{where}: unknown operator {op!r}; known: {list(COMPARISONS)}")
    quantifier, segments = _split_path(path, where)

    def test(data: Any) -> bool:
        values = _resolve_path(data, segments)
        if op == "present":
            if not isinstance(expected, bool):
                raise ClaimsError(f"{where}: 'present' takes true or false")
            return bool(values) is expected
        if op == "absent":
            if not isinstance(expected, bool):
                raise ClaimsError(f"{where}: 'absent' takes true or false")
            return (not values) is expected
        if quantifier == "every":
            # Vacuously true on an empty resolution -- stated in
            # docs/CLAIMS_SCHEMA.md, because it is a place a claim can survive
            # without its author meaning it to.
            return all(_compare(op, value, expected) for value in values)
        return any(_compare(op, value, expected) for value in values)

    return test


# ---------------------------------------------------------------------------
# conditions
# ---------------------------------------------------------------------------

# A predicate answers one root and returns (holds, locators). Locators point
# into the record that made it hold, so a refutation names its counterexample.
Predicate = Callable[[RunRecord], tuple[bool, list[str]]]


def _one_key(raw: Any, where: str) -> tuple[str, Any]:
    if not isinstance(raw, dict):
        raise ClaimsError(f"{where}: a condition is an object, got {type(raw).__name__}")
    if len(raw) != 1:
        raise ClaimsError(f"{where}: a condition has exactly one key, got {sorted(raw)}")
    return next(iter(raw.items()))


def _min_count(spec: dict[str, Any], where: str) -> int:
    value = spec.get("min_count", 1)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ClaimsError(f"{where}.min_count must be an integer >= 1, got {value!r}")
    return value


def _known_keys(spec: dict[str, Any], allowed: Iterable[str], where: str) -> None:
    extra = sorted(set(spec) - set(allowed))
    if extra:
        raise ClaimsError(f"{where}: unknown key(s) {extra}; known: {sorted(allowed)}")


def compile_condition(raw: Any, where: str = "condition") -> Predicate:
    """One condition object into a predicate. Fail closed on anything unknown.

    An unrecognised key RAISES rather than evaluating to false: a typo that
    quietly becomes a survival is the failure mode this whole instrument
    exists to make visible.
    """

    key, value = _one_key(raw, where)

    if key in ("all_of", "any_of"):
        if not isinstance(value, list) or not value:
            raise ClaimsError(f"{where}.{key} must be a non-empty list")
        parts = [compile_condition(item, f"{where}.{key}[{i}]") for i, item in enumerate(value)]

        def nested(record: RunRecord) -> tuple[bool, list[str]]:
            locators: list[str] = []
            results = []
            for part in parts:
                holds, found = part(record)
                results.append(holds)
                if holds:
                    locators.extend(found)
            holds = all(results) if key == "all_of" else any(results)
            return holds, locators if holds else []

        return nested

    if key == "not":
        inner = compile_condition(value, f"{where}.not")

        def negated(record: RunRecord) -> tuple[bool, list[str]]:
            holds, _ = inner(record)
            # A negation's witness is an absence; there is nothing in the
            # record to point at, so it names none rather than pointing at
            # something that is not the reason.
            return (not holds), []

        return negated

    if key == "status":
        if not isinstance(value, dict):
            raise ClaimsError(f"{where}.status must be an object")
        _known_keys(value, ("field", *COMPARISONS), f"{where}.status")
        field = value.get("field")
        if not isinstance(field, str) or not field:
            raise ClaimsError(f"{where}.status.field must be a non-empty string")
        ops = [op for op in COMPARISONS if op in value]
        if len(ops) != 1:
            raise ClaimsError(
                f"{where}.status takes exactly one comparison, got {ops or 'none'}"
            )
        op = ops[0]
        expected = value[op]
        clause = _clause([field, op, expected], f"{where}.status")

        def status(record: RunRecord) -> tuple[bool, list[str]]:
            if not clause(record.status):
                return False, []
            shown = record.status.get(field, "<absent>")
            return True, [f"run-status.json:{field}={shown!r}"]

        return status

    if key == "event":
        if not isinstance(value, dict):
            raise ClaimsError(f"{where}.event must be an object")
        _known_keys(value, ("rule", "min_count"), f"{where}.event")
        rule = value.get("rule")
        if rule not in EVENT_RULES:
            raise ClaimsError(
                f"{where}.event.rule {rule!r} is not a record rule name; "
                f"known: {list(EVENT_RULES)}"
            )
        need = _min_count(value, f"{where}.event")

        def event(record: RunRecord) -> tuple[bool, list[str]]:
            hits = [e for e in record.events if e.get("rule") == rule]
            return len(hits) >= need, [f"log.jsonl:seq={e.get('seq')}" for e in hits]

        return event

    if key == "measure":
        if not isinstance(value, dict):
            raise ClaimsError(f"{where}.measure must be an object")
        _known_keys(value, ("code", "code_prefix", "min_count"), f"{where}.measure")
        code = value.get("code")
        prefix = value.get("code_prefix")
        if (code is None) == (prefix is None):
            raise ClaimsError(f"{where}.measure takes exactly one of code, code_prefix")
        if code is not None and not isinstance(code, str):
            raise ClaimsError(f"{where}.measure.code must be a string")
        if prefix is not None and not isinstance(prefix, str):
            raise ClaimsError(f"{where}.measure.code_prefix must be a string")
        need = _min_count(value, f"{where}.measure")

        def measure(record: RunRecord) -> tuple[bool, list[str]]:
            hits = []
            for entry in record.events:
                if entry.get("rule") != "Measure":
                    continue
                inputs = entry.get("inputs")
                if not isinstance(inputs, list) or not inputs:
                    continue
                head = inputs[0]
                if not isinstance(head, str):
                    continue
                if (code is not None and head == code) or (
                    prefix is not None and head.startswith(prefix)
                ):
                    hits.append(entry)
            return len(hits) >= need, [f"log.jsonl:seq={e.get('seq')}" for e in hits]

        return measure

    if key == "control":
        if not isinstance(value, dict):
            raise ClaimsError(f"{where}.control must be an object")
        _known_keys(value, ("action", "min_count"), f"{where}.control")
        action = value.get("action")
        if not isinstance(action, str) or not action:
            raise ClaimsError(f"{where}.control.action must be a non-empty string")
        need = _min_count(value, f"{where}.control")

        def control(record: RunRecord) -> tuple[bool, list[str]]:
            hits = []
            for entry in record.events:
                if entry.get("rule") != "Control":
                    continue
                payload = entry.get("control")
                if isinstance(payload, dict) and payload.get("action") == action:
                    hits.append(entry)
            return len(hits) >= need, [f"log.jsonl:seq={e.get('seq')}" for e in hits]

        return control

    if key == "object":
        if not isinstance(value, dict):
            raise ClaimsError(f"{where}.object must be an object")
        _known_keys(value, ("kind", "where", "min_count"), f"{where}.object")
        kind = value.get("kind")
        if not isinstance(kind, str) or not kind or "/" in kind or kind.startswith("."):
            raise ClaimsError(f"{where}.object.kind must be a plain directory name")
        raw_where = value.get("where") or []
        if not isinstance(raw_where, list):
            raise ClaimsError(f"{where}.object.where must be a list of clauses")
        clauses = [
            _clause(item, f"{where}.object.where[{i}]") for i, item in enumerate(raw_where)
        ]
        need = _min_count(value, f"{where}.object")

        def objects(record: RunRecord) -> tuple[bool, list[str]]:
            hits = []
            for stem, data in record.objects(kind):
                if all(clause(data) for clause in clauses):
                    hits.append(stem)
            return len(hits) >= need, [f"objects/{kind}/{stem}.json" for stem in hits]

        return objects

    raise ClaimsError(
        f"{where}: unknown condition key {key!r}; known: all_of, any_of, not, "
        "status, event, measure, control, object"
    )


# ---------------------------------------------------------------------------
# claims
# ---------------------------------------------------------------------------


class Scope:
    def __init__(self, raw: Any, where: str) -> None:
        self.selectors: dict[str, list[Any]] = {}
        if raw is None:
            return
        if not isinstance(raw, dict):
            raise ClaimsError(f"{where}: scope must be an object or null")
        _known_keys(raw, SCOPE_KEYS, where)
        for key, field in SCOPE_KEYS.items():
            value = raw.get(key)
            if value is None:
                continue
            if not isinstance(value, list) or not value:
                raise ClaimsError(f"{where}.{key} must be a non-empty list or null")
            self.selectors[field] = list(value)

    def admits(self, record: RunRecord) -> bool:
        for field, allowed in self.selectors.items():
            if record.scope_value(field) not in allowed:
                return False
        return True

    def to_dict(self) -> dict[str, Any]:
        inverse = {field: key for key, field in SCOPE_KEYS.items()}
        return {inverse[f]: v for f, v in sorted(self.selectors.items())}


class Claim:
    def __init__(self, raw: Any, where: str) -> None:
        if not isinstance(raw, dict):
            raise ClaimsError(f"{where}: a claim is an object")
        _known_keys(raw, ("claim_id", "statement", "kind", "scope", "condition", "note"), where)
        claim_id = raw.get("claim_id")
        if not isinstance(claim_id, str) or not CLAIM_ID.match(claim_id):
            raise ClaimsError(f"{where}.claim_id {claim_id!r} is not a claim id")
        self.claim_id = claim_id
        statement = raw.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            raise ClaimsError(f"{where}.statement must be a non-empty string")
        self.statement = statement
        kind = raw.get("kind")
        if kind not in CLAIM_KINDS:
            raise ClaimsError(f"{where}.kind must be one of {list(CLAIM_KINDS)}, got {kind!r}")
        self.kind = kind
        if "condition" not in raw:
            raise ClaimsError(f"{where}: a claim needs a condition")
        self.condition = raw["condition"]
        self.predicate = compile_condition(self.condition, f"{where}.condition")
        self.scope = Scope(raw.get("scope"), f"{where}.scope")
        note = raw.get("note")
        if note is not None and not isinstance(note, str):
            raise ClaimsError(f"{where}.note must be a string or null")
        self.note = note


def load_claims(path: Path) -> tuple[str | None, list[Claim]]:
    try:
        raw = json.loads(path.read_text())
    except OSError as exc:
        raise ClaimsError(f"cannot read claims file {path}: {exc}") from exc
    except ValueError as exc:
        raise ClaimsError(f"{path} is not valid JSON: {exc}") from exc
    return claims_from_dict(raw)


def claims_from_dict(raw: Any) -> tuple[str | None, list[Claim]]:
    if not isinstance(raw, dict):
        raise ClaimsError("a claims file is a JSON object")
    _known_keys(raw, ("schema_version", "title", "claims"), "claims file")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ClaimsError(
            f"claims schema_version must be {SCHEMA_VERSION!r}, got "
            f"{raw.get('schema_version')!r}"
        )
    title = raw.get("title")
    if title is not None and not isinstance(title, str):
        raise ClaimsError("claims file title must be a string or absent")
    entries = raw.get("claims")
    if not isinstance(entries, list) or not entries:
        raise ClaimsError("a claims file needs a non-empty 'claims' list")
    claims: list[Claim] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        claim = Claim(entry, f"claims[{index}]")
        if claim.claim_id in seen:
            raise ClaimsError(f"claims[{index}].claim_id {claim.claim_id!r} repeats")
        seen.add(claim.claim_id)
        claims.append(claim)
    return title, claims


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------


class ClaimResult:
    def __init__(self, claim: Claim) -> None:
        self.claim = claim
        self.tested = 0
        self.refuting: list[tuple[str, list[str]]] = []
        self.witnesses_outside_scope = 0

    @property
    def status(self) -> str:
        if self.tested == 0:
            return STATUS_NOT_TESTED
        if self.refuting:
            return STATUS_REFUTED
        return STATUS_UNREFUTED

    @property
    def standing(self) -> str:
        if self.refuting or self.witnesses_outside_scope:
            return STANDING_SHOWN
        return STANDING_NOT_SHOWN

    def to_dict(self) -> dict[str, Any]:
        shown = self.refuting[:MAX_REFUTING_SHOWN]
        return {
            "claim_id": self.claim.claim_id,
            "statement": self.claim.statement,
            "kind": self.claim.kind,
            "scope": self.claim.scope.to_dict(),
            "status": self.status,
            "standing": self.standing,
            "tested": self.tested,
            "refuting": len(self.refuting),
            "refuting_record_ids": [run_id for run_id, _ in shown],
            "refuting_record_ids_omitted": max(0, len(self.refuting) - len(shown)),
            "witnesses": {
                run_id: locators[:3] for run_id, locators in shown
            },
            "witnesses_outside_scope": self.witnesses_outside_scope,
            "shown_able_to_fail": self.standing == STANDING_SHOWN,
            "note": self.claim.note,
            "epistemic_limit": NON_INDUCTIVE_LIMIT,
        }


def evaluate(claims: Sequence[Claim], records: Sequence[RunRecord]) -> list[ClaimResult]:
    results = []
    for claim in claims:
        result = ClaimResult(claim)
        for record in records:
            holds, locators = claim.predicate(record)
            refutes = holds if claim.kind == "never" else not holds
            if not claim.scope.admits(record):
                if refutes:
                    result.witnesses_outside_scope += 1
                continue
            result.tested += 1
            if refutes:
                result.refuting.append((record.run_id, locators))
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" + ("" if count == 1 else "s")


def render(
    results: Sequence[ClaimResult],
    records: Sequence[RunRecord],
    title: str | None,
    *,
    quiet: bool = False,
) -> str:
    lines: list[str] = []
    if not quiet:
        lines.append(f"# Record claims — {title}" if title else "# Record claims")
        lines.append("")
        lines.append(f"Roots supplied: {len(records)}")
        for record in records:
            lines.append(f"  {record.describe()}")
        lines.append("")
    for result in results:
        lines.append(f"## {result.claim.claim_id}: {result.status}")
        lines.append("")
        lines.append(f"*{result.claim.statement}* (`{result.claim.kind}`)")
        lines.append("")
        scope = result.claim.scope.to_dict()
        lines.append(
            f"- tested on {_plural(result.tested, 'root')}"
            + (f"; scope {json.dumps(scope, sort_keys=True)}" if scope else "; scope: every root")
        )
        if result.refuting:
            shown = result.refuting[:MAX_REFUTING_SHOWN]
            omitted = len(result.refuting) - len(shown)
            lines.append(
                f"- refuting record ids ({len(result.refuting)}"
                + (f", showing {len(shown)}" if omitted else "")
                + "):"
            )
            for run_id, locators in shown:
                first = locators[0] if locators else "the condition did not hold"
                lines.append(f"    {run_id} — {first}")
            if omitted:
                lines.append(f"    (+{omitted} further refuting record id(s) not shown)")
            lines.append(f"- standing: {result.standing}")
        elif result.status == STATUS_NOT_TESTED:
            lines.append("- no supplied root fell inside the declared scope, so nothing was tested")
            if result.standing == STANDING_SHOWN:
                lines.append(
                    "- the refuting condition did hold on "
                    f"{_plural(result.witnesses_outside_scope, 'supplied root')}, "
                    "all outside the scope, so the check is live but was not run here"
                )
            else:
                lines.append(f"- {NOT_SHOWN_SENTENCE}")
            lines.append(f"- standing: {result.standing}")
        else:
            if result.standing == STANDING_SHOWN:
                lines.append(
                    "- the refuting condition held on "
                    f"{_plural(result.witnesses_outside_scope, 'supplied root')} "
                    "outside the declared scope, so the check has been shown "
                    "able to fail"
                )
            else:
                lines.append(f"- {NOT_SHOWN_SENTENCE}")
            lines.append(f"- standing: {result.standing}")
        if result.claim.note:
            lines.append(f"- note: {result.claim.note}")
        lines.append("")
    if not quiet:
        lines.append(NON_INDUCTIVE_LIMIT)
        lines.append("")
        lines.append(
            "This is not a gate, a status, or a score: nothing was written to "
            "any root and no status changed."
        )
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _refuse_inside_a_root(destination: Path) -> None:
    """A report must not land inside a run root: a root is evidence, not scratch."""

    for parent in [destination.resolve(), *destination.resolve().parents]:
        if (parent / "run-status.json").is_file() and (parent / "log.jsonl").exists():
            raise ClaimsError(
                f"refusing to write {destination}: it is inside the run root {parent}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="record_claims.py",
        description=(
            "Test pre-registered universal statements against one or more "
            "DeepReason run records. Read-only: not a gate, not a status, "
            "not a score."
        ),
    )
    parser.add_argument("--claims", required=True, help="path to a claims file")
    parser.add_argument(
        "--root",
        required=True,
        action="append",
        dest="roots",
        metavar="ROOT",
        help="a run root; repeat for more than one",
    )
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument(
        "--markdown", metavar="PATH", help="also write the report as markdown to PATH"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="omit the header and the closing limit"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        title, claims = load_claims(Path(args.claims))
        records = [RunRecord(Path(root)) for root in args.roots]
        results = evaluate(claims, records)
        report = render(results, records, title, quiet=args.quiet)
        if args.markdown:
            destination = Path(args.markdown)
            _refuse_inside_a_root(destination)
            destination.write_text(report)
    except ClaimsError as exc:
        print(f"record_claims: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(
            json.dumps(
                {
                    "result_type": "RECORD_CLAIMS_RESULT_V1",
                    "title": title,
                    "roots": [
                        {"run_id": r.run_id, "root": str(r.root), "name": r.name}
                        for r in records
                    ],
                    "claims": [result.to_dict() for result in results],
                    "epistemic_limit": NON_INDUCTIVE_LIMIT,
                },
                indent=2,
                sort_keys=False,
            )
        )
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
