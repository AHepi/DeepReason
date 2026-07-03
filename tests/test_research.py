"""P4 acceptance (spec §16): an observation-valued commitment with no
evidence spawns a research task; fetched evidence enters as an attackable
artifact; lambda is computed live and the grounding brake fires on a
staged decay."""

import json

from deepreason.capture import detection
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
    Warrant,
    WarrantType,
)
from deepreason.research.backends import StaticBackend, covered, run_research
from deepreason.rules.spawn import scan_spawns
from deepreason.scheduler.scheduler import Scheduler
from tests.conftest import art, attack


def _observation_setup(harness) -> str:
    harness.register_commitment(
        Commitment(id="k-tide-tables", eval="predicate:True", observation_valued=True)
    )
    harness.register_problem(
        Problem(
            id="pi-tides",
            description="explain the tides",
            criteria=["k-tide-tables"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    candidate = harness.create_artifact(
        "the moon pulls the sea",
        interface=Interface(commitments=["k-tide-tables"]),
        provenance=Provenance(role="conjecturer"),
        problem_id="pi-tides",
    )
    return candidate.id


def test_observation_valued_spawns_research(harness):
    aid = _observation_setup(harness)
    scan_spawns(harness, Config())
    rid = f"research:k-tide-tables:{aid[:12]}"
    assert rid in harness.state.problems
    problem = harness.state.problems[rid]
    assert problem.provenance.trigger.value == "research"
    assert not covered(harness, rid)
    # Idempotent rescan.
    n = len(harness.state.problems)
    scan_spawns(harness, Config())
    assert len(harness.state.problems) == n


def test_evidence_enters_as_attackable_artifact(harness):
    aid = _observation_setup(harness)
    scan_spawns(harness, Config())
    rid = f"research:k-tide-tables:{aid[:12]}"
    problem = harness.state.problems[rid]
    backend = StaticBackend({problem.description: ("NOAA tide tables 2025: ...", "NOAA")})
    evidence = run_research(harness, problem, backend)
    assert evidence is not None
    assert harness.state.status[evidence.id] == Status.ACCEPTED
    assert covered(harness, rid)  # covering => no further research Spawn

    # Attack the source-reliability node: evidence orphaned, not false.
    reliability = next(
        r.target for r in evidence.interface.refs if r.role.value == "dependence"
    )
    attack(harness, reliability, "noaa-feed-was-stale")
    assert harness.state.status[evidence.id] == Status.SUSPENDED_UNSUPPORTED
    assert not covered(harness, rid)  # uncovered again — research re-arms


def test_scheduler_runs_standing_exogenous_schedule(tmp_path):
    harness = Harness(tmp_path / "run")
    aid = _observation_setup(harness)
    rid = f"research:k-tide-tables:{aid[:12]}"
    vs = json.dumps({"candidates": [{"content": "the moon pulls the sea again", "typicality": 0.5}]})
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda p: vs)}, harness.blobs, retry_max=2
    )
    backend = StaticBackend(
        {f"obtain evidence for observation-valued k-tide-tables on {aid[:12]}":
             ("measured tide tables", "NOAA")}
    )
    scheduler = Scheduler(
        harness, adapter, Config(VS_K=1, N_SCHOOLS=0, FLOOR=0, RESEARCH_PERIOD=1),
        research_backend=backend,
    )
    scheduler.run(2)
    assert covered(harness, rid)  # fetched on schedule, no manual step


def test_grounding_brake_fires_on_staged_decay(tmp_path):
    harness = Harness(tmp_path / "run")
    config = Config(
        VS_K=1, N_SCHOOLS=0, FLOOR=0, LAMBDA_FLOOR=0.8, CAPTURE_W=40
    )
    harness.register_problem(
        Problem(
            id="pi-plain",
            description="a problem with no evaluable criteria",
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    # Staged decay: a run of rubric-derived verdicts and nothing exogenous.
    # Rubric warrants require conforming trial transcripts (§2, P5).
    from deepreason.informal.trial import transcript_blob

    harness.register_commitment(Commitment(id="kappa-r", eval="rubric:std-1"))
    for i in range(4):
        target = art(harness, f"informal claim {i}")
        nu = art(harness, f"nu: rubric ruling {i} is sound")
        trace_ref = transcript_blob(
            harness,
            case=f"the claim violates clause {i} of std-1",
            answer="the defence concedes the clause applies",
            decisive_point=f"violates clause {i}",
            checks={"order_swap": "skipped", "paraphrase": "skipped"},
        )
        harness.create_artifact(
            f"critic: rubric fail {i}",
            provenance=Provenance(role="critic"),
            warrants=[
                Warrant(
                    id=f"w-r{i}",
                    target=target.id,
                    type=WarrantType.DEMONSTRATIVE,
                    commitment="kappa-r",
                    verdict="fail",
                    trace_ref=trace_ref,
                    validity_node=nu.id,
                )
            ],
        )
    assert detection.grounding_lambda(harness, config.CAPTURE_W) < 0.8  # live lambda

    counter = {"n": 0}

    def conjecture(prompt):
        counter["n"] += 1
        return json.dumps(
            {"candidates": [{"content": f"claim {counter['n']}", "typicality": 0.5}]}
        )

    adapter = LLMAdapter({"conjecturer": MockEndpoint(conjecture)}, harness.blobs, retry_max=2)
    scheduler = Scheduler(harness, adapter, config)
    scheduler.run(3)  # flag must sustain 2 checks (hysteresis) before firing

    assert scheduler.research_priority  # the brake raised research priority
    interventions = [
        e for e in harness.log.read() if "intervention:exogenous-brake" in e.inputs
    ]
    assert interventions  # logged with its trigger — efficacy is measurable
