#!/usr/bin/env python3
"""Finalize deliverables after both bounded bridge workflows failed closed."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

from deepreason.harness import Harness
from deepreason.ontology import Provenance
from deepreason.programs import content_text

import run_jolt_inquiry as inquiry


TEST_RESULT = """classification: test_backed
Read-only targeted invariant tests at pinned commit.
command: PYTHONPATH=/tmp/deepreason-jolt-deps:src:mini python -m pytest -q tests/test_run_manifest_scratch_bridge.py tests/test_scratch_attention.py tests/test_bridge_two_stage.py tests/test_route_firewall_scheduler.py tests/test_continuation.py tests/test_migration_compat.py mini/tests/test_scratch_bridge_forward_compat.py
exit: 0
41 passed in 0.89s"""


def reconstruct(harness):
    initial = {school["id"]: [] for school in inquiry.SCHOOLS}
    revised = {school["id"]: [] for school in inquiry.SCHOOLS}
    criticisms = []
    evidence = []
    for event in harness.log.read():
        if event.rule.value == "Conj" and event.inputs:
            destination = revised if event.inputs[0] == inquiry.MAIN else initial
            for oid in event.outputs:
                artifact = harness.state.artifacts.get(oid)
                if artifact is not None and artifact.provenance.school in destination:
                    destination[artifact.provenance.school].append(oid)
        if event.rule.value == "Measure" and event.inputs:
            values = list(event.inputs)
            if values[0] == "scrutiny" and len(values) >= 6:
                target, critic_id, critic_school = values[1], values[2], values[4]
                owner = harness.state.artifacts[target].provenance.school or "unknown"
                school = next(s for s in inquiry.SCHOOLS if s["id"] == critic_school)
                criticisms.append({
                    "round": int(values[-1].split(":", 1)[1]),
                    "target": target, "owner": owner,
                    "critic": critic_school, "model": school["model"],
                    "critic_id": critic_id,
                    "case": content_text(harness.state.artifacts[critic_id], harness.blobs),
                })
    for aid, artifact in harness.state.artifacts.items():
        if artifact.provenance.role.value != "import":
            continue
        text = content_text(artifact, harness.blobs)
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
    return initial, revised, criticisms, evidence


def write_files(harness, initial, revised, criticisms, evidence):
    root = inquiry.ROOT
    evidence_lines = [
        "# Evidence map", "",
        "The map separates implemented behaviour and documented intent. Every repository observation below is a formal import artifact at the pinned commit.", "",
    ]
    for item in evidence:
        evidence_lines += [
            f"## {item['path']}:{item['start']}-{item['end']}", "",
            f"Classification: `{item['class']}`. Evidence artifact: `{item['artifact_id']}`.", "",
            item["observation"], "", "```text", item["excerpt"], "```", "",
        ]
    evidence_lines += ["## Executable checks", "", "```text", TEST_RESULT, "```", ""]
    (root / "EVIDENCE_MAP.md").write_text("\n".join(evidence_lines), encoding="utf-8")

    candidates = [
        "# Candidate architectures", "",
        "These are formal conjecture artifacts, not implemented facts. Initial candidates were produced independently on exact routes; revised candidates incorporate two foreign-school criticisms.", "",
    ]
    for school in inquiry.SCHOOLS:
        candidates += [f"## {school['id']} — `{school['model']}`", ""]
        for aid in initial[school["id"]]:
            candidates += [f"### Initial `{aid}`", "", content_text(harness.state.artifacts[aid], harness.blobs), ""]
        for aid in revised[school["id"]]:
            candidates += [f"### Revised `{aid}`", "", content_text(harness.state.artifacts[aid], harness.blobs), ""]
    (root / "CANDIDATE_ARCHITECTURES.md").write_text("\n".join(candidates), encoding="utf-8")

    crit = [
        "# Criticism summary", "",
        "All sixteen substantial candidates received two foreign-school assignments. Critic prose was recorded as scrutiny without warrants and could not change formal status.", "",
    ]
    for item in criticisms:
        crit += [
            f"## Round {item['round']}: {item['critic']} → `{item['target']}`", "",
            f"Target school: `{item['owner']}`. Critic route: `{item['model']}`. Critic artifact: `{item['critic_id']}`.", "",
            item["case"], "",
        ]
    (root / "CRITICISM_SUMMARY.md").write_text("\n".join(crit), encoding="utf-8")

    responsibility = """# Responsibility map

This is the strongest surviving conjectural boundary. The grounded bridge did not validate it as a final answer.

| Concern | Deterministic software or immutable policy | Bounded model responsibility | Interface |
|---|---|---|---|
| Routes, budgets, phase graph, permissions, retry ceilings, stopping | Compile and enact | None | Versioned policy plus route lease |
| Work scheduling | Select enabled typed transition and emit work order | None | `WorkOrder` with one task and capability set |
| Conjecture and reframing | Bound, persist, and admit | Generate open semantic proposals | Role-specific proposal contract |
| Evidence acquisition | Authorize connectors, log request/result, validate identity | Formulate query or inspect evidence | `EvidenceRequest` / `EvidenceResult` |
| Formal epistemic state | Register artifacts and warrants; verify; adjudicate; replay | Propose only | Canonical ontology contracts and guard result |
| Scratch | Persist separately; retrieve; cover; fence | Author provisional blocks and links | Advisory-context receipt; no promotion primitive |
| Criticism | Assign foreign critics; execute deterministic checks | Find semantic defects and counterexamples | Typed scrutiny or executable counterexample |
| Repair | Localize rejection; cap and log attempts/exhaustion | Repair only the rejected payload or subtree | Typed diagnostic and immutable repair budget |
| Final composition | Freeze catalog; validate ledger and claim uses | Ledger classification, composition, review | Canonical two-stage grounded bridge |
| Client interaction | Shared application services translate intent to commands | Optional conversational interpretation | CLI/MCP/chat adapters with equivalent events |

The key mechanism is a capability-typed, event-sourced control plane with a pure transition reducer. Models return proposals; they never return executable controller decisions. Open-endedness is preserved inside proposal content, query formulation, semantic criticism, analogy, decomposition and reframing.
"""
    (root / "RESPONSIBILITY_MAP.md").write_text(responsibility, encoding="utf-8")

    surviving = """# Surviving architecture

## Provisional recommendation

The strongest surviving family is a capability-typed, event-sourced control plane. A manifest compiler freezes a versioned workflow graph, school-to-route bindings, budgets, repair policies and stopping policy. A pure reducer consumes canonical state plus a typed event and emits the next enabled work order. Each model call receives one semantic responsibility and a closed capability set. Its output is data until deterministic guards register it as scratch, evidence, a conjecture, criticism, or a bridge record.

Consequential transitions become explicit `TransitionDecision` events containing prior-state digest, enabled transition, guard result, work-order ID, route lease, budget delta and next-state digest. Replay applies those events without re-running models. Evidence I/O is separated from inference; scratch stays in a different replay state and has no promotion operation; formal status remains a function of canonical artifacts, commitments, warrants and deterministic adjudication.

Determinism should stop at the semantic boundary. Models should retain discretion over problem decomposition, conjectural mechanism, analogy, reframing, evidence queries, semantic counterexamples, synthesis wording and whether available evidence warrants abstention. Attention ranking can be deterministic and replayable, but its policy remains a fallible search heuristic rather than truth authority.

## Alternatives that did not survive intact

Prompt refactoring or moving instructions to YAML fails because the model still interprets controller semantics. A fully deterministic planner fails because it closes the semantic search prematurely. A free-form agent with capability tools still leaves phase, retry and stop choices model-mediated. A model-proposed transition architecture survives only when proposals are non-authoritative and a deterministic guard makes the actual transition.

## Status

This is a synthesis of surviving formal conjectures and recorded criticism, not a successful Stage-B grounded composition. Both bounded bridge workflows failed closed, so the canonical final outcome remains partially answered.
"""
    (root / "SURVIVING_ARCHITECTURE.md").write_text(surviving, encoding="utf-8")

    implementation = """# Implementation sequence

1. Add characterization and adversarial tests around current scheduler, adapter, stop, scratch, bridge, replay, CLI, MCP and MiniReason behaviour.
2. Define immutable `WorkOrder`, `ProposalResult`, `GuardResult`, `TransitionDecision` and `StopDecision` records and a pure reducer. Run it in shadow mode against the existing scheduler.
3. Add a new manifest version that freezes controller version, workflow graph, explicit school-to-route bindings, capability grants and workflow-level retry policy. Keep v1-v3 loaders and replay unchanged.
4. Emit an event for every enabled, rejected, repaired, exhausted, advanced, paused, resumed and stopped transition. Add state-digest replay assertions.
5. Integrate scratch attention and evidence acquisition as explicit controller states. Converting scratch into a formal candidate must require a fresh typed model call and normal admission; no direct promotion API should exist.
6. Replace broad orchestration prompts role by role with bounded semantic work orders. Keep prompt text as presentation guidance where semantic judgment is desired.
7. Put CLI, MCP, MiniReason and future chat behind the same application services, with client-specific parsing outside the controller.
8. Retain the grounded two-stage bridge as the sole final composer; separately repair the observed compact-ledger handle confusion before production cutover.
"""
    (root / "IMPLEMENTATION_SEQUENCE.md").write_text(implementation, encoding="utf-8")

    tests = """# Test strategy

The central recommendation is falsified if model prose changes a route, budget, phase, retry bound, stop decision or formal status without a typed logged transition; if replay differs; if scratch becomes authoritative; or if different clients/providers produce different control transitions from the same canonical state and policy.

Required cases include phase-changing prompt injection; output selecting another route; malformed output; local repair and exhaustion; missing/conflicting evidence; interruption and continuation; historical replay; v1-v3 manifest compatibility; scratch attempting formal promotion; bridge composition introducing a fact absent from the ledger; CLI/MCP equivalence; and provider substitution under the same state machine. Assert event sequences, route leases, budget deltas, state hashes, retry counts, formal status and claim references—not merely schema validity.

Add reducer property tests, event-prefix replay at every transition, mutation tests that remove event emissions, capability-denial tests for forbidden controller fields, crash/restart tests between every write, and shadow-run differentials against legacy scheduler traces. The bridge regression suite must include the two observed failures: a contract label used as an event handle and a formal-artifact handle used in `scratch_handles`.

The pinned checkout's targeted existing suite passed: 41 tests in 0.89 seconds.
"""
    (root / "TEST_STRATEGY.md").write_text(tests, encoding="utf-8")

    open_questions = """# Open questions

- The right shared state-machine granularity across reasoning, code, simulation, proof and website workloads is not established by this run.
- Replayable attention policies can still encode brittle heuristics; operator override and policy-evaluation semantics remain open.
- A future manifest's exact compatibility promise and workflow-level retry field require an explicit version decision.
- Provider equivalence needs an oracle for control equivalence without requiring identical semantic proposals.
- Current implementation lacks native school-to-route binding and automatic scratch-to-Conj integration.
- The grounded bridge's compact handle contract failed twice despite schema repairs; whether prompt presentation, alias namespace design or contract ergonomics is the primary cause remains unresolved.
"""
    (root / "OPEN_QUESTIONS.md").write_text(open_questions, encoding="utf-8")

    terminal = json.loads((inquiry.RUN / "bridge-result.json").read_text())
    ledgers = list(harness.bridge_state.ledgers.values())
    ledger = ledgers[-1]
    final = [
        "# Final grounded answer", "",
        "Resolution: `partially_answered` at the experiment level; canonical bridge process status: `failure`.", "",
        "## Stage A ledger", "",
    ]
    for entry in ledger.entries:
        final += [entry.claim, "", f"Claim class: `{entry.claim_class.value}`. Ledger entry: `{entry.id}`.", ""]
    final += [
        "## Uncovered requirement", "",
        *(item.requirement for item in (ledger.uncovered_requirements or [])), "",
        "## Bridge outcome", "",
        f"Stage B did not produce a bridge output. The terminal failure is `{terminal['error_code']}`: {terminal['error_message']}", "",
        "DeepReason therefore does not provide a canonically grounded architectural answer from this run. The evidence map, rival candidates, criticisms and provisional surviving architecture are preserved separately, but must not be mistaken for successful grounded composition.", "",
        "## Confidence", "",
        "High confidence in the recorded process failure and replayable evidence; no bridge-justified confidence in the provisional recommendation as a final grounded answer.", "",
    ]
    (root / "FINAL_GROUNDED_ANSWER.md").write_text("\n".join(final), encoding="utf-8")


def main():
    harness = Harness(inquiry.RUN)
    if not any(
        content_text(a, harness.blobs) == TEST_RESULT
        for a in harness.state.artifacts.values()
    ):
        harness.create_artifact(
            TEST_RESULT, provenance=Provenance(role="import"),
            problem_id=inquiry.MAIN,
        )
        harness.record_measure(inputs=["targeted-tests", "exit:0", "passed:41"])
    initial, revised, criticisms, evidence = reconstruct(harness)
    counts = Counter(item["target"] for item in criticisms)
    substantial = [aid for values in initial.values() for aid in values] + [aid for values in revised.values() for aid in values]
    if len(substantial) != 16 or any(counts[aid] != 2 for aid in substantial):
        raise RuntimeError("foreign-school criticism coverage invariant failed")
    write_files(harness, initial, revised, criticisms, evidence)
    events = list(harness.log.read())
    calls = [event.llm for event in events if event.llm is not None]
    inquiry.dump_json(inquiry.ROOT / "TOKEN_ACCOUNTING.json", {
        "budget": inquiry.TOKEN_BUDGET,
        "logged_total": sum(call.tokens for call in calls),
        "calls": len(calls),
        "remaining": inquiry.TOKEN_BUDGET - sum(call.tokens for call in calls),
    })
    inquiry.dump_json(inquiry.ROOT / "terminal-result.json", json.loads((inquiry.RUN / "bridge-result.json").read_text()))
    inquiry.dump_json(inquiry.ROOT / "model-routes.json", {
        school["id"]: {"role": school["role"], "model": school["model"], "lens": school["lens"]}
        for school in inquiry.SCHOOLS
    })
    inquiry.dump_json(inquiry.ROOT / "inquiry-index.json", {
        "manifest_sha256": "04671601f2548ed8b675c72d5d442ad8bf4c59fb7e0be2386011aa516e1866d8",
        "main_problem": inquiry.MAIN, "initial": initial, "revised": revised,
        "criticism_count": len(criticisms),
        "evidence_artifacts": [item["artifact_id"] for item in evidence],
        "bridge_workflow_attempts": 2, "bridge_process_status": "failure",
        "run_root": str(inquiry.RUN.relative_to(inquiry.REPO)),
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
        "attention_receipts": len(replay.scratch_state.attention_receipts),
        "coverage_cycles": len(replay.scratch_state.coverage_cycles),
        "bridge_ledgers": len(replay.bridge_state.ledgers),
        "bridge_failures": len(replay.bridge_state.failures),
    })
    if not ok:
        raise RuntimeError("replay mismatch")


if __name__ == "__main__":
    main()
