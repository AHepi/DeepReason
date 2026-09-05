"""M-measurement: can mini dispatch a NEW wire contract id and stay replay-valid?

Arm 1: mini as it ships (conjecturer.compact.reference_free.v1).
Arm 2: mini with a NEW contract id (mini.relaxed.v1) whose wire model has
       no required skeleton and no length bound at all.
Both -> verify_root. Frozen surface 3 is contacted only if arm 2 fails
a check arm 1 passes.
"""
import json, sys, tempfile
from pathlib import Path

sys.path.insert(0, "mini")

from pydantic import Field
from deepreason.invariants import verify_root
from deepreason.llm.contracts import ConjecturerOutput, ConjectureCandidate
from deepreason.llm.wire import StrictWireModel, WireContract
from minireason.call import MockEndpoint
from minireason import compat
from minireason.loop import run


def _skeleton(i):
    return json.dumps({"claim": f"claim {i}", "mechanism": f"mech {i}",
                       "forbidden": [{"case": "must state a mechanism",
                                      "eval": "program:json-wf"}]})

def _conj(*contents):
    return json.dumps({"candidates": [{"content": c, "typicality": 0.5}
                                      for c in contents]})


# --- arm 2's relaxed form: free prose, no length bound, no required fields ---
class RelaxedMiniCandidate(StrictWireModel):
    content: str = Field(min_length=1)
    typicality: float = Field(default=0.5, ge=0.0, le=1.0)

class RelaxedMiniConjecturer(StrictWireModel):
    candidates: list[RelaxedMiniCandidate] = Field(min_length=1)

class RelaxedMiniWireContract(WireContract[ConjecturerOutput]):
    def __init__(self):
        super().__init__("mini.conjecturer.relaxed.v1", RelaxedMiniConjecturer,
                         ConjecturerOutput, variant="compact")
    def compile(self, wire):
        return ConjecturerOutput(candidates=[
            ConjectureCandidate(content=i.content, typicality=i.typicality)
            for i in wire.candidates])


def arm(root, contract=None):
    calls = {"n": 0}
    def fn(prompt):
        calls["n"] += 1
        i = calls["n"]
        return _conj(_skeleton(2 * i), _skeleton(2 * i + 1)) if i <= 3 else _conj(_skeleton(2), _skeleton(3))
    real_init = compat.initialize
    if contract is not None:
        def patched(root_, endpoint, model_profile=compat.DEFAULT_MODEL_PROFILE):
            k = real_init(root_, endpoint, model_profile)
            return compat.CompatibilityKernel(profile=k.profile, lease=k.lease,
                                              wire_contract=contract, manifest=k.manifest)
        import minireason.loop as L
        L.initialize = patched
    else:
        import minireason.loop as L
        L.initialize = real_init
    summary = run([("pi-0", "why?")], MockEndpoint(fn), budget=200_000,
                  root=root, vs_k=2, turnover_k=3, orbit_floor=3)
    v = verify_root(Path(root))
    return summary, v


with tempfile.TemporaryDirectory() as td:
    for label, contract in (("ARM1 shipped reference_free.v1", None),
                            ("ARM2 new id mini.conjecturer.relaxed.v1", RelaxedMiniWireContract())):
        root = Path(td) / label.split()[0]
        s, v = arm(root, contract)
        print(f"--- {label}")
        print("  stop=%s cycles=%s problems=%s" % (s["stop"], s["cycles"], s["problems"]))
        print("  verify_root violations:", len(v["violations"]))
        for row in v["violations"][:8]:
            print("   ", row["check"], "|", row["detail"][:160])
