"""Deterministic admission recovery for transactional v6 conjecture work.

The provider boundary is deliberately absent from this module. Recovery
consumes the raw blob already named by ProviderAttemptV1, rebuilds the exact
call-local wire contract, and resumes only deterministic validation and
materialization.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from deepreason.canonical import canonical_json
from deepreason.conjecture_turn import (
    ConjectureTurnV6,
    ReasoningConjecturerTurnV6,
)
from deepreason.llm.contracts import CandidateRef, ConjectureCandidate
from deepreason.llm.firewall import reject_model_control_fields
from deepreason.llm.repair import parse_one_json_value
from deepreason.llm.wire import AliasTable, ConjecturerTurnWireContractV6
from deepreason.ontology import Artifact, Provenance, Rule
from deepreason.rules.guards import anti_relapse
from deepreason.run_manifest import RunManifest, config_from_run_manifest
from deepreason.scratch.authoring import (
    ScratchAuthoringError,
    ScratchAuthoringService,
)
from deepreason.scratch.conjecture import validate_conjecture_context_call
from deepreason.scratch.service import ScratchService
from deepreason.workflow.models import WorkflowTaskKind
from deepreason.workflow.profiles import compile_workflow_profile
from deepreason.workflow.transaction import (
    ContextNamespace,
    ProviderAttemptV1,
    SemanticAdmissionV1,
)
from deepreason.workflow.transaction_service import InquiryTransactionService
from deepreason.workloads.models import (
    MandatoryInterface,
    MandatoryRef,
    compile_interface_draft,
)
from deepreason.workloads.text import (
    draft_countercondition_commitments,
    envelope_json,
    proposal_envelope,
)


class ConjectureRecoveryAuthorityError(RuntimeError):
    """Durable records do not describe one authorized conjecture attempt."""


class ConjectureRecoverySemanticError(RuntimeError):
    """A validated response cannot be deterministically materialized."""


def _authority(condition: bool, message: str) -> None:
    if not condition:
        raise ConjectureRecoveryAuthorityError(message)


def _payload_dict(value: Any) -> dict[str, Any]:
    _authority(
        isinstance(value, Mapping),
        "conjecture preparation payload is not an object",
    )
    return {str(key): item for key, item in value.items()}


def _source_call(harness, provider: ProviderAttemptV1):
    matches = [
        (event.seq, event.llm)
        for event in harness.log.read()
        if event.llm is not None
        and event.llm.work_order_id == provider.work_id
        and event.llm.dispatch_authorization_ref
        == provider.authorization_bundle_ref
    ]
    _authority(
        len(matches) == 1,
        "provider attempt does not have exactly one durable call",
    )
    source_call_seq, call = matches[0]
    _authority(
        call.raw_ref == provider.raw_ref,
        "provider raw reference differs from call",
    )
    _authority(
        call.role == "conjecturer",
        "conjecture work was served by another role",
    )
    _authority(call.prompt_ref != "", "provider call has no frozen prompt")
    return source_call_seq, call


def _catalogs(
    item,
    payload: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str], tuple[str, ...]]:
    exposure = item.exposure
    _authority(
        exposure is not None,
        "provider result has no context exposure receipt",
    )
    source_aliases = {
        entry.alias: entry.object_ref
        for entry in exposure.exposed_items
        if entry.namespace == ContextNamespace.SOURCE
    }
    scratch_aliases = {
        entry.alias: entry.object_ref
        for entry in exposure.exposed_items
        if entry.namespace == ContextNamespace.SCRATCH
    }
    simulation_exposed = {
        entry.alias
        for entry in exposure.exposed_items
        if entry.namespace == ContextNamespace.SIMULATION
    }
    simulation = payload.get("simulation_authority")
    _authority(
        isinstance(simulation, Mapping),
        "conjecture payload lacks simulation authority",
    )
    raw_aliases = simulation.get("input_aliases", ())
    _authority(
        isinstance(raw_aliases, (tuple, list))
        and all(isinstance(alias, str) for alias in raw_aliases),
        "simulation input aliases are malformed",
    )
    simulation_aliases = tuple(raw_aliases)
    _authority(
        len(simulation_aliases) == len(set(simulation_aliases)),
        "simulation input aliases are duplicated",
    )
    _authority(
        set(simulation_aliases).issubset(simulation_exposed),
        "simulation contract names context that was not exposed",
    )
    return source_aliases, scratch_aliases, simulation_aliases


def _validate_authority(
    harness,
    manifest: RunManifest,
    provider: ProviderAttemptV1,
):
    item = harness.workflow_state.transaction_work.get(provider.work_id)
    _authority(item is not None, "provider attempt names no replayed transaction")
    preparation = item.preparation
    _authority(
        preparation.task_kind == WorkflowTaskKind.CONJECTURE,
        "work is not conjecture",
    )
    _authority(
        preparation.manifest_digest == manifest.sha256,
        "work belongs to another manifest",
    )
    _authority(
        preparation.contract_id == "conjecturer.turn.v6",
        "work uses another contract",
    )
    _authority(
        provider.outcome == "provider_result",
        "transport failures have no semantic result",
    )
    _authority(
        provider.raw_ref is not None,
        "provider result has no durable raw blob",
    )
    _authority(
        item.authorization is not None
        and item.reservation is not None
        and item.exposure is not None,
        "provider result lacks issued authority",
    )
    payload = _payload_dict(preparation.task_payload_value)
    _authority(
        payload.get("schema") == "conjecture.semantic-task.v2",
        "unknown conjecture payload schema",
    )
    problem_ref = payload.get("problem_ref")
    _authority(
        isinstance(problem_ref, str),
        "conjecture payload has no problem reference",
    )
    _authority(
        preparation.target_refs == (problem_ref,),
        "prepared target differs from payload",
    )
    problem = harness.state.problems.get(problem_ref)
    _authority(problem is not None, "prepared conjecture problem is unavailable")
    _authority(
        payload.get("run_input_digest") == manifest.run_input_digest,
        "conjecture payload belongs to another run input",
    )
    _authority(
        set(problem.criteria).issubset(preparation.input_refs),
        "prepared inputs omit a problem criterion",
    )
    profile = compile_workflow_profile(manifest)
    _authority(
        payload.get("maximum_candidates") == profile.max_candidates,
        "candidate ceiling differs from manifest",
    )
    _authority(
        payload.get("workload_profile") == manifest.workload_profile,
        "workload profile differs from manifest",
    )
    simulation = payload.get("simulation_authority")
    policy = manifest.inquiry_capability_policy.simulation
    _authority(
        isinstance(simulation, Mapping),
        "simulation authority is missing",
    )
    _authority(
        bool(simulation.get("enabled")) == policy.enabled
        and simulation.get("policy_digest") == policy.digest
        and simulation.get("maximum_proposals_per_turn")
        == policy.maximum_proposals_per_turn,
        "simulation authority differs from manifest",
    )
    source_call_seq, call = _source_call(harness, provider)
    prompt = harness.blobs.get(call.prompt_ref)
    prompt_sha256 = hashlib.sha256(prompt).hexdigest()
    _authority(
        prompt_sha256 == item.exposure.prompt_sha256,

        "stored prompt differs from exposure",
    )
    _authority(
        prompt_sha256 == provider.prompt_sha256,
        "stored prompt differs from provider authority",
    )
    scratch_aliases = {
        entry.alias: entry.object_ref
        for entry in item.exposure.exposed_items
        if entry.namespace == ContextNamespace.SCRATCH
    }
    if scratch_aliases:
        _authority(
            call.conjecture_context is not None,
            "scratch-bearing provider result has no conjecture context authority",
        )
        try:
            validate_conjecture_context_call(
                ScratchService(harness),
                call.conjecture_context,
                manifest_digest=manifest.sha256,
                problem_id=problem.id,
                school_id=payload.get("school_id"),
                scratch_aliases=scratch_aliases,
                provider_prompt=prompt,
            )
        except ValueError as error:
            raise ConjectureRecoveryAuthorityError(
                f"conjecture context authority is invalid: {error}"
            ) from error
    else:
        _authority(
            call.conjecture_context is None,
            "provider call claims scratch context absent from transaction exposure",
        )
    return item, payload, problem, source_call_seq, call


def _wire_output(
    harness, manifest: RunManifest, item, payload, problem, provider
):
    source_aliases, scratch_aliases, simulation_aliases = _catalogs(
        item, payload
    )
    reasoning = any(
        harness.commitments[commitment_id].eval
        == "program:reasoning-envelope-wf"
        for commitment_id in problem.criteria
        if commitment_id in harness.commitments
    )
    _authority(
        payload.get("reasoning") is reasoning,
        "reasoning contract flag differs from problem",
    )
    control = manifest.control_plane_policy
    _authority(control is not None, "v6 manifest has no control plane")
    simulation_policy = manifest.inquiry_capability_policy.simulation
    contract = ConjecturerTurnWireContractV6(
        reasoning=reasoning,
        aliases=AliasTable(source_aliases),
        scratch_aliases=scratch_aliases,
        permitted_retrieval_channels=(
            control.conjecture_context.permitted_retrieval_channels
        ),
        simulation_enabled=simulation_policy.enabled,
        maximum_simulation_proposals=(
            simulation_policy.maximum_proposals_per_turn
            if simulation_policy.enabled
            else 0
        ),
        simulation_input_aliases=simulation_aliases,
        scratch_authoring_policy=control.scratch_authoring,
    )
    _authority(
        contract.contract_id == item.preparation.contract_id,
        "reconstructed contract id differs",
    )
    try:
        raw = harness.blobs.get(provider.raw_ref).decode("utf-8")
    except (KeyError, UnicodeDecodeError) as error:
        raise ConjectureRecoveryAuthorityError(
            "provider raw blob is unavailable or non-UTF-8"
        ) from error
    candidate = parse_one_json_value(raw).value
    reject_model_control_fields(candidate)
    wire_value = contract.validate_value(candidate)
    output = contract.compile(wire_value)
    expected_model = (
        ReasoningConjecturerTurnV6 if reasoning else ConjectureTurnV6
    )
    _authority(
        isinstance(output, expected_model),
        "reconstructed contract compiled another output type",
    )
    return output, scratch_aliases, reasoning


def _mandatory_interface(payload: Mapping[str, Any]) -> MandatoryInterface:
    value = payload.get("mandatory_interface")
    if value is None:
        return MandatoryInterface()
    if not isinstance(value, Mapping):
        raise ConjectureRecoveryAuthorityError(
            "mandatory interface is malformed"
        )
    commitments = value.get("commitments", ())
    refs = value.get("refs", ())
    if not isinstance(commitments, (list, tuple)) or not all(
        isinstance(item, str) for item in commitments
    ):
        raise ConjectureRecoveryAuthorityError(
            "mandatory commitments are malformed"
        )
    if not isinstance(refs, (list, tuple)):
        raise ConjectureRecoveryAuthorityError(
            "mandatory references are malformed"
        )
    normalized_refs = []
    for item in refs:
        if not isinstance(item, Mapping) or not isinstance(
            item.get("target"), str
        ):
            raise ConjectureRecoveryAuthorityError(
                "mandatory reference is malformed"
            )
        normalized_refs.append(
            MandatoryRef(
                item["target"],
                item.get("role", "dependence"),
            )
        )
    return MandatoryInterface(
        commitments=tuple(commitments),
        refs=tuple(normalized_refs),
    )


def _existing_conjecture_artifacts(
    harness,
    source_call_seq: int,
) -> tuple[str, ...]:
    marker = f"conjecture-call:{source_call_seq}"
    found: list[str] = []
    for event in harness.log.read():
        if marker not in event.inputs:
            continue
        found.extend(
            output
            for output in event.outputs
            if output in harness.state.artifacts
        )
    return tuple(dict.fromkeys(found))



def _materialize_formal(
    harness,
    manifest: RunManifest,
    output,
    payload: Mapping[str, Any],
    problem,
    source_call_seq: int,
    *,
    embedder,
    contract_id: str = "conjecturer.turn.v6",
) -> tuple[str, ...]:
    reasoning = bool(payload.get("reasoning", False))
    maximum = int(payload["maximum_candidates"])
    proposals = list(output.candidates)
    if bool(payload.get("tail_weighted", False)):
        proposals.sort(key=lambda proposal: proposal.typicality)
    proposals = proposals[:maximum]
    candidate_rows: list[
        tuple[ConjectureCandidate, tuple[Any, ...]]
    ] = []
    if reasoning:
        for proposal in proposals:
            envelope = proposal_envelope(proposal)
            candidate_rows.append(
                (
                    ConjectureCandidate(
                        content=envelope_json(envelope),
                        typicality=proposal.typicality,
                        refs=[
                            CandidateRef(target=target, role="mention")
                            for target in proposal.optional_refs
                        ],
                    ),
                    tuple(
                        draft_countercondition_commitments(envelope)
                    ),
                )
            )
    else:
        candidate_rows = [(candidate, ()) for candidate in proposals]

    mandatory = _mandatory_interface(payload)
    prepared = []
    for candidate, draft_pool in candidate_rows:
        candidate_mandatory = MandatoryInterface(
            commitments=tuple(
                dict.fromkeys(
                    (
                        *mandatory.commitments,
                        *(item.id for item in draft_pool),
                    )
                )
            ),
            refs=mandatory.refs,
        )
        interface, draft = compile_interface_draft(
            harness,
            problem,
            candidate.content,
            mandatory=candidate_mandatory,
            optional_refs=(
                (ref.target, ref.role) for ref in candidate.refs
            ),
            draft_commitments=draft_pool,
        )
        artifact = Artifact(
            id=Artifact.compute_id(
                f"inline:{candidate.content}",
                "utf8",
                interface,
            ),
            content_ref=f"inline:{candidate.content}",
            codec="utf8",
            interface=interface,
            provenance=Provenance(
                role="conjecturer",
                school=payload.get("school_id"),
                event_seq=harness._next_seq,
            ),
        )
        prepared.append(
            (artifact, tuple(draft), candidate_mandatory)
        )

    existing_refs = set(
        _existing_conjecture_artifacts(harness, source_call_seq)
    )
    expected_refs = {
        artifact.id for artifact, _draft, _mandatory in prepared
    }
    _authority(
        existing_refs.issubset(expected_refs),
        "existing conjecture effects do not match provider output",
    )
    admitted_drafts: dict[str, Any] = {}
    admitted_artifacts: list[Artifact] = []
    candidate_domains = {}
    seen: set[str] = set()
    from deepreason.rules.conj import root_problem_family

    family = root_problem_family(harness.state, problem.id)
    config = config_from_run_manifest(manifest)
    for artifact, draft, candidate_mandatory in prepared:
        if artifact.id in seen:
            continue
        overlay = {
            **harness.commitments,
            **admitted_drafts,
            **{item.id: item for item in draft},
        }
        domain = anti_relapse.relapse_domain(
            artifact,
            harness,
            workload_profile=(
                "text" if reasoning else manifest.workload_profile
            ),
            problem_family=family,
            contract_id=contract_id,
            mandatory_refs=candidate_mandatory.domain_refs(),
            component_spec=payload.get("component_spec"),
            theorem_interface=payload.get("theorem_interface"),
            commitments=overlay,
        )
        if artifact.id in existing_refs:
            current = harness.state.artifacts[artifact.id]
            _authority(
                current.content_ref == artifact.content_ref
                and current.codec == artifact.codec
                and current.interface == artifact.interface,
                "existing recovered artifact conflicts with provider output",
            )
            admitted = True
            reason = "recovered-existing"
        else:
            admitted, reason = anti_relapse.check(
                artifact,
                [],
                harness,
                embedder=embedder,
                near_dup_eps=config.NEAR_DUP_EPS,
                domain=domain,
                commitments=overlay,
            )
        if not admitted:
            if not any(
                list(event.inputs)
                == [f"gate:{reason}", artifact.id, problem.id]
                for event in harness.log.read()
            ):
                harness.record_measure(
                    inputs=[
                        f"gate:{reason}",
                        artifact.id,
                        problem.id,
                    ]
                )
            continue
        for commitment in draft:
            admitted_drafts[commitment.id] = commitment
        seen.add(artifact.id)
        admitted_artifacts.append(artifact)
        candidate_domains[artifact.id] = domain

    for commitment in admitted_drafts.values():
        harness.register_commitment(commitment)
    batch = []
    for artifact in admitted_artifacts:
        if artifact.id in existing_refs:
            batch.append(
                (harness.state.artifacts[artifact.id], [])
            )
        else:
            batch.append(
                (
                    artifact.model_copy(
                        update={
                            "provenance": (
                                artifact.provenance.model_copy(
                                    update={
                                        "event_seq": harness._next_seq
                                    }
                                )
                            )
                        }
                    ),
                    [],
                )
            )
    recorded = anti_relapse.recorded_domains(harness)
    for artifact in admitted_artifacts:
        domain = candidate_domains[artifact.id]
        if recorded.get(artifact.id) != domain:
            anti_relapse.record_domain(
                harness,
                artifact.id,
                domain,
            )
    harness.register_batch(
        batch,
        problem_id=problem.id,
        rule=Rule.CONJ,
        process_inputs=(
            f"conjecture-call:{source_call_seq}",
        ),
    )
    return tuple(
        artifact.id for artifact in admitted_artifacts
    )


def _diagnostic_ref(
    harness,
    code: str,
    error: Exception,
) -> str:
    return harness.blobs.put(
        canonical_json(
            {
                "schema": (
                    "conjecture-admission-recovery-diagnostic.v1"
                ),
                "code": code,
                "error_type": type(error).__name__,
                "message": str(error)[:500],
            }
        )
    )


def _terminal_failure(
    service: InquiryTransactionService,
    provider: ProviderAttemptV1,
    *,
    outcome: str,
    reason_code: str,
    diagnostic_ref: str,
) -> SemanticAdmissionV1:
    admission = service.record_semantic_admission(
        provider,
        outcome=outcome,
        diagnostic_refs=(diagnostic_ref,),
    )
    service.terminate(
        work_id=provider.work_id,
        attempt_index=provider.attempt_index,
        status=(
            "schema_exhausted"
            if outcome == "schema_exhausted"
            else "rejected"
        ),
        reason_code=reason_code,
        usage_status=provider.usage_status,
        prompt_tokens=provider.prompt_tokens,
        completion_tokens=provider.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    return admission



def recover_conjecture_admission(
    harness,
    manifest: RunManifest,
    meter,
    provider: ProviderAttemptV1,
    *,
    embedder=None,
) -> SemanticAdmissionV1:
    """Resume one durable result without any provider dispatch."""

    manifest = RunManifest.model_validate(manifest)
    _authority(
        manifest.schema_version == 6,
        "conjecture recovery requires RunManifest v6",
    )
    service = InquiryTransactionService(
        harness,
        manifest,
        meter,
    )
    (
        item,
        payload,
        problem,
        source_call_seq,
        _call,
    ) = _validate_authority(
        harness,
        manifest,
        provider,
    )
    try:
        output, scratch_aliases, _reasoning = _wire_output(
            harness,
            manifest,
            item,
            payload,
            problem,
            provider,
        )
    except ConjectureRecoveryAuthorityError:
        raise
    except (TypeError, ValueError, ValidationError) as error:
        return _terminal_failure(
            service,
            provider,
            outcome="schema_exhausted",
            reason_code="recovered_schema_exhausted",
            diagnostic_ref=_diagnostic_ref(
                harness,
                "schema_exhausted",
                error,
            ),
        )

    try:
        scratch_refs: tuple[str, ...] = ()
        scratch_proposal = getattr(
            output,
            "scratch_proposal",
            None,
        )
        if scratch_proposal is not None:
            scratch_refs = ScratchAuthoringService(
                ScratchService(harness),
                object(),
            ).admit_proposal(
                scratch_proposal,
                policy=(
                    manifest.control_plane_policy.scratch_authoring
                ),
                visible_aliases=scratch_aliases,
                context_ref=item.exposure.id,
            )
        artifact_refs = _materialize_formal(
            harness,
            manifest,
            output,
            payload,
            problem,
            source_call_seq,
            embedder=embedder,
        )
        simulation_refs: tuple[str, ...] = ()
        if output.simulation_proposals:
            from deepreason.capabilities.simulation import (
                SimulationCapabilityController,
            )

            simulation_refs = SimulationCapabilityController(
                harness, manifest
            ).materialize_transactional_proposals(
                tuple(output.simulation_proposals),
                preparation=item.preparation,
                provider_attempt=provider,
                source_call_seq=source_call_seq,
            )
    except (
        ScratchAuthoringError,
        ConjectureRecoverySemanticError,
        TypeError,
        ValueError,
    ) as error:
        return _terminal_failure(
            service,
            provider,
            outcome="rejected",
            reason_code="recovered_semantic_rejected",
            diagnostic_ref=_diagnostic_ref(
                harness,
                "semantic_rejected",
                error,
            ),
        )

    semantic_output_ref = harness.blobs.put(
        canonical_json(
            output.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            )
        )
    )
    admitted_refs = tuple(
        dict.fromkeys(
            (
                semantic_output_ref,
                *artifact_refs,
                *scratch_refs,
                *simulation_refs,
            )
        )
    )
    admission = service.record_semantic_admission(
        provider,
        outcome="admitted",
        admitted_refs=admitted_refs,
    )
    service.terminate(
        work_id=provider.work_id,
        attempt_index=provider.attempt_index,
        status="completed",
        reason_code=(
            "recovered_semantic_admission_complete"
        ),
        usage_status=provider.usage_status,
        prompt_tokens=provider.prompt_tokens,
        completion_tokens=provider.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    return admission


__all__ = [
    "ConjectureRecoveryAuthorityError",
    "ConjectureRecoverySemanticError",
    "recover_conjecture_admission",
]
