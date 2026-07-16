"""Canonical event-derived Tranche-A terminal audits."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from deepreason.canonical import canonical_json
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
from deepreason.bridge.events import BridgeAction


def _atomic_write(path: Path, data: bytes) -> None:
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _write_markdown(path: Path, title: str, lines: list[str]) -> None:
    body = "\n".join([f"# {title}", "", *lines, ""])
    _atomic_write(path, body.encode("utf-8"))


def _transition_chains(harness: Harness) -> dict[str, list[Any]]:
    chains: dict[str, list[Any]] = defaultdict(list)
    for event in harness.log.read():
        if event.capability is None:
            continue
        transition = harness.capability_state.transitions[
            event.capability.transition_ref
        ]
        chains[transition.request_ref].append(transition)
    return dict(chains)


def write_tranche_a_audits(root: Path | str) -> dict[str, str]:
    """Write only replay-derived reports; never ask models to self-report lineage."""

    root = Path(root)
    manifest = load_run_manifest(root / MANIFEST_NAME)
    if manifest.schema_version != 5:
        return {}
    harness = Harness(root, read_only=True)
    state = harness.capability_state
    chains = _transition_chains(harness)
    written: dict[str, str] = {}

    request_lines = [
        f"Manifest: `{manifest.sha256}`",
        "",
        "Every entry below is reconstructed from typed Capability events and immutable records.",
        "",
    ]
    for request_ref, transitions in chains.items():
        proposal = state.proposals[request_ref]
        request_lines.extend(
            (
                f"## {proposal.request_identifier}",
                "",
                f"Proposal: `{proposal.id}`  ",
                f"Origin work: `{proposal.originating_work_order_ref}`  ",
                f"Source call sequence: `{proposal.source_call_seq}`  ",
                f"Hypothesis: {proposal.hypothesis}  ",
                f"Discriminating purpose: {proposal.discriminating_purpose}  ",
                "Lifecycle: "
                + " → ".join(item.lifecycle.value for item in transitions)
                + "  ",
                f"Terminal reason: `{transitions[-1].reason_code}`",
                "",
            )
        )
    target = root / "CAPABILITY_REQUEST_AUDIT.md"
    _write_markdown(target, "Capability Request Audit", request_lines)
    written[target.name] = str(target)

    result_lines = [
        "A successful backend result establishes only the recorded program execution under the exact stored inputs, seeds, and limits.",
        "",
    ]
    for receipt in state.receipts.values():
        compiled = state.compiled[receipt.compiled_specification_ref]
        work_order = state.work_orders[receipt.simulation_work_order_ref]
        package = next(
            (
                item
                for item in state.result_packages.values()
                if item.receipt_ref == receipt.id
            ),
            None,
        )
        result_lines.extend(
            (
                f"## Receipt {receipt.id}",
                "",
                f"Compiled specification: `{compiled.id}`  ",
                f"Simulation work order: `{work_order.id}`  ",
                f"Template: `{compiled.template_identity}`  ",
                f"Operational status: `{receipt.operational_status}`  ",
                f"Execution disposition: `{receipt.execution_disposition}`  ",
                f"Backend verdict: `{receipt.final_backend_verdict}`  ",
                f"Attempts: `{len(receipt.attempts)}`  ",
                f"Samples in final attempt: `{receipt.attempts[-1].sample_count}`  ",
                f"Source SHA-256: `{receipt.source_sha256}`  ",
                f"Input SHA-256: `{receipt.inputs_sha256}`  ",
                f"Checker SHA-256: `{receipt.checker_sha256}`  ",
                f"Output bytes: `{receipt.output_bytes}`  ",
                f"Output truncated: `{str(receipt.output_truncated).lower()}`  ",
                "Resource limits: `"
                + json.dumps(receipt.resource_limits, sort_keys=True, separators=(",", ":"))
                + "`  ",
                f"Result package: `{package.id if package is not None else 'none'}`",
                "",
            )
        )
    target = root / "SIMULATION_RESULTS.md"
    _write_markdown(target, "Simulation Results", result_lines)
    written[target.name] = str(target)

    lineage_lines = [
        "Edges below are explicit record references. Temporal adjacency alone is not treated as causation.",
        "",
    ]
    events = list(harness.log.read())
    for proposal in state.proposals.values():
        grants = [item for item in state.grants.values() if item.proposal_ref == proposal.id]
        compiled = [item for item in state.compiled.values() if item.proposal_ref == proposal.id]
        receipts = [item for item in state.receipts.values() if item.proposal_ref == proposal.id]
        packages = [item for item in state.result_packages.values() if item.proposal_ref == proposal.id]
        consumptions = [item for item in state.consumptions.values() if item.proposal_ref == proposal.id]
        semantic_effects: list[str] = []
        for consumption in consumptions:
            work_ref = consumption.follow_up_work_order_ref
            call_events = [
                event
                for event in events
                if event.llm is not None and event.llm.work_order_id == work_ref
            ]
            if not call_events:
                semantic_effects.append(
                    f"work `{work_ref}` has no recorded provider result"
                )
                continue
            for call_event in call_events:
                formal_events = [
                    event
                    for event in events
                    if f"conjecture-call:{call_event.seq}" in event.inputs
                ]
                turn_events = [
                    event
                    for event in events
                    if event.conjecture_turn is not None
                    and event.conjecture_turn.source_call_seq == call_event.seq
                ]
                child_requests = [
                    item
                    for item in state.proposals.values()
                    if item.originating_work_order_ref == work_ref
                    and item.source_call_seq == call_event.seq
                ]
                if formal_events:
                    refs = [ref for event in formal_events for ref in event.outputs]
                    semantic_effects.append(
                        "provider call "
                        f"`{call_event.seq}` admitted formal candidate output(s) "
                        + ", ".join(f"`{ref}`" for ref in refs)
                    )
                if child_requests:
                    semantic_effects.append(
                        f"provider call `{call_event.seq}` proposed follow-on discriminator(s) "
                        + ", ".join(f"`{item.id}`" for item in child_requests)
                    )
                if turn_events:
                    actions = ", ".join(
                        f"`{event.conjecture_turn.action.value}`" for event in turn_events
                    )
                    semantic_effects.append(
                        f"provider call `{call_event.seq}` recorded process outcome(s) {actions}"
                    )
                if not formal_events and not child_requests and not turn_events:
                    semantic_effects.append(
                        f"provider call `{call_event.seq}` produced no separately typed semantic change"
                    )
        lineage_lines.extend(
            (
                f"## {proposal.request_identifier}",
                "",
                f"Theory proposal `{proposal.id}` from work `{proposal.originating_work_order_ref}`.",
                f"Grant refs: {', '.join(f'`{item.id}`' for item in grants) or 'none'}.",
                f"Compiled refs: {', '.join(f'`{item.id}`' for item in compiled) or 'none'}.",
                f"Receipt refs: {', '.join(f'`{item.id}`' for item in receipts) or 'none'}.",
                f"Package refs: {', '.join(f'`{item.id}`' for item in packages) or 'none'}.",
                "Fresh result work refs: "
                + (
                    ", ".join(f"`{item.follow_up_work_order_ref}`" for item in consumptions)
                    or "none"
                )
                + ".",
                "Recorded semantic effects: "
                + ("; ".join(semantic_effects) if semantic_effects else "none")
                + ".",
                "",
            )
        )
    target = root / "THEORY_TEST_LINEAGE.md"
    _write_markdown(target, "Theory-to-Test Lineage", lineage_lines)
    written[target.name] = str(target)

    from deepreason.evidence.state import load_evidence_dossier, load_run_input

    evidence = manifest.inquiry_capability_policy.attached_evidence
    run_input = load_run_input(root)
    dossier = load_evidence_dossier(root)
    source_lines = [
        "Tranche A performs no open-web retrieval after manifest freeze.",
        "",
        f"Run-input digest: `{run_input.run_input_digest}`",
        f"Evidence dossier digest: `{dossier.dossier_digest}`",
        f"Evidence policy digest: `{evidence.digest}`",
        "",
    ]
    for item in dossier.sources:
        attached = []
        for artifact in harness.state.artifacts.values():
            if not artifact.content_ref.startswith("inline:"):
                continue
            try:
                value = json.loads(artifact.content_ref.removeprefix("inline:"))
            except json.JSONDecodeError:
                continue
            source = value.get("source") if isinstance(value, dict) else None
            if (
                value.get("schema") == "attached-source-record.v1"
                and isinstance(source, dict)
                and source.get("id") == item.id
            ):
                attached.append(artifact.id)
        source_lines.extend(
            (
                f"## {item.id}: {item.title}",
                "",
                f"Class: `{item.source_class}`  ",
                f"Locator: `{item.source_locator}`  ",
                f"Content SHA-256: `{item.content_sha256}`  ",
                f"Attached source-record artifacts: {', '.join(f'`{ref}`' for ref in attached) or 'none'}",
                "Epistemic status: candidate source; attachment does not establish reliability or truth.",
                "",
            )
        )
    target = root / "RESEARCH_SOURCE_AUDIT.md"
    _write_markdown(target, "Research Source Audit", source_lines)
    written[target.name] = str(target)

    calls = [event.llm for event in events if event.llm is not None]
    attempts = [attempt for call in calls for attempt in call.attempt_trace]
    bridge_actions = [
        event.bridge.action for event in events if event.bridge is not None
    ]
    bridge_roles = set()
    if manifest.bridge_policy is not None:
        bridge_roles.update(
            {
                manifest.bridge_policy.ledger_role,
                manifest.bridge_policy.composer_role,
            }
        )
        for name in ("review_role", "repair_role"):
            value = getattr(manifest.bridge_policy, name, None)
            if value:
                bridge_roles.add(value)
    bridge_calls = [call for call in calls if call.role in bridge_roles]
    embedding_observations = len(harness.scratch_state.similarity_hits)
    token_accounting = {
        "schema": "token-accounting.v1",
        "manifest_digest": manifest.sha256,
        "preflight_provider_usage": {"usage_known": False},
        "inquiry_provider_calls": len(calls),
        "inquiry_provider_attempts": len(attempts),
        "inquiry_provider_tokens": sum(call.tokens for call in calls),
        "inquiry_provider_usage_known": not any(
            attempt.usage_unknown for attempt in attempts
        ),
        "local_schema_repairs": sum(max(0, len(call.attempt_trace) - 1) for call in calls),
        "embedding_usage": {
            "usage_known": False,
            "recorded_similarity_observations": embedding_observations,
            "reason": (
                "receipts preserve vectors and embedder identity but not a universal "
                "provider-token accounting unit"
            ),
        },
        "simulation_compilations": len(state.compiled),
        "simulation_executions": state.execution_count,
        "simulation_backend_attempts": sum(
            len(receipt.attempts) for receipt in state.receipts.values()
        ),
        "bridge_provider_calls": len(bridge_calls),
        "bridge_repairs": sum(
            action == BridgeAction.REPAIR_ATTEMPTED for action in bridge_actions
        ),
        "workflow_bridge_retries": len(harness.bridge_state.workflow_retries),
        "research_requests": 0,
        "formal_tool_executions": 0,
    }
    target = root / "TOKEN_ACCOUNTING.json"
    _atomic_write(target, canonical_json(token_accounting))
    written[target.name] = str(target)

    validation = verify_root(root)
    replay_validation = {
        "schema": "replay-validation.v1",
        "manifest_digest": manifest.sha256,
        "workflow_process_digest": harness.workflow_state.digest,
        "capability_process_digest": state.digest,
        "valid": not validation["violations"],
        "verification": validation,
    }
    target = root / "REPLAY_VALIDATION.json"
    _atomic_write(target, canonical_json(replay_validation))
    written[target.name] = str(target)
    return written


__all__ = ["write_tranche_a_audits"]
