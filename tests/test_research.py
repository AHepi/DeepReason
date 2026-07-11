"""P4 acceptance (spec §16): an observation-valued commitment with no
evidence spawns a research task; fetched evidence enters as an attackable
artifact; lambda is computed live and the grounding brake fires on a
staged decay."""

import json

import pytest

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
from deepreason.ops import (
    report_research_failure,
    research_docket,
    submit_evidence,
)
from deepreason.research.backends import (
    ResearchService,
    StaticBackend,
    build_service,
    covered,
    run_research,
)
from deepreason.rules.crit import crit_program
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


# ===================================================================== #
# The research gate fix: service modes, agent channel, bounded failures,
# episode signals, provisional coverage, replay.

class _RaisingBackend:
    name = "raising"

    def fetch(self, query):
        raise RuntimeError("web-fetch-failed: www.science.org blocked us")


class _EmptyBackend:
    name = "empty"

    def fetch(self, query):
        return None


def _open_research_harness(tmp_path, relevance: str | None = None):
    """Harness with exactly ONE open research problem (optionally carrying
    a relevance predicate criterion) + a scripted conjecturer adapter. The
    seed problem carries NO criteria so fresh conjectures never auto-spawn
    additional research problems mid-test."""
    harness = Harness(tmp_path / "run")
    harness.register_commitment(
        Commitment(id="k-tide-tables", eval="predicate:True", observation_valued=True)
    )
    harness.register_problem(Problem(
        id="pi-tides", description="explain the tides", criteria=[],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    aid = harness.create_artifact(
        "the moon pulls the sea",
        interface=Interface(commitments=["k-tide-tables"]),
        provenance=Provenance(role="conjecturer"),
        problem_id="pi-tides",
    ).id
    criteria = []
    if relevance is not None:
        harness.register_commitment(
            Commitment(id="k-relevance", eval=f"predicate:{relevance}")
        )
        criteria = ["k-relevance"]
    rid = f"research:k-tide-tables:{aid[:12]}"
    harness.register_problem(Problem(
        id=rid,
        description=f"obtain evidence for observation-valued k-tide-tables on {aid[:12]}",
        criteria=criteria,
        provenance=ProblemProvenance.model_validate(
            {"trigger": "research", "from": [aid, "k-tide-tables"]}),
    ))
    vs = json.dumps({"candidates": [{"content": "another moon idea", "typicality": 0.5}]})
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda p: vs)}, harness.blobs, retry_max=2
    )
    return harness, rid, adapter


def _signals(harness, name):
    from deepreason.ontology import Rule

    return [e for e in harness.log.read()
            if e.rule == Rule.MEASURE and e.inputs and e.inputs[0] == name]


# ---- service modes -------------------------------------------------- #

def test_agent_mode_is_the_default_and_wired_by_ops(tmp_path, monkeypatch):
    """Normal runs get an ACTIVE agent-mode research service without any
    caller wiring — the gate that silently disabled research is gone."""
    import deepreason.scheduler.scheduler as sched_mod
    from deepreason import ops

    assert Config().RESEARCH_BACKEND == "agent"
    seen = {}

    class _FakeScheduler:
        def __init__(self, harness, adapter, config, embedder=None,
                     browser_backend=None, controller=None,
                     research_backend=None):
            seen["research"] = research_backend

        def run(self, cycles, on_cycle=None):
            return {"survivors": []}

    monkeypatch.setattr(sched_mod, "Scheduler", _FakeScheduler)
    h = Harness(tmp_path / "run")
    ops.run_scheduler(h, Config(roles={"conjecturer": {
        "endpoint": "https://example.invalid", "model": "m"}}), cycles=0)
    service = seen["research"]
    assert isinstance(service, ResearchService)
    assert service.mode == "agent" and not service.internal  # no web fetcher


def test_backend_modes_are_distinct_and_invalid_values_fail_loudly(tmp_path):
    assert build_service(Config(RESEARCH_BACKEND=None)).mode == "off"
    agent = build_service(Config(RESEARCH_BACKEND="agent"))
    assert agent.mode == "agent" and not agent.internal

    fixture = tmp_path / "corpus.yaml"
    fixture.write_text('"some query": ["evidence text", "a source"]\n')
    static = build_service(Config(RESEARCH_BACKEND=f"static:{fixture}"))
    assert static.mode == "static" and static.internal
    assert static.fetcher.fetch("some query") == ("evidence text", "a source")

    with pytest.raises(ValueError, match="not found"):
        build_service(Config(RESEARCH_BACKEND="static:/does/not/exist.yaml"))
    with pytest.raises(ValueError, match="unknown RESEARCH_BACKEND"):
        build_service(Config(RESEARCH_BACKEND="webby"))


def test_unattended_ask_user_never_blocks_and_attended_is_explicit():
    unattended = build_service(Config(RESEARCH_BACKEND="ask-user"))
    assert unattended.mode == "ask-user" and not unattended.internal
    attended = build_service(
        Config(RESEARCH_BACKEND="ask-user", RESEARCH_ATTENDED=True))
    assert attended.internal and attended.attended


# ---- spawn semantics stay §12-exact ---------------------------------- #

def test_uncovered_commitment_is_pending_never_failed(harness):
    """Absence of evidence is not a verdict: the carrier stays ACCEPTED
    and no warrant names the observation-valued commitment."""
    aid = _observation_setup(harness)
    scan_spawns(harness, Config())
    crit_program(harness, aid)  # observation-valued kappa is not evaluable
    assert harness.state.status[aid] == Status.ACCEPTED
    assert not any(
        w.commitment == "k-tide-tables" for w in harness.warrants.values()
    )


# ---- the docket: read-only, deterministic, graph-derived ------------- #

def test_research_docket_lists_open_requests_without_mutating(tmp_path):
    harness, rid, _ = _open_research_harness(tmp_path)
    events_before = len(list(harness.log.read()))
    entries = research_docket(harness, Config())
    assert len(list(harness.log.read())) == events_before  # read-only
    assert [e["problem"] for e in entries] == [rid]
    entry = entries[0]
    assert entry["commitment"] == "k-tide-tables"
    assert entry["backend_mode"] == "agent"
    assert entry["failed_internal_attempts"] == 0
    assert entry["internal_exhausted"] is False
    assert entry["external_submission_open"] is True
    assert entry["priority"] == "normal"
    assert "obtain evidence" in entry["claim"]


# ---- submit_evidence: registration is NOT coverage ------------------- #

def test_reliable_but_irrelevant_candidate_registers_without_covering(tmp_path):
    harness, rid, _ = _open_research_harness(
        tmp_path, relevance="'tide' in content.lower()")
    candidate = submit_evidence(
        harness, rid, "https://almanac.example/astrology",
        "the stars incline but do not compel")
    # Registered (nothing deleted), refuted by the ordinary relevance
    # commitment + warrant path, and the problem stays open.
    assert candidate.id in harness.state.artifacts
    assert harness.state.status[candidate.id] == Status.REFUTED
    assert any(w.commitment == "k-relevance" for w in harness.warrants.values())
    assert not covered(harness, rid)
    assert [e["problem"] for e in research_docket(harness, Config())] == [rid]


def test_relevant_supported_candidate_covers_until_reliability_falls(tmp_path):
    harness, rid, _ = _open_research_harness(
        tmp_path, relevance="'tide' in content.lower()")
    evidence = submit_evidence(
        harness, rid, "https://noaa.example/tides",
        "NOAA tide tables 2026: measured highs and lows",
        metadata={"retrieved_at": "2026-07-11T04:00:00Z", "query": "tide tables"})
    assert harness.state.status[evidence.id] == Status.ACCEPTED
    assert evidence.provenance.role.value == "import"  # agent material
    assert covered(harness, rid)
    assert research_docket(harness, Config()) == []  # left the open docket
    assert _signals(harness, "research-evidence-registered")

    # The claimed retrieval time is claim metadata on the attackable
    # reliability artifact — never the event clock.
    reliability_id = next(
        r.target for r in evidence.interface.refs if r.role.value == "dependence")
    reliability = harness.state.artifacts[reliability_id]
    assert "2026-07-11T04:00:00Z" in reliability.content_ref
    register_events = [e for e in harness.log.read()
                       if evidence.id in (e.outputs or [])]
    assert register_events and register_events[0].ts  # harness-controlled ts
    assert "2026-07-11T04:00:00Z" not in register_events[0].ts

    # Reliability attacked -> suspended_unsupported -> problem reopens via
    # graph recomputation; the evidence artifact is untouched.
    attack(harness, reliability_id, "source-was-a-mirror-site")
    assert harness.state.status[evidence.id] == Status.SUSPENDED_UNSUPPORTED
    assert not covered(harness, rid)
    assert [e["problem"] for e in research_docket(harness, Config())] == [rid]
    assert evidence.id in harness.state.artifacts  # nothing deleted

    # Replay: a fresh harness over the same log reconstructs everything.
    replayed = Harness(harness.log.path.parent if hasattr(harness.log, "path")
                       else tmp_path / "run")
    assert replayed.state.status == harness.state.status


def test_submit_evidence_rejects_non_research_problems(tmp_path):
    harness, rid, _ = _open_research_harness(tmp_path)
    with pytest.raises(ValueError, match="not a research problem"):
        submit_evidence(harness, "pi-tides", "src", "text")


def test_report_research_failure_is_operational_only(tmp_path):
    harness, rid, _ = _open_research_harness(tmp_path)
    artifacts_before = set(harness.state.artifacts)
    statuses_before = dict(harness.state.status)
    report_research_failure(
        harness, rid, "https://www.science.org/article",
        "The read operation timed out", category="blocked",
        detail="RuntimeError")
    failures = _signals(harness, "research-fetch-failed")
    assert len(failures) == 1 and failures[0].inputs[1] == rid
    assert failures[0].inputs[3] == "agent"  # never burns the internal cap
    assert set(harness.state.artifacts) == artifacts_before
    assert dict(harness.state.status) == statuses_before
    docket = research_docket(harness, Config())
    assert docket and docket[0]["failed_internal_attempts"] == 0


# ---- internal retrieval: bounded, logged, nonfatal ------------------- #

def test_backend_exception_is_caught_logged_and_cooled_down(tmp_path):
    harness, rid, adapter = _open_research_harness(tmp_path)
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=0, RESEARCH_PERIOD=1,
                    RESEARCH_COOLDOWN=3, RESEARCH_ATTEMPTS_MAX=5)
    scheduler = Scheduler(harness, adapter, config,
                          research_backend=_RaisingBackend())
    scheduler.run(3)  # survives every cycle
    failures = _signals(harness, "research-fetch-failed")
    assert len(failures) == 1  # cycle 0 attempt; cycles 1-2 inside cooldown
    assert failures[0].inputs[1] == rid
    assert "science.org" in " ".join(failures[0].inputs)
    scheduler.run(1)  # cycle 3: cooldown (3) elapsed -> second attempt
    assert len(_signals(harness, "research-fetch-failed")) == 2


def test_empty_result_takes_the_same_bounded_path(tmp_path):
    harness, rid, adapter = _open_research_harness(tmp_path)
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=0, RESEARCH_PERIOD=1,
                    RESEARCH_COOLDOWN=0, RESEARCH_ATTEMPTS_MAX=3)
    scheduler = Scheduler(harness, adapter, config,
                          research_backend=_EmptyBackend())
    scheduler.run(2)
    failures = _signals(harness, "research-fetch-failed")
    assert len(failures) == 2 and failures[0].inputs[4] == "no-result"


def test_attempt_cap_pauses_internal_strategy_only(tmp_path):
    harness, rid, adapter = _open_research_harness(tmp_path)
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=0, RESEARCH_PERIOD=1,
                    RESEARCH_COOLDOWN=0, RESEARCH_ATTEMPTS_MAX=2)
    scheduler = Scheduler(harness, adapter, config,
                          research_backend=_RaisingBackend())
    scheduler.run(5)
    assert len(_signals(harness, "research-fetch-failed")) == 2  # capped
    exhausted = _signals(harness, "research-fetch-exhausted")
    assert len(exhausted) == 1 and exhausted[0].inputs[1] == rid
    entry = research_docket(harness, config, cycle=scheduler._cycles)[0]
    assert entry["internal_exhausted"] and entry["failed_internal_attempts"] == 2
    # The problem is paused for the INTERNAL strategy, not closed: the
    # agent channel still covers it.
    evidence = submit_evidence(harness, rid, "https://noaa.example",
                               "measured tide tables")
    assert harness.state.status[evidence.id] == Status.ACCEPTED
    assert covered(harness, rid)


def test_one_internal_attempt_per_cycle_deterministic_order(tmp_path):
    harness, rid, adapter = _open_research_harness(tmp_path)
    # A second open research problem: same commitment on a second carrier.
    other = harness.create_artifact(
        "the wind pushes the sea",
        interface=Interface(commitments=["k-tide-tables"]),
        provenance=Provenance(role="conjecturer"), problem_id="pi-tides")
    rid2 = f"research:k-tide-tables:{other.id[:12]}"
    harness.register_problem(Problem(
        id=rid2, description="obtain evidence (second carrier)", criteria=[],
        provenance=ProblemProvenance.model_validate(
            {"trigger": "research", "from": [other.id, "k-tide-tables"]}),
    ))
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=0, RESEARCH_PERIOD=1,
                    RESEARCH_COOLDOWN=10, RESEARCH_ATTEMPTS_MAX=5)
    scheduler = Scheduler(harness, adapter, config,
                          research_backend=_RaisingBackend())
    scheduler.run(2)
    failures = _signals(harness, "research-fetch-failed")
    # One attempt per cycle even though both problems fail, and the order
    # is the sorted problem ids — a failing site is never hammered.
    assert [f.inputs[1] for f in failures] == sorted([rid, rid2])[:len(failures)]
    assert len(failures) == 2


def test_attempt_state_reconstructs_from_the_log_alone(tmp_path):
    harness, rid, adapter = _open_research_harness(tmp_path)
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=0, RESEARCH_PERIOD=1,
                    RESEARCH_COOLDOWN=0, RESEARCH_ATTEMPTS_MAX=2)
    Scheduler(harness, adapter, config,
              research_backend=_RaisingBackend()).run(3)
    # A FRESH harness + docket over the same root sees the same attempt
    # counts and exhaustion — no hidden mutable counters anywhere.
    reopened = Harness(tmp_path / "run")
    entry = research_docket(reopened, config)[0]
    assert entry["failed_internal_attempts"] == 2
    assert entry["internal_exhausted"] is True


# ---- episode signals ------------------------------------------------- #

def test_null_mode_logs_research_off_once_per_episode(tmp_path):
    harness, rid, adapter = _open_research_harness(tmp_path)
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=0)
    scheduler = Scheduler(harness, adapter, config, research_backend=None)
    scheduler.run(3)
    assert len(_signals(harness, "research-off")) == 1  # deduplicated
    # Episode ends when the request is covered...
    evidence = submit_evidence(harness, rid, "https://noaa.example",
                               "measured tide tables")
    assert covered(harness, rid)
    scheduler.run(1)
    assert len(_signals(harness, "research-off")) == 1
    # ...and a NEW episode logs a NEW event when coverage falls again.
    reliability = next(r.target for r in evidence.interface.refs
                       if r.role.value == "dependence")
    attack(harness, reliability, "the-source-was-fabricated")
    scheduler.run(1)
    assert len(_signals(harness, "research-off")) == 2


def test_agent_mode_waits_and_never_claims_research_off(tmp_path):
    harness, rid, adapter = _open_research_harness(tmp_path)
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=0)
    scheduler = Scheduler(harness, adapter, config,
                          research_backend=ResearchService("agent"))
    scheduler.run(4)  # docket sits open for several cycles
    assert _signals(harness, "research-off") == []  # silence != absence
    waiting = _signals(harness, "research-awaiting-agent")
    assert len(waiting) == 1 and rid in waiting[0].inputs


def test_grounding_brake_escalates_agent_docket(tmp_path):
    harness = Harness(tmp_path / "run")
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=0, LAMBDA_FLOOR=0.8, CAPTURE_W=40)
    aid = _observation_setup(harness)
    rid = f"research:k-tide-tables:{aid[:12]}"
    harness.register_problem(Problem(
        id=rid, description="obtain evidence", criteria=[],
        provenance=ProblemProvenance.model_validate(
            {"trigger": "research", "from": [aid, "k-tide-tables"]}),
    ))
    # Staged decay: rubric-only verdicts (the shape the existing brake test
    # uses) so grounding_decay fires under LAMBDA_FLOOR=0.8.
    from deepreason.informal.trial import transcript_blob

    harness.register_commitment(Commitment(id="kappa-r", eval="rubric:std-1"))
    for i in range(4):
        target = art(harness, f"informal claim {i}")
        nu = art(harness, f"nu: rubric ruling {i} is sound")
        trace_ref = transcript_blob(
            harness, case=f"violates clause {i}", answer="conceded",
            decisive_point=f"clause {i}",
            checks={"order_swap": "skipped", "paraphrase": "skipped"})
        harness.create_artifact(
            f"critic: rubric fail {i}", provenance=Provenance(role="critic"),
            warrants=[Warrant(id=f"w-r{i}", target=target.id,
                              type=WarrantType.DEMONSTRATIVE,
                              commitment="kappa-r", verdict="fail",
                              trace_ref=trace_ref, validity_node=nu.id)])
    counter = {"n": 0}

    def conjecture(prompt):
        counter["n"] += 1
        return json.dumps({"candidates": [
            {"content": f"claim {counter['n']}", "typicality": 0.5}]})

    adapter = LLMAdapter({"conjecturer": MockEndpoint(conjecture)},
                         harness.blobs, retry_max=2)
    scheduler = Scheduler(harness, adapter, config,
                          research_backend=ResearchService("agent"))
    scheduler.run(3)
    assert scheduler.research_priority
    requested = _signals(harness, "research-agent-requested")
    assert requested and rid in requested[0].inputs
    entry = research_docket(harness, config)[0]
    assert entry["priority"] == "escalated"  # log-derived docket priority


# ---- MCP / CLI parity ------------------------------------------------ #

def test_mcp_and_cli_expose_the_research_channel(tmp_path, monkeypatch):
    from deepreason import mcp_server
    from deepreason.cli.main import main as cli_main

    harness, rid, _ = _open_research_harness(tmp_path)
    root = str(tmp_path / "run")

    listing = mcp_server.call_tool("research_docket", {"root": root})
    assert rid in listing
    reply = mcp_server.call_tool("submit_evidence", {
        "root": root, "problem_id": rid, "source": "https://noaa.example",
        "content": "measured tide tables",
        "retrieved_at": "2026-07-11T04:00:00Z",
    })
    assert "candidate evidence registered" in reply and "covered" in reply
    reply = mcp_server.call_tool("report_research_failure", {
        "root": root, "problem_id": rid, "source": "https://www.science.org",
        "reason": "blocked",
    })
    assert "stays open" in reply

    # CLI parity over a fresh root.
    harness2, rid2, _ = _open_research_harness(tmp_path / "second")
    root2 = str(tmp_path / "second" / "run")
    assert cli_main(["--root", root2, "research"]) == 0
    evidence_file = tmp_path / "evidence.txt"
    evidence_file.write_text("measured tide tables again")
    assert cli_main(["--root", root2, "submit-evidence", rid2,
                     "--source", "https://noaa.example",
                     "--file", str(evidence_file)]) == 0
    assert covered(Harness(tmp_path / "second" / "run"), rid2)
    assert cli_main(["--root", root2, "report-research-failure", rid2,
                     "--source", "x", "--reason", "y"]) == 0
