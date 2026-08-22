"""The scope predicate sigma -- `declarative-scope.v1` (D-5, answered A).

Def 9.2 requires sigma to be "a total computable predicate over problem
records", C1-deterministic, with "embeddings may inform nomination, never
membership". D-5 chose a FIXED FINITE DSL over an arbitrary program artifact:
the tree already refuses model-authored Python without a certified container
(v1.6, `sandboxed_python_v1` fails closed), and choosing the program road would
have imported that refusal into scope membership.

The SHAPE is `declarative_numeric_v1`'s (`simulation/compiler.py`): a JSON
expression tree of typed leaves and `{"op", "args"}` nodes, validated whole
before anything runs, under the same depth and node bounds. What is deliberately
NOT reused is that module's second half -- it compiles to Python source for the
trusted verifier, and a predicate needs no code generation. Compiling to source
here would create a second authored-code execution path for no expressiveness.

Determinism is STRUCTURAL, not promised: the only inputs an expression can name
are the five fields of the `Problem` record. There is no leaf for artifact
state, status, the log, wall-clock, or randomness, so "same problem + state =
same answer" holds because nothing else is reachable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCOPE_SCHEMA = "declarative-scope.v1"

# Closed, and closed is the requirement rather than the current size: an open
# operation set would let an authored predicate name become quasi-semantics,
# and each one would need its own determinism and totality argument.
_BOOLEAN_OPS = frozenset({"and", "or", "not"})
_STRING_OPS = frozenset({"eq", "contains", "starts_with"})
_LIST_OPS = frozenset({"member", "any_contains", "empty"})
OPS: frozenset[str] = _BOOLEAN_OPS | _STRING_OPS | _LIST_OPS

# The whole evaluation domain: the `Problem` record and nothing else.
_FIELDS = frozenset({"id", "description", "trigger"})
_LISTS = frozenset({"criteria", "sources"})

_MAX_DEPTH = 16
_MAX_NODES = 512


class ScopeError(ValueError):
    """A typed refusal. Carries `code` so callers branch on a value rather
    than on message text, exactly as `ClaimDecodeError.code` is used."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class CompiledScope:
    """A fully validated predicate tree. Frozen because a scope document is
    artifact CONTENT: mutating a compiled scope after registration would
    detach the predicate from the content address that names it."""

    tree: Any


def _budget(state: dict, depth: int) -> None:
    if depth > _MAX_DEPTH:
        raise ScopeError("scope-too-deep", f"nesting exceeds {_MAX_DEPTH}")
    state["nodes"] += 1
    if state["nodes"] > _MAX_NODES:
        raise ScopeError("scope-too-large", f"node bound {_MAX_NODES} exceeded")


def _text(node: Any, state: dict, depth: int) -> tuple[str, Any]:
    _budget(state, depth)
    if not isinstance(node, dict):
        raise ScopeError("scope-not-an-expression", type(node).__name__)
    if set(node) == {"text"}:
        if not isinstance(node["text"], str):
            raise ScopeError("scope-text-not-a-string", type(node["text"]).__name__)
        return ("text", node["text"])
    if set(node) == {"field"}:
        if node["field"] not in _FIELDS:
            raise ScopeError("scope-field-unknown", repr(node["field"]))
        return ("field", node["field"])
    raise ScopeError("scope-not-a-string-expression", repr(sorted(node))[:120])


def _list(node: Any, state: dict, depth: int) -> tuple[str, Any]:
    _budget(state, depth)
    if not isinstance(node, dict) or set(node) != {"list"}:
        raise ScopeError("scope-not-a-list-expression", repr(node)[:120])
    if node["list"] not in _LISTS:
        raise ScopeError("scope-list-unknown", repr(node["list"]))
    return ("list", node["list"])


def _predicate(node: Any, state: dict, depth: int) -> tuple:
    _budget(state, depth)
    if not isinstance(node, dict):
        raise ScopeError("scope-not-an-expression", type(node).__name__)
    if set(node) == {"const"}:
        if not isinstance(node["const"], bool):
            raise ScopeError("scope-const-not-a-boolean", type(node["const"]).__name__)
        return ("const", node["const"])
    if set(node) != {"op", "args"}:
        raise ScopeError("scope-not-an-operation", repr(sorted(node))[:120])
    op, args = node["op"], node["args"]
    if not isinstance(op, str) or op not in OPS:
        raise ScopeError("scope-op-unsupported", repr(op))
    if not isinstance(args, list):
        raise ScopeError("scope-args-not-a-list", type(args).__name__)
    if op == "not":
        if len(args) != 1:
            raise ScopeError("scope-arity", "not takes one argument")
        return ("not", _predicate(args[0], state, depth + 1))
    if op in {"and", "or"}:
        if not args:
            raise ScopeError("scope-arity", f"{op} takes at least one argument")
        return (op, tuple(_predicate(a, state, depth + 1) for a in args))
    if op in _STRING_OPS:
        if len(args) != 2:
            raise ScopeError("scope-arity", f"{op} takes two arguments")
        return (op, _text(args[0], state, depth + 1), _text(args[1], state, depth + 1))
    if op == "empty":
        if len(args) != 1:
            raise ScopeError("scope-arity", "empty takes one argument")
        return ("empty", _list(args[0], state, depth + 1))
    if len(args) != 2:
        raise ScopeError("scope-arity", f"{op} takes two arguments")
    return (op, _list(args[0], state, depth + 1), _text(args[1], state, depth + 1))


def compile_scope(document: Any) -> CompiledScope:
    """Validate a scope document WHOLE, before anything evaluates it.

    Up-front validation is what makes sigma total: a predicate that could fail
    part-way through evaluation would make membership depend on which problem
    happened to be tested first.
    """
    if not isinstance(document, dict):
        raise ScopeError("scope-not-an-object", type(document).__name__)
    if set(document) != {"schema", "predicate"}:
        raise ScopeError("scope-document-shape", repr(sorted(document))[:120])
    if document["schema"] != SCOPE_SCHEMA:
        raise ScopeError("scope-schema-unknown", repr(document["schema"]))
    return CompiledScope(_predicate(document["predicate"], {"nodes": 0}, 0))


def _string(node: tuple, problem) -> str:
    if node[0] == "text":
        return node[1]
    if node[1] == "trigger":
        return problem.provenance.trigger.value
    return getattr(problem, node[1])


def _sequence(node: tuple, problem) -> list[str]:
    if node[1] == "criteria":
        return list(problem.criteria)
    return list(problem.provenance.from_)


def _evaluate(node: tuple, problem) -> bool:
    head = node[0]
    if head == "const":
        return node[1]
    if head == "not":
        return not _evaluate(node[1], problem)
    if head == "and":
        return all(_evaluate(a, problem) for a in node[1])
    if head == "or":
        return any(_evaluate(a, problem) for a in node[1])
    if head == "empty":
        return not _sequence(node[1], problem)
    if head in _STRING_OPS:
        left, right = _string(node[1], problem), _string(node[2], problem)
        if head == "eq":
            return left == right
        if head == "contains":
            return right in left
        return left.startswith(right)
    values, needle = _sequence(node[1], problem), _string(node[2], problem)
    if head == "member":
        return needle in values
    return any(needle in value for value in values)


def scope_admits(scope: CompiledScope, problem) -> bool:
    """Does sigma admit this problem? A pure function of the `Problem` record."""
    return _evaluate(scope.tree, problem)
