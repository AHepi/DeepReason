"""Smallest offline demonstration of the P8 cause, against CURRENT code."""
import json, sys, tempfile
from pathlib import Path
from types import SimpleNamespace

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.transaction import WorkBudgetDenied


def _scheduler(root):
    harness = Harness(root)
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(Problem(
        id="pi-tides", description="explain the tides", criteria=["k-moon"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda p: json.dumps({"candidates": []}))},
        harness.blobs, retry_max=1,
    )
    return Scheduler(harness, adapter, Config(VS_K=1, N_SCHOOLS=0, FUZZ_N=0))


def absorbed(error):
    with tempfile.TemporaryDirectory() as tmp:
        s = _scheduler(Path(tmp) / "run")
        def _boom():
            raise error
        s.step = _boom
        try:
            s.run(1)
        except BaseException as escaped:
            return False, type(escaped).__name__
        return True, None


def _denied(exhausted):
    terminal = SimpleNamespace(work_id="sha256:" + "d" * 8)
    try:
        return WorkBudgetDenied(terminal, budget_exhausted=exhausted)
    except TypeError:          # pre-fix signature: no such keyword
        return WorkBudgetDenied(terminal)


print("A. TokenBudgetExceeded absorbed by the cycle loop:",
      absorbed(TokenBudgetExceeded("token budget exhausted: 500000/500000")))
print("B. WorkBudgetDenied (ceiling spent) absorbed:", absorbed(_denied(True)))
print("B2. WorkBudgetDenied (budget remaining) absorbed:", absorbed(_denied(False)))

# C. The meter offers nothing that separates a spent ceiling from one
#    oversized request.
meter = TokenMeter(budget=500_000)
meter.prompt_tokens = 495_362           # the observed root's spend
try:
    meter.reserve(prompt_text="x" * 3_000, max_tokens=8192)
except TokenBudgetExceeded as error:
    spent = error
meter2 = TokenMeter(budget=500_000)
try:
    meter2.reserve(prompt_text="x" * 3_000_000, max_tokens=8192)   # nothing spent
except TokenBudgetExceeded as error:
    oversized = error
print("C. spent-ceiling denial carries budget_exhausted:",
      getattr(spent, "budget_exhausted", "ABSENT"))
print("C. oversized-request denial carries budget_exhausted:",
      getattr(oversized, "budget_exhausted", "ABSENT"))
