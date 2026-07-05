"""Regression tests for the code-review remediation.

Each test pins a specific fix so the bug cannot silently return. Grouped by
the review's finding groups (durability, budget/endpoint, invariants).
"""

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter, _usage_tokens
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Status
from deepreason.storage.merge import merge
from deepreason.storage.objects import ObjectStore
from tests.conftest import art

GOOD = json.dumps({"candidates": [{"content": "the moon pulls the sea", "typicality": 0.7}]})


# --------------------------------------------------------------------------- #
# Group 1 — durability                                                        #
# --------------------------------------------------------------------------- #

def test_log_tolerates_torn_final_line(tmp_path):
    """A crash mid-append leaves a partial final line; reopening must skip it,
    not raise, so the session stays openable."""
    root = tmp_path / "run"
    harness = Harness(root)
    harness.register_commitment(Commitment(id="k", eval="predicate:True"))
    art(harness, "a durable claim")
    good = harness.state.model_dump_json()

    # Simulate a torn write: append a truncated JSON line to the log.
    with open(root / "log.jsonl", "a", encoding="utf-8") as f:
        f.write('{"seq": 999, "rule": "register", "inp')  # no newline, cut off

    with pytest.warns(UserWarning, match="torn final line"):
        reopened = Harness(root)
    assert reopened.state.model_dump_json() == good  # torn event dropped


def test_object_store_heals_corrupt_record(tmp_path):
    """A partially-written object file must be rewritable, not permanently
    poisoned by the exists-check."""
    store = ObjectStore(tmp_path / "objects")
    commitment = Commitment(id="k-heal", eval="predicate:True")
    # Poison the content-addressed path with a truncated file.
    path = store._path(commitment.id)
    path.write_text('{"schema": "commitment", "id": "k-heal", "dat')  # corrupt
    with pytest.raises(ValueError):
        store.get(commitment.id)
    # put() must detect the corruption and rewrite atomically.
    store.put("commitment", commitment)
    schema, obj = store.get(commitment.id)
    assert schema == "commitment" and obj.id == "k-heal"


# --------------------------------------------------------------------------- #
# Group 2 — budget + endpoint robustness                                      #
# --------------------------------------------------------------------------- #

def test_partial_usage_dict_counts_tokens():
    """A truthy-but-partial usage dict (only total_tokens) must not count as
    zero spend against the hard budget."""
    only_total = _usage_tokens({"total_tokens": 1500}, "req", "raw")
    assert only_total["prompt_tokens"] + only_total["completion_tokens"] == 1500
    # A usage dict missing every count falls back to the chars/4 estimate.
    est = _usage_tokens({"foo": 1}, "a" * 40, "b" * 40)
    assert est["prompt_tokens"] == 10 and est["completion_tokens"] == 10


def test_partial_usage_dict_trips_budget(tmp_path):
    """End-to-end: an endpoint reporting only total_tokens still advances the
    meter, so the hard ceiling trips."""
    from deepreason.storage.blobs import BlobStore

    class PartialUsageEndpoint(MockEndpoint):
        def complete(self, prompt):
            out = super().complete(prompt)
            self.last_usage = {"total_tokens": 1000}  # partial shape
            return out

    meter = TokenMeter(budget=500)
    adapter = LLMAdapter(
        {"conjecturer": PartialUsageEndpoint([GOOD, GOOD])},
        BlobStore(tmp_path / "b"), retry_max=2, meter=meter,
    )
    adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert meter.total == 1000  # not zero
    with pytest.raises(TokenBudgetExceeded):
        adapter.call("conjecturer", "PACK", ConjecturerOutput)


def test_null_content_raises_endpoint_error(monkeypatch):
    from deepreason.llm import endpoints as ep

    endpoint = ep.OpenAICompatEndpoint("https://api.test", "m")
    monkeypatch.setattr(
        ep, "request_with_retries",
        lambda fn: {"choices": [{"message": {"content": None}, "finish_reason": "content_filter"}]},
    )
    with pytest.raises(ep.EndpointError, match="null content"):
        endpoint.complete("PROMPT")


def test_malformed_body_raises_endpoint_error(monkeypatch):
    from deepreason.llm import endpoints as ep

    endpoint = ep.OpenAICompatEndpoint("https://api.test", "m")
    monkeypatch.setattr(
        ep, "request_with_retries", lambda fn: {"error": {"message": "overloaded"}}
    )
    with pytest.raises(ep.EndpointError, match="malformed completion"):
        endpoint.complete("PROMPT")


def test_deepseek_low_effort_stays_cheap():
    """The reasoning cost knob must be ordinal: low != high."""
    from deepreason.llm.providers import reasoning_body

    assert reasoning_body("deepseek", "low") == {
        "thinking": {"type": "enabled", "effort": "low"}
    }
    assert reasoning_body("deepseek", "medium") == {
        "thinking": {"type": "enabled", "effort": "medium"}
    }


def test_token_meter_zero_budget_stops_immediately():
    """budget=0 is a real ceiling: the first check trips before any spend."""
    meter = TokenMeter(budget=0)
    with pytest.raises(TokenBudgetExceeded):
        meter.check()


# --------------------------------------------------------------------------- #
# Group 3 — core invariants                                                   #
# --------------------------------------------------------------------------- #

def _session_with_addr(root, problem_id: str, content: str) -> Harness:
    h = Harness(root)
    h.register_commitment(Commitment(id="k-true", eval="predicate:True"))
    h.register_problem(
        Problem(
            id=problem_id, description=f"problem {problem_id}", criteria=["k-true"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    h.create_artifact(content, problem_id=problem_id)
    return h


def test_merge_preserves_addr_to_new_problem(tmp_path):
    """A known artifact addressed to a fresh problem in the source must keep
    that (artifact, problem) pair after merge (not be dropped as 'known')."""
    a = _session_with_addr(tmp_path / "a", "pi-a", "the shared claim")
    b = _session_with_addr(tmp_path / "b", "pi-b", "the shared claim")
    shared_id = next(iter(a.state.artifacts))
    assert shared_id in b.state.artifacts  # same content => same id

    merge(a, tmp_path / "b")
    assert ("pi-b" in a.state.problems)
    assert (shared_id, "pi-b") in a.state.addr  # addr reconstructed
    assert (shared_id, "pi-a") in a.state.addr  # original preserved


def test_merge_keeps_latest_measurement(tmp_path):
    """Two re-estimates in the source must land latest-wins, not oldest-wins."""
    a = Harness(tmp_path / "a")
    b = Harness(tmp_path / "b")
    x = art(b, "measured claim")
    b.record_measure(hv={x.id: 0.3})
    b.record_measure(hv={x.id: 0.8})  # newer re-estimate
    merge(a, tmp_path / "b")
    assert a.state.hv[x.id] == 0.8


def test_reach_clears_to_zero(tmp_path):
    """A once-reaching artifact that no longer reaches must be cleared to 0.0,
    not ranked forever on a stale count (the falsy-zero bug kept it stuck)."""
    from deepreason.measures.reach import reach_sweep

    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-true", eval="predicate:True"))
    h.register_problem(
        Problem(
            id="home", description="home", criteria=["k-true"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    artifact = h.create_artifact("reaching claim", problem_id="home")
    # Pre-seed a stale reach as an earlier sweep would have (Measure event).
    h.record_measure(reach={artifact.id: 3.0})
    assert h.state.reach[artifact.id] == 3.0
    # A foreign problem the artifact does NOT satisfy: current reach is 0.
    h.register_commitment(Commitment(id="k-no", eval="predicate:'zzzz' in content"))
    h.register_problem(
        Problem(
            id="foreign", description="foreign", criteria=["k-no"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    reach_sweep(h)
    assert h.state.reach.get(artifact.id) == 0.0  # stale 3.0 cleared


def test_program_verdict_trace_is_deterministic():
    """No wall-clock value may drive a verdict or enter the content-addressed
    trace (determinism, §0)."""
    from deepreason import programs
    from deepreason.ontology import Artifact, Interface, Provenance
    from deepreason.ontology.commitment import Budget

    commitment = Commitment(
        id="k", eval="predicate:'moon' in content", budget=Budget(time_ms=0)
    )
    artifact = Artifact(
        id="x", content_ref="inline:the moon", codec="utf8",
        interface=Interface(), provenance=Provenance(role="seed"),
    )
    verdict, trace = programs.evaluate(commitment, artifact, None)
    assert verdict == programs.PASS  # NOT rewritten to overrun despite time_ms=0
    assert "elapsed_ms" not in trace  # no wall-clock in the addressed trace


def test_skeleton_id_includes_observation_valued(tmp_path):
    """Two forbidden cases identical but for observation_valued must get
    distinct commitment ids, or the research Spawn trigger is suppressed."""
    from deepreason.informal.skeleton import (
        ForbiddenCase, Scope, Skeleton, compile_forbidden_commitments,
    )

    h = Harness(tmp_path / "run")

    def skel(obs: bool) -> Skeleton:
        return Skeleton(
            claim="c", mechanism="m", scope=Scope(),
            forbidden=[ForbiddenCase(case="X", eval="program:json-wf", observation_valued=obs)],
        )

    id_false = compile_forbidden_commitments(h, skel(False))[0]
    id_true = compile_forbidden_commitments(h, skel(True))[0]
    assert id_false != id_true
    assert h.commitments[id_true].observation_valued is True


def test_hv_floor_no_vacuous_pass_on_empty_edits(tmp_path):
    """No sampled edits => hv UNMEASURED, never a vacuous hv=1.0 PASS. Reached
    when k=0 slices edits[:0] to empty (VariatorOutput forbids an empty list
    on the wire)."""
    from deepreason.measures.hv import hv_floor_commitment, run_hv_floor
    from deepreason.ontology import Interface
    from deepreason.programs import OVERRUN

    h = Harness(tmp_path / "run")
    config = Config(HV_K=0, HV_MIN=0.5)  # k=0 => edits[:0] == []
    floor = hv_floor_commitment(config)
    h.register_commitment(floor)
    target = h.create_artifact("a relation", interface=Interface(commitments=[floor.id]))
    adapter = LLMAdapter(
        {"variator": MockEndpoint([json.dumps({"edits": [{"content": "an edit"}]})])},
        h.blobs, retry_max=2,
    )
    verdict = run_hv_floor(h, adapter, target.id, floor)
    assert verdict == OVERRUN
    assert target.id not in h.state.hv  # nothing recorded — not a vacuous 1.0


def test_ladder_interventions_clear_after_window(tmp_path):
    """A response-ladder intervention is active for CAPTURE_W cycles, then
    clears — it must not latch on for the rest of the run."""
    from deepreason.capture import ladder
    from deepreason.scheduler.scheduler import Scheduler

    h = Harness(tmp_path / "run")
    adapter = LLMAdapter({}, h.blobs, retry_max=2)
    sched = Scheduler(h, adapter, Config(CAPTURE_W=3, N_SCHOOLS=0, FLOOR=0))
    assert not sched.recruit_all and not sched.spec_injection

    ladder.respond(sched, {"lineage_stagnation": True})  # fires at cycle 0
    assert sched.recruit_all and sched.tail_weighted
    assert sched.complement and sched.spec_injection

    sched._cycles = 2  # still inside the CAPTURE_W=3 window
    assert sched.recruit_all
    sched._cycles = 3  # window (0 + 3) has elapsed
    assert not sched.recruit_all and not sched.tail_weighted
    assert not sched.complement and not sched.spec_injection


def test_pairwise_blocks_empty_decisive_point(tmp_path):
    """A pairwise winner with an empty decisive_point is unscreened LLM
    adjudication and must be blocked, registering nothing."""
    from deepreason.informal.trial import pairwise_discriminate

    h = Harness(tmp_path / "run")
    h.register_problem(
        Problem(
            id="pi", description="discriminate", criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    a = art(h, "candidate A")
    b = art(h, "candidate B")
    # Order-swap-consistent winner, but no decisive_point on either ruling.
    rulings = [json.dumps({"winner": "A", "decisive_point": ""}),
               json.dumps({"winner": "B", "decisive_point": ""})]
    adapter = LLMAdapter({"judge": MockEndpoint(rulings)}, h.blobs, retry_max=2)
    before = set(h.state.artifacts)
    result = pairwise_discriminate(h, h.state.problems["pi"], a.id, b.id, adapter, Config())
    assert result is None  # blocked
    assert h.state.status.get(b.id) == Status.ACCEPTED  # loser NOT refuted
    assert set(h.state.artifacts) == before  # no critic/nu registered
