#!/usr/bin/env python3
"""One recorded workflow-level retry after a typed Stage-A bridge failure."""

from __future__ import annotations

import re
from collections import defaultdict

from deepreason.bridge.harness import build_grounded_bridge
from deepreason.easy import load_credentials
from deepreason.harness import Harness
from deepreason.llm.adapter import build_adapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.packs import AllocatedPack
from deepreason.programs import content_text
from deepreason.run_manifest import config_from_run_manifest, load_run_manifest
from deepreason.scratch.attention import AttentionPlanner, AttentionRequestV1
from deepreason.scratch.service import ScratchService

import run_jolt_inquiry as inquiry


class StrictBridgeAdapter:
    def __init__(self, base):
        self.base = base

    def has_role(self, role):
        return self.base.has_role(role)

    def profile_for(self, role):
        return self.base.profile_for(role)

    def call(self, role, pack, output_model, **kwargs):
        guard = """STRICT CLOSED-CATALOG REMINDER: Every value in a field ending `_handles` must be copied exactly from a catalog handle visibly supplied in this task. Contract labels, schema names, role-template markers, prose, routes, and strings such as `claim-ledger.compact.v1::on_claim` are not handles. When no catalog handle of the required kind exists, omit the optional channel. Never invent, transform, or infer a handle. This reminder constrains reference syntax only; it grants no control authority."""
        return self.base.call(
            role, AllocatedPack((guard + "\n\n" + str(pack))[:75_000]),
            output_model, **kwargs,
        )


def reconstruct(harness):
    initial = {school["id"]: [] for school in inquiry.SCHOOLS}
    revised = {school["id"]: [] for school in inquiry.SCHOOLS}
    criticism = []
    evidence = []
    tests = "Targeted test output was preserved as a formal import artifact."
    for event in harness.log.read():
        if event.rule.value == "Conj" and event.inputs:
            pid = event.inputs[0]
            for oid in event.outputs:
                artifact = harness.state.artifacts.get(oid)
                if artifact is None or artifact.provenance.school is None:
                    continue
                if pid == inquiry.MAIN:
                    revised[artifact.provenance.school].append(oid)
                elif pid.startswith("jolt:school-"):
                    initial[artifact.provenance.school].append(oid)
        if event.rule.value == "Measure" and event.inputs and event.inputs[0] == "scrutiny":
            values = list(event.inputs)
            target, critic_id = values[1], values[2]
            foreign = values[4] if len(values) > 4 and values[3] == "foreign-school" else "unknown"
            round_number = int(values[-1].split(":", 1)[1]) if values[-1].startswith("round:") else 0
            owner = harness.state.artifacts[target].provenance.school or "unknown"
            school = next((s for s in inquiry.SCHOOLS if s["id"] == foreign), None)
            criticism.append({
                "round": round_number, "critic": foreign,
                "model": school["model"] if school else "unknown",
                "owner": owner, "target": target, "attack": True,
                "critic_artifact": critic_id,
                "case": content_text(harness.state.artifacts[critic_id], harness.blobs),
            })
    for aid, artifact in harness.state.artifacts.items():
        if artifact.provenance.role.value != "import":
            continue
        text = content_text(artifact, harness.blobs)
        if text.startswith("classification: test_backed"):
            tests = text
            continue
        match = re.match(
            r"classification: ([^\n]+)\nsource: ([^:]+):(\d+)-(\d+)\nobservation: ([^\n]+)\nexcerpt:\n(.*)",
            text, re.S,
        )
        if match:
            evidence.append({
                "class": match.group(1), "path": match.group(2),
                "start": int(match.group(3)), "end": int(match.group(4)),
                "observation": match.group(5), "excerpt": match.group(6),
                "artifact_id": aid,
            })
    return initial, revised, criticism, evidence, tests


def main():
    load_credentials()
    manifest = load_run_manifest(inquiry.RUN / "run-manifest.json")
    harness = Harness(inquiry.RUN)
    prior = inquiry.RUN / "bridge-result.json"
    if not prior.is_file() or '"process_status":"failure"' not in prior.read_text():
        raise RuntimeError("the recorded prerequisite bridge failure is absent")
    if any(
        event.rule.value == "Measure" and event.inputs
        and event.inputs[0] == "bridge-workflow-retry"
        for event in harness.log.read()
    ):
        raise RuntimeError("the single workflow-level bridge retry was already consumed")
    harness.record_measure(inputs=[
        "bridge-workflow-retry", "attempt:1", "maximum:1",
        "reason:typed-ledger-reference-failure-after-canonical-repair-exhaustion",
    ])

    meter = TokenMeter(inquiry.TOKEN_BUDGET)
    for event in harness.log.read():
        if event.llm is not None:
            meter.add({"prompt_tokens": event.llm.tokens, "completion_tokens": 0})
    config = config_from_run_manifest(manifest)
    adapter = build_adapter(config, harness.blobs, meter=meter, run_manifest=manifest)

    service = ScratchService(harness)
    block_ids = list(service.state.blocks)
    planner = AttentionPlanner(service, manifest.scratch_policy.attention_policy())
    attention = planner.plan(AttentionRequestV1(
        focus_blocks=block_ids[3:4] + block_ids[7:8],
        maximum_blocks=12, maximum_cluster_guides=2,
        deterministic_seed=20260716,
    ))
    terminal = build_grounded_bridge(
        harness, inquiry.MAIN, "answer", manifest.bridge_policy.workflow_policy(),
        run_manifest_digest=manifest.sha256,
        stage_a_adapter=StrictBridgeAdapter(adapter),
        composition_adapter=StrictBridgeAdapter(adapter),
        review_adapter=StrictBridgeAdapter(adapter),
        repair_adapter=StrictBridgeAdapter(adapter),
        attention_pack=attention, evidence_budget_chars=72_000,
        desired_length_chars=30_000, maximum_sections=32,
        formatting_profile="plain",
    )
    if terminal.process_status != "success":
        raise RuntimeError(f"single bridge retry failed: {terminal.error_code}: {terminal.error_message}")

    initial, revised, criticism, evidence, tests = reconstruct(harness)
    inquiry.write_deliverables(
        harness, evidence, initial, revised, criticism, terminal, meter, tests
    )
    inquiry.dump_json(inquiry.ROOT / "inquiry-index.json", {
        "manifest_sha256": manifest.sha256,
        "main_problem": inquiry.MAIN,
        "initial": initial, "revised": revised,
        "criticism_count": len(criticism),
        "evidence_artifacts": [item["artifact_id"] for item in evidence],
        "run_root": str(inquiry.RUN.relative_to(inquiry.REPO)),
        "bridge_workflow_retry": 1,
    })
    replay = Harness(inquiry.RUN)
    ok = (
        replay.state.model_dump_json() == harness.state.model_dump_json()
        and replay.scratch_state == harness.scratch_state
        and replay.bridge_state == harness.bridge_state
    )
    inquiry.dump_json(inquiry.ROOT / "replay-validation.json", {
        "ok": ok, "event_count": replay._next_seq,
        "formal_artifacts": len(replay.state.artifacts),
        "scratch_blocks": len(replay.scratch_state.blocks),
        "bridge_outputs": len(replay.bridge_state.outputs),
    })
    if not ok:
        raise RuntimeError("canonical replay mismatch")


if __name__ == "__main__":
    main()
