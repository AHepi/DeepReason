"""Shape buys nothing: no rank, admission, immunity or refutation path reads
the commitment-proposal kind, and no mini schema carries a field that could
buy standing.

Implements S4's architecture accept (C9, the formalism-optional law; R13,
"within mini, criticism can't overturn anything"). The window's ruling of
2026-09-05, verbatim: "A test enumerates every mini schema for score, rank,
weight, confidence, priority, authority, severity -- RED if one appears."

Three limbs. (1) The authority side -- the full harness's rank, adjudication,
rules, event application and replay validation, and mini's own admission,
registration and refutation functions -- never names the kind or the record
marker: a path that cannot name a thing cannot rank it. (2) Every mini schema,
enumerated, carries none of the seven fields. (3) Behaviourally: recording a
proposal about a standing conjecture and about a refuted one changes neither
status, and the run's survivors are what they were.
"""

import ast
import json
import pathlib

import pytest

from minireason.call import MockEndpoint
from minireason.loop import Session, run

REPO = pathlib.Path(__file__).resolve().parents[2]
MINI = REPO / "mini" / "minireason"

# The names a generation-side kind must never reach.
_KIND_NAMES = ("commitment-proposal", "mini:record", "mini.commitment", "mini.criticism")

# The full harness's authority side: rank and status are decided here and
# nowhere else. Total over these paths: not one of the names may appear.
_AUTHORITY_PATHS = (
    "src/deepreason/scheduler",
    "src/deepreason/adjudication",
    "src/deepreason/rules",
    "src/deepreason/harness.py",
    "src/deepreason/invariants.py",
    "src/deepreason/verification",
    "src/deepreason/capabilities/state.py",
)

# Mini's own authority functions: the ones that admit, register, guard or
# refute. Named, because loop.py also DISPATCHES and may legitimately name a
# seat there (from T5 on).
_MINI_AUTHORITY_FUNCTIONS = (
    "register_commitments",
    "build_candidate",
    "guard_scope",
    "admit_candidate",
    "register_candidates",
    "refute",
    "_prepare_controlled_candidates",
    "_admit_controlled_candidates",
    "_mini_guard_finding",
    "_conjecture_stage",
)

_FORBIDDEN_FIELDS = {"score", "rank", "weight", "confidence", "priority", "authority", "severity"}


def _sources(path: pathlib.Path):
    return sorted(path.rglob("*.py")) if path.is_dir() else [path]


def test_limb1_no_authority_path_names_the_kind():
    offenders = []
    for rel in _AUTHORITY_PATHS:
        for path in _sources(REPO / rel):
            text = path.read_text(encoding="utf-8")
            for name in _KIND_NAMES:
                if name in text:
                    offenders.append(f"{path.relative_to(REPO)}: {name}")
    for module in ("loop.py", "checks.py", "gate.py"):
        source = (MINI / module).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and (
                module != "loop.py" or node.name in _MINI_AUTHORITY_FUNCTIONS
            ):
                body = ast.get_source_segment(source, node) or ""
                for name in _KIND_NAMES:
                    if name in body:
                        offenders.append(f"mini/minireason/{module}::{node.name}: {name}")
    assert not offenders, offenders


def _schema_fields(schema: dict) -> set[str]:
    fields = set(schema.get("properties", {}))
    for nested in schema.get("$defs", {}).values():
        fields |= set(nested.get("properties", {}))
    return fields


def test_limb2_no_mini_schema_carries_a_field_that_could_buy_standing():
    """Enumerated, not listed: every registered form's whole rendered schema,
    every dataclass and pydantic model mini's record, source, seat and policy
    modules define."""
    import dataclasses
    import importlib
    import inspect

    from pydantic import BaseModel
    from minireason.forms import mini_form_ids, resolve_mini_form

    offenders = []
    for form_id in mini_form_ids():
        fields = _schema_fields(resolve_mini_form(form_id).wire_model.model_json_schema())
        if fields & _FORBIDDEN_FIELDS:
            offenders.append((form_id, fields & _FORBIDDEN_FIELDS))
    for module_name in ("records", "sources", "seats", "policy", "forms"):
        module = importlib.import_module(f"minireason.{module_name}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module.__name__:
                continue
            if dataclasses.is_dataclass(obj):
                fields = {f.name for f in dataclasses.fields(obj)}
            elif issubclass(obj, BaseModel):
                fields = _schema_fields(obj.model_json_schema())
            else:
                continue
            if fields & _FORBIDDEN_FIELDS:
                offenders.append((f"{module_name}.{name}", fields & _FORBIDDEN_FIELDS))
    assert not offenders, offenders


_PROSE = "Sunlight scatters off molecules much smaller than its wavelength. "


def _mixed_endpoint():
    calls = {"n": 0}

    def endpoint_fn(prompt):
        calls["n"] += 1
        return json.dumps({"candidates": [
            {"content": json.dumps({"claim": f"c{calls['n']}", "mechanism": "m",
                                    "forbidden": [{"case": "x", "eval": "program:json-wf"}]}),
             "typicality": 0.5},
            {"content": f"{_PROSE}(variation {calls['n']})", "typicality": 0.5},
        ]})

    return MockEndpoint(endpoint_fn)


def test_limb3_a_proposal_changes_no_status_either_way(tmp_path):
    """A proposal about a STANDING conjecture and one about a REFUTED
    conjecture: neither status moves, the survivors are unchanged, and the
    record still replays and verifies."""
    from deepreason.invariants import verify_root
    from minireason.forms import resolve_mini_form
    from minireason.log import replay
    from minireason.seats import record_commitment_proposals

    root = tmp_path / "run"
    run([("pi-0", "why does the sky look blue?")], _mixed_endpoint(), budget=200_000,
        root=root, vs_k=2, max_cycles=2)
    session = Session(root)
    standing = session.survivors("pi-0")
    refuted = sorted(session.state.refuted)
    assert standing and refuted
    before = dict(session.state.statuses)

    model = resolve_mini_form("mini.commitment.relaxed.v1").wire_model
    record_commitment_proposals(session, model.model_validate({"proposals": [
        {"about": standing[0], "body": "it forbids a red sky at noon"},
        {"about": refuted[0], "body": "it forbids nothing that could be checked"},
    ]}))
    assert dict(session.state.statuses) == before
    assert session.survivors("pi-0") == standing
    assert sorted(session.state.refuted) == refuted
    assert replay(root).digest() == session.state.digest()
    assert verify_root(root)["violations"] == []
