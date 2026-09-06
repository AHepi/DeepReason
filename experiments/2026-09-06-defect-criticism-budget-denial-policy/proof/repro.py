"""Smallest offline demonstration of P1, and of what R2 asks for.

Run from the repository root.
"""

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Provenance
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.transaction import WorkBudgetDenied


def _scheduler(root, **config_kwargs):
    harness = Harness(root)
    harness.register_commitment(
        Commitment(id="k-moon", eval="predicate:'moon' in content")
    )
    harness.register_problem(
        Problem(
            id="pi-tides", description="explain the tides", criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(lambda _p: json.dumps({"candidates": []})),
            "argumentative_critic": MockEndpoint(lambda _p: json.dumps({"cases": []})),
        },
        harness.blobs,
        retry_max=1,
    )
    config = Config(VS_K=1, N_SCHOOLS=0, FUZZ_N=0, **config_kwargs)
    return harness, Scheduler(harness, adapter, config)


def _targets(harness, n):
    ids = []
    for i in range(n):
        artifact = harness.create_artifact(
            f"the moon pulls the sea, reading {i}",
            provenance=Provenance(role="conjecturer"),
            problem_id="pi-tides",
        )
        ids.append(artifact.id)
    return ids


def survives(*, exhausted, config_kwargs, batch_calls):
    """Does one refused criticism batch leave the cycle alive?"""

    with tempfile.TemporaryDirectory() as tmp:
        harness, scheduler = _scheduler(Path(tmp) / "run", **config_kwargs)
        ids = _targets(harness, 4)

        import deepreason.scheduler.scheduler as module

        original = module.crit_argumentative_batch

        def _deny(_harness, target_ids, *_a, **_kw):
            batch_calls.append(tuple(target_ids))
            raise WorkBudgetDenied(
                SimpleNamespace(work_id="sha256:" + "d" * 8),
                budget_exhausted=exhausted,
            )

        module.crit_argumentative_batch = _deny
        try:
            scheduler._arg_crit(ids)
        except BaseException as escaped:
            return f"run ended: {type(escaped).__name__}"
        finally:
            module.crit_argumentative_batch = original
        return "cycle continued"


calls = []
print("A. refusal with budget REMAINING, default config:  ",
      survives(exhausted=False, config_kwargs={}, batch_calls=calls),
      f"({len(calls)} batch call(s))")

calls = []
print("B. refusal on a SPENT ceiling, default config:     ",
      survives(exhausted=True, config_kwargs={}, batch_calls=calls),
      f"({len(calls)} batch call(s))")

# R2: is the behaviour reachable as configuration at all?
print("C. Config carries a criticism budget-denial knob:  ",
      hasattr(Config(), "CRITICISM_BUDGET_DENIAL_POLICY"))
