"""Execution oracle — the *acting* evaluator (prototype).

The harness's criticism is normally either a well-formedness program (skeleton-wf,
lineage_ref — internal) or a rubric judge (an LLM marking an LLM's homework —
self-referential). Neither TESTS a conjecture against reality; the run's
`evidence_lambda` sits at None. This module is the seam that closes that gap:
a `program:` commitment whose verdict comes from RUNNING the candidate against
fixed tests. A conjecture that proposes a function is refuted by *executing it
and observing the wrong output* — a warrant from reality, not from argument.
It generalizes what `scripts/cachebench.py` did once by hand (docs/CACHE_DESIGN.md:
a real measurement that refuted a design and lifted λ 0.0 -> 0.67).

Determinism (§0): the candidate runs against FIXED inputs under a DETERMINISTIC
step bound (Python line-event count, never wall-clock), and an AST int-literal
cap forbids C-level range/collection bombs — so the verdict is a pure function
of content and replays byte-for-byte. `overrun` (not a wall-clock condition, §1)
is reserved for a malformed spec.

Security: the candidate is UNTRUSTED model output, so it is AST-guarded (no
imports, no underscore/dunder names or attributes, no `**`, no huge int
literals, no global/nonlocal) and executed with a locked, whitelist
`__builtins__` — the same escape-family guard programs.py uses for predicates,
extended to a callable. This is a PROTOTYPE sandbox: a production evaluator must
run in a subprocess/container with real resource limits. See tests/test_oracle.py
for the blocked-escape cases.
"""

import ast
import builtins as _builtins
import json
import sys

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology.commitment import Budget, Commitment

PASS, FAIL, OVERRUN = "pass", "fail", "overrun"

EXEC_PROGRAM = "exec_oracle"
_STEP_LIMIT_DEFAULT = 100_000
_INT_LITERAL_CAP = 1_000_000  # forbid range()/collection bombs the step bound can't see

# Whitelist builtins (mirrors programs._SAFE_NAMES, sufficient for pure functions).
_ALLOWED = (
    "len range min max abs sum sorted enumerate zip map filter list dict set "
    "tuple str int float bool any all reversed round chr ord divmod isinstance"
).split()
_SAFE_BUILTINS = {name: getattr(_builtins, name) for name in _ALLOWED}


class _StepExceeded(Exception):
    """The candidate ran past its deterministic line-event budget."""


def _guard(tree: ast.AST) -> None:
    """Reject the untrusted-code escape family (same shape as programs._validate_
    predicate, extended for a def+body): no imports, no underscore names/attrs
    (blocks the .__class__... walk), no ** (int bomb), no global/nonlocal, and
    no integer literal above the cap (blocks range(10**9)-style C-level hangs the
    line-event bound cannot see)."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("imports are not allowed")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError(f"underscore attribute .{node.attr}")
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise ValueError(f"underscore name {node.id}")
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            raise ValueError("global/nonlocal not allowed")
        if isinstance(node, ast.Pow):
            raise ValueError("** not allowed (int bomb)")
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and abs(
            node.value
        ) > _INT_LITERAL_CAP:
            raise ValueError(f"integer literal exceeds cap {_INT_LITERAL_CAP}")


def _short(value: object, limit: int = 120) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + "…"


def run(source: str, entry: str, tests: list, step_limit: int = _STEP_LIMIT_DEFAULT):
    """Execute candidate ``source``, call ``entry`` on each test's positional
    args, and PASS iff every result equals the expected output. Deterministic
    (fixed tests + line-event bound); returns (verdict, trace)."""
    try:
        tree = ast.parse(source)
        _guard(tree)
    except (SyntaxError, ValueError) as e:
        return FAIL, {"error": f"unsafe or unparseable candidate: {e}"}

    namespace: dict = {"__builtins__": dict(_SAFE_BUILTINS)}
    try:
        exec(compile(tree, "<candidate>", "exec"), namespace)  # noqa: S102 - guarded+sandboxed
    except Exception as e:  # noqa: BLE001 - a bad candidate is a failed verdict, not a crash
        return FAIL, {"error": f"candidate did not load: {e}"}
    fn = namespace.get(entry)
    if not callable(fn):
        return FAIL, {"error": f"entry point {entry!r} is not defined"}

    steps = [0]

    def _tracer(frame, event, arg):
        if event == "line":
            steps[0] += 1
            if steps[0] > step_limit:
                raise _StepExceeded()
        return _tracer

    previous = sys.gettrace()
    sys.settrace(_tracer)
    try:
        for i, case in enumerate(tests):
            args = case.get("in", [])
            try:
                got = fn(*args)
            except _StepExceeded:
                return FAIL, {"case": i, "error": "step limit exceeded", "step_limit": step_limit}
            except Exception as e:  # noqa: BLE001 - candidate raised => failed test
                return FAIL, {"case": i, "error": f"raised {type(e).__name__}: {e}"}
            if got != case.get("out"):
                return FAIL, {
                    "case": i, "input": args, "expected": case.get("out"), "got": _short(got)
                }
    finally:
        sys.settrace(previous)
    return PASS, {"cases_passed": len(tests), "steps": steps[0]}


def run_from_spec(source: str, budget) -> tuple:
    """programs.py entry point: pull the frozen {entry, tests, step_limit} spec
    from the commitment budget and execute ``source`` against it."""
    try:
        spec = json.loads(budget.extra.get("spec", "{}")) if budget and budget.extra else {}
    except (ValueError, AttributeError):
        spec = {}
    if not spec.get("tests") or not spec.get("entry"):
        return OVERRUN, {"error": "exec-oracle spec missing entry/tests"}
    return run(source, spec["entry"], spec["tests"], int(spec.get("step_limit", _STEP_LIMIT_DEFAULT)))


def exec_oracle_commitment(entry: str, tests: list, step_limit: int = _STEP_LIMIT_DEFAULT) -> Commitment:
    """Build a content-addressed exec-oracle commitment (like hv-floor/lineage-ref):
    the entry point + fixed test cases are frozen into the id, so verdicts are
    replay-stable and retuning the tests only affects future instantiations. A
    conjecture carrying this commitment is refuted by RUNNING it and failing a
    test — criticism grounded in execution."""
    spec = {"entry": entry, "tests": tests, "step_limit": step_limit}
    digest = sha256_hex(canonical_json(spec))[:12]
    return Commitment(
        id=f"exec-oracle@{digest}",
        eval=f"program:{EXEC_PROGRAM}",
        budget=Budget(extra={"spec": json.dumps(spec, sort_keys=True)}),
    )
