"""Post-run invariant checker — the chaos battery's measuring instrument.

Every check is a hard property the spec promises regardless of how badly
the engine LLM behaves: replay determinism (§0), accounting totality
(every token on the log exactly once), graph well-formedness (§2), and
detection totality. ``verify_root`` returns named violations so a report
can say WHICH promise broke; the chaos battery treats every entry as a
bug candidate.
"""

import json
from enum import Enum
from pathlib import Path

from deepreason.adjudication.edges import DependenceCycleError, build_dep, toposort
from deepreason.bridge.events import BridgeAction
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.controller import ENVELOPES, GENERATOR_LEDGER
from deepreason.harness import Harness
from deepreason.llm.firewall import route_fingerprint
from deepreason.ontology.state import Status
from deepreason.run_manifest import (
    MANIFEST_HASH_NAME,
    MANIFEST_NAME,
    load_run_manifest,
    resolve_route_seat_behavioral_capability,
    resolve_route_seat_base_profile,
)


class ExpectedCallOutcome(str, Enum):
    """Attempt-validity shape authorized by one typed process event."""

    SUCCESS_REQUIRED = "success_required"
    FAILURE_REQUIRED = "failure_required"
    LEGACY_DROPPED = "legacy_dropped"


def _is_typed_bridge_failure(event) -> bool:
    payload = event.bridge
    return bool(
        event.rule.value == "Bridge"
        and payload is not None
        and payload.action == BridgeAction.FAILED
        and payload.error_code
        and event.llm is not None
    )


def _legacy_bridge_failure_call_seqs(events, bridge_state) -> set[int]:
    """Correlate only the historical Stage-A three-event failure shape.

    Older bridge workflows put exhausted Stage-A spend on LEDGER_CREATED,
    followed immediately by LEDGER_VALIDATED and a typed FAILED event.  This
    resolver recognizes that exact canonical chain; near misses remain normal
    successful-call candidates and therefore fail attempt validity.
    """

    correlated: set[int] = set()
    for index in range(len(events) - 2):
        created, validated, failed = events[index : index + 3]
        if not (
            created.rule.value == validated.rule.value == failed.rule.value == "Bridge"
            and created.bridge is not None
            and created.bridge.action == BridgeAction.LEDGER_CREATED
            and created.llm is not None
            and validated.bridge is not None
            and validated.bridge.action == BridgeAction.LEDGER_VALIDATED
            and validated.llm is None
            and failed.bridge is not None
            and failed.bridge.action == BridgeAction.FAILED
            and failed.llm is None
            and failed.bridge.error_code == "BRIDGE_LEDGER_REPAIR_EXHAUSTED"
        ):
            continue
        failures = [
            bridge_state.failures[output]
            for output in failed.outputs
            if output in bridge_state.failures
        ]
        if len(failures) != 1:
            continue
        failure = failures[0]
        ledger_id = failure.claim_ledger_id
        report_id = failure.validation_report_id
        if not (
            failure.phase == "stage_a"
            and failure.error_code == failed.bridge.error_code
            and ledger_id is not None
            and report_id is not None
            and any(
                diagnostic.code == "BRIDGE_LEDGER_REPAIR_EXHAUSTED"
                for diagnostic in failure.diagnostics
            )
            and {
                failure.evidence_pack_id,
                failure.catalog_id,
                ledger_id,
            }.issubset(set(created.outputs))
            and list(validated.inputs) == [ledger_id]
            and validated.bridge.finding_ref == report_id
            and report_id in validated.outputs
            and list(failed.inputs) == [ledger_id, report_id]
            and list(failure.terminal_inputs) == [ledger_id, report_id]
        ):
            continue
        correlated.add(created.seq)
    return correlated


def _expected_call_outcome(
    event,
    legacy_failure_call_seqs: set[int],
    workflow_failure_call_seqs: set[int],
) -> ExpectedCallOutcome:
    if (
        event.seq in legacy_failure_call_seqs
        or event.seq in workflow_failure_call_seqs
        or _is_typed_bridge_failure(event)
    ):
        return ExpectedCallOutcome.FAILURE_REQUIRED
    if any(
        value == "dropped-call"
        or value.endswith("-dropped")
        or value in {"budget-exhausted", "terminal-route-firewall"}
        for value in event.inputs
    ):
        return ExpectedCallOutcome.LEGACY_DROPPED
    return ExpectedCallOutcome.SUCCESS_REQUIRED


def _controller_v3_history(root: Path) -> tuple[list[dict], dict]:
    """Audit controller-v3 correlations without changing the inspected root.

    The controller-v3 provider event and the later formal event are deliberately
    non-adjacent.  Their durable join is::

        Conj ``conjecture-call:<event-seq>``
          -> provider-result event
          -> ProviderAttemptV1
          -> DispatchAuthorizationBundleV1 / WorkPreparationV1
          -> SemanticAdmissionV1.admitted_refs

    This pass reads those canonical records directly.  In particular it does
    not synthesize a historical ``TransitionDecisionV1`` or infer identity from
    school names, timestamps, provider text, or list position.
    """

    findings: list[dict] = []
    seen_findings: set[tuple[str, str]] = set()

    def finding(check: str, detail: str) -> None:
        key = (check, detail)
        if key not in seen_findings:
            seen_findings.add(key)
            findings.append({"check": check, "detail": detail[:400]})

    context = {
        "events": (),
        "provider_events_by_seq": {},
        "transition_by_id": {},
        "failure_call_seqs": set(),
    }
    manifest_path = Path(root) / MANIFEST_NAME
    try:
        manifest = load_run_manifest(manifest_path)
    except Exception:  # the main verifier reports manifest/open failures
        return findings, context
    if manifest.schema_version != 6:
        return findings, context

    from deepreason.log.event_log import EventLog
    from deepreason.storage.objects import ObjectStore
    from deepreason.workflow.transaction import (
        DispatchAuthorizationBundleV1,
        ProviderAttemptV1,
        SemanticAdmissionV1,
        WorkLifecycleTransitionV1,
        WorkPreparationV1,
        WorkTransitionKind,
    )

    try:
        events = tuple(EventLog(Path(root) / "log.jsonl", read_only=True).read())
    except Exception:  # malformed logs remain the main verifier's open finding
        return findings, context
    context["events"] = events
    objects = ObjectStore(Path(root) / "objects", read_only=True)
    rows_by_work: dict[str, list[tuple[object, WorkLifecycleTransitionV1, dict]]] = {}
    preparations: dict[str, WorkPreparationV1] = {}
    authorizations: dict[str, DispatchAuthorizationBundleV1] = {}
    authorization_owner: dict[str, str] = {}
    attempt_owner: dict[str, tuple[str, int]] = {}
    admissions: dict[tuple[str, int], list[SemanticAdmissionV1]] = {}
    provider_rows: dict[int, dict] = {}

    transaction_actions = {"work_transition", "provider_result"}
    for event in events:
        payload = getattr(event, "control", None)
        if (
            getattr(payload, "schema_", None) != "control.event.v3"
            or getattr(payload, "action", None) not in transaction_actions
        ):
            continue
        try:
            transition_schema, transition = objects.get(payload.decision_ref)
        except Exception as error:  # noqa: BLE001 - corrupt durable authority
            finding(
                "workflow-decision",
                f"event seq={event.seq}: lifecycle transition is unavailable: {error!r}",
            )
            continue
        if (
            transition_schema != "workflow-work-lifecycle-transition-v1"
            or not isinstance(transition, WorkLifecycleTransitionV1)
        ):
            finding(
                "workflow-decision",
                f"event seq={event.seq}: decision is not a controller-v3 lifecycle transition",
            )
            continue
        previous = context["transition_by_id"].setdefault(transition.id, transition)
        if previous is not transition:
            finding(
                "workflow-decision",
                f"event seq={event.seq}: lifecycle transition is ambiguously reused",
            )
        records: dict[str, tuple[str, object]] = {}
        for object_id in event.outputs:
            try:
                records[object_id] = objects.get(object_id)
            except Exception as error:  # noqa: BLE001 - missing committed output
                finding(
                    "workflow-decision",
                    f"event seq={event.seq}: transaction output is unavailable: {error!r}",
                )
        if (
            tuple(event.inputs) != (transition.work_id, transition.trigger_ref)
            or tuple(payload.inputs) != tuple(event.inputs)
            or tuple(payload.outputs) != tuple(event.outputs)
            or not event.outputs
            or event.outputs[-1] != transition.id
        ):
            finding(
                "workflow-decision",
                f"event seq={event.seq}: transition envelope differs from durable work identity",
            )
        expected_action = (
            "provider_result"
            if transition.transition_kind == WorkTransitionKind.PROVIDER_RESULT
            else "work_transition"
        )
        if payload.action != expected_action:
            finding(
                "workflow-decision",
                f"event seq={event.seq}: control action differs from lifecycle phase",
            )
        phase_records = [
            value for object_id, value in records.items() if object_id != transition.id
        ]
        if any(
            getattr(record, "work_id", None) != transition.work_id
            or getattr(record, "attempt_index", None) != transition.attempt_index
            for _schema, record in phase_records
        ):
            finding(
                "workflow-decision",
                f"event seq={event.seq}: lifecycle phase contains cross-work records",
            )
        rows_by_work.setdefault(transition.work_id, []).append(
            (event, transition, records)
        )

        for schema, record in phase_records:
            if schema == "workflow-work-preparation-v1" and isinstance(
                record, WorkPreparationV1
            ):
                if record.id in preparations:
                    finding(
                        "workflow-decision",
                        f"event seq={event.seq}: work preparation is duplicated",
                    )
                preparations[record.id] = record
            elif schema == "workflow-dispatch-authorization-v1" and isinstance(
                record, DispatchAuthorizationBundleV1
            ):
                owner = authorization_owner.setdefault(record.id, transition.work_id)
                if owner != transition.work_id:
                    finding(
                        "workflow-call-pairing",
                        f"event seq={event.seq}: authorization is reused across work",
                    )
                authorizations[record.id] = record
            elif schema == "workflow-provider-attempt-v1" and isinstance(
                record, ProviderAttemptV1
            ):
                owner = attempt_owner.setdefault(
                    record.id, (transition.work_id, transition.attempt_index)
                )
                if owner != (transition.work_id, transition.attempt_index):
                    finding(
                        "workflow-call-pairing",
                        f"event seq={event.seq}: provider attempt is reused across work",
                    )
            elif schema == "workflow-semantic-admission-v1" and isinstance(
                record, SemanticAdmissionV1
            ):
                admissions.setdefault(
                    (transition.work_id, transition.attempt_index), []
                ).append(record)

        if transition.transition_kind == WorkTransitionKind.PROVIDER_RESULT:
            provider_attempts = [
                record
                for schema, record in phase_records
                if schema == "workflow-provider-attempt-v1"
                and isinstance(record, ProviderAttemptV1)
            ]
            call = event.llm
            if len(provider_attempts) != 1 or call is None:
                finding(
                    "workflow-call-pairing",
                    f"event seq={event.seq}: provider result lacks one durable call/attempt pair",
                )
                continue
            attempt = provider_attempts[0]
            authorization = authorizations.get(attempt.authorization_bundle_ref)
            if authorization is None:
                try:
                    schema, candidate = objects.get(attempt.authorization_bundle_ref)
                except Exception:  # reported by the exact pairing comparison below
                    candidate = None
                    schema = None
                if schema == "workflow-dispatch-authorization-v1" and isinstance(
                    candidate, DispatchAuthorizationBundleV1
                ):
                    authorization = candidate
            exact_pair = bool(
                authorization is not None
                and authorization.work_id == transition.work_id
                and authorization.attempt_index == transition.attempt_index
                and call.work_order_id == transition.work_id
                and call.dispatch_authorization_ref == authorization.id
                and attempt.authorization_bundle_ref == authorization.id
                and attempt.contract_id == authorization.contract_id
                and attempt.route_lease == authorization.route_lease
                and attempt.prompt_sha256 == authorization.prompt_sha256
                and attempt.raw_ref == call.raw_ref
            )
            if not exact_pair:
                finding(
                    "workflow-call-pairing",
                    f"event seq={event.seq}: provider result differs from its authorized attempt",
                )
            duplicate = next(
                (
                    row
                    for row in provider_rows.values()
                    if row["attempt"].id == attempt.id
                    or (
                        row["work_id"] == transition.work_id
                        and row["attempt_index"] == transition.attempt_index
                    )
                ),
                None,
            )
            if duplicate is not None:
                finding(
                    "workflow-call-pairing",
                    f"event seq={event.seq}: provider result pairing is duplicate or ambiguous",
                )
            provider_rows[int(event.seq)] = {
                "event": event,
                "transition": transition,
                "attempt": attempt,
                "authorization": authorization,
                "work_id": transition.work_id,
                "attempt_index": transition.attempt_index,
            }

    legal_progressions = {
        (WorkTransitionKind.WORK_PREPARED,),
        (WorkTransitionKind.WORK_PREPARED, WorkTransitionKind.WORK_ISSUED),
        (
            WorkTransitionKind.WORK_PREPARED,
            WorkTransitionKind.WORK_ISSUED,
            WorkTransitionKind.PROVIDER_RESULT,
        ),
        (
            WorkTransitionKind.WORK_PREPARED,
            WorkTransitionKind.WORK_ISSUED,
            WorkTransitionKind.PROVIDER_RESULT,
            WorkTransitionKind.SEMANTIC_ADMISSION,
        ),
        (WorkTransitionKind.WORK_PREPARED, WorkTransitionKind.BUDGET_DENIED),
        (WorkTransitionKind.WORK_PREPARED, WorkTransitionKind.WORK_TERMINATED),
        (
            WorkTransitionKind.WORK_PREPARED,
            WorkTransitionKind.WORK_ISSUED,
            WorkTransitionKind.WORK_TERMINATED,
        ),
        (
            WorkTransitionKind.WORK_PREPARED,
            WorkTransitionKind.WORK_ISSUED,
            WorkTransitionKind.PROVIDER_RESULT,
            WorkTransitionKind.WORK_TERMINATED,
        ),
        (
            WorkTransitionKind.WORK_PREPARED,
            WorkTransitionKind.WORK_ISSUED,
            WorkTransitionKind.PROVIDER_RESULT,
            WorkTransitionKind.SEMANTIC_ADMISSION,
            WorkTransitionKind.WORK_TERMINATED,
        ),
    }
    for work_id, rows in rows_by_work.items():
        seqs = tuple(int(row[0].seq) for row in rows)
        progression = tuple(row[1].transition_kind for row in rows)
        attempts_for_work = {row[1].attempt_index for row in rows}
        transition_ids = tuple(row[1].id for row in rows)
        if (
            seqs != tuple(sorted(seqs))
            or len(seqs) != len(set(seqs))
            or len(transition_ids) != len(set(transition_ids))
            or len(attempts_for_work) != 1
            or progression not in legal_progressions
            or work_id not in preparations
        ):
            finding(
                "workflow-decision",
                f"work {work_id}: lifecycle progression is missing, duplicate, out of order, or ambiguous",
            )

    # Every transaction-authorized call must be the call on exactly one
    # provider-result transition.  A detached LLM event is not accepted as a
    # substitute for the missing lifecycle decision.
    for event in events:
        call = event.llm
        if call is None or call.dispatch_authorization_ref is None:
            continue
        row = provider_rows.get(int(event.seq))
        if row is None:
            finding(
                "workflow-decision",
                f"event seq={event.seq}: transaction call has no provider-result lifecycle transition",
            )
            finding(
                "workflow-call-pairing",
                f"event seq={event.seq}: transaction call has no authorized attempt result",
            )

    # Associate each formal Conj event with the exact provider attempt and the
    # later admission that made its output durable.  The source event may be
    # separated by arbitrary intervening records.
    source_users: dict[int, int] = {}
    admitted_owners: dict[str, set[tuple[str, int]]] = {}
    for key, values in admissions.items():
        for admission in values:
            for ref in admission.admitted_refs:
                # A content-addressed formal artifact may be independently
                # rediscovered and admitted by more than one provider attempt.
                # Ownership is therefore the provider-attempt/admission pair,
                # not global uniqueness of the semantic object ID.
                admitted_owners.setdefault(ref, set()).add(key)
    for event in events:
        if event.rule.value != "Conj":
            continue
        refs = [
            value for value in event.inputs if value.startswith("conjecture-call:")
        ]
        if not refs:
            continue
        try:
            source_seqs = tuple(
                int(value.removeprefix("conjecture-call:")) for value in refs
            )
        except ValueError:
            source_seqs = ()
        if len(source_seqs) != 1:
            finding(
                "workflow-call-pairing",
                f"event seq={event.seq}: Conj has an ambiguous provider-result reference",
            )
            continue
        source_seq = source_seqs[0]
        row = provider_rows.get(source_seq)
        if row is None or source_seq >= int(event.seq):
            finding(
                "workflow-call-pairing",
                f"event seq={event.seq}: Conj source is not one preceding provider attempt",
            )
            continue
        previous_user = source_users.setdefault(source_seq, int(event.seq))
        if previous_user != int(event.seq):
            finding(
                "workflow-call-pairing",
                f"event seq={event.seq}: provider result is reused by multiple Conj records",
            )
        key = (row["work_id"], row["attempt_index"])
        matching_admissions = [
            admission
            for admission in admissions.get(key, ())
            if admission.provider_attempt_ref == row["attempt"].id
            and set(event.outputs).issubset(set(admission.admitted_refs))
        ]
        if len(matching_admissions) != 1:
            owners = {
                owner
                for output in event.outputs
                for owner in admitted_owners.get(output, ())
            }
            cross_work = bool(owners) and key not in owners
            finding(
                "workflow-call-pairing",
                f"event seq={event.seq}: Conj outputs are {'cross-work' if cross_work else 'not uniquely'} admitted by their provider attempt",
            )

    # Verify the school receipt through the frozen work preparation and route
    # lease.  The generic school verifier below separately checks that the same
    # receipt resolves to the manifest's frozen route-seat policy.
    for source_seq, row in provider_rows.items():
        preparation = preparations.get(row["work_id"])
        authorization = row["authorization"]
        attempt = row["attempt"]
        call = row["event"].llm
        if preparation is None or authorization is None or call is None:
            continue
        payload = preparation.task_payload_value
        school_id = payload.get("school_id") if hasattr(payload, "get") else None
        receipt = call.school_route
        if school_id is not None and receipt is None:
            finding(
                "school-route",
                f"event seq={source_seq}: school work has no route-seat receipt",
            )
            continue
        if receipt is not None and (
            receipt.school_id != school_id
            or receipt.role != preparation.route_lease.role
            or receipt.seat != preparation.route_lease.seat
            or receipt.endpoint_id != preparation.route_lease.endpoint_id
            or receipt.route_sha256 != preparation.route_lease.route_sha256
            or receipt.contract_id != preparation.contract_id
            or authorization.route_lease != preparation.route_lease
            or attempt.route_lease != preparation.route_lease
        ):
            finding(
                "school-route",
                f"event seq={source_seq}: provider route differs from prepared route-seat lease",
            )

    for source_seq, row in provider_rows.items():
        key = (row["work_id"], row["attempt_index"])
        admission = next(
            (
                value
                for value in admissions.get(key, ())
                if value.provider_attempt_ref == row["attempt"].id
            ),
            None,
        )
        if row["attempt"].outcome == "transport_failure" or (
            admission is not None and admission.outcome != "admitted"
        ):
            context["failure_call_seqs"].add(source_seq)
    context["provider_events_by_seq"] = {
        seq: row["event"] for seq, row in provider_rows.items()
    }
    return findings, context


def verify_root(root: Path, meter_total: int | None = None) -> dict:
    """Run every invariant over the session at ``root``. Returns
    {"violations": [{"check", "detail"}, ...], "stats": {...}}."""
    violations: list[dict] = []

    def fail(check: str, detail: str) -> None:
        violations.append({"check": check, "detail": detail[:400]})

    # Controller-v3 history is correlated from durable records before normal
    # replay.  If replay cannot open a corrupted history, these typed findings
    # retain the exact failed boundary instead of collapsing it to a generic
    # legacy verifier error.
    controller_v3_findings, controller_v3 = _controller_v3_history(Path(root))

    # 1. Replay determinism: two independent materializations agree.
    try:
        h = Harness(root, read_only=True)
        second = Harness(root, read_only=True)
        if second.state.model_dump_json() != h.state.model_dump_json():
            fail("replay", "two replays of the same log produced different state")
        if second.scratch_state != h.scratch_state:
            fail("scratch-replay", "two replays produced different advisory scratch state")
        if second.bridge_state != h.bridge_state:
            fail("bridge-replay", "two replays produced different advisory bridge state")
        if second.workflow_state.digest != h.workflow_state.digest:
            fail("workflow-replay", "two replays produced different authority state")
        if second.capability_state.digest != h.capability_state.digest:
            fail("capability-replay", "two replays produced different capability state")
    except Exception as e:  # noqa: BLE001 - an unopenable root is the finding
        if controller_v3_findings:
            return {"violations": controller_v3_findings, "stats": {}}
        return {"violations": [{"check": "open", "detail": repr(e)[:400]}], "stats": {}}

    for item in controller_v3_findings:
        fail(str(item["check"]), str(item["detail"]))

    events = list(h.log.read())
    legacy_failure_call_seqs = _legacy_bridge_failure_call_seqs(
        events, h.bridge_state
    )
    workflow_failure_call_seqs = {
        receipt.source_call_seq
        for receipt in h.workflow_state.proposal_receipts.values()
        if receipt.validation_outcome.value
        in {"repair_exhausted", "transport_failed"}
    }
    workflow_failure_call_seqs.update(controller_v3["failure_call_seqs"])

    # Process metadata is replay/audit input only.  Its checks never inspect
    # or alter att, dep, status, warrants, guards, or acceptance.
    manifest = None
    manifest_path = Path(root) / MANIFEST_NAME
    if manifest_path.exists():
        hash_path = Path(root) / MANIFEST_HASH_NAME
        if not hash_path.exists():
            fail("run-manifest-hash", f"missing {MANIFEST_HASH_NAME}")
        try:
            manifest = load_run_manifest(manifest_path)
            if manifest_path.read_bytes() != manifest.canonical_bytes():
                fail("run-manifest-canonical", "manifest bytes are not canonical JSON")
            # V1 froze one shared compatibility profile.  V2 deliberately
            # separates workload pack shape, transport model capacity, and
            # output wire shape (e.g. reasoning.text.v1 / compact /
            # compact.v2); equality would reject every legal v2 root.
            if (
                manifest.schema_version == 1
                and manifest.pack_profile != manifest.model_profile
            ):
                fail(
                    "profile-metadata",
                    f"pack_profile={manifest.pack_profile!r} differs from "
                    f"model_profile={manifest.model_profile!r}",
                )
            if (
                manifest.schema_version == 1
                and manifest.output_profile != manifest.model_profile
            ):
                fail(
                    "profile-metadata",
                    f"output_profile={manifest.output_profile!r} differs from "
                    f"model_profile={manifest.model_profile!r}",
                )
        except Exception as e:  # noqa: BLE001 - invalid metadata is the finding
            fail("run-manifest", repr(e))

    control_events = [event for event in events if event.control is not None]
    if control_events:
        control = (
            manifest.control_plane_policy
            if manifest is not None and manifest.schema_version in {4, 5, 6}
            else None
        )
        expected_control = (
            ("workflow.controller.v3", "active_inquiry", "control.event.v3")
            if manifest is not None and manifest.schema_version == 6
            else ("workflow.controller.v2", "active_inquiry", "control.event.v2")
            if manifest is not None and manifest.schema_version == 5
            else ("workflow.controller.v1", None, "control.event.v1")
        )
        if (
            control is None
            or control.controller_version != expected_control[0]
            or (
                expected_control[1] is not None
                and control.mode != expected_control[1]
            )
            or (
                expected_control[1] is None
                and control.mode not in {"shadow", "active_conjecture"}
            )
            or control.contract_versions.control_event_schema != expected_control[2]
        ):
            fail(
                "workflow-manifest",
                "Control events require an opt-in v4 workflow controller profile",
            )
        else:
            from deepreason.workflow.profiles import compile_workflow_profile

            try:
                workflow_profile = compile_workflow_profile(manifest)
            except Exception as e:  # noqa: BLE001 - invalid authority is a finding
                workflow_profile = None
                fail(
                    "workflow-manifest",
                    f"cannot compile workflow authority: {e!r}",
                )

            for event in control_events:
                control_action = getattr(event.control, "action", None)
                transaction_transition = controller_v3["transition_by_id"].get(
                    event.control.decision_ref
                )
                if transaction_transition is not None:
                    if (
                        transaction_transition.controller_version
                        != control.controller_version
                        or transaction_transition.workflow_profile
                        != control.workflow_profile
                    ):
                        fail(
                            "workflow-manifest",
                            f"event seq={event.seq}: transaction transition differs from manifest authority",
                        )
                    continue
                decision = h.workflow_state.decisions.get(
                    event.control.decision_ref
                )
                lifecycle = h.workflow_state.lifecycle_decisions.get(
                    event.control.decision_ref
                )
                resume = h.workflow_state.resume_decisions.get(
                    event.control.decision_ref
                )
                terminal_commitment = next(
                    (
                        item
                        for item in h.workflow_state.terminal_commitments_by_epoch.values()
                        if item.id == event.control.decision_ref
                    ),
                    None,
                )
                classification_binding = (
                    h.workflow_state.model_classification_binding
                    if control_action == "classification_bound"
                    else None
                )
                decomposition_record = None
                if control_action == "contract_decomposition_activated":
                    decomposition_record = next(
                        (
                            item
                            for item in h.workflow_state.contract_decomposition_by_source_work.values()
                            if item.id == event.control.decision_ref
                        ),
                        None,
                    )
                elif control_action == "contract_decomposition_completed":
                    decomposition_record = next(
                        (
                            item
                            for item in h.workflow_state.contract_decomposition_completion_by_transition.values()
                            if item.id == event.control.decision_ref
                        ),
                        None,
                    )
                if decision is None:
                    process_decision = (
                        lifecycle
                        or resume
                        or terminal_commitment
                        or classification_binding
                        or decomposition_record
                    )
                    if process_decision is None:
                        fail(
                            "workflow-decision",
                            f"event seq={event.seq}: decision is absent after replay",
                        )
                        continue
                    if decomposition_record is not None:
                        if (
                            decomposition_record.manifest_digest != manifest.sha256
                            or tuple(event.outputs) != (decomposition_record.id,)
                        ):
                            fail(
                                "contract-decomposition-authority",
                                f"event seq={event.seq}: decomposition record "
                                "differs from replayed manifest authority",
                        )
                        continue
                    if terminal_commitment is not None:
                        if (
                            terminal_commitment.manifest_sha256 != manifest.sha256
                            or terminal_commitment.run_id != manifest.sha256
                            or h.workflow_state.terminal_commitment_event_seq.get(
                                terminal_commitment.id
                            )
                            != event.seq
                        ):
                            fail(
                                "workflow-manifest",
                                f"event seq={event.seq}: terminal commitment differs from manifest authority",
                            )
                        continue
                    if classification_binding is not None:
                        plan = h.workflow_state.route_seat_model_classification
                        if (
                            plan is None
                            or event.seq
                            != h.workflow_state.model_classification_event_seq
                            or tuple(event.outputs)
                            != (plan.id, classification_binding.id)
                            or classification_binding.manifest_digest
                            != manifest.sha256
                        ):
                            fail(
                                "model-classification-authority",
                                f"event seq={event.seq}: classification binding "
                                "differs from replayed manifest authority",
                            )
                        continue
                    if (
                        process_decision.manifest_digest != manifest.sha256
                        or process_decision.workflow_profile != control.workflow_profile
                        or process_decision.controller_version
                        != control.controller_version
                    ):
                        fail(
                            "workflow-manifest",
                            f"event seq={event.seq}: lifecycle decision differs from manifest authority",
                        )
                    continue
                if (
                    decision.manifest_digest != manifest.sha256
                    or decision.workflow_profile != control.workflow_profile
                ):
                    fail(
                        "workflow-manifest",
                        f"event seq={event.seq}: decision differs from manifest authority",
                    )
            if workflow_profile is not None:
                if (
                    workflow_profile.conjecturer_contract_id
                    in {"conjecturer.turn.v4", "conjecturer.turn.v5", "conjecturer.turn.v6"}
                ):
                    authorized_contract_ids = {
                        workflow_profile.conjecturer_contract_id
                    }
                else:
                    from deepreason.llm.contracts import ConjecturerOutput
                    from deepreason.llm.wire import (
                        AliasTable,
                        wire_contract_for,
                    )
                    from deepreason.workloads.text import (
                        ReasoningConjecturerOutput,
                    )

                    transport_profiles = {manifest.model_profile}
                    if (
                        manifest.schema_version < 6
                        and manifest.model_profile in {"standard", "frontier"}
                    ):
                        # A logged direct-contract exhaustion can arm compact
                        # transport for a later call without changing the
                        # manifest's frozen model identity.
                        transport_profiles.add("compact")
                    authorized_contract_ids = {
                        wire_contract_for(
                            "conjecturer",
                            output_model,
                            transport_profile,
                            AliasTable(),
                        ).contract_id
                        for output_model in (
                            ConjecturerOutput,
                            ReasoningConjecturerOutput,
                        )
                        for transport_profile in transport_profiles
                    }
                    # The reducer-owned semantic profile remains a valid
                    # authority label for work planned before a concrete
                    # provider transport is selected.
                    authorized_contract_ids.add(
                        workflow_profile.conjecturer_contract_id
                    )
                    if (
                        manifest.engine_profile == "mini"
                        and manifest.model_profile == "compact"
                    ):
                        # Mini's compact conjecturer intentionally omits
                        # references instead of exposing an unusable empty
                        # alias table. It is still the parent's canonical
                        # wire contract and is frozen by the Mini engine/profile
                        # tuple rather than a client-selected route.
                        from deepreason.llm.wire import (
                            ReferenceFreeConjecturerWireContract,
                        )

                        authorized_contract_ids.add(
                            ReferenceFreeConjecturerWireContract().contract_id
                        )
                context_limit = (
                    workflow_profile.context_policy.max_context_expansion_requests
                )
                authorized_grants = tuple(
                    workflow_profile.capability_grant(
                        completed_context_expansions=completed
                    )
                    for completed in range(context_limit + 1)
                )
                try:
                    engine_config = json.loads(manifest.engine_config_json)
                    school_count = engine_config.get("N_SCHOOLS")
                except (TypeError, json.JSONDecodeError):
                    school_count = None

                for work in h.workflow_state.work_orders.values():
                    differences: list[str] = []
                    if work.manifest_digest != manifest.sha256:
                        differences.append("manifest_digest")
                    if work.workflow_profile != control.workflow_profile:
                        differences.append("workflow_profile")
                    if work.contract_id not in authorized_contract_ids:
                        differences.append("contract_id")
                    if work.repair_policy_ref != workflow_profile.repair_policy.id:
                        differences.append("repair_policy_ref")
                    if work.capability_grant not in authorized_grants:
                        differences.append("capability_grant")

                    expected_seat = 0
                    school_policy = control.school_execution
                    if work.school_id is not None:
                        if (
                            isinstance(school_count, bool)
                            or not isinstance(school_count, int)
                            or school_count < 0
                            or work.school_id
                            not in {
                                f"school-{index}"
                                for index in range(school_count)
                            }
                        ):
                            differences.append("school_id")
                        if school_policy.mode == "route_bound":
                            bindings = tuple(
                                binding
                                for binding in school_policy.bindings
                                if binding.school_id == work.school_id
                                and binding.role == "conjecturer"
                            )
                            if len(bindings) != 1:
                                differences.append("school_route_binding")
                            else:
                                expected_seat = bindings[0].seat

                    routes = manifest.roles.get("conjecturer", ())
                    expected_route = (
                        routes[expected_seat]
                        if 0 <= expected_seat < len(routes)
                        else None
                    )
                    if expected_route is None:
                        differences.append("route_lease_seat")
                    elif (
                        work.route_lease.role != "conjecturer"
                        or work.route_lease.seat != expected_seat
                        or work.route_lease.endpoint_id
                        != expected_route.endpoint_id
                        or work.route_lease.route_sha256
                        != route_fingerprint(expected_route)
                    ):
                        differences.append("route_lease")

                    if differences:
                        fail(
                            "workflow-work-order-authority",
                            f"work order {work.id} differs from manifest authority: "
                            + ", ".join(differences),
                        )

    capability_events = [event for event in events if event.capability is not None]
    if capability_events:
        policy = (
            manifest.inquiry_capability_policy.simulation
            if manifest is not None
            and manifest.schema_version >= 5
            and manifest.inquiry_capability_policy is not None
            else None
        )
        if policy is None:
            fail(
                "capability-manifest",
                "Capability events require one manifest-bound v5+ simulation policy",
            )
        else:
            state = h.capability_state
            grants = len(state.grants)
            if grants > policy.maximum_simulation_requests:
                fail("capability-budget", "simulation grant count exceeds request policy")
            if state.execution_count > policy.maximum_simulation_executions:
                fail("capability-budget", "simulation execution count exceeds policy")
            if state.consumption_count > policy.maximum_follow_up_reasoning_turns:
                fail("capability-budget", "simulation follow-up count exceeds policy")
            for event in capability_events:
                transition = state.transitions.get(event.capability.transition_ref)
                if transition is None:
                    fail(
                        "capability-transition",
                        f"event seq={event.seq}: transition is absent after replay",
                    )
                    continue
                if (
                    transition.manifest_digest != manifest.sha256
                    or transition.run_input_digest != manifest.run_input_digest
                    or transition.capability_policy_digest != policy.digest
                ):
                    fail(
                        "capability-authority",
                        f"event seq={event.seq}: transition differs from frozen policy",
                    )
                if event.llm is not None:
                    fail(
                        "capability-authority",
                        f"event seq={event.seq}: model call authored an authority transition",
                    )
            for proposal in state.proposals.values():
                from deepreason.workflow.models import CapabilityOutcome

                if manifest.schema_version == 6:
                    from deepreason.capabilities.simulation import (
                        SimulationCapabilityController,
                    )

                    try:
                        SimulationCapabilityController(
                            h, manifest
                        ).require_transactional_origin(proposal)
                    except Exception as error:  # noqa: BLE001 - root diagnostic
                        fail(
                            "capability-origin",
                            f"proposal {proposal.id} has no completed transaction origin: {error!r}",
                        )
                    continue

                work = h.workflow_state.work_orders.get(
                    proposal.originating_work_order_ref
                )
                source = next(
                    (item for item in events if item.seq == proposal.source_call_seq),
                    None,
                )
                if (
                    proposal.originating_provider_attempt_ref is not None
                    or work is None
                    or work.problem_ref != proposal.problem_ref
                    or proposal.run_input_digest != manifest.run_input_digest
                    or work.run_input_digest != manifest.run_input_digest
                    or CapabilityOutcome.SIMULATION_REQUEST
                    not in work.capability_grant.allowed_outcomes
                    or source is None
                    or source.llm is None
                    or source.llm.work_order_id != work.id
                    or work.contract_id
                    != manifest.control_plane_policy.contract_versions.conjecturer_turn_contract
                    or any(
                        attempt.contract_id != work.contract_id
                        for attempt in source.llm.attempt_trace
                    )
                    or proposal.proposal_index
                    >= policy.maximum_proposals_per_turn
                ):
                    fail(
                        "capability-origin",
                        f"proposal {proposal.id} does not resolve to its provider work order",
                    )
            proposals_by_call: dict[int, int] = {}
            for proposal in state.proposals.values():
                proposals_by_call[proposal.source_call_seq] = (
                    proposals_by_call.get(proposal.source_call_seq, 0) + 1
                )
            if any(
                count > policy.maximum_proposals_per_turn
                for count in proposals_by_call.values()
            ):
                fail(
                    "capability-origin",
                    "one provider call exceeds its frozen proposal-count authority",
                )
            for grant in state.grants.values():
                proposal = state.proposals.get(grant.proposal_ref)
                expected_seeds = (
                    policy.fixed_seed_set
                    if policy.deterministic_seed_policy == "fixed_manifest"
                    else (proposal.requested_seed_set if proposal is not None else ())
                )
                if (
                    proposal is None
                    or grant.manifest_digest != manifest.sha256
                    or grant.run_input_digest != manifest.run_input_digest
                    or grant.policy_digest != policy.digest
                    or grant.template_identity != policy.runner_template_identity
                    or grant.backend_identity != policy.backend_identity
                    or grant.toolchain_identity != policy.python_toolchain_identity
                    or grant.seed_set != expected_seeds
                    or grant.deterministic_step_limit != policy.maximum_steps
                    or grant.sample_limit != policy.maximum_samples
                    or grant.maximum_output_bytes != policy.maximum_output_bytes
                ):
                    fail(
                        "capability-grant",
                        f"grant {grant.id} differs from its proposal or frozen policy",
                    )
            for compiled in state.compiled.values():
                grant = state.grants.get(compiled.grant_ref)
                proposal = state.proposals.get(compiled.proposal_ref)
                if (
                    grant is None
                    or proposal is None
                    or grant.proposal_ref != compiled.proposal_ref
                    or compiled.template_identity != grant.template_identity
                    or compiled.maximum_output_bytes != grant.maximum_output_bytes
                    or compiled.specification.seed_set != grant.seed_set
                    or compiled.specification.toolchain_id != grant.toolchain_identity
                    or compiled.specification.deterministic_step_limit
                    != grant.deterministic_step_limit
                    or compiled.specification.sample_limit != grant.sample_limit
                    or compiled.specification.inputs_ref != compiled.input_ref
                    or compiled.specification.checker_ref != compiled.checker_ref
                ):
                    fail(
                        "capability-compiled-authority",
                        f"compiled simulation {compiled.id} differs from its grant",
                    )
                if proposal is not None:
                    catalog = {
                        item.alias: item.value for item in policy.input_catalog
                    }
                    sealed = {
                        alias: catalog[alias]
                        for alias in proposal.input_aliases
                        if alias in catalog
                    }
                    parameters = proposal.parameter_definitions or ()
                    expected_inputs = canonical_json(
                        [
                            {
                                "parameter_set": item.name,
                                "parameters": item.values,
                                "sealed_inputs": sealed,
                            }
                            for item in parameters
                        ]
                        if parameters
                        else [
                            {
                                "parameter_set": "default",
                                "parameters": {},
                                "sealed_inputs": sealed,
                            }
                        ]
                    )
                    from deepreason.capabilities.simulation import (
                        TRUSTED_CHECKER_SOURCE_V1,
                    )

                    expected_checker = TRUSTED_CHECKER_SOURCE_V1.encode("utf-8")
                    from deepreason.simulation.compiler import (
                        compile_declarative_numeric,
                    )

                    expected_source = (
                        compile_declarative_numeric(
                            proposal.model_source,
                            proposal.requested_observables,
                        )
                        if proposal.simulation_mode == "declarative_numeric_v1"
                        else None
                    )
                    try:
                        source_payload = h.blobs.get(compiled.source_ref)
                        input_payload = h.blobs.get(compiled.input_ref)
                        checker_payload = h.blobs.get(compiled.checker_ref)
                    except KeyError:
                        pass
                    else:
                        if (
                            expected_source is None
                            or source_payload != expected_source
                            or input_payload != expected_inputs
                            or checker_payload != expected_checker
                            or compiled.specification.observables
                            != proposal.requested_observables
                            or compiled.generated_code_bytes != len(source_payload)
                            or compiled.input_bytes != len(input_payload)
                        ):
                            fail(
                                "capability-compiled-authority",
                                f"compiled simulation {compiled.id} differs from trusted template inputs",
                            )
                for ref in (
                    compiled.source_ref,
                    compiled.input_ref,
                    compiled.checker_ref,
                ):
                    try:
                        payload = h.blobs.get(ref)
                        expected_digest = {
                            compiled.source_ref: compiled.source_sha256,
                            compiled.input_ref: compiled.input_sha256,
                            compiled.checker_ref: compiled.checker_sha256,
                        }[ref]
                        if sha256_hex(payload) != expected_digest:
                            fail(
                                "capability-artifact",
                                f"compiled simulation {compiled.id} blob digest differs",
                            )
                    except Exception as error:  # noqa: BLE001
                        fail(
                            "capability-artifact",
                            f"compiled simulation {compiled.id} has missing blob: {error!r}",
                        )
            for work_order in state.work_orders.values():
                grant = state.grants.get(work_order.grant_ref)
                compiled = state.compiled.get(work_order.compiled_simulation_ref)
                if (
                    grant is None
                    or compiled is None
                    or grant.id != compiled.grant_ref
                    or work_order.proposal_ref != compiled.proposal_ref
                    or work_order.manifest_digest != manifest.sha256
                    or work_order.run_input_digest != manifest.run_input_digest
                    or work_order.policy_digest != policy.digest
                    or work_order.runner_profile != policy.runner_profile
                    or work_order.template_identity != policy.runner_template_identity
                    or work_order.backend_identity != policy.backend_identity
                    or work_order.toolchain_identity
                    != policy.python_toolchain_identity
                    or work_order.maximum_wall_ms != policy.maximum_wall_ms
                    or work_order.maximum_memory_bytes
                    != policy.maximum_memory_bytes
                    or work_order.maximum_output_bytes
                    != policy.maximum_output_bytes
                    or work_order.deterministic_step_limit != policy.maximum_steps
                    or work_order.sample_limit != policy.maximum_samples
                    or work_order.network is not False
                ):
                    fail(
                        "capability-work-order",
                        f"simulation work order {work_order.id} differs from frozen authority",
                    )
            for receipt in state.receipts.values():
                compiled = state.compiled.get(receipt.compiled_specification_ref)
                work_order = state.work_orders.get(
                    receipt.simulation_work_order_ref
                )
                if compiled is None:
                    fail(
                        "capability-receipt",
                        f"receipt {receipt.id} has no compiled specification",
                    )
                elif (
                    receipt.proposal_ref != compiled.proposal_ref
                    or work_order is None
                    or work_order.compiled_simulation_ref != compiled.id
                    or receipt.run_input_digest != manifest.run_input_digest
                    or receipt.source_sha256 != compiled.source_sha256
                    or receipt.inputs_sha256 != compiled.input_sha256
                    or receipt.checker_sha256 != compiled.checker_sha256
                    or receipt.specification_sha256
                    != sha256_hex(
                        canonical_json(
                            compiled.specification.model_dump(
                                mode="json", by_alias=True
                            )
                        )
                    )
                    or receipt.resource_limits.get("network") is not False
                ):
                    fail(
                        "capability-receipt",
                        f"receipt {receipt.id} differs from compiled execution authority",
                    )
                for attempt in receipt.attempts:
                    if (
                        attempt.fingerprint.get("backend") != policy.backend_identity
                        or attempt.fingerprint.get("toolchain_id")
                        != policy.python_toolchain_identity
                    ):
                        fail(
                            "capability-receipt",
                            f"receipt {receipt.id} used a non-manifest runner identity",
                        )
                    for ref in (
                        attempt.diagnostics_ref,
                        attempt.output_ref,
                        attempt.stdout_ref,
                        attempt.stderr_ref,
                    ):
                        if ref is None:
                            continue
                        try:
                            h.blobs.get(ref)
                        except Exception as error:  # noqa: BLE001
                            fail(
                                "capability-receipt",
                                f"receipt {receipt.id} has missing trace blob: {error!r}",
                            )
                final_output_ref = receipt.attempts[-1].output_ref
                if final_output_ref is not None:
                    try:
                        if len(h.blobs.get(final_output_ref)) != receipt.output_bytes:
                            fail(
                                "capability-receipt",
                                f"receipt {receipt.id} output byte count differs from trace",
                            )
                    except KeyError:
                        pass
            for package in state.result_packages.values():
                receipt = state.receipts.get(package.receipt_ref)
                if receipt is None:
                    fail(
                        "capability-result-package",
                        f"package {package.id} has no execution receipt",
                    )
                elif (
                    package.proposal_ref != receipt.proposal_ref
                    or package.run_input_digest != manifest.run_input_digest
                    or package.epistemic_status != "recorded_observation"
                ):
                    fail(
                        "capability-result-package",
                        f"package {package.id} differs from its execution receipt",
                    )
                for ref in (package.structured_result_ref, package.result_context_ref):
                    try:
                        h.blobs.get(ref)
                    except Exception as error:  # noqa: BLE001
                        fail(
                            "capability-result-package",
                            f"package {package.id} has missing bounded result: {error!r}",
                        )
            for consumption in state.consumptions.values():
                if manifest.schema_version == 6:
                    item = h.workflow_state.transaction_work.get(
                        consumption.follow_up_work_order_ref
                    )
                    package = state.result_packages.get(
                        consumption.result_package_ref
                    )
                    terminal = item.terminal if item is not None else None
                    admission = (
                        item.admissions.get(terminal.attempt_index)
                        if item is not None and terminal is not None
                        else None
                    )
                    payload = (
                        item.preparation.task_payload_value
                        if item is not None
                        else None
                    )
                    result_plans = (
                        tuple(
                            plan
                            for plan in item.plans.values()
                            if plan.plan_kind == "simulation_result"
                        )
                        if item is not None
                        else ()
                    )
                    result_item = (
                        result_plans[0].items[0]
                        if len(result_plans) == 1
                        and len(result_plans[0].items) == 1
                        else None
                    )
                    simulation_authority = (
                        payload.get("simulation_authority")
                        if hasattr(payload, "get")
                        else None
                    )
                    sealed_aliases = (
                        tuple(simulation_authority.get("input_aliases") or ())
                        if hasattr(simulation_authority, "get")
                        else ()
                    )
                    if (
                        item is None
                        or package is None
                        or terminal is None
                        or terminal.status != "completed"
                        or admission is None
                        or admission.outcome != "admitted"
                        or consumption.follow_up_semantic_admission_ref
                        != admission.id
                        or terminal.semantic_admission_ref != admission.id
                        or consumption.follow_up_work_order_ref
                        in h.workflow_state.work_orders
                        or consumption.run_input_digest != manifest.run_input_digest
                        or package.proposal_ref != consumption.proposal_ref
                        or package.id not in item.preparation.input_refs
                        or package.result_context_ref not in item.preparation.input_refs
                        or payload.get("capability_result_package_ref") != package.id
                        or payload.get("capability_result_context_ref")
                        != package.result_context_ref
                        or result_item is None
                        or result_item.object_ref != package.id
                        or result_item.content_sha256 != package.result_context_ref
                        or result_item.alias in sealed_aliases
                    ):
                        fail(
                            "capability-consumption",
                            f"consumption {consumption.id} has no matching fresh transaction",
                        )
                    continue

                work = h.workflow_state.work_orders.get(
                    consumption.follow_up_work_order_ref
                )
                package = state.result_packages.get(consumption.result_package_ref)
                if (
                    work is None
                    or package is None
                    or consumption.run_input_digest != manifest.run_input_digest
                    or work.run_input_digest != manifest.run_input_digest
                    or package.proposal_ref != consumption.proposal_ref
                    or consumption.result_package_ref not in work.input_refs
                    or work.task_payload_schema_id != "simulation-result-context.v1"
                    or work.task_payload_value.get("result_package_ref")
                    != consumption.result_package_ref
                    or work.task_payload_value.get("result_context_ref")
                    != package.result_context_ref
                ):
                    fail(
                        "capability-consumption",
                        f"consumption {consumption.id} has no matching fresh work order",
                    )

    if manifest is not None and manifest.schema_version >= 5:
        try:
            from deepreason.evidence.state import (
                load_evidence_dossier,
                load_run_input,
                verify_run_input,
            )

            input_verification = verify_run_input(root)
            run_input = load_run_input(root)
            dossier = load_evidence_dossier(root)
        except Exception as error:  # noqa: BLE001 - complete root diagnostic
            fail("run-input", f"bound run input is invalid: {error!r}")
            run_input = None
            dossier = None
        else:
            if (
                input_verification["run_input_digest"] != manifest.run_input_digest
                or run_input.run_input_digest != manifest.run_input_digest
            ):
                fail("run-input", "manifest and bound run-input digests differ")
            evidence = manifest.inquiry_capability_policy.attached_evidence
            if (
                len(dossier.sources) > evidence.maximum_sources
                or dossier.total_byte_count > evidence.maximum_total_bytes
            ):
                fail("run-input", "bound dossier exceeds frozen evidence authority")

            first_llm_seq = min(
                (event.seq for event in events if event.llm is not None),
                default=len(events) + 1,
            )
            source_records: dict[str, tuple[int, str]] = {}
            for event in events:
                for output in event.outputs:
                    artifact = h.state.artifacts.get(output)
                    if artifact is None or not artifact.content_ref.startswith("inline:"):
                        continue
                    try:
                        attached = json.loads(
                            artifact.content_ref.removeprefix("inline:")
                        )
                    except (TypeError, json.JSONDecodeError):
                        continue
                    if attached.get("schema") != "attached-source-record.v1":
                        continue
                    source = attached.get("source") or {}
                    source_id = str(source.get("id") or "")
                    expected = next(
                        (item for item in dossier.sources if item.id == source_id),
                        None,
                    )
                    if (
                        expected is None
                        or attached.get("run_input_digest") != run_input.run_input_digest
                        or attached.get("dossier_digest") != dossier.dossier_digest
                        or source != expected.model_dump(
                            mode="json", by_alias=True, exclude_none=True
                        )
                        or event.seq >= first_llm_seq
                        or source_id in source_records
                    ):
                        fail(
                            "attached-evidence",
                            f"event seq={event.seq}: attached source differs from its bound dossier or arrived late",
                        )
                    source_records[source_id] = (event.seq, artifact.id)
            for source in dossier.sources:
                record = source_records.get(source.id)
                if record is None:
                    fail(
                        "attached-evidence",
                        f"bound source {source.id} has no unique source record",
                    )
                    continue
                record_ref = record[1]
                candidates = [
                    artifact
                    for artifact in h.state.artifacts.values()
                    if any(
                        ref.target == record_ref and ref.role == "mention"
                        for ref in artifact.interface.refs
                    )
                ]
                if len(candidates) != 1 or not any(
                    ref.role == "dependence"
                    for ref in candidates[0].interface.refs
                ):
                    fail(
                        "attached-evidence",
                        f"bound source {source.id} lacks one reliability-dependent candidate evidence artifact",
                    )

            for event in events:
                if not event.inputs or event.inputs[0] != "dossier-pack-receipt.v1":
                    continue
                if len(event.inputs) < 2:
                    fail("dossier-pack", f"event seq={event.seq}: missing receipt reference")
                    continue
                try:
                    _schema, receipt = h.objects.get(
                        event.inputs[1], schema="dossier-pack-receipt"
                    )
                except Exception as error:  # noqa: BLE001
                    fail("dossier-pack", f"event seq={event.seq}: {error!r}")
                    continue
                source_ids = {source.id for source in dossier.sources}
                pack_work = h.workflow_state.work_orders.get(
                    receipt.work_order_ref
                )
                if (
                    receipt.run_input_digest != run_input.run_input_digest
                    or pack_work is None
                    or pack_work.run_input_digest != run_input.run_input_digest
                    or pack_work.problem_ref != dossier.problem_ref
                    or not receipt.state_fence.startswith(
                        f"formal:{pack_work.formal_fence_seq};scratch:{pack_work.scratch_fence_seq};"
                    )
                    or set(receipt.candidate_source_ids) != source_ids
                    or len(receipt.selected_source_ids)
                    > evidence.maximum_sources_per_pack
                    or sum(excerpt.byte_count for excerpt in receipt.excerpts)
                    > evidence.maximum_total_bytes
                    or any(
                        excerpt.source_id not in source_ids
                        or excerpt.byte_count
                        > evidence.maximum_excerpt_bytes_per_source
                        for excerpt in receipt.excerpts
                    )
                ):
                    fail(
                        "dossier-pack",
                        f"event seq={event.seq}: receipt exceeds bound dossier authority",
                    )
                for excerpt in receipt.excerpts:
                    try:
                        payload = h.blobs.get(excerpt.excerpt_ref)
                    except Exception as error:  # noqa: BLE001
                        fail("dossier-pack", f"event seq={event.seq}: {error!r}")
                    else:
                        if (
                            len(payload) != excerpt.byte_count
                            or sha256_hex(payload) != excerpt.excerpt_sha256
                        ):
                            fail(
                                "dossier-pack",
                                f"event seq={event.seq}: excerpt identity differs",
                            )
    for event in events:
        work_order_id = (
            event.llm.work_order_id
            if event.llm is not None
            else None
        )
        active_conjecture_call = bool(
            event.llm is not None
            and event.inputs
            and event.inputs[0] == "conjecture-turn-call"
            and manifest is not None
            and manifest.schema_version in {4, 5, 6}
            and manifest.control_plane_policy is not None
            and manifest.control_plane_policy.mode in {
                "active_conjecture", "active_inquiry"
            }
        )
        if active_conjecture_call and work_order_id is None:
            fail(
                "workflow-call-pairing",
                f"event seq={event.seq}: active conjecture call is not bound to work",
            )
        if work_order_id is not None and work_order_id in h.workflow_state.transaction_work:
            provider_event = controller_v3["provider_events_by_seq"].get(int(event.seq))
            if provider_event is None or provider_event != event:
                fail(
                    "workflow-call-pairing",
                    f"event seq={event.seq}: transaction call is not its durable provider result",
                )
        elif (
            work_order_id is not None
            and work_order_id not in h.workflow_state.work_orders
        ):
            fail(
                "workflow-call-pairing",
                f"event seq={event.seq}: provider call names an unknown work order",
            )

    # 2. Incremental transitions == from-scratch walk.
    try:
        if h.transitions() != Harness(root, read_only=True).transitions():
            fail("transitions", "incremental transitions diverge from a fresh walk")
    except Exception as e:  # noqa: BLE001
        fail("transitions", repr(e))

    # 3. Time-travel at sampled seqs must not crash.
    seqs = [e.seq for e in events]
    for seq in sorted({seqs[i * (len(seqs) - 1) // 4] for i in range(5)} if seqs else []):
        try:
            Harness.at(root, seq)
        except Exception as e:  # noqa: BLE001
            fail("time-travel", f"Harness.at(seq={seq}): {e!r}")

    # 4. Accounting: meter total == sum of logged call tokens; every
    #    llm-bearing event's prompt/raw blobs exist.
    logged = 0
    profile_totals: dict[str, dict[str, int]] = {}
    authorized_controller_limits: dict[str, set[int]] = {}
    foreign_criticism_coverage: dict[str, set[str]] = {}

    def profile_row(profile: str) -> dict[str, int]:
        return profile_totals.setdefault(
            profile,
            {
                "calls": 0,
                "attempts": 0,
                "repair_attempts": 0,
                "tokens": 0,
                "traced_calls": 0,
                "first_pass_valid": 0,
                "eventual_valid": 0,
                "schema_exhausted": 0,
                "transport_dropped": 0,
                "usage_unknown_attempts": 0,
                "provider_transport_attempts": 0,
            },
        )

    def validate_school_route(event) -> None:
        call = event.llm
        receipt = getattr(call, "school_route", None) if call is not None else None
        if receipt is None and event.rule.value == "Conj":
            source_refs = [
                value
                for value in event.inputs
                if value.startswith("conjecture-call:")
            ]
            if len(source_refs) == 1:
                try:
                    source_seq = int(source_refs[0].removeprefix("conjecture-call:"))
                except ValueError:
                    source_seq = -1
                source = controller_v3["provider_events_by_seq"].get(source_seq)
                if source is None:
                    source = next(
                        (candidate for candidate in events if candidate.seq == source_seq),
                        None,
                    )
                controller_v3_source = (
                    source is not None
                    and source is controller_v3["provider_events_by_seq"].get(source_seq)
                )
                active_source = (
                    source is not None
                    and len(source.inputs) >= 3
                    and source.inputs[0] == "conjecture-turn-call"
                    and manifest is not None
                    and source.inputs[2] == f"manifest:{manifest.sha256}"
                )
                shadow_source = (
                    source is not None
                    and len(source.inputs) >= 2
                    and source.inputs[0] == "workflow-conjecture-call"
                    and getattr(source.llm, "work_order_id", None) is not None
                )
                if (
                    source is not None
                    and source.seq < event.seq
                    and source.llm is not None
                    and event.inputs
                    and (
                        controller_v3_source
                        or (
                            source.inputs[1] == event.inputs[0]
                            and (active_source or shadow_source)
                        )
                    )
                ):
                    call = source.llm
                    receipt = source.llm.school_route
        output_schools = (
            {
                artifact.provenance.school
                for output in event.outputs
                if (artifact := h.state.artifacts.get(output)) is not None
                and artifact.provenance.school is not None
            }
            if event.rule.value == "Conj"
            else set()
        )
        tagged_schools = (
            {
                value.removeprefix("school:")
                for value in event.inputs
                if value.startswith("school:")
            }
            if event.inputs and event.inputs[0] == "conj-noregister"
            else set()
        )
        expected_school = output_schools | tagged_schools

        mini_semantic_lineage = bool(
            manifest is not None
            and manifest.engine_profile == "mini"
            and expected_school
            and all(
                not (
                    value.startswith("school-")
                    and value.removeprefix("school-").isdigit()
                )
                for value in expected_school
            )
        )
        if (
            manifest is not None
            and manifest.schema_version in {4, 5, 6}
            and expected_school
            and not mini_semantic_lineage
        ):
            if len(expected_school) != 1:
                fail(
                    "school-route",
                    f"event seq={event.seq}: one call records multiple schools "
                    f"{sorted(expected_school)!r}",
                )
            if receipt is None:
                fail(
                    "school-route",
                    f"event seq={event.seq}: school-conditioned call has no route receipt",
                )
            elif receipt.school_id not in expected_school:
                fail(
                    "school-route",
                    f"event seq={event.seq}: receipt school={receipt.school_id!r}, "
                    f"event schools={sorted(expected_school)!r}",
                )

        if receipt is None:
            return
        if manifest is None or manifest.schema_version not in {4, 5, 6}:
            fail(
                "school-route",
                f"event seq={event.seq}: school route receipt requires a v4 manifest",
            )
            return
        control = manifest.control_plane_policy
        if control is None:
            fail("school-route", f"event seq={event.seq}: v4 control policy is missing")
            return
        engine_data = json.loads(manifest.engine_config_json)
        roster = {
            f"school-{index}"
            for index in range(int(engine_data.get("N_SCHOOLS", 0)))
        }
        if receipt.school_id not in roster:
            fail(
                "school-route",
                f"event seq={event.seq}: receipt school is outside manifest roster",
            )
            return
        if receipt.role not in {"conjecturer", "argumentative_critic"}:
            fail(
                "school-route",
                f"event seq={event.seq}: unsupported school role {receipt.role!r}",
            )
            return
        routes = manifest.roles.get(receipt.role, ())
        expected_seat = 0
        expected_endpoint = None
        if receipt.role == "argumentative_critic":
            criticism_policy = manifest.criticism_policy
            if criticism_policy is None:
                fail(
                    "school-route",
                    f"event seq={event.seq}: critic route has no criticism policy",
                )
                return
            matches = [
                binding
                for binding in criticism_policy.bindings
                if binding.school_id == receipt.school_id
                and binding.role == receipt.role
            ]
            if len(matches) != 1:
                fail(
                    "school-route",
                    f"event seq={event.seq}: receipt has no unique manifest binding",
                )
                return
            expected_seat = matches[0].seat
            expected_endpoint = matches[0].endpoint_id
        else:
            school_policy = control.school_execution
            if school_policy.mode == "route_bound":
                matches = [
                    binding
                    for binding in school_policy.bindings
                    if binding.school_id == receipt.school_id
                    and binding.role == receipt.role
                ]
                if len(matches) != 1:
                    fail(
                        "school-route",
                        f"event seq={event.seq}: receipt has no unique manifest binding",
                    )
                    return
                expected_seat = matches[0].seat
                expected_endpoint = matches[0].endpoint_id
        if receipt.seat != expected_seat:
            fail(
                "school-route",
                f"event seq={event.seq}: receipt seat={receipt.seat}, "
                f"policy seat={expected_seat}",
            )
            return
        if receipt.seat >= len(routes):
            fail(
                "school-route",
                f"event seq={event.seq}: receipt seat is outside manifest routes",
            )
            return
        route = routes[receipt.seat]
        if expected_endpoint is not None and receipt.endpoint_id != expected_endpoint:
            fail(
                "school-route",
                f"event seq={event.seq}: receipt endpoint differs from binding",
            )
        if receipt.endpoint_id != route.endpoint_id:
            fail(
                "school-route",
                f"event seq={event.seq}: receipt endpoint differs from manifest route",
            )
        if receipt.route_sha256 != route_fingerprint(route):
            fail(
                "school-route",
                f"event seq={event.seq}: receipt route hash differs from manifest route",
            )

    def validate_conjecture_context(event) -> None:
        """Prove the exact advisory bytes and their append-only provenance."""

        call = event.llm
        receipt = (
            getattr(call, "conjecture_context", None) if call is not None else None
        )
        if receipt is None:
            return
        prefix = f"event seq={event.seq}"
        if manifest is None or manifest.schema_version not in {4, 5, 6}:
            fail(
                "conjecture-context",
                f"{prefix}: advisory context receipt requires a v4 manifest",
            )
        else:
            control = manifest.control_plane_policy
            if (
                control is None
                or control.mode not in {
                    "shadow", "active_conjecture", "active_inquiry"
                }
                or control.conjecture_context.mode == "disabled"
            ):
                fail(
                    "conjecture-context",
                    f"{prefix}: manifest does not authorize conjecture context",
                )
            if receipt.manifest_digest != manifest.sha256:
                fail(
                    "conjecture-context",
                    f"{prefix}: receipt manifest digest does not match the run",
                )

        if receipt.formal_fence_seq >= event.seq:
            fail(
                "conjecture-context",
                f"{prefix}: context fence does not precede the call event",
            )
        route_receipt = getattr(call, "school_route", None)
        if receipt.school_id is not None and route_receipt is None:
            fail(
                "conjecture-context",
                f"{prefix}: school context has no matching route receipt",
            )
        if receipt.expansion_decision_ref is not None:
            decisions = [
                candidate
                for candidate in events
                if candidate.conjecture_turn is not None
                and candidate.conjecture_turn.decision_id
                == receipt.expansion_decision_ref
            ]
            if len(decisions) != 1 or decisions[0].seq >= event.seq:
                fail(
                    "conjecture-context",
                    f"{prefix}: expanded context has no unique preceding decision",
                )
            else:
                decision = decisions[0].conjecture_turn
                if (
                    decision.action.value != "context_granted"
                    or decision.request_hash != receipt.expansion_request_hash
                    or decision.expansion_index != receipt.expansion_index
                    or decision.prior_selection_receipt_ref
                    != receipt.prior_selection_receipt_ref
                ):
                    fail(
                        "conjecture-context",
                        f"{prefix}: expansion lineage differs from its grant",
                    )
        try:
            fenced = Harness.at(root, receipt.formal_fence_seq)
            if receipt.problem_id not in fenced.state.problems:
                fail(
                    "conjecture-context",
                    f"{prefix}: problem was absent at the formal fence",
                )
        except Exception as error:  # noqa: BLE001 - malformed evidence is a finding
            fail(
                "conjecture-context",
                f"{prefix}: cannot reconstruct formal fence: {error!r}",
            )

        selection = h.scratch_state.attention_receipts.get(
            receipt.selection_receipt_ref
        )
        context = h.scratch_state.advisory_contexts.get(
            receipt.advisory_context_ref
        )
        if selection is None:
            fail(
                "conjecture-context",
                f"{prefix}: selection receipt is absent from scratch replay",
            )
        elif selection.state_seq != receipt.scratch_fence_seq:
            fail(
                "conjecture-context",
                f"{prefix}: selection receipt names another scratch fence",
            )
        if context is None:
            fail(
                "conjecture-context",
                f"{prefix}: advisory context is absent from scratch replay",
            )
        elif context.retrieval_receipt != receipt.selection_receipt_ref:
            fail(
                "conjecture-context",
                f"{prefix}: advisory context names another selection receipt",
            )
        elif selection is not None and [block.id for block in context.blocks] != list(
            selection.final_order
        ):
            fail(
                "conjecture-context",
                f"{prefix}: advisory blocks differ from the selected order",
            )

        selection_events = [
            candidate
            for candidate in events
            if candidate.scratch is not None
            and receipt.selection_receipt_ref in candidate.outputs
        ]
        context_events = [
            candidate
            for candidate in events
            if candidate.scratch is not None
            and receipt.advisory_context_ref in candidate.outputs
        ]
        if len(selection_events) != 1 or selection_events[0].seq >= event.seq:
            fail(
                "conjecture-context",
                f"{prefix}: selection must have one preceding scratch event",
            )
        elif selection_events[0].scratch.context_ref != receipt.render_receipt_ref:
            fail(
                "conjecture-context",
                f"{prefix}: selection event does not bind the render receipt blob",
            )
        if len(context_events) != 1 or context_events[0].seq >= event.seq:
            fail(
                "conjecture-context",
                f"{prefix}: advisory context must have one preceding scratch event",
            )

        try:
            from deepreason.scratch.render import ScratchRenderReceiptV1

            render = ScratchRenderReceiptV1.model_validate_json(
                h.blobs.get(receipt.render_receipt_ref)
            )
            if render.state_seq != receipt.scratch_fence_seq:
                fail(
                    "conjecture-context",
                    f"{prefix}: render receipt names another scratch fence",
                )
            if render.attention_receipt != receipt.selection_receipt_ref:
                fail(
                    "conjecture-context",
                    f"{prefix}: render receipt names another selection",
                )
            if selection is not None and list(render.block_handles.values()) != list(
                selection.final_order
            ):
                fail(
                    "conjecture-context",
                    f"{prefix}: render handles differ from the selected blocks",
                )
        except (KeyError, TypeError, ValueError) as error:
            fail(
                "conjecture-context",
                f"{prefix}: invalid render receipt blob: {error!r}",
            )

        try:
            rendered = h.blobs.get(receipt.rendered_context_ref)
            initial_prompt = h.blobs.get(call.attempt_trace[0].prompt_ref)
            if initial_prompt.count(rendered) != 1:
                fail(
                    "conjecture-context",
                    f"{prefix}: initial prompt does not contain exact context once",
                )
            marker, separator, payload_bytes = rendered.partition(b"\n")
            payload = json.loads(payload_bytes) if separator else None
            from deepreason.scratch.contracts import SCRATCH_CONTRACT_INSTRUCTIONS

            if (
                marker != b"SCRATCH_ADVISORY_CONTEXT_V1"
                or not isinstance(payload, dict)
                or payload.get("warning") != SCRATCH_CONTRACT_INSTRUCTIONS
                or context is None
                or context.warning != SCRATCH_CONTRACT_INSTRUCTIONS
            ):
                fail(
                    "conjecture-context",
                    f"{prefix}: rendered advisory warning or envelope differs",
                )
        except (IndexError, KeyError, TypeError, UnicodeError, ValueError) as error:
            fail(
                "conjecture-context",
                f"{prefix}: rendered context evidence is incomplete: {error!r}",
            )

    def validate_conjecture_turn(event) -> None:
        payload = event.conjecture_turn
        if payload is None:
            return
        prefix = f"event seq={event.seq}"
        control = None
        context_policy = None
        if manifest is None or manifest.schema_version not in {4, 5, 6}:
            fail(
                "conjecture-turn",
                f"{prefix}: typed turn evidence requires a v4 manifest",
            )
        else:
            control = manifest.control_plane_policy
            if (
                control is None
                or control.mode not in {"active_conjecture", "active_inquiry"}
                or control.contract_versions.conjecturer_turn_contract
                not in {
                    "conjecturer.turn.v4",
                    "conjecturer.turn.v5",
                    "conjecturer.turn.v6",
                }
            ):
                fail(
                    "conjecture-turn",
                    f"{prefix}: manifest does not authorize v4 conjecture turns",
                )
            else:
                context_policy = control.conjecture_context
            if payload.manifest_digest != manifest.sha256:
                fail(
                    "conjecture-turn",
                    f"{prefix}: payload manifest digest differs from the run",
                )

        source = next(
            (candidate for candidate in events if candidate.seq == payload.source_call_seq),
            None,
        )
        source_call = source.llm if source is not None else None
        source_context = (
            source_call.conjecture_context if source_call is not None else None
        )
        if (
            source is None
            or source.seq >= event.seq
            or source_call is None
            or source_call.role != "conjecturer"
        ):
            fail(
                "conjecture-turn",
                f"{prefix}: source does not name one preceding conjecturer call",
            )
        else:
            expected_inputs = [
                "conjecture-turn-call",
                payload.problem_id,
                f"manifest:{payload.manifest_digest}",
            ]
            if payload.school_id is not None:
                expected_inputs.append(f"school:{payload.school_id}")
            if list(source.inputs) != expected_inputs:
                fail(
                    "conjecture-turn",
                    f"{prefix}: source call names another work item or manifest",
                )
            if any(
                attempt.contract_id
                != control.contract_versions.conjecturer_turn_contract
                for attempt in source_call.attempt_trace
            ):
                fail(
                    "conjecture-turn",
                    f"{prefix}: source call used another wire contract",
                )
            if source_call.work_order_id is None:
                fail(
                    "conjecture-turn",
                    f"{prefix}: source call is not bound to an active work order",
                )
            route_school = (
                source_call.school_route.school_id
                if source_call.school_route is not None
                else None
            )
            if route_school != payload.school_id:
                fail(
                    "conjecture-turn",
                    f"{prefix}: turn school differs from its source route",
                )
            source_selection = (
                source_context.selection_receipt_ref
                if source_context is not None
                else None
            )
            if source_selection != payload.prior_selection_receipt_ref:
                fail(
                    "conjecture-turn",
                    f"{prefix}: turn prior selection differs from its source context",
                )
            if source_context is not None and (
                source_context.manifest_digest != payload.manifest_digest
                or source_context.problem_id != payload.problem_id
                or source_context.school_id != payload.school_id
            ):
                fail(
                    "conjecture-turn",
                    f"{prefix}: source context belongs to another work item",
                )

        if context_policy is not None and (
            payload.maximum_expansions
            != context_policy.max_context_expansion_requests
        ):
            fail(
                "conjecture-turn",
                f"{prefix}: expansion ceiling differs from the manifest",
            )

        request = None
        if payload.request_ref is not None:
            try:
                from deepreason.conjecture_turn import ContextRequestV1

                request = ContextRequestV1.model_validate_json(
                    h.blobs.get(payload.request_ref)
                )
                if request.request_hash != payload.request_hash:
                    fail(
                        "conjecture-turn",
                        f"{prefix}: request hash differs from its blob",
                    )
            except (KeyError, TypeError, ValueError) as error:
                fail(
                    "conjecture-turn",
                    f"{prefix}: invalid request evidence: {error!r}",
                )
        if payload.abstention_ref is not None:
            try:
                from deepreason.conjecture_turn import ConjectureAbstentionV1

                abstention = ConjectureAbstentionV1.model_validate_json(
                    h.blobs.get(payload.abstention_ref)
                )
                if abstention.abstention_hash != payload.abstention_hash:
                    fail(
                        "conjecture-turn",
                        f"{prefix}: abstention hash differs from its blob",
                    )
            except (KeyError, TypeError, ValueError) as error:
                fail(
                    "conjecture-turn",
                    f"{prefix}: invalid abstention evidence: {error!r}",
                )

        # The typed turn is semantic evidence emitted after the code-authored
        # authority transition.  Correlate both surfaces so deleting,
        # reordering, or retargeting either side cannot leave a plausible but
        # unauthorized context decision behind.
        work_order_id = (
            source_call.work_order_id if source_call is not None else None
        )
        if work_order_id is not None:
            from deepreason.workflow.models import TransitionKind

            work_decisions = [
                decision
                for decision in h.workflow_state.decisions.values()
                if decision.work_order_id == work_order_id
            ]
            decision_seq = {
                control_event.control.decision_ref: control_event.seq
                for control_event in control_events
                if control_event.control is not None
            }
            proposals = [
                receipt
                for receipt in h.workflow_state.proposal_receipts.values()
                if receipt.work_order_id == work_order_id
                and receipt.source_call_seq == payload.source_call_seq
            ]
            if len(proposals) != 1:
                fail(
                    "conjecture-turn-control",
                    f"{prefix}: turn must have one durable proposal receipt",
                )
            else:
                proposal = proposals[0]
                if (
                    proposal.context_request_hash != payload.request_hash
                    or proposal.context_request_ref != payload.request_ref
                    or proposal.abstention_hash != payload.abstention_hash
                    or proposal.abstention_ref != payload.abstention_ref
                ):
                    fail(
                        "conjecture-turn-control",
                        f"{prefix}: turn evidence differs from its proposal receipt",
                    )

            proposal_decisions = [
                decision
                for decision in work_decisions
                if decision.transition_kind == TransitionKind.PROPOSAL_RECEIVED
            ]
            if len(proposal_decisions) != 1:
                fail(
                    "conjecture-turn-control",
                    f"{prefix}: turn must follow one proposal transition",
                )
            terminal_kinds = {
                TransitionKind.PROPOSAL_ADMITTED,
                TransitionKind.PROPOSAL_REJECTED,
                TransitionKind.PROPOSAL_DEDUPLICATED,
                TransitionKind.WORK_FINISHED,
            }
            terminal_decisions = [
                decision
                for decision in work_decisions
                if decision.transition_kind in terminal_kinds
            ]
            if len(terminal_decisions) != 1:
                fail(
                    "conjecture-turn-control",
                    f"{prefix}: turn must follow one terminal work transition",
                )

            if payload.request_ref is not None:
                request_decisions = [
                    decision
                    for decision in work_decisions
                    if decision.transition_kind == TransitionKind.CONTEXT_REQUESTED
                ]
                expected_kind = (
                    TransitionKind.CONTEXT_GRANTED
                    if payload.action.value == "context_granted"
                    else TransitionKind.CONTEXT_DENIED
                )
                context_decisions = [
                    decision
                    for decision in work_decisions
                    if decision.transition_kind == expected_kind
                ]
                if (
                    len(request_decisions) != 1
                    or request_decisions[0].trigger_ref != payload.request_hash
                ):
                    fail(
                        "conjecture-turn-control",
                        f"{prefix}: request lacks its exact authority transition",
                    )
                if (
                    len(context_decisions) != 1
                    or context_decisions[0].trigger_ref != payload.decision_id
                ):
                    fail(
                        "conjecture-turn-control",
                        f"{prefix}: context outcome lacks its exact authority transition",
                    )
                ordered = [
                    payload.source_call_seq,
                    *(
                        [decision_seq.get(proposal_decisions[0].id, -1)]
                        if len(proposal_decisions) == 1
                        else []
                    ),
                    *(
                        [decision_seq.get(request_decisions[0].id, -1)]
                        if len(request_decisions) == 1
                        else []
                    ),
                    *(
                        [decision_seq.get(context_decisions[0].id, -1)]
                        if len(context_decisions) == 1
                        else []
                    ),
                    *(
                        [decision_seq.get(terminal_decisions[0].id, -1)]
                        if len(terminal_decisions) == 1
                        else []
                    ),
                    event.seq,
                ]
                if len(ordered) != 6 or any(
                    left >= right for left, right in zip(ordered, ordered[1:])
                ):
                    fail(
                        "conjecture-turn-control",
                        f"{prefix}: authority transitions do not precede semantic evidence",
                    )
            elif len(proposal_decisions) == 1 and len(terminal_decisions) == 1:
                ordered = (
                    payload.source_call_seq,
                    decision_seq.get(proposal_decisions[0].id, -1),
                    decision_seq.get(terminal_decisions[0].id, -1),
                    event.seq,
                )
                if any(
                    left >= right for left, right in zip(ordered, ordered[1:])
                ):
                    fail(
                        "conjecture-turn-control",
                        f"{prefix}: authority transitions do not precede semantic evidence",
                    )

        action = payload.action.value
        desired = (
            {channel.value for channel in request.desired_retrieval_channels}
            if request is not None
            else set()
        )
        permitted = (
            set(context_policy.permitted_retrieval_channels)
            if context_policy is not None
            else set()
        )
        if action == "context_granted":
            if (
                context_policy is None
                or context_policy.mode != "harness_plus_model_request"
                or desired - permitted
                or not 1 <= payload.expansion_index <= payload.maximum_expansions
            ):
                fail(
                    "conjecture-turn",
                    f"{prefix}: context grant exceeds its frozen capability",
                )
            children = [
                candidate
                for candidate in events
                if candidate.seq > event.seq
                and candidate.llm is not None
                and candidate.llm.conjecture_context is not None
                and candidate.llm.conjecture_context.expansion_decision_ref
                == payload.decision_id
            ]
            if len(children) != 1:
                fail(
                    "conjecture-turn",
                    f"{prefix}: grant must have one expanded follow-up call",
                )
            else:
                child_call = children[0].llm
                child = child_call.conjecture_context
                if (
                    child.expansion_request_hash != payload.request_hash
                    or child.expansion_index != payload.expansion_index
                    or child.prior_selection_receipt_ref
                    != payload.prior_selection_receipt_ref
                    or child.manifest_digest != payload.manifest_digest
                    or child.problem_id != payload.problem_id
                    or child.school_id != payload.school_id
                ):
                    fail(
                        "conjecture-turn",
                        f"{prefix}: follow-up receipt differs from the grant",
                    )
                if child_call.school_route != source_call.school_route:
                    fail(
                        "conjecture-turn",
                        f"{prefix}: follow-up call changed the frozen route lease",
                    )
                selection = h.scratch_state.attention_receipts.get(
                    child.selection_receipt_ref
                )
                prior = (
                    h.scratch_state.attention_receipts.get(
                        child.prior_selection_receipt_ref
                    )
                    if child.prior_selection_receipt_ref is not None
                    else None
                )
                prior_order = list(prior.final_order) if prior is not None else []
                if selection is not None:
                    order = list(selection.final_order)
                    added = [item for item in order if item not in set(prior_order)]
                    root_order = list(child.root_block_refs or ())
                    expected_root = (
                        list(source_context.root_block_refs)
                        if source_context is not None
                        and source_context.root_block_refs is not None
                        else prior_order
                    )
                    cumulative_added = [
                        item for item in order if item not in set(root_order)
                    ]
                    if (
                        order[: len(prior_order)] != prior_order
                        or added != list(child.added_block_refs or ())
                        or child.root_block_refs is None
                        or root_order != expected_root
                        or order[: len(root_order)] != root_order
                        or (
                            context_policy is not None
                            and len(cumulative_added)
                            > context_policy.max_extra_blocks
                        )
                    ):
                        fail(
                            "conjecture-turn",
                            f"{prefix}: expanded selection exceeds or loses context",
                        )
        elif action == "context_exhausted":
            if payload.expansion_index != payload.maximum_expansions:
                fail(
                    "conjecture-turn",
                    f"{prefix}: exhausted request is below its frozen ceiling",
                )
        elif action == "context_denied" and payload.reason_code == "channel_not_permitted":
            if not (desired - permitted):
                fail(
                    "conjecture-turn",
                    f"{prefix}: channel denial has no forbidden channel",
                )
        if action != "context_granted" and any(
            candidate.seq > event.seq
            and candidate.llm is not None
            and candidate.llm.conjecture_context is not None
            and candidate.llm.conjecture_context.expansion_decision_ref
            == payload.decision_id
            for candidate in events
        ):
            fail(
                "conjecture-turn",
                f"{prefix}: a non-grant decision authorized expanded context",
            )

    def validate_foreign_criticism_coverage(event) -> None:
        if (
            event.rule.value != "Measure"
            or not event.inputs
            or event.inputs[0] != "foreign-criticism-coverage.v1"
        ):
            return
        prefix = f"event seq={event.seq}"
        if len(event.inputs) != 6:
            fail(
                "foreign-criticism",
                f"{prefix}: coverage receipt has a non-canonical shape",
            )
            return
        target_id = event.inputs[1]
        owner_value, critic_value, source_value, route_value = event.inputs[2:]
        if not (
            owner_value.startswith("owner:")
            and critic_value.startswith("critic:")
            and source_value.startswith("source:")
            and route_value.startswith("route:")
        ):
            fail(
                "foreign-criticism",
                f"{prefix}: coverage receipt fields are not canonical",
            )
            return
        owner_school_id = owner_value.removeprefix("owner:")
        critic_school_id = critic_value.removeprefix("critic:")
        route_sha256 = route_value.removeprefix("route:")
        try:
            source_seq = int(source_value.removeprefix("source:"))
        except ValueError:
            fail(
                "foreign-criticism",
                f"{prefix}: source call sequence is not an integer",
            )
            return

        policy = (
            manifest.criticism_policy
            if manifest is not None and manifest.schema_version in {4, 5, 6}
            else None
        )
        if policy is None:
            fail(
                "foreign-criticism",
                f"{prefix}: coverage receipt has no active v4 criticism policy",
            )
            return
        target = h.state.artifacts.get(target_id)
        provenance = target.provenance if target is not None else None
        if (
            target is None
            or provenance is None
            or provenance.school != owner_school_id
            or provenance.role not in {"conjecturer", "synthesizer"}
        ):
            fail(
                "foreign-criticism",
                f"{prefix}: target owner differs from canonical artifact provenance",
            )
        if critic_school_id == owner_school_id:
            fail(
                "foreign-criticism",
                f"{prefix}: self-criticism cannot satisfy foreign coverage",
            )

        source = next((item for item in events if item.seq == source_seq), None)
        call = source.llm if source is not None else None
        receipt = call.school_route if call is not None else None
        if (
            source is None
            or source.seq >= event.seq
            or call is None
            or call.role != "argumentative_critic"
            or receipt is None
            or receipt.school_id != critic_school_id
            or receipt.route_sha256 != route_sha256
        ):
            fail(
                "foreign-criticism",
                f"{prefix}: coverage does not reference one preceding routed critic call",
            )
            return
        matches = [
            binding
            for binding in policy.bindings
            if binding.school_id == critic_school_id
            and binding.role == "argumentative_critic"
        ]
        if (
            len(matches) != 1
            or matches[0].seat != receipt.seat
            or matches[0].endpoint_id != receipt.endpoint_id
        ):
            fail(
                "foreign-criticism",
                f"{prefix}: critic school differs from its manifest binding",
            )
            return
        covered = foreign_criticism_coverage.setdefault(target_id, set())
        if critic_school_id in covered:
            fail(
                "foreign-criticism",
                f"{prefix}: duplicate school does not add foreign coverage",
            )
            return
        covered.add(critic_school_id)

    compact_transition_seq_by_route_seat: dict[
        tuple[str, int, str, str], int
    ] = {}
    classification_by_route_seat = {}
    classification_event_seq = None
    if manifest is not None and manifest.schema_version == 6:
        classification = h.workflow_state.route_seat_model_classification
        binding = h.workflow_state.model_classification_binding
        classification_event_seq = h.workflow_state.model_classification_event_seq
        if classification is not None or binding is not None:
            try:
                if classification is None or binding is None:
                    raise ValueError("classification binding is incomplete")
                h.workflow_state._validate_model_classification(
                    manifest,
                    classification,
                )
                if (
                    classification_event_seq is None
                    or binding.classification_plan_ref != classification.id
                    or binding.manifest_digest != manifest.sha256
                    or binding.qualification_evidence_sha256
                    != classification.qualification_evidence_sha256
                ):
                    raise ValueError("classification binding differs from its plan")
                classification_by_route_seat = {
                    (
                        entry.role,
                        entry.seat,
                        entry.endpoint_id,
                        entry.route_sha256,
                    ): entry
                    for entry in classification.entries
                }
            except ValueError as error:
                fail("model-classification-authority", str(error))
        for item in h.workflow_state.transaction_work.values():
            prepared_seq = item.event_seqs[0] if item.event_seqs else None
            if manifest.route_seat_behavioral_capability_plan is not None and (
                classification_event_seq is None
                or prepared_seq is None
                or classification_event_seq >= prepared_seq
            ):
                fail(
                    "model-classification-authority",
                    f"work {item.preparation.id}: preparation precedes exact "
                    "route-seat classification authority",
                )
        for event in events:
            for object_id in event.outputs:
                try:
                    schema, value = h.objects.get(object_id)
                except (KeyError, ValueError):
                    continue
                if schema != "workflow-compact-recovery-transition-v1":
                    continue
                key = value.route_seat_key
                if key in compact_transition_seq_by_route_seat:
                    fail(
                        "attempt-profile-authority",
                        f"event seq={event.seq}: duplicate compact transition "
                        f"for {key[0]}[{key[1]}]",
                    )
                    continue
                compact_transition_seq_by_route_seat[key] = event.seq

    for e in events:
        validate_school_route(e)
        validate_conjecture_context(e)
        validate_conjecture_turn(e)
        validate_foreign_criticism_coverage(e)
        # Controller policies are harness-authored, attackable artifacts. A
        # value is transport-authorized only after its policy is appended;
        # later refutation may cause a revert but cannot erase that historical
        # request setting from the replay trace.
        for output in e.outputs if e.rule.value == "Refl" else ():
            artifact = h.state.artifacts.get(output)
            if (
                artifact is None
                or artifact.provenance.role.value != "controller"
                or not artifact.content_ref.startswith("inline:")
            ):
                continue
            try:
                body = json.loads(artifact.content_ref[len("inline:"):])
            except (TypeError, ValueError):
                continue
            knobs = body.get("knobs") if isinstance(body, dict) else None
            if not isinstance(knobs, dict):
                continue
            for knob, value in knobs.items():
                envelope = ENVELOPES.get(knob)
                if (
                    knob in GENERATOR_LEDGER
                    and type(value) is int
                    and envelope is not None
                    and envelope["min"] <= value <= envelope["max"]
                ):
                    authorized_controller_limits.setdefault(knob, set()).add(
                        value
                    )
        if e.llm is None:
            continue
        trace = list(e.llm.attempt_trace)
        fallback_profile = (
            manifest.model_profile if manifest is not None else "unprofiled"
        )
        profile = (
            str(trace[0].model_profile or fallback_profile)
            if trace
            else fallback_profile
        )
        profile_stats = profile_row(profile)
        profile_stats["calls"] += 1
        profile_stats["attempts"] += e.llm.attempts
        profile_stats["repair_attempts"] += max(0, e.llm.attempts - 1)
        profile_stats["tokens"] += e.llm.tokens
        logged += e.llm.tokens
        control_policy = (
            manifest.control_plane_policy
            if manifest is not None and manifest.schema_version in {4, 5, 6}
            else None
        )
        if (
            control_policy is not None
            and control_policy.mode in {"active_conjecture", "active_inquiry"}
            and e.inputs
            and e.inputs[0] == "conjecture-turn-call"
        ):
            if (
                e.llm.role != "conjecturer"
                or len(e.inputs) < 3
                or e.inputs[1] not in h.state.problems
                or e.inputs[2] != f"manifest:{manifest.sha256}"
                or any(
                    attempt.contract_id
                    != control_policy.contract_versions.conjecturer_turn_contract
                    for attempt in trace
                )
            ):
                fail(
                    "conjecture-turn-contract",
                    f"event seq={e.seq}: active turn escaped its bound v4 work item",
                )
        expected_outcome = _expected_call_outcome(
            e,
            legacy_failure_call_seqs,
            workflow_failure_call_seqs,
        )
        if trace:
            profile_stats["traced_calls"] += 1
            profile_stats["first_pass_valid"] += int(trace[0].valid)
            profile_stats["eventual_valid"] += int(
                any(attempt.valid for attempt in trace)
            )
            profile_stats["usage_unknown_attempts"] += sum(
                int(attempt.usage_unknown) for attempt in trace
            )
            profile_stats["provider_transport_attempts"] += sum(
                attempt.transport_attempts for attempt in trace
            )
            if not any(attempt.valid for attempt in trace):
                if any(attempt.usage_unknown for attempt in trace):
                    profile_stats["transport_dropped"] += 1
                else:
                    profile_stats["schema_exhausted"] += 1

            if len(trace) != e.llm.attempts:
                fail(
                    "attempt-trace",
                    f"event seq={e.seq}: trace has {len(trace)} entries but "
                    f"attempts={e.llm.attempts}",
                )
            trace_tokens = sum(attempt.tokens for attempt in trace)
            if trace_tokens != e.llm.tokens:
                fail(
                    "attempt-accounting",
                    f"event seq={e.seq}: trace tokens={trace_tokens} but "
                    f"call tokens={e.llm.tokens}",
                )
            valid_indexes = [
                index for index, attempt in enumerate(trace) if attempt.valid
            ]
            if (
                expected_outcome == ExpectedCallOutcome.LEGACY_DROPPED
                and valid_indexes
            ):
                fail(
                    "attempt-validity",
                    f"event seq={e.seq}: dropped call contains a valid attempt",
                )
            elif (
                expected_outcome == ExpectedCallOutcome.FAILURE_REQUIRED
                and valid_indexes
            ):
                fail(
                    "attempt-validity",
                    f"event seq={e.seq}: failed call must contain no valid "
                    f"attempt, got {valid_indexes}",
                )
            elif (
                expected_outcome == ExpectedCallOutcome.SUCCESS_REQUIRED
                and valid_indexes != [len(trace) - 1]
            ):
                fail(
                    "attempt-validity",
                    f"event seq={e.seq}: successful call must have one final valid "
                    f"attempt, got {valid_indexes}",
                )
        elif expected_outcome == ExpectedCallOutcome.FAILURE_REQUIRED:
            fail(
                "attempt-trace",
                f"event seq={e.seq}: typed failed LLM call has no attempt trace",
            )
        elif manifest is not None:
            # Historical records remain readable because attempt_trace has a
            # default, but a manifest-bound run without total attempt evidence
            # cannot substantiate replay/accounting claims.
            fail(
                "attempt-trace",
                f"event seq={e.seq}: manifest-bound LLM call has no attempt trace",
            )

        prompt_payload = None
        empty_raw_allowed = bool(trace and trace[-1].usage_unknown)
        for ref, kind in ((e.llm.prompt_ref, "prompt"), (e.llm.raw_ref, "raw")):
            if not ref:
                if kind == "raw" and empty_raw_allowed:
                    continue
                fail("blobs", f"event seq={e.seq}: {kind} blob reference is empty")
                continue
            try:
                payload = h.blobs.get(ref)
                if kind == "prompt":
                    prompt_payload = payload
            except KeyError:
                fail("blobs", f"event seq={e.seq}: {kind} blob {ref[:12]} missing")

        inspect_attempts = (
            manifest is not None
            or expected_outcome == ExpectedCallOutcome.FAILURE_REQUIRED
        )
        if inspect_attempts:
            for index, attempt in enumerate(trace):
                prefix = f"event seq={e.seq} attempt={index}"
                if attempt.attempt != index:
                    fail(
                        "attempt-order",
                        f"{prefix}: recorded attempt index={attempt.attempt}",
                    )
                for ref, kind in (
                    (attempt.prompt_ref, "prompt"),
                    (attempt.raw_ref, "raw"),
                    (attempt.diagnostic_ref, "diagnostic"),
                ):
                    required = (
                        kind == "prompt"
                        or (kind == "raw" and not attempt.usage_unknown)
                        or (kind == "diagnostic" and not attempt.valid)
                    )
                    if not ref:
                        if required:
                            fail("attempt-blobs", f"{prefix}: missing {kind} ref")
                        continue
                    try:
                        h.blobs.get(ref)
                    except KeyError:
                        fail(
                            "attempt-blobs",
                            f"{prefix}: {kind} blob {ref[:12]} missing",
                        )
                if not attempt.contract_id:
                    fail("attempt-contract", f"{prefix}: contract_id is empty")

        if manifest is not None:
            routes = manifest.roles.get(e.llm.role, ())
            if not routes:
                fail(
                    "frozen-route",
                    f"event seq={e.seq}: role {e.llm.role!r} has no active manifest route",
                )
            elif not any(
                route.model_id == e.llm.model and route.base_url == e.llm.endpoint
                for route in routes
            ):
                fail(
                    "frozen-route",
                    f"event seq={e.seq}: {e.llm.role} used "
                    f"endpoint={e.llm.endpoint!r} model={e.llm.model!r} outside manifest",
                )

            for index, attempt in enumerate(trace):
                prefix = f"event seq={e.seq} attempt={index}"
                if attempt.seat < 0 or attempt.seat >= len(routes):
                    fail(
                        "attempt-route",
                        f"{prefix}: seat {attempt.seat} outside role route table",
                    )
                    continue
                route = routes[attempt.seat]
                if (
                    e.llm.model != route.model_id
                    or e.llm.endpoint != route.base_url
                ):
                    fail(
                        "attempt-route",
                        f"{prefix}: top-level call does not match recorded seat",
                    )
                if attempt.endpoint_id != route.endpoint_id:
                    fail(
                        "attempt-route",
                        f"{prefix}: endpoint_id={attempt.endpoint_id!r}, "
                        f"manifest={route.endpoint_id!r}",
                    )
                expected_route_hash = route_fingerprint(route)
                if attempt.route_sha256 != expected_route_hash:
                    fail(
                        "attempt-route",
                        f"{prefix}: route hash does not match manifest seat",
                    )
                if manifest.schema_version == 6:
                    try:
                        base_profile = resolve_route_seat_base_profile(
                            manifest,
                            role=e.llm.role,
                            seat=attempt.seat,
                            endpoint_id=route.endpoint_id,
                        )
                    except Exception as error:  # invalid authority is a finding
                        fail(
                            "attempt-profile-authority",
                            f"{prefix}: route-seat base profile cannot resolve: "
                            f"{error!r}",
                        )
                        continue
                    if manifest.route_seat_behavioral_capability_plan is not None:
                        try:
                            behavioral = resolve_route_seat_behavioral_capability(
                                manifest,
                                role=e.llm.role,
                                seat=attempt.seat,
                                endpoint_id=route.endpoint_id,
                                route_sha256=expected_route_hash,
                            )
                        except Exception as error:
                            fail(
                                "attempt-behavioral-authority",
                                f"{prefix}: route-seat behavioral capability "
                                f"cannot resolve: {error!r}",
                            )
                            continue
                        if attempt.contract_id not in {
                            grant.contract_id for grant in behavioral.contracts
                        }:
                            fail(
                                "attempt-behavioral-authority",
                                f"{prefix}: contract_id={attempt.contract_id!r} "
                                "is not authorized for the route seat",
                            )
                    if attempt.model_profile != base_profile:
                        fail(
                            "attempt-profile",
                            f"{prefix}: model_profile={attempt.model_profile!r}, "
                            f"route-seat base={base_profile!r}",
                        )
                    key = (
                        e.llm.role,
                        attempt.seat,
                        route.endpoint_id,
                        expected_route_hash,
                    )
                    transition_seq = compact_transition_seq_by_route_seat.get(
                        key
                    )
                    compact_authorized = (
                        manifest.compact_recovery_policy is not None
                        and base_profile in {"standard", "frontier"}
                        and transition_seq is not None
                        and transition_seq < e.seq
                    )
                    expected_transport = (
                        "compact" if compact_authorized else base_profile
                    )
                    if attempt.transport_profile != expected_transport:
                        fail(
                            "attempt-profile-authority",
                            f"{prefix}: transport_profile="
                            f"{attempt.transport_profile!r}, expected="
                            f"{expected_transport!r} for chronological "
                            "route-seat authority",
                        )
                    if manifest.route_seat_behavioral_capability_plan is not None:
                        selected = classification_by_route_seat.get(key)
                        if (
                            classification_event_seq is None
                            or classification_event_seq >= e.seq
                            or selected is None
                            or selected.selected_class
                            != "qualified_exact_behavior"
                            or attempt.contract_id
                            not in selected.authorized_contract_ids
                        ):
                            fail(
                                "attempt-model-classification",
                                f"{prefix}: attempt precedes or differs from exact "
                                "route-seat model classification authority",
                            )
                elif attempt.model_profile != manifest.model_profile:
                    fail(
                        "attempt-profile",
                        f"{prefix}: model_profile={attempt.model_profile!r}, "
                        f"manifest={manifest.model_profile!r}",
                    )
                if attempt.output_mechanism != route.output_mechanism:
                    fail(
                        "attempt-route",
                        f"{prefix}: output mechanism={attempt.output_mechanism!r}, "
                        f"manifest={route.output_mechanism!r}",
                    )
                # timeout_s is the marker for the extended trace. Historical
                # attempts default it to None and remain replayable; every new
                # adapter attempt records both limits. Values may differ from
                # the base route only after an earlier logged controller
                # policy authorized that exact process setting.
                if attempt.timeout_s is not None:
                    allowed_timeouts = {
                        route.timeout_s,
                        *authorized_controller_limits.get(
                            "timeout:transport", set()
                        ),
                    }
                    if attempt.timeout_s not in allowed_timeouts:
                        fail(
                            "attempt-limits",
                            f"{prefix}: timeout_s={attempt.timeout_s!r} was not "
                            "authorized by the route or a prior controller policy",
                        )
                    allowed_caps = {
                        route.max_tokens,
                        *authorized_controller_limits.get(
                            f"cap:{e.llm.role}", set()
                        ),
                    }
                    if attempt.max_tokens not in allowed_caps:
                        fail(
                            "attempt-limits",
                            f"{prefix}: max_tokens={attempt.max_tokens!r} was not "
                            "authorized by the route or a prior controller policy",
                        )

            # W4 has one initial generation and at most two repairs.  Attempts
            # and the final repair pack are operational evidence, not verdicts.
            if e.llm.attempts < 1 or e.llm.attempts > 3:
                fail(
                    "repair-metadata",
                    f"event seq={e.seq}: attempts={e.llm.attempts}, expected 1..3",
                )
            if e.llm.attempts > 1 and prompt_payload is not None:
                prompt_text = prompt_payload.decode("utf-8", errors="replace")
                if "DIAGNOSTIC:" not in prompt_text:
                    fail(
                        "repair-metadata",
                        f"event seq={e.seq}: repaired call lacks field diagnostic in final prompt",
                    )
                expected = (
                    "replacement JSON value"
                    if e.llm.attempts == 3
                    else "complete corrected JSON value"
                )
                if expected not in prompt_text:
                    fail(
                        "repair-metadata",
                        f"event seq={e.seq}: final repair prompt does not match attempts",
                    )

    criticism_policy = (
        manifest.criticism_policy
        if manifest is not None and manifest.schema_version in {4, 5, 6}
        else None
    )
    if criticism_policy is not None:
        for target_id, artifact in h.state.artifacts.items():
            provenance = artifact.provenance
            if (
                h.state.status.get(target_id) != Status.ACCEPTED
                or provenance is None
                or provenance.school is None
                or provenance.role not in {"conjecturer", "synthesizer"}
            ):
                continue
            covered = foreign_criticism_coverage.get(target_id, set())
            if len(covered) < criticism_policy.minimum_foreign_school_coverage:
                fail(
                    "foreign-criticism",
                    f"target {target_id} has {len(covered)} foreign schools; "
                    f"policy requires {criticism_policy.minimum_foreign_school_coverage}",
                )
    if meter_total is not None and logged != meter_total:
        fail("accounting",
             f"meter says {meter_total} tokens, log accounts for {logged} "
             f"(delta {meter_total - logged})")

    # 5. Graph well-formedness.
    for wid, w in h.warrants.items():
        if w.validity_node not in h.state.artifacts:
            fail("warrant-validity", f"{wid}: validity node not registered")
        if w.target not in h.state.artifacts:
            fail("warrant-target", f"{wid}: target not registered")
    for carrier, wid in h.state.carries:
        if carrier not in h.state.artifacts:
            fail("carry-carrier", f"{carrier}: carrier artifact not registered")
        if wid not in h.warrants:
            fail("carry-warrant", f"{wid}: carried warrant not registered")
    for x, t in h.state.att:
        if x not in h.state.artifacts or t not in h.state.artifacts:
            fail("att-endpoints", f"dangling attack edge ({x[:12]}, {t[:12]})")
    try:
        toposort(set(h.state.artifacts), build_dep(h.state.artifacts))
    except DependenceCycleError as e:
        fail("dep-dag", str(e))
    # Any Status enum member is legal — SUSPENDED/SUSPENDED_UNSUPPORTED
    # are the spec §4 support-cascade labels (dependent of a refuted
    # premise; orphaned != false), first produced live on runs/ab_needham.
    # The check guards against values outside the enum domain entirely.
    for aid, status in h.state.status.items():
        if not isinstance(status, Status):
            fail("status-domain", f"{aid[:12]}: {status}")
    for aid, pid in h.state.addr:
        if aid not in h.state.artifacts or pid not in h.state.problems:
            fail("addr", f"dangling addr pair ({aid[:12]}, {pid})")

    # 6. Event stream: seqs strictly consecutive from 0.
    if seqs != list(range(len(seqs))):
        fail("seq-stream", "event seqs are not consecutive from 0")

    # 7. Detection stays a total function over a messy log.
    try:
        from deepreason.capture.detection import raw_flags
        from deepreason.config import Config
        from deepreason.llm.embedder import HashingEmbedder

        raw_flags(h, HashingEmbedder(), Config())
    except Exception as e:  # noqa: BLE001
        fail("detection-total", repr(e))

    if not profile_totals:
        profile_row(
            manifest.model_profile if manifest is not None else "unprofiled"
        )
    canonical_profile_totals = {
        profile: profile_totals[profile] for profile in sorted(profile_totals)
    }
    model_execution = None
    if manifest is not None and manifest.schema_version == 6:
        try:
            from deepreason.application.models import derive_model_execution_summary
            from deepreason.runtime.terminal_authority import (
                derive_terminal_authority,
            )

            terminal_authority = derive_terminal_authority(
                root,
                manifest=manifest,
            )
            if terminal_authority.status == "invalid_incomplete":
                fail(
                    "terminal-authority",
                    "canonical terminal authority is invalid: "
                    f"{terminal_authority.detail_code}",
                )

            model_execution = derive_model_execution_summary(
                h,
                manifest,
                event_horizon_seq=(
                    terminal_authority.reasoning_event_horizon_seq
                    if terminal_authority.current_valid
                    else None
                ),
            ).model_dump(mode="json", by_alias=True)
        except Exception as error:  # replay disagreement is an invariant finding
            fail(
                "model-execution-summary",
                f"canonical model execution projection failed: {error!r}",
            )

    stats = {
        "events": len(events),
        "artifacts": len(h.state.artifacts),
        "problems": len(h.state.problems),
        "warrants": len(h.warrants),
        "accepted": sum(1 for s in h.state.status.values() if s == Status.ACCEPTED),
        "refuted": sum(1 for s in h.state.status.values() if s == Status.REFUTED),
        "logged_tokens": logged,
        "process": {
            "manifest_present": manifest_path.exists(),
            "manifest_sha256": manifest.sha256 if manifest is not None else None,
            "engine_profile": manifest.engine_profile if manifest is not None else None,
            "model_profile": manifest.model_profile if manifest is not None else None,
            "profile_totals": canonical_profile_totals,
            "model_execution": model_execution,
        },
        "gate_blocks": sum(1 for e in events for i in e.inputs if i.startswith("gate:")),
        "trial_blocks": sum(1 for e in events for i in e.inputs
                            if i.startswith("trial-blocked:")),
        "dropped_calls": sum(1 for e in events if "dropped-call" in e.inputs),
        "interventions": sum(1 for e in events for i in e.inputs
                             if i.startswith("intervention:")),
        "reseeds": sum(1 for e in events if e.rule.value == "Reseed"),
        "scratch_events": sum(1 for e in events if e.scratch is not None),
        "bridge_events": sum(1 for e in events if e.bridge is not None),
        "conjecture_turn_events": sum(
            1 for e in events if e.conjecture_turn is not None
        ),
        "control_events": len(control_events),
        "workflow_branches": len(h.workflow_state.branches),
        "outstanding_work_orders": list(
            h.workflow_state.outstanding_work_order_ids
        ),
        "workflow_process_digest": h.workflow_state.digest,
        "capability_events": len(capability_events),
        "capability_requests": h.capability_state.request_count,
        "capability_executions": h.capability_state.execution_count,
        "capability_consumptions": h.capability_state.consumption_count,
        "capability_process_digest": h.capability_state.digest,
        "max_problem_desc_len": max(
            (len(p.description) for p in h.state.problems.values()), default=0),
    }
    return {"violations": violations, "stats": stats}


def verify_root_report(root: Path, meter_total: int | None = None):
    """Return the dimensioned v2 report while preserving ``verify_root``.

    The import is intentionally local: the v2 adapter calls the legacy
    verifier and must not introduce an import cycle during harness startup.
    """

    from deepreason.verification.report import verify_root_report as _report

    return _report(root, meter_total=meter_total)
