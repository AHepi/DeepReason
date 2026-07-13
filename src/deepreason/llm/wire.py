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
from typing import Any, Generic, Literal, Mapping, TypeVar

from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator

from deepreason.llm.contracts import (
    ArgumentativeCriticOutput,
    CandidateRef,
    ConjectureCandidate,
    ConjecturerOutput,
    DefenderOutput,
    JudgeRuling,
    PairwiseRuling,
    SynthesizerOutput,
    VariatorEdit,
    VariatorOutput,
)
from deepreason.llm.profiles import ModelProfile, get_profile
from deepreason.llm.repair import parse_one_json_value
from deepreason.workloads.text import (
    OperationalSidecar,
    ReasoningCandidateProposal,
    ReasoningConjecturerOutput,
)


CanonicalOutput = TypeVar("CanonicalOutput", bound=BaseModel)

FORBIDDEN_CONTROL_FIELDS = frozenset(
    {
        "model",
        "endpoint",
        "provider",
        "tool",
        "command",
        "delegate",
        "guard_policy",
        "acceptance",
        "status",
        "route",
    }
)


class UnknownAliasError(ValueError):
    pass


class AliasTableRequiredError(ValueError):
    """A compact reference-bearing role was invoked without local aliases."""


class CriticTargetRequiredError(ValueError):
    """A compact critic contract was not bound to its actual target."""


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


def _strict_schema(node: Any, root: dict | None = None) -> Any:
    """Mark every model-visible object as closed, including $defs."""
    result = copy.deepcopy(node)
    root = result if root is None else root

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object" or "properties" in value:
                value["additionalProperties"] = False
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(result)
    return result


def _reject_control_fields(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}/{key}"
            if key in FORBIDDEN_CONTROL_FIELDS:
                raise ValueError(
                    f"control field {key!r} is not part of this role contract at {here}"
                )
            # A counterexample is opaque application input; e.g. an app may
            # legitimately accept a data object whose domain key is status.
            if key != "counterexample":
                _reject_control_fields(child, here)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_control_fields(child, f"{path}/{index}")


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
    ) -> None:
        self.contract_id = contract_id
        self.wire_model = wire_model
        self.canonical_model = canonical_model
        self.aliases = aliases or AliasTable()
        self.variant = variant

    def model_json_schema(self) -> dict:
        return _strict_schema(self.wire_model.model_json_schema())

    def validate_value(self, value: Any) -> BaseModel:
        _reject_control_fields(value)
        schema = self.model_json_schema()
        _reject_unknown_fields(value, schema, schema)
        return self.wire_model.model_validate(value)

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


class CompactConjectureCandidate(StrictWireModel):
    content: str = Field(min_length=1)
    typicality: float = Field(ge=0.0, le=1.0)
    neighbours: list[str] = Field(default_factory=list)


class CompactConjecturer(StrictWireModel):
    candidates: list[CompactConjectureCandidate] = Field(min_length=1)


class ConjecturerWireContract(WireContract[ConjecturerOutput]):
    def __init__(self, aliases: AliasTable | None = None) -> None:
        super().__init__(
            "conjecturer.compact.v1",
            CompactConjecturer,
            ConjecturerOutput,
            aliases=aliases,
            variant="compact",
        )

    def compile(self, wire: CompactConjecturer) -> ConjecturerOutput:
        return ConjecturerOutput(
            candidates=[
                ConjectureCandidate(
                    content=item.content,
                    typicality=item.typicality,
                    refs=[CandidateRef(target=self.aliases.resolve(a)) for a in item.neighbours],
                )
                for item in wire.candidates
            ]
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
                    sidecar=OperationalSidecar(
                        search_signal=candidate.sidecar.search_signal,
                        requested_context_aliases=requested,
                    ),
                )
            )
        return ReasoningConjecturerOutput(candidates=tuple(candidates))

class CompactCritic(StrictWireModel):
    attack: bool
    target_alias: str
    claim: str = ""
    grounds: str = ""
    cited_input_aliases: list[str] = Field(default_factory=list)
    counterexample: list[Any] | None = None


class CriticWireContract(WireContract[ArgumentativeCriticOutput]):
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
        )


class ResponseClause(StrictWireModel):
    item_alias: str
    response: str = Field(min_length=1)


class CompactDefender(StrictWireModel):
    clauses: list[ResponseClause] = Field(min_length=1)


class DefenderWireContract(WireContract[DefenderOutput]):
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
    winner: Literal["A", "B", "neither"]
    decisive_point_alias: str = ""

    @model_validator(mode="after")
    def _winner_has_a_located_point(self):
        if self.winner != "neither" and not self.decisive_point_alias:
            raise ValueError("a named winner requires decisive_point_alias")
        return self


class PairwiseJudgeWireContract(WireContract[PairwiseRuling]):
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
    """Exactly one syntax-only example suitable for compact prompts."""
    from deepreason.llm.repair import minimal_skeleton

    return json.dumps(minimal_skeleton(contract.model_json_schema()), separators=(",", ":"))
