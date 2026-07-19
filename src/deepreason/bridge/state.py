"""Replay-derived state for grounded bridge process events.

Bridge records are advisory final-view material.  They are materialized beside
``EpistemicState`` and never contribute artifacts, warrants, graph edges,
status, commitments, or adjudication inputs.  The only inputs to this state
are immutable objects and typed append-only events.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from pydantic import BaseModel

from deepreason.bridge.events import BridgeAction, BridgeEventPayloadV1
from deepreason.control_events import ControlEventPayloadV3
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
_FAILURE_SCHEMAS = frozenset(
    {"bridge-evidence-pack", "bridge-ledger-input-catalog", "bridge-failure"}
)
_RETRY_SCHEMAS = frozenset({"bridge-workflow-retry"})

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
    BridgeAction.FAILED: _FAILURE_SCHEMAS,
    BridgeAction.WORKFLOW_RETRY_STARTED: _RETRY_SCHEMAS,
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
    BridgeAction.WORKFLOW_RETRY_STARTED: "bridge-workflow-retry",
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
    failures: dict[str, BaseModel] = field(default_factory=dict)
    workflow_retries: dict[str, BaseModel] = field(default_factory=dict)
    retry_attempt_ids: dict[str, str] = field(default_factory=dict)
    attempt_number_by_failure: dict[str, int] = field(default_factory=dict)
    retry_id_by_failure: dict[str, str] = field(default_factory=dict)
    cumulative_tokens_by_failure: dict[str, int] = field(default_factory=dict)
    calls_by_failure: dict[str, list[BaseModel]] = field(default_factory=dict)
    object_schemas: dict[str, str] = field(default_factory=dict)
    object_event_seq: dict[str, int] = field(default_factory=dict)
    event_seqs: list[int] = field(default_factory=list)
    events_by_action: dict[BridgeAction, list[int]] = field(default_factory=dict)
    inputs_by_event: dict[int, list[str]] = field(default_factory=dict)
    outputs_by_event: dict[int, list[str]] = field(default_factory=dict)
    completed_events: list[int] = field(default_factory=list)
    failed_events: list[int] = field(default_factory=list)
    error_codes_by_event: dict[int, str] = field(default_factory=dict)
    _pending_retry: BaseModel | None = field(default=None, repr=False)
    _awaiting_retry_attempt_start: bool = field(default=False, repr=False)
    _attempt_tokens: int = field(default=0, repr=False)
    _attempt_calls: list[BaseModel] = field(default_factory=list, repr=False)
    _v6_provider_attempt_ids: set[str] = field(default_factory=set, repr=False)

    def apply_v6_provider_result(self, event: Event, workflow_state) -> None:
        """Account one bridge v6 provider receipt after canonical workflow replay.

        ``WorkflowReplayState`` has already validated the control-event envelope,
        receipt, dispatch authority, and LLM/token correspondence.  This bridge
        index only selects its own v6 work and retains the validated call for
        retry accounting; it never reinterprets transaction authority.
        """

        control = event.control
        if not isinstance(control, ControlEventPayloadV3) or control.action != "provider_result":
            return
        item = workflow_state.transaction_work.get(control.inputs[0])
        if item is None:
            return
        payload = item.preparation.task_payload_value
        if (
            not isinstance(payload, Mapping)
            or payload.get("schema") != "bridge.transaction-task.v2"
        ):
            return
        attempt = item.provider_attempts.get(item.preparation.attempt_index)
        call = event.llm
        if (
            attempt is None
            or attempt.id != control.inputs[1]
            or call is None
            or attempt.outcome != "provider_result"
            or attempt.usage_status != "exact"
        ):
            return
        if attempt.id in self._v6_provider_attempt_ids:
            raise ValueError("bridge v6 provider result was counted twice")
        self._v6_provider_attempt_ids.add(attempt.id)
        self._attempt_tokens += call.tokens
        self._attempt_calls.append(call)

    def _repair_lineage(self, output_id: str, review) -> bool:
        return any(
            output_id in self.outputs_by_event.get(seq, [])
            and review.id in self.inputs_by_event.get(seq, [])
            and review.bridge_output_id in self.inputs_by_event.get(seq, [])
            for seq in self.events_by_action.get(BridgeAction.REPAIR_ATTEMPTED, [])
        )

    @staticmethod
    def _assert_safe_repair(before, after) -> None:
        from deepreason.bridge.repair import assert_safe_repair_diff

        try:
            assert_safe_repair_diff(before, after)
        except RuntimeError as error:
            raise ValueError(str(error)) from error

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
        elif primary_schema is None and records and action != BridgeAction.FAILED:
            raise ValueError(f"bridge action {action.value} cannot create objects")

        self._validate_finding_ref(payload, records)
        input_ids = set(payload.inputs)

        if action == BridgeAction.FAILED and records:
            _failure_id, failure = self._one(records, "bridge-failure")
            packs = [
                obj for schema, _oid, obj in records if schema == "bridge-evidence-pack"
            ]
            catalogs = [
                obj
                for schema, _oid, obj in records
                if schema == "bridge-ledger-input-catalog"
            ]
            if len(packs) > 1 or len(catalogs) > 1:
                raise ValueError("failed bridge event permits at most one pack and catalog")
            if bool(packs) != bool(catalogs):
                raise ValueError("a new failed bridge pack and catalog must be stored together")
            pack = packs[0] if packs else self.evidence_packs.get(failure.evidence_pack_id)
            catalog = catalogs[0] if catalogs else self.catalogs.get(failure.catalog_id)
            if pack is None or pack.id != failure.evidence_pack_id:
                raise ValueError("bridge failure names an unknown evidence pack")
            if catalog is None or catalog.id != failure.catalog_id:
                raise ValueError("bridge failure names an unknown input catalog")
            if (
                pack.problem_ref != failure.problem_ref
                or pack.formal_seq != failure.formal_seq
                or catalog.problem_ref != failure.problem_ref
                or catalog.formal_seq != failure.formal_seq
                or catalog.output_target != failure.output_target
            ):
                raise ValueError("bridge failure metadata differs from its pack or catalog")
            if failure.error_code != payload.error_code:
                raise ValueError("bridge failure error code differs from event payload")
            if list(failure.terminal_inputs) != list(payload.inputs):
                raise ValueError("bridge failure inputs differ from event payload")
            for field_name, schema in (
                ("claim_ledger_id", "bridge-claim-ledger"),
                ("bridge_output_id", "bridge-output"),
                ("validation_report_id", "bridge-validation-report"),
                ("review_id", "bridge-grounding-review"),
            ):
                object_id = getattr(failure, field_name)
                if object_id is not None and self._known_schema(object_id, records) != schema:
                    raise ValueError(
                        f"bridge failure {field_name} does not name a known {schema}"
                    )
            ledger = self.ledgers.get(failure.claim_ledger_id)
            output = self.outputs.get(failure.bridge_output_id)
            report = self.validation_reports.get(failure.validation_report_id)
            review = self.grounding_reviews.get(failure.review_id)
            if ledger is not None and (
                ledger.problem_ref != failure.problem_ref
                or ledger.formal_seq != failure.formal_seq
                or ledger.output_target != failure.output_target
            ):
                raise ValueError("bridge failure ledger differs from terminal metadata")
            if output is not None and (
                ledger is None or output.claim_ledger_id != ledger.id
            ):
                raise ValueError("bridge failure output does not belong to its ledger")
            if report is not None and (
                ledger is None
                or report.claim_ledger_id != ledger.id
                or report.bridge_output_id != (
                    output.id if output is not None else None
                )
            ):
                raise ValueError("bridge failure report does not belong to partial output")
            if review is not None and (
                ledger is None
                or output is None
                or review.claim_ledger_id != ledger.id
            ):
                raise ValueError("bridge failure review does not belong to partial output")
            if review is not None and (
                review.bridge_output_id != output.id
                and not self._repair_lineage(output.id, review)
            ):
                raise ValueError("bridge failure review lacks repaired-output lineage")

        if action == BridgeAction.WORKFLOW_RETRY_STARTED:
            _retry_id, retry = self._one(records, "bridge-workflow-retry")
            if list(payload.inputs) != [retry.prior_failure_id]:
                raise ValueError("workflow retry must name exactly its prior failure")
            failure = self.failures.get(retry.prior_failure_id)
            if failure is None:
                raise ValueError("workflow retry names an unknown prior failure")
            if any(
                prior.prior_failure_id == retry.prior_failure_id
                for prior in self.workflow_retries.values()
            ):
                raise ValueError("prior bridge failure already has a retry attempt")
            if (
                retry.reason_code != failure.error_code
                or retry.attempt_fence.formal_seq != failure.formal_seq
                or retry.attempt_fence.catalog_id != failure.catalog_id
                or retry.attempt_fence.manifest_digest
                != failure.run_manifest_digest
            ):
                raise ValueError("workflow retry differs from its prior failure fence")
            prior_attempt = self.attempt_number_by_failure.get(failure.id, 1)
            if retry.attempt_number != prior_attempt + 1:
                raise ValueError("workflow retry attempt number is not replay-derived")
            prior_retry_id = self.retry_id_by_failure.get(failure.id)
            if retry.prior_retry_id != prior_retry_id:
                raise ValueError("workflow retry chain does not name its prior authorization")
            prior_tokens = self.cumulative_tokens_by_failure.get(failure.id)
            if prior_tokens is not None and retry.prior_token_count != prior_tokens:
                raise ValueError("workflow retry token accounting differs from replay")
            if self._pending_retry is not None:
                raise ValueError("workflow retry cannot start while another attempt is open")
            if retry.next_attempt_id is not None:
                if retry.next_attempt_id in self.retry_attempt_ids:
                    raise ValueError("workflow retry attempt identity is already in use")
            if prior_retry_id is not None:
                prior = self.workflow_retries[prior_retry_id]
                if (
                    retry.maximum_attempts != prior.maximum_attempts
                    or retry.attempt_fence != prior.attempt_fence
                ):
                    raise ValueError("workflow retry changed its frozen retry fence")
            calls = self.calls_by_failure.get(failure.id, [])
            if not calls:
                raise ValueError("workflow retry requires a replayed failed model call")
            call = calls[-1]
            fence = retry.attempt_fence
            if call.role != fence.role or not call.attempt_trace:
                raise ValueError("workflow retry role differs from the failed call")
            for attempt in call.attempt_trace:
                if attempt.contract_id != fence.contract_id:
                    raise ValueError("workflow retry contract differs from the failed call")
                if (
                    attempt.seat != fence.seat
                    or attempt.endpoint_id != fence.endpoint_id
                    or attempt.route_sha256 != fence.route_sha256
                ):
                    raise ValueError("workflow retry route differs from the failed call")

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
                matched_reviews = [
                    review
                    for review in failed_reviews
                    if review.bridge_output_id in input_ids
                    and review.claim_ledger_id == output.claim_ledger_id
                ]
                if not matched_reviews:
                    raise ValueError(
                        "repair output must retain the failed review's claim ledger"
                    )
                for review in matched_reviews:
                    self._assert_safe_repair(
                        self.outputs[review.bridge_output_id], output
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
            if len(completed_outputs) != 1:
                raise ValueError("completed bridge event requires exactly one bridge output")
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
                review_ids = input_ids & self.grounding_reviews.keys()
                if len(review_ids) > 1:
                    raise ValueError("completed bridge event permits at most one review")
                if review_ids:
                    review = self.grounding_reviews[next(iter(review_ids))]
                    if review.passed:
                        if (
                            review.claim_ledger_id != output.claim_ledger_id
                            or review.bridge_output_id != output_id
                        ):
                            raise ValueError(
                                "completed passed review must name the terminal output"
                            )
                    else:
                        if not self._repair_lineage(output_id, review):
                            raise ValueError(
                                "completed failed review requires a replayed safe repair"
                            )
                        self._assert_safe_repair(
                            self.outputs[review.bridge_output_id], output
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
            "bridge-failure": self.failures,
            "bridge-workflow-retry": self.workflow_retries,
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
        if self._pending_retry is not None and event.bridge.action != BridgeAction.WORKFLOW_RETRY_STARTED:
            if self._awaiting_retry_attempt_start:
                if event.bridge.action not in {
                    BridgeAction.LEDGER_CREATED,
                    BridgeAction.FAILED,
                }:
                    raise ValueError(
                        "authorized workflow retry is not linked to a fresh attempt"
                    )
                if event.bridge.action == BridgeAction.LEDGER_CREATED:
                    fence = self._pending_retry.attempt_fence
                    if not any(
                        schema == "bridge-ledger-input-catalog" and oid == fence.catalog_id
                        for schema, oid, _obj in records
                    ):
                        raise ValueError("workflow retry did not reuse its sealed catalog")
                    if event.llm is not None:
                        if event.llm.role != fence.role or any(
                            attempt.contract_id != fence.contract_id
                            or attempt.seat != fence.seat
                            or attempt.endpoint_id != fence.endpoint_id
                            or attempt.route_sha256 != fence.route_sha256
                            for attempt in event.llm.attempt_trace
                        ):
                            raise ValueError(
                                "workflow retry start changed contract or route"
                            )
        self.validate(payload, records)
        for schema, oid, obj in records:
            self._register(schema, oid, obj, event.seq)
        self.event_seqs.append(event.seq)
        self.events_by_action.setdefault(payload.action, []).append(event.seq)
        self.inputs_by_event[event.seq] = list(event.inputs)
        self.outputs_by_event[event.seq] = list(event.outputs)
        if event.llm is not None:
            self._attempt_tokens += event.llm.tokens
            self._attempt_calls.append(event.llm)
        if payload.action == BridgeAction.WORKFLOW_RETRY_STARTED:
            retry = records[-1][2]
            self._pending_retry = retry
            self._awaiting_retry_attempt_start = True
            if retry.next_attempt_id is not None:
                self.retry_attempt_ids[retry.next_attempt_id] = retry.id
            self._attempt_tokens = 0
            self._attempt_calls = []
        elif self._pending_retry is not None:
            self._awaiting_retry_attempt_start = False
        if payload.action == BridgeAction.COMPLETED:
            self.completed_events.append(event.seq)
            self._pending_retry = None
            self._awaiting_retry_attempt_start = False
            self._attempt_tokens = 0
            self._attempt_calls = []
        elif payload.action == BridgeAction.FAILED:
            self.failed_events.append(event.seq)
            self.error_codes_by_event[event.seq] = payload.error_code
            failure = next(
                (
                    obj
                    for schema, _oid, obj in records
                    if schema == "bridge-failure"
                ),
                None,
            )
            if failure is None:
                self._pending_retry = None
                self._awaiting_retry_attempt_start = False
                self._attempt_tokens = 0
                self._attempt_calls = []
                return
            pending = self._pending_retry
            self.attempt_number_by_failure[failure.id] = (
                pending.attempt_number if pending is not None else 1
            )
            prior_tokens = pending.prior_token_count if pending is not None else 0
            self.cumulative_tokens_by_failure[failure.id] = (
                prior_tokens + self._attempt_tokens
            )
            if pending is not None:
                self.retry_id_by_failure[failure.id] = pending.id
            self.calls_by_failure[failure.id] = list(self._attempt_calls)
            self._pending_retry = None
            self._awaiting_retry_attempt_start = False
            self._attempt_tokens = 0
            self._attempt_calls = []


def rebuild_bridge_state(objects: ObjectStore, events: Iterable[Event]) -> BridgeState:
    state = BridgeState()
    for event in events:
        state.apply(event, objects)
    return state


__all__ = ["BridgeState", "rebuild_bridge_state"]
