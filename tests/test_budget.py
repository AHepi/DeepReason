"""Token budgeting: usage recorded per call, hard ceiling enforced before
spending, scheduler stops gracefully when the budget is exhausted."""

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.informal.standards import register_standard
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
    # Reserve-settle semantics (llm/budget.py): a dispatch is admitted only
    # when spent + reserved + its conservative bound fits the ceiling.  The
    # first call's bound is ~1284 tokens here (chars/3 prompt estimate + the
    # mock's 512 completion cap), so 1500 admits exactly one call.
    meter = TokenMeter(budget=1500)
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([GOOD, GOOD])}, BlobStore(tmp_path / "b"),
        retry_max=2, meter=meter,
    )
    adapter.call("conjecturer", "PACK", ConjecturerOutput)
    spent = meter.total
    assert 0 < spent <= 1100  # settled to reported usage, under the ceiling
    with pytest.raises(TokenBudgetExceeded):
        adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert meter.total == spent  # the blocked call spent nothing


def test_budget_smaller_than_any_bound_blocks_the_first_dispatch(tmp_path):
    """The ceiling is never overshot, not even by the first call: a budget
    below the call's reserved bound rejects the dispatch before spending."""
    meter = TokenMeter(budget=1)
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([GOOD])}, BlobStore(tmp_path / "b"),
        retry_max=2, meter=meter,
    )
    with pytest.raises(TokenBudgetExceeded):
        adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert meter.total == 0 and meter.reserved == 0


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

    meter = TokenMeter(budget=2500)  # a few calls' worth of reserved bounds
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(conjecture)}, harness.blobs, retry_max=2, meter=meter
    )
    scheduler = Scheduler(harness, adapter, Config(VS_K=1, N_SCHOOLS=0, FLOOR=0))
    result = scheduler.run(50)  # would be 50 cycles unbounded

    stopped = [d for d in result["diagnostics"] if "stopped" in d]
    assert stopped and "token budget" in stopped[-1]["stopped"]
    # Ran until a dispatch could no longer be reserved, then stopped; the
    # reserve-settle meter never lets the logged total exceed the ceiling.
    assert 0 < meter.total <= 2500
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


def _rubric_trial_adapter(judge, harness):
    """A cross-family judge ensemble (require_cross_family_judges, R2's
    solo law reconciliation: adapter.py:673) plus the argumentative_critic/
    defender roles run_trial also requires (informal/trial.py:239-241) --
    without either, every trial blocks before ever reaching the judge,
    which would make a judge-call counter measure nothing."""
    return LLMAdapter(
        {
            "judge": [
                MockEndpoint(judge, name="mock://judge-gemma", model="gemma-test"),
                MockEndpoint(judge, name="mock://judge-qwen", model="qwen-test"),
            ],
            "argumentative_critic": MockEndpoint(
                lambda p: json.dumps({"attack": True, "case": "violates clause 1"})
            ),
            "defender": MockEndpoint(lambda p: json.dumps({"answer": "no."})),
        },
        harness.blobs,
    )


def test_judge_summons_per_cycle_cap(tmp_path):
    """JUDGE_SUMMONS_PER_CYCLE (Part D, R10): a static per-cycle cap on
    judge dispatch, modeled on ARG_CRIT_PER_CYCLE above. Calls _criticize
    directly (like test_scheduler.py's gating test) rather than driving a
    full run(): VS_K>1 rivals on one problem spawn discrimination, which
    dispatches judges through an unrelated, un-throttled path and would
    contaminate the count this test means to isolate."""
    from deepreason.ontology import Interface, Provenance

    harness = Harness(tmp_path / "run")
    register_standard(harness, "std-x", rubric="must name a mechanism")
    commitment = Commitment(id="k-rubric", eval="rubric:std-x")
    harness.register_commitment(commitment)
    targets = [
        harness.create_artifact(
            f"the mechanism, account {i}",
            interface=Interface(commitments=[commitment.id]),
            provenance=Provenance(role="conjecturer"),
        )
        for i in range(3)
    ]
    judge_calls = {"n": 0}

    def judge(prompt):
        judge_calls["n"] += 1
        return json.dumps({"verdict": "pass", "decisive_point": "x"})

    adapter = _rubric_trial_adapter(judge, harness)
    config = Config(
        N_SCHOOLS=0, JUDGE_SEATS_ENABLED=True,
        JUDGE_SUMMONS_PER_CYCLE=1, JUDGE_SUMMONS_COOLDOWN=0,
    )
    scheduler = Scheduler(harness, adapter, config, workload_profile="code")
    for target in targets:
        scheduler._criticize(target)  # all within the same (uncleared) cycle
    # One trial gets through (cap=1); each trial consults both cross-family
    # judge seats (require_cross_family_judges), so one admitted trial is 2
    # judge calls, not 1 -- capped at that despite 3 rubric-bearing targets.
    assert judge_calls["n"] == 2


def test_judge_summons_cooldown(tmp_path):
    """JUDGE_SUMMONS_COOLDOWN (Part D, R10): a static per-target cooldown,
    modeled on DISC_COOLDOWN -- the SAME rubric target re-triggers a judge
    summons every cycle, but the cooldown spaces its repeat summonses out
    so one standoff cannot monopolize the whole run's judge budget. Cycle
    advancement is simulated by hand (the same _cycles/_judge_summons_this_
    cycle bookkeeping step() does) so the test isolates the cooldown from
    the per-cycle cap and from unrelated dispatch (see the per-cycle-cap
    test above for why a full run() would contaminate the count)."""
    from deepreason.ontology import Interface, Provenance

    harness = Harness(tmp_path / "run")
    register_standard(harness, "std-x", rubric="must name a mechanism")
    commitment = Commitment(id="k-rubric", eval="rubric:std-x")
    harness.register_commitment(commitment)
    target = harness.create_artifact(
        "the mechanism is explicit",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer"),
    )
    judge_calls = {"n": 0}

    def judge(prompt):
        judge_calls["n"] += 1
        return json.dumps({"verdict": "pass", "decisive_point": "x"})

    adapter = _rubric_trial_adapter(judge, harness)
    config = Config(
        N_SCHOOLS=0, JUDGE_SEATS_ENABLED=True,
        JUDGE_SUMMONS_PER_CYCLE=10, JUDGE_SUMMONS_COOLDOWN=3,
    )
    scheduler = Scheduler(harness, adapter, config, workload_profile="code")
    for cycle in range(6):
        scheduler._cycles = cycle
        scheduler._judge_summons_this_cycle = 0  # per-cycle reset, as step() does
        scheduler._criticize(target)
    # Admitted at cycle 0 and again at cycle 3 (3 - 0 == COOLDOWN, no longer
    # < it); cycles 1-2 and 4-5 fall inside the cooldown window and block.
    # Two admitted trials x two cross-family judge seats each = 4 calls.
    assert judge_calls["n"] == 4


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


def test_predicate_comprehensions_work():
    """Comprehension bodies must see the safe namespace (globals, not locals)."""
    from deepreason import programs
    from deepreason.ontology import Artifact, Commitment, Interface, Provenance

    oracle = Commitment(
        id="oracle",
        eval=(
            'predicate:[len(w) for w in re.findall(r"[A-Za-z]+", content)][:8] '
            "== [3, 1, 4, 1, 5, 9, 2, 6]"
        ),
    )

    def artifact(text):
        return Artifact(
            id="x", content_ref=f"inline:{text}", codec="utf8",
            interface=Interface(), provenance=Provenance(role="seed"),
        )

    good = artifact("How I need a drink, alcoholic of course")
    bad = artifact("The tides are magic")
    assert programs.evaluate(oracle, good, None)[0] == "pass"
    assert programs.evaluate(oracle, bad, None)[0] == "fail"
