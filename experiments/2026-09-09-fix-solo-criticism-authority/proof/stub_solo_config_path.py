"""Stub root: one-model configuration, both switches on, no manifest.

Shows what a Config-driven single_family_trial actually does on a run where
one model occupies every seat.
"""
import json, pathlib, sys, itertools

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_endpoints
from deepreason.scheduler.scheduler import Scheduler
from deepreason.ontology import WarrantType

root = pathlib.Path(sys.argv[1])
root.mkdir(parents=True, exist_ok=True)
h = Harness(root)

CONJ = json.dumps({"candidates": [
    {"content": "a chorale passage with parallel fifths in bar 3", "typicality": 0.5},
    {"content": "a chorale passage that avoids parallel fifths", "typicality": 0.4},
]})
CASE = json.dumps({"attack": True, "case": "clause 2 forbids parallel fifths and bar 3 has them"})
DEFENCE = json.dumps({"answer": "the fifths echo the cantus firmus deliberately"})
RULING = json.dumps({"verdict": "fail", "decisive_point": "bar 3 has them"})

def _fixed(text):
    return lambda prompt: text

M = "qwen-stub"
endpoints = {
    "conjecturer": MockEndpoint(_fixed(CONJ), name="mock://c", model=M),
    "argumentative_critic": MockEndpoint(_fixed(CASE), name="mock://ac", model=M),
    "defender": MockEndpoint(_fixed(DEFENCE), name="mock://d", model=M),
    "judge": [
        MockEndpoint(_fixed(RULING), name="mock://j0", model=M),
        MockEndpoint(_fixed(RULING), name="mock://j1", model=M),
    ],
}
leases = leases_from_endpoints(endpoints)
adapter = LLMAdapter(endpoints, h.blobs, leases=leases)
print("is_single_model:", adapter.is_single_model())
print("judge seats:", len(adapter.judge_seats()))

from deepreason.ontology import Problem, ProblemProvenance
h.register_problem(Problem(
    id="p-seed",
    description="Does a chorale passage with parallel fifths in bar 3 violate clause 2?",
    provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
))

cfg = Config(
    N_SCHOOLS=2,
    ARGUMENTATIVE_AUTHORITY="single_family_trial",
    ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
)
Scheduler(h, adapter, cfg).run(int(sys.argv[2]) if len(sys.argv) > 2 else 3)

h2 = Harness(root, read_only=True)
warrants = list(h2.warrants.values())
arg = [w for w in warrants if w.type == WarrantType.ARGUMENTATIVE]
print("warrants total:", len(warrants), "argumentative:", len(arg))
print("attack edges:", len(h2.state.att))
declines = [tuple(e.inputs) for e in h2.log.read()
            if e.inputs and str(e.inputs[0]).startswith(("trial-declined", "trial-blocked", "arg-crit"))]
from collections import Counter
print("trial/crit measures:", Counter(d[0] + (":" + d[2] if d[0] == "trial-declined" and len(d) > 2 else "") for d in declines))
