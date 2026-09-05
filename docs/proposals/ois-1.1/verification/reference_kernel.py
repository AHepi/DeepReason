"""Finite bookkeeping reference for Open Inquiry Semantics 1.1.

This module checks records, computes DA-1 application labels, and summarizes
cases. It has no implementation of semantic truth, creativity, or universality.
Application activation and semantic interpretations are supplied, fallible inputs.
Only the Python standard library is required.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence
from types import MappingProxyType


class ContractError(ValueError):
    """The supplied finite representation violates a declared contract."""


class Check(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Reference:
    artifact: str
    local: bool = False


@dataclass(frozen=True)
class Entry:
    id: str
    actor: str
    kind: str
    causes: frozenset[str] = frozenset()
    creates: frozenset[str] = frozenset()
    payload: Any = None
    # (created child, previously available parent). This is record ancestry.
    parents: tuple[tuple[str, str], ...] = ()


def references(value: Any) -> Iterable[Reference]:
    """Walk every typed reference, including ones nested in body fields."""
    if isinstance(value, Reference):
        if not value.artifact:
            raise ContractError("empty artifact reference")
        yield value
    elif isinstance(value, Mapping):
        if any(not isinstance(k, str) for k in value):
            raise ContractError("payload map keys must be strings")
        for item in value.values():
            yield from references(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from references(item)
    elif value is None or isinstance(value, (str, bool, int, float)):
        return
    else:
        raise ContractError(f"unsupported payload value: {type(value).__name__}")


def canonical(value: Any) -> Any:
    if isinstance(value, Reference):
        return {"artifact": value.artifact, "local": value.local}
    if isinstance(value, Mapping):
        return {k: canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [canonical(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(canonical(v) for v in value)
    return value


def freeze_payload(value: Any) -> Any:
    """Detach payloads from callers so a validated snapshot cannot change in place."""
    if isinstance(value, Mapping):
        return MappingProxyType({k: freeze_payload(v) for k, v in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(freeze_payload(v) for v in value)
    return value


@dataclass
class RecordModel:
    initial: frozenset[str]
    entries: Sequence[Entry]
    alternatives: tuple[frozenset[str], ...] = ()
    _by_id: dict[str, Entry] = field(init=False, repr=False)
    _past: dict[str, frozenset[str]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.initial = frozenset(self.initial)
        self.entries = tuple(replace(e, causes=frozenset(e.causes), creates=frozenset(e.creates),
                                     payload=freeze_payload(e.payload), parents=tuple(e.parents))
                             for e in self.entries)
        self.alternatives = tuple(frozenset(a) for a in self.alternatives)
        self._by_id = {e.id: e for e in self.entries}
        if len(self._by_id) != len(self.entries):
            raise ContractError("duplicate entry ID")
        if any(not e.id or not e.actor or not e.kind for e in self.entries):
            raise ContractError("entry ID, actor and kind must be nonempty")
        self._past = {}
        visiting: set[str] = set()

        def ancestors(eid: str) -> frozenset[str]:
            if eid not in self._by_id:
                raise ContractError(f"unknown cause: {eid}")
            if eid in visiting:
                raise ContractError(f"causal cycle at {eid}")
            if eid in self._past:
                return self._past[eid]
            visiting.add(eid)
            result: set[str] = set()
            for parent in self._by_id[eid].causes:
                result.add(parent)
                result.update(ancestors(parent))
            visiting.remove(eid)
            self._past[eid] = frozenset(result)
            return self._past[eid]

        for e in self.entries:
            ancestors(e.id)
        owners: dict[str, str | None] = {x: None for x in self.initial}
        if "" in owners:
            raise ContractError("empty initial artifact ID")
        for e in self.entries:
            for artifact in e.creates:
                if not artifact or artifact in owners:
                    raise ContractError(f"duplicate or empty artifact ID: {artifact}")
                owners[artifact] = e.id
        for alt in self.alternatives:
            if len(alt) < 2 or not alt.issubset(self._by_id):
                raise ContractError("invalid alternative set")
        for e in self.entries:
            possible_past = set(self._past[e.id]) | {e.id}
            if any(len(alt & possible_past) > 1 for alt in self.alternatives):
                raise ContractError(f"incompatible causal history for {e.id}")
            available = set(self.initial)
            for old in self._past[e.id]:
                available.update(self._by_id[old].creates)
            for ref in references(e.payload):
                allowed = e.creates if ref.local else available
                if ref.artifact not in allowed:
                    mode = "local" if ref.local else "historical"
                    raise ContractError(f"ungrounded {mode} ref {ref.artifact} at {e.id}")
            for child, parent in e.parents:
                if child not in e.creates or parent not in available:
                    raise ContractError(f"invalid ancestry edge {(child, parent)} at {e.id}")

    def validate_cut(self, cut: Iterable[str]) -> frozenset[str]:
        selected = frozenset(cut)
        if not selected.issubset(self._by_id):
            raise ContractError("cut contains an unknown entry")
        for eid in selected:
            if not self._past[eid].issubset(selected):
                raise ContractError("cut is not downward closed")
        if any(len(alt & selected) > 1 for alt in self.alternatives):
            raise ContractError("cut contains alternative transactions")
        return selected

    def digest(self, cut: Iterable[str]) -> str:
        selected = self.validate_cut(cut)
        data = {
            "initial": sorted(self.initial),
            "alternatives": sorted(sorted(a) for a in self.alternatives),
            "entries": [
                {"id": e.id, "actor": e.actor, "kind": e.kind,
                 "causes": sorted(e.causes), "creates": sorted(e.creates),
                 "payload": canonical(e.payload), "parents": sorted(e.parents)}
                for e in sorted((self._by_id[x] for x in selected), key=lambda e: e.id)
            ],
        }
        encoded = json.dumps(data, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode()
        return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ClaimKey:
    predicate: str
    subject: str
    history: str
    boundary: str
    grain: str
    contribution: str
    situation_before: str
    situation_after: str
    respect: str
    interpretation: str
    # A fixed explicit field can be "not_applicable" if the signature permits it.
    def __post_init__(self) -> None:
        if any(not isinstance(v, str) or not v for v in self.__dict__.values()):
            raise ContractError("claim indices must be explicit nonempty strings")


@dataclass(frozen=True)
class Application:
    id: str
    essential: frozenset[str] = frozenset()
    targets: frozenset[str] = frozenset()
    readiness: Check = Check.PASS
    role: str = "provisional_use"
    # These fixture nodes stand for already supplied activation assessments.
    assessment: str = "stipulated-fixture-assessment"


@dataclass(frozen=True)
class Labels:
    inside: frozenset[str]
    outside: frozenset[str]
    undecided: frozenset[str]
    rounds: int

    def of(self, app_id: str) -> str:
        if app_id in self.inside:
            return "in"
        if app_id in self.outside:
            return "out"
        if app_id in self.undecided:
            return "undecided"
        raise ContractError(f"unknown application {app_id}")


def appraise(applications: Sequence[Application]) -> Labels:
    """Compute DA-1 from explicitly activated, context-interpreted fixture nodes."""
    nodes = {a.id: a for a in applications}
    if len(nodes) != len(applications) or any(not x for x in nodes):
        raise ContractError("duplicate or empty application ID")
    for a in applications:
        if not (a.essential | a.targets).issubset(nodes):
            raise ContractError(f"unresolved application reference at {a.id}")
        if not isinstance(a.readiness, Check):
            raise ContractError(f"undeclared readiness value at {a.id}")
    attackers = {x: {a.id for a in applications if x in a.targets} for x in nodes}
    inside: set[str] = set()
    outside: set[str] = set()
    productive_rounds = 0
    while True:
        new_i = inside | {
            a.id for a in applications
            if a.readiness == Check.PASS and bool(a.assessment)
            and a.essential.issubset(inside) and attackers[a.id].issubset(outside)
        }
        new_o = outside | {
            a.id for a in applications
            if a.readiness == Check.FAIL or bool(a.essential & outside)
            or bool(attackers[a.id] & inside)
        }
        if new_i & new_o:
            raise AssertionError("DA-1 invariant failure: inconsistent labels")
        if new_i == inside and new_o == outside:
            return Labels(frozenset(inside), frozenset(outside),
                          frozenset(nodes.keys() - inside - outside), productive_rounds)
        inside, outside = new_i, new_o
        productive_rounds += 1
        if productive_rounds > 2 * len(nodes):
            raise AssertionError("DA-1 finite termination bound exceeded")


@dataclass(frozen=True)
class Case:
    id: str
    key: ClaimKey
    polarity: str
    application: str | None = None


def case_state(polarities: Iterable[str]) -> str:
    values = set(polarities)
    if not values.issubset({"positive", "negative"}):
        raise ContractError("unknown polarity")
    return {
        frozenset(): "NO_CASE",
        frozenset({"positive"}): "POSITIVE_CASE_ONLY",
        frozenset({"negative"}): "NEGATIVE_CASE_ONLY",
        frozenset({"positive", "negative"}): "BOTH_CASES",
    }[frozenset(values)]


def report(key: ClaimKey, cases: Sequence[Case], apps: Sequence[Application],
           snapshot_digest: str, bindings: Mapping[str, str]) -> dict[str, Any]:
    if len({c.id for c in cases}) != len(cases):
        raise ContractError("duplicate case ID")
    required = {"authority_digest", "specification_digest", "interpretation_version",
                "profile_version", "checker_version", "policy_version"}
    if not required.issubset(bindings) or any(not bindings[k] for k in required):
        raise ContractError("missing report binding")
    if bindings["policy_version"] != "DA-1":
        raise ContractError("report policy does not match computed policy")
    if bindings["interpretation_version"] != key.interpretation:
        raise ContractError("claim and report interpretations differ")
    labels = appraise(apps)
    ids = {a.id for a in apps}
    relevant = [c for c in cases if c.key == key]
    for c in relevant:
        if c.application is not None and c.application not in ids:
            raise ContractError("case names missing application")
    usable = [c for c in relevant if c.application in labels.inside]
    return {
        "claim": dict(key.__dict__), "snapshot": snapshot_digest,
        "bindings": dict(bindings), "policy": "DA-1", "raw": case_state(c.polarity for c in relevant),
        "usable": case_state(c.polarity for c in usable),
        "raw_case_ids": [c.id for c in relevant],
        "usable_case_ids": [c.id for c in usable],
        "unassessed_case_ids": [c.id for c in relevant if c.application is None],
        "labels": {a.id: labels.of(a.id) for a in apps},
        "checks": {a.id: a.readiness.value for a in apps},
        "activation": {a.id: "RECORDED" if a.assessment else "MISSING" for a in apps},
        "semantic_decision": "NOT_EVALUATED",
    }


def merge_view(existing: Iterable[str], imported: Iterable[str],
               importable_snapshot: Iterable[str]) -> frozenset[str]:
    """Import already located records; do not relocate them or add future ones."""
    imported_set = frozenset(imported)
    if not imported_set.issubset(importable_snapshot):
        raise ContractError("import names unavailable or future entries")
    return frozenset(existing) | imported_set


def finite_variation_summary(informative: bool, free_variant_cases: Sequence[bool]) -> str:
    """A report on a stipulated finite family, never a global hardness verdict."""
    if not informative or not free_variant_cases:
        return "UNINFORMATIVE_FAMILY"
    if any(free_variant_cases):
        return "FREE_VARIANT_CASE_FOUND"
    return "NO_FREE_VARIANT_CASE_FOUND_IN_V"


def match_contribution(request: ClaimKey, attempted: ClaimKey,
                       newness: ClaimKey, authorship: ClaimKey) -> bool:
    """Identity guard only. Matching keys does not establish any semantic conjunct."""
    if (request.predicate, attempted.predicate, newness.predicate, authorship.predicate) != (
        "OCA", "Attempt", "New", "Authors"
    ):
        return False
    def indices(key: ClaimKey) -> tuple[str, ...]:
        return tuple(v for k, v in key.__dict__.items() if k != "predicate")
    return indices(request) == indices(attempted) == indices(newness) == indices(authorship)


def validate_slice(model: RecordModel, cut: Iterable[str], apps: Sequence[Application],
                   subjects: Mapping[str, str], cases: Sequence[Case]) -> None:
    """Bind an appraisal slice to present artifacts; do not validate their meaning."""
    selected = model.validate_cut(cut)
    available = set(model.initial)
    for eid in selected:
        available.update(model._by_id[eid].creates)
    ids = {a.id for a in apps}
    if set(subjects) != ids:
        raise ContractError("slice subject bindings do not match application IDs")
    if any(ref not in available for ref in subjects.values()):
        raise ContractError("slice subject is not present at cut")
    if any(a.assessment not in available for a in apps):
        raise ContractError("slice activation assessment is not present at cut")
    if any(c.id not in available for c in cases):
        raise ContractError("case artifact is not present at cut")
    appraise(apps)  # Also check all dependency and attack references.
