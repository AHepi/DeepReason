#!/usr/bin/env python3
"""Reproduce: the steering controller is inert on a compiled-manifest run.

Mirrors the grounded-extension root's live conditions exactly as the record
shows them (DIAGNOSIS.md): the SAME eleven role names that
run-manifest.json binds, every endpoint at the SAME max_tokens=16384, and
the SAME process signal the log carries for the five roles that actually
called a provider -- truncated=0, attempts=1 on every call.

Run:  python experiments/2026-08-13-defect-controller-steering-inert/\
repro_controller_inert.py
Exit: 0 when the defect reproduces (part A inert AND part B steers).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from deepreason.controller import CLEAN_WINDOWS, Controller  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.llm.adapter import LLMAdapter  # noqa: E402
from deepreason.ontology import (  # noqa: E402
    Commitment,
    Problem,
    ProblemProvenance,
    Rule,
)
from deepreason.ontology.event import LLMCall  # noqa: E402

# run-manifest.json roles, verbatim, with the caps the manifest pins.
MANIFEST_ROLES = (
    "argumentative_critic",
    "conjecturer",
    "defender",
    "grounding_reviewer",
    "judge",
    "property_designer",
    "summarizer",
    "synthesizer",
    "thesis",
    "variator",
    "vision_critic",
)
MANIFEST_CAP = 16384

# Roles the committed log shows actually calling a provider, with counts.
CALLING_ROLES = {
    "judge": 342,
    "argumentative_critic": 123,
    "defender": 122,
    "conjecturer": 49,
    "variator": 30,
}


class _Endpoint:
    def __init__(self, cap: int):
        self.name = "ep"
        self.model = "m"
        self.max_tokens = cap
        self.timeout_s = 120
        self.last_finish_reason = None
        self.last_usage = None
        self.last_mean_surprisal = None


def _harness(root: Path) -> Harness:
    h = Harness(root)
    h.register_commitment(Commitment(id="k", eval="predicate:'x' in content"))
    h.register_problem(
        Problem(
            id="p", description="d", criteria=["k"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    return h


def _append_clean_calls(h: Harness, role: str, n: int) -> None:
    """The signal the record shows: every call clean, never truncated,
    never repaired. More than CLEAN_WINDOWS so the efficiency branch is
    eligible."""
    for _ in range(n):
        h._commit(
            Rule.CONJ,
            inputs=["p"],
            outputs=[],
            llm=LLMCall(
                role=role, model="m", endpoint="e",
                prompt_ref="inline:p", raw_ref="inline:r",
                truncated=False, attempts=1,
            ),
        )


def _policy_artifacts(h: Harness) -> list[str]:
    out = []
    for event in h.log.read():
        if event.rule != Rule.REFL:
            continue
        for aid in event.outputs:
            art = h.state.artifacts.get(aid)
            if art is None or not art.content_ref.startswith("inline:"):
                continue
            try:
                body = json.loads(art.content_ref[len("inline:"):])
            except (TypeError, ValueError):
                continue
            if isinstance(body, dict) and "knobs" in body:
                out.append(aid)
    return out


def _controller_records(h: Harness) -> list[list[str]]:
    return [
        list(e.inputs)
        for e in h.log.read()
        if e.inputs and str(e.inputs[0]).startswith("controller-")
    ]


def part_a(tmp: Path) -> bool:
    """The defect: manifest caps, abundant clean signal, nothing moves and
    nothing is recorded."""
    h = _harness(tmp / "a")
    endpoints = {r: _Endpoint(MANIFEST_CAP) for r in MANIFEST_ROLES}
    adapter = LLMAdapter(dict(endpoints), h.blobs)
    for role, _live_n in CALLING_ROLES.items():
        _append_clean_calls(h, role, CLEAN_WINDOWS + 3)

    c = Controller(h, adapter)
    proposals = [c.step() for _ in range(8)]

    caps_after = {r: endpoints[r].max_tokens for r in MANIFEST_ROLES}
    policies = _policy_artifacts(h)
    records = _controller_records(h)

    print("PART A — grounded manifest reproduced offline")
    print(f"  roles bound                 : {len(MANIFEST_ROLES)}")
    print(f"  every endpoint max_tokens   : {sorted(set(caps_after.values()))}")
    print(f"  roles with clean signal     : {sorted(CALLING_ROLES)}")
    print(f"  controller.step() over 8 cy : {proposals}")
    print(f"  policy artifacts emitted    : {len(policies)}")
    print(f"  controller-* records in log : {records}")
    ok = (
        all(p is None for p in proposals)
        and policies == []
        and records == []
        and set(caps_after.values()) == {MANIFEST_CAP}
    )
    print(f"  => inert, and SILENT        : {ok}")
    return ok


def part_b(tmp: Path) -> bool:
    """The control: identical in every way except one cap inside its
    envelope. If this steers, the envelope bound is the gate — not the
    wiring, not the signal."""
    h = _harness(tmp / "b")
    endpoints = {r: _Endpoint(MANIFEST_CAP) for r in MANIFEST_ROLES}
    endpoints["conjecturer"].max_tokens = 3000  # inside cap:conjecturer [800,5000]
    adapter = LLMAdapter(dict(endpoints), h.blobs)
    for role in CALLING_ROLES:
        _append_clean_calls(h, role, CLEAN_WINDOWS + 3)

    c = Controller(h, adapter)
    first = c.step()
    policies = _policy_artifacts(h)

    print()
    print("PART B — control: one cap moved inside its envelope")
    print(f"  conjecturer cap before      : 3000")
    print(f"  controller.step() cycle 1   : {first}")
    print(f"  conjecturer cap after       : {endpoints['conjecturer'].max_tokens}")
    print(f"  other caps unchanged        : "
          f"{sorted({endpoints[r].max_tokens for r in MANIFEST_ROLES if r != 'conjecturer'})}")
    print(f"  policy artifacts emitted    : {len(policies)}")
    ok = first == {"cap:conjecturer": 1875} and len(policies) == 1
    print(f"  => steers normally          : {ok}")
    return ok


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        a = part_a(tmp)
        b = part_b(tmp)
    print()
    if a and b:
        print("REPRODUCED: the controller is inert on manifest caps and "
              "steers on in-envelope caps. The envelope table is the gate.")
        return 0
    print("NOT REPRODUCED — diagnosis needs revisiting.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
