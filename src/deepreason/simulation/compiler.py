"""Compile a finite numeric DSL without granting model-authored operations.

``declarative_numeric_v1`` is JSON data, not Python.  This module validates the
entire expression tree and emits the small Python function accepted by the
existing trusted simulation verifier.  The generated program can only read
declared values from ``parameters`` or ``sealed_inputs`` and combine them with
a fixed arithmetic vocabulary.

``sandboxed_python_v1`` is only syntax-checked here.  It is never eligible for
the local runner: execution additionally requires the manifest-bound certified
container profile.
"""

from __future__ import annotations

import ast
import json
import math
import re
from dataclasses import dataclass
from typing import Any

from deepreason.canonical import canonical_json

_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
_MAX_DEPTH = 24
_MAX_NODES = 4_096
_MAX_LITERAL_MAGNITUDE = 10**100


class DeclarativeSimulationError(ValueError):
    """The semantic numeric program falls outside the trusted DSL."""


@dataclass
class _Budget:
    nodes: int = 0

    def take(self, depth: int) -> None:
        if depth > _MAX_DEPTH:
            raise DeclarativeSimulationError("numeric expression nesting is too deep")
        self.nodes += 1
        if self.nodes > _MAX_NODES:
            raise DeclarativeSimulationError("numeric expression node bound exceeded")


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise DeclarativeSimulationError(
            f"{label} requires exactly {', '.join(sorted(expected))}"
        )


def _constant(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int):
        if abs(value) > _MAX_LITERAL_MAGNITUDE:
            raise DeclarativeSimulationError("integer literal magnitude is too large")
        return repr(value)
    if isinstance(value, float):
        if not math.isfinite(value) or abs(value) > _MAX_LITERAL_MAGNITUDE:
            raise DeclarativeSimulationError("floating-point literal must be finite and bounded")
        return repr(value)
    raise DeclarativeSimulationError("numeric constants must be finite numbers or booleans")


def _input_path(value: Any) -> str:
    if not isinstance(value, str):
        raise DeclarativeSimulationError("input reference must be a dotted string")
    parts = value.split(".")
    if len(parts) < 2 or parts[0] not in {"parameters", "sealed_inputs"}:
        raise DeclarativeSimulationError(
            "input reference must begin with parameters or sealed_inputs"
        )
    if any(_NAME.fullmatch(part) is None for part in parts[1:]):
        raise DeclarativeSimulationError("input reference contains an invalid segment")
    expression = "inputs"
    for part in parts:
        expression += f"[{part!r}]"
    return expression


def _compile_expression(value: Any, *, budget: _Budget, depth: int) -> str:
    budget.take(depth)
    if not isinstance(value, dict):
        raise DeclarativeSimulationError("every numeric expression must be an object")
    if set(value) == {"const"}:
        return _constant(value["const"])
    if set(value) == {"input"}:
        return _input_path(value["input"])
    _exact_keys(value, {"op", "args"}, "operation")
    operation = value["op"]
    arguments = value["args"]
    if not isinstance(operation, str) or not isinstance(arguments, list):
        raise DeclarativeSimulationError("operation and args have invalid types")
    compiled = [
        _compile_expression(item, budget=budget, depth=depth + 1)
        for item in arguments
    ]
    if operation in {"neg", "abs"}:
        if len(compiled) != 1:
            raise DeclarativeSimulationError(f"{operation} requires one argument")
        return (
            f"(-({compiled[0]}))"
            if operation == "neg"
            else f"abs({compiled[0]})"
        )
    if operation in {"sub", "div", "lt", "le", "gt", "ge", "eq"}:
        if len(compiled) != 2:
            raise DeclarativeSimulationError(f"{operation} requires two arguments")
        symbol = {
            "sub": "-",
            "div": "/",
            "lt": "<",
            "le": "<=",
            "gt": ">",
            "ge": ">=",
            "eq": "==",
        }[operation]
        return f"(({compiled[0]}) {symbol} ({compiled[1]}))"
    if operation in {"add", "mul"}:
        if not compiled:
            raise DeclarativeSimulationError(f"{operation} requires at least one argument")
        symbol = "+" if operation == "add" else "*"
        return "(" + f" {symbol} ".join(f"({item})" for item in compiled) + ")"
    if operation in {"min", "max"}:
        if not compiled:
            raise DeclarativeSimulationError(f"{operation} requires at least one argument")
        return f"{operation}({', '.join(compiled)})"
    if operation == "select":
        if len(compiled) != 3:
            raise DeclarativeSimulationError("select requires condition, true, false")
        return f"(({compiled[1]}) if ({compiled[0]}) else ({compiled[2]}))"
    raise DeclarativeSimulationError(f"unsupported numeric operation {operation!r}")


def compile_declarative_numeric(
    model_source: str,
    requested_observables: tuple[str, ...],
) -> bytes:
    """Return harness-authored Python for one fully validated JSON program."""

    try:
        document = json.loads(model_source)
    except json.JSONDecodeError as error:
        raise DeclarativeSimulationError(
            f"declarative numeric source is not JSON: {error.msg}"
        ) from error
    if not isinstance(document, dict):
        raise DeclarativeSimulationError("declarative numeric source must be an object")
    _exact_keys(document, {"schema", "observables"}, "numeric program")
    if document["schema"] != "declarative-numeric.v1":
        raise DeclarativeSimulationError("unknown declarative numeric schema")
    observables = document["observables"]
    if not isinstance(observables, dict) or not observables:
        raise DeclarativeSimulationError("numeric program requires observables")
    if any(not isinstance(name, str) or _NAME.fullmatch(name) is None for name in observables):
        raise DeclarativeSimulationError("numeric program has an invalid observable name")
    if tuple(sorted(observables)) != tuple(sorted(requested_observables)):
        raise DeclarativeSimulationError(
            "numeric program observables differ from the semantic request"
        )
    budget = _Budget()
    lines = ["def simulate(inputs, rng):", "    return {"]
    for name in sorted(observables):
        expression = _compile_expression(observables[name], budget=budget, depth=0)
        lines.append(f"        {name!r}: {expression},")
    lines.extend(("    }", ""))
    return "\n".join(lines).encode("utf-8")


_FORBIDDEN_CALLS = {
    "compile",
    "delattr",
    "eval",
    "exec",
    "getattr",
    "globals",
    "input",
    "locals",
    "open",
    "setattr",
    "vars",
}
_FORBIDDEN_ROOTS = {
    "asyncio",
    "ctypes",
    "importlib",
    "inspect",
    "marshal",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "requests",
    "shutil",
    "socket",
    "subprocess",
    "sys",
    "threading",
    "urllib",
}


def validate_sandboxed_python_source(source: str) -> None:
    """Validate semantic Python shape; this does not authorise execution."""

    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise ValueError(f"sandboxed Python is not parseable: {error.msg}") from error
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError("sandboxed Python must define exactly one simulate function")
    function = tree.body[0]
    if (
        function.name != "simulate"
        or function.decorator_list
        or function.returns is not None
        or function.args.posonlyargs
        or function.args.vararg is not None
        or function.args.kwarg is not None
        or function.args.kwonlyargs
        or function.args.defaults
        or tuple(argument.arg for argument in function.args.args) != ("inputs", "rng")
    ):
        raise ValueError("sandboxed Python requires def simulate(inputs, rng)")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            raise ValueError("imports and scope mutation are forbidden")
        if isinstance(node, ast.Name):
            if node.id.startswith("_") or node.id in _FORBIDDEN_CALLS | _FORBIDDEN_ROOTS:
                raise ValueError(f"forbidden Python name {node.id!r}")
        if isinstance(node, ast.Attribute):
            root = node
            while isinstance(root, ast.Attribute):
                if root.attr.startswith("_"):
                    raise ValueError("private and dunder attribute traversal is forbidden")
                root = root.value
            if isinstance(root, ast.Name) and root.id in _FORBIDDEN_ROOTS:
                raise ValueError(f"forbidden Python capability root {root.id!r}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _FORBIDDEN_CALLS:
                raise ValueError(f"forbidden Python call {node.func.id!r}")
    # A canonical parse is intentionally computed so syntax acceptance is
    # deterministic across equivalent source text; no compilation occurs.
    canonical_json({"ast": ast.dump(tree, annotate_fields=True, include_attributes=False)})


__all__ = [
    "DeclarativeSimulationError",
    "compile_declarative_numeric",
    "validate_sandboxed_python_source",
]
