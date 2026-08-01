"""Offline contracts for the trusted declarative simulation compiler."""

from __future__ import annotations

import json

import pytest

from deepreason.llm.wire import (
    SIMULATION_MODEL_SOURCE_CONTRACT,
    SIMULATION_REQUESTED_OBSERVABLES_CONTRACT,
    AliasTable,
    ConjecturerTurnWireContractV5,
    ConjecturerTurnWireContractV6,
)
from deepreason.simulation.compiler import (
    DeclarativeSimulationError,
    compile_declarative_numeric,
    validate_sandboxed_python_source,
)
from deepreason.verification.contained import CONTAINED_WORKER_SOURCE_V1


def _program(expression, *, name="x") -> str:
    return json.dumps(
        {
            "schema": "declarative-numeric.v1",
            "observables": {name: expression},
        }
    )


def test_declarative_numeric_compiles_only_the_fixed_expression_vocabulary():
    source = compile_declarative_numeric(
        _program(
            {
                "op": "div",
                "args": [
                    {"input": "parameters.weight_bytes"},
                    {"const": 2},
                ],
            }
        ),
        ("x",),
    ).decode()

    assert source.startswith("def simulate(inputs, rng):")
    assert "inputs['parameters']['weight_bytes']" in source
    assert " / " in source
    assert "import" not in source


@pytest.mark.parametrize(
    "document",
    [
        {"schema": "declarative-numeric.v1", "observables": {"x": {"input": "/etc/passwd"}}},
        {"schema": "declarative-numeric.v1", "observables": {"x": {"op": "exec", "args": []}}},
        {"schema": "declarative-numeric.v1", "observables": {"x": {"const": float("inf")}}},
        {
            "schema": "declarative-numeric.v1",
            "observables": {"x": {"const": 1}},
            "command": "python unsafe.py",
        },
    ],
)
def test_declarative_numeric_rejects_authority_and_unbounded_values(document):
    with pytest.raises(DeclarativeSimulationError):
        compile_declarative_numeric(json.dumps(document), ("x",))


def test_declarative_numeric_requires_exact_declared_observables():
    with pytest.raises(DeclarativeSimulationError, match="observables differ"):
        compile_declarative_numeric(_program({"const": 1}, name="y"), ("x",))


@pytest.mark.parametrize(
    "source",
    [
        "import os\ndef simulate(inputs, rng):\n    return {'x': 1}\n",
        "def simulate(inputs, rng):\n    return open('/etc/passwd').read()\n",
        "def simulate(inputs, rng):\n    return inputs.__class__\n",
        "def simulate(inputs, rng, command=None):\n    return {}\n",
        "def helper():\n    return 1\ndef simulate(inputs, rng):\n    return {}\n",
    ],
)
def test_sandboxed_python_contract_rejects_operational_escape_surfaces(source):
    with pytest.raises(ValueError):
        validate_sandboxed_python_source(source)


def test_sandboxed_python_validation_is_not_execution_authority():
    validate_sandboxed_python_source(
        "def simulate(inputs, rng):\n    return {'x': inputs['parameters']['x']}\n"
    )


def test_the_conjecturer_is_shown_the_program_contract_the_harness_enforces():
    """Regression (tensorrank run-27b80f26bd398c718360e97e2a403593): the model
    submitted an 11-statement script and was denied invalid_model_program.
    The pack described model_source only as a bounded string, so neither the
    shape the sandbox validator requires nor the rule binding
    requested_observables to the program's own output reached the model
    anywhere.  Disclosure and enforcement are asserted together so that
    changing one without the other fails here rather than in the field.
    """

    signature = "def simulate(inputs, rng)"
    assert signature in SIMULATION_MODEL_SOURCE_CONTRACT
    # The disclosed signature is the one the validator admits ...
    validate_sandboxed_python_source(f"{signature}:\n    return {{'value': 1}}\n")
    # ... and the field run's shape, that function with a script around it,
    # is the one it refuses.
    with pytest.raises(ValueError, match="exactly one simulate function"):
        validate_sandboxed_python_source(
            f"{signature}:\n    return {{'value': 1}}\n"
            "result = simulate({'parameters': {}}, None)\n"
        )

    # The consequence the observables text names is the runner's own wording.
    assert "declared observable missing" in SIMULATION_REQUESTED_OBSERVABLES_CONTRACT
    assert "declared observable missing" in CONTAINED_WORKER_SOURCE_V1
    # The same set rule, at the declarative site the text also describes.
    with pytest.raises(DeclarativeSimulationError, match="observables differ"):
        compile_declarative_numeric(_program({"const": 1}, name="value"), ("stdout",))

    for contract in (
        ConjecturerTurnWireContractV5(
            reasoning=False,
            aliases=AliasTable({"SRC_001": "c1"}),
            maximum_simulation_proposals=1,
        ),
        ConjecturerTurnWireContractV6(
            reasoning=False,
            aliases=AliasTable({"SRC_001": "c1"}),
            simulation_enabled=True,
            maximum_simulation_proposals=1,
        ),
    ):
        # The adapter serialises this whole schema into the prompt, so what it
        # carries is exactly what the conjecturer is shown.
        pack = json.dumps(contract.model_json_schema(), sort_keys=True)
        assert signature in pack
        assert "sealed_inputs" in pack
        assert SIMULATION_REQUESTED_OBSERVABLES_CONTRACT in pack
