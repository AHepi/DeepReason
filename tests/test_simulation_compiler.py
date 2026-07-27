"""Offline contracts for the trusted declarative simulation compiler."""

from __future__ import annotations

import json

import pytest

from deepreason.simulation.compiler import (
    DeclarativeSimulationError,
    compile_declarative_numeric,
    validate_sandboxed_python_source,
)


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
