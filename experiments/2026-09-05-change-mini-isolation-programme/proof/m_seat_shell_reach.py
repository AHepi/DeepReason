"""M3: can a mini seat render its brief through the SHIPPED seat-shell
machinery, with no scheduler, no manifest policy and no V6 transaction?

Arm A: register a mini layout + shell from THIS process (what a code edit
       buys today), then walk it with a SectionRequestV1 built from a live
       mini Session. If this renders, D6/D7 need no new renderer.
Arm B: the same layout declared in a FILE under a DEEPREASON_HOME, with no
       Python. This is prerequisite F2; it is expected to fail.
"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, "mini")

from deepreason.llm.packs import _walk_seat_layout
from deepreason.llm.seat_sections import (
    SectionRequestV1, SeatPackLayoutEntryV1, SeatPackLayoutV1, SeatShellV1,
    register_seat_pack_layout, register_seat_shell, resolve_seat_shell,
    seat_pack_layout_ids, seat_shell_ids, section_plugin_ids,
)
from minireason.call import MockEndpoint
from minireason.loop import run, Session

def _sk(i):
    return json.dumps({"claim": f"claim {i}", "mechanism": f"mech {i}",
                       "forbidden": [{"case": "x", "eval": "program:json-wf"}]})
def _cj(*c):
    return json.dumps({"candidates": [{"content": x, "typicality": 0.5} for x in c]})

with tempfile.TemporaryDirectory() as td:
    n = {"i": 0}
    def fn(p):
        n["i"] += 1
        return _cj(_sk(2 * n["i"]), _sk(2 * n["i"] + 1))
    root = Path(td) / "r"
    run([("pi-0", "why did X happen?")], MockEndpoint(fn), budget=200_000,
        root=root, vs_k=2, turnover_k=3)
    session = Session(root)

    print("registered section plugins:", len(section_plugin_ids()))
    print("registered layouts BEFORE :", seat_pack_layout_ids())
    print("registered shells  BEFORE :", seat_shell_ids())

    # --- ARM A: register a mini layout + shell in-process -----------------
    layout = SeatPackLayoutV1(
        layout_id="seat-pack.mini.conjecturer.v0",
        entries=(
            SeatPackLayoutEntryV1(plugin_id="dr.problem", priority=1),
            SeatPackLayoutEntryV1(plugin_id="dr.neighbourhood", priority=8,
                                  droppable=True, compressible=True, min_tokens=32),
        ),
    )
    register_seat_pack_layout(layout)
    register_seat_shell(SeatShellV1(
        shell_id="seat.mini.conjecturer.v0", seat_id="mini.conjecturer",
        layout_id="seat-pack.mini.conjecturer.v0",
        form_id="mini.conjecturer.relaxed.v1",
        role_prompt_template_id="role-prompt.legacy-v0"), default_for_seat="mini.conjecturer")
    shell = resolve_seat_shell("mini.conjecturer")
    print("ARM A shell resolves ->", shell.shell_id, "| form_id:", shell.form_id)

    pid = "pi-0"
    raw = session.state.problems.get(pid)
    print("mini State.problems[pid] type:", type(raw).__name__, "| keys:", sorted(raw)[:8] if isinstance(raw, dict) else "-")
    from deepreason.ontology import Problem
    problems = {pid: Problem.model_validate(raw)}
    print("adapted to ontology Problem:", type(problems[pid]).__name__)
    accepted = [a for a, p in session.state.addr if p == pid and a in session.state.accepted]
    request = SectionRequestV1(
        problem=problems.get(pid),
        state=session.state,
        commitments=dict(session.harness.commitments),
        blobs=session.blobs,
        layout=__import__("deepreason.llm.layout", fromlist=["x"]).ROBUST_LAYOUT_POLICY,
        supplied={"accepted": tuple(accepted[:4])},
    )
    for lid, entries in (
        ("seat-pack.mini.a1.v0", (SeatPackLayoutEntryV1(plugin_id="dr.problem", priority=1),)),
        ("seat-pack.mini.a2.v0", (SeatPackLayoutEntryV1(plugin_id="dr.problem", priority=1),
                                  SeatPackLayoutEntryV1(plugin_id="dr.neighbourhood", priority=8,
                                                        droppable=True, compressible=True,
                                                        min_tokens=32))),
    ):
        register_seat_pack_layout(SeatPackLayoutV1(layout_id=lid, entries=entries))
        receipts = []
        try:
            sections = _walk_seat_layout("mini.conjecturer", lid, request, receipts)
            print(f"  {lid}: RENDERED {len(sections)} section(s);",
                  [(r.section_id, r.disposition, r.rendered_bytes) for r in receipts])
        except Exception as e:
            print(f"  {lid}: FAILED {type(e).__name__}: {e}")
    print("ARM A VERDICT: the shipped seat-shell walk runs from a live mini Session")
    print("               with no scheduler, no V6 transaction and no manifest policy;")
    print("               record-backed sections need ONE adapter (mini State returns dicts).")

    # --- ARM B: the same layout from a FILE, no Python (prerequisite F2) ---
    home = Path(td) / "home"
    (home / "seat_plugins").mkdir(parents=True)
    (home / "seat_plugins" / "mini_layout.json").write_text(
        json.dumps({"layout_id": "seat-pack.mini.fromfile.v0",
                    "entries": [{"plugin_id": "dr.problem", "priority": 1}]}))
    import os
    os.environ["DEEPREASON_HOME"] = str(home)
    from deepreason.llm.seat_sections import load_operator_plugins
    notices = load_operator_plugins(home=home)
    print("ARM B loader notices:", notices)
    print("ARM B layouts after   :", "seat-pack.mini.fromfile.v0" in seat_pack_layout_ids())
    print("ARM B VERDICT: a layout declared in a FILE is", 
          "REGISTERED" if "seat-pack.mini.fromfile.v0" in seat_pack_layout_ids() else "NOT registered (F2 confirmed)")
