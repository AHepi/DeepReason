"""Event schema (spec §1) — the source of truth, append-only JSONL.

Graph state is a materialized view; recompute from the log at any ``seq``
for time-travel. Embedder calls are logged exactly like any other role
(prompt/input ref + raw output ref) so every §11.3 diagnostic is
replay-deterministic.
"""

from enum import Enum
from typing import Literal, Mapping

from pydantic import ConfigDict, Field, field_validator, model_validator

from deepreason.bridge.events import BridgeEventPayloadV1
from deepreason.ontology.frozen import FrozenDict, FrozenList, FrozenRecord
from deepreason.scratch.events import ScratchEventPayloadV1


class Rule(str, Enum):
    CONJ = "Conj"
    CRIT = "Crit"
    ADJ = "Adj"
    SPAWN = "Spawn"
    REFL = "Refl"
    REGISTER = "Register"
    MERGE = "Merge"
    MEASURE = "Measure"
    REVEAL = "Reveal"
    RESEED = "Reseed"
    SCRATCH = "Scratch"
    BRIDGE = "Bridge"


class LLMAttempt(FrozenRecord):
    """Process-only trace for one provider completion attempt.

    Every rejected wire value and repair diagnostic remains reachable from
    the append-only event record.  These fields are accounting/replay data;
    they never participate in graph state, warrants, guards, or status.
    """

    prompt_ref: str
    raw_ref: str = ""
    diagnostic_ref: str = ""
    # Zero-based provider completion index: 0 is the initial generation,
    # 1 the whole-object correction, and 2 the smallest-subtree correction.
    # Defaults keep historical events replayable.
    attempt: int = 0
    # JSON Pointer reported by validation for this failed attempt, or the
    # pointer being repaired by a successful retry. Process-only metadata.
    validation_path: str = ""
    contract_id: str = ""
    endpoint_id: str = ""
    route_sha256: str = ""
    seat: int = 0
    model_profile: str = ""
    # Effective model-facing transport for this call. It may become compact
    # on a later scheduler cycle after direct-contract exhaustion, while
    # model_profile remains the frozen RunManifest identity.
    transport_profile: str = ""
    repair_scope: str = ""
    # Exact effective process-health limits immediately before this provider
    # request. They may differ from the compiled route after a logged,
    # bounded controller update. Optional defaults keep historical logs
    # replayable without pretending their unrecorded values are known.
    max_tokens: int | None = Field(default=None, gt=0)
    timeout_s: int | None = Field(default=None, gt=0)
    tokens: int = 0
    # A request can reach a provider and then fail before a usage block is
    # returned.  Recording that distinction prevents a zero-token estimate
    # from being mistaken for proof that no provider work occurred.
    usage_unknown: bool = False
    ms: int = 0
    valid: bool = False
    output_mechanism: str = "json_text"
    transport_attempts: int = 1
    transport_diagnostics: list[str] = Field(default_factory=FrozenList)

    @field_validator("transport_diagnostics", mode="after")
    @classmethod
    def _freeze_diagnostics(cls, value):
        return FrozenList(value)


class SchoolRouteReceiptV1(FrozenRecord):
    """Exact v4 school assignment used for one conjecturer model call."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True
    )

    schema_: Literal["school-route-receipt.v1"] = Field(
        "school-route-receipt.v1", alias="schema"
    )
    school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    role: str = Field(min_length=1)
    seat: int = Field(ge=0)
    endpoint_id: str = Field(min_length=1)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    contract_id: str = Field(min_length=1)


class LLMCall(FrozenRecord):
    role: str
    model: str
    endpoint: str
    prompt_ref: str  # blob
    raw_ref: str  # blob — replay consumes logged raws (§0)
    tokens: int = 0
    ms: int = 0
    attempts: int = 1  # completions consumed incl. schema repairs (P6 valid-JSON rate)
    # A pure PROCESS signal (not outcome): did any attempt in this call hit the
    # completion length limit? Read by the self-calibration controller
    # (controller.py) to widen caps; default False keeps old events replayable.
    truncated: bool = False
    # Mean token surprisal (-mean logprob) of the final completion, when the
    # endpoint returns logprobs. A token-level uncertainty signal that stays
    # informative even when response-level diversity collapses — the
    # decoupling reported in docs/research (alignment tax): detection §11.3.
    mean_surprisal: float | None = None
    # Defaults empty for byte-compatible replay of historical roots. New
    # calls contain exactly one entry per completed/failed schema attempt.
    attempt_trace: list[LLMAttempt] = Field(default_factory=FrozenList)
    # Present only for v4 school-routed conjecture work. ``exclude_if`` keeps
    # every historical event shape byte-compatible.
    school_route: SchoolRouteReceiptV1 | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    @field_validator("attempt_trace", mode="after")
    @classmethod
    def _freeze_attempt_trace(cls, value):
        return FrozenList(value)

    @model_validator(mode="after")
    def _school_route_matches_attempts(self):
        receipt = self.school_route
        if receipt is None:
            return self
        if receipt.role != self.role:
            raise ValueError("school route role must match LLMCall.role")
        if not self.attempt_trace:
            raise ValueError("school route receipt requires an attempt trace")
        for attempt in self.attempt_trace:
            if (
                attempt.seat != receipt.seat
                or attempt.endpoint_id != receipt.endpoint_id
                or attempt.route_sha256 != receipt.route_sha256
                or attempt.contract_id != receipt.contract_id
            ):
                raise ValueError("school route receipt must match every LLM attempt")
        return self


class StateDiff(FrozenRecord):
    att_add: list[tuple[str, str]] = Field(default_factory=FrozenList, alias="att+")
    dep_add: list[tuple[str, str]] = Field(default_factory=FrozenList, alias="dep+")
    a_add: list[str] = Field(default_factory=FrozenList, alias="A+")
    pi_add: list[str] = Field(default_factory=FrozenList, alias="Π+")
    status_changed: list[str] = Field(default_factory=FrozenList)
    # Measure-rule payloads (§6): estimates recorded in the event so replay
    # applies them without re-running the variator (raws are logged too).
    hv_set: Mapping[str, float] = Field(default_factory=FrozenDict)
    reach_set: Mapping[str, float] = Field(default_factory=FrozenDict)
    # Normative amendment (reach, Def 3.7): a FULL reach hit - genuine
    # cross-problem survival of another problem's non-trivial battery -
    # registers the artifact as ADDRESSING that problem. Carried in the
    # event so replay applies it without re-running the sweep.
    addr_add: list[tuple[str, str]] = Field(default_factory=FrozenList, alias="addr+")
    # Append-only warrant carriage. Kept out of Artifact.compute_id so an
    # artifact remains the same content object when it packages more than one
    # attack; old events remain compatible through the default empty list.
    carry_add: list[tuple[str, str]] = Field(default_factory=FrozenList, alias="carry+")

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    @field_validator("hv_set", "reach_set", mode="after")
    @classmethod
    def _freeze_maps(cls, value):
        return FrozenDict(value)

    @field_validator(
        "att_add", "dep_add", "a_add", "pi_add", "status_changed", "addr_add",
        "carry_add", mode="after",
    )
    @classmethod
    def _freeze_sequences(cls, value):
        return FrozenList(value)


class Event(FrozenRecord):
    seq: int
    ts: str  # iso8601
    rule: Rule
    inputs: list[str] = Field(default_factory=FrozenList)
    outputs: list[str] = Field(default_factory=FrozenList)
    llm: LLMCall | None = None
    state_diff: StateDiff = Field(default_factory=StateDiff)
    # ``exclude_if`` preserves the exact legacy JSON shape for formal events.
    scratch: ScratchEventPayloadV1 | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    bridge: BridgeEventPayloadV1 | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    @field_validator("inputs", "outputs", mode="after")
    @classmethod
    def _freeze_sequences(cls, value):
        return FrozenList(value)

    @model_validator(mode="after")
    def _process_payload_contract(self):
        if (self.rule == Rule.SCRATCH) != (self.scratch is not None):
            raise ValueError("Scratch rule and typed scratch payload must appear together")
        if (self.rule == Rule.BRIDGE) != (self.bridge is not None):
            raise ValueError("Bridge rule and typed bridge payload must appear together")
        if self.scratch is not None:
            if list(self.inputs) != list(self.scratch.inputs):
                raise ValueError("scratch payload inputs must match Event.inputs")
            if list(self.outputs) != list(self.scratch.outputs):
                raise ValueError("scratch payload outputs must match Event.outputs")
        if self.bridge is not None:
            if list(self.inputs) != list(self.bridge.inputs):
                raise ValueError("bridge payload inputs must match Event.inputs")
            if list(self.outputs) != list(self.bridge.outputs):
                raise ValueError("bridge payload outputs must match Event.outputs")
        if self.scratch is not None or self.bridge is not None:
            formal = self.state_diff.model_dump(mode="json", by_alias=True)
            if any(formal.values()):
                raise ValueError("scratch and bridge events cannot mutate formal StateDiff")
        return self
