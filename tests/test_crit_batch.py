"""Batch criticism (docs/TOKEN_ECONOMY.md angle 3): one argumentative-critic
call over K targets. The call is shared; the epistemology is not — every
attacking case registers a per-target argumentative warrant with its own nu,
cases naming unlisted targets are dropped, and the shared call is logged
exactly once (on the first registration, or on a Measure when nothing
registers)."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Commitment,
    Problem,
    ProblemProvenance,
    Rule,
    Status,
    WarrantType,
)
from deepreason.rules.crit import crit_argumentative_batch
from deepreason.scheduler.scheduler import Scheduler


def _batch(*cases) -> str:
    return json.dumps({"cases": list(cases)})


def _adapter(harness, critic_responses) -> LLMAdapter:
    return LLMAdapter(
        {"argumentative_critic": MockEndpoint(critic_responses)},
        harness.blobs,
        retry_max=2,
    )


def _two_targets(harness):
    a = harness.create_artifact("the moon pulls the sea")
    b = harness.create_artifact("moon resonance in basins")
    return a, b


def test_batch_registers_per_target_warrants(harness):
    a, b = _two_targets(harness)
    adapter = _adapter(
        harness,
        [
            _batch(
                {"target": a.id, "attack": True, "case": "ignores solar forcing"},
                {"target": b.id, "attack": True, "case": "resonance needs a basin period"},
            )
        ],
    )
    critics = crit_argumentative_batch(harness, [a.id, b.id], adapter, Config())
    assert len(critics) == 2
    warrants = [w for c in critics for w in harness.warrants.values() if w.target in (a.id, b.id)]
    assert {w.target for w in warrants} == {a.id, b.id}
    assert all(w.type == WarrantType.ARGUMENTATIVE for w in warrants)
    # Each warrant hangs on its OWN attackable validity node.
    assert len({w.validity_node for w in warrants}) == 2
    # Unanswered attacks stand: both targets fall, independently.
    assert harness.state.status[a.id] == Status.REFUTED
    assert harness.state.status[b.id] == Status.REFUTED
    # The shared call is logged exactly once across the two registrations.
    llm_events = [e for e in harness.log.read() if e.llm is not None]
    assert len(llm_events) == 1


def test_case_against_unlisted_target_is_dropped(harness):
    a, b = _two_targets(harness)
    outsider = harness.create_artifact("an artifact the critic was never shown")
    adapter = _adapter(
        harness,
        [
            _batch(
                {"target": outsider.id, "attack": True, "case": "confabulated attack"},
                {"target": a.id, "attack": False, "case": ""},
                {"target": b.id, "attack": False, "case": ""},
            )
        ],
    )
    critics = crit_argumentative_batch(harness, [a.id, b.id], adapter, Config())
    assert critics == []  # no verdict without exposure
    assert harness.state.status[outsider.id] == Status.ACCEPTED
    # The no-registration call is still on the record (token accounting).
    last = list(harness.log.read())[-1]
    assert last.rule == Rule.MEASURE and last.llm is not None
    assert last.inputs == ["batch-crit", a.id, b.id]


def test_single_target_delegates_to_single_contract(harness):
    a = harness.create_artifact("the moon pulls the sea")
    # Response shaped for ArgumentativeCriticOutput — only valid via delegation.
    adapter = _adapter(harness, [json.dumps({"attack": True, "case": "no solar term"})])
    critics = crit_argumentative_batch(harness, [a.id], adapter, Config())
    assert len(critics) == 1
    assert harness.state.status[a.id] == Status.REFUTED


def _seeded_scheduler(tmp_path, critic_endpoint, **config_kwargs):
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(
        Problem(
            id="pi-tides",
            description="explain the tides",
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    conj = json.dumps(
        {
            "candidates": [
                {"content": f"moon idea {i}", "typicality": 0.9 - 0.1 * i}
                for i in range(3)
            ]
        }
    )
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint([conj]),
            "argumentative_critic": critic_endpoint,
        },
        harness.blobs,
        retry_max=2,
    )
    config = Config(VS_K=3, N_SCHOOLS=0, **config_kwargs)
    return harness, Scheduler(harness, adapter, config)


class _CountingCritic:
    """Answers every pack with per-target attack=false entries."""

    def __init__(self):
        self.calls = 0

    def __call__(self, prompt: str) -> str:
        self.calls += 1
        targets = [
            line.split()[1]
            for line in prompt.splitlines()
            if line.startswith("TARGET ")
        ]
        if targets:  # batch pack
            return _batch(*[{"target": t, "attack": False, "case": ""} for t in targets])
        return json.dumps({"attack": False, "case": ""})


def test_scheduler_batches_survivors_into_one_call(tmp_path):
    critic = _CountingCritic()
    harness, scheduler = _seeded_scheduler(
        tmp_path, MockEndpoint(critic), CRIT_BATCH_K=3
    )
    scheduler.step()
    survivors = [a for a, s in harness.state.status.items() if s == Status.ACCEPTED]
    assert len(survivors) >= 3
    assert critic.calls == 1  # three admitted targets, one critic call


def test_arg_crit_cap_counts_targets_not_calls(tmp_path):
    critic = _CountingCritic()
    harness, scheduler = _seeded_scheduler(
        tmp_path, MockEndpoint(critic), CRIT_BATCH_K=3, ARG_CRIT_PER_CYCLE=2
    )
    scheduler.step()
    assert critic.calls == 1
    # Only 2 of the 3 admitted targets were shown to the critic.
    last_prompt = [e for e in harness.log.read() if e.rule == Rule.MEASURE and e.llm][-1]
    assert len(last_prompt.inputs) - 1 == 2  # ["batch-crit", t1, t2]


def test_standing_survivor_swept_into_leftover_slots(tmp_path):
    from deepreason.ontology import Provenance

    critic = _CountingCritic()
    harness, scheduler = _seeded_scheduler(
        tmp_path, MockEndpoint(critic), CRIT_BATCH_K=4, ARG_CRIT_PER_CYCLE=4
    )
    # Accepted BEFORE any cycle: under legacy behavior it would never be
    # criticized (only freshly admitted artifacts reached the critic).
    standing = harness.create_artifact(
        "an early accepted moon claim nobody ever attacked",
        provenance=Provenance(role="conjecturer"),
    )
    scheduler.step()
    # 3 fresh admits + 1 leftover slot -> the standing survivor was shown.
    shown = [
        e for e in harness.log.read()
        if e.rule == Rule.MEASURE and e.llm and standing.id in e.inputs
    ]
    assert shown


def test_standing_goodhart_trap_is_fuzz_refuted_in_the_sweep(tmp_path):
    """End-to-end (mock LLM): a seeded candidate passes its frozen property
    inputs (execution-backed Goodhart survivor) but is wrong in general. The
    standing sweep runs the deterministic fuzz pass BEFORE spending an LLM
    call, and the trap falls to a machine-found counterexample — refuted by
    a demonstrative warrant, no critic model involved."""
    from deepreason.ontology import Interface, Provenance, WarrantType
    from deepreason.oracle import property_oracle_commitment

    critic = _CountingCritic()
    harness, scheduler = _seeded_scheduler(
        tmp_path, MockEndpoint(critic), CRIT_BATCH_K=4, ARG_CRIT_PER_CYCLE=4
    )
    checker = (
        "def check(inp, out):\n"
        "    xs = inp[0]\n"
        "    return isinstance(out, list) and sorted(xs) == out\n"
    )
    gen = (
        "def gen(k):\n"
        "    n = 1 + k % 4\n"
        "    xs = []\n"
        "    j = k\n"
        "    for i in range(n):\n"
        "        xs.append((j * 7 + i * 3) % 10)\n"
        "        j = j // 2 + 1\n"
        "    return [xs]\n"
    )
    c = property_oracle_commitment(
        "solve", [[[3, 1, 2]]], checker, generator=gen
    )
    harness.register_commitment(c)
    trap = harness.create_artifact(
        "def solve(xs):\n"
        "    if len(xs) > 2:\n"
        "        return sorted(xs)\n"
        "    return xs\n",
        codec="code:python",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"),
    )
    assert harness.state.status[trap.id] == Status.ACCEPTED  # frozen input passes
    scheduler.step()
    assert harness.state.status[trap.id] == Status.REFUTED
    w = next(w for w in harness.warrants.values() if w.target == trap.id)
    assert w.type == WarrantType.DEMONSTRATIVE  # machine experiment, not a judge


def test_recrit_standing_off_preserves_legacy(tmp_path):
    from deepreason.ontology import Provenance

    critic = _CountingCritic()
    harness, scheduler = _seeded_scheduler(
        tmp_path, MockEndpoint(critic),
        CRIT_BATCH_K=4, ARG_CRIT_PER_CYCLE=4, RECRIT_STANDING=False,
    )
    standing = harness.create_artifact(
        "an early accepted moon claim nobody ever attacked",
        provenance=Provenance(role="conjecturer"),
    )
    scheduler.step()
    shown = [
        e for e in harness.log.read()
        if e.rule == Rule.MEASURE and e.llm and standing.id in e.inputs
    ]
    assert not shown  # legacy: only freshly admitted artifacts are criticized
