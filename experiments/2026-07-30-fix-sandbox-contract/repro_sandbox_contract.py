"""Reproduce D2: the sandboxed_python_v1 contract is enforced but never shown.

Three parts, all offline:

  1. Render the conjecturer wire schema exactly as the adapter serialises it
     into the prompt (adapter.py:764) and search it for the words the
     validator requires.
  2. Feed the field run's own recorded model_source to the validator.
  3. Show the second, latent denial: a program that satisfies the validator
     still fails when a requested observable is not a key of what simulate
     returns.

Run from the repository root:
    python3 experiments/2026-07-30-fix-sandbox-contract/repro_sandbox_contract.py
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from deepreason.llm.wire import (
    AliasTable,
    ConjecturerTurnWireContractV5,
    ConjecturerTurnWireContractV6,
)
from deepreason.simulation.compiler import validate_sandboxed_python_source

FIELD_ROOT = Path(
    "experiments/live_research_2026-07-29/openchallenge/runs"
    "/run-27b80f26bd398c718360e97e2a403593"
)
CONTRACT_WORDS = ("simulate", "inputs", "rng")


def _schema_text(contract) -> str:
    # The adapter serialises the whole schema, sorted, into the prompt.
    return json.dumps(contract.model_json_schema(), sort_keys=True)


def part_one_pack_text() -> None:
    print("== 1. what the pack says about model_source ==")
    contracts = {
        "conjecturer.turn.v5": ConjecturerTurnWireContractV5(
            reasoning=False,
            aliases=AliasTable({"SRC_001": "c1"}),
            maximum_simulation_proposals=1,
        ),
        "conjecturer.turn.v6": ConjecturerTurnWireContractV6(
            reasoning=False,
            aliases=AliasTable({"SRC_001": "c1"}),
            simulation_enabled=True,
            maximum_simulation_proposals=1,
        ),
    }
    for name, contract in contracts.items():
        text = _schema_text(contract)
        counts = {word: text.count(word) for word in CONTRACT_WORDS}
        node = contract.model_json_schema()["$defs"]["SimulationProposalWireV1"]
        print(f"  {name}: {len(text)} bytes of schema")
        print(f"    model_source          -> {json.dumps(node['properties']['model_source'], sort_keys=True)}")
        print(f"    requested_observables -> {json.dumps(node['properties']['requested_observables'], sort_keys=True)}")
        print(f"    occurrences {counts}")

    print("  the same question asked of the field run's own committed packs:")
    for blob in sorted(FIELD_ROOT.joinpath("blobs").rglob("*")):
        if not blob.is_file():
            continue
        raw = blob.read_bytes()
        if b"simulation_proposals" not in raw or len(raw) < 20_000:
            continue
        counts = {word: raw.count(word.encode()) for word in CONTRACT_WORDS}
        print(f"    blob {blob.name[:8]} ({len(raw)} bytes) occurrences {counts}")


def part_two_field_program() -> None:
    print("== 2. the field run's recorded model_source, through the validator ==")
    from deepreason.harness import Harness

    harness = Harness(FIELD_ROOT, read_only=True)
    (proposal,) = [
        value
        for value in harness.capability_state.proposals.values()
        if type(value).__name__ == "SimulationProposalV1"
    ]
    body = ast.parse(proposal.model_source).body
    print(f"    request_identifier    = {proposal.request_identifier}")
    print(f"    simulation_mode       = {proposal.simulation_mode}")
    print(f"    requested_observables = {proposal.requested_observables}")
    print(f"    top-level statements  = {len(body)}")
    try:
        validate_sandboxed_python_source(proposal.model_source)
    except ValueError as error:
        print(f"    validator             -> ValueError({str(error)!r})")
    else:
        print("    validator             -> accepted")


def part_three_latent_observable() -> None:
    print("== 3. the latent second denial: an undeclarable observable ==")
    conformant = (
        "def simulate(inputs, rng):\n"
        "    return {'value': inputs['parameters'].get('base', 2) ** 2}\n"
    )
    try:
        validate_sandboxed_python_source(conformant)
        print("    a single simulate(inputs, rng) module -> accepted by the validator")
    except ValueError as error:
        print(f"    unexpected: {error}")

    import hashlib

    from deepreason.verification.contained import ContainedSimulationBackend
    from deepreason.verification.simulation import SimulationRequest
    from deepreason.workloads.code import SimulationSpec

    class _Blobs(dict):
        def put(self, data: bytes) -> str:
            ref = hashlib.sha256(data).hexdigest()
            self[ref] = data
            return ref

        def get(self, ref: str) -> bytes:
            return self[ref]

    if not ContainedSimulationBackend.containment_available():
        print("    host cannot contain; the runner half of part 3 is skipped")
        return

    blobs = _Blobs()
    inputs = json.dumps(
        [{"parameter_set": "default", "parameters": {"base": 2}, "sealed_inputs": {}}]
    ).encode("utf-8")
    checker = b"def check(input_item, seed, output):\n    return {'pass': True}\n"
    backend = ContainedSimulationBackend(
        toolchain_id="python@contained-repro",
        maximum_wall_ms=20_000,
        maximum_memory_bytes=512 * 1024 * 1024,
    )
    # The field run's own declared observable name, against a program that
    # the validator accepts: the second stage is what rejects it.
    request = SimulationRequest(
        source_ref=blobs.put(conformant.encode("utf-8")),
        spec=SimulationSpec(
            entry="simulate",
            seed_set=(7,),
            inputs_ref=blobs.put(inputs),
            observables=("stdout",),
            checker_ref=blobs.put(checker),
            deterministic_step_limit=100_000,
            sample_limit=8,
            toolchain_id="python@contained-repro",
        ),
        maximum_output_bytes=65_536,
    )
    result = backend.verify(request, blobs)
    print(f"    requested_observables  ['stdout']  (the field run's)")
    print(f"    contained runner       -> verdict={result.verdict!r} trace={result.trace}")


if __name__ == "__main__":
    part_one_pack_text()
    part_two_field_program()
    part_three_latent_observable()
