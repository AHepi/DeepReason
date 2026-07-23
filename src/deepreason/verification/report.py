"""Dimensioned, read-only verification reports for run roots.

The historical :func:`deepreason.invariants.verify_root` API deliberately
remains unchanged.  This module translates its findings into independent
integrity, security, completion, epistemic, and operational channels and adds
terminal-state observations without writing to the inspected root.
"""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


VerificationChannel = Literal["integrity", "security", "completion", "epistemic", "operational"]


class VerificationFindingV2(BaseModel):
    """One bounded finding in exactly one verification dimension."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_: Literal["verification.finding.v2"] = Field("verification.finding.v2", alias="schema")
    channel: VerificationChannel
    check: str = Field(min_length=1, max_length=128)
    detail: str = Field(min_length=1, max_length=2_000)
    source: Literal["legacy", "terminal", "derived"] = "derived"


class VerificationReportV2(BaseModel):
    """A multi-dimensional audit whose validity is authority-only.

    ``valid`` intentionally does not mean complete, epistemically adequate, or
    operationally successful.  It means only that no integrity or security
    finding was observed.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_: Literal["verification.report.v2"] = Field("verification.report.v2", alias="schema")
    integrity: tuple[VerificationFindingV2, ...] = ()
    security: tuple[VerificationFindingV2, ...] = ()
    completion: tuple[VerificationFindingV2, ...] = ()
    epistemic: tuple[VerificationFindingV2, ...] = ()
    operational: tuple[VerificationFindingV2, ...] = ()
    stats: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _channels_match(self):
        for channel in (
            "integrity",
            "security",
            "completion",
            "epistemic",
            "operational",
        ):
            if any(item.channel != channel for item in getattr(self, channel)):
                raise ValueError(f"{channel} contains a differently classified finding")
        return self

    @computed_field(return_type=bool)
    @property
    def integrity_valid(self) -> bool:
        return not self.integrity

    @computed_field(return_type=bool)
    @property
    def security_valid(self) -> bool:
        return not self.security

    @computed_field(return_type=bool)
    @property
    def completion_satisfied(self) -> bool:
        return not self.completion

    @computed_field(return_type=bool)
    @property
    def epistemic_checks_passed(self) -> bool:
        return not self.epistemic

    @computed_field(return_type=bool)
    @property
    def operational_checks_passed(self) -> bool:
        return not self.operational

    @computed_field(return_type=bool)
    @property
    def valid(self) -> bool:
        return self.integrity_valid and self.security_valid

    def summary_payload(self) -> dict[str, Any]:
        """Return the bounded summary embedded by RunResult v2."""

        return {
            "schema": "verification.summary.v2",
            "valid": self.valid,
            "integrity_valid": self.integrity_valid,
            "security_valid": self.security_valid,
            "completion_satisfied": self.completion_satisfied,
            "epistemic_checks_passed": self.epistemic_checks_passed,
            "operational_checks_passed": self.operational_checks_passed,
            "finding_counts": {
                channel: len(getattr(self, channel))
                for channel in (
                    "integrity",
                    "security",
                    "completion",
                    "epistemic",
                    "operational",
                )
            },
        }


_SECURITY_CHECKS = frozenset(
    {
        "attempt-route",
        "capability-authority",
        "capability-compiled-authority",
        "capability-grant",
        "capability-work-order",
        "frozen-route",
        "school-route",
    }
)
_OPERATIONAL_CHECKS = frozenset({"detection-total", "time-travel"})
_EPISTEMIC_CHECKS = frozenset(
    {
        "bridge-epistemic",
        "bridge-grounding",
        "grounding-review",
    }
)


def _legacy_channel(check: str, detail: str) -> VerificationChannel:
    # A missing final coverage target is liveness debt.  A malformed or false
    # coverage receipt remains an integrity violation.
    if (
        check == "foreign-criticism"
        and detail.startswith("target ")
        and "policy requires" in detail
    ):
        return "completion"
    if check in _SECURITY_CHECKS:
        return "security"
    if check in _OPERATIONAL_CHECKS:
        return "operational"
    if check in _EPISTEMIC_CHECKS:
        return "epistemic"
    return "integrity"


def _finding(
    channel: VerificationChannel,
    check: str,
    detail: str,
    *,
    source: Literal["legacy", "terminal", "derived"],
) -> VerificationFindingV2:
    return VerificationFindingV2(
        channel=channel,
        check=str(check)[:128] or "unknown",
        detail=str(detail)[:2_000] or "unspecified finding",
        source=source,
    )


def _read_terminal(root: Path) -> tuple[dict[str, Any] | None, VerificationFindingV2 | None]:
    target = root / "run-result.json"
    try:
        observed = target.lstat()
    except FileNotFoundError:
        return None, None
    except OSError as error:
        return None, _finding(
            "integrity",
            "run-result",
            f"cannot inspect run-result.json: {error!r}",
            source="terminal",
        )
    if not stat.S_ISREG(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
        return None, _finding(
            "integrity",
            "run-result",
            "run-result.json is not a regular file",
            source="terminal",
        )
    if observed.st_size > 4 * 1024 * 1024:
        return None, _finding(
            "integrity",
            "run-result",
            "run-result.json exceeds the control-file bound",
            source="terminal",
        )
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, _finding(
            "integrity",
            "run-result",
            f"run-result.json is malformed: {error!r}",
            source="terminal",
        )
    if not isinstance(payload, dict):
        return None, _finding(
            "integrity",
            "run-result",
            "run-result.json must contain one object",
            source="terminal",
        )
    if payload.get("schema") not in {
        "deepreason-run-result-v1",
        "deepreason-run-result-v2",
    }:
        return None, _finding(
            "integrity",
            "run-result",
            "run-result.json has an unknown schema",
            source="terminal",
        )
    if payload.get("schema") == "deepreason-run-result-v2":
        from deepreason.application.models import RunResultV2

        try:
            payload = RunResultV2.model_validate(payload).model_dump(
                mode="json", by_alias=True, exclude_none=True
            )
        except ValueError as error:
            return None, _finding(
                "integrity",
                "run-result",
                f"RunResult v2 is internally inconsistent: {error!r}",
                source="terminal",
            )
    if payload.get("state") not in {"completed", "cancelled", "failed"}:
        return None, _finding(
            "integrity",
            "run-result",
            "run-result.json has a missing or unknown state",
            source="terminal",
        )
    return payload, None


def _terminal_findings(payload: dict[str, Any] | None) -> list[VerificationFindingV2]:
    if payload is None:
        return []
    findings: list[VerificationFindingV2] = []
    state = payload["state"]
    if state == "failed":
        error_type = str(payload.get("error_type") or "operational failure")
        detail = str(payload.get("error") or error_type)
        findings.append(
            _finding(
                "operational",
                "run-terminal",
                f"reasoning terminated as failed ({error_type}): {detail}",
                source="terminal",
            )
        )
    elif state == "cancelled":
        findings.append(
            _finding(
                "completion",
                "run-terminal",
                "reasoning was cancelled before ordinary completion",
                source="terminal",
            )
        )

    if payload.get("schema") == "deepreason-run-result-v2":
        summary = payload.get("verification")
        if isinstance(summary, dict):
            if summary.get("integrity_valid") is False:
                findings.append(
                    _finding(
                        "integrity",
                        "run-result-verification",
                        "RunResult v2 records an integrity-invalid verification summary",
                        source="terminal",
                    )
                )
            if summary.get("security_valid") is False:
                findings.append(
                    _finding(
                        "security",
                        "run-result-verification",
                        "RunResult v2 records a security-invalid verification summary",
                        source="terminal",
                    )
                )
            if summary.get("completion_satisfied") is False:
                findings.append(
                    _finding(
                        "completion",
                        "run-result-verification",
                        "RunResult v2 records outstanding completion debt",
                        source="terminal",
                    )
                )
            if summary.get("epistemic_checks_passed") is False:
                findings.append(
                    _finding(
                        "epistemic",
                        "run-result-verification",
                        "RunResult v2 records failed epistemic checks",
                        source="terminal",
                    )
                )
            if summary.get("operational_checks_passed") is False and state != "failed":
                findings.append(
                    _finding(
                        "operational",
                        "run-result-verification",
                        "RunResult v2 records failed operational checks",
                        source="terminal",
                    )
                )
    return findings


def _manifest_schema_version(root: Path) -> int | None:
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    target = root / MANIFEST_NAME
    if not target.exists():
        return None
    try:
        return load_run_manifest(target).schema_version
    except (OSError, ValueError):
        return None


def _model_execution_findings(
    root: Path,
    payload: dict[str, Any] | None,
    *,
    terminal_authority=None,
) -> tuple[VerificationFindingV2, ...]:
    """Compare stored v6 execution reporting with a fresh canonical replay."""

    if payload is None or payload.get("schema") != "deepreason-run-result-v2":
        return ()
    from deepreason.application.models import derive_model_execution_summary
    from deepreason.harness import Harness
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    try:
        manifest = load_run_manifest(root / MANIFEST_NAME)
    except Exception:
        # Manifest integrity is already reported by the legacy verifier.
        return ()
    if manifest.schema_version != 6:
        return ()
    stored = payload.get("model_execution")
    if manifest.terminal_commitment_policy is not None:
        if terminal_authority is None or not terminal_authority.current_valid:
            return ()
        if not isinstance(stored, dict):
            return ()
        try:
            harness = Harness(root, read_only=True)
            expected = derive_model_execution_summary(
                harness,
                manifest,
                event_horizon_seq=(
                    terminal_authority.reasoning_event_horizon_seq
                ),
            ).model_dump(mode="json", by_alias=True, exclude_none=True)
        except Exception as error:
            return (
                _finding(
                    "integrity",
                    "model-execution-summary",
                    f"model execution summary cannot be replayed: {error!r}"[:2_000],
                    source="derived",
                ),
            )
        if stored != expected:
            return (
                _finding(
                    "integrity",
                    "model-execution-summary",
                    "stored model execution summary differs from canonical replay",
                    source="terminal",
                ),
            )
        return ()
    if stored is None:
        # Gate 4R-A policy presence identifies manifests compiled after this
        # summary became part of the v6 terminal contract. Historical v6
        # results remain readable without retroactive claims.
        if manifest.compact_recovery_policy is None:
            return ()
        return (
            _finding(
                "integrity",
                "model-execution-summary",
                "new v6 run-result omits its replay-derived model execution summary",
                source="terminal",
            ),
        )
    stop = payload.get("stop")
    stop_seq = stop.get("event_seq") if isinstance(stop, dict) else None
    stored_horizon = (
        stored.get("event_horizon_seq") if isinstance(stored, dict) else None
    )
    if stored_horizon is not None and type(stop_seq) is not int:
        return (
            _finding(
                "integrity",
                "model-execution-summary",
                "stored model execution horizon has no typed run stop",
                source="terminal",
            ),
        )
    if stop_seq is not None and stored_horizon != stop_seq:
        return (
            _finding(
                "integrity",
                "model-execution-summary",
                "stored model execution horizon differs from the run stop",
                source="terminal",
            ),
        )
    try:
        harness = Harness(root, read_only=True)
    except Exception as error:
        return (
            _finding(
                "integrity",
                "model-execution-summary",
                f"durable execution history cannot be replayed: {error!r}"[:2_000],
                source="derived",
            ),
        )
    events = tuple(harness.log.read())
    lifecycle_stop_bound = any(
        decision.stop_event_seq is not None
        and decision.stop_record_digest is not None
        for decision in harness.workflow_state.lifecycle_decisions.values()
    )
    event_stop_bound = any(
        event.rule.value == "Measure"
        and list(event.inputs)[:1] == ["run-stop"]
        for event in events
    )
    try:
        (root / "run-stop.json").lstat()
        durable_stop_pointer = True
    except FileNotFoundError:
        durable_stop_pointer = False
    except OSError:
        # Inspection debt cannot make a current root look historical.
        durable_stop_pointer = True
    current_stop_authority_required = (
        payload.get("state") == "completed"
        and manifest.production_qualification_policy is not None
        and (lifecycle_stop_bound or event_stop_bound or durable_stop_pointer)
    )
    if current_stop_authority_required and type(stored_horizon) is not int:
        return (
            _finding(
                "integrity",
                "model-execution-summary",
                "current completed v6 run-result omits its authorised event horizon",
                source="terminal",
            ),
        )
    if current_stop_authority_required and type(stop_seq) is not int:
        return (
            _finding(
                "integrity",
                "model-execution-summary",
                "current completed v6 run-result omits its canonical stop receipt",
                source="terminal",
            ),
        )
    if stored_horizon is not None:
        from deepreason.canonical import canonical_json, sha256_hex
        from deepreason.ontology.event import Rule

        required_stop_fields = {
            "schema",
            "reason",
            "policy_digest",
            "metrics",
            "event_seq",
            "digest",
        }
        if not isinstance(stop, dict) or set(stop) != required_stop_fields:
            return (
                _finding(
                    "integrity",
                    "model-execution-summary",
                    "stored model execution horizon lacks its canonical stop receipt",
                    source="terminal",
                ),
            )
        unsigned_stop = {key: value for key, value in stop.items() if key != "digest"}
        stop_digest = stop.get("digest")
        if (
            stop.get("schema") != "deepreason-run-stop-v1"
            or not isinstance(stop_digest, str)
            or stop_digest != sha256_hex(canonical_json(unsigned_stop))
        ):
            return (
                _finding(
                    "integrity",
                    "model-execution-summary",
                    "stored model execution stop receipt is not canonical",
                    source="terminal",
                ),
            )
        history_path = root / "run-stops" / (
            f"{stored_horizon:012d}-{stop_digest}.json"
        )
        try:
            metadata = history_path.lstat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 64 * 1024:
                raise ValueError("unsafe stop receipt")
            history_bytes = history_path.read_bytes()
        except (OSError, ValueError) as error:
            return (
                _finding(
                    "integrity",
                    "model-execution-summary",
                    f"durable model execution stop receipt is unavailable: {error!r}"[:2_000],
                    source="terminal",
                ),
            )
        if history_bytes != canonical_json(stop) + b"\n":
            return (
                _finding(
                    "integrity",
                    "model-execution-summary",
                    "durable model execution stop receipt differs from the terminal",
                    source="terminal",
                ),
            )
        lifecycle_bound = any(
            decision.stop_event_seq == stored_horizon
            and decision.stop_record_digest == stop_digest
            for decision in harness.workflow_state.lifecycle_decisions.values()
        )
        post_horizon = tuple(
            event for event in events if event.seq > stored_horizon
        )
        bridge_work_ids = {
            work.preparation.id
            for work in harness.workflow_state.transaction_work.values()
            if isinstance(work.preparation.task_payload_value, dict)
            and work.preparation.task_payload_value.get("schema")
            in {"bridge.transaction-task.v2", "contract-decomposition-child.v1"}
            and isinstance(
                work.preparation.task_payload_value.get("execution_id"), str
            )
            and isinstance(
                work.preparation.task_payload_value.get("execution_snapshot_ref"),
                str,
            )
        }
        classification_schemas = {
            "workflow-route-seat-model-classification-plan-v1",
            "workflow-model-classification-binding-v1",
        }

        def _is_canonical_downstream_bridge_event(event) -> bool:
            if event.rule == Rule.BRIDGE:
                return True
            if event.rule != Rule.CONTROL:
                return False
            refs = set(event.inputs) | set(event.outputs)
            if refs & bridge_work_ids:
                return True
            output_schemas = set()
            for object_id in event.outputs:
                try:
                    schema, _record = harness.objects.get(object_id)
                except Exception:
                    return False
                output_schemas.add(schema)
            return bool(output_schemas) and output_schemas <= classification_schemas

        if current_stop_authority_required and any(
            not _is_canonical_downstream_bridge_event(event)
            for event in post_horizon
        ):
            return (
                _finding(
                    "integrity",
                    "model-execution-summary",
                    "durable execution history extends beyond the authorised stop horizon",
                    source="derived",
                ),
            )
        stop_event = next(
            (event for event in events if event.seq == stored_horizon),
            None,
        )
        metrics_json = json.dumps(stop.get("metrics"), sort_keys=True)
        measure_prefix = [
            "run-stop",
            stop.get("policy_digest"),
            metrics_json,
            stop.get("reason"),
        ]
        measure_bound = (
            stop_event is not None
            and stop_event.rule == Rule.MEASURE
            and list(stop_event.inputs)[:4] == measure_prefix
        )
        if not lifecycle_bound and not measure_bound:
            return (
                _finding(
                    "integrity",
                    "model-execution-summary",
                    "model execution stop receipt is not bound to durable history",
                    source="terminal",
                ),
            )
    try:
        expected = derive_model_execution_summary(
            harness,
            manifest,
            event_horizon_seq=stored_horizon,
        ).model_dump(mode="json", by_alias=True, exclude_none=True)
    except Exception as error:  # canonical replay disagreement is integrity debt
        return (
            _finding(
                "integrity",
                "model-execution-summary",
                f"model execution summary cannot be replayed: {error!r}"[:2_000],
                source="derived",
            ),
        )
    if stored != expected:
        return (
            _finding(
                "integrity",
                "model-execution-summary",
                "stored model execution summary differs from canonical replay",
                source="terminal",
            ),
        )
    return ()


def _terminal_authority_findings(
    root: Path,
    payload: dict[str, Any] | None,
    manifest,
):
    from deepreason.runtime.terminal_authority import derive_terminal_authority

    authority = derive_terminal_authority(
        root,
        manifest=manifest,
        result_payload=payload,
    )
    if authority.status == "historical_read_only":
        if getattr(manifest, "schema_version", None) != 6:
            return authority, ()
        return authority, (
            _finding(
                "operational",
                "terminal-authority",
                "historical v6 root is readable but has no current terminal authority",
                source="derived",
            ),
        )
    if authority.status == "operational_abort":
        return authority, ()
    if authority.status == "current_open_uncommitted":
        return authority, (
            _finding(
                "operational",
                "terminal-authority",
                "current v6 terminal epoch remains open and uncommitted",
                source="derived",
            ),
        )
    if authority.status == "invalid_incomplete":
        return authority, (
            _finding(
                "integrity",
                "terminal-authority",
                "current v6 terminal authority is incomplete or inconsistent "
                f"({authority.detail_code or 'TERMINAL_AUTHORITY_INVALID'})",
                source="derived",
            ),
        )
    return authority, ()


def _transaction_findings(root: Path) -> tuple[VerificationFindingV2, ...]:
    """Audit v6 work authority and classify terminals dimensionally.

    Replay proves that transaction records agree with one another. This pass
    also proves that the authority they agree on is authority the frozen
    RunManifest actually granted. Prepared or denied work has no provider call
    for the legacy route verifier to inspect, so it must be checked here.
    """

    from deepreason.harness import Harness
    from deepreason.llm.firewall import route_fingerprint
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    try:
        harness = Harness(root, read_only=True)
        work = harness.workflow_state.transaction_work
    except Exception:  # legacy verification already reports unreadable history
        return ()

    manifest = None
    try:
        candidate = root / MANIFEST_NAME
        if candidate.exists():
            loaded = load_run_manifest(candidate)
            if loaded.schema_version == 6:
                manifest = loaded
    except Exception:
        # Manifest/hash failures are already retained from legacy verification.
        # Do not manufacture follow-on findings from an untrusted policy.
        manifest = None

    def authority_differences(work_id: str, item) -> tuple[str, ...]:
        if manifest is None:
            return ()
        preparation = item.preparation
        differences: list[str] = []
        lease = preparation.route_lease
        task = preparation.task_kind.value
        payload = (
            preparation.task_payload_value
            if isinstance(preparation.task_payload_value, dict)
            else None
        )

        if preparation.manifest_digest != manifest.sha256:
            differences.append("manifest digest differs from the bound v6 manifest")

        routes = manifest.roles.get(lease.role, ())
        route = routes[lease.seat] if 0 <= lease.seat < len(routes) else None
        if route is None:
            differences.append(
                f"route {lease.role}[{lease.seat}] is absent from the frozen manifest"
            )
        else:
            if lease.endpoint_id != route.endpoint_id:
                differences.append("route endpoint differs from the frozen seat")
            if lease.route_sha256 != route_fingerprint(route):
                differences.append("route fingerprint differs from the frozen seat")

        control = manifest.control_plane_policy
        versions = control.contract_versions
        expected_contract: str | None = None
        expected_role: str | None = None
        expected_seat: int | None = None
        expected_endpoint: str | None = None

        is_atomic_child = (
            payload is not None
            and payload.get("schema") == "contract-decomposition-child.v1"
        )
        if is_atomic_child:
            try:
                harness.workflow_state._validate_preparation_decomposition_authority(
                    preparation
                )
            except ValueError as error:
                differences.append(str(error))
            expected_contract = preparation.contract_id
            expected_role = lease.role
            expected_seat = lease.seat
            expected_endpoint = lease.endpoint_id
        elif task == "conjecture":
            expected_contract = versions.conjecturer_turn_contract
            expected_role = "conjecturer"
            if payload is not None and payload.get("schema") in {
                "conjecture.semantic-task.v1",
                "conjecture.semantic-task.v2",
                "conjecture.context-continuation-task.v1",
                "simulation.follow-up-task.v1",
            }:
                run_input_digest = payload.get("run_input_digest")
                if (
                    run_input_digest is not None
                    and run_input_digest != manifest.run_input_digest
                ):
                    differences.append(
                        "conjecture task carries a different run-input digest"
                    )
                school_id = payload.get("school_id")
                if control.school_execution.mode == "route_bound":
                    binding = next(
                        (
                            candidate
                            for candidate in control.school_execution.bindings
                            if candidate.school_id == school_id
                        ),
                        None,
                    )
                    if binding is None:
                        differences.append(
                            "route-bound conjecture has no frozen school binding"
                        )
                    else:
                        expected_role = binding.role
                        expected_seat = binding.seat
                        expected_endpoint = binding.endpoint_id
        elif task == "criticism":
            expected_contract = versions.batch_critic_contract
            policy = manifest.criticism_policy
            if policy is None:
                differences.append("criticism work is not authorized by the manifest")
            elif payload is None or payload.get("schema") != "criticism.semantic-task.v1":
                differences.append("criticism work has no recognized semantic task")
            else:
                school_id = payload.get("critic_school_id")
                binding = next(
                    (
                        candidate
                        for candidate in policy.bindings
                        if candidate.school_id == school_id
                    ),
                    None,
                )
                if binding is None:
                    differences.append("critic school has no frozen criticism binding")
                else:
                    expected_role = binding.role
                    expected_seat = binding.seat
                    expected_endpoint = binding.endpoint_id
        elif task == "bridge_ledger":
            expected_contract = versions.bridge_ledger_wire_contract
            expected_role = manifest.bridge_policy.ledger_role
        elif task == "bridge_composition":
            expected_contract = versions.bridge_composition_contract
            expected_role = manifest.bridge_policy.composer_role
        elif task == "bridge_review":
            expected_contract = "groundingverdictwirev1.direct.v1"
            expected_role = manifest.bridge_policy.reviewer_role
            if not manifest.bridge_policy.grounding_review:
                differences.append("bridge review is disabled by the frozen manifest")
        elif task == "scratch_authoring":
            authoring = control.scratch_authoring
            scratch_policy = manifest.scratch_policy
            if (
                not authoring.enabled
                or scratch_policy is None
                or not scratch_policy.enabled
            ):
                differences.append("model scratch authoring is disabled by the manifest")
            if payload is None or payload.get("schema") != "scratch.authoring-task.v1":
                differences.append("scratch work has no recognized authoring task")
            else:
                operation = payload.get("operation")
                expected = (
                    {
                        "block": (
                            scratch_policy.block_role,
                            "scratch.block.compact.v1",
                        ),
                        "link": (
                            scratch_policy.link_role,
                            "scratch.link.compact.v1",
                        ),
                        "guide": (
                            scratch_policy.guide_role,
                            "scratch.cluster-guide.compact.v1",
                        ),
                    }.get(operation)
                    if scratch_policy is not None
                    else None
                )
                if expected is None:
                    differences.append("scratch work names an unknown operation")
                else:
                    expected_role, expected_contract = expected
        elif task == "repair":
            if payload is None:
                differences.append("repair work has no inspectable authority payload")
            elif payload.get("schema") == "repair.semantic-task.v1":
                parent_id = payload.get("parent_work_id")
                parent = work.get(parent_id)
                if parent is None or parent_id == work_id:
                    differences.append("repair work has no valid parent transaction")
                else:
                    expected_contract = parent.preparation.contract_id
                    if lease != parent.preparation.route_lease:
                        differences.append("repair route differs from its parent transaction")
            elif (
                payload.get("schema")
                in {"bridge.transaction-task.v1", "bridge.transaction-task.v2"}
                and payload.get("template_role") == "bridge_grounding_repair"
            ):
                expected_contract = "groundingrepairwirev1.direct.v1"
                expected_role = manifest.bridge_policy.grounding_repair_role
                if not manifest.bridge_policy.grounding_review:
                    differences.append(
                        "bridge grounding repair is disabled by the frozen manifest"
                    )
            else:
                differences.append("repair work has an unrecognized authority payload")
        else:
            differences.append(f"unknown v6 task kind {task!r}")

        if expected_contract is not None and preparation.contract_id != expected_contract:
            differences.append(
                f"contract {preparation.contract_id!r} differs from "
                f"authorized {expected_contract!r}"
            )
        if expected_role is not None and lease.role != expected_role:
            differences.append(
                f"role {lease.role!r} differs from authorized {expected_role!r}"
            )
        if expected_seat is not None and lease.seat != expected_seat:
            differences.append(
                f"seat {lease.seat} differs from authorized seat {expected_seat}"
            )
        if expected_endpoint is not None and lease.endpoint_id != expected_endpoint:
            differences.append("endpoint differs from the task's frozen school binding")
        return tuple(dict.fromkeys(differences))

    findings: list[VerificationFindingV2] = []
    for work_id, item in sorted(work.items()):
        differences = authority_differences(work_id, item)
        if differences:
            findings.append(
                _finding(
                    "security",
                    "transaction-authority",
                    f"work {work_id[:19]} exceeds frozen authority: "
                    + "; ".join(differences),
                    source="derived",
                )
            )
        terminal = item.terminal
        task = item.preparation.task_kind.value
        short_id = work_id[:19]
        if terminal is None:
            if item.issued:
                findings.append(
                    _finding(
                        "operational",
                        "transaction-terminal",
                        f"issued {task} work {short_id} has no typed terminal",
                        source="derived",
                    )
                )
            else:
                findings.append(
                    _finding(
                        "completion",
                        "transaction-terminal",
                        f"prepared {task} work {short_id} was never issued or closed",
                        source="derived",
                    )
                )
            continue

        status = terminal.status
        if status == "completed":
            continue
        if status in {"budget_denied", "cancelled"}:
            channel: VerificationChannel = "completion"
        elif status == "abandoned" and not item.issued:
            channel = "completion"
        else:
            channel = "operational"
        findings.append(
            _finding(
                channel,
                "transaction-terminal",
                f"{task} work {short_id} terminated as {status}: {terminal.reason_code}",
                source="derived",
            )
        )
    return tuple(findings)

def _deferred_model_phase_findings(
    root: Path,
) -> tuple[VerificationFindingV2, ...]:
    """Expose deliberately deferred v6 model phases as completion debt."""

    from deepreason.harness import Harness

    try:
        events = tuple(Harness(root, read_only=True).log.read())
    except Exception:
        return ()
    findings: list[VerificationFindingV2] = []
    for event in events:
        inputs = tuple(event.inputs)
        if not inputs or inputs[0] != "v6-model-phase-deferred.v1":
            continue
        if len(inputs) != 6 or any(
            not isinstance(value, str) or not value for value in inputs
        ):
            findings.append(
                _finding(
                    "integrity",
                    "model-phase-deferred",
                    f"event seq={event.seq} has a malformed v6 deferral marker",
                    source="derived",
                )
            )
            continue
        _schema, phase, role, target_ref, obligation_ref, reason = inputs
        findings.append(
            _finding(
                "completion",
                "model-phase-deferred",
                f"phase {phase!r} for role {role!r} was deferred ({reason}); "
                f"target={target_ref}, obligation={obligation_ref}",
                source="derived",
            )
        )
    return tuple(findings)



def verify_root_report(
    root: Path | str,
    meter_total: int | None = None,
    *,
    allow_missing_terminal: bool = False,
) -> VerificationReportV2:
    """Derive a v2 report without altering legacy verification or root bytes."""

    from deepreason.invariants import verify_root

    resolved = Path(root)
    manifest_schema_version = _manifest_schema_version(resolved)
    legacy = verify_root(resolved, meter_total=meter_total)
    retained_legacy = 0
    channels: dict[str, list[VerificationFindingV2]] = {
        "integrity": [],
        "security": [],
        "completion": [],
        "epistemic": [],
        "operational": [],
    }
    for item in legacy.get("violations", ()):  # tolerate historical mapping shape
        check = str(item.get("check") or "legacy")
        detail = str(item.get("detail") or "legacy verifier finding")
        retained_legacy += 1
        channel = _legacy_channel(check, detail)
        channels[channel].append(_finding(channel, check, detail, source="legacy"))

    payload, terminal_error = _read_terminal(resolved)
    if terminal_error is not None:
        channels[terminal_error.channel].append(terminal_error)
    if (
        manifest_schema_version == 6
        and payload is not None
        and payload.get("schema") != "deepreason-run-result-v2"
    ):
        channels["integrity"].append(
            _finding(
                "integrity",
                "run-result-version",
                "v6 root has a legacy run-result schema; "
                "deepreason-run-result-v2 is required",
                source="terminal",
            )
        )
    if (
        payload is None
        and terminal_error is None
        and manifest_schema_version == 6
        and not allow_missing_terminal
    ):
        channels["operational"].append(
            _finding(
                "operational",
                "run-result",
                "v6 root has no canonical run-result.json terminal",
                source="derived",
            )
        )
    for finding in _terminal_findings(payload):
        channels[finding.channel].append(finding)
    terminal_authority = None
    if manifest_schema_version == 6:
        try:
            from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

            authority_manifest = load_run_manifest(resolved / MANIFEST_NAME)
        except Exception:
            authority_manifest = None
        if authority_manifest is not None:
            terminal_authority, authority_findings = _terminal_authority_findings(
                resolved,
                payload,
                authority_manifest,
            )
            if not (
                allow_missing_terminal
                and payload is None
                and terminal_authority.status == "current_open_uncommitted"
            ):
                for finding in authority_findings:
                    channels[finding.channel].append(finding)
        for finding in _model_execution_findings(
            resolved,
            payload,
            terminal_authority=terminal_authority,
        ):
            channels[finding.channel].append(finding)
        for finding in _transaction_findings(resolved):
            channels[finding.channel].append(finding)
        for finding in _deferred_model_phase_findings(resolved):
            channels[finding.channel].append(finding)

    stats = dict(legacy.get("stats") or {})
    capability_requests = stats.get("capability_requests")
    capability_executions = stats.get("capability_executions")
    if (
        isinstance(capability_requests, int)
        and not isinstance(capability_requests, bool)
        and isinstance(capability_executions, int)
        and not isinstance(capability_executions, bool)
        and capability_requests > capability_executions
    ):
        channels["completion"].append(
            _finding(
                "completion",
                "capability-lifecycle",
                f"{capability_requests - capability_executions} capability request(s) "
                "did not reach execution",
                source="derived",
            )
        )
    stats["verification_v2"] = {
        "terminal_state": payload.get("state") if payload is not None else None,
        "legacy_violation_count": retained_legacy,
        "legacy_adapter_suppressed_count": 0,
        "manifest_schema_version": manifest_schema_version,
    }
    return VerificationReportV2(
        integrity=tuple(channels["integrity"]),
        security=tuple(channels["security"]),
        completion=tuple(channels["completion"]),
        epistemic=tuple(channels["epistemic"]),
        operational=tuple(channels["operational"]),
        stats=stats,
    )


__all__ = [
    "VerificationChannel",
    "VerificationFindingV2",
    "VerificationReportV2",
    "verify_root_report",
]
