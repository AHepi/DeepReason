"""CI chaos: scripted garbage endpoints drive the scheduler down failure
paths (schema-repair storms, judge disagreement, duplicate floods), then
invariants.verify_root must hold over the wreckage. The free, always-on
version of scripts/chaos_battery.py."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.scheduler.scheduler import Scheduler


def _seed(harness):
    harness.register_commitment(
        Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(Problem(
        id="pi-t", description="explain the tides", criteria=["k-moon"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []})))


def _chaotic_conjecturer():
    """Cycles through the garbage classes a weak model actually emits:
    invalid JSON, truncated JSON, empty candidates, duplicates, then a
    valid novel candidate so the run also makes progress."""
    calls = {"n": 0}

    def respond(prompt):
        calls["n"] += 1
        n = calls["n"]
        return [
            "utterly not json {{{",
            '{"candidates": [{"content": "the moon pulls',       # truncated
            '{"candidates": []}',                                 # empty
            json.dumps({"candidates": [
                {"content": "the moon pulls the sea", "typicality": 0.5}]}),
            json.dumps({"candidates": [                           # duplicate
                {"content": "the moon pulls the sea", "typicality": 0.5}]}),
            json.dumps({"candidates": [
                {"content": f"the moon pulls the sea, take {n}", "typicality": 0.4}]}),
        ][n % 6]

    return MockEndpoint(respond)


def _disagreeing_judge(verdict):
    return MockEndpoint(lambda p: json.dumps(
        {"verdict": verdict, "decisive_point": "clause 1" if verdict == "fail" else "x"}))


def test_chaotic_conjecturer_preserves_invariants(tmp_path):
    root = tmp_path / "run"
    h = Harness(root)
    _seed(h)
    meter = TokenMeter()
    adapter = LLMAdapter({"conjecturer": _chaotic_conjecturer()}, h.blobs,
                         retry_max=1, meter=meter)
    Scheduler(h, adapter, Config(VS_K=2, N_SCHOOLS=0, FLOOR=0)).run(8)

    result = verify_root(root, meter.total)
    assert result["violations"] == [], result["violations"]
    # The chaos actually happened: drops from schema-repair exhaustion.
    assert result["stats"]["dropped_calls"] >= 1
    assert result["stats"]["artifacts"] >= 1  # and progress happened anyway


def test_disagreeing_ensemble_and_weak_defender(tmp_path):
    from deepreason.informal.standards import register_standard

    root = tmp_path / "run"
    h = Harness(root)
    register_standard(h, "std-x", rubric="must name a mechanism")
    h.register_commitment(Commitment(id="kappa-x", eval="rubric:std-x"))
    h.register_problem(Problem(
        id="pi-x", description="an informal question", criteria=["kappa-x"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []})))
    meter = TokenMeter()
    endpoints = {
        "conjecturer": MockEndpoint(lambda p: json.dumps({"candidates": [
            {"content": f"account {hash(p) % 997}", "typicality": 0.5}]})),
        "argumentative_critic": MockEndpoint(lambda p: json.dumps(
            {"attack": True, "case": "violates clause 1 badly"})),
        "defender": MockEndpoint(lambda p: json.dumps({"answer": "no."})),
        # Two seats that ALWAYS disagree: every ruling must block, and every
        # blocked trial's spend must still reach the log.
        "judge": [_disagreeing_judge("fail"), _disagreeing_judge("pass")],
    }
    adapter = LLMAdapter(endpoints, h.blobs, retry_max=1, meter=meter)
    Scheduler(h, adapter, Config(VS_K=1, N_SCHOOLS=0, FLOOR=0)).run(3)

    result = verify_root(root, meter.total)
    assert result["violations"] == [], result["violations"]
    assert result["stats"]["trial_blocks"] >= 1  # ensemble-split fired
    assert result["stats"]["warrants"] == 0 or all(
        v["check"] != "warrant-validity" for v in result["violations"])


def test_budget_exhaustion_mid_retry_still_reconciles(tmp_path):
    """Live finding (in-band accounting, first outing): TokenBudgetExceeded
    raised mid-retry left prior attempts' spend off the log (833-token
    delta). The exception now carries the spend; the meter and the log must
    reconcile exactly even when the budget dies inside a repair loop."""
    root = tmp_path / "run"
    h = Harness(root)
    _seed(h)
    meter = TokenMeter(budget=250)  # dies after roughly one garbage attempt
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda p: "never valid json {{{")},
        h.blobs, retry_max=2, meter=meter)
    Scheduler(h, adapter, Config(VS_K=1, N_SCHOOLS=0, FLOOR=0)).run(3)

    logged = sum(e.llm.tokens for e in h.log.read() if e.llm)
    assert meter.total > 0
    assert logged == meter.total  # nothing invisible, even at the death
    result = verify_root(root, meter.total)
    assert result["violations"] == [], result["violations"]


def test_successor_descriptions_do_not_nest(tmp_path):
    """Chaos finding: successor problems embedded the whole ancestor chain
    (7 levels deep live). A successor-of-a-successor must carry the ROOT
    description exactly once, at any depth."""
    from deepreason.rules.spawn import scan_spawns
    from tests.conftest import attack

    h = Harness(tmp_path / "run")
    _seed(h)
    seed_desc = h.state.problems["pi-t"].description
    config = Config(HV_MIN=None, FLOOR=0)
    pid = "pi-t"
    for depth in range(3):
        a = h.create_artifact(f"candidate at depth {depth}", problem_id=pid)
        attack(h, a.id, f"kill-{depth}")
        spawned = scan_spawns(h, config)
        succ = next(p for p in spawned if p.id == f"succ:{a.id[:12]}")
        assert succ.description.count("Original problem:") == 1
        assert seed_desc in succ.description
        pid = succ.id


def test_duplicate_flood_hits_gate_and_dedupe(tmp_path):
    root = tmp_path / "run"
    h = Harness(root)
    _seed(h)
    meter = TokenMeter()
    # Same candidate every call: after registration it dedupes; the shared
    # call must still land on the log each cycle (conj-noregister path).
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda p: json.dumps({"candidates": [
            {"content": "the moon pulls the sea", "typicality": 0.5}]}))},
        h.blobs, retry_max=1, meter=meter)
    Scheduler(h, adapter, Config(VS_K=1, N_SCHOOLS=0, FLOOR=0)).run(4)

    result = verify_root(root, meter.total)
    assert result["violations"] == [], result["violations"]
    events = list(h.log.read())
    noregister = [e for e in events if "conj-noregister" in e.inputs]
    assert len(noregister) >= 2  # dedupe cycles still accounted
