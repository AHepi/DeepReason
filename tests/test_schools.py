"""P2 acceptance (spec §16): schools measurably diverge; forced convergence
triggers Reseed, replayed byte-for-byte; allocation follows §11.2."""

import json

from deepreason.capture import detection, schools
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.embedder import HashingEmbedder
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Rule
from deepreason.scheduler.scheduler import Scheduler


def _vs(*contents) -> str:
    return json.dumps(
        {"candidates": [{"content": c, "typicality": 0.5} for c in contents]}
    )


def _seed_problem(harness, criteria=()) -> None:
    for cid in criteria:
        harness.register_commitment(Commitment(id=cid, eval="predicate:True"))
    harness.register_problem(
        Problem(
            id="pi-seed",
            description="a seed problem",
            criteria=list(criteria),
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


class _SchoolScripted:
    """Answers depend on which school's stance is in the pack — schools
    genuinely diverge in vocabulary."""

    def __init__(self, vocab_by_stance: dict[str, str]):
        self.vocab = vocab_by_stance
        self.calls = 0

    def __call__(self, prompt: str) -> str:
        self.calls += 1
        for stance, vocab in self.vocab.items():
            if stance in prompt:
                return _vs(f"{vocab} account number {self.calls}")
        return _vs(f"generic account number {self.calls}")


def test_make_profile_keeps_capture_machinery_on(tmp_path):
    """Capture control (spec §11) is mandatory in normal runs: the app
    profile must not zero schools or leave the tripwires unable to fire,
    and a make-shaped scheduler must actually build the school roster."""
    from deepreason.easy import MAKE_OVERRIDES

    assert "N_SCHOOLS" not in MAKE_OVERRIDES  # inherits the configured range
    config = Config(**MAKE_OVERRIDES)
    assert 3 <= config.N_SCHOOLS <= 5  # spec §11.1 normal range
    assert config.RESEED_RATIO_MAX is not None  # school convergence can fire
    assert config.LAMBDA_FLOOR is not None      # grounding decay can fire
    assert config.GATE_ORBIT_MIN is not None    # attractor orbiting can fire

    harness = Harness(tmp_path / "run")
    _seed_problem(harness)
    adapter = LLMAdapter({"conjecturer": MockEndpoint(lambda p: _vs("x"))}, harness.blobs)
    scheduler = Scheduler(harness, adapter, config, embedder=HashingEmbedder())
    assert len(scheduler.schools) == config.N_SCHOOLS


def test_init_and_allocation(tmp_path):
    harness = Harness(tmp_path / "run")
    config = Config(N_SCHOOLS=2)
    roster = schools.init_schools(harness, config)
    assert sorted(roster) == ["school-0", "school-1"]
    # Policy artifacts are ordinary registered artifacts (Refl), attackable.
    for policy in roster.values():
        assert policy["artifact_id"] in harness.state.artifacts
    _seed_problem(harness)
    problem = harness.state.problems["pi-seed"]
    assert schools.allocate(harness, problem, roster, config) == ["school-0", "school-1"]


def test_successor_owned_by_spawning_lineage(tmp_path):
    harness = Harness(tmp_path / "run")
    config = Config(N_SCHOOLS=2, VS_K=1)
    _seed_problem(harness, criteria=["k-true"])
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda p: _vs("some account"))},
        harness.blobs, retry_max=2,
    )
    scheduler = Scheduler(harness, adapter, config)
    from deepreason.ontology import Problem as P
    from deepreason.ontology import ProblemProvenance as PP

    # Fake a successor problem spawned from a school-1 artifact.
    from deepreason.ontology import Interface, Provenance

    artifact = harness.create_artifact(
        "school-1 lineage artifact",
        interface=Interface(),
        provenance=Provenance(role="conjecturer", school="school-1"),
    )
    successor = harness.register_problem(
        P(
            id="succ:test",
            description="follow through",
            provenance=PP.model_validate(
                {"trigger": "successor", "from": [artifact.id]}
            ),
        )
    )
    assert schools.allocate(harness, successor, scheduler.schools, config) == ["school-1"]


def test_schools_diverge_measurably(tmp_path):
    harness = Harness(tmp_path / "run")
    config = Config(N_SCHOOLS=2, VS_K=1, FLOOR=0, CAPTURE_W=20)
    _seed_problem(harness)
    endpoint = _SchoolScripted(
        {
            "causal mechanism": "gear pressure torque mechanism linkage",
            "counterexample": "anomaly exception boundary refutation instance",
        }
    )
    adapter = LLMAdapter({"conjecturer": MockEndpoint(endpoint)}, harness.blobs, retry_max=2)
    Scheduler(harness, adapter, config).run(3)
    metrics = detection.generator_metrics(harness, HashingEmbedder(), config.CAPTURE_W)
    assert metrics["inter_school_min_dist"] is not None
    assert metrics["inter_school_min_dist"] > 0.3  # diverged from a zero-distance seed


def test_forced_convergence_triggers_reseed_and_replays(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    config = Config(N_SCHOOLS=2, VS_K=1, FLOOR=0, RESEED_DIST_MIN=0.5, CAPTURE_W=10)
    _seed_problem(harness)
    counter = {"n": 0}

    def same_basin(prompt: str) -> str:  # both schools emit near-identical content
        counter["n"] += 1
        return _vs(f"the one modal answer everyone gives {counter['n']}")

    adapter = LLMAdapter({"conjecturer": MockEndpoint(same_basin)}, harness.blobs, retry_max=2)
    Scheduler(harness, adapter, config).run(4)

    events = list(harness.log.read())
    reseeds = [e for e in events if e.rule == Rule.RESEED]
    assert reseeds, "sustained convergence must trigger a Reseed"
    # Succession, not deletion: both old and new policy artifacts persist.
    roster = schools.roster(harness)
    reseeded = [s for s, p in roster.items() if "reseed_of" in p]
    assert reseeded
    old_policy_id = roster[reseeded[0]]["reseed_of"]
    assert old_policy_id in harness.state.artifacts
    # Byte-for-byte replay including the Reseed event.
    assert Harness(root).state.model_dump_json() == harness.state.model_dump_json()
