"""Replay-derived state for grounded bridge process events.

Bridge records are advisory final-view material.  They are materialized beside
``EpistemicState`` and never contribute artifacts, warrants, graph edges,
status, commitments, or adjudication inputs.  The only inputs to this state
are immutable objects and typed append-only events.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field

from pydantic import BaseModel

from deepreason.bridge.events import BridgeAction, BridgeEventPayloadV1
from deepreason.ontology.event import Event
from deepreason.storage.objects import ObjectStore


_LEDGER_SCHEMAS = frozenset(
    {
        "bridge-evidence-pack",
        "bridge-ledger-input-catalog",
        "bridge-ledger-entry",
        "bridge-uncovered-requirement",
        "bridge-source-conflict",
        "bridge-claim-ledger",
    }
)
_OUTPUT_SCHEMAS = frozenset(
    {"bridge-claim-use", "bridge-unresolved-item", "bridge-output"}
)
_VALIDATION_SCHEMAS = frozenset(
    {"bridge-validation-finding", "bridge-validation-report"}
)
_REVIEW_SCHEMAS = frozenset(
    {"bridge-grounding-finding", "bridge-grounding-review"}
)

_ALLOWED_OUTPUT_SCHEMAS: dict[BridgeAction, frozenset[str]] = {
    BridgeAction.LEDGER_CREATED: _LEDGER_SCHEMAS,
    BridgeAction.LEDGER_VALIDATED: _VALIDATION_SCHEMAS,
    BridgeAction.LEDGER_AMENDMENT_REQUESTED: frozenset(),
    BridgeAction.LEDGER_AMENDMENT_ATTEMPTED: frozenset(),
    BridgeAction.LEDGER_AMENDED: _LEDGER_SCHEMAS,
    BridgeAction.OUTPUT_COMPOSED: _OUTPUT_SCHEMAS,
    BridgeAction.OUTPUT_VALIDATED: _VALIDATION_SCHEMAS,
    BridgeAction.GROUNDED_REVIEW_ATTEMPTED: frozenset(),
    BridgeAction.GROUNDED_REVIEWED: _REVIEW_SCHEMAS,
    BridgeAction.REPAIR_ATTEMPTED: _OUTPUT_SCHEMAS,
    BridgeAction.COMPLETED: frozenset(),
    BridgeAction.FAILED: frozenset(),
}

_PRIMARY_SCHEMA: dict[BridgeAction, str | None] = {
    BridgeAction.LEDGER_CREATED: "bridge-claim-ledger",
    BridgeAction.LEDGER_VALIDATED: "bridge-validation-report",
    BridgeAction.LEDGER_AMENDMENT_REQUESTED: None,
    BridgeAction.LEDGER_AMENDMENT_ATTEMPTED: None,
    BridgeAction.LEDGER_AMENDED: "bridge-claim-ledger",
    BridgeAction.OUTPUT_COMPOSED: "bridge-output",
    BridgeAction.OUTPUT_VALIDATED: "bridge-validation-report",
    BridgeAction.GROUNDED_REVIEW_ATTEMPTED: None,
    BridgeAction.GROUNDED_REVIEWED: "bridge-grounding-review",
    BridgeAction.REPAIR_ATTEMPTED: "bridge-output",
    BridgeAction.COMPLETED: None,
    BridgeAction.FAILED: None,
}


def _ids(values) -> set[str]:
    return {value.id for value in values or ()}


@dataclass
class BridgeState:
    """A deterministic, non-authoritative materialized bridge index."""

    evidence_packs: dict[str, BaseModel] = field(default_factory=dict)
    catalogs: dict[str, BaseModel] = field(default_factory=dict)
    ledger_entries: dict[str, BaseModel] = field(default_factory=dict)
    uncovered_requirements: dict[str, BaseModel] = field(default_factory=dict)
    source_conflicts: dict[str, BaseModel] = field(default_factory=dict)
    ledgers: dict[str, BaseModel] = field(default_factory=dict)
    claim_uses: dict[str, BaseModel] = field(default_factory=dict)
    unresolved_items: dict[str, BaseModel] = field(default_factory=dict)
    outputs: dict[str, BaseModel] = field(default_factory=dict)
    validation_findings: dict[str, BaseModel] = field(default_factory=dict)
    validation_reports: dict[str, BaseModel] = field(default_factory=dict)
    grounding_findings: dict[str, BaseModel] = field(default_factory=dict)
    grounding_reviews: dict[str, BaseModel] = field(default_factory=dict)
    object_schemas: dict[str, str] = field(default_factory=dict)
    object_event_seq: dict[str, int] = field(default_factory=dict)
    event_seqs: list[int] = field(default_factory=list)
    events_by_action: dict[BridgeAction, list[int]] = field(default_factory=dict)
    outputs_by_event: dict[int, list[str]] = field(default_factory=dict)
    completed_events: list[int] = field(default_factory=list)
    failed_events: list[int] = field(default_factory=list)
    error_codes_by_event: dict[int, str] = field(default_factory=dict)

    @staticmethod
    def _one(
        records: list[tuple[str, str, BaseModel]], schema: str
    ) -> tuple[str, BaseModel]:
        matches = [(oid, obj) for found, oid, obj in records if found == schema]
        if len(matches) != 1:
            raise ValueError(f"bridge event requires exactly one {schema} output")
        return matches[0]

    def _known_schema(
        self,
        oid: str,
        records: list[tuple[str, str, BaseModel]],
    ) -> str | None:
        for schema, candidate, _obj in records:
            if candidate == oid:
                return schema
        return self.object_schemas.get(oid)

    def _validate_finding_ref(
        self,
        payload: BridgeEventPayloadV1,
        records: list[tuple[str, str, BaseModel]],
    ) -> None:
        if payload.finding_ref is None:
            return
        schema = self._known_schema(payload.finding_ref, records)
        if schema not in {
            "bridge-validation-finding",
            "bridge-validation-report",
            "bridge-grounding-finding",
            "bridge-grounding-review",
        }:
            raise ValueError("bridge finding_ref must name a persisted bridge finding or report")

    @staticmethod
    def _validate_auxiliary_membership(
        records: list[tuple[str, str, BaseModel]],
        members: dict[str, set[str]],
    ) -> None:
        for schema, oid, _obj in records:
            allowed = members.get(schema)
            if allowed is not None and oid not in allowed:
                raise ValueError(
                    f"bridge auxiliary output {oid} is not contained in its primary record"
                )

    def validate(
        self,
        payload: BridgeEventPayloadV1,
        records: list[tuple[str, str, BaseModel]],
    ) -> None:
        """Validate one action without mutating this materialized view."""

        action = payload.action
        if action == BridgeAction.FAILED:
            if payload.error_code is None:
                raise ValueError("failed bridge event requires error_code")
        elif payload.error_code is not None:
            raise ValueError("error_code is only valid for a failed bridge event")

        record_ids = [oid for _schema, oid, _obj in records]
        if record_ids != list(payload.outputs):
            raise ValueError("resolved bridge records must exactly match payload outputs")
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("bridge event outputs must not contain duplicate object IDs")
        if len(payload.inputs) != len(set(payload.inputs)):
            raise ValueError("bridge event inputs must not contain duplicate object IDs")

        actual = Counter(schema for schema, _oid, _obj in records)
        non_bridge = {schema for schema in actual if not schema.startswith("bridge-")}
        if non_bridge:
            raise ValueError(
                f"bridge event output uses non-bridge schema {sorted(non_bridge)[0]!r}"
            )
        disallowed = set(actual) - _ALLOWED_OUTPUT_SCHEMAS[action]
        if disallowed:
            raise ValueError(
                f"bridge action {action.value} has disallowed output schema "
                f"{sorted(disallowed)[0]}"
            )
        primary_schema = _PRIMARY_SCHEMA[action]
        primary_count = 0 if primary_schema is None else actual[primary_schema]
        if action == BridgeAction.REPAIR_ATTEMPTED:
            if primary_count > 1:
                raise ValueError("repair_attempted permits at most one bridge-output")
        elif primary_schema is not None and primary_count != 1:
            raise ValueError(
                f"bridge action {action.value} requires exactly one {primary_schema}"
            )
        elif primary_schema is None and records:
            raise ValueError(f"bridge action {action.value} cannot create objects")

        self._validate_finding_ref(payload, records)
        input_ids = set(payload.inputs)

        if action in {BridgeAction.LEDGER_CREATED, BridgeAction.LEDGER_AMENDED}:
            _ledger_id, ledger = self._one(records, "bridge-claim-ledger")
            packs = [
                obj for schema, _oid, obj in records if schema == "bridge-evidence-pack"
            ]
            if len(packs) > 1 or (packs and action != BridgeAction.LEDGER_CREATED):
                raise ValueError("only ledger_created permits one evidence pack")
            catalogs = [obj for schema, _oid, obj in records if schema == "bridge-ledger-input-catalog"]
            if len(catalogs) > 1:
                raise ValueError("a ledger event permits at most one input catalog")
            if action == BridgeAction.LEDGER_AMENDED:
                prior_ids = input_ids & self.ledgers.keys()
                if len(prior_ids) != 1:
                    raise ValueError("ledger_amended requires exactly one prior ledger input")
                prior = self.ledgers[next(iter(prior_ids))]
                if ledger.id == prior.id:
                    raise ValueError("ledger_amended must create a new immutable ledger")
                for field_name in (
                    "problem_ref",
                    "formal_seq",
                    "output_target",
                    "advisory_context_ref",
                    "retrieval_receipt_ref",
                ):
                    if getattr(ledger, field_name) != getattr(prior, field_name):
                        raise ValueError(
                            f"ledger amendment cannot change fixed {field_name}"
                        )
            if catalogs:
                catalog = catalogs[0]
                for field_name in (
                    "problem_ref",
                    "formal_seq",
                    "output_target",
                    "advisory_context_ref",
                    "retrieval_receipt_ref",
                ):
                    if getattr(catalog, field_name) != getattr(ledger, field_name):
                        raise ValueError(
                            f"bridge input catalog {field_name} does not match ledger"
                        )
            if packs:
                pack = packs[0]
                if (
                    pack.problem_ref != ledger.problem_ref
                    or pack.formal_seq != ledger.formal_seq
                ):
                    raise ValueError("bridge evidence pack fence does not match ledger")
            self._validate_auxiliary_membership(
                records,
                {
                    "bridge-ledger-entry": _ids(ledger.entries),
                    "bridge-uncovered-requirement": _ids(ledger.uncovered_requirements),
                    "bridge-source-conflict": _ids(ledger.source_conflicts),
                },
            )

        elif action in {BridgeAction.LEDGER_VALIDATED, BridgeAction.OUTPUT_VALIDATED}:
            _report_id, report = self._one(records, "bridge-validation-report")
            if report.claim_ledger_id not in self.ledgers:
                raise ValueError("bridge validation report names an unknown ledger")
            if report.claim_ledger_id not in input_ids:
                raise ValueError("bridge validation event must input its claim ledger")
            if action == BridgeAction.LEDGER_VALIDATED:
                if report.bridge_output_id is not None:
                    raise ValueError("ledger validation report cannot name a bridge output")
            else:
                if report.bridge_output_id not in self.outputs:
                    raise ValueError("output validation report names an unknown bridge output")
                if report.bridge_output_id not in input_ids:
                    raise ValueError("output validation event must input its bridge output")
                output = self.outputs[report.bridge_output_id]
                if output.claim_ledger_id != report.claim_ledger_id:
                    raise ValueError("output validation report ledger does not match output")
            self._validate_auxiliary_membership(
                records,
                {"bridge-validation-finding": _ids(report.findings)},
            )

        elif action in {
            BridgeAction.LEDGER_AMENDMENT_REQUESTED,
            BridgeAction.LEDGER_AMENDMENT_ATTEMPTED,
        }:
            prior_ids = input_ids & self.ledgers.keys()
            if len(prior_ids) != 1:
                raise ValueError(
                    f"{action.value} requires exactly one known ledger input"
                )

        elif action in {BridgeAction.OUTPUT_COMPOSED, BridgeAction.REPAIR_ATTEMPTED}:
            if action == BridgeAction.REPAIR_ATTEMPTED:
                if not (input_ids & self.outputs.keys()):
                    raise ValueError("repair_attempted requires a prior bridge output input")
                reviews = [
                    self.grounding_reviews[review_id]
                    for review_id in input_ids & self.grounding_reviews.keys()
                ]
                if not reviews or all(review.passed for review in reviews):
                    raise ValueError(
                        "repair_attempted requires a failed grounding review input"
                    )
                if primary_count == 0:
                    if records:
                        raise ValueError(
                            "repair_attempted cannot store auxiliary records without an output"
                        )
                    return
            _output_id, output = self._one(records, "bridge-output")
            if output.claim_ledger_id not in self.ledgers:
                raise ValueError("bridge output names an unknown ledger")
            if output.claim_ledger_id not in input_ids:
                raise ValueError("bridge output event must input its claim ledger")
            valid_ledger_reports = [
                report
                for report in self.validation_reports.values()
                if report.claim_ledger_id == output.claim_ledger_id
                and report.bridge_output_id is None
                and report.valid
            ]
            if not valid_ledger_reports:
                raise ValueError("bridge output requires a valid claim-ledger report")
            if action == BridgeAction.REPAIR_ATTEMPTED:
                failed_reviews = [review for review in reviews if not review.passed]
                if not any(
                    review.bridge_output_id in input_ids
                    and review.claim_ledger_id == output.claim_ledger_id
                    for review in failed_reviews
                ):
                    raise ValueError(
                        "repair output must retain the failed review's claim ledger"
                    )
            self._validate_auxiliary_membership(
                records,
                {
                    "bridge-claim-use": _ids(output.sections),
                    "bridge-unresolved-item": _ids(output.unresolved_items),
                },
            )

        elif action == BridgeAction.GROUNDED_REVIEWED:
            _review_id, review = self._one(records, "bridge-grounding-review")
            if review.claim_ledger_id not in self.ledgers:
                raise ValueError("grounding review names an unknown ledger")
            if review.bridge_output_id not in self.outputs:
                raise ValueError("grounding review names an unknown bridge output")
            output = self.outputs[review.bridge_output_id]
            if output.claim_ledger_id != review.claim_ledger_id:
                raise ValueError("grounding review ledger does not match bridge output")
            required = {review.claim_ledger_id, review.bridge_output_id}
            if not required.issubset(input_ids):
                raise ValueError("grounding review must input its ledger and bridge output")
            valid_output_reports = [
                report
                for report in self.validation_reports.values()
                if report.bridge_output_id == review.bridge_output_id and report.valid
            ]
            if not valid_output_reports:
                raise ValueError("grounding review requires a valid bridge-output report")
            self._validate_auxiliary_membership(
                records,
                {"bridge-grounding-finding": _ids(review.findings)},
            )

        elif action == BridgeAction.GROUNDED_REVIEW_ATTEMPTED:
            known_ledgers = input_ids & self.ledgers.keys()
            known_outputs = input_ids & self.outputs.keys()
            if len(known_ledgers) != 1 or len(known_outputs) != 1:
                raise ValueError(
                    "grounded_review_attempted requires one known ledger and output"
                )
            output = self.outputs[next(iter(known_outputs))]
            if output.claim_ledger_id not in known_ledgers:
                raise ValueError("grounded review attempt ledger does not match output")

        elif action == BridgeAction.COMPLETED:
            completed_outputs = input_ids & self.outputs.keys()
            if not completed_outputs:
                raise ValueError("completed bridge event requires a bridge output input")
            for output_id in completed_outputs:
                output = self.outputs[output_id]
                if output.claim_ledger_id not in input_ids:
                    raise ValueError("completed bridge event must input its claim ledger")
                report_ids = [
                    report_id
                    for report_id, report in self.validation_reports.items()
                    if report.bridge_output_id == output_id and report.valid
                ]
                if not report_ids:
                    raise ValueError("completed bridge output requires a valid validation report")
                if not input_ids.intersection(report_ids):
                    raise ValueError(
                        "completed bridge event must input its valid validation report"
                    )

    def _register(self, schema: str, oid: str, obj: BaseModel, event_seq: int) -> None:
        existing = self.object_schemas.get(oid)
        if existing is not None and existing != schema:
            raise ValueError(f"bridge object {oid} changed schema during replay")
        self.object_schemas[oid] = schema
        self.object_event_seq.setdefault(oid, event_seq)
        indexes = {
            "bridge-evidence-pack": self.evidence_packs,
            "bridge-ledger-input-catalog": self.catalogs,
            "bridge-ledger-entry": self.ledger_entries,
            "bridge-uncovered-requirement": self.uncovered_requirements,
            "bridge-source-conflict": self.source_conflicts,
            "bridge-claim-ledger": self.ledgers,
            "bridge-claim-use": self.claim_uses,
            "bridge-unresolved-item": self.unresolved_items,
            "bridge-output": self.outputs,
            "bridge-validation-finding": self.validation_findings,
            "bridge-validation-report": self.validation_reports,
            "bridge-grounding-finding": self.grounding_findings,
            "bridge-grounding-review": self.grounding_reviews,
        }
        indexes[schema][oid] = obj

    def apply(self, event: Event, objects: ObjectStore) -> None:
        payload = event.bridge
        if payload is None:
            return
        records: list[tuple[str, str, BaseModel]] = []
        for oid in event.outputs:
            schema, obj = objects.get(oid)
            if not schema.startswith("bridge-"):
                raise ValueError(
                    f"bridge event output {oid!r} uses non-bridge schema {schema!r}"
                )
            records.append((schema, oid, obj))
        self.validate(payload, records)
        for schema, oid, obj in records:
            self._register(schema, oid, obj, event.seq)
        self.event_seqs.append(event.seq)
        self.events_by_action.setdefault(payload.action, []).append(event.seq)
        self.outputs_by_event[event.seq] = list(event.outputs)
        if payload.action == BridgeAction.COMPLETED:
            self.completed_events.append(event.seq)
        elif payload.action == BridgeAction.FAILED:
            self.failed_events.append(event.seq)
            self.error_codes_by_event[event.seq] = payload.error_code


def rebuild_bridge_state(objects: ObjectStore, events: Iterable[Event]) -> BridgeState:
    state = BridgeState()
    for event in events:
        state.apply(event, objects)
    return state


__all__ = ["BridgeState", "rebuild_bridge_state"]
