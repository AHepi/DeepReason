"""The modularity law's "enforced" clause, for the reduced engine: five checks
that go RED on a bypass (SPEC S9; C8).

"Enforced" means a check that can fail when a consumer bypasses the
interface or when a customization point requires a code edit to use
(CLAUDE.md, the modularity law, 2026-08-26). Each test below has a mutation
that turns it red, run and pasted into
`experiments/2026-09-05-change-mini-isolation-programme/proof/mutation_<n>.txt`
before it was written down.

1. the loop names no seat, kind or stage -- enumerated from the registries,
   matched as whole string constants on the AST (a substring match would trip
   on a pre-existing relapse-domain label, "mini.conjecturer.v1", that is
   folded into a recorded digest and cannot move);
2. no evidence-side path reads a mini seat name or artifact kind -- C7's
   scope boundary, the R-g guardrail;
3. a section added to a mini brief needs no source edit;
4. a new artifact kind needs no source edit;
5. only the no-op calibration hook is registered (R8).
"""

import ast
import json
import pathlib
import uuid

import pytest

from minireason.call import MockEndpoint
from minireason.loop import Session, run

REPO = pathlib.Path(__file__).resolve().parents[2]
MINI = REPO / "mini" / "minireason"
SRC = REPO / "src" / "deepreason"

_EVIDENCE_SIDE = (
    "src/deepreason/scheduler",
    "src/deepreason/adjudication",
    "src/deepreason/rules",
    "src/deepreason/harness.py",
    "src/deepreason/invariants.py",
    "src/deepreason/verification",
    "src/deepreason/capabilities/state.py",
)
_MINI_AUTHORITY_FUNCTIONS = (
    "register_commitments", "build_candidate", "guard_scope", "admit_candidate",
    "register_candidates", "refute", "_prepare_controlled_candidates",
    "_admit_controlled_candidates", "_mini_guard_finding", "_conjecture_stage",
)


def _registered_names() -> set[str]:
    """Every seat, shell, layout, flow, stage and kind id the registries hold
    -- read from the registries, so a new registration widens the check."""
    from deepreason.llm.seat_sections import seat_pack_layout_ids, seat_shell_ids
    import minireason.flow as flow
    import minireason.seats as seats

    names = set(seats.MINI_SEATS) | set(seat_shell_ids()) | set(seat_pack_layout_ids())
    names |= set(flow.mini_flow_ids())
    for flow_id in flow.mini_flow_ids():
        resolved = flow.resolve_mini_flow(flow_id)
        names |= set(resolved.artifact_kinds) | {s.stage_id for s in resolved.stages}
    names.add("mini:record")
    return names


def _string_constants(node) -> set[str]:
    return {
        n.value for n in ast.walk(node)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }


def _snapshot(*roots):
    return {p: p.stat().st_mtime_ns for root in roots for p in root.rglob("*.py")}


# ------------------------------------------------------------------ 1


def test_1_the_loop_names_no_seat_kind_or_stage():
    source = (MINI / "loop.py").read_text(encoding="utf-8")
    hits = sorted(_string_constants(ast.parse(source)) & _registered_names())
    assert hits == [], hits
    assert "skeleton" not in source


# ------------------------------------------------------------------ 2


def test_2_no_evidence_side_path_reads_a_mini_seat_name_or_kind():
    """Total over the full harness's authority packages (a whole-id text
    match: no src file legitimately names a mini id at all), and over mini's
    own authority functions as whole string constants."""
    names = _registered_names()
    offenders = []
    for rel in _EVIDENCE_SIDE:
        top = REPO / rel
        for path in (sorted(top.rglob("*.py")) if top.is_dir() else [top]):
            constants = _string_constants(ast.parse(path.read_text(encoding="utf-8")))
            for name in sorted(constants & names):
                offenders.append(f"{path.relative_to(REPO)}: {name}")
    for module in ("loop.py", "checks.py", "gate.py"):
        source = (MINI / module).read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.FunctionDef) and (
                module != "loop.py" or node.name in _MINI_AUTHORITY_FUNCTIONS
            ):
                for name in sorted(_string_constants(node) & names):
                    offenders.append(f"mini/minireason/{module}::{node.name}: {name}")
    assert offenders == [], offenders


# ------------------------------------------------------------------ 3


def _session(tmp_path):
    def endpoint_fn(prompt):
        return json.dumps({"candidates": [{"content": json.dumps(
            {"claim": "c", "mechanism": "m", "forbidden": [{"case": "x", "eval": "program:json-wf"}]}
        ), "typicality": 0.5}]})

    root = tmp_path / "run"
    run([("pi-0", "why?")], MockEndpoint(endpoint_fn), budget=100_000, root=root, vs_k=1, max_cycles=1)
    return Session(root)


def test_3_a_section_added_to_a_mini_brief_needs_no_source_edit(tmp_path):
    """A plugin file and a layout file in an operator home directory, loaded
    through the shipped loader, rendered into a MINI seat's brief -- and no
    file under mini/minireason/ or src/ changed."""
    from deepreason.llm.seat_sections import load_operator_plugins, seat_plugins_root
    from minireason.seats import render_mini_brief

    before = _snapshot(MINI, SRC)
    tag = uuid.uuid4().hex[:8]
    home = tmp_path / "home"
    plugins = seat_plugins_root(home=home, environ={})
    plugins.mkdir(parents=True)
    (plugins / f"arch_{tag}.py").write_text(
        "from pydantic import BaseModel\n"
        "from deepreason.llm.seat_sections import SectionRenderV1\n"
        "class _P(BaseModel):\n    pass\n"
        "class _S:\n"
        f"    plugin_id = 'test.operator.section.{tag}'\n"
        "    plugin_version = '1.0.0'\n"
        f"    section_id = 'operator-section-{tag}'\n"
        "    declared_handle_kinds = ()\n"
        "    requires = ()\n"
        "    parameters_model = _P\n"
        "    def render(self, request, params):\n"
        "        return SectionRenderV1(section_id=self.section_id,\n"
        f"                               text='A MINI SECTION NOBODY EDITED CODE FOR {tag}')\n"
        "PLUGIN = _S()\n"
    )
    (plugins / f"arch_{tag}.layout.json").write_text(json.dumps({
        "layout_id": f"seat-pack.test.operator.{tag}",
        "entries": [
            {"plugin_id": "mini.problem", "priority": 1},
            {"plugin_id": "mini.everything-so-far", "priority": 2},
            {"plugin_id": f"test.operator.section.{tag}", "priority": 3},
        ],
    }))
    loaded, notices = load_operator_plugins(home=home, environ={})
    assert notices == [] and set(loaded) == {
        f"test.operator.section.{tag}", f"seat-pack.test.operator.{tag}"
    }, (loaded, notices)

    brief = render_mini_brief(_session(tmp_path), "mini.conjecturer", "pi-0",
                              layout_id=f"seat-pack.test.operator.{tag}")
    assert f"A MINI SECTION NOBODY EDITED CODE FOR {tag}" in brief
    assert "## everything-so-far" in brief
    assert _snapshot(MINI, SRC) == before


# ------------------------------------------------------------------ 4


def test_4_a_new_artifact_kind_needs_no_source_edit(tmp_path):
    """A kind nobody has heard of: its form, layout, shell, stage and flow
    registered here under unique ids, one cycle run through the loop, the
    record carrying the kind -- and no file under the engine changed."""
    from pydantic import BaseModel, ConfigDict, Field

    from deepreason.llm.seat_sections import (
        SeatPackLayoutEntryV1, SeatPackLayoutV1, SeatShellV1,
        register_seat_pack_layout, register_seat_shell,
    )
    from deepreason.llm.wire import WireContract
    from minireason.flow import MiniFlowV1, MiniStageV1, register_mini_flow, resolve_mini_flow
    from minireason.forms import MiniFormV1, register_mini_form
    from minireason.records import mini_records

    before = _snapshot(MINI, SRC)
    tag = uuid.uuid4().hex[:8]
    kind = f"test.kind.{tag}.v1"

    class _Item(BaseModel):
        model_config = ConfigDict(extra="forbid")
        about: str = Field(min_length=1)
        body: str = Field(min_length=1)

    class _Items(BaseModel):
        model_config = ConfigDict(extra="forbid")
        items: list[_Item] = Field(min_length=1)

    class _Contract(WireContract):
        def __init__(self):
            super().__init__(f"test.form.{tag}", _Items, _Items, variant="mini")

        def compile(self, wire):
            return wire

    register_mini_form(MiniFormV1(form_id=f"test.form.{tag}", form_version="1.0.0",
                                  contract=_Contract(),
                                  records_of=lambda out: [(i.about, i.body) for i in out.items]))
    register_seat_pack_layout(SeatPackLayoutV1(layout_id=f"seat-pack.test.{tag}", entries=(
        SeatPackLayoutEntryV1(plugin_id="mini.problem", priority=1),
        SeatPackLayoutEntryV1(plugin_id="mini.target-conjecture", priority=2),
        SeatPackLayoutEntryV1(plugin_id="mini.directive", priority=98,
                              params={"text": f"You are the {tag} seat. Answer about the TARGET CONJECTURE."}),
    )))
    register_seat_shell(SeatShellV1(shell_id=f"seat.test.{tag}", seat_id=f"test.seat.{tag}",
                                    layout_id=f"seat-pack.test.{tag}", form_id=f"test.form.{tag}",
                                    role_prompt_template_id="role-prompt.legacy-v0"),
                        default_for_seat=f"test.seat.{tag}")
    base = resolve_mini_flow("mini.flow.isolation.v1")
    flow = register_mini_flow(MiniFlowV1(
        flow_id=f"test.flow.{tag}", flow_version="1.0.0",
        stages=(base.stages[0], MiniStageV1(
            stage_id=f"test.stage.{tag}", seat_id=f"test.seat.{tag}", shell_id=f"seat.test.{tag}",
            produces_kind=kind, reads_kinds=("mini.conjecture.v1",), per_target=True,
        )),
        artifact_kinds=("mini.conjecture.v1", kind),
        commitment_policy=base.commitment_policy,
    ))

    def endpoint_fn(prompt):
        if f"You are the {tag} seat" in prompt:
            target = prompt.split("TARGET CONJECTURE ", 1)[1].split("\n", 1)[0].strip()
            return json.dumps({"items": [{"about": target, "body": f"answer {tag}"}]})
        return json.dumps({"candidates": [{"content": f"a conjecture {tag}", "typicality": 0.5}]})

    root = tmp_path / "run"
    summary = run([("pi-0", "why?")], MockEndpoint(endpoint_fn), budget=100_000,
                  root=root, vs_k=1, max_cycles=1, flow=flow)
    assert summary["flow"] == f"test.flow.{tag}"
    records = mini_records(Session(root))
    assert [r.kind for r in records] == [kind] and records[0].content == f"answer {tag}"
    assert _snapshot(MINI, SRC) == before


# ------------------------------------------------------------------ 5


def test_5_only_the_noop_calibration_hook_is_registered():
    """R8: one hook, the no-op; two source lines name the registration; and
    nothing under src/ or mini/minireason/ calls the hook."""
    from minireason.seats import mini_calibration_hook_ids, resolve_mini_calibration_hook

    assert mini_calibration_hook_ids() == ("mini.calibration.noop.v1",)
    assert resolve_mini_calibration_hook().calibrate(seat_id="x", cycle=0, entries=()) is None
    sites, callers = [], []
    for root in (SRC, MINI):
        for path in sorted(root.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            sites += [f"{path.relative_to(REPO)}:{n}" for n, line in enumerate(source.splitlines(), 1)
                      if "register_mini_calibration_hook" in line]
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Call):
                    func = node.func
                    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                    if name in {"calibrate", "resolve_mini_calibration_hook"}:
                        callers.append(f"{path.relative_to(REPO)}:{node.lineno}")
    assert len(sites) == 2, sites
    assert callers == [], callers
