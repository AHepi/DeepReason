"""Token budgeting: usage recorded per call, hard ceiling enforced before
spending, scheduler stops gracefully when the budget is exhausted."""

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.report import eval_report
from deepreason.scheduler.scheduler import Scheduler
from deepreason.storage.blobs import BlobStore

GOOD = json.dumps({"candidates": [{"content": "the moon pulls the sea", "typicality": 0.7}]})


def test_llmcall_records_tokens(tmp_path):
    meter = TokenMeter(budget=None)
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([GOOD])}, BlobStore(tmp_path / "b"),
        retry_max=2, meter=meter,
    )
    _, call = adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert call.tokens > 0
    assert meter.total == call.tokens
    assert meter.calls == 1


def test_budget_hard_stop_before_spending(tmp_path):
    meter = TokenMeter(budget=1)  # exhausted after the first call
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([GOOD, GOOD])}, BlobStore(tmp_path / "b"),
        retry_max=2, meter=meter,
    )
    adapter.call("conjecturer", "PACK", ConjecturerOutput)
    spent = meter.total
    with pytest.raises(TokenBudgetExceeded):
        adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert meter.total == spent  # the blocked call spent nothing


def test_scheduler_stops_gracefully_on_budget(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(
        Problem(
            id="pi-tides", description="explain the tides", criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    calls = {"n": 0}

    def conjecture(prompt):
        calls["n"] += 1
        return json.dumps(
            {"candidates": [{"content": f"the moon pulls the sea {calls['n']}", "typicality": 0.5}]}
        )

    meter = TokenMeter(budget=800)  # a couple of calls' worth
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(conjecture)}, harness.blobs, retry_max=2, meter=meter
    )
    scheduler = Scheduler(harness, adapter, Config(VS_K=1, N_SCHOOLS=0, FLOOR=0))
    result = scheduler.run(50)  # would be 50 cycles unbounded

    stopped = [d for d in result["diagnostics"] if "stopped" in d]
    assert stopped and "token budget exhausted" in stopped[-1]["stopped"]
    assert meter.total >= 800  # ran up to the ceiling, then stopped
    # State is consistent and the report still renders (tokens included).
    report = eval_report(harness, Config())
    assert report["totals"]["llm_tokens"] == sum(
        e.llm.tokens for e in harness.log.read() if e.llm
    )
    assert Harness(tmp_path / "run").state.model_dump_json() == harness.state.model_dump_json()


def test_arg_crit_per_cycle_cap(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(
        Problem(
            id="pi-tides", description="explain the tides", criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    critic_calls = {"n": 0}

    def critic(prompt):
        critic_calls["n"] += 1
        return json.dumps({"attack": False, "case": ""})

    def conjecture(prompt):
        return json.dumps(
            {"candidates": [
                {"content": f"moon account {i} {hash(prompt) % 997}", "typicality": 0.5}
                for i in range(3)
            ]}
        )

    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(conjecture), "argumentative_critic": MockEndpoint(critic)},
        harness.blobs, retry_max=2,
    )
    config = Config(VS_K=3, N_SCHOOLS=0, FLOOR=0, ARG_CRIT_PER_CYCLE=1)
    Scheduler(harness, adapter, config).run(2)
    assert critic_calls["n"] == 2  # one per cycle despite 3 admitted per cycle


def test_truncation_hint_on_length_finish(tmp_path):
    """A length-truncated response gets a compression hint, not a blind retry."""
    prompts_seen = []

    class TruncatingEndpoint(MockEndpoint):
        def complete(self, prompt):
            prompts_seen.append(prompt)
            response = super().complete(prompt)
            self.last_finish_reason = "length" if len(prompts_seen) == 1 else "stop"
            return response

    endpoint = TruncatingEndpoint(['{"candidates": [{"content": "cut off mid', GOOD])
    adapter = LLMAdapter({"conjecturer": endpoint}, BlobStore(tmp_path / "b"), retry_max=2)
    output, call = adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert call.attempts == 2
    assert "CUT OFF" in prompts_seen[1]  # the repair prompt says compress


def test_contract_coerces_object_content():
    """Skeleton emitted as a JSON object (not embedded string) still parses."""
    raw = json.dumps(
        {"candidates": [{"content": {"claim": "x", "mechanism": "y"}, "typicality": 0.5}]}
    )
    output = ConjecturerOutput.model_validate_json(raw)
    parsed = json.loads(output.candidates[0].content)
    assert parsed == {"claim": "x", "mechanism": "y"}


def test_transport_retries_transient_then_succeeds(monkeypatch):
    import urllib.error

    from deepreason.llm import endpoints as ep

    monkeypatch.setattr(ep.time, "sleep", lambda s: None)  # no real backoff in tests
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise urllib.error.URLError(ConnectionResetError(104, "reset by peer"))
        return {"ok": True}

    assert ep.request_with_retries(flaky) == {"ok": True}
    assert attempts["n"] == 3

    def auth_fail():
        raise urllib.error.HTTPError("u", 401, "unauthorized", {}, None)

    with pytest.raises(ep.EndpointError):  # non-retryable: raises immediately
        ep.request_with_retries(auth_fail)
