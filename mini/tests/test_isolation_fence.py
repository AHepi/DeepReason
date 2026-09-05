"""The isolation fence: mini must not reach into the larger harness.

Implements S1 (R1, R11) of the mini isolation programme. R1 is the operator's
own "mini needs to be tested in isolation", and R11 is "test this new config
in isolation without the larger harness activated". The fence is a TEST rather
than a convention -- that is the modularity law's "enforced" clause, a check
that can fail.

WHAT THIS PROVES AND WHAT IT DOES NOT. SPEC.md S1 names eleven packages as
"the larger harness". Four of them -- adjudication, bridge, capabilities and
workflow.transaction_service -- are loaded by the very modules S1 allows mini
to use, because the event ontology imports its bridge and capability payload
types and the harness imports the adjudicator's edge builders. Those modules
ARE the record rather than the harness around it, which is why they are
allowed. So a fence reading "none of the eleven is ever imported" could not be
passed without changing two frozen surfaces, and would be a fence about
Python's import graph rather than about what mini uses.

The three tests below measure what can be true and still bites:

1. mini's own sources import no fenced module directly;
2. importing mini adds no fenced package beyond what the allowed record
   modules already bring;
3. a mini run imports no fenced module that was not loaded when it started --
   the one that catches a lazy `import deepreason.scheduler` inside a
   function, which the first two would both miss.

What none of them proves is that no code inside those four packages ever
executes. Their payload types are constructed by the record itself. Proving
non-execution is a different instrument and is not built here.
"""

import ast
import json
import pathlib
import subprocess
import sys

from minireason.call import MockEndpoint

# SPEC.md S1's list, verbatim. It says what mini must not USE.
FENCED = (
    "deepreason.scheduler",
    "deepreason.qualification",
    "deepreason.capabilities",
    "deepreason.amendment",
    "deepreason.bridge",
    "deepreason.evaluation",
    "deepreason.adjudication",
    "deepreason.application.text_runs",
    "deepreason.calculus",
    "deepreason.workflow.transaction_service",
    "deepreason.schools",
)

# S1's other list: the record itself, which mini MAY use.
ALLOWED = (
    "deepreason.harness",
    "deepreason.ontology",
    "deepreason.log.event_log",
    "deepreason.invariants",
    "deepreason.programs",
    "deepreason.informal.skeleton",
    "deepreason.rules.guards",
    "deepreason.rules.warrants",
    "deepreason.run_manifest",
    "deepreason.llm.wire",
    "deepreason.llm.contracts",
    "deepreason.llm.firewall",
    "deepreason.llm.profiles",
)

_MINI = pathlib.Path(__file__).resolve().parents[1] / "minireason"
_REPO = pathlib.Path(__file__).resolve().parents[2]


def _is_fenced(name: str) -> str | None:
    for fenced in FENCED:
        if name == fenced or name.startswith(fenced + "."):
            return fenced
    return None


_CLOSURE_PROGRAM = """
import importlib, json, sys
for name in %r:
    importlib.import_module(name)
loaded = {f for f in %r for k in sys.modules if k == f or k.startswith(f + '.')}
print(json.dumps(sorted(loaded)))
"""


def _fenced_closure(modules: tuple[str, ...]) -> set[str]:
    """What of FENCED is loaded after importing `modules`, in a FRESH
    interpreter -- this process has already imported everything."""

    program = _CLOSURE_PROGRAM % (list(modules), list(FENCED))
    done = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        cwd=str(_REPO),
    )
    assert done.returncode == 0, done.stderr[-3000:]
    return set(json.loads(done.stdout.strip().splitlines()[-1]))


def test_mini_imports_no_fenced_module_directly():
    """Part 1: mini reaches for nothing in the larger harness.

    Relative imports are resolved rather than substring-matched: `from
    ..bridge.retry import X` walks straight past a grep for the dotted name
    (`docs/map/SCHEMA.md`'s check-writing rule 3).
    """
    violations = []
    for path in sorted(_MINI.rglob("*.py")):
        package = "minireason" + "".join(
            f".{part}" for part in path.relative_to(_MINI).parts[:-1]
        )
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = package.rsplit(".", node.level - 1)[0] if node.level > 1 else package
                    names = [f"{base}.{node.module}" if node.module else base]
                elif node.module:
                    names = [node.module]
            for name in names:
                fenced = _is_fenced(name)
                if fenced is not None:
                    violations.append(
                        f"{path.relative_to(_REPO)}:{node.lineno}: {name} "
                        f"(fenced: {fenced})"
                    )
    assert not violations, "mini imports the larger harness directly:\n" + "\n".join(
        violations
    )


def test_importing_mini_adds_no_fenced_package():
    """Part 2: mini adds nothing to the closure the record already carries.

    The comparison is against ARM A rather than against the empty set,
    because four of the eleven arrive through modules S1 allows. Measured in
    `experiments/2026-09-05-change-mini-isolation-programme/proof/
    fence_arms.txt`.
    """
    already = _fenced_closure(ALLOWED)
    with_mini = _fenced_closure(("minireason.loop",))
    added = sorted(with_mini - already)
    assert added == [], (
        "importing mini pulls in fenced packages the record modules do not: "
        f"{added}"
    )


def test_a_mini_run_imports_no_new_fenced_module(tmp_path):
    """Part 3: nothing fenced is imported DURING a run.

    This is the part a lazy import inside a function cannot walk past. The run
    is driven by the deterministic stub endpoint, so it needs no key and no
    network.
    """
    from minireason.loop import run

    before = {
        name
        for name in list(sys.modules)
        if _is_fenced(name) is not None
    }

    def endpoint_fn(prompt):
        return json.dumps(
            {
                "candidates": [
                    {
                        "content": json.dumps(
                            {
                                "claim": "claim 1",
                                "mechanism": "mechanism 1",
                                "forbidden": [
                                    {
                                        "case": "must state a mechanism",
                                        "eval": "program:json-wf",
                                    }
                                ],
                            }
                        ),
                        "typicality": 0.5,
                    }
                ]
            }
        )

    run(
        [("pi-0", "why?")],
        MockEndpoint(endpoint_fn),
        budget=200_000,
        root=tmp_path / "run",
        max_cycles=2,
    )

    after = {
        name
        for name in list(sys.modules)
        if _is_fenced(name) is not None
    }
    assert after - before == set(), (
        "a mini run imported the larger harness while running: "
        f"{sorted(after - before)}"
    )
