"""Model-visible wire contracts compiled into existing canonical outputs.

Wire values are transport objects, never artifacts.  Their local aliases and
profile identifiers stay outside the canonical ontology and event semantics.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Generic, Literal, Mapping, Sequence, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    create_model,
    field_validator,
    model_validator,
)

from deepreason.conjecture_turn import (
    ConjectureAbstentionV1,
    ConjectureTurnV6,
    ConjecturerTurnV4,
    ContextRequestV1,
    ReasoningConjecturerTurnV4,
    ConjecturerTurnV5,
    ReasoningConjecturerTurnV5,
    ReasoningConjecturerTurnV6,
)
from deepreason.capabilities.models import (
    ObservableName,
    SealedInputAlias,
    SimulationSeed,
    ResearchFetchProposalDraftV1,
    SimulationParameterSetV1,
    SimulationProposalDraftV1,
)
from deepreason.llm.contracts import (
    ArgumentativeCriticOutput,
    BatchCase,
    BatchCriticOutput,
    CandidateRef,
    ConjectureCandidate,
    ConjecturerOutput,
    DischargeWireV1,
    EvidenceRefClaimV1,
    discharge_kind_enum,
    QuotedEvidenceRefV1,
    DefenderOutput,
    JudgeRuling,
    PairwiseRuling,
    SynthesizerOutput,
    VariatorEdit,
    VariatorOutput,
)
from deepreason.llm.profiles import ModelProfile, get_profile
from deepreason.llm.repair import (
    RepairDiagnosticEnvelopeV2,
    RepairPatchV1,
    parse_one_json_value,
    repair_patch_response_schema,
    tolerant_patch_value,
)
from deepreason.scratch.proposals import (
    ScratchProposalV1,
    V6_SCRATCH_WORKSHOP_SCHEMA_DESCRIPTION,
)
from deepreason.workloads.text import (
    AnalogyClaim,
    OperationalSidecar,
    ReasoningCandidateProposal,
    ReasoningConjecturerOutput,
)


CanonicalOutput = TypeVar("CanonicalOutput", bound=BaseModel)

CONJECTURER_TURN_CONTRACT_V6 = "conjecturer.turn.v6"
# P-CEPP-1: additive to v6 (D2 rev 2 dual-mode) -- the SAME wire schema,
# a different manifest-facing label so the new eval-kind vocabulary
# entry (program:candidate_checker) is expected on this turn.
CONJECTURER_TURN_CONTRACT_V7 = "conjecturer.turn.v7"
BATCH_CRITIC_CONTRACT_V2 = "batch-critic.v2"
ATOMIC_CONJECTURE_CONTRACT_V1 = "conjecturer.atomic-candidate.v1"
ATOMIC_CRITIC_CONTRACT_V1 = "critic.atomic-target.v1"
BRIDGE_LEDGER_CONTRACT_V3 = "bridge.ledger.v3"
BRIDGE_COMPOSITION_CONTRACT_V2 = "bridge.composition.v2"

class UnknownAliasError(ValueError):
    pass


class AliasTableRequiredError(ValueError):
    """A compact reference-bearing role was invoked without local aliases."""


class CriticTargetRequiredError(ValueError):
    """A compact critic contract was not bound to its actual target."""


class V6WireReferenceError(UnknownAliasError):
    """A v6 value used a handle outside one exact call-local namespace."""

    code = "V6_WIRE_REFERENCE_INVALID"

    def __init__(
        self,
        message: str,
        *,
        pointer: str,
        legal_handles: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.pointer = pointer
        self.repair_scope = pointer
        self.authorized_pointers = (pointer,)
        self.legal_handles = legal_handles


@dataclass(frozen=True)
class AliasTable:
    """Immutable call-local alias mapping held outside the model response."""

    aliases: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        copied = dict(self.aliases)
        if len(set(copied.values())) != len(copied):
            raise ValueError("alias targets must be unique")
        for alias, target in copied.items():
            if not alias or not target:
                raise ValueError("aliases and targets must be nonempty")
        object.__setattr__(self, "aliases", MappingProxyType(copied))

    @classmethod
    def from_values(cls, values: list[str], prefix: str = "A") -> "AliasTable":
        return cls({f"{prefix}{index}": value for index, value in enumerate(values, 1)})

    def resolve(self, alias: str) -> str:
        try:
            return self.aliases[alias]
        except KeyError as exc:
            raise UnknownAliasError(f"unknown local alias {alias!r}") from exc

    def alias_for(self, canonical: str) -> str:
        for alias, target in self.aliases.items():
            if target == canonical:
                return alias
        raise UnknownAliasError(f"canonical reference has no local alias: {canonical!r}")

    def render(self) -> str:
        return "\n".join(f"{alias}: {target}" for alias, target in self.aliases.items())

    def render_pack(self, pack: str) -> str:
        """Replace machine identifiers; annotate textual exchange spans."""
        rendered = pack
        for alias, target in sorted(
            self.aliases.items(), key=lambda item: (-len(item[1]), item[0])
        ):
            if re.fullmatch(r"[a-f0-9]{12,64}", target) or target.startswith(
                ("pi-", "kappa-", "w:", "fc-")
            ):
                rendered = rendered.replace(target, alias)
            else:
                rendered = rendered.replace(target, f"[{alias}] {target}")
        return rendered


class StrictWireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


def _resolve_ref(node: dict, root: dict) -> dict:
    ref = node.get("$ref")
    if not ref:
        return node
    current: Any = root
    for part in ref.lstrip("#/").split("/"):
        current = current.get(part, {}) if isinstance(current, dict) else {}
    return current if isinstance(current, dict) else node


def exclusive_fields_schema(*groups: tuple[str, ...]):
    """Encode "exactly one field per group" INTO the JSON Schema.

    A cross-field rule that lives only in a ``model_validator`` is invisible
    to a model reading the schema as its source of structural truth: the
    schema says every field is optional and nullable, the validator says
    exactly one is legal, and with reasoning disabled the schema wins.
    Measured on glm-5.2 with thinking off, one such rule cost 11/20 then
    9/20 first-pass valid and failed production qualification twice.

    Two encoding constraints, both learned the hard way:

    * Groups are INDEPENDENT. A rule over two endpoints is two groups, not
      one ``oneOf`` over paired required lists — pairing forbids the legal
      mixed form.
    * Branches carry ``required`` ONLY. ``_strict_schema`` below closes
      every subschema holding a ``properties`` key, so a branch written
      with ``properties`` becomes an object that rejects its siblings.

    ``null`` is stripped from the named fields so ``required`` means
    "present and usable"; otherwise an explicit null satisfies ``required``
    and violates the rule anyway. Python models keep accepting ``None``, so
    this narrows what the model is TOLD and never what the harness admits.
    """

    def apply(schema: dict) -> None:
        properties = schema.get("properties", {})
        for group in groups:
            for name in group:
                field = properties.get(name)
                if not isinstance(field, dict):
                    continue
                concrete = [
                    option
                    for option in field.get("anyOf", ())
                    if isinstance(option, dict) and option.get("type") != "null"
                ]
                if len(concrete) == 1:
                    field.pop("anyOf", None)
                    field.pop("default", None)
                    field.update(concrete[0])
        schema["allOf"] = [
            {"oneOf": [{"required": [name]} for name in group]} for group in groups
        ]

    return apply


_COMBINATORS = frozenset({"oneOf", "anyOf", "allOf", "not", "if", "then", "else"})


def _concrete_options(field: Mapping[str, Any]) -> list[dict]:
    """The non-null alternatives of a rendered field, whatever its shape."""

    options = field.get("anyOf")
    if isinstance(options, list):
        return [
            option
            for option in options
            if isinstance(option, dict) and option.get("type") != "null"
        ]
    return [dict(field)] if field else []


def _renders_as(field: Mapping[str, Any], kind: str) -> bool:
    """True when every non-null alternative of ``field`` is ``kind``."""

    options = _concrete_options(field)
    if not options:
        return False
    if kind == "array":
        return all(
            option.get("type") == "array" or "items" in option for option in options
        )
    return all(option.get("type") == kind for option in options)


def present_and_nonempty(name: str, properties: dict, *, minimum: int = 1) -> dict:
    """One branch asserting a field is present AND actually says something.

    "Present" is not enough on any shape the wire uses: an array field
    defaults to ``[]``, a nullable field defaults to ``null``, an alias field
    defaults to ``""``, and the Python validators test truthiness, not
    presence. The branch has to say so, which is why it carries
    ``properties`` — legal only because ``_strict_schema`` leaves constraint
    branches open, and only for as long as the branch never declares
    ``"type": "object"`` itself.

    The shape switch reads the RENDERED property, not the annotation. A
    nullable array renders as ``{"anyOf": [{"type": "array", ...},
    {"type": "null"}]}`` with no top-level ``type`` and no ``items``, so a
    naive array test misses it and emits ``{"not": {"type": "null"}}`` —
    which admits ``[]`` and silently drops the rule. Every reference array on
    the claim ledger has exactly that shape.
    """

    field = properties.get(name, {})
    if _renders_as(field, "array"):
        inner: dict = {"minItems": minimum}
    elif _renders_as(field, "string"):
        inner = {"minLength": 1}
    else:
        return {"required": [name], "properties": {name: {"not": {"type": "null"}}}}
    # `minItems`/`minLength` constrain only their own instance type, so on a
    # NULLABLE field they are vacuously satisfied by an explicit null and the
    # branch admits exactly what it meant to forbid. Pinning the type closes it.
    if field.get("type") is None:
        inner["type"] = "array" if "minItems" in inner else "string"
    return {"required": [name], "properties": {name: inner}}


def absent_or_empty(name: str, properties: dict) -> dict:
    """The dual of :func:`present_and_nonempty`, as a bare property constraint.

    Carries no ``required``, so an absent field satisfies it — which is the
    whole point: inside a ``then`` there is no in-band way to say "absent"
    except :func:`require_absent`, and a field that has an empty
    representation should be allowed to use it.

    Raises when the field has no empty representation at all: emitting
    ``maxLength: 0`` against a rendered ``minLength: 1`` would make the
    consequent unsatisfiable and so forbid the discriminator value outright,
    which is a much larger claim than the validator makes.
    """

    field = properties.get(name, {})
    options = _concrete_options(field)
    nullable = any(
        option.get("type") == "null" for option in field.get("anyOf", []) if isinstance(option, dict)
    )
    if _renders_as(field, "array"):
        empty: dict = {"maxItems": 0}
        return {"anyOf": [{"type": "null"}, empty]} if nullable else empty
    if nullable:
        return {"type": "null"}
    if _renders_as(field, "string") and not any(
        option.get("minLength", 0) for option in options
    ):
        return {"maxLength": 0}
    raise ValueError(
        f"{name!r} has no empty representation; use require_absent instead"
    )


def require_absent(name: str) -> dict:
    """Forbid a field outright, for the fields that cannot be empty."""

    return {"not": {"required": [name]}}


def _names_mentioned(node: Any) -> set[str]:
    """Every property name a constraint subtree constrains or requires."""

    found: set[str] = set()
    if isinstance(node, dict):
        required = node.get("required")
        if isinstance(required, list):
            found.update(name for name in required if isinstance(name, str))
        properties = node.get("properties")
        if isinstance(properties, dict):
            found.update(properties)
        for key, child in node.items():
            if key in _COMBINATORS:
                found |= _names_mentioned(child)
    elif isinstance(node, list):
        for child in node:
            found |= _names_mentioned(child)
    return found


def _without_property(clause: Any, name: str) -> Any | None:
    """Rewrite one constraint clause as if ``name`` had never been declared.

    Returns ``None`` when the clause has nothing left to say. An emptied
    branch must be DROPPED, never returned as ``{}``: a vacuously true branch
    inside an ``anyOf`` satisfies the whole disjunction and silently deletes
    the rule it was carrying — which is exactly the "``{}`` is a valid turn"
    defect the outcome encoding exists to prevent.
    """

    if not isinstance(clause, dict):
        return clause
    if "if" in clause:
        if name in _names_mentioned(clause["if"]):
            return None
        rewritten = dict(clause)
        for branch in ("then", "else"):
            if branch not in rewritten:
                continue
            pruned = _without_property(rewritten[branch], name)
            if pruned is None:
                rewritten.pop(branch)
            else:
                rewritten[branch] = pruned
        return rewritten if rewritten.keys() - {"if"} else None
    rewritten = dict(clause)
    for key in ("anyOf", "oneOf", "allOf"):
        branches = rewritten.get(key)
        if not isinstance(branches, list):
            continue
        kept = [
            pruned
            for pruned in (_without_property(branch, name) for branch in branches)
            if pruned is not None
        ]
        if not kept:
            rewritten.pop(key)
        else:
            rewritten[key] = kept
    required = rewritten.get("required")
    if isinstance(required, list) and name in required:
        remaining = [item for item in required if item != name]
        if remaining:
            rewritten["required"] = remaining
        else:
            rewritten.pop("required")
    properties = rewritten.get("properties")
    if isinstance(properties, dict) and name in properties:
        properties.pop(name)
        if not properties:
            rewritten.pop("properties")
    return rewritten or None


def prune_property(node: dict[str, Any], name: str) -> None:
    """Remove a property AND every constraint that still names it.

    Capability-gated contracts drop properties at render time, and
    ``additionalProperties: false`` then forbids the very field a surviving
    ``allOf`` branch still advertises as a way to satisfy the schema. The
    rendered result must be indistinguishable from one where the property was
    never declared, so omission and encoding cannot disagree.
    """

    node.get("properties", {}).pop(name, None)
    required = node.get("required")
    if isinstance(required, list) and name in required:
        required.remove(name)
    clauses = node.get("allOf")
    if not isinstance(clauses, list):
        return
    kept = [
        pruned
        for pruned in (_without_property(clause, name) for clause in clauses)
        if pruned is not None
    ]
    if kept:
        node["allOf"] = kept
    else:
        node.pop("allOf")


def outcome_shape_schema(
    *,
    meaningful: tuple[str, ...],
    abstention: str | None = None,
    abstention_excludes: tuple[str, ...] = (),
):
    """Encode "at least one meaningful outcome" and abstention exclusivity.

    Both rules lived only in ``_meaningful_*_outcome`` validators, so the
    schema said every field was optional and a model reading it could emit
    ``{}`` — structurally valid, semantically refused. In the coin
    canonicity run ``conjecturer.turn.v6`` was rejected five times and
    completed zero times, and every surviving candidate came from the
    atomic fallback instead.

    Constraints are appended under ``allOf`` deliberately:
    ``_reject_unknown_fields`` inspects only a TOP-LEVEL ``anyOf``/``oneOf``
    and then ``properties``, so nesting under ``allOf`` leaves that
    firewall's behaviour exactly as it was.
    """

    def apply(schema: dict) -> None:
        properties = schema.get("properties", {})
        present = [name for name in meaningful if name in properties]
        if not present:
            return
        clauses = schema.setdefault("allOf", [])
        clauses.append(
            {"anyOf": [present_and_nonempty(n, properties) for n in present]}
        )
        if abstention is None or abstention not in properties:
            return
        excluded = [name for name in abstention_excludes if name in properties]
        if not excluded:
            return
        emptied = {name: absent_or_empty(name, properties) for name in excluded}
        clauses.append(
            {
                "if": present_and_nonempty(abstention, properties),
                "then": {"properties": emptied},
            }
        )

    return apply


@dataclass(frozen=True)
class FieldIn:
    """The clause applies when ``name`` holds one of ``values``."""

    name: str
    values: tuple[str, ...]


@dataclass(frozen=True)
class FieldPresent:
    """The clause applies when ``name`` is present and carries content."""

    name: str


@dataclass(frozen=True)
class ShapeClause:
    """One "this value of that field demands this shape" rule.

    ``requires`` names fields that must each carry content; an entry may be
    ``(name, n)`` to demand ``n`` items rather than one. ``requires_any`` holds
    INDEPENDENT groups, one satisfied alternative per group. ``forbids`` names
    fields that must be absent or empty. ``field_values`` narrows another
    field's enum.
    """

    when: FieldIn | FieldPresent
    requires: tuple[str | tuple[str, int], ...] = ()
    requires_any: tuple[tuple[str | tuple[str, int], ...], ...] = ()
    forbids: tuple[str, ...] = ()
    field_values: Mapping[str, tuple[str, ...]] = field(
        default_factory=lambda: MappingProxyType({})
    )


def _clause_branch(entry: str | tuple[str, int], properties: dict) -> dict:
    name, minimum = entry if isinstance(entry, tuple) else (entry, 1)
    return present_and_nonempty(name, properties, minimum=minimum)


def discriminated_shape_schema(*clauses: ShapeClause):
    """Encode "the value of one field decides the shape of the others".

    The single most common prose-only rule in this repository: five
    validators across the ledger, the grounding repair, the composition and
    the pairwise judge say it in English while the schema declares every
    field independently optional.

    Three encoding constraints, each of which was a real trap:

    * Clauses append to ``allOf``. ``_reject_unknown_fields`` inspects only a
      TOP-LEVEL ``anyOf``/``oneOf`` before falling through to ``properties``,
      so nesting here leaves that firewall's behaviour exactly as it was.
    * Negation is spelled as the positive complement. ``FieldIn`` enumerates
      the values a clause fires on rather than wrapping a ``not``, which keeps
      the emitted schema inside the keyword subset that constrained-decoding
      backends actually implement. Every discriminator here is a closed
      ``Literal``, so the complement is always writable.
    * The ``if`` carries ``required`` as well as the value test, so a clause
      cannot apply vacuously to a document that simply omits the
      discriminator.

    Where a provider rejects ``if``/``then`` outright, every clause below is
    mechanically rewritable as ``{"anyOf": [{"properties": {d: {"enum":
    complement}}}, consequent]}`` using only ``anyOf`` and ``enum``.

    A clause naming a field the contract does not render is narrowed to the
    fields that survive, exactly as ``prune_property`` narrows one after the
    fact, so the two paths cannot disagree.
    """

    def apply(schema: dict) -> None:
        properties = schema.get("properties", {})
        emitted = []
        for clause in clauses:
            condition = _clause_condition(clause, properties, schema)
            if condition is None:
                continue
            consequent = _clause_consequent(clause, properties)
            if consequent is None:
                continue
            emitted.append({"if": condition, "then": consequent})
        if emitted:
            schema.setdefault("allOf", []).extend(emitted)

    return apply


def _declared_enum(
    field: Mapping[str, Any], root: dict | None = None
) -> tuple[str, ...] | None:
    """The values a field may hold, following one ``$ref`` into ``$defs``.

    Enum-typed fields render as a bare ``$ref``, so reading the property alone
    sees no values at all and every clause over them would look unverifiable.
    """

    for option in _concrete_options(field):
        resolved = _resolve_ref(option, root) if root is not None else option
        values = resolved.get("enum")
        if isinstance(values, list):
            return tuple(values)
        if "const" in resolved:
            return (resolved["const"],)
    return None


def _clause_condition(
    clause: ShapeClause, properties: dict, root: dict | None = None
) -> dict | None:
    name = clause.when.name
    if name not in properties:
        return None
    if isinstance(clause.when, FieldPresent):
        return present_and_nonempty(name, properties)
    declared = _declared_enum(properties[name], root)
    if declared is not None:
        unknown = [value for value in clause.when.values if value not in declared]
        if unknown:
            # A typo'd literal must be a hard error: as a silently vacuous
            # clause it would look encoded and enforce nothing.
            raise ValueError(
                f"{name!r} clause names values outside the rendered enum: {unknown!r}"
            )
    live = [value for value in clause.when.values if declared is None or value in declared]
    if not live:
        return None
    return {"required": [name], "properties": {name: {"enum": live}}}


def _clause_consequent(clause: ShapeClause, properties: dict) -> dict | None:
    constraints: list[dict] = []
    for entry in clause.requires:
        name = entry[0] if isinstance(entry, tuple) else entry
        if name in properties:
            constraints.append(_clause_branch(entry, properties))
    for group in clause.requires_any:
        branches = [
            _clause_branch(entry, properties)
            for entry in group
            if (entry[0] if isinstance(entry, tuple) else entry) in properties
        ]
        if branches:
            constraints.append({"anyOf": branches})
    emptied = {}
    for name in clause.forbids:
        if name not in properties:
            continue
        try:
            emptied[name] = absent_or_empty(name, properties)
        except ValueError:
            constraints.append(require_absent(name))
    if emptied:
        constraints.append({"properties": emptied})
    narrowed = {
        name: {"enum": list(values)}
        for name, values in clause.field_values.items()
        if name in properties
    }
    if narrowed:
        constraints.append({"properties": narrowed})
    if not constraints:
        return None
    return constraints[0] if len(constraints) == 1 else {"allOf": constraints}


def restrict_discriminator_values(
    schema: dict, discriminator: str, allowed: Sequence[str]
) -> None:
    """Advertise only the discriminator values this CALL actually permits.

    The pack tells the model which actions are permitted for the finding in
    hand, but the schema kept offering the whole enum, so the two disagreed on
    every call and only the prose carried the narrower truth. The harness
    refuses a value outside ``allowed`` anyway, so this narrows what the model
    is TOLD and nothing else.

    Enum fields render as a bare ``$ref``, so the values are narrowed in
    ``$defs`` — correct only while the definition has one user, which is
    checked here rather than assumed.
    """

    keep = list(allowed)
    field = schema.get("properties", {}).get(discriminator)
    if not isinstance(field, dict):
        return
    for option in _concrete_options(field):
        ref = option.get("$ref")
        target = _resolve_ref(option, schema) if ref else option
        values = target.get("enum")
        if not isinstance(values, list):
            continue
        if ref and _ref_users(schema, ref) > 1:
            raise ValueError(
                f"{ref} is shared, so narrowing it for {discriminator!r} would "
                "silently narrow another field"
            )
        target["enum"] = [value for value in values if value in keep]
    clauses = schema.get("allOf")
    if not isinstance(clauses, list):
        return
    kept = []
    for clause in clauses:
        condition = clause.get("if", {}) if isinstance(clause, dict) else {}
        values = condition.get("properties", {}).get(discriminator, {}).get("enum")
        if not values:
            kept.append(clause)
            continue
        live = [value for value in values if value in keep]
        if not live:
            continue
        condition["properties"][discriminator]["enum"] = live
        kept.append(clause)
    if kept:
        schema["allOf"] = kept
    else:
        schema.pop("allOf")


def _ref_users(node: Any, ref: str) -> int:
    if isinstance(node, dict):
        if node.get("$ref") == ref:
            return 1
        return sum(_ref_users(child, ref) for child in node.values())
    if isinstance(node, list):
        return sum(_ref_users(child, ref) for child in node)
    return 0


def _branch_is_unsatisfiable(branch: dict, properties: dict) -> bool:
    """True when no instance can satisfy this ``present_and_nonempty`` branch."""

    for name, demand in branch.get("properties", {}).items():
        minimum = demand.get("minItems")
        if minimum is None:
            continue
        for option in _concrete_options(properties.get(name, {})):
            ceiling = option.get("maxItems")
            if ceiling is not None and ceiling < minimum:
                return True
    return False


def narrow_unsatisfiable_discriminator_values(node: dict, discriminator: str) -> None:
    """Stop advertising a discriminator value nothing can satisfy.

    Catalog binding pins a reference channel the run has no items for to
    ``maxItems: 0``. A clause whose every alternative demands one of those
    channels is then unsatisfiable, so the schema names a value in the
    discriminator's enum while forbidding every way to use it — the inverse
    of a prose-only rule, and just as misleading: the contract advertises
    more than the harness can accept.

    Dropping the value narrows only what the model is TOLD. The harness
    already refuses such an entry, because the handles it would have to cite
    do not exist in the catalog.
    """

    clauses = node.get("allOf")
    properties = node.get("properties", {})
    field = properties.get(discriminator)
    if not isinstance(clauses, list) or not isinstance(field, dict):
        return
    dead: set[str] = set()
    kept = []
    for clause in clauses:
        condition = clause.get("if", {}) if isinstance(clause, dict) else {}
        values = condition.get("properties", {}).get(discriminator, {}).get("enum")
        if not values:
            kept.append(clause)
            continue
        groups = _consequent_groups(clause.get("then", {}))
        if groups and any(
            all(_branch_is_unsatisfiable(branch, properties) for branch in group)
            for group in groups
        ):
            dead.update(values)
            continue
        kept.append(clause)
    if not dead:
        return
    node["allOf"] = kept
    if not kept:
        node.pop("allOf")
    for option in (*_concrete_options(field), field):
        values = option.get("enum")
        if isinstance(values, list):
            option["enum"] = [value for value in values if value not in dead]


def _consequent_groups(consequent: dict) -> list[list[dict]]:
    """The alternative-sets a ``then`` demands, one list per independent group."""

    constraints = consequent.get("allOf", [consequent])
    groups = []
    for constraint in constraints:
        if not isinstance(constraint, dict):
            continue
        if "anyOf" in constraint:
            groups.append(list(constraint["anyOf"]))
        elif "required" in constraint:
            groups.append([constraint])
    return groups


def _strict_schema(node: Any, root: dict | None = None) -> Any:
    """Mark every model-visible object as closed, including $defs.

    A subschema sitting directly under a combinator is a CONSTRAINT on an
    object declared elsewhere, not a declaration of one. Closing it would
    make ``{"required": [...], "properties": {...}}`` reject every sibling
    field of the object it is meant to constrain, which is what blocked
    encoding cross-field rules (minItems on one array, say) into the schema.
    Such a branch is left open unless it declares ``"type": "object"``
    itself, in which case it really is an object and is closed as before.

    Verified inert when introduced: across all 18 constructible wire
    contracts, no combinator branch carried a ``properties`` key, so every
    rendered schema was byte-identical before and after this distinction.
    """

    result = copy.deepcopy(node)
    root = result if root is None else root

    def visit(value: Any, constrains: bool = False) -> None:
        if isinstance(value, dict):
            declares_object = value.get("type") == "object"
            if declares_object or ("properties" in value and not constrains):
                value["additionalProperties"] = False
            for key, child in value.items():
                visit(child, key in _COMBINATORS)
        elif isinstance(value, list):
            for child in value:
                visit(child, constrains)

    visit(result)
    return result


def _reject_control_fields(value: Any, path: str = "") -> None:
    # Lazy import avoids making run-manifest initialization part of this
    # module's import graph while retaining the one canonical typed firewall.
    from deepreason.llm.firewall import reject_model_control_fields

    reject_model_control_fields(value, pointer=path)


def _reject_unknown_fields(value: Any, schema: dict, root: dict, path: str = "") -> None:
    schema = _resolve_ref(schema, root)
    branches = schema.get("anyOf") or schema.get("oneOf")
    if branches:
        # Nullability is the common Pydantic branch shape. For structured
        # values, select a branch with the matching JSON type.
        choices = [_resolve_ref(b, root) for b in branches]
        if isinstance(value, dict):
            schema = next(
                (b for b in choices if b.get("type") == "object" or "properties" in b),
                schema,
            )
        elif isinstance(value, list):
            schema = next((b for b in choices if b.get("type") == "array"), schema)
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key, child in value.items():
            if key not in properties:
                raise ValueError(f"extra field at {path}/{key}")
            if key != "counterexample":
                _reject_unknown_fields(child, properties[key], root, f"{path}/{key}")
    elif isinstance(value, list):
        item_schema = schema.get("items", {})
        for index, child in enumerate(value):
            _reject_unknown_fields(child, item_schema, root, f"{path}/{index}")


class WireContract(Generic[CanonicalOutput]):
    """Deterministic transport -> canonical compiler interface."""

    def __init__(
        self,
        contract_id: str,
        wire_model: type[BaseModel],
        canonical_model: type[CanonicalOutput],
        *,
        aliases: AliasTable | None = None,
        variant: str = "direct",
        discharge_enabled: bool = False,
    ) -> None:
        self.contract_id = contract_id
        self.wire_model = wire_model
        self.canonical_model = canonical_model
        self.aliases = aliases or AliasTable()
        self.variant = variant
        # Default OFF for every contract, so a run with the discharge channel
        # disabled emits the schema bytes it emitted before the channel
        # existed. `CompactConjectureCandidate` is embedded by contracts this
        # tranche has no business changing, and committed tests read its `$def`
        # properties directly.
        self.discharge_enabled = discharge_enabled

    #: Fields whose values must be call-local aliases. Named here so the
    #: schema can state the legal set instead of leaving the model to guess
    #: it from the prompt, which is where the 20B battery's handle and
    #: namespace violations came from.
    ALIAS_ARRAY_FIELDS: tuple[str, ...] = ()
    ALIAS_SCALAR_FIELDS: tuple[str, ...] = ()

    def model_json_schema(self) -> dict:
        schema = _strict_schema(self.wire_model.model_json_schema())
        self._bind_alias_fields(schema)
        self._bind_discharge_field(schema)
        return schema

    def _bind_discharge_field(self, schema: dict) -> None:
        """Prune `discharges` unless this contract opted in.

        Absence has to be TOTAL, not merely a property removal: `prune_property`
        also drops the constraints that still name the field, because
        `additionalProperties: false` beside a surviving `allOf` branch
        advertising it yields a schema no document can satisfy. The `$def`
        itself goes too, so a pruned schema is byte-indistinguishable from one
        built before the field was declared.
        """
        definitions = schema.get("$defs", {})
        if self.discharge_enabled:
            return
        for definition in (schema, *definitions.values()):
            if isinstance(definition, dict):
                prune_property(definition, "discharges")
        definitions.pop("DischargeWireV1", None)

    def _bind_alias_fields(self, schema: dict) -> None:
        """Name the legal aliases in the schema, as an enum.

        `AliasTable.resolve` refuses anything outside the table, so the legal
        set is known at render time and there is no reason to make the model
        infer it. Binding is skipped when the table is empty: an empty enum is
        unsatisfiable, and a contract with no aliases cannot be answered
        anyway — better to leave the field open than to emit a schema no
        document can satisfy.
        """

        legal = sorted(self.aliases.aliases)
        if not legal:
            return
        # An alias-bearing field is as often on a nested item model as on the
        # response root — the defender's clauses are a $def — so every
        # property map in the document is a candidate.
        maps = [schema.get("properties", {})]
        maps.extend(
            definition.get("properties", {})
            for definition in schema.get("$defs", {}).values()
            if isinstance(definition, dict)
        )
        for name in self.ALIAS_ARRAY_FIELDS:
            for properties in maps:
                field = properties.get(name)
                if isinstance(field, dict):
                    field["items"] = {"type": "string", "enum": list(legal)}
        for name in self.ALIAS_SCALAR_FIELDS:
            for properties in maps:
                field = properties.get(name)
                if not isinstance(field, dict):
                    continue
                # A field defaulting to "" uses the empty string to mean "no
                # alias", so the enum must keep it or the default becomes
                # illegal — the pairwise judge's `neither` verdict needs it.
                values = list(legal)
                if field.get("default") == "":
                    values = ["", *values]
                field["enum"] = values
                field["type"] = "string"

    def _menu_binding(self, value: Any) -> Any:
        """The call-local facts this contract's reference menus were built
        from, or None when it declares none.

        Overridden by the contracts that carry a legal handle set. The
        default returns None, so index resolution is a no-op everywhere it
        was not declared -- a contract cannot acquire the behaviour by
        accident.
        """

        return None

    def _resolve_menu_indices(self, value: Any) -> Any:
        """Turn a seat's `[2]` into the handle its menu showed at index 2.

        Runs before every firewall and validator, and can only ever replace
        an index token -- which no registered field's grammar admits as a
        handle -- with a value the menu already listed as legal.
        """

        binding = self._menu_binding(value)
        if binding is None:
            return value
        from deepreason.llm.reference_menu import resolve_indices_in

        return resolve_indices_in(value, self.contract_id, binding)

    def _preflight_value(self, value: Any) -> None:
        """Apply transport firewalls before contract-specific validation."""

        _reject_control_fields(value)
        schema = self.model_json_schema()
        _reject_unknown_fields(value, schema, schema)

    def validate_value(self, value: Any) -> BaseModel:
        if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
            # An unambiguous single-element array wrapping the one expected
            # object is transport noise, tolerated exactly like a narrated
            # code fence.  Observed live: a fully qualified model wrapped a
            # valid atomic candidate in [] and the resulting object-wide
            # extra-field error had no finite repair, terminally exhausting
            # the route seat's smallest contract.  Multiple elements or
            # nested wrappers still fail exact validation unchanged.
            value = value[0]
        self._preflight_value(value)
        # AFTER the control-field firewall, never before it: resolution reads
        # model output, and the firewall exists so that nothing the model
        # writes becomes process authority. Resolution can only replace a
        # value with one this call already listed as legal, or delete an
        # optional one -- it never adds a key -- but it still runs downstream
        # of the firewall so the ordering needs no argument to be safe.
        value = self._resolve_menu_indices(value)
        try:
            return self.wire_model.model_validate(value)
        except ValidationError as error:
            # Diagnostic sourcing: a reference-bearing field's legal set is
            # durable contract state, and a rejection that carries it can
            # name the legal handles instead of only the pattern that failed.
            # Attached, never consulted for validity.
            blocks = getattr(self, "citable_block_ids", ())
            if blocks:
                error.citable_block_ids = blocks
            raise

    def validate_json(self, raw: str) -> BaseModel:
        return self.validate_value(parse_one_json_value(raw).value)

    def compile(self, wire: BaseModel) -> CanonicalOutput:
        if self.wire_model is self.canonical_model:
            return self.canonical_model.model_validate(wire.model_dump())
        raise NotImplementedError(self.contract_id)

    def parse_compile(self, raw: str) -> CanonicalOutput:
        return self.compile(self.validate_json(raw))


class DirectWireContract(WireContract[CanonicalOutput]):
    def __init__(self, canonical_model: type[CanonicalOutput]) -> None:
        name = canonical_model.__name__.removesuffix("Output").lower()
        super().__init__(f"{name}.direct.v1", canonical_model, canonical_model)

class RepairPatchWireContract(WireContract[RepairPatchV1]):
    """One local patch response under the frozen parent contract identity."""

    def __init__(
        self,
        parent_contract_id: str,
        envelope: RepairDiagnosticEnvelopeV2,
    ) -> None:
        if envelope.contract != parent_contract_id:
            raise ValueError("repair envelope does not match the parent contract")
        self.envelope = envelope
        super().__init__(
            parent_contract_id,
            RepairPatchV1,
            RepairPatchV1,
            variant="repair-patch-v1",
        )

    def model_json_schema(self) -> dict:
        return repair_patch_response_schema(self.envelope)

    def validate_value(self, value: Any) -> BaseModel:
        # Keep exact agreement with V6PatchRepairSession.candidate_from_raw:
        # both boundaries strip the same unambiguous patch wrappers, so a
        # patch the session applies is never re-rejected at admission.
        return super().validate_value(tolerant_patch_value(value, self.envelope))

    def compile(self, wire: RepairPatchV1) -> RepairPatchV1:
        # The generic identity compiler dumps defaults before revalidation.
        # That would turn an omitted remove-patch value into value null
        # and falsely reject the already validated frozen patch.
        return wire


class CompactConjectureCandidate(StrictWireModel):
    content: str = Field(min_length=1)
    typicality: float = Field(ge=0.0, le=1.0)
    neighbours: list[str] = Field(default_factory=list)
    # Optional claimed groundings in admitted evidence blocks (admission §4).
    # The claim model is already strict and frozen, so it serves as its own
    # wire shape; citations are byte-checked after admission, never trusted.
    evidence_refs: list[EvidenceRefClaimV1] = Field(default_factory=list, max_length=8)
    # Additive and optional, so the candidate's own wire TYPE never changes and
    # no contract-version bump is owed -- the same narrower alternative
    # `ReasoningCandidateProposal.checker_specs` took for the same reason.
    # OPTIONAL is also R4: an undischarged submission is returned once and then
    # accepted with a disclosure, so a required field would make the wire
    # enforce a gate the design forbids, and no re-ask could be attempted
    # because the reply would not parse.
    discharges: list[DischargeWireV1] = Field(default_factory=list, max_length=32)


class CompactConjecturer(StrictWireModel):
    candidates: list[CompactConjectureCandidate] = Field(min_length=1)


class ConjecturerWireContract(WireContract[ConjecturerOutput]):
    def __init__(
        self, aliases: AliasTable | None = None, *, discharge_enabled: bool = False
    ) -> None:
        super().__init__(
            "conjecturer.compact.v1",
            CompactConjecturer,
            ConjecturerOutput,
            aliases=aliases,
            variant="compact",
            discharge_enabled=discharge_enabled,
        )

    def compile(self, wire: CompactConjecturer) -> ConjecturerOutput:
        return ConjecturerOutput(
            candidates=[
                ConjectureCandidate(
                    content=item.content,
                    typicality=item.typicality,
                    refs=[CandidateRef(target=self.aliases.resolve(a)) for a in item.neighbours],
                    evidence_refs=list(item.evidence_refs),
                )
                for item in wire.candidates
            ]
        )


class AtomicConjectureCandidateWireV1(StrictWireModel):
    """One bounded candidate slot or an honest no-candidate outcome.

    The exactly-one rule is in the schema, not only in the validator below.
    """

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        json_schema_extra=exclusive_fields_schema(("candidate", "abstention")),
    )

    candidate: CompactConjectureCandidate | None = None
    abstention: ConjectureAbstentionV1 | None = None

    @model_validator(mode="after")
    def _exactly_one_outcome(self):
        if (self.candidate is None) == (self.abstention is None):
            raise ValueError(
                "atomic conjecture requires exactly one candidate or abstention"
            )
        return self


class AtomicReasoningConjectureCandidateWireV1(StrictWireModel):
    """One bounded reasoning-envelope candidate or honest abstention.

    The exactly-one rule is in the schema, not only in the validator below.
    """

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        json_schema_extra=exclusive_fields_schema(("candidate", "abstention")),
    )

    candidate: ReasoningCandidateProposal | None = None
    abstention: ConjectureAbstentionV1 | None = None

    @model_validator(mode="after")
    def _exactly_one_outcome(self):
        if (self.candidate is None) == (self.abstention is None):
            raise ValueError(
                "atomic reasoning conjecture requires exactly one candidate or abstention"
            )
        return self


class AtomicConjectureWireContractV1(WireContract[BaseModel]):
    """Separately named single-candidate contract for authorized decomposition."""

    def __init__(
        self,
        aliases: AliasTable,
        *,
        reasoning: bool = False,
        discharge_enabled: bool = False,
    ) -> None:
        self.reasoning = bool(reasoning)
        self.visible_aliases = tuple(sorted(aliases.aliases))
        super().__init__(
            ATOMIC_CONJECTURE_CONTRACT_V1,
            (
                AtomicReasoningConjectureCandidateWireV1
                if self.reasoning
                else AtomicConjectureCandidateWireV1
            ),
            ReasoningConjecturerTurnV6 if self.reasoning else ConjectureTurnV6,
            aliases=aliases,
            variant="atomic.v1",
            discharge_enabled=discharge_enabled,
        )

    def model_json_schema(self) -> dict:
        schema = super().model_json_schema()
        definitions = schema.get("$defs", {})
        candidate = definitions.get(
            "ReasoningCandidateProposal"
            if self.reasoning
            else "CompactConjectureCandidate",
            {},
        )
        reference_field = candidate.get("properties", {}).get(
            "optional_refs" if self.reasoning else "neighbours"
        )
        if isinstance(reference_field, dict):
            if self.visible_aliases:
                reference_field["items"] = {
                    "enum": list(self.visible_aliases),
                    "type": "string",
                }
            else:
                reference_field["maxItems"] = 0
        if self.reasoning:
            sidecar = definitions.get("OperationalSidecar", {})
            requested = sidecar.get("properties", {}).get(
                "requested_context_aliases"
            )
            if isinstance(requested, dict):
                if self.visible_aliases:
                    requested["items"] = {
                        "enum": list(self.visible_aliases),
                        "type": "string",
                    }
                else:
                    requested["maxItems"] = 0
        return schema

    def validate_value(self, value: Any) -> BaseModel:
        # A bare candidate payload (the candidate's inner fields at top
        # level, no {"candidate": ...} envelope) is an unambiguous slip
        # observed live: the envelope has no fields besides candidate and
        # abstention, and no abstention payload shares the candidate's
        # required marker field, so re-enveloping is lossless.  Anything
        # containing an envelope key, or missing the marker, is left for
        # exact validation unchanged.
        marker = "claim" if self.reasoning else "content"
        if (
            isinstance(value, dict)
            and marker in value
            and not ({"candidate", "abstention"} & set(value))
        ):
            value = {"candidate": value}
        return super().validate_value(value)

    def compile(self, wire: BaseModel) -> BaseModel:
        if wire.abstention is not None:
            model = ReasoningConjecturerTurnV6 if self.reasoning else ConjectureTurnV6
            return model(abstention=wire.abstention)
        assert wire.candidate is not None
        candidate = wire.candidate
        if self.reasoning:
            requested = tuple(
                self.aliases.resolve(alias)
                for alias in candidate.sidecar.requested_context_aliases
            )
            return ReasoningConjecturerTurnV6(
                candidates=(
                    ReasoningCandidateProposal(
                        claim=candidate.claim,
                        mechanism=candidate.mechanism,
                        counterconditions=candidate.counterconditions,
                        typicality=candidate.typicality,
                        optional_refs=tuple(
                            self.aliases.resolve(alias)
                            for alias in candidate.optional_refs
                        ),
                        evidence_refs=candidate.evidence_refs,
                        analogy=candidate.analogy,
                        sidecar=OperationalSidecar(
                            search_signal=candidate.sidecar.search_signal,
                            requested_context_aliases=requested,
                        ),
                    ),
                )
            )
        return ConjectureTurnV6(
            candidates=(
                ConjectureCandidate(
                    content=candidate.content,
                    typicality=candidate.typicality,
                    refs=tuple(
                        CandidateRef(target=self.aliases.resolve(alias))
                        for alias in candidate.neighbours
                    ),
                    evidence_refs=list(candidate.evidence_refs),
                ),
            )
        )


class ReferenceFreeConjectureCandidate(StrictWireModel):
    """Compact conjecture value for schedulers that cannot preserve refs."""

    content: str = Field(min_length=1)
    typicality: float = Field(ge=0.0, le=1.0)


class ReferenceFreeConjecturer(StrictWireModel):
    candidates: list[ReferenceFreeConjectureCandidate] = Field(min_length=1)


class ReferenceFreeConjecturerWireContract(WireContract[ConjecturerOutput]):
    """Compact transport that explicitly omits unsupported references.

    This is distinct from a reference-bearing contract with an empty alias
    table: the model-visible schema has no ``neighbours`` field to invent,
    and compilation cannot imply that references were preserved.
    """

    def __init__(self) -> None:
        super().__init__(
            "conjecturer.compact.reference_free.v1",
            ReferenceFreeConjecturer,
            ConjecturerOutput,
            variant="compact",
        )

    def compile(self, wire: ReferenceFreeConjecturer) -> ConjecturerOutput:
        return ConjecturerOutput(
            candidates=[
                ConjectureCandidate(
                    content=item.content,
                    typicality=item.typicality,
                )
                for item in wire.candidates
            ]
        )


class ReasoningConjecturerWireContract(WireContract[ReasoningConjecturerOutput]):
    """Compact-v2 reasoning values with harness-resolved optional aliases."""

    def __init__(self, aliases: AliasTable) -> None:
        super().__init__(
            "reasoning.conjecturer.compact.v2",
            ReasoningConjecturerOutput,
            ReasoningConjecturerOutput,
            aliases=aliases,
            variant="compact.v2",
        )

    def compile(self, wire: ReasoningConjecturerOutput) -> ReasoningConjecturerOutput:
        candidates = []
        for candidate in wire.candidates:
            optional_refs = tuple(
                self.aliases.resolve(alias) for alias in candidate.optional_refs
            )
            requested = tuple(
                self.aliases.resolve(alias)
                for alias in candidate.sidecar.requested_context_aliases
            )
            candidates.append(
                ReasoningCandidateProposal(
                    claim=candidate.claim,
                    mechanism=candidate.mechanism,
                    counterconditions=candidate.counterconditions,
                    typicality=candidate.typicality,
                    optional_refs=optional_refs,
                    evidence_refs=candidate.evidence_refs,
                    sidecar=OperationalSidecar(
                        search_signal=candidate.sidecar.search_signal,
                        requested_context_aliases=requested,
                    ),
                )
            )
        return ReasoningConjecturerOutput(candidates=tuple(candidates))


_HTTPS_URL = r"^https://[^\s]{1,2048}$"
_V1_VISIBLE_ALIAS = r"^[ABCLG][1-9][0-9]{0,4}$"
_V2_VISIBLE_ALIAS = r"^(?:SRC|SCR)_[0-9]{3}$"
"""The alias namespaces `_visible_alias_syntax` enforces, said in the schema.

A namespace stated only in prose is the failure the 20B battery produced
first: handles invented in the right shape but the wrong namespace.
"""

_UNIQUE_ITEMS = {"uniqueItems": True}
"""Duplicates are refused by `_unique_values`; the schema must say so too."""


CONTEXT_REQUEST_SELECTOR_SHAPE = outcome_shape_schema(
    meaningful=("query", "requested_visible_aliases", "desired_retrieval_channels")
)
"""`_has_semantic_selector`, for both context-request versions.

They are siblings rather than a chain, so the encoder is attached to each;
they carry the same rule over the same field names and differ only in alias
syntax.
"""


class ContextRequestWireV1(StrictWireModel):
    """Only call-local aliases and bounded semantic search material."""

    model_config = ConfigDict(
        extra="forbid", strict=True, json_schema_extra=CONTEXT_REQUEST_SELECTOR_SHAPE
    )

    query: str | None = Field(default=None, min_length=1, max_length=8_192)
    requested_visible_aliases: list[str] = Field(
        default_factory=list,
        max_length=64,
        json_schema_extra={
            **_UNIQUE_ITEMS,
            # `items` REPLACES the rendered one, so the type must be restated:
            # `pattern` constrains only strings and a number would slip past it.
            "items": {"type": "string", "pattern": _V1_VISIBLE_ALIAS},
        },
    )
    desired_retrieval_channels: list[str] = Field(
        default_factory=list, max_length=16, json_schema_extra=_UNIQUE_ITEMS
    )
    purpose: str | None = Field(default=None, min_length=1, max_length=4_096)

    @model_validator(mode="after")
    def _has_semantic_selector(self):
        if not (
            self.query
            or self.requested_visible_aliases
            or self.desired_retrieval_channels
        ):
            raise ValueError(
                "context request requires a query, visible alias, or channel"
            )
        return self

    @field_validator("requested_visible_aliases", "desired_retrieval_channels")
    @classmethod
    def _unique_values(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("context request values must not contain duplicates")
        return value

    @field_validator("requested_visible_aliases")
    @classmethod
    def _visible_alias_syntax(cls, value):
        for alias in value:
            if re.fullmatch(r"[ABCLG][1-9][0-9]{0,4}", alias) is None:
                raise ValueError(
                    "requested context must use a visible A*, B*, C*, L*, or G* alias"
                )
        return value


class ContextRequestWireV2(StrictWireModel):
    """V6 semantic retrieval using only SRC_### and SCR_### handles."""

    model_config = ConfigDict(
        extra="forbid", strict=True, json_schema_extra=CONTEXT_REQUEST_SELECTOR_SHAPE
    )

    query: str | None = Field(default=None, min_length=1, max_length=8_192)
    requested_visible_aliases: list[str] = Field(
        default_factory=list,
        max_length=64,
        json_schema_extra={
            **_UNIQUE_ITEMS,
            "items": {"type": "string", "pattern": _V2_VISIBLE_ALIAS},
        },
    )
    desired_retrieval_channels: list[str] = Field(
        default_factory=list, max_length=16, json_schema_extra=_UNIQUE_ITEMS
    )
    purpose: str | None = Field(default=None, min_length=1, max_length=4_096)

    @model_validator(mode="after")
    def _has_semantic_selector(self):
        if not (
            self.query
            or self.requested_visible_aliases
            or self.desired_retrieval_channels
        ):
            raise ValueError(
                "context request requires a query, visible alias, or channel"
            )
        return self

    @field_validator("requested_visible_aliases", "desired_retrieval_channels")
    @classmethod
    def _unique_values(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("context request values must not contain duplicates")
        return value

    @field_validator("requested_visible_aliases")
    @classmethod
    def _visible_alias_syntax(cls, value):
        for alias in value:
            if re.fullmatch(r"(?:SRC|SCR)_[0-9]{3}", alias) is None:
                raise ValueError(
                    "requested context must use a visible SRC_### or SCR_### alias"
                )
        return value

TURN_OUTCOME_SHAPE = outcome_shape_schema(
    meaningful=(
        "candidates",
        "context_request",
        "abstention",
        "simulation_proposals",
        "scratch_proposal",
        "research_proposals",
    ),
    abstention="abstention",
    abstention_excludes=(
        "candidates",
        "simulation_proposals",
        "scratch_proposal",
        "research_proposals",
    ),
)
"""The two turn outcome rules, declared once for every version that has them.

Named here as the SUPERSET across v4, v5 and v6 and attached to each chain's
base class, because ``json_schema_extra`` is inherited: attaching a v4-shaped
tuple would make a simulation-only v5 turn schema-invalid while the validator
still accepts it, which is a false reject on a live path. ``outcome_shape_schema``
filters by RENDERED properties, so v4 emits three branches, v5 four and v6 six —
each exactly matching that version's own ``_meaningful_*_outcome`` validator.
A future v7 outcome field is then one edit here, not six.
"""


class ConjecturerTurnWireV4(StrictWireModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, json_schema_extra=TURN_OUTCOME_SHAPE
    )

    candidates: list[CompactConjectureCandidate] = Field(
        default_factory=list, max_length=256
    )
    context_request: ContextRequestWireV1 | None = None
    abstention: ConjectureAbstentionV1 | None = None

    @model_validator(mode="after")
    def _meaningful_outcome(self):
        simulations = getattr(self, "simulation_proposals", ())
        if not (self.candidates or self.context_request or self.abstention or simulations):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and (self.candidates or simulations):
            raise ValueError("abstention cannot accompany semantic proposals")
        return self


class ReasoningConjecturerTurnWireV4(StrictWireModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, json_schema_extra=TURN_OUTCOME_SHAPE
    )

    candidates: list[ReasoningCandidateProposal] = Field(
        default_factory=list, max_length=256
    )
    context_request: ContextRequestWireV1 | None = None
    abstention: ConjectureAbstentionV1 | None = None

    @model_validator(mode="after")
    def _meaningful_outcome(self):
        simulations = getattr(self, "simulation_proposals", ())
        if not (self.candidates or self.context_request or self.abstention or simulations):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and (self.candidates or simulations):
            raise ValueError("abstention cannot accompany semantic proposals")
        return self


class ConjecturerTurnWireContractV4(WireContract[BaseModel]):
    """Call-local v4 turn compiler shared by direct and compact profiles."""

    def __init__(
        self,
        *,
        reasoning: bool,
        aliases: AliasTable,
        scratch_aliases: Mapping[str, str] | None = None,
        permitted_retrieval_channels: tuple[str, ...] = (),
        discharge_enabled: bool = False,
    ) -> None:
        self.reasoning = reasoning
        self.scratch_aliases = MappingProxyType(dict(scratch_aliases or {}))
        if set(self.scratch_aliases) & set(aliases.aliases):
            raise ValueError("formal and scratch alias namespaces must not overlap")
        self.permitted_retrieval_channels = tuple(permitted_retrieval_channels)
        super().__init__(
            "conjecturer.turn.v4",
            ReasoningConjecturerTurnWireV4 if reasoning else ConjecturerTurnWireV4,
            ReasoningConjecturerTurnV4 if reasoning else ConjecturerTurnV4,
            aliases=aliases,
            variant="compact.v4",
            discharge_enabled=discharge_enabled,
        )

    def _resolve_context_alias(self, alias: str) -> str:
        if alias in self.scratch_aliases:
            return self.scratch_aliases[alias]
        return self.aliases.resolve(alias)

    def _compile_request(
        self, request: ContextRequestWireV1 | None
    ) -> ContextRequestV1 | None:
        if request is None:
            return None
        desired = tuple(request.desired_retrieval_channels)
        return ContextRequestV1(
            query=request.query,
            requested_refs=tuple(
                self._resolve_context_alias(alias)
                for alias in request.requested_visible_aliases
            ),
            desired_retrieval_channels=desired,
            purpose=request.purpose,
        )

    def compile(self, wire: BaseModel) -> BaseModel:
        request = self._compile_request(wire.context_request)
        if not self.reasoning:
            return ConjecturerTurnV4(
                candidates=tuple(
                    ConjectureCandidate(
                        content=item.content,
                        typicality=item.typicality,
                        refs=[
                            CandidateRef(target=self.aliases.resolve(alias))
                            for alias in item.neighbours
                        ],
                        evidence_refs=list(item.evidence_refs),
                    )
                    for item in wire.candidates
                ),
                context_request=request,
                abstention=wire.abstention,
            )

        candidates = []
        sidecar_refs: list[str] = []
        for candidate in wire.candidates:
            optional_refs = tuple(
                self.aliases.resolve(alias) for alias in candidate.optional_refs
            )
            requested = tuple(
                self._resolve_context_alias(alias)
                for alias in candidate.sidecar.requested_context_aliases
            )
            sidecar_refs.extend(requested)
            candidates.append(
                ReasoningCandidateProposal(
                    claim=candidate.claim,
                    mechanism=candidate.mechanism,
                    counterconditions=candidate.counterconditions,
                    typicality=candidate.typicality,
                    optional_refs=optional_refs,
                    evidence_refs=candidate.evidence_refs,
                    analogy=AnalogyClaim.model_validate(candidate.analogy)
                    if candidate.analogy is not None
                    else None,
                    sidecar=OperationalSidecar(
                        search_signal=candidate.sidecar.search_signal,
                        requested_context_aliases=requested,
                    ),
                )
            )
        if sidecar_refs:
            combined_refs = tuple(
                dict.fromkeys(
                    [
                        *(request.requested_refs if request is not None else ()),
                        *sidecar_refs,
                    ]
                )
            )
            if request is None:
                request = ContextRequestV1(requested_refs=combined_refs)
            else:
                request = ContextRequestV1(
                    query=request.query,
                    requested_refs=combined_refs,
                    desired_retrieval_channels=request.desired_retrieval_channels,
                    purpose=request.purpose,
                )
        return ReasoningConjecturerTurnV4(
            candidates=tuple(candidates),
            context_request=request,
            abstention=wire.abstention,
        )


SIMULATION_MODEL_SOURCE_CONTRACT = (
    "The program itself; its required shape follows simulation_mode. For "
    "sandboxed_python_v1 the entire source must be exactly one function "
    "definition and nothing else: def simulate(inputs, rng), with no "
    "imports, no statements outside it, no decorators, no return "
    "annotation, and no default, keyword-only, or variadic arguments. It "
    "is called once per (input, seed) pair, where inputs is one mapping "
    "carrying parameter_set, parameters, and sealed_inputs, and rng is a "
    "seeded random.Random. It must return a JSON-safe mapping of "
    "observable name to finite value; that mapping is the only output "
    "recorded, so printing reports nothing. math is available and nothing "
    "else may be imported. For declarative_numeric_v1 this field is a JSON "
    "document instead of Python."
)
SIMULATION_REQUESTED_OBSERVABLES_CONTRACT = (
    "The observable names this proposal is judged on. Each is an identifier, "
    "or up to eight identifiers joined by dots to reach into a nested result "
    "(a.b.c tries the literal key a.b.c first, then walks a, then b, then c). "
    "Every name must resolve in what the program produces: for "
    "sandboxed_python_v1 in the mapping simulate returns, for "
    "declarative_numeric_v1 among the document's observables. The two sets "
    "must match exactly. A name that does not resolve ends the run with "
    "declared observable missing, so stream names like stdout are never "
    "observables."
)


class SimulationParameterSetWireV1(StrictWireModel):
    name: str = Field(min_length=1, max_length=128)
    # Canonical JSON text keeps arbitrary finite numerical arrays inside one
    # bounded semantic field without turning object keys into a shadow schema.
    values_json: str = Field(min_length=2, max_length=262_144)


class SimulationProposalWireV1(StrictWireModel):
    request_identifier: str = Field(min_length=1, max_length=128)
    hypothesis: str = Field(min_length=1, max_length=16_384)
    rival_predictions: list[str] = Field(
        min_length=1, max_length=32, json_schema_extra=_UNIQUE_ITEMS
    )
    discriminating_purpose: str = Field(min_length=1, max_length=8_192)
    declared_assumptions: list[str] = Field(
        default_factory=list, max_length=64, json_schema_extra=_UNIQUE_ITEMS
    )
    input_aliases: list[SealedInputAlias] = Field(
        default_factory=list, max_length=64, json_schema_extra=_UNIQUE_ITEMS
    )
    parameter_definitions: list[SimulationParameterSetWireV1] = Field(
        default_factory=list, max_length=256
    )
    requested_seed_set: list[SimulationSeed] = Field(
        default_factory=list, max_length=256, json_schema_extra=_UNIQUE_ITEMS
    )
    simulation_mode: Literal[
        "declarative_numeric_v1", "sandboxed_python_v1"
    ]
    # These two descriptions are the only place the harness states the program
    # contract to the author of the program: the sandbox validator and the
    # contained runner enforce it, and the model sees nothing but this schema.
    # They must track validate_sandboxed_python_source and the runner's
    # declared-observable check.
    model_source: str = Field(
        min_length=1,
        max_length=262_144,
        description=SIMULATION_MODEL_SOURCE_CONTRACT,
    )
    # The pattern lives on the item type, not in json_schema_extra: the wire
    # model must REFUSE what the draft refuses, not merely advertise it.
    requested_observables: list[ObservableName] = Field(
        min_length=1,
        max_length=128,
        description=SIMULATION_REQUESTED_OBSERVABLES_CONTRACT,
        json_schema_extra=_UNIQUE_ITEMS,
    )
    interpretation_conditions: list[str] = Field(
        min_length=1, max_length=64, json_schema_extra=_UNIQUE_ITEMS
    )


class ResearchFetchProposalWireV1(StrictWireModel):
    """Directed-fetch intent on the v6 wire: explicit https URLs only.

    The model proposes sources; the harness alone validates them against
    the frozen domain allowlist and executes them under containment. The
    wire shape mirrors ResearchFetchProposalDraftV1 exactly — which it did
    not: the draft rejects a non-https or duplicated URL and the wire took
    both, so the refusal landed in compile() after the response had been
    accepted, and the schema advertised neither rule.
    """

    request_identifier: str = Field(min_length=1, max_length=128)
    purpose: str = Field(min_length=1, max_length=2_000)
    urls: list[str] = Field(
        min_length=1,
        max_length=3,
        json_schema_extra={
            **_UNIQUE_ITEMS,
            "items": {"type": "string", "pattern": _HTTPS_URL},
        },
    )

    @field_validator("urls")
    @classmethod
    def _https_and_unique(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("research proposal urls must not contain duplicates")
        if any(re.fullmatch(_HTTPS_URL, url) is None for url in value):
            raise ValueError("research proposal urls must be bounded https URLs")
        return value


class ConjecturerTurnWireV5(ConjecturerTurnWireV4):
    simulation_proposals: list[SimulationProposalWireV1] = Field(
        default_factory=list, max_length=32
    )

    @model_validator(mode="after")
    def _meaningful_v5_outcome(self):
        if not (
            self.candidates
            or self.context_request
            or self.abstention
            or self.simulation_proposals
        ):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and (
            self.candidates or self.simulation_proposals
        ):
            raise ValueError("abstention cannot accompany semantic proposals")
        return self


class ReasoningConjecturerTurnWireV5(ReasoningConjecturerTurnWireV4):
    simulation_proposals: list[SimulationProposalWireV1] = Field(
        default_factory=list, max_length=32
    )

    @model_validator(mode="after")
    def _meaningful_v5_outcome(self):
        if not (
            self.candidates
            or self.context_request
            or self.abstention
            or self.simulation_proposals
        ):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and (
            self.candidates or self.simulation_proposals
        ):
            raise ValueError("abstention cannot accompany semantic proposals")
        return self


class ConjecturerTurnWireV6(ConjecturerTurnWireV5):
    # The outcome rules are carried by the schema too, not only by the
    # validators, so a model reading the schema cannot emit a structurally
    # valid turn that the harness then refuses. Inherited from
    # ConjecturerTurnWireV4 via TURN_OUTCOME_SHAPE; the encoder narrows itself
    # to the properties this version actually renders.

    context_request: ContextRequestWireV2 | None = None
    scratch_proposal: ScratchProposalV1 | None = None
    research_proposals: list[ResearchFetchProposalWireV1] = Field(
        default_factory=list, max_length=2
    )

    @model_validator(mode="after")
    def _meaningful_outcome(self):
        return self._meaningful_v6_outcome()

    @model_validator(mode="after")
    def _meaningful_v5_outcome(self):
        return self._meaningful_v6_outcome()

    def _meaningful_v6_outcome(self):
        if not (
            self.candidates
            or self.context_request
            or self.abstention
            or self.simulation_proposals
            or self.scratch_proposal
            or self.research_proposals
        ):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and (
            self.candidates
            or self.simulation_proposals
            or self.scratch_proposal
            or self.research_proposals
        ):
            raise ValueError("abstention cannot accompany semantic proposals")
        return self


class ReasoningConjecturerTurnWireV6(ReasoningConjecturerTurnWireV5):
    context_request: ContextRequestWireV2 | None = None
    scratch_proposal: ScratchProposalV1 | None = None
    research_proposals: list[ResearchFetchProposalWireV1] = Field(
        default_factory=list, max_length=2
    )

    @model_validator(mode="after")
    def _meaningful_outcome(self):
        return self._meaningful_v6_outcome()

    @model_validator(mode="after")
    def _meaningful_v5_outcome(self):
        return self._meaningful_v6_outcome()

    def _meaningful_v6_outcome(self):
        if not (
            self.candidates
            or self.context_request
            or self.abstention
            or self.simulation_proposals
            or self.scratch_proposal
            or self.research_proposals
        ):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and (
            self.candidates
            or self.simulation_proposals
            or self.scratch_proposal
            or self.research_proposals
        ):
            raise ValueError("abstention cannot accompany semantic proposals")
        return self


class ConjecturerTurnWireContractV5(ConjecturerTurnWireContractV4):
    """Tranche-A compiler; simulation values remain semantic drafts."""

    def __init__(
        self,
        *,
        reasoning: bool,
        aliases: AliasTable,
        scratch_aliases: Mapping[str, str] | None = None,
        permitted_retrieval_channels: tuple[str, ...] = (),
        maximum_simulation_proposals: int = 0,
        discharge_enabled: bool = False,
    ) -> None:
        self.maximum_simulation_proposals = maximum_simulation_proposals
        ConjecturerTurnWireContractV4.__init__(
            self,
            reasoning=reasoning,
            aliases=aliases,
            scratch_aliases=scratch_aliases,
            permitted_retrieval_channels=permitted_retrieval_channels,
            discharge_enabled=discharge_enabled,
        )
        self.contract_id = "conjecturer.turn.v5"
        self.wire_model = (
            ReasoningConjecturerTurnWireV5
            if reasoning
            else ConjecturerTurnWireV5
        )
        self.canonical_model = (
            ReasoningConjecturerTurnV5 if reasoning else ConjecturerTurnV5
        )
        self.variant = "compact.v5"

    def compile(self, wire: BaseModel) -> BaseModel:
        if len(wire.simulation_proposals) > self.maximum_simulation_proposals:
            raise ValueError("simulation proposal count exceeds frozen per-turn authority")
        if wire.candidates or wire.context_request or wire.abstention:
            base = ConjecturerTurnWireContractV4.compile(self, wire)
            values = base.model_dump(mode="python")
        else:
            # V4 intentionally rejects an empty ordinary outcome.  A
            # simulation-only v5 response is valid and binds no hidden
            # candidate merely to satisfy that older schema.
            values = {
                "candidates": (),
                "context_request": None,
                "abstention": None,
            }
        simulations = tuple(
            SimulationProposalDraftV1(
                request_identifier=item.request_identifier,
                hypothesis=item.hypothesis,
                rival_predictions=tuple(item.rival_predictions),
                discriminating_purpose=item.discriminating_purpose,
                declared_assumptions=tuple(item.declared_assumptions),
                input_aliases=tuple(item.input_aliases),
                parameter_definitions=tuple(
                    SimulationParameterSetV1(
                        name=parameters.name,
                        values=json.loads(parameters.values_json),
                    )
                    for parameters in item.parameter_definitions
                ),
                requested_seed_set=tuple(item.requested_seed_set),
                simulation_mode=item.simulation_mode,
                model_source=item.model_source,
                requested_observables=tuple(item.requested_observables),
                interpretation_conditions=tuple(item.interpretation_conditions),
            )
            for item in wire.simulation_proposals
        )
        values["simulation_proposals"] = simulations
        model = ReasoningConjecturerTurnV5 if self.reasoning else ConjecturerTurnV5
        return model.model_validate(values)


class ConjecturerTurnWireContractV6(ConjecturerTurnWireContractV5):
    """Manifest- and call-specialized transactional conjecture contract."""

    _SCRATCH_CEILINGS = (
        ("new_blocks", "maximum_new_blocks_per_turn"),
        ("revisions", "maximum_revisions_per_turn"),
        ("links", "maximum_links_per_turn"),
        ("unresolved_questions", "maximum_unresolved_questions_per_turn"),
        ("cluster_suggestions", "maximum_cluster_suggestions_per_turn"),
    )

    def __init__(
        self,
        *,
        reasoning: bool,
        aliases: AliasTable,
        scratch_aliases: Mapping[str, str] | None = None,
        permitted_retrieval_channels: tuple[str, ...] = (),
        simulation_enabled: bool = False,
        maximum_simulation_proposals: int = 0,
        simulation_input_aliases: Mapping[str, str] | tuple[str, ...] = (),
        scratch_authoring_policy: Any | None = None,
        research_enabled: bool = False,
        maximum_research_proposals: int = 0,
        citable_block_ids: tuple[str, ...] = (),
        contract_id: str = CONJECTURER_TURN_CONTRACT_V6,
        discharge_enabled: bool = False,
    ) -> None:
        formal = tuple(aliases.aliases)
        scratch = tuple((scratch_aliases or {}).keys())
        if isinstance(simulation_input_aliases, Mapping):
            simulation_inputs = tuple(simulation_input_aliases)
            if any(not value for value in simulation_input_aliases.values()):
                raise ValueError("simulation input catalog targets must be nonempty")
        else:
            simulation_inputs = tuple(simulation_input_aliases)
        self._require_namespace(formal, "SRC")
        self._require_namespace(scratch, "SCR")
        self._require_namespace(simulation_inputs, "SIM")
        all_visible = (*formal, *scratch, *simulation_inputs)
        if len(all_visible) != len(set(all_visible)):
            raise ValueError("v6 visible alias namespaces must be disjoint")
        if simulation_enabled:
            if not 1 <= maximum_simulation_proposals <= 32:
                raise ValueError(
                    "enabled simulation requires a per-turn maximum in 1..32"
                )
        elif maximum_simulation_proposals != 0:
            raise ValueError("disabled simulation must have a zero proposal maximum")
        if research_enabled:
            if not 1 <= maximum_research_proposals <= 2:
                raise ValueError(
                    "enabled research requires a per-turn maximum in 1..2"
                )
        elif maximum_research_proposals != 0:
            raise ValueError("disabled research must have a zero proposal maximum")

        # Diagnostic sourcing ONLY. Not read by `model_json_schema`, so the
        # form the model reads is unchanged whether or not a call knows which
        # blocks are citable -- pinned by
        # `tests/test_reference_menu.py::test_wire_schema_sha_does_not_move`.
        self.citable_block_ids = tuple(
            block for block in citable_block_ids if isinstance(block, str)
        )
        self.research_enabled = bool(research_enabled)
        self.maximum_research_proposals = maximum_research_proposals
        self.simulation_enabled = bool(simulation_enabled)
        self.simulation_input_aliases = tuple(sorted(simulation_inputs))
        self.visible_context_aliases = tuple(sorted((*formal, *scratch)))
        self.scratch_authoring_policy = scratch_authoring_policy
        self.scratch_authoring_enabled = bool(
            getattr(scratch_authoring_policy, "enabled", False)
        )
        ConjecturerTurnWireContractV5.__init__(
            self,
            reasoning=reasoning,
            aliases=aliases,
            scratch_aliases=scratch_aliases,
            permitted_retrieval_channels=permitted_retrieval_channels,
            maximum_simulation_proposals=maximum_simulation_proposals,
            discharge_enabled=discharge_enabled,
        )
        if contract_id not in (CONJECTURER_TURN_CONTRACT_V6, CONJECTURER_TURN_CONTRACT_V7):
            raise ValueError(f"unknown conjecturer-turn contract id: {contract_id}")
        self.contract_id = contract_id
        self.wire_model = (
            ReasoningConjecturerTurnWireV6
            if reasoning
            else ConjecturerTurnWireV6
        )
        self.canonical_model = (
            ReasoningConjecturerTurnV6 if reasoning else ConjectureTurnV6
        )
        self.variant = "compact.v6"

    @staticmethod
    def _require_namespace(aliases: tuple[str, ...], prefix: str) -> None:
        pattern = rf"^{prefix}_[0-9]{{3}}$"
        malformed = tuple(alias for alias in aliases if re.fullmatch(pattern, alias) is None)
        if malformed:
            raise ValueError(
                f"v6 {prefix} aliases must use {prefix}_###: {malformed!r}"
            )

    _omit_property = staticmethod(prune_property)

    @staticmethod
    def _bind_alias_array(
        node: dict[str, Any],
        name: str,
        aliases: tuple[str, ...],
    ) -> None:
        if not aliases:
            ConjecturerTurnWireContractV6._omit_property(node, name)
            return
        field = node.get("properties", {}).get(name)
        if isinstance(field, dict):
            field["items"] = {"enum": list(aliases), "type": "string"}

    def model_json_schema(self) -> dict:
        schema = super().model_json_schema()
        properties = schema.get("properties", {})
        if not self.simulation_enabled:
            self._omit_property(schema, "simulation_proposals")
        else:
            proposals = properties.get("simulation_proposals", {})
            proposals["maxItems"] = self.maximum_simulation_proposals
        if not self.scratch_authoring_enabled:
            self._omit_property(schema, "scratch_proposal")
        if not self.research_enabled:
            self._omit_property(schema, "research_proposals")
        else:
            research = properties.get("research_proposals", {})
            research["maxItems"] = self.maximum_research_proposals

        definitions = schema.get("$defs", {})
        if self.scratch_authoring_enabled:
            workshop_purpose = V6_SCRATCH_WORKSHOP_SCHEMA_DESCRIPTION
            properties.get("scratch_proposal", {})["description"] = workshop_purpose
            definitions.get("ScratchProposalV1", {})["description"] = workshop_purpose
        simulation = definitions.get("SimulationProposalWireV1", {})
        self._bind_alias_array(
            simulation,
            "input_aliases",
            self.simulation_input_aliases,
        )
        candidate_name = (
            "ReasoningCandidateProposal"
            if self.reasoning
            else "CompactConjectureCandidate"
        )
        candidate = definitions.get(candidate_name, {})
        self._bind_alias_array(
            candidate,
            "optional_refs" if self.reasoning else "neighbours",
            tuple(sorted(self.aliases.aliases)),
        )
        context = definitions.get("ContextRequestWireV2", {})
        self._bind_alias_array(
            context,
            "requested_visible_aliases",
            self.visible_context_aliases,
        )
        self._bind_alias_array(
            context,
            "desired_retrieval_channels",
            tuple(sorted(self.permitted_retrieval_channels)),
        )
        if self.reasoning:
            sidecar = definitions.get("OperationalSidecar", {})
            self._bind_alias_array(
                sidecar,
                "requested_context_aliases",
                self.visible_context_aliases,
            )
        if self.scratch_authoring_enabled:
            scratch = definitions.get("ScratchProposalV1", {})
            for field, policy_field in self._SCRATCH_CEILINGS:
                array_schema = scratch.get("properties", {}).get(field)
                if isinstance(array_schema, dict):
                    array_schema["maxItems"] = int(
                        getattr(self.scratch_authoring_policy, policy_field)
                    )
        return schema

    def _invalid_reference(
        self,
        pointer: str,
        alias: str,
        legal: tuple[str, ...],
    ) -> None:
        if alias not in legal:
            raise V6WireReferenceError(
                f"unknown v6 call-local alias {alias!r}",
                pointer=pointer,
                legal_handles=legal,
            )

    def _preflight_v6_references(self, value: Any) -> None:
        if not isinstance(value, dict):
            return
        scratch = value.get("scratch_proposal")
        if "scratch_proposal" in value and not self.scratch_authoring_enabled:
            raise V6WireReferenceError(
                "scratch_proposal is absent when scratch authoring is disabled",
                pointer="/scratch_proposal",
            )
        if self.scratch_authoring_enabled and isinstance(scratch, dict):
            for field, policy_field in self._SCRATCH_CEILINGS:
                items = scratch.get(field)
                maximum = int(getattr(self.scratch_authoring_policy, policy_field))
                if isinstance(items, (list, tuple)) and len(items) > maximum:
                    raise V6WireReferenceError(
                        f"scratch {field} exceeds frozen per-turn authority",
                        pointer=f"/scratch_proposal/{field}/{maximum}",
                    )
        research = value.get("research_proposals")
        if "research_proposals" in value and not self.research_enabled:
            raise V6WireReferenceError(
                "research_proposals is absent when research is disabled",
                pointer="/research_proposals",
            )
        if isinstance(research, list) and len(research) > self.maximum_research_proposals:
            raise V6WireReferenceError(
                "research proposal count exceeds frozen per-turn authority",
                pointer=(
                    "/research_proposals/"
                    f"{self.maximum_research_proposals}"
                ),
            )
        proposals = value.get("simulation_proposals")
        if "simulation_proposals" in value and not self.simulation_enabled:
            raise V6WireReferenceError(
                "simulation_proposals is absent when simulation is disabled",
                pointer="/simulation_proposals",
            )
        if isinstance(proposals, list):
            if len(proposals) > self.maximum_simulation_proposals:
                raise V6WireReferenceError(
                    "simulation proposal count exceeds frozen per-turn authority",
                    pointer=(
                        "/simulation_proposals/"
                        f"{self.maximum_simulation_proposals}"
                    ),
                )
            for index, proposal in enumerate(proposals):
                if not isinstance(proposal, dict):
                    continue
                inputs = proposal.get("input_aliases")
                pointer = f"/simulation_proposals/{index}/input_aliases"
                if "input_aliases" in proposal and not self.simulation_input_aliases:
                    raise V6WireReferenceError(
                        "input_aliases is absent when no simulation inputs exist",
                        pointer=pointer,
                    )
                if isinstance(inputs, list):
                    for item_index, alias in enumerate(inputs):
                        if isinstance(alias, str):
                            self._invalid_reference(
                                f"{pointer}/{item_index}",
                                alias,
                                self.simulation_input_aliases,
                            )

        candidates = value.get("candidates")
        if isinstance(candidates, list):
            source_aliases = tuple(sorted(self.aliases.aliases))
            for index, candidate in enumerate(candidates):
                if not isinstance(candidate, dict):
                    continue
                field = "optional_refs" if self.reasoning else "neighbours"
                refs = candidate.get(field)
                pointer = f"/candidates/{index}/{field}"
                if field in candidate and not source_aliases:
                    raise V6WireReferenceError(
                        f"{field} is absent when no formal sources exist",
                        pointer=pointer,
                    )
                if isinstance(refs, (list, tuple)):
                    for item_index, alias in enumerate(refs):
                        if isinstance(alias, str):
                            self._invalid_reference(
                                f"{pointer}/{item_index}",
                                alias,
                                source_aliases,
                            )
                if self.reasoning and isinstance(candidate.get("sidecar"), dict):
                    sidecar = candidate["sidecar"]
                    requested = sidecar.get(
                        "requested_context_aliases"
                    )
                    sidecar_pointer = (
                        f"/candidates/{index}/sidecar/requested_context_aliases"
                    )
                    if (
                        "requested_context_aliases" in sidecar
                        and not self.visible_context_aliases
                    ):
                        raise V6WireReferenceError(
                            "requested_context_aliases is absent when no visible "
                            "source or scratch catalog exists",
                            pointer=sidecar_pointer,
                        )
                    if isinstance(requested, (list, tuple)):
                        for item_index, alias in enumerate(requested):
                            if isinstance(alias, str):
                                self._invalid_reference(
                                    f"{sidecar_pointer}/{item_index}",
                                    alias,
                                    self.visible_context_aliases,
                                )

        request = value.get("context_request")
        if isinstance(request, dict):
            requested = request.get("requested_visible_aliases")
            requested_pointer = "/context_request/requested_visible_aliases"
            if (
                "requested_visible_aliases" in request
                and not self.visible_context_aliases
            ):
                raise V6WireReferenceError(
                    "requested_visible_aliases is absent when no visible source "
                    "or scratch catalog exists",
                    pointer=requested_pointer,
                )
            if isinstance(requested, list):
                for index, alias in enumerate(requested):
                    if isinstance(alias, str):
                        self._invalid_reference(
                            f"{requested_pointer}/{index}",
                            alias,
                            self.visible_context_aliases,
                        )
            channels = request.get("desired_retrieval_channels")
            channel_pointer = "/context_request/desired_retrieval_channels"
            if (
                "desired_retrieval_channels" in request
                and not self.permitted_retrieval_channels
            ):
                raise V6WireReferenceError(
                    "desired_retrieval_channels is absent when no retrieval "
                    "channels are permitted",
                    pointer=channel_pointer,
                )
            if isinstance(channels, list):
                legal_channels = tuple(sorted(self.permitted_retrieval_channels))
                for index, channel in enumerate(channels):
                    if isinstance(channel, str):
                        self._invalid_reference(
                            f"{channel_pointer}/{index}",
                            channel,
                            legal_channels,
                        )

    def _preflight_value(self, value: Any) -> None:
        self._preflight_v6_references(value)
        super()._preflight_value(value)

    def _attach_scratch_reference_context(
        self, error: Exception, value: Any
    ) -> None:
        """Attach the durable legal-handle state to a validation failure.

        Scratch-proposal reference fields (link endpoints, related_refs,
        member_refs, revision targets) are validated by pattern plus a closed
        local namespace, so their rejections would otherwise carry only a bare
        pattern diagnostic.  The legal set at this point is durable state the
        contract already holds: the run's visible SCR catalog plus the
        proposal's own NEW keys.  The diagnostic compiler uses this context
        for guidance only; validity is unchanged.
        """

        if not self.scratch_authoring_enabled:
            return
        new_keys: tuple[str, ...] = ()
        scratch = value.get("scratch_proposal") if isinstance(value, dict) else None
        if isinstance(scratch, dict):
            blocks = scratch.get("new_blocks")
            if isinstance(blocks, (list, tuple)):
                new_keys = tuple(
                    block.get("local_key")
                    for block in blocks
                    if isinstance(block, dict)
                    and isinstance(block.get("local_key"), str)
                )
        error.scratch_reference_context = {
            "scratch_handles": tuple(sorted(self.scratch_aliases)),
            "new_block_keys": new_keys,
        }

    def _menu_binding(self, value: Any) -> Any:
        from deepreason.llm.reference_menu import MenuBinding

        new_keys: tuple[str, ...] = ()
        scratch = value.get("scratch_proposal") if isinstance(value, dict) else None
        if isinstance(scratch, dict):
            blocks = scratch.get("new_blocks")
            if isinstance(blocks, (list, tuple)):
                new_keys = tuple(
                    block.get("local_key")
                    for block in blocks
                    if isinstance(block, dict)
                    and isinstance(block.get("local_key"), str)
                )
        return MenuBinding(
            citable_block_ids=self.citable_block_ids,
            scratch_handles=tuple(sorted(self.scratch_aliases)),
            new_block_keys=new_keys,
            aliases=tuple(self.aliases.aliases),
        )

    def validate_value(self, value: Any) -> BaseModel:
        # The strict proposal records intentionally use immutable tuples.
        # Validate through Pydantic's JSON boundary so JSON arrays are accepted
        # as tuples without enabling Python-side scalar coercion.
        self._preflight_value(value)
        value = self._resolve_menu_indices(value)
        raw = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        try:
            return self.wire_model.model_validate_json(raw)
        except ValidationError as error:
            self._attach_scratch_reference_context(error, value)
            error.citable_block_ids = self.citable_block_ids
            raise

    def compile(self, wire: BaseModel) -> BaseModel:
        # Defence in depth for callers compiling a constructed wire model
        # without first invoking validate_value/validate_json.
        self._preflight_v6_references(
            wire.model_dump(mode="python", exclude_unset=True)
        )
        scratch = getattr(wire, "scratch_proposal", None)
        research_wire = tuple(getattr(wire, "research_proposals", ()))
        if len(research_wire) > self.maximum_research_proposals:
            raise ValueError("research proposal count exceeds frozen per-turn authority")
        if not (
            wire.candidates
            or wire.context_request
            or wire.abstention
            or wire.simulation_proposals
        ) and (scratch is not None or research_wire):
            # V5 intentionally rejects an empty ordinary outcome. A
            # scratch-only or research-only v6 response is valid and binds
            # no hidden candidate merely to satisfy the older schema.
            values = {
                "candidates": (),
                "context_request": None,
                "abstention": None,
                "simulation_proposals": (),
            }
        else:
            compiled = ConjecturerTurnWireContractV5.compile(self, wire)
            values = compiled.model_dump(mode="python")
        values["scratch_proposal"] = scratch
        values["research_proposals"] = tuple(
            ResearchFetchProposalDraftV1(
                request_identifier=item.request_identifier,
                purpose=item.purpose,
                urls=tuple(item.urls),
            )
            for item in research_wire
        )
        model = ReasoningConjecturerTurnV6 if self.reasoning else ConjectureTurnV6
        return model.model_validate(values)


class QuotedEvidenceWireV1(StrictWireModel):
    block: str = Field(pattern=r"^[0-9a-f]{12,64}$")
    quote: str = Field(min_length=1, max_length=2_000)


class BatchCriticCaseWireV2(StrictWireModel):
    target_alias: str
    attack: bool
    case: str = ""
    counterexample: list[Any] | None = None
    premise: str | None = None
    premise_evidence: list[QuotedEvidenceWireV1] | None = Field(
        default=None, max_length=2
    )
    successor_question: str | None = None


class BatchCriticWireV2(StrictWireModel):
    cases: list[BatchCriticCaseWireV2] = Field(default_factory=list, max_length=256)

    @model_validator(mode="after")
    def _one_case_per_target(self):
        targets = tuple(item.target_alias for item in self.cases)
        if len(targets) != len(set(targets)):
            raise ValueError("batch critic cannot return duplicate target cases")
        return self


class BatchCriticWireContractV2(WireContract[BatchCriticOutput]):
    """Call-local batch critic whose targets are exact SRC_### literals."""

    def __init__(
        self,
        aliases: AliasTable,
        expected_targets: tuple[str, ...] | None = None,
        citable_block_ids: tuple[str, ...] = (),
    ) -> None:
        if not aliases.aliases:
            raise AliasTableRequiredError(
                "batch-critic.v2 requires a nonempty call-local target catalog"
            )
        # Diagnostic sourcing ONLY; never read by `model_json_schema`.
        self.citable_block_ids = tuple(
            block for block in citable_block_ids if isinstance(block, str)
        )
        ConjecturerTurnWireContractV6._require_namespace(
            tuple(aliases.aliases), "SRC"
        )
        targets = tuple(
            aliases.aliases.values()
            if expected_targets is None
            else expected_targets
        )
        if not targets:
            raise ValueError("batch-critic.v2 requires at least one assigned target")
        if len(targets) != len(set(targets)):
            raise ValueError("expected batch critic targets must be unique")
        expected_aliases = tuple(sorted(aliases.alias_for(item) for item in targets))
        self.expected_aliases = expected_aliases
        super().__init__(
            BATCH_CRITIC_CONTRACT_V2,
            BatchCriticWireV2,
            BatchCriticOutput,
            aliases=aliases,
            variant="compact.v2",
        )

    def _menu_binding(self, value: Any) -> Any:
        from deepreason.llm.reference_menu import MenuBinding

        return MenuBinding(
            citable_block_ids=self.citable_block_ids,
            aliases=self.expected_aliases,
        )

    def model_json_schema(self) -> dict:
        schema = super().model_json_schema()
        cases = schema.get("properties", {}).get("cases")
        if isinstance(cases, dict):
            cases["maxItems"] = len(self.expected_aliases)
        case = schema.get("$defs", {}).get("BatchCriticCaseWireV2", {})
        target = case.get("properties", {}).get("target_alias")
        if isinstance(target, dict):
            target.clear()
            target.update({"enum": list(self.expected_aliases), "type": "string"})
        return schema

    def _check_targets(self, value: Any) -> None:
        if not isinstance(value, dict) or not isinstance(value.get("cases"), list):
            return
        if len(value["cases"]) > len(self.expected_aliases):
            raise V6WireReferenceError(
                "batch critic returned more cases than assigned targets",
                pointer=f"/cases/{len(self.expected_aliases)}",
            )
        seen: set[str] = set()
        for index, case in enumerate(value["cases"]):
            if not isinstance(case, dict):
                continue
            alias = case.get("target_alias")
            if isinstance(alias, str) and alias in seen:
                raise V6WireReferenceError(
                    f"batch critic duplicated target {alias!r}",
                    pointer=f"/cases/{index}/target_alias",
                    legal_handles=self.expected_aliases,
                )
            if isinstance(alias, str):
                seen.add(alias)
            if isinstance(alias, str) and alias not in self.expected_aliases:
                raise V6WireReferenceError(
                    f"batch critic target {alias!r} was not assigned",
                    pointer=f"/cases/{index}/target_alias",
                    legal_handles=self.expected_aliases,
                )

    def _preflight_value(self, value: Any) -> None:
        self._check_targets(value)
        super()._preflight_value(value)

    def compile(self, wire: BatchCriticWireV2) -> BatchCriticOutput:
        self._check_targets(wire.model_dump(mode="python"))
        return BatchCriticOutput(
            cases=[
                BatchCase(
                    target=self.aliases.resolve(item.target_alias),
                    attack=item.attack,
                    case=item.case,
                    counterexample=item.counterexample,
                    premise=item.premise,
                    premise_evidence=[
                        QuotedEvidenceRefV1(block=ref.block, quote=ref.quote)
                        for ref in (item.premise_evidence or ())
                    ]
                    or None,
                    successor_question=item.successor_question,
                )
                for item in wire.cases
            ]
        )

class CompactCritic(StrictWireModel):
    attack: bool
    target_alias: str
    claim: str = ""
    grounds: str = ""
    cited_input_aliases: list[str] = Field(default_factory=list)
    counterexample: list[Any] | None = None
    premise: str | None = None
    premise_evidence: list[QuotedEvidenceWireV1] | None = Field(
        default=None, max_length=2
    )
    successor_question: str | None = None


class CriticWireContract(WireContract[ArgumentativeCriticOutput]):
    ALIAS_ARRAY_FIELDS = ("cited_input_aliases",)

    def __init__(self, aliases: AliasTable, expected_target: str) -> None:
        # Bind the target in the model-visible schema as well as checking it
        # during compilation.  A critic may cite any exposed input alias, but
        # it may attack only the exact target selected by the deterministic
        # caller.  Keeping this call-local constraint in the wire layer avoids
        # adding target/profile fields to the canonical critic output.
        expected_alias = aliases.alias_for(expected_target)
        bound_model = create_model(
            "BoundCompactCritic",
            __base__=CompactCritic,
            target_alias=(Literal[expected_alias], ...),
        )
        self.expected_target = expected_target
        self.expected_alias = expected_alias
        super().__init__(
            "argumentative_critic.compact.v1",
            bound_model,
            ArgumentativeCriticOutput,
            aliases=aliases,
            variant="compact",
        )

    def compile(self, wire: CompactCritic) -> ArgumentativeCriticOutput:
        resolved_target = self.aliases.resolve(wire.target_alias)
        if resolved_target != self.expected_target:
            # Defence in depth for callers that compile an already-constructed
            # wire value without first running this contract's bound validator.
            raise UnknownAliasError(
                f"target alias {wire.target_alias!r} does not name the attacked "
                f"target {self.expected_alias!r}"
            )
        cited = [self.aliases.resolve(a) for a in wire.cited_input_aliases]
        parts = [part.strip() for part in (wire.claim, wire.grounds) if part.strip()]
        if cited:
            parts.append("cites: " + ", ".join(cited))
        return ArgumentativeCriticOutput(
            attack=wire.attack,
            case="\n".join(parts),
            counterexample=wire.counterexample,
            premise=wire.premise,
            premise_evidence=[
                QuotedEvidenceRefV1(block=ref.block, quote=ref.quote)
                for ref in (wire.premise_evidence or ())
            ]
            or None,
            successor_question=wire.successor_question,
        )


class AtomicCriticWireContractV1(CriticWireContract):
    """One exact deterministic target under separately frozen authority."""

    def __init__(self, aliases: AliasTable, expected_target: str) -> None:
        super().__init__(aliases, expected_target)
        self.contract_id = ATOMIC_CRITIC_CONTRACT_V1
        self.variant = "atomic.v1"


class ResponseClause(StrictWireModel):
    item_alias: str
    response: str = Field(min_length=1)


class CompactDefender(StrictWireModel):
    clauses: list[ResponseClause] = Field(min_length=1)


class DefenderWireContract(WireContract[DefenderOutput]):
    ALIAS_SCALAR_FIELDS = ("item_alias",)

    def __init__(self, aliases: AliasTable) -> None:
        super().__init__(
            "defender.compact.v1",
            CompactDefender,
            DefenderOutput,
            aliases=aliases,
            variant="compact",
        )

    def compile(self, wire: CompactDefender) -> DefenderOutput:
        lines = []
        for clause in wire.clauses:
            resolved = self.aliases.resolve(clause.item_alias)
            lines.append(f"{resolved}: {clause.response}")
        return DefenderOutput(answer="\n".join(lines))


class CompactJudge(StrictWireModel):
    decision: Literal["fail", "pass"]
    decisive_point_alias: str
    grounds: str = ""


class JudgeWireContract(WireContract[JudgeRuling]):
    ALIAS_SCALAR_FIELDS = ("decisive_point_alias",)

    def __init__(self, aliases: AliasTable) -> None:
        super().__init__(
            "judge.compact.v1",
            CompactJudge,
            JudgeRuling,
            aliases=aliases,
            variant="compact",
        )

    def compile(self, wire: CompactJudge) -> JudgeRuling:
        # The alias resolves to an exact exchange span, preserving the existing
        # referential-integrity check rather than replacing it with free prose.
        return JudgeRuling(
            verdict=wire.decision,
            decisive_point=self.aliases.resolve(wire.decisive_point_alias),
        )


class CompactPairwiseJudge(StrictWireModel):
    # "neither" is the only verdict that needs no located point, so the rule
    # is one clause over its complement — both named winners.
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        json_schema_extra=discriminated_shape_schema(
            ShapeClause(
                when=FieldIn("winner", ("A", "B")),
                requires=("decisive_point_alias",),
            )
        ),
    )

    winner: Literal["A", "B", "neither"]
    decisive_point_alias: str = ""

    @model_validator(mode="after")
    def _winner_has_a_located_point(self):
        if self.winner != "neither" and not self.decisive_point_alias:
            raise ValueError("a named winner requires decisive_point_alias")
        return self


class PairwiseJudgeWireContract(WireContract[PairwiseRuling]):
    ALIAS_SCALAR_FIELDS = ("decisive_point_alias",)

    def __init__(self, aliases: AliasTable) -> None:
        super().__init__(
            "judge_pairwise.compact.v1",
            CompactPairwiseJudge,
            PairwiseRuling,
            aliases=aliases,
            variant="compact",
        )

    def compile(self, wire: CompactPairwiseJudge) -> PairwiseRuling:
        decisive = (
            self.aliases.resolve(wire.decisive_point_alias)
            if wire.decisive_point_alias
            else ""
        )
        return PairwiseRuling(winner=wire.winner, decisive_point=decisive)


class CompactEdit(StrictWireModel):
    content: str = Field(min_length=1)
    changed_fields: list[str] = Field(min_length=1)


class CompactVariator(StrictWireModel):
    edits: list[CompactEdit] = Field(min_length=1)


class VariatorWireContract(WireContract[VariatorOutput]):
    def __init__(self) -> None:
        super().__init__(
            "variator.compact.v1",
            CompactVariator,
            VariatorOutput,
            variant="compact",
        )

    def compile(self, wire: CompactVariator) -> VariatorOutput:
        return VariatorOutput(edits=[VariatorEdit(content=edit.content) for edit in wire.edits])


class CompactSynthesizer(StrictWireModel):
    relation: str = Field(min_length=1)
    depends_on: list[str] = Field(min_length=1)


class SynthesizerWireContract(WireContract[SynthesizerOutput]):
    ALIAS_ARRAY_FIELDS = ("depends_on",)

    def __init__(self, aliases: AliasTable) -> None:
        super().__init__(
            "synthesizer.compact.v1",
            CompactSynthesizer,
            SynthesizerOutput,
            aliases=aliases,
            variant="compact",
        )

    def compile(self, wire: CompactSynthesizer) -> SynthesizerOutput:
        return SynthesizerOutput(
            relation=wire.relation,
            connects=[self.aliases.resolve(a) for a in wire.depends_on],
        )


def wire_contract_for(
    role: str,
    output_model: type[CanonicalOutput],
    profile: str | ModelProfile = ModelProfile.STANDARD,
    aliases: AliasTable | None = None,
    *,
    expected_target: str | None = None,
) -> WireContract[CanonicalOutput]:
    """Return a role transport while keeping the canonical output unchanged."""
    spec = get_profile(profile)
    if (
        not spec.direct_contracts
        and role == "conjecturer"
        and output_model is ReasoningConjecturerOutput
    ):
        if aliases is None:
            raise AliasTableRequiredError(
                "compact reasoning calls require an explicit call-local AliasTable"
            )
        return ReasoningConjecturerWireContract(aliases)
    if spec.direct_contracts:
        return DirectWireContract(output_model)
    # Alias-dependent roles remain on their canonical direct transport until
    # the caller supplies a complete call-local table. An empty table must
    # never create a compact contract that can only fail compilation.
    if role == "variator" and output_model is VariatorOutput:
        return VariatorWireContract()
    if role == "conjecturer" and output_model is ConjecturerOutput:
        if aliases is None:
            raise AliasTableRequiredError(
                "compact conjecturer calls require an explicit call-local AliasTable"
            )
        # An explicitly supplied empty table means the pack exposes no local
        # neighbours; unknown aliases still fail deterministically.
        return ConjecturerWireContract(aliases)
    alias_contract = (
        role == "argumentative_critic" and output_model is ArgumentativeCriticOutput
    ) or (role == "defender" and output_model is DefenderOutput) or (
        role == "judge" and output_model in {JudgeRuling, PairwiseRuling}
    ) or (role == "synthesizer" and output_model is SynthesizerOutput)
    if alias_contract and (aliases is None or not aliases.aliases):
        raise AliasTableRequiredError(
            f"compact {role} calls require a nonempty call-local AliasTable"
        )
    table = aliases or AliasTable()
    if role == "argumentative_critic" and output_model is ArgumentativeCriticOutput:
        if expected_target is None:
            raise CriticTargetRequiredError(
                "compact argumentative critic calls require the exact attacked target"
            )
        return CriticWireContract(table, expected_target)
    if role == "defender" and output_model is DefenderOutput:
        return DefenderWireContract(table)
    if role == "judge" and output_model is JudgeRuling:
        return JudgeWireContract(table)
    if role == "judge" and output_model is PairwiseRuling:
        return PairwiseJudgeWireContract(table)
    if role == "synthesizer" and output_model is SynthesizerOutput:
        return SynthesizerWireContract(table)
    # Auxiliary and not-yet-microtasked contracts retain the measured direct
    # fast path. They still receive strict extra/control-field validation.
    return DirectWireContract(output_model)


def minimal_example(contract: WireContract) -> str:
    """Exactly one syntax-only example suitable for compact prompts.

    ``minimal_skeleton`` reads ``properties``/``required`` and ignores
    ``allOf``, so on any contract carrying a cross-field rule it will happily
    build a document the contract rejects — it takes the first enum value and
    stops. A contract whose rules it cannot see supplies its own example via
    ``minimal_example_document``; the turn contracts are the older, hardcoded
    form of the same exemption.
    """

    from deepreason.llm.repair import minimal_skeleton

    if contract.contract_id in {
        "conjecturer.turn.v4",
        "conjecturer.turn.v5",
        CONJECTURER_TURN_CONTRACT_V6,
        CONJECTURER_TURN_CONTRACT_V7,
    }:
        return '{"abstention":{"search_signal":"stuck"}}'
    supplied = getattr(contract, "minimal_example_document", None)
    document = (
        supplied() if callable(supplied) else minimal_skeleton(contract.model_json_schema())
    )
    return json.dumps(document, separators=(",", ":"))
