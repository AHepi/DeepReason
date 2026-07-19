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

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
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
BATCH_CRITIC_CONTRACT_V2 = "batch-critic.v2"
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
    ) -> None:
        self.contract_id = contract_id
        self.wire_model = wire_model
        self.canonical_model = canonical_model
        self.aliases = aliases or AliasTable()
        self.variant = variant

    def model_json_schema(self) -> dict:
        return _strict_schema(self.wire_model.model_json_schema())

    def _preflight_value(self, value: Any) -> None:
        """Apply transport firewalls before contract-specific validation."""

        _reject_control_fields(value)
        schema = self.model_json_schema()
        _reject_unknown_fields(value, schema, schema)

    def validate_value(self, value: Any) -> BaseModel:
        self._preflight_value(value)
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

    def compile(self, wire: RepairPatchV1) -> RepairPatchV1:
        # The generic identity compiler dumps defaults before revalidation.
        # That would turn an omitted remove-patch value into value null
        # and falsely reject the already validated frozen patch.
        return wire


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


class ContextRequestWireV1(StrictWireModel):
    """Only call-local aliases and bounded semantic search material."""

    query: str | None = Field(default=None, min_length=1, max_length=8_192)
    requested_visible_aliases: list[str] = Field(default_factory=list, max_length=64)
    desired_retrieval_channels: list[str] = Field(
        default_factory=list, max_length=16
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

    query: str | None = Field(default=None, min_length=1, max_length=8_192)
    requested_visible_aliases: list[str] = Field(default_factory=list, max_length=64)
    desired_retrieval_channels: list[str] = Field(
        default_factory=list, max_length=16
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

class ConjecturerTurnWireV4(StrictWireModel):
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


class SimulationParameterSetWireV1(StrictWireModel):
    name: str = Field(min_length=1, max_length=128)
    # Canonical JSON text keeps arbitrary finite numerical arrays inside one
    # bounded semantic field without turning object keys into a shadow schema.
    values_json: str = Field(min_length=2, max_length=262_144)


class SimulationProposalWireV1(StrictWireModel):
    request_identifier: str = Field(min_length=1, max_length=128)
    hypothesis: str = Field(min_length=1, max_length=16_384)
    rival_predictions: list[str] = Field(min_length=1, max_length=32)
    discriminating_purpose: str = Field(min_length=1, max_length=8_192)
    declared_assumptions: list[str] = Field(default_factory=list, max_length=64)
    input_aliases: list[str] = Field(default_factory=list, max_length=64)
    parameter_definitions: list[SimulationParameterSetWireV1] = Field(
        default_factory=list, max_length=256
    )
    requested_seed_set: list[int] = Field(default_factory=list, max_length=256)
    simulation_mode: Literal[
        "declarative_numeric_v1", "sandboxed_python_v1"
    ]
    model_source: str = Field(min_length=1, max_length=262_144)
    requested_observables: list[str] = Field(min_length=1, max_length=128)
    interpretation_conditions: list[str] = Field(min_length=1, max_length=64)


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
    context_request: ContextRequestWireV2 | None = None
    scratch_proposal: ScratchProposalV1 | None = None

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
        ):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and (
            self.candidates or self.simulation_proposals or self.scratch_proposal
        ):
            raise ValueError("abstention cannot accompany semantic proposals")
        return self


class ReasoningConjecturerTurnWireV6(ReasoningConjecturerTurnWireV5):
    context_request: ContextRequestWireV2 | None = None
    scratch_proposal: ScratchProposalV1 | None = None

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
        ):
            raise ValueError("a conjecture turn requires at least one meaningful outcome")
        if self.abstention is not None and (
            self.candidates or self.simulation_proposals or self.scratch_proposal
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
    ) -> None:
        self.maximum_simulation_proposals = maximum_simulation_proposals
        ConjecturerTurnWireContractV4.__init__(
            self,
            reasoning=reasoning,
            aliases=aliases,
            scratch_aliases=scratch_aliases,
            permitted_retrieval_channels=permitted_retrieval_channels,
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
        )
        self.contract_id = CONJECTURER_TURN_CONTRACT_V6
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

    @staticmethod
    def _omit_property(node: dict[str, Any], name: str) -> None:
        node.get("properties", {}).pop(name, None)
        required = node.get("required")
        if isinstance(required, list) and name in required:
            required.remove(name)

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

    def validate_value(self, value: Any) -> BaseModel:
        # The strict proposal records intentionally use immutable tuples.
        # Validate through Pydantic's JSON boundary so JSON arrays are accepted
        # as tuples without enabling Python-side scalar coercion.
        self._preflight_value(value)
        raw = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return self.wire_model.model_validate_json(raw)

    def compile(self, wire: BaseModel) -> BaseModel:
        # Defence in depth for callers compiling a constructed wire model
        # without first invoking validate_value/validate_json.
        self._preflight_v6_references(
            wire.model_dump(mode="python", exclude_unset=True)
        )
        scratch = getattr(wire, "scratch_proposal", None)
        if not (
            wire.candidates
            or wire.context_request
            or wire.abstention
            or wire.simulation_proposals
        ) and scratch is not None:
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
        model = ReasoningConjecturerTurnV6 if self.reasoning else ConjectureTurnV6
        return model.model_validate(values)


class BatchCriticCaseWireV2(StrictWireModel):
    target_alias: str
    attack: bool
    case: str = ""
    counterexample: list[Any] | None = None


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
    ) -> None:
        if not aliases.aliases:
            raise AliasTableRequiredError(
                "batch-critic.v2 requires a nonempty call-local target catalog"
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

    if contract.contract_id in {
        "conjecturer.turn.v4",
        "conjecturer.turn.v5",
        CONJECTURER_TURN_CONTRACT_V6,
    }:
        return '{"abstention":{"search_signal":"stuck"}}'
    return json.dumps(minimal_skeleton(contract.model_json_schema()), separators=(",", ":"))
